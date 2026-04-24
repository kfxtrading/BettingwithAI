"""Differentiable Kelly loss — maximises expected log-bankroll growth.

Reference: Kelly (1956). ``f* = (b*p − (1−p)) / b`` with ``b = o − 1``.
The loss is ``E[-log(1 + f* · r)]`` where ``r`` is the realised return.

Clamped to ``[0, f_cap]`` (matches production ``kelly_fraction=0.25``) and
guarded against numerical blow-ups (``p∈[ε, 1−ε]``, ``growth ≥ ε``).

Phase B of [_plans/gpu_kelly_training_plan.md] adds three capabilities:
    * Per-sample reduction on :class:`KellyLoss` (``reduction='none'``) so
      callers can apply a row-level Kelly mask aligned with opening-odds
      coverage from :mod:`football_betting.predict.kelly_data`.
    * :class:`ShrinkageCombinedLoss` — ``CE + λ·Kelly·mask + β·KL(p‖market)``
      to pull posteriors toward the market when information is thin.
    * :class:`LambdaSchedule` — linear warmup for the Kelly weight.
"""

from __future__ import annotations

from typing import Any


def _import_torch() -> Any:
    import torch
    import torch.nn as nn

    return torch, nn


class KellyLoss:
    """Differentiable, clamped Kelly-growth loss.

    Supports two reductions:
        * ``"mean"`` (default) — scalar batch average, back-compatible.
        * ``"none"`` — per-sample ``(N,)`` tensor, required for Kelly masking.
    """

    def __init__(self, f_cap: float = 0.25, eps: float = 1e-6) -> None:
        torch, nn = _import_torch()
        self._nn_module = self._build_module(torch, nn, f_cap, eps)

    def _build_module(self, torch: Any, nn: Any, f_cap: float, eps: float) -> Any:
        class _KellyLossModule(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.f_cap = f_cap
                self.eps = eps

            def forward(
                self,
                probs: Any,
                odds: Any,
                y_onehot: Any,
                reduction: str = "mean",
            ) -> Any:
                p = probs.clamp(self.eps, 1.0 - self.eps)
                b = (odds - 1.0).clamp(min=self.eps)
                f_star = ((b * p - (1.0 - p)) / b).clamp(0.0, self.f_cap)
                r = odds * y_onehot - 1.0
                growth = (1.0 + f_star * r).clamp(min=self.eps)
                per_sample = -(p * torch.log(growth)).sum(dim=1)
                if reduction == "none":
                    return per_sample
                if reduction == "mean":
                    return per_sample.mean()
                raise ValueError(f"Unknown reduction: {reduction!r}")

        return _KellyLossModule()

    def __call__(
        self,
        probs: Any,
        odds: Any,
        y_onehot: Any,
        reduction: str = "mean",
    ) -> Any:
        return self._nn_module(probs, odds, y_onehot, reduction)

    @property
    def module(self) -> Any:
        return self._nn_module


def _masked_kelly_term(
    torch: Any,
    kelly_module: Any,
    probs: Any,
    odds: Any,
    y_onehot: Any,
    mask: Any | None,
) -> Any:
    """Per-sample Kelly, averaged over ``mask==True`` rows only.

    Returns a zero-scalar of the same dtype/device as ``probs`` when no
    row is unmasked — keeps autograd graph intact.
    """
    per_sample = kelly_module(probs, odds, y_onehot, reduction="none")
    if mask is None:
        return per_sample.mean()
    mask_f = mask.to(dtype=per_sample.dtype)
    denom = mask_f.sum().clamp(min=1.0)
    return (per_sample * mask_f).sum() / denom


class CombinedLoss:
    """Weighted sum ``CE + λ · KellyLoss`` with λ-schedule and mask support.

    Phase B extension: ``kelly_mask`` (``(N,)`` bool / float) restricts the
    Kelly gradient to rows that have usable opening odds. Rows with
    ``mask == False`` still contribute to cross-entropy (label is known)
    but are excluded from the Kelly term.
    """

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
        kelly_mask: Any | None = None,
    ) -> Any:
        ce = self._ce(logits, labels)
        if self.lam <= 0.0 or odds is None or y_onehot is None:
            return ce
        probs = self._torch.softmax(logits.float(), dim=1)
        kelly = _masked_kelly_term(
            self._torch,
            self._kelly.module,
            probs,
            odds.float(),
            y_onehot.float(),
            kelly_mask,
        )
        return ce + self.lam * kelly


def _market_probs(torch: Any, odds: Any, eps: float) -> Any:
    """Normalised inverse odds (margin-removed): ``(1/o) / Σ(1/o)``.

    Standard bookmaker-margin removal. Returns a distribution over the
    same 3 outcomes as ``odds``.
    """
    inv = 1.0 / odds.clamp(min=1.0 + eps)
    return inv / inv.sum(dim=1, keepdim=True).clamp(min=eps)


