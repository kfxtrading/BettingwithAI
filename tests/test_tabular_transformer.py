"""Tests for the FT-Transformer tabular head.

Focus on structural correctness (forward shape, determinism, persistence)
rather than end-to-end training quality — the latter is covered by the
league-level backtest suite.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from football_betting.config import TabTransformerConfig
from football_betting.predict.tabular_transformer import _build_network


def test_ft_transformer_forward_shape() -> None:
    cfg = TabTransformerConfig(d_token=32, n_heads=4, n_blocks=2, dropout=0.0)
    net = _build_network(input_dim=20, cfg=cfg)
    net.eval()
    x = torch.randn(5, 20)
    with torch.no_grad():
        logits = net(x)
    assert logits.shape == (5, 3)
    assert torch.isfinite(logits).all()


def test_ft_transformer_deterministic_with_seed() -> None:
    cfg = TabTransformerConfig(d_token=32, n_heads=4, n_blocks=2, dropout=0.0)
    torch.manual_seed(123)
    net_a = _build_network(input_dim=20, cfg=cfg)
    torch.manual_seed(123)
    net_b = _build_network(input_dim=20, cfg=cfg)
    x = torch.randn(4, 20)
    net_a.eval()
    net_b.eval()
    with torch.no_grad():
        out_a = net_a(x)
        out_b = net_b(x)
    assert torch.allclose(out_a, out_b, atol=1e-6)


def test_ft_transformer_state_dict_roundtrip(tmp_path: Path) -> None:
    cfg = TabTransformerConfig(d_token=16, n_heads=4, n_blocks=1, dropout=0.0)
    net = _build_network(input_dim=12, cfg=cfg)
    net.eval()
    x = torch.randn(3, 12)
    with torch.no_grad():
        out_before = net(x)

    ckpt = tmp_path / "ft.pt"
    torch.save(net.state_dict(), ckpt)
    net2 = _build_network(input_dim=12, cfg=cfg)
    net2.load_state_dict(torch.load(ckpt, map_location="cpu"))
    net2.eval()
    with torch.no_grad():
        out_after = net2(x)
    assert torch.allclose(out_before, out_after, atol=1e-6)


def test_ft_transformer_tokenizer_shapes() -> None:
    """Explicit check that the FeatureTokenizer lifts (B,F) → (B,F,d) tokens."""
    cfg = TabTransformerConfig(d_token=8, n_heads=2, n_blocks=1, dropout=0.0)
    net = _build_network(input_dim=5, cfg=cfg)
    tokens = net.tokenizer(torch.randn(2, 5))  # type: ignore[operator]
    assert tokens.shape == (2, 5, 8)


def test_ft_transformer_handles_zero_input() -> None:
    """Zero features must still produce a valid softmax distribution via [CLS]+bias."""
    cfg = TabTransformerConfig(d_token=16, n_heads=4, n_blocks=1, dropout=0.0)
    net = _build_network(input_dim=10, cfg=cfg)
    net.eval()
    with torch.no_grad():
        logits = net(torch.zeros(2, 10))
        probs = torch.softmax(logits, dim=1)
    assert probs.shape == (2, 3)
    np.testing.assert_allclose(probs.sum(dim=1).numpy(), np.ones(2), atol=1e-6)
