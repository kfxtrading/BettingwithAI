"""Bootstrap data for Railway pre-deploy.

Two jobs, both idempotent:

1. Copy image-baked seed files from /app/data_seed/ into the mounted
   /app/data/ volume (fixtures*.json today; only files that don't yet
   exist in the volume are copied, so operator-generated content wins).

2. Download historical football-data.co.uk CSVs via the existing helper.
   Skips files already present.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console

from football_betting.config import DATA_DIR
from football_betting.data.downloader import download_all

console = Console()

SEED_DIR = Path("/app/data_seed")


def _copy_seeds() -> None:
    if not SEED_DIR.is_dir():
        console.log(f"[yellow]No seed dir at {SEED_DIR}; skipping[/yellow]")
        return

    copied = 0
    skipped = 0
    for src in SEED_DIR.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(SEED_DIR)
        dst = DATA_DIR / rel
        if dst.exists():
            skipped += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        console.log(f"  seeded {rel}")
        copied += 1
    console.log(f"Seed copy: {copied} copied, {skipped} already present")


if __name__ == "__main__":
    _copy_seeds()
    download_all()
