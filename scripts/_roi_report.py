"""Ad-hoc Phase-E ROI report from models/_runs/*.kelly.calibration.json."""

from __future__ import annotations

import glob
import json
import statistics
from pathlib import Path


def main() -> None:
    runs = sorted(glob.glob("models/_runs/*.kelly.calibration.json"))
    header = (
        f"{'arch':<15}{'league':<8}{'winner':<13}"
        f"{'growth':>10}{'kROI':>10}{'fROI':>10}{'n_bets':>8}{'n_eval':>8}"
    )
    print(header)
    print("-" * len(header))

    rows: list[tuple[str, str, str, float, float, float, int, int]] = []
    for p in runs:
        d = json.loads(Path(p).read_text())
        w = d["winner"]
        m = d["metrics"][w]
        row = (
            d["architecture"],
            d["league"],
            w,
            float(m.get("kelly_growth", 0.0)),
            float(m.get("kelly_roi", 0.0)),
            float(m.get("flat_roi", 0.0)),
            int(m.get("n_bets", 0)),
            int(d["n_eval"]),
        )
        rows.append(row)
        print(
            f"{row[0]:<15}{row[1]:<8}{row[2]:<13}"
            f"{row[3]:>+10.4f}{row[4] * 100:>+9.1f}%{row[5] * 100:>+9.1f}%"
            f"{row[6]:>8}{row[7]:>8}"
        )

    print("-" * len(header))
    k = [r[4] for r in rows]
    f = [r[5] for r in rows]
    nb = [r[6] for r in rows]

    print(
        f"Kelly-stake ROI  mean: {statistics.mean(k) * 100:+.2f}%   "
        f"median: {statistics.median(k) * 100:+.2f}%   "
        f"min/max: {min(k) * 100:+.1f}% / {max(k) * 100:+.1f}%"
    )
    print(
        f"Flat-stake ROI   mean: {statistics.mean(f) * 100:+.2f}%   "
        f"median: {statistics.median(f) * 100:+.2f}%   "
        f"min/max: {min(f) * 100:+.1f}% / {max(f) * 100:+.1f}%"
    )

    total_nb = max(sum(nb), 1)
    wk = sum(k[i] * nb[i] for i in range(len(rows))) / total_nb
    wf = sum(f[i] * nb[i] for i in range(len(rows))) / total_nb
    print(f"n_bets-weighted:      kelly={wk * 100:+.2f}%   flat={wf * 100:+.2f}%")
    print(f"Total bets placed: {sum(nb)}")

    # Per-league aggregate.
    by_league: dict[str, list[tuple[float, float, int]]] = {}
    for r in rows:
        by_league.setdefault(r[1], []).append((r[4], r[5], r[6]))
    print()
    print(f"{'league':<8}{'kROI_mean':>12}{'fROI_mean':>12}{'n_bets':>10}")
    for lg, xs in sorted(by_league.items()):
        km = statistics.mean(x[0] for x in xs)
        fm = statistics.mean(x[1] for x in xs)
        nbs = sum(x[2] for x in xs)
        print(f"{lg:<8}{km * 100:>+11.2f}%{fm * 100:>+11.2f}%{nbs:>10}")


if __name__ == "__main__":
    main()
