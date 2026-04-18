"""Bootstrap historical football-data.co.uk CSVs.

Idempotent: skips files that already exist. Runs as Railway pre-deploy step
so the mounted /app/data/raw volume gets seeded on first boot (and any
missing seasons on subsequent deploys).
"""
from __future__ import annotations

from football_betting.data.downloader import download_all


if __name__ == "__main__":
    download_all()
