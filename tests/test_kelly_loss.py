"""KellyLoss + CombinedLoss — gradients, clamping, numerical guards."""
from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from football_betting.predict.losses import CombinedLoss, KellyLoss  # noqa: E402


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
