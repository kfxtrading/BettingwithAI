"""Level-2 Stacking meta-learner.

Inputs per match (default, 19 features):
  * 4 member probs × 3 classes = 12
  * 4 member entropies           = 4
  * 3 power-devigged market probs = 3
  = 19

Members: CatBoost, Poisson, MLP, Sequence — any subset is allowed.
When a member is missing, its 3 probs are set to the uniform (1/3, 1/3, 1/3)
and its entropy to ``log(3)``. The meta-feature vector is thus
always stable in shape.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np

from football_betting.betting.margin import remove_margin
from football_betting.config import STACKING_CFG, StackingConfig
from football_betting.data.models import Fixture, Prediction

OUTCOME_TO_INT = {"H": 0, "D": 1, "A": 2}
N_META_FEATURES = 4 * 3 + 4 + 3  # 19

UNIFORM_PROB = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
UNIFORM_ENTROPY = math.log(3.0)


def _entropy(p: tuple[float, float, float]) -> float:
    s = 0.0
    for q in p:
        if q > 1e-12:
            s -= q * math.log(q)
    return s


def _devig_triple(odds: tuple[float, float, float] | None) -> tuple[float, float, float]:
    if odds is None or any(o <= 1.0 for o in odds):
        return UNIFORM_PROB
    return remove_margin(odds[0], odds[1], odds[2], method="power")


def build_meta_row(
    cb: tuple[float, float, float] | None,
    po: tuple[float, float, float] | None,
    mlp: tuple[float, float, float] | None,
    seq: tuple[float, float, float] | None,
    market_odds: tuple[float, float, float] | None,
) -> np.ndarray:
    parts: list[float] = []
    for p in (cb, po, mlp, seq):
        triple = p if p is not None else UNIFORM_PROB
        parts.extend(triple)
    for p in (cb, po, mlp, seq):
        parts.append(_entropy(p) if p is not None else UNIFORM_ENTROPY)
    parts.extend(_devig_triple(market_odds))
    return np.asarray(parts, dtype=np.float32)


@dataclass(slots=True)
class StackingEnsemble:
    """LogReg (default) or small NN meta-learner on top of L1 member probs."""

    cfg: StackingConfig = field(default_factory=lambda: STACKING_CFG)
    meta: Any = None          # sklearn model or torch.nn.Module
    _meta_kind: Literal["lr", "nn"] = "lr"

    # ───────────────────────── Fit ─────────────────────────

    def fit(self, X_meta: np.ndarray, y: np.ndarray) -> None:  # noqa: N803
        """Fit the meta-learner.

        X_meta : (N, N_META_FEATURES) float32
        y      : (N,) int in {0,1,2}
        """
        if X_meta.shape[1] != N_META_FEATURES:
            raise ValueError(
                f"X_meta must have {N_META_FEATURES} features, got {X_meta.shape[1]}"
            )
        if self.cfg.meta_learner == "lr":
            self._fit_lr(X_meta, y)
        else:
            self._fit_nn(X_meta, y)

    def _fit_lr(self, X: np.ndarray, y: np.ndarray) -> None:  # noqa: N803
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(
            C=self.cfg.lr_C,
            max_iter=self.cfg.lr_max_iter,
            multi_class="multinomial",
            solver="lbfgs",
            random_state=self.cfg.random_seed,
        )
        model.fit(X, y)
        self.meta = model
        self._meta_kind = "lr"

    def _fit_nn(self, X: np.ndarray, y: np.ndarray) -> None:  # noqa: N803
        import torch
        import torch.nn as nn
        import torch.optim as optim
        torch.manual_seed(self.cfg.random_seed)

        net = nn.Sequential(
            nn.Linear(N_META_FEATURES, self.cfg.nn_hidden),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(self.cfg.nn_hidden, 3),
        )
        opt = optim.Adam(net.parameters(), lr=self.cfg.nn_lr)
        ce = nn.CrossEntropyLoss()

        xt = torch.tensor(X, dtype=torch.float32)
        yt = torch.tensor(y, dtype=torch.long)
        for _ in range(self.cfg.nn_epochs):
            net.train()
            opt.zero_grad()
            logits = net(xt)
            loss = ce(logits, yt)
            loss.backward()
            opt.step()

        self.meta = net
        self._meta_kind = "nn"

    # ───────────────────────── Predict ─────────────────────────

    def predict_proba(self, X_meta: np.ndarray) -> np.ndarray:  # noqa: N803
        if self.meta is None:
            raise RuntimeError("StackingEnsemble.fit() not called yet.")
        if self._meta_kind == "lr":
            return np.asarray(self.meta.predict_proba(X_meta), dtype=np.float32)
        import torch
        self.meta.eval()
        with torch.no_grad():
            logits = self.meta(torch.tensor(X_meta, dtype=torch.float32))
            probs = torch.softmax(logits, dim=1).numpy()
        return probs.astype(np.float32)

    def predict_one(
        self,
        fixture: Fixture,
        cb_probs: tuple[float, float, float] | None,
        po_probs: tuple[float, float, float] | None,
        mlp_probs: tuple[float, float, float] | None,
        seq_probs: tuple[float, float, float] | None,
    ) -> Prediction:
        odds = None
        if fixture.odds:
            odds = (fixture.odds.home, fixture.odds.draw, fixture.odds.away)
        row = build_meta_row(cb_probs, po_probs, mlp_probs, seq_probs, odds)
        probs = self.predict_proba(row[None, :])[0]
        return Prediction(
            fixture=fixture,
            model_name=f"Stacking({self._meta_kind})",
            prob_home=float(probs[0]),
            prob_draw=float(probs[1]),
            prob_away=float(probs[2]),
        )


__all__ = ["StackingEnsemble", "build_meta_row", "N_META_FEATURES"]
