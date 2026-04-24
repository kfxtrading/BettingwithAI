"""KellyLoss + CombinedLoss — gradients, clamping, numerical guards."""

from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from football_betting.predict.losses import (  # noqa: E402
    CombinedLoss,
    KellyLoss,
    LambdaSchedule,
    ShrinkageCombinedLoss,
)


def test_kelly_loss_forward_scalar():
    loss = KellyLoss(f_cap=0.25)
    probs = torch.tensor([[0.5, 0.3, 0.2]], requires_grad=True)
    odds = torch.tensor([[2.0, 3.5, 4.0]])
    y = torch.tensor([[1.0, 0.0, 0.0]])
    val = loss(probs, odds, y)
    assert val.ndim == 0
    assert torch.isfinite(val)


def test_kelly_loss_gradient_flows():
    loss = KellyLoss(f_cap=0.25)
    probs = torch.tensor([[0.5, 0.3, 0.2]], requires_grad=True)
    odds = torch.tensor([[2.0, 3.5, 4.0]])
    y = torch.tensor([[1.0, 0.0, 0.0]])
    val = loss(probs, odds, y)
    val.backward()
    assert probs.grad is not None
    assert torch.isfinite(probs.grad).all()


def test_kelly_loss_clamps_extremes():
    loss = KellyLoss(f_cap=0.25, eps=1e-6)
    # degenerate probs at 0/1 boundary — must not produce nan/inf
    probs = torch.tensor([[1.0 - 1e-9, 1e-9, 1e-9]], requires_grad=True)
    odds = torch.tensor([[1.01, 1.01, 1.01]])
    y = torch.tensor([[1.0, 0.0, 0.0]])
    val = loss(probs, odds, y)
    assert torch.isfinite(val)


def test_combined_loss_ce_only_when_lambda_zero():
    ce_only = CombinedLoss(lam=0.0)
    logits = torch.tensor([[1.0, 0.2, -0.5]], requires_grad=True)
    labels = torch.tensor([0])
    odds = torch.tensor([[2.0, 3.5, 4.0]])
    yh = torch.tensor([[1.0, 0.0, 0.0]])
    val = ce_only(logits, labels, odds=odds, y_onehot=yh)
    assert torch.isfinite(val)


def test_combined_loss_lambda_setter():
    combo = CombinedLoss(lam=0.3)
    combo.set_lambda(0.5)
    assert combo.lam == 0.5


def test_combined_loss_with_kelly_differs_from_ce():
    combo = CombinedLoss(lam=0.5)
    logits = torch.tensor([[1.0, 0.2, -0.5]], requires_grad=True)
    labels = torch.tensor([0])
    odds = torch.tensor([[2.0, 3.5, 4.0]])
    yh = torch.tensor([[1.0, 0.0, 0.0]])
    with_kelly = combo(logits, labels, odds=odds, y_onehot=yh).item()

    combo.set_lambda(0.0)
    ce_only = combo(logits, labels, odds=odds, y_onehot=yh).item()
    assert with_kelly != pytest.approx(ce_only)


# ────────────────────────── Phase B additions ──────────────────────────


def test_kelly_loss_reduction_none_shape():
    loss = KellyLoss(f_cap=0.25)
    probs = torch.tensor([[0.5, 0.3, 0.2], [0.1, 0.8, 0.1]], requires_grad=True)
    odds = torch.tensor([[2.0, 3.5, 4.0], [5.0, 1.5, 3.0]])
    y = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    per_sample = loss(probs, odds, y, reduction="none")
    assert per_sample.shape == (2,)
    # Mean reduction must match per-sample mean
    scalar = loss(probs, odds, y, reduction="mean")
    assert torch.allclose(per_sample.mean(), scalar)


def test_kelly_loss_unknown_reduction_raises():
    loss = KellyLoss()
    probs = torch.tensor([[0.5, 0.3, 0.2]])
    odds = torch.tensor([[2.0, 3.5, 4.0]])
    y = torch.tensor([[1.0, 0.0, 0.0]])
    with pytest.raises(ValueError, match="Unknown reduction"):
        loss(probs, odds, y, reduction="sum")


