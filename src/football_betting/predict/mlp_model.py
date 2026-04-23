"""
MLP (Multi-Layer Perceptron) classifier for match outcome prediction.

v0.3 adds a neural network as a third ensemble member. Keeps the same
feature pipeline as CatBoost so they share input preprocessing.

Architecture:
    input → Linear → BN → ReLU → Dropout → ... → Linear(3) → Softmax

Uses early stopping on validation log-loss, and saves both PyTorch state
dict and ONNX export for production deployment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from rich.console import Console
from sklearn.preprocessing import StandardScaler

from football_betting.config import (
    MLP_CFG,
    MODELS_DIR,
    MLPConfig,
    ModelPurpose,
    artifact_suffix,
)
from football_betting.data.models import Fixture, Match, Prediction
from football_betting.features.builder import FeatureBuilder
from football_betting.predict.calibration import ProbabilityCalibrator

console = Console()

OUTCOME_TO_INT = {"H": 0, "D": 1, "A": 2}
INT_TO_OUTCOME = {v: k for k, v in OUTCOME_TO_INT.items()}


# Lazy torch import — keeps the rest of the package usable without torch installed
def _import_torch():
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader, TensorDataset

        return torch, nn, optim, DataLoader, TensorDataset
    except ImportError as e:
        raise ImportError("PyTorch required for MLP model. Install with: pip install torch") from e


def _build_network(input_dim: int, cfg: MLPConfig):
    """Construct the MLP network."""
    torch, nn, *_ = _import_torch()

    layers = []
    prev_dim = input_dim
    for hidden_dim in cfg.hidden_dims:
        layers.append(nn.Linear(prev_dim, hidden_dim))
        if cfg.batch_norm:
            layers.append(nn.BatchNorm1d(hidden_dim))
        layers.append(nn.ReLU())
        if cfg.dropout > 0:
            layers.append(nn.Dropout(cfg.dropout))
        prev_dim = hidden_dim
    layers.append(nn.Linear(prev_dim, 3))  # 3-class: H/D/A
    return nn.Sequential(*layers)


@dataclass(slots=True)
class MLPPredictor:
    """PyTorch MLP for match outcome prediction."""

    feature_builder: FeatureBuilder = field(default_factory=FeatureBuilder)
    cfg: MLPConfig = field(default_factory=lambda: MLP_CFG)
    model: Any = None  # torch.nn.Module
    scaler: StandardScaler | None = None
    feature_names: list[str] = field(default_factory=list)
    calibrator: ProbabilityCalibrator | None = None
    #: Dual-model split — see ``CatBoostPredictor.purpose``.
    purpose: ModelPurpose = "1x2"

    # ───────────────────────── Training data ─────────────────────────

    def build_training_data(
        self,
        matches: list[Match],
        warmup_games: int = 100,
    ) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
        """Same no-leak chronological walk as CatBoostPredictor.

        Returns (features_df, labels, odds_array) where odds_array has shape
        (N, 3) — columns (home, draw, away). Missing odds → (2.0, 3.5, 3.5)
        placeholder so KellyLoss stays well-defined.
        """
        self.feature_builder.reset()

        rows: list[dict[str, float]] = []
        labels: list[int] = []
        odds_rows: list[tuple[float, float, float]] = []
        matches_sorted = sorted(matches, key=lambda m: m.date)

        for idx, match in enumerate(matches_sorted):
            if idx >= warmup_games:
                feats = self.feature_builder.build_features(
                    home_team=match.home_team,
                    away_team=match.away_team,
                    league_key=match.league,
                    match_date=match.date,
                    odds_home=match.odds.home if match.odds else None,
                    odds_draw=match.odds.draw if match.odds else None,
                    odds_away=match.odds.away if match.odds else None,
                    season=match.season,
                    kickoff_datetime_utc=match.kickoff_datetime_utc,
                )
                rows.append(feats)
                labels.append(OUTCOME_TO_INT[match.result])
                if match.odds:
                    odds_rows.append((match.odds.home, match.odds.draw, match.odds.away))
                else:
                    odds_rows.append((2.0, 3.5, 3.5))

            self.feature_builder.update_with_match(match)

        df = pd.DataFrame(rows).fillna(0.0)
        self.feature_names = list(df.columns)
        return df, np.array(labels), np.asarray(odds_rows, dtype=np.float32)

    # ───────────────────────── Training ─────────────────────────

    def fit(
        self,
        matches: list[Match],
        warmup_games: int = 100,
        val_fraction: float = 0.15,
        calibrate: bool = True,
    ) -> dict[str, Any]:
        torch, nn, optim, DataLoader, TensorDataset = _import_torch()
        torch.manual_seed(self.cfg.random_seed)

        X, y, odds = self.build_training_data(matches, warmup_games=warmup_games)
        if len(X) < 200:
            raise ValueError(f"Too few samples: {len(X)}")

        split = int(len(X) * (1 - val_fraction))
        X_train, X_val = X.iloc[:split].values, X.iloc[split:].values
        y_train, y_val = y[:split], y[split:]
        odds_train, odds_val = odds[:split], odds[split:]

        # Fit scaler on train only
        self.scaler = StandardScaler()
        X_train_s = self.scaler.fit_transform(X_train)
        X_val_s = self.scaler.transform(X_val)

        # Build network
        self.model = _build_network(X_train_s.shape[1], self.cfg)
        from football_betting.predict.gpu_utils import resolve_device

        device_pref = os.environ.get("FB_TORCH_DEVICE", "auto")
        device, backend = resolve_device(device_pref)  # type: ignore[arg-type]
        console.log(f"[cyan]MLP training on {backend} ({device})[/cyan]")
        self.model.to(device)

        optimizer = optim.Adam(
            self.model.parameters(),
            lr=self.cfg.learning_rate,
            weight_decay=self.cfg.weight_decay,
        )

        use_kelly = bool(getattr(self.cfg, "use_kelly_loss", False))
        if use_kelly:
            from football_betting.predict.losses import CombinedLoss

            combined = CombinedLoss(
                lam=self.cfg.kelly_lambda,
                f_cap=self.cfg.kelly_f_cap,
            )
            ce_only = nn.CrossEntropyLoss()
        else:
            combined = None
            ce_only = nn.CrossEntropyLoss()

        _eye3 = torch.eye(3, dtype=torch.float32, device=device)

        def _onehot(yb: Any) -> Any:
            # Indexing into a fixed eye matrix — avoids ``F.one_hot``
            # (and scatter) which are unsupported on the DirectML backend.
            return _eye3[yb]

        train_ds = TensorDataset(
            torch.tensor(X_train_s, dtype=torch.float32, device=device),
            torch.tensor(y_train, dtype=torch.long, device=device),
            torch.tensor(odds_train, dtype=torch.float32, device=device),
        )
        val_ds = TensorDataset(
            torch.tensor(X_val_s, dtype=torch.float32, device=device),
            torch.tensor(y_val, dtype=torch.long, device=device),
            torch.tensor(odds_val, dtype=torch.float32, device=device),
        )
        train_loader = DataLoader(train_ds, batch_size=self.cfg.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.cfg.batch_size)

        best_val_loss = float("inf")
        patience_counter = 0
        best_state = None

        for epoch in range(self.cfg.epochs):
            # λ-schedule: warmup 3 epochs → full λ (only when Kelly enabled)
            if use_kelly and combined is not None:
                if epoch < 3:
                    combined.set_lambda(0.0)
                else:
                    combined.set_lambda(self.cfg.kelly_lambda)

            # Train
            self.model.train()
            train_loss = 0.0
            for xb, yb, ob in train_loader:
                optimizer.zero_grad()
                logits = self.model(xb)
                if use_kelly and combined is not None:
                    loss = combined(logits, yb, odds=ob, y_onehot=_onehot(yb))
                else:
                    loss = ce_only(logits, yb)
                loss.backward()
                optimizer.step()
                train_loss += loss.item() * xb.size(0)
            train_loss /= len(train_ds)

            # Validate (always CE-only for comparability)
            self.model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for xb, yb, _ob in val_loader:
                    logits = self.model(xb)
                    val_loss += ce_only(logits, yb).item() * xb.size(0)
            val_loss /= len(val_ds)

            if val_loss < best_val_loss:
                best_val_loss = val_loss
                best_state = {k: v.clone() for k, v in self.model.state_dict().items()}
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= self.cfg.early_stopping_patience:
                    console.log(f"Early stopping at epoch {epoch}")
                    break

            if epoch % 10 == 0:
                console.log(f"Epoch {epoch}: train={train_loss:.4f} val={val_loss:.4f}")

        # Restore best weights
        if best_state is not None:
            self.model.load_state_dict(best_state)

        # Compute validation predictions for calibrator
        self.model.eval()
        with torch.no_grad():
            X_val_t = torch.tensor(X_val_s, dtype=torch.float32, device=device)
            val_logits = self.model(X_val_t)
            val_probs = torch.softmax(val_logits, dim=1).cpu().numpy()

        if calibrate:
            self.calibrator = ProbabilityCalibrator()
            self.calibrator.fit(val_probs, y_val)

        return {
            "n_train": len(X_train),
            "n_val": len(X_val),
            "n_features": len(self.feature_names),
            "best_val_loss": best_val_loss,
            "val_predictions": val_probs,
            "val_labels": y_val,
        }

    # ───────────────────────── Inference ─────────────────────────

    def predict_logits(self, fixture: Fixture) -> np.ndarray:
        """Return raw pre-softmax logits (shape (3,)) — used by stacking meta-learner."""
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model not trained / loaded.")
        torch, *_ = _import_torch()
        feats = self.feature_builder.features_for_fixture(fixture)
        X = (
            pd.DataFrame([feats])
            .reindex(columns=self.feature_names, fill_value=0.0)
            .fillna(0.0)
            .values
        )
        X_s = self.scaler.transform(X)
        self.model.eval()
        with torch.no_grad():
            logits = self.model(torch.tensor(X_s, dtype=torch.float32))
        return logits.cpu().numpy()[0]

    def predict(self, fixture: Fixture) -> Prediction:
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model not trained / loaded.")

        torch, *_ = _import_torch()
        feats = self.feature_builder.features_for_fixture(fixture)
        X = (
            pd.DataFrame([feats])
            .reindex(columns=self.feature_names, fill_value=0.0)
            .fillna(0.0)
            .values
        )
        X_s = self.scaler.transform(X)

        self.model.eval()
        with torch.no_grad():
            logits = self.model(torch.tensor(X_s, dtype=torch.float32))
            raw_probs = torch.softmax(logits, dim=1).numpy()[0]

        if self.calibrator and self.calibrator.is_fitted:
            probs = self.calibrator.transform(raw_probs.reshape(1, -1))[0]
        else:
            probs = raw_probs

        return Prediction(
            fixture=fixture,
            model_name=f"MLP{'+Cal' if self.calibrator else ''}",
            prob_home=float(probs[OUTCOME_TO_INT["H"]]),
            prob_draw=float(probs[OUTCOME_TO_INT["D"]]),
            prob_away=float(probs[OUTCOME_TO_INT["A"]]),
        )

    # ───────────────────────── Persistence ─────────────────────────

    def save(self, path: Path) -> None:
        """Save PyTorch state dict + scaler + metadata."""
        if self.model is None:
            raise RuntimeError("No model to save — fit first.")
        torch, *_ = _import_torch()

        torch.save(self.model.state_dict(), path)
        meta = {
            "feature_names": self.feature_names,
            "input_dim": len(self.feature_names),
            "cfg": {
                "hidden_dims": self.cfg.hidden_dims,
                "dropout": self.cfg.dropout,
                "batch_norm": self.cfg.batch_norm,
            },
        }
        joblib.dump(self.scaler, path.with_suffix(".scaler.joblib"))
        path.with_suffix(".meta.json").write_text(str(meta))
        if self.calibrator and self.calibrator.is_fitted:
            joblib.dump(self.calibrator, path.with_suffix(".calibrator.joblib"))

    def load(self, path: Path) -> None:
        torch, *_ = _import_torch()

        import ast

        meta_path = path.with_suffix(".meta.json")
        meta = ast.literal_eval(meta_path.read_text())
        self.feature_names = meta["feature_names"]

        # Reconstruct model
        self.model = _build_network(meta["input_dim"], self.cfg)
        # weights_only=False: checkpoints produced by this repo are trusted.
        # Needed for PyTorch >=2.6 compatibility with numpy-pickled state dicts.
        self.model.load_state_dict(torch.load(path, map_location="cpu", weights_only=False))
        self.model.eval()

        self.scaler = joblib.load(path.with_suffix(".scaler.joblib"))
        cal_path = path.with_suffix(".calibrator.joblib")
        if cal_path.exists():
            self.calibrator = joblib.load(cal_path)

    @classmethod
    def for_league(
        cls,
        league_key: str,
        feature_builder: FeatureBuilder,
        purpose: ModelPurpose = "1x2",
    ) -> MLPPredictor | None:
        """Load MLP for league if available, else return None."""
        suffix = artifact_suffix(purpose)
        path = MODELS_DIR / f"mlp_{league_key}{suffix}.pt"
        if not path.exists():
            return None
        inst = cls(feature_builder=feature_builder, purpose=purpose)
        try:
            inst.load(path)
            console.log(f"Loaded MLP: {path.name}")
            return inst
        except Exception as e:
            console.log(f"[red]Failed to load MLP {path.name}: {e}[/red]")
            return None

    def export_onnx(self, path: Path) -> None:
        """Export model to ONNX for production deployment."""
        if self.model is None:
            raise RuntimeError("No model to export.")
        torch, *_ = _import_torch()

        self.model.eval()
        dummy_input = torch.zeros(1, len(self.feature_names), dtype=torch.float32)
        torch.onnx.export(
            self.model,
            dummy_input,
            str(path),
            input_names=["features"],
            output_names=["logits"],
            dynamic_axes={"features": {0: "batch"}, "logits": {0: "batch"}},
            opset_version=17,
        )
        console.log(f"[green]ONNX exported: {path}[/green]")
