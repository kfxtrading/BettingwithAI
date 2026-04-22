"""Post-hoc probability calibration for the support intent classifier (M3).

Temperature scaling (Guo et al., 2017) — a single scalar T divides the
pre-softmax logits. On multi-class models with ~270 fine-grained intents
and imbalanced validation subsets it typically cuts the Expected
Calibration Error (ECE) by 2–4x while leaving the argmax ranking
untouched.

The module has two public symbols:

* :func:`expected_calibration_error` — numeric ECE on a held-out split.
* :class:`TemperatureCalibrator` — fits T, applies it, save/load.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

# ───────────────────────── ECE ─────────────────────────


def expected_calibration_error(
    probs: np.ndarray,
    labels: np.ndarray,
    *,
    n_bins: int = 15,
) -> float:
    """Compute the Expected Calibration Error on (probs, labels).

    Parameters
    ----------
    probs:
        ``(N, C)`` post-softmax probabilities.
    labels:
        ``(N,)`` integer gold class ids.
    n_bins:
        Number of equal-width confidence bins (``[0, 1/B), ..., [1-1/B, 1]``).

    Returns
    -------
    ECE in ``[0, 1]``; 0 means perfect calibration.
    """
    if probs.ndim != 2:
        raise ValueError(f"probs must be 2D, got shape {probs.shape}")
    if labels.ndim != 1 or labels.shape[0] != probs.shape[0]:
        raise ValueError(
            f"labels must be 1D of length {probs.shape[0]}, got {labels.shape}"
        )

    confidences = probs.max(axis=1)
    predictions = probs.argmax(axis=1)
    correct = (predictions == labels).astype(np.float64)

    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = float(len(labels))
    for lo, hi in zip(bin_edges[:-1], bin_edges[1:], strict=False):
        # Include upper edge in last bin.
        in_bin = (confidences > lo) & (confidences <= hi)
        if lo == 0.0:
            in_bin = in_bin | (confidences == 0.0)
        count = int(in_bin.sum())
        if count == 0:
            continue
        acc = float(correct[in_bin].mean())
        conf = float(confidences[in_bin].mean())
        ece += (count / n) * abs(acc - conf)
    return float(ece)


# ───────────────────────── Calibrator ─────────────────────────


@dataclass(slots=True)
class TemperatureCalibrator:
    """One-parameter temperature scaler for logits → calibrated probs.

    Fit minimises NLL on a held-out validation set via a cheap 1-D LBFGS
    search. ``T`` is stored as a Python float so ``save``/``load`` are
    just JSON with no torch dependency at load time.
    """

    temperature: float = 1.0
    n_fit: int = 0
    ece_before: float | None = None
    ece_after: float | None = None
    _fit_info: dict[str, Any] = field(default_factory=dict)

    def fit(
        self,
        logits: np.ndarray,
        labels: np.ndarray,
        *,
        max_iter: int = 100,
        lr: float = 0.01,
    ) -> dict[str, Any]:
        """Fit T by minimising multi-class NLL with LBFGS.

        ``logits`` must be **pre-softmax** logits ``(N, C)``.
        """
        try:
            import torch  # type: ignore[import-not-found]
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                "torch not installed — `pip install -e .[ml]`"
            ) from exc

        if logits.ndim != 2:
            raise ValueError(f"logits must be 2D, got shape {logits.shape}")
        if labels.ndim != 1 or labels.shape[0] != logits.shape[0]:
            raise ValueError(
                f"labels must be 1D of length {logits.shape[0]}, got {labels.shape}"
            )
        if len(labels) < 2:
            # No point fitting T on 0–1 samples; keep T=1.
            self.n_fit = int(len(labels))
            return {"temperature": 1.0, "n_fit": self.n_fit, "converged": False}

        # ECE before (on raw softmax).
        probs_before = _softmax_np(logits)
        self.ece_before = expected_calibration_error(probs_before, labels)

        device = torch.device("cpu")  # Fitting is tiny — CPU keeps it DML-safe.
        logits_t = torch.tensor(logits, dtype=torch.float32, device=device)
        labels_t = torch.tensor(labels, dtype=torch.long, device=device)
        log_T = torch.zeros(1, requires_grad=True, device=device)  # T = exp(log_T)

        optimizer = torch.optim.LBFGS(
            [log_T], lr=lr, max_iter=max_iter, line_search_fn="strong_wolfe"
        )
        ce = torch.nn.CrossEntropyLoss()

        def _closure() -> Any:
            optimizer.zero_grad()
            t = torch.exp(log_T).clamp(min=1e-3, max=1e3)
            loss = ce(logits_t / t, labels_t)
            loss.backward()
            return loss

        optimizer.step(_closure)
        t_final = float(torch.exp(log_T.detach()).clamp(min=1e-3, max=1e3).item())
        self.temperature = t_final
        self.n_fit = int(len(labels))

        probs_after = _softmax_np(logits / t_final)
        self.ece_after = expected_calibration_error(probs_after, labels)
        self._fit_info = {
            "converged": True,
            "max_iter": max_iter,
            "lr": lr,
        }
        return {
            "temperature": t_final,
            "n_fit": self.n_fit,
            "ece_before": self.ece_before,
            "ece_after": self.ece_after,
            "converged": True,
        }

    # ───────────────────────── Apply ─────────────────────────

    def apply_logits(self, logits: np.ndarray) -> np.ndarray:
        """Return calibrated logits (``logits / T``)."""
        return logits / float(self.temperature)

    def apply_probs(self, logits: np.ndarray) -> np.ndarray:
        """Return calibrated softmax probabilities."""
        return _softmax_np(self.apply_logits(logits))

    # ───────────────────────── Persistence ─────────────────────────

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "temperature": float(self.temperature),
            "n_fit": int(self.n_fit),
            "ece_before": self.ece_before,
            "ece_after": self.ece_after,
            "fit_info": dict(self._fit_info),
        }
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @classmethod
    def load(cls, path: Path) -> TemperatureCalibrator:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        obj = cls(
            temperature=float(payload.get("temperature", 1.0)),
            n_fit=int(payload.get("n_fit", 0)),
            ece_before=payload.get("ece_before"),
            ece_after=payload.get("ece_after"),
        )
        obj._fit_info = dict(payload.get("fit_info") or {})
        return obj


# ───────────────────────── Internals ─────────────────────────


def _softmax_np(logits: np.ndarray) -> np.ndarray:
    z = logits - logits.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


__all__ = [
    "TemperatureCalibrator",
    "expected_calibration_error",
]
