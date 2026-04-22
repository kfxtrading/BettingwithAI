"""Loss functions for the support intent classifier (M3).

``SupConLoss`` implements Supervised Contrastive Learning (Khosla et al.,
2020) adapted for intent classification. It is combined with cross-entropy
in :class:`TransformerIntentClassifier` to physically spread class clusters
in the encoder's latent space — the report's recommended remedy for the
"soft margins" problem that Cross-Entropy alone produces on 124+ classes.

Torch is imported lazily inside the module body so the base install (without
``.[ml]``/``.[support-aug]``) does not crash on ``from football_betting...``.
"""

from __future__ import annotations

from typing import Any


def _require_torch() -> Any:
    try:
        import torch  # type: ignore[import-not-found]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "torch not installed — `pip install -e .[ml]` (or .[support-aug])"
        ) from exc
    return torch


def sup_con_loss(
    features: Any,
    labels: Any,
    temperature: float = 0.07,
) -> Any:
    """Supervised Contrastive loss on L2-normalised features.

    Parameters
    ----------
    features:
        ``(B, D)`` float tensor — one embedding per anchor. Need NOT be
        pre-normalised; the function applies L2 normalisation internally.
    labels:
        ``(B,)`` long tensor of integer class ids.
    temperature:
        Softmax temperature (the report recommends 0.07).

    Returns
    -------
    0-dim tensor — the batch-averaged contrastive loss. Falls back to a
    zero-loss (with grad) if the batch has no positive pairs.
    """
    torch = _require_torch()
    if features.dim() != 2:
        raise ValueError(f"features must be 2D, got shape {tuple(features.shape)}")
    if labels.dim() != 1 or labels.shape[0] != features.shape[0]:
        raise ValueError(
            f"labels must be 1D with length {features.shape[0]}, got {tuple(labels.shape)}"
        )

    device = features.device
    batch_size = features.shape[0]
    if batch_size < 2:
        return torch.zeros((), device=device, dtype=features.dtype, requires_grad=True)

    feats = torch.nn.functional.normalize(features, dim=1)
    logits = torch.matmul(feats, feats.T) / max(temperature, 1e-8)

    # Numerical stability: subtract row-wise max.
    logits_max, _ = logits.max(dim=1, keepdim=True)
    logits = logits - logits_max.detach()

    # Positives mask: same label & off-diagonal.
    labels_col = labels.view(-1, 1)
    pos_mask = (labels_col == labels_col.T).to(logits.dtype)
    # NOTE: built with arange/broadcasting instead of torch.eye — torch-directml
    # 0.2.5 falls back `aten::eye.m_out` to CPU and returns a malformed tensor.
    idx = torch.arange(batch_size, device=device)
    off_diag = (idx.view(-1, 1) != idx.view(1, -1)).to(logits.dtype)
    pos_mask = pos_mask * off_diag

    exp_logits = torch.exp(logits) * off_diag
    log_prob = logits - torch.log(exp_logits.sum(dim=1, keepdim=True) + 1e-12)

    pos_counts = pos_mask.sum(dim=1)
    # Anchors without positives contribute 0 loss (avoid div-by-zero).
    safe_counts = torch.where(pos_counts == 0, torch.ones_like(pos_counts), pos_counts)
    mean_log_prob_pos = (pos_mask * log_prob).sum(dim=1) / safe_counts
    valid = (pos_counts > 0).to(mean_log_prob_pos.dtype)

    if valid.sum() == 0:
        return torch.zeros((), device=device, dtype=features.dtype, requires_grad=True)

    loss = -(mean_log_prob_pos * valid).sum() / valid.sum()
    return loss


class SupConLoss:
    """Callable wrapper around :func:`sup_con_loss` for ``nn.Module``-style use.

    Not a ``torch.nn.Module`` subclass on purpose — avoids the hard import at
    module load time so tests without torch installed can still collect this
    module.
    """

    __slots__ = ("temperature",)

    def __init__(self, temperature: float = 0.07) -> None:
        self.temperature = temperature

    def __call__(self, features: Any, labels: Any) -> Any:
        return sup_con_loss(features, labels, temperature=self.temperature)


__all__ = ["SupConLoss", "sup_con_loss"]
