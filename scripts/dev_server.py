"""Run the FastAPI server locally without writing to production-tracked files.

The in-process scheduler normally writes ``data/live_scores.jsonl`` and
``data/snapshots/odds_<LEAGUE>.jsonl`` every few minutes. Those files are
git-tracked because Railway has no persistent volume — local runs would
otherwise pollute the working tree with diffs that race against the
production server.

This wrapper forces the noisy loops off before uvicorn boots so you can
develop locally without committing accidental drift. The snapshot refresh
itself still runs (so today.json gets generated), but no live polling
and no pre-kickoff odds capture.

Usage:
    python -m scripts.dev_server
    python -m scripts.dev_server --port 8001
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Force local-safe defaults BEFORE the app imports the scheduler. Setting
# these via env-var (rather than monkey-patching) keeps the production
# code path identical — Railway just doesn't see these values.
os.environ.setdefault("LIVE_SETTLE_INTERVAL_MIN", "0")
os.environ.setdefault("PREKICKOFF_SNAPSHOT_INTERVAL_MIN", "0")
os.environ.setdefault("STALE_RETRY_INTERVAL_MIN", "0")

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
except ImportError:
    pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Local-safe dev server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    print(">>> dev_server: live-settle, prekickoff, stale-retry loops disabled.")
    print(f">>> dev_server: http://{args.host}:{args.port}")

    import uvicorn
    uvicorn.run(
        "football_betting.api.app:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