def test_combined_loss_mask_excludes_rows_from_kelly():
    """When a row is masked out, Kelly term must equal the unmasked
    average over remaining rows — not the full-batch average."""
    combo_full = CombinedLoss(lam=0.5)
    combo_masked = CombinedLoss(lam=0.5)
    logits = torch.tensor([[1.0, 0.2, -0.5], [0.1, 0.9, 0.0]], requires_grad=True)
    labels = torch.tensor([0, 1])
    odds = torch.tensor([[2.0, 3.5, 4.0], [5.0, 1.5, 3.0]])
    yh = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])

    # Mask-only-first = Kelly computed only on row 0
    mask = torch.tensor([True, False])
    masked = combo_masked(logits, labels, odds=odds, y_onehot=yh, kelly_mask=mask)

    # Reference: CombinedLoss with only row 0 in the Kelly term requires
    # computing CE over the full batch + Kelly over just row 0. Easiest
    # check: masked loss differs from unmasked, and all-True mask equals
    # unmasked.
    full = combo_full(logits, labels, odds=odds, y_onehot=yh)
    all_true = combo_full(
        logits,
        labels,
        odds=odds,
        y_onehot=yh,
        kelly_mask=torch.tensor([True, True]),
    )
    assert torch.allclose(all_true, full)
    assert not torch.allclose(masked, full)


def test_combined_loss_all_masked_equals_ce():
    """When every row is masked out, the Kelly contribution must be zero
    and the total must equal plain cross-entropy."""
    combo = CombinedLoss(lam=0.5)
    logits = torch.tensor([[1.0, 0.2, -0.5]], requires_grad=True)
    labels = torch.tensor([0])
    odds = torch.tensor([[2.0, 3.5, 4.0]])
    yh = torch.tensor([[1.0, 0.0, 0.0]])

    ce_only = torch.nn.functional.cross_entropy(logits, labels)
    masked = combo(
        logits,
        labels,
        odds=odds,
        y_onehot=yh,
        kelly_mask=torch.tensor([False]),
    )
    assert torch.allclose(masked, ce_only)


def test_combined_loss_mask_preserves_gradient_flow():
    combo = CombinedLoss(lam=0.5)
    logits = torch.tensor([[1.0, 0.2, -0.5], [0.1, 0.9, 0.0]], requires_grad=True)
    labels = torch.tensor([0, 1])
    odds = torch.tensor([[2.0, 3.5, 4.0], [5.0, 1.5, 3.0]])
    yh = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    mask = torch.tensor([True, False])
    loss = combo(logits, labels, odds=odds, y_onehot=yh, kelly_mask=mask)
    loss.backward()
    assert logits.grad is not None
    assert torch.isfinite(logits.grad).all()


def test_shrinkage_loss_reduces_to_ce_when_lambda_and_beta_zero():
    loss = ShrinkageCombinedLoss(lam=0.0, beta=0.0)
    logits = torch.tensor([[1.0, 0.2, -0.5]], requires_grad=True)
    labels = torch.tensor([0])
    odds = torch.tensor([[2.0, 3.5, 4.0]])
    yh = torch.tensor([[1.0, 0.0, 0.0]])
    val = loss(logits, labels, odds=odds, y_onehot=yh)
    ce_ref = torch.nn.functional.cross_entropy(logits, labels)
    assert torch.allclose(val, ce_ref)


