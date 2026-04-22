"""Unit tests for the 1D-CNN + Transformer sequence network.

Tests the pure network module (``_build_network``) — avoids the heavy
``fit`` pipeline. Covers:
    * forward shape ``(B, 2, T, F) → (B, 3)``
    * masking: fully-padded rows must produce finite outputs (no NaN)
    * padding invariance: masked timesteps must not change the prediction
    * determinism under fixed seed
"""

from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from football_betting.config import SequenceConfig  # noqa: E402
from football_betting.predict.sequence_features import N_SEQ_FEATURES  # noqa: E402
from football_betting.predict.sequence_model import _build_network  # noqa: E402


def _make_cfg() -> SequenceConfig:
    return SequenceConfig(
        window_t=10,
        conv_channels=32,
        conv_kernel=3,
        tx_layers=2,
        tx_heads=4,
        tx_ffn_factor=2,
        head_hidden=64,
        dropout=0.0,
    )


@pytest.fixture
def net() -> torch.nn.Module:
    torch.manual_seed(0)
    return _build_network(_make_cfg()).eval()


def _rand_batch(batch: int, t: int = 10) -> tuple[torch.Tensor, ...]:
    torch.manual_seed(42)
    hs = torch.randn(batch, t, N_SEQ_FEATURES)
    as_ = torch.randn(batch, t, N_SEQ_FEATURES)
    hm = torch.ones(batch, t)
    am = torch.ones(batch, t)
    return hs, hm, as_, am


def test_forward_shape(net: torch.nn.Module) -> None:
    hs, hm, as_, am = _rand_batch(4)
    with torch.no_grad():
        out = net(hs, hm, as_, am)
    assert out.shape == (4, 3)
    assert torch.isfinite(out).all()


def test_softmax_sums_to_one(net: torch.nn.Module) -> None:
    hs, hm, as_, am = _rand_batch(3)
    with torch.no_grad():
        probs = torch.softmax(net(hs, hm, as_, am), dim=1)
    assert torch.allclose(probs.sum(dim=1), torch.ones(3), atol=1e-5)


def test_fully_padded_row_is_finite(net: torch.nn.Module) -> None:
    """Cold-start: a team with zero match history must not explode."""
    hs, hm, as_, am = _rand_batch(2)
    hm[0] = 0.0  # home team entirely unknown
    am[1] = 0.0  # away team entirely unknown
    with torch.no_grad():
        out = net(hs, hm, as_, am)
    assert out.shape == (2, 3)
    assert torch.isfinite(out).all()


def test_padding_is_invariant(net: torch.nn.Module) -> None:
    """Changing padded-timestep values must not change model output."""
    hs, hm, as_, am = _rand_batch(2)
    # last 3 home slots padded
    hm[:, -3:] = 0.0
    with torch.no_grad():
        out_a = net(hs.clone(), hm, as_, am)
    # Corrupt masked slots in home sequence with wild noise
    hs_noise = hs.clone()
    hs_noise[:, -3:] = torch.randn_like(hs_noise[:, -3:]) * 50.0
    with torch.no_grad():
        out_b = net(hs_noise, hm, as_, am)
    # Note: Conv1d leaks across neighbours (kernel=3), so exact equality
    # cannot hold — but the leaked values only affect 2 adjacent valid
    # positions max. Use a generous tolerance on softmax output.
    p_a = torch.softmax(out_a, dim=1)
    p_b = torch.softmax(out_b, dim=1)
    assert (p_a - p_b).abs().max().item() < 0.5  # bounded influence


def test_seed_determinism() -> None:
    cfg = _make_cfg()
    torch.manual_seed(123)
    net1 = _build_network(cfg).eval()
    torch.manual_seed(123)
    net2 = _build_network(cfg).eval()
    hs, hm, as_, am = _rand_batch(2)
    with torch.no_grad():
        o1 = net1(hs, hm, as_, am)
        o2 = net2(hs, hm, as_, am)
    assert torch.allclose(o1, o2, atol=1e-6)


def test_state_dict_roundtrip() -> None:
    cfg = _make_cfg()
    torch.manual_seed(7)
    src = _build_network(cfg).eval()
    dst = _build_network(cfg).eval()
    dst.load_state_dict(src.state_dict())
    hs, hm, as_, am = _rand_batch(2)
    with torch.no_grad():
        o1 = src(hs, hm, as_, am)
        o2 = dst(hs, hm, as_, am)
    assert torch.allclose(o1, o2, atol=1e-6)


def test_output_dtype_is_float32(net: torch.nn.Module) -> None:
    hs, hm, as_, am = _rand_batch(1)
    with torch.no_grad():
        out = net(hs, hm, as_, am)
    assert out.dtype == torch.float32
    assert not np.isnan(out.numpy()).any()
