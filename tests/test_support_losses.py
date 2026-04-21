"""Tests for the Supervised Contrastive loss helper (M3)."""
from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from football_betting.support.losses import SupConLoss, sup_con_loss  # noqa: E402


def test_sup_con_loss_shape_and_non_negative() -> None:
    feats = torch.randn(8, 16, requires_grad=True)
    labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3])
    loss = sup_con_loss(feats, labels, temperature=0.07)
    assert loss.dim() == 0
    assert float(loss.item()) >= 0.0


def test_sup_con_loss_backward() -> None:
    feats = torch.randn(6, 8, requires_grad=True)
    labels = torch.tensor([0, 0, 1, 1, 2, 2])
    loss = sup_con_loss(feats, labels)
    loss.backward()
    assert feats.grad is not None
    assert feats.grad.shape == feats.shape


def test_sup_con_loss_rejects_bad_shapes() -> None:
    with pytest.raises(ValueError):
        sup_con_loss(torch.randn(4), torch.tensor([0, 1, 0, 1]))
    with pytest.raises(ValueError):
        sup_con_loss(torch.randn(4, 8), torch.tensor([[0], [1], [0], [1]]))
    with pytest.raises(ValueError):
        sup_con_loss(torch.randn(4, 8), torch.tensor([0, 1, 0]))


def test_sup_con_loss_without_positives_returns_zero() -> None:
    feats = torch.randn(4, 8, requires_grad=True)
    labels = torch.tensor([0, 1, 2, 3])  # no class has a pair
    loss = sup_con_loss(feats, labels)
    assert float(loss.item()) == 0.0


def test_sup_con_loss_singleton_batch_zero() -> None:
    feats = torch.randn(1, 8, requires_grad=True)
    labels = torch.tensor([0])
    loss = sup_con_loss(feats, labels)
    assert float(loss.item()) == 0.0


def test_supcon_loss_class_callable() -> None:
    feats = torch.randn(4, 8, requires_grad=True)
    labels = torch.tensor([0, 0, 1, 1])
    fn = SupConLoss(temperature=0.1)
    a = fn(feats, labels)
    b = sup_con_loss(feats, labels, temperature=0.1)
    assert pytest.approx(float(a.item()), rel=1e-6) == float(b.item())


def test_sup_con_loss_pulls_same_class_together() -> None:
    """Loss should decrease as same-class features cluster."""
    labels = torch.tensor([0, 0, 1, 1])
    scattered = torch.randn(4, 8) * 2.0
    loss_scattered = sup_con_loss(scattered, labels).item()

    clustered = torch.tensor(
        [
            [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [1.0, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 1.0, 0.1, 0.0, 0.0],
        ],
    )
    loss_clustered = sup_con_loss(clustered, labels).item()
    assert loss_clustered < loss_scattered
