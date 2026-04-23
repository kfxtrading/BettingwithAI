"""
FT-Transformer tabular classifier for 1x2 match outcomes (v0.4).

Architecture (minimal FT-Transformer, numerical-only):
    * FeatureTokenizer: each scalar feature xᵢ → tokenᵢ = wᵢ·xᵢ + bᵢ  ∈ ℝ^d
    * Prepend learnable [CLS] token → sequence of length F+1
    * N × TransformerEncoderLayer (MultiheadSelfAttention + FFN, pre-norm)
    * [CLS] embedding → LayerNorm → Linear(d, 3)

Rationale vs. the existing MLP head:
    * Attention captures pairwise feature interactions explicitly, so
      highly correlated tabular features (market_p_*, pi-ratings, xG) can
      re-weight each other at inference time — something the stacked
      Linear+BN blocks in ``mlp_model.py`` cannot represent efficiently.
    * Drop-in API: same ``fit / predict / save / load / for_league``
      signatures as ``MLPPredictor`` so the ensemble code is unchanged
      — a follow-up can route ``EnsembleModel.mlp`` to either head.

This module deliberately does *not* replace the legacy MLP yet; it is an
additive option trainable via ``fb train-tab``.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from rich.console import Console
from sklearn.preprocessing import StandardScaler

from football_betting.config import MODELS_DIR, TAB_TRANSFORMER_CFG, TabTransformerConfig
from football_betting.data.models import Fixture, Match, Prediction
from football_betting.features.builder import FeatureBuilder
from football_betting.predict.calibration import ProbabilityCalibrator

console = Console()

OUTCOME_TO_INT = {"H": 0, "D": 1, "A": 2}
INT_TO_OUTCOME = {v: k for k, v in OUTCOME_TO_INT.items()}


def _import_torch() -> Any:
    try:
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader, TensorDataset

        return torch, nn, optim, DataLoader, TensorDataset
    except ImportError as e:  # pragma: no cover - tested via skip marker
        raise ImportError(
            "PyTorch required for TabTransformer. Install with: pip install torch"
        ) from e


def _build_network(input_dim: int, cfg: TabTransformerConfig) -> Any:
    torch, nn, *_ = _import_torch()

    class FeatureTokenizer(nn.Module):
        """xᵢ ∈ ℝ  →  wᵢ·xᵢ + bᵢ ∈ ℝ^d  for each feature."""

        def __init__(self, n_features: int, d: int) -> None:
            super().__init__()
            self.weight = nn.Parameter(torch.empty(n_features, d))
            self.bias = nn.Parameter(torch.empty(n_features, d))
            # rsqrt(d) init mirrors the FT-Transformer reference impl
            nn.init.uniform_(self.weight, -1.0 / math.sqrt(d), 1.0 / math.sqrt(d))
            nn.init.uniform_(self.bias, -1.0 / math.sqrt(d), 1.0 / math.sqrt(d))

        def forward(self, x: Any) -> Any:
            # x: (B, F) → (B, F, d)
            return x.unsqueeze(-1) * self.weight + self.bias

    class TabTransformerNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.tokenizer = FeatureTokenizer(input_dim, cfg.d_token)
            self.cls = nn.Parameter(torch.zeros(1, 1, cfg.d_token))
            nn.init.normal_(self.cls, std=0.02)

            encoder_layer = nn.TransformerEncoderLayer(
                d_model=cfg.d_token,
                nhead=cfg.n_heads,
                dim_feedforward=cfg.d_token * cfg.ffn_factor,
                dropout=cfg.dropout,
                activation="gelu",
                batch_first=True,
                norm_first=True,  # pre-norm (stable)
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=cfg.n_blocks)
            self.norm = nn.LayerNorm(cfg.d_token)
            self.head = nn.Linear(cfg.d_token, 3)

        def forward(self, x: Any) -> Any:
            tokens = self.tokenizer(x)  # (B, F, d)
            cls = self.cls.expand(tokens.size(0), -1, -1)  # (B, 1, d)
            seq = torch.cat([cls, tokens], dim=1)  # (B, F+1, d)
            seq = self.encoder(seq)
            cls_out = self.norm(seq[:, 0])  # (B, d)
            return self.head(cls_out)  # (B, 3)

    return TabTransformerNet()


@dataclass(slots=True)
class TabTransformerPredictor:
    """FT-Transformer outcome classifier; drop-in compatible with ``MLPPredictor``."""

    feature_builder: FeatureBuilder = field(default_factory=FeatureBuilder)
    cfg: TabTransformerConfig = field(default_factory=lambda: TAB_TRANSFORMER_CFG)
    model: Any = None
    scaler: StandardScaler | None = None
    feature_names: list[str] = field(default_factory=list)
    calibrator: ProbabilityCalibrator | None = None

    # ───────────────────────── Training data ─────────────────────────

    def build_training_data(
        self,
        matches: list[Match],
        warmup_games: int = 100,
    ) -> tuple[pd.DataFrame, np.ndarray]:
        """Chronological no-leak walk identical to ``MLPPredictor``."""
        self.feature_builder.reset()
        rows: list[dict[str, float]] = []
        labels: list[int] = []
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
            self.feature_builder.update_with_match(match)

        df = pd.DataFrame(rows).fillna(0.0)
        self.feature_names = list(df.columns)
        return df, np.array(labels)

    # ───────────────────────── Fit ─────────────────────────

    def fit(
        self,
        matches: list[Match],
        warmup_games: int = 100,
        val_fraction: float = 0.15,
        calibrate: bool = True,
    ) -> dict[str, Any]:
        torch, nn, optim, DataLoader, TensorDataset = _import_torch()
        torch.manual_seed(self.cfg.random_seed)

        X, y = self.build_training_data(matches, warmup_games=warmup_games)
        if len(X) < 200:
            raise ValueError(f"Too few samples: {len(X)}")

        split = int(len(X) * (1 - val_fraction))
        X_train, X_val = X.iloc[:split].values, X.iloc[split:].values
        y_train, y_val = y[:split], y[split:]

        self.scaler = StandardScaler()
        X_train_s = self.scaler.fit_transform(X_train).astype(np.float32)
        X_val_s = self.scaler.transform(X_val).astype(np.float32)

        self.model = _build_network(X_train_s.shape[1], self.cfg)
        from football_betting.predict.gpu_utils import resolve_device

        device_pref = os.environ.get("FB_TORCH_DEVICE", "auto")
        device, backend = resolve_device(device_pref)  # type: ignore[arg-type]
        console.log(f"[cyan]TabTransformer training on {backend} ({device})[/cyan]")
        self.model.to(device)

        optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.cfg.learning_rate,
            weight_decay=self.cfg.weight_decay,
        )
        # Cosine schedule with linear warmup
        warmup_steps = max(1, int(self.cfg.warmup_fraction * self.cfg.epochs))

        def _lr_lambda(epoch: int) -> float:
            if epoch < warmup_steps:
                return (epoch + 1) / warmup_steps
            progress = (epoch - warmup_steps) / max(1, self.cfg.epochs - warmup_steps)
            return 0.5 * (1.0 + math.cos(math.pi * progress))

        scheduler = optim.lr_scheduler.LambdaLR(optimizer, _lr_lambda)
        loss_fn = nn.CrossEntropyLoss(label_smoothing=self.cfg.label_smoothing)

        train_ds = TensorDataset(
            torch.tensor(X_train_s, dtype=torch.float32, device=device),
            torch.tensor(y_train, dtype=torch.long, device=device),
        )
        val_ds = TensorDataset(
            torch.tensor(X_val_s, dtype=torch.float32, device=device),
            torch.tensor(y_val, dtype=torch.long, device=device),
        )
        # DirectML has no pinned-memory path; batch size dominates throughput.
        train_loader = DataLoader(train_ds, batch_size=self.cfg.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.cfg.batch_size)

        best_val = float("inf")
        best_state: dict[str, Any] | None = None
        patience = 0

        for epoch in range(self.cfg.epochs):
            self.model.train()
            train_loss = 0.0
            for xb, yb in train_loader:
                optimizer.zero_grad()
                logits = self.model(xb)
                loss = loss_fn(logits, yb)
                loss.backward()
                optimizer.step()
                train_loss += loss.item() * xb.size(0)
            train_loss /= len(train_ds)
            scheduler.step()

            self.model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for xb, yb in val_loader:
                    logits = self.model(xb)
                    val_loss += loss_fn(logits, yb).item() * xb.size(0)
            val_loss /= len(val_ds)

            if val_loss < best_val - 1e-5:
                best_val = val_loss
                best_state = {k: v.detach().clone() for k, v in self.model.state_dict().items()}
                patience = 0
            else:
                patience += 1
                if patience >= self.cfg.early_stopping_patience:
                    console.log(f"Early stopping at epoch {epoch}")
                    break

            if epoch % 10 == 0:
                console.log(f"Epoch {epoch}: train={train_loss:.4f} val={val_loss:.4f}")

        if best_state is not None:
            self.model.load_state_dict(best_state)

        self.model.eval()
        with torch.no_grad():
            val_logits = self.model(torch.tensor(X_val_s, dtype=torch.float32, device=device))
            val_probs = torch.softmax(val_logits, dim=1).cpu().numpy()

        if calibrate:
            self.calibrator = ProbabilityCalibrator()
            self.calibrator.fit(val_probs, y_val)

        return {
            "n_train": len(X_train),
            "n_val": len(X_val),
            "n_features": len(self.feature_names),
            "best_val_loss": best_val,
            "val_predictions": val_probs,
            "val_labels": y_val,
            "backend": backend,
        }

    # ───────────────────────── Inference ─────────────────────────

    def _forward_np(self, X_s: np.ndarray) -> np.ndarray:
        torch, *_ = _import_torch()
        self.model.eval()
        with torch.no_grad():
            logits = self.model(torch.tensor(X_s, dtype=torch.float32))
            return torch.softmax(logits, dim=1).cpu().numpy()

    def predict(self, fixture: Fixture) -> Prediction:
        if self.model is None or self.scaler is None:
            raise RuntimeError("Model not trained / loaded.")
        feats = self.feature_builder.features_for_fixture(fixture)
        X = (
            pd.DataFrame([feats])
            .reindex(columns=self.feature_names, fill_value=0.0)
            .fillna(0.0)
            .values
        )
        X_s = self.scaler.transform(X).astype(np.float32)
        raw_probs = self._forward_np(X_s)[0]

        if self.calibrator and self.calibrator.is_fitted:
            probs = self.calibrator.transform(raw_probs.reshape(1, -1))[0]
        else:
            probs = raw_probs

        return Prediction(
            fixture=fixture,
            model_name=f"TabTransformer{'+Cal' if self.calibrator else ''}",
            prob_home=float(probs[OUTCOME_TO_INT["H"]]),
            prob_draw=float(probs[OUTCOME_TO_INT["D"]]),
            prob_away=float(probs[OUTCOME_TO_INT["A"]]),
        )

    # ───────────────────────── Persistence ─────────────────────────

    def save(self, path: Path) -> None:
        if self.model is None:
            raise RuntimeError("No model to save — fit first.")
        torch, *_ = _import_torch()
        # Always save on CPU for portability (DML tensors can't be pickled).
        cpu_state = {k: v.detach().cpu() for k, v in self.model.state_dict().items()}
        torch.save(cpu_state, path)
        meta = {
            "feature_names": self.feature_names,
            "input_dim": len(self.feature_names),
            "cfg": {
                "d_token": self.cfg.d_token,
                "n_heads": self.cfg.n_heads,
                "n_blocks": self.cfg.n_blocks,
                "ffn_factor": self.cfg.ffn_factor,
                "dropout": self.cfg.dropout,
            },
        }
        joblib.dump(self.scaler, path.with_suffix(".scaler.joblib"))
        path.with_suffix(".meta.json").write_text(json.dumps(meta))
        if self.calibrator and self.calibrator.is_fitted:
            joblib.dump(self.calibrator, path.with_suffix(".calibrator.joblib"))

    def load(self, path: Path) -> None:
        torch, *_ = _import_torch()
        meta = json.loads(path.with_suffix(".meta.json").read_text())
        self.feature_names = meta["feature_names"]
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
        cls, league_key: str, feature_builder: FeatureBuilder
    ) -> TabTransformerPredictor | None:
        path = MODELS_DIR / f"tabtransformer_{league_key}.pt"
        if not path.exists():
            return None
        inst = cls(feature_builder=feature_builder)
        try:
            inst.load(path)
            console.log(f"Loaded TabTransformer: {path.name}")
            return inst
        except Exception as e:  # pragma: no cover - defensive
            console.log(f"[red]Failed to load TabTransformer {path.name}: {e}[/red]")
            return None
