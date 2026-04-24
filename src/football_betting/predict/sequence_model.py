"""1D-CNN + Transformer sequence model over team match-history (v0.4).

Architecture (per team branch, shared weights):
    ``(B, T, F_seq) → Conv1d(F_seq → C, k=3) → GELU → Conv1d(C → C, k=3) → GELU
    → (B, T, C) → + learnable positional embedding
    → TransformerEncoder(d=C, heads=tx_heads, layers=tx_layers, pre-norm)
    → masked mean-pool over valid timesteps → (B, C)``

Both team branches are concatenated, dropout-gated, and fed through a
2-layer MLP head producing ``(B, 3)`` H/D/A logits.

Rationale vs. the earlier GRU+Attention head:
    * Conv1d stacks expose *local* temporal patterns (win-streaks,
      regression-to-mean after losses) that a GRU has to learn over many
      timesteps.
    * Transformer self-attention replaces the single-head attention
      pool → multi-head dependencies across the 10-match window.
    * Uses ``resolve_device`` so DirectML (AMD/Intel) works out of the
      box, not CUDA-only.

API is unchanged: ``SequencePredictor.fit / predict / predict_logits /
save / load`` keep the signatures the ensemble code already consumes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from rich.console import Console

from football_betting.config import (
    MODELS_DIR,
    SEQUENCE_CFG,
    ModelPurpose,
    SequenceConfig,
    artifact_suffix,
)
from football_betting.data.models import Fixture, Match, Prediction
from football_betting.features.form import FormTracker
from football_betting.predict.sequence_features import (
    N_SEQ_FEATURES,
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

    C = cfg.conv_channels
    T = cfg.window_t

    class _TeamEncoder(nn.Module):
        """Conv1d×2 → learnable PE → TransformerEncoder. Shared across teams."""

        def __init__(self) -> None:
            super().__init__()
            pad = cfg.conv_kernel // 2
            self.conv1 = nn.Conv1d(N_SEQ_FEATURES, C, kernel_size=cfg.conv_kernel, padding=pad)
            self.conv2 = nn.Conv1d(C, C, kernel_size=cfg.conv_kernel, padding=pad)
            self.act = nn.GELU()
            self.pos_embed = nn.Parameter(torch.zeros(1, T, C))
            nn.init.trunc_normal_(self.pos_embed, std=0.02)
            self.dropout = nn.Dropout(cfg.dropout)

            encoder_layer = nn.TransformerEncoderLayer(
                d_model=C,
                nhead=cfg.tx_heads,
                dim_feedforward=C * cfg.tx_ffn_factor,
                dropout=cfg.dropout,
                activation="gelu",
                batch_first=True,
                norm_first=True,  # pre-norm → stable on DML/CPU
            )
            self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=cfg.tx_layers)
            self.norm = nn.LayerNorm(C)

        def forward(self, seq: Any, mask: Any) -> Any:
            # seq: (B, T, F_seq) → (B, F_seq, T) for Conv1d
            x = seq.transpose(1, 2)
            x = self.act(self.conv1(x))
            x = self.act(self.conv2(x))
            x = x.transpose(1, 2)  # → (B, T, C)
            x = x + self.pos_embed
            x = self.dropout(x)

            # key_padding_mask: True where padding → ignored by attention
            key_padding = mask < 0.5
            # If a row is entirely padded the transformer produces NaNs for
            # that row. Guard by swapping its mask to a single "valid" slot
            # (the last one) and zero out afterwards via ``any_valid``.
            any_valid = (~key_padding).any(dim=1)
            safe_kp = key_padding.clone()
            safe_kp[~any_valid, -1] = False

            x = self.encoder(x, src_key_padding_mask=safe_kp)  # (B, T, C)
            # Masked mean-pool over valid timesteps
            valid_f = (~key_padding).float().unsqueeze(-1)  # (B, T, 1)
            denom = valid_f.sum(dim=1).clamp_min(1.0)
            pooled = (x * valid_f).sum(dim=1) / denom
            pooled = self.norm(pooled)
            # cold-start: zero out rows that had no valid timestep
            pooled = pooled * any_valid.float().unsqueeze(-1)
            return pooled

    class _SeqNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            # Separate encoders per team branch → more capacity without weight
            # sharing quirks (branches see home/away asymmetry via `is_home`).
            self.home_encoder = _TeamEncoder()
            self.away_encoder = _TeamEncoder()
            self.dropout = nn.Dropout(cfg.dropout)
            self.head = nn.Sequential(
                nn.Linear(2 * C, cfg.head_hidden),
                nn.GELU(),
                nn.Dropout(cfg.dropout),
                nn.Linear(cfg.head_hidden, 64),
                nn.GELU(),
                nn.Linear(64, 3),
            )

        def forward(
            self,
            home_seq: Any,
            home_mask: Any,
            away_seq: Any,
            away_mask: Any,
        ) -> Any:
            h_h = self.home_encoder(home_seq, home_mask)
            h_a = self.away_encoder(away_seq, away_mask)
            return self.head(self.dropout(torch.cat([h_h, h_a], dim=-1)))

    return _SeqNet()


@dataclass(slots=True)
class SequencePredictor:
    """1D-CNN + Transformer ensemble member over 10-match team histories."""

    form_tracker: FormTracker = field(default_factory=FormTracker)
    pi_ratings: PiRatings = field(default_factory=PiRatings)
    cfg: SequenceConfig = field(default_factory=lambda: SEQUENCE_CFG)
    model: Any = None
    _device: Any = None
    #: Dual-model split — see ``CatBoostPredictor.purpose``.
    purpose: ModelPurpose = "1x2"

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
            matches,
            self.form_tracker,
            self.pi_ratings,
            window_t=self.cfg.window_t,
            warmup_games=warmup_games,
        )
        if len(y) < 200:
            raise ValueError(f"Too few sequence samples: {len(y)}")

        # Phase C: CLV-aware opening-odds + mask.
        use_shrinkage = bool(getattr(self.cfg, "use_shrinkage_kelly", False))
        opening_np: np.ndarray | None = None
        mask_np: np.ndarray | None = None
        if use_shrinkage:
            from football_betting.predict.kelly_data import (
                collect_opening_odds_and_mask,
                coverage,
            )

            opening_np, mask_np = collect_opening_odds_and_mask(matches, warmup_games=warmup_games)
            if opening_np.shape[0] != len(y):
                raise RuntimeError(
                    "opening/mask rows do not align with sequence dataset rows "
                    f"({opening_np.shape[0]} vs {len(y)})."
                )
            opening_np = np.where(np.isfinite(opening_np), opening_np, 2.0).astype(np.float32)
            cov = coverage(mask_np)
            console.log(f"[cyan]Sequence Kelly-mask coverage: {cov * 100:.1f}%[/cyan]")

        split = int(len(y) * (1 - val_fraction))
        tr = slice(0, split)
        va = slice(split, len(y))

        from football_betting.predict.gpu_utils import resolve_device

        device_pref = os.environ.get("FB_TORCH_DEVICE", "auto")
        device, backend = resolve_device(device_pref)  # type: ignore[arg-type]
        console.log(f"[cyan]SequenceModel training on {backend} ({device})[/cyan]")
        self._device = device
        self.model = _build_network(self.cfg).to(device)

        optimizer = optim.AdamW(
            self.model.parameters(),
            lr=self.cfg.learning_rate,
            weight_decay=self.cfg.weight_decay,
        )
        ce = nn.CrossEntropyLoss()

        shrinkage_loss: Any = None
        lambda_schedule: Any = None
        if use_shrinkage:
            from football_betting.predict.losses import (
                LambdaSchedule,
                ShrinkageCombinedLoss,
            )

            shrinkage_loss = ShrinkageCombinedLoss(
                lam=0.0,
                beta=self.cfg.kelly_beta,
                f_cap=self.cfg.kelly_f_cap,
            )
            lambda_schedule = LambdaSchedule(
                warmup=self.cfg.kelly_warmup_epochs,
                lam_max=self.cfg.kelly_lam_max,
            )
            combined: Any = None
        elif self.cfg.use_kelly_loss:
            from football_betting.predict.losses import CombinedLoss

            combined = CombinedLoss(lam=self.cfg.kelly_lambda)
        else:
            combined = None

        def _to(t: np.ndarray, dtype: Any) -> Any:
            return torch.tensor(t, dtype=dtype, device=device)

        train_tensors = [
            _to(H[tr], torch.float32),
            _to(HM[tr], torch.float32),
            _to(A[tr], torch.float32),
            _to(AM[tr], torch.float32),
            _to(y[tr], torch.long),
            _to(odds[tr], torch.float32),
        ]
        val_tensors = [
            _to(H[va], torch.float32),
            _to(HM[va], torch.float32),
            _to(A[va], torch.float32),
            _to(AM[va], torch.float32),
            _to(y[va], torch.long),
            _to(odds[va], torch.float32),
        ]
        if use_shrinkage and opening_np is not None and mask_np is not None:
            train_tensors.extend([_to(opening_np[tr], torch.float32), _to(mask_np[tr], torch.bool)])
            val_tensors.extend([_to(opening_np[va], torch.float32), _to(mask_np[va], torch.bool)])

        train_ds = TensorDataset(*train_tensors)
        val_ds = TensorDataset(*val_tensors)
        train_loader = DataLoader(train_ds, batch_size=self.cfg.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.cfg.batch_size)

        best_val = float("inf")
        best_growth = -float("inf")
        best_state: Any = None
        for epoch in range(self.cfg.epochs):
            if use_shrinkage and shrinkage_loss is not None and lambda_schedule is not None:
                shrinkage_loss.set_lambda(lambda_schedule(epoch))
            elif combined is not None:
                combined.set_lambda(0.0 if epoch < 3 else self.cfg.kelly_lambda)

            self.model.train()
            tloss = 0.0
            for batch in train_loader:
                if use_shrinkage:
                    hs, hm, as_, am, yb, _ob, op_b, mask_b = batch
                else:
                    hs, hm, as_, am, yb, ob = batch
                optimizer.zero_grad()
                logits = self.model(hs, hm, as_, am)
                yh = nn.functional.one_hot(yb, num_classes=3).float()
                if use_shrinkage and shrinkage_loss is not None:
                    loss = shrinkage_loss(logits, yb, odds=op_b, y_onehot=yh, kelly_mask=mask_b)
                elif combined is not None:
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
            val_growth_accum = 0.0
            val_mask_rows = 0
            with torch.no_grad():
                for batch in val_loader:
                    if use_shrinkage:
                        hs, hm, as_, am, yb, _ob, op_b, mask_b = batch
                    else:
                        hs, hm, as_, am, yb, _ob = batch
                    logits = self.model(hs, hm, as_, am)
                    vloss += ce(logits, yb).item() * hs.size(0)
                    if use_shrinkage:
                        from football_betting.predict.losses import kelly_growth_metric

                        probs = torch.softmax(logits, dim=1)
                        yh = nn.functional.one_hot(yb, num_classes=3).float()
                        g = kelly_growth_metric(
                            probs,
                            op_b,
                            yh,
                            mask=mask_b,
                            f_cap=self.cfg.kelly_f_cap,
                        )
                        m_sum = int(mask_b.sum().item())
                        if m_sum > 0:
                            val_growth_accum += g * m_sum
                            val_mask_rows += m_sum
            vloss /= len(val_ds)
            val_growth = (val_growth_accum / val_mask_rows) if val_mask_rows > 0 else 0.0

            improved = val_growth > best_growth if use_shrinkage else vloss < best_val
            if improved:
                if use_shrinkage:
                    best_growth = val_growth
                    best_val = min(best_val, vloss)
                else:
                    best_val = vloss
                best_state = {k: v.detach().clone() for k, v in self.model.state_dict().items()}

            if epoch % 5 == 0:
                if use_shrinkage:
                    console.log(
                        f"SeqModel epoch {epoch}: train={tloss:.4f} "
                        f"val={vloss:.4f} growth={val_growth:+.5f}"
                    )
                else:
                    console.log(f"SeqModel epoch {epoch}: train={tloss:.4f} val={vloss:.4f}")

        if best_state is not None:
            self.model.load_state_dict(best_state)

        return {
            "n_train": split,
            "n_val": len(y) - split,
            "best_val_loss": best_val,
            "best_val_growth": best_growth if use_shrinkage else None,
            "kelly_mask_coverage": (
                float(mask_np.mean()) if use_shrinkage and mask_np is not None else None
            ),
            "backend": backend,
        }

    # ───────────────────────── Inference ─────────────────────────

    def predict(self, fixture: Fixture) -> Prediction:
        torch, *_ = _import_torch()
        if self.model is None:
            raise RuntimeError("SequenceModel not trained / loaded.")
        hs, hm, as_, am = fixture_tensors(
            fixture.home_team,
            fixture.away_team,
            self.form_tracker,
            self.pi_ratings,
            self.cfg.window_t,
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
            model_name="Sequence1DCNN+Tx",
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
            fixture.home_team,
            fixture.away_team,
            self.form_tracker,
            self.pi_ratings,
            self.cfg.window_t,
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
        cpu_state = {k: v.detach().cpu() for k, v in self.model.state_dict().items()}
        torch.save(cpu_state, path)

    def load(self, path: Path) -> None:
        torch, *_ = _import_torch()
        self.model = _build_network(self.cfg)
        # weights_only=False: checkpoints produced by this repo are trusted.
        # Needed for PyTorch >=2.6 compatibility with numpy-pickled state dicts.
        self.model.load_state_dict(torch.load(path, map_location="cpu", weights_only=False))
        self.model.eval()
        self._device = torch.device("cpu")

    @classmethod
    def for_league(
        cls,
        league_key: str,
        purpose: ModelPurpose = "1x2",
    ) -> SequencePredictor | None:
        """Load Sequence predictor for league if the checkpoint exists."""
        suffix = artifact_suffix(purpose)
        path = MODELS_DIR / f"sequence_{league_key}{suffix}.pt"
        if not path.exists():
            return None
        inst = cls(purpose=purpose)
        try:
            inst.load(path)
            console.log(f"Loaded Sequence: {path.name}")
            return inst
        except Exception as e:  # pragma: no cover - defensive
            console.log(f"[red]Failed to load Sequence {path.name}: {e}[/red]")
            return None