def test_shrinkage_kl_pulls_posterior_toward_market():
    """The KL term must be non-negative and vanish when the posterior
    coincides with the market-implied distribution."""
    # Market odds imply probs roughly (1/2, 1/3.5, 1/4) normalised.
    odds = torch.tensor([[2.0, 3.5, 4.0]])
    inv = 1.0 / odds
    market = inv / inv.sum(dim=1, keepdim=True)
    labels = torch.tensor([0])
    yh = torch.tensor([[1.0, 0.0, 0.0]])

    # Same logits, two losses: beta=0 (CE-only) vs beta=1 (CE + KL).
    # KL is non-negative, so beta=1 must be >= beta=0 at identical logits.
    far_logits = torch.tensor([[5.0, -5.0, -5.0]], requires_grad=False)
    loss_ce = ShrinkageCombinedLoss(lam=0.0, beta=0.0)
    loss_kl = ShrinkageCombinedLoss(lam=0.0, beta=1.0)
    v_ce = loss_ce(far_logits, labels, odds=odds, y_onehot=yh).item()
    v_kl = loss_kl(far_logits, labels, odds=odds, y_onehot=yh).item()
    assert v_kl > v_ce  # KL adds strictly positive mass far from market

    # When posterior == market, KL ≈ 0 → beta contribution vanishes.
    aligned_logits = market.log().clone().detach()
    v_ce_aligned = loss_ce(aligned_logits, labels, odds=odds, y_onehot=yh).item()
    v_kl_aligned = loss_kl(aligned_logits, labels, odds=odds, y_onehot=yh).item()
    assert v_kl_aligned == pytest.approx(v_ce_aligned, abs=1e-5)


def test_shrinkage_mask_disables_both_kelly_and_kl():
    loss = ShrinkageCombinedLoss(lam=0.5, beta=0.5)
    logits = torch.tensor([[1.0, 0.2, -0.5]], requires_grad=True)
    labels = torch.tensor([0])
    odds = torch.tensor([[2.0, 3.5, 4.0]])
    yh = torch.tensor([[1.0, 0.0, 0.0]])
    all_masked = loss(
        logits,
        labels,
        odds=odds,
        y_onehot=yh,
        kelly_mask=torch.tensor([False]),
    )
    ce_ref = torch.nn.functional.cross_entropy(logits, labels)
    assert torch.allclose(all_masked, ce_ref)


def test_shrinkage_gradcheck_kl_branch_double_precision():
    """gradcheck on the KL + CE branch (lam=0): this branch is fully
    smooth. The Kelly branch uses ``clamp`` at ``f_star=0`` and
    ``growth=eps`` boundaries, so finite-difference gradients are only
    reliable when the batch stays strictly inside the smooth region. For
    robust CI, gradcheck the KL branch only — the Kelly branch is
    covered by forward-value and gradient-flow tests elsewhere."""
    loss = ShrinkageCombinedLoss(lam=0.0, beta=0.2)
    logits = torch.tensor(
        [[0.4, 0.1, -0.2], [0.0, 0.3, 0.2]],
        dtype=torch.float64,
        requires_grad=True,
    )
    labels = torch.tensor([0, 1])
    odds = torch.tensor([[2.0, 3.5, 4.0], [5.0, 1.8, 3.0]], dtype=torch.float64)
    yh = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=torch.float64)
    mask = torch.tensor([True, True])

    def fn(lg: torch.Tensor) -> torch.Tensor:
        return loss(lg, labels, odds=odds, y_onehot=yh, kelly_mask=mask)

    assert torch.autograd.gradcheck(fn, (logits,), eps=1e-6, atol=1e-5)


def test_lambda_schedule_linear_warmup():
    sched = LambdaSchedule(warmup=5, lam_max=0.5)
    assert sched(0) == pytest.approx(0.0)
    assert sched(1) == pytest.approx(0.1)
    assert sched(5) == pytest.approx(0.5)
    assert sched(10) == pytest.approx(0.5)  # clamped
    assert sched(-1) == pytest.approx(0.0)  # negative clamped


def test_lambda_schedule_zero_warmup_is_constant():
    sched = LambdaSchedule(warmup=0, lam_max=0.5)
    assert sched(0) == pytest.approx(0.5)
    assert sched(100) == pytest.approx(0.5)


def test_lambda_schedule_rejects_negative():
    with pytest.raises(ValueError):
        LambdaSchedule(warmup=-1, lam_max=0.5)
    with pytest.raises(ValueError):
        LambdaSchedule(warmup=5, lam_max=-0.1)
