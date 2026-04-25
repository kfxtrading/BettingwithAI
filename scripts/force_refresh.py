"""
Force a manual refresh of today.json (predictions + value bets).

Runs the same blocking pipeline used by the daily scheduler:
    Odds-API fetch -> fixtures_<date>.json -> today.json
    + dated snapshot capture + regrade of all bets

Usage:
    python -m scripts.force_refresh
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def _setup_logging() -> None:
    logger = logging.getLogger("football_betting.api")
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-5s | %(message)s",
                          datefmt="%H:%M:%S")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def main() -> None:
    _setup_logging()
    from football_betting.api.scheduler import _refresh_blocking

    print(">>> Forcing manual snapshot refresh (Odds-API -> today.json) ...")
    _refresh_blocking()
    print(">>> Done.")


if __name__ == "__main__":
    main()
