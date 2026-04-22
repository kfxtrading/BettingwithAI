"""GRU+Attention sequence model over team match-history (v0.4).

Input:  (B, 2, T, F_seq) — home+away team histories
Output: logits (B, 3) for H/D/A
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from rich.console import Console

from football_betting.config import SEQUENCE_CFG, SequenceConfig
from football_betting.data.models import Fixture, Match, Prediction
from football_betting.features.form import FormTracker
from football_betting.predict.sequence_features import (
    build_dataset,
    fixture_tensors,
)
from football_betting.rating.pi_ratings import PiRatings

console = Console()

OUTCOME_TO_INT = {"H": 0, "D": 1, "A": 2}


def _import_torch() -> Any:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    return torch, nn, optim, DataLoader, TensorDataset


def _build_network(cfg: SequenceConfig) -> Any:
    torch, nn, *_ = _import_torch()

    class _SeqNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.gru = nn.GRU(
                input_size=N_SEQ_FEATURES,
                hidden_size=cfg.gru_hidden,
                num_layers=cfg.gru_layers,
                batch_first=True,
                bidirectional=cfg.bidirectional,
                dropout=cfg.dropout if cfg.gru_layers > 1 else 0.0,
            )
            out_dim = cfg.gru_hidden * (2 if cfg.bidirectional else 1)
            self.attn = nn.Linear(out_dim, 1)
            self.dropout = nn.Dropout(cfg.dropout)
            self.head = nn.Sequential(
                nn.Linear(out_dim * 2, 128),
                nn.ReLU(),
                nn.Dropout(cfg.dropout),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, 3),
            )

        def _encode(self, seq: Any, mask: Any) -> Any:
            h, _ = self.gru(seq)  # (B, T, H*dir)
            scores = self.attn(h).squeeze(-1)  # (B, T)
            # mask padding (mask==0 → -inf)
            scores = scores.masked_fill(mask < 0.5, float("-inf"))
            # if ALL timesteps masked (cold start), fall back to zero vector
            any_valid = (mask.sum(dim=1) > 0).unsqueeze(-1)
            weights = torch.softmax(scores, dim=1).unsqueeze(-1)
            weights = torch.nan_to_num(weights, nan=0.0)
            pooled = (h * weights).sum(dim=1)
            return pooled * any_valid.float()

        def forward(self, home_seq: Any, home_mask: Any, away_seq: Any, away_mask: Any) -> Any:
            h_h = self._encode(home_seq, home_mask)
            h_a = self._encode(away_seq, away_mask)
            return self.head(self.dropout(torch.cat([h_h, h_a], dim=-1)))

    return _SeqNet()


@dataclass(slots=True)
class SequencePredictor:
    """GRU+Attention ensemble member."""

    form_tracker: FormTracker = field(default_factory=FormTracker)
    pi_ratings: PiRatings = field(default_factory=PiRatings)
    cfg: SequenceConfig = field(default_factory=lambda: SEQUENCE_CFG)
    model: Any = None
    _device: Any = None

    # ───────────────────────── Training ─────────────────────────

    def fit(
        self,
        matches: list[Match],
        warmup_games: int = 100,
        val_fraction: float = 0.15,
    ) -> dict[str, Any]:
        torch, nn, optim, DataLoader, TensorDataset = _import_torch()  # noqa: N806
        torch.manual_seed(self.cfg.random_seed)

        # Reset trackers for clean walk
        self.form_tracker = FormTracker()
        self.pi_ratings = PiRatings()

        H, HM, A, AM, y, odds = build_dataset(  # noqa: N806
            matches, self.form_tracker, self.pi_ratings,
            window_t=self.cfg.window_t, warmup_games=warmup_games,
        )
        if len(y) < 200:
            raise ValueError(f"Too few sequence samples: {len(y)}")

        split = int(len(y) * (1 - val_fraction))
        tr = slice(0, split)
        va = slice(split, len(y))

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._device = device
        self.model = _build_network(self.cfg).to(device)

        optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.cfg.learning_rate,
            weight_decay=self.cfg.weight_decay,
        )
        ce = nn.CrossEntropyLoss()

        if self.cfg.use_kelly_loss:
            from football_betting.predict.losses import CombinedLoss
            combined: Any = CombinedLoss(lam=self.cfg.kelly_lambda)
        else:
            combined = None

        def _to(t: np.ndarray, dtype: Any) -> Any:
            return torch.tensor(t, dtype=dtype, device=device)

        train_ds = TensorDataset(
            _to(H[tr], torch.float32), _to(HM[tr], torch.float32),
            _to(A[tr], torch.float32), _to(AM[tr], torch.float32),
            _to(y[tr], torch.long), _to(odds[tr], torch.float32),
        )
        val_ds = TensorDataset(
            _to(H[va], torch.float32), _to(HM[va], torch.float32),
            _to(A[va], torch.float32), _to(AM[va], torch.float32),
            _to(y[va], torch.long), _to(odds[va], torch.float32),
        )
        train_loader = DataLoader(train_ds, batch_size=self.cfg.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.cfg.batch_size)

        best_val = float("inf")
        best_state: Any = None
        for epoch in range(self.cfg.epochs):
            if combined is not None:
                combined.set_lambda(0.0 if epoch < 3 else self.cfg.kelly_lambda)

            self.model.train()
            tloss = 0.0
            for hs, hm, as_, am, yb, ob in train_loader:
                optimizer.zero_grad()
                logits = self.model(hs, hm, as_, am)
                if combined is not None:
                    yh = nn.functional.one_hot(yb, num_classes=3).float()
                    loss = combined(logits, yb, odds=ob, y_onehot=yh)
                else:
                    loss = ce(logits, yb)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                tloss += loss.item() * hs.size(0)
            tloss /= len(train_ds)

            self.model.eval()
            vloss = 0.0
            with torch.no_grad():
                for hs, hm, as_, am, yb, _ob in val_loader:
                    logits = self.model(hs, hm, as_, am)
                    vloss += ce(logits, yb).item() * hs.size(0)
            vloss /= len(val_ds)

            if vloss < best_val:
                best_val = vloss
                best_state = {k: v.clone() for k, v in self.model.state_dict().items()}

            if epoch % 5 == 0:
                console.log(f"SeqModel epoch {epoch}: train={tloss:.4f} val={vloss:.4f}")

        if best_state is not None:
            self.model.load_state_dict(best_state)

        return {"n_train": split, "n_val": len(y) - split, "best_val_loss": best_val}

    # ───────────────────────── Inference ─────────────────────────

    def predict(self, fixture: Fixture) -> Prediction:
        torch, *_ = _import_torch()
        if self.model is None:
            raise RuntimeError("SequenceModel not trained / loaded.")
        hs, hm, as_, am = fixture_tensors(
            fixture.home_team, fixture.away_team,
            self.form_tracker, self.pi_ratings, self.cfg.window_t,
        )
        device = self._device or torch.device("cpu")
        self.model.eval()
        with torch.no_grad():
            logits = self.model(
                torch.tensor(hs[None], dtype=torch.float32, device=device),
                torch.tensor(hm[None], dtype=torch.float32, device=device),
                torch.tensor(as_[None], dtype=torch.float32, device=device),
                torch.tensor(am[None], dtype=torch.float32, device=device),
            )
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
        return Prediction(
            fixture=fixture,
            model_name="SequenceGRU",
            prob_home=float(probs[0]),
            prob_draw=float(probs[1]),
            prob_away=float(probs[2]),
        )

    def predict_logits(self, fixture: Fixture) -> np.ndarray:
        """Raw (3,) pre-softmax logits for stacking."""
        torch, *_ = _import_torch()
        if self.model is None:
            raise RuntimeError("SequenceModel not trained / loaded.")
        hs, hm, as_, am = fixture_tensors(
            fixture.home_team, fixture.away_team,
            self.form_tracker, self.pi_ratings, self.cfg.window_t,
        )
        device = self._device or torch.device("cpu")
        self.model.eval()
        with torch.no_grad():
            logits = self.model(
                torch.tensor(hs[None], dtype=torch.float32, device=device),
                torch.tensor(hm[None], dtype=torch.float32, device=device),
                torch.tensor(as_[None], dtype=torch.float32, device=device),
                torch.tensor(am[None], dtype=torch.float32, device=device),
            )
        return logits.cpu().numpy()[0]

    # ───────────────────────── Persistence ─────────────────────────

    def save(self, path: Path) -> None:
        torch, *_ = _import_torch()
        if self.model is None:
            raise RuntimeError("No model to save.")
        torch.save(self.model.state_dict(), path)

    def load(self, path: Path) -> None:
        torch, *_ = _import_torch()
        self.model = _build_network(self.cfg)
        self.model.load_state_dict(torch.load(path, map_location="cpu"))
        self.model.eval()
        self._device = torch.device("cpu")
