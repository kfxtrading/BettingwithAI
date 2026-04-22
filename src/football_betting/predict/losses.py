"""Differentiable Kelly loss — maximises expected log-bankroll growth.

Reference: Kelly (1956). ``f* = (b*p − (1−p)) / b`` with ``b = o − 1``.
The loss is ``E[-log(1 + f* · r)]`` where ``r`` is the realised return.

Clamped to ``[0, f_cap]`` (matches production ``kelly_fraction=0.25``) and
guarded against numerical blow-ups (``p∈[ε, 1−ε]``, ``growth ≥ ε``).
"""
from __future__ import annotations

from typing import Any


def _import_torch() -> Any:
    import torch
    import torch.nn as nn
    return torch, nn


class KellyLoss:
    """Differentiable, clamped Kelly-growth loss."""

    def __init__(self, f_cap: float = 0.25, eps: float = 1e-6) -> None:
        torch, nn = _import_torch()
        self._nn_module = self._build_module(torch, nn, f_cap, eps)

    def _build_module(self, torch: Any, nn: Any, f_cap: float, eps: float) -> Any:
        class _KellyLossModule(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.f_cap = f_cap
                self.eps = eps

            def forward(self, probs: Any, odds: Any, y_onehot: Any) -> Any:
                p = probs.clamp(self.eps, 1.0 - self.eps)
                b = (odds - 1.0).clamp(min=self.eps)
                f_star = ((b * p - (1.0 - p)) / b).clamp(0.0, self.f_cap)
                r = odds * y_onehot - 1.0
                growth = (1.0 + f_star * r).clamp(min=self.eps)
                return -(p * torch.log(growth)).sum(dim=1).mean()

        return _KellyLossModule()

    def __call__(self, probs: Any, odds: Any, y_onehot: Any) -> Any:
        return self._nn_module(probs, odds, y_onehot)

    @property
    def module(self) -> Any:
        return self._nn_module


class CombinedLoss:
    """Weighted sum ``CE + λ · KellyLoss`` with λ-schedule support."""

    def __init__(self, lam: float = 0.3, f_cap: float = 0.25, eps: float = 1e-6) -> None:
        torch, nn = _import_torch()
        self._ce = nn.CrossEntropyLoss()
        self._kelly = KellyLoss(f_cap=f_cap, eps=eps)
        self.lam = lam
        self._torch = torch

    def set_lambda(self, lam: float) -> None:
        self.lam = lam

    def __call__(
        self,
        logits: Any,
        labels: Any,
        odds: Any | None = None,
        y_onehot: Any | None = None,
    ) -> Any:
        ce = self._ce(logits, labels)
        if self.lam <= 0.0 or odds is None or y_onehot is None:
            return ce
        probs = self._torch.softmax(logits.float(), dim=1)
        kelly = self._kelly(probs, odds.float(), y_onehot.float())
        return ce + self.lam * kelly