class ShrinkageCombinedLoss:
    """``CE + λ·Kelly·mask + β·KL(p_model ‖ p_market)``.

    * ``CE``: standard multinomial log-loss on true label.
    * ``Kelly term``: per-sample Kelly growth loss on **opening** odds,
      averaged only over ``kelly_mask==True`` rows. Rows without opening
      odds contribute nothing to this term.
    * ``KL term``: shrinks the model posterior toward the market implied
      distribution from the same opening odds. Also masked — rows
      without opening odds have no market reference. KL uses
      ``torch.nn.functional.kl_div(log p_model, p_market, reduction='batchmean')``
      where ``log p_model`` is the log-softmax of ``logits``.

    The KL term is the Bayesian-shrinkage prior that prevents the Kelly
    objective from over-committing on thin-data edges: when the model
    has little evidence the market distribution dominates, when evidence
    accumulates the CE + Kelly terms pull the posterior away.
    """

    def __init__(
        self,
        lam: float = 0.3,
        beta: float = 0.05,
        f_cap: float = 0.25,
        eps: float = 1e-6,
    ) -> None:
        torch, nn = _import_torch()
        self._ce = nn.CrossEntropyLoss()
        self._kelly = KellyLoss(f_cap=f_cap, eps=eps)
        self._torch = torch
        self._nn = nn
        self.lam = lam
        self.beta = beta
        self.eps = eps

    def set_lambda(self, lam: float) -> None:
        self.lam = lam

    def set_beta(self, beta: float) -> None:
        self.beta = beta

    def __call__(
        self,
        logits: Any,
        labels: Any,
        odds: Any | None = None,
        y_onehot: Any | None = None,
        kelly_mask: Any | None = None,
    ) -> Any:
        ce = self._ce(logits, labels)
        if odds is None or y_onehot is None:
            return ce

        torch = self._torch
        # Preserve float64 inputs (needed for gradcheck); only upcast
        # half-precision to float32 for numerical stability.
        logits_f = logits.float() if logits.dtype in (torch.float16, torch.bfloat16) else logits
        odds_f = odds.to(dtype=logits_f.dtype)
        y_f = y_onehot.to(dtype=logits_f.dtype)
        log_probs = torch.log_softmax(logits_f, dim=1)
        probs = log_probs.exp()

        total = ce

        if self.lam > 0.0:
            kelly = _masked_kelly_term(
                torch,
                self._kelly.module,
                probs,
                odds_f,
                y_f,
                kelly_mask,
            )
            total = total + self.lam * kelly

        if self.beta > 0.0:
            market = _market_probs(torch, odds_f, self.eps)
            # KL(p_model ‖ p_market) = Σ p_model · (log p_model − log p_market)
            kl_per_sample = (
                probs.clamp(min=self.eps) * (log_probs - market.clamp(min=self.eps).log())
            ).sum(dim=1)
            if kelly_mask is not None:
                mask_f = kelly_mask.to(dtype=kl_per_sample.dtype)
                denom = mask_f.sum().clamp(min=1.0)
                kl = (kl_per_sample * mask_f).sum() / denom
            else:
                kl = kl_per_sample.mean()
            total = total + self.beta * kl

        return total


class LambdaSchedule:
    """Linear warmup schedule for the Kelly weight.

    ``λ(epoch) = min(epoch / warmup, 1.0) · lam_max``.

    Use during training:

    .. code-block:: python

        schedule = LambdaSchedule(warmup=5, lam_max=0.5)
        for epoch in range(n_epochs):
            loss_fn.set_lambda(schedule(epoch))
            ...

    The warmup prevents the Kelly gradient — which is dominated by
    variance early in training when the posterior is near-uniform —
    from disrupting the CE signal before the backbone stabilises.
    """

    def __init__(self, warmup: int = 5, lam_max: float = 0.5) -> None:
        if warmup < 0:
            raise ValueError(f"warmup must be >= 0, got {warmup}")
        if lam_max < 0.0:
            raise ValueError(f"lam_max must be >= 0, got {lam_max}")
        self.warmup = warmup
        self.lam_max = lam_max

    def __call__(self, epoch: int) -> float:
        if self.warmup == 0:
            return self.lam_max
        frac = min(max(epoch, 0) / float(self.warmup), 1.0)
        return frac * self.lam_max


def kelly_growth_metric(
    probs: Any,
    odds: Any,
    y_onehot: Any,
    mask: Any | None = None,
    f_cap: float = 0.25,
    eps: float = 1e-6,
) -> float:
    """Validation metric: mean realised log-bankroll-growth under clamped Kelly.

    Higher is better (log-growth per bet). Used as early-stopping criterion
    in Phase C training loops. Masked rows are excluded from the average;
    if no row is unmasked the function returns ``0.0`` (neutral).
    """
    torch, _ = _import_torch()
    with torch.no_grad():
        p = probs.clamp(eps, 1.0 - eps)
        b = (odds - 1.0).clamp(min=eps)
        f_star = ((b * p - (1.0 - p)) / b).clamp(0.0, f_cap)
        r = odds * y_onehot - 1.0
        growth = (1.0 + f_star * r).clamp(min=eps)
        # Realised per-sample log-growth on the actual outcome.
        per_sample = (y_onehot * torch.log(growth)).sum(dim=1)
        if mask is None:
            return float(per_sample.mean().item())
        mask_f = mask.to(dtype=per_sample.dtype)
        denom = mask_f.sum().clamp(min=1.0)
        val = (per_sample * mask_f).sum() / denom
        if mask_f.sum().item() == 0.0:
            return 0.0
        return float(val.item())
