"""Promote Kelly-trained models to production.

For each (arch, league), copies models/<arch>_<league>.kelly.{pt,scaler.joblib}
on top of the production files, backing up the previous production artifacts
to <name>.pre_kelly.{pt,scaler.joblib,calibrator.joblib}. Per the Phase D
audit (``models/_runs/<arch>_<league>.kelly.calibration.json``):

- ``winner == "none"``: removes the stale production calibrator (it was fit
  against the pre-Kelly logits and would distort Kelly-trained probs).
- ``winner in {"isotonic", "temperature"}``: copies the winner calibrator
  (``.kelly.calibrator.joblib``) on top of ``.calibrator.joblib``.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

MODELS_DIR = Path("models")
RUNS_DIR = MODELS_DIR / "_runs"
ARCHITECTURES = ("mlp", "sequence", "tabtransformer")
LEAGUES = ("BL", "CH", "LL", "PL", "SA")


def _backup(src: Path) -> None:
    if not src.exists():
        return
    backup = src.with_suffix(src.suffix + ".pre_kelly")  # e.g. .pt → .pt.pre_kelly
    # Only back up once; don't clobber a previous backup.
    if not backup.exists():
        shutil.copy2(src, backup)


def promote(arch: str, league: str) -> dict[str, str]:
    audit_path = RUNS_DIR / f"{arch}_{league}.kelly.calibration.json"
    if not audit_path.exists():
        return {"status": "skip-no-audit"}
    audit = json.loads(audit_path.read_text())
    winner = audit["winner"]

    src_pt = MODELS_DIR / f"{arch}_{league}.kelly.pt"
    src_scaler = MODELS_DIR / f"{arch}_{league}.kelly.scaler.joblib"
    src_cal = MODELS_DIR / f"{arch}_{league}.kelly.calibrator.joblib"
    dst_pt = MODELS_DIR / f"{arch}_{league}.pt"
    dst_scaler = MODELS_DIR / f"{arch}_{league}.scaler.joblib"
    dst_cal = MODELS_DIR / f"{arch}_{league}.calibrator.joblib"

    if not src_pt.exists():
        return {"status": "skip-no-kelly-pt"}

    # Back up production artifacts.
    _backup(dst_pt)
    _backup(dst_scaler)
    _backup(dst_cal)

    # Copy Kelly weights + scaler over production paths.
    shutil.copy2(src_pt, dst_pt)
    if src_scaler.exists():
        shutil.copy2(src_scaler, dst_scaler)

    # Handle calibrator based on Phase D winner.
    if winner in ("isotonic", "temperature"):
        if not src_cal.exists():
            return {"status": "error-missing-kelly-cal", "winner": winner}
        shutil.copy2(src_cal, dst_cal)
        cal_state = f"replaced({winner})"
    else:  # "none" → remove stale production calibrator.
        if dst_cal.exists():
            dst_cal.unlink()
            cal_state = "removed(none-winner)"
        else:
            cal_state = "absent"

    return {"status": "ok", "winner": winner, "calibrator": cal_state}


def main() -> int:
    rc = 0
    print(f"{'arch':<15}{'league':<6}{'winner':<13}{'status':<32}{'cal':<24}")
    print("-" * 90)
    for arch in ARCHITECTURES:
        for league in LEAGUES:
            result = promote(arch, league)
            if result["status"].startswith("error") or result["status"].startswith("skip"):
                if result["status"].startswith("error"):
                    rc = 1
            print(
                f"{arch:<15}{league:<6}{result.get('winner', '-'):<13}"
                f"{result['status']:<32}{result.get('calibrator', '-'):<24}"
            )
    return rc


if __name__ == "__main__":
    sys.exit(main())
