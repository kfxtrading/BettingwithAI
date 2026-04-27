"""Benchmark report: model probabilities vs market-implied baselines."""
from __future__ import annotations

import csv
import json
import math
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal, cast

import numpy as np

from football_betting.betting.margin import DevigMethod, remove_margin
from football_betting.data.models import Outcome
from football_betting.predict.calibration import expected_calibration_error
from football_betting.scraping.team_names import normalize
from football_betting.tracking.metrics import brier_score, ranked_probability_score

OUTCOME_ORDER: tuple[Outcome, ...] = ("H", "D", "A")
OUTCOME_FIELDS: tuple[str, str, str] = ("home", "draw", "away")
PROB_FIELDS: tuple[str, str, str] = ("prob_home", "prob_draw", "prob_away")
ODDS_FIELDS: tuple[str, str, str] = ("odds_home", "odds_draw", "odds_away")
OPENING_ODDS_FIELDS: tuple[str, str, str] = (
    "opening_odds_home",
    "opening_odds_draw",
    "opening_odds_away",
)

BenchmarkFormat = Literal["json", "markdown", "all"]
MatchKey = tuple[str, str, str]
ProbabilityTriplet = tuple[float, float, float]
BacktestRow = dict[str, object]
ProbabilityResolver = Callable[[BacktestRow], ProbabilityTriplet | None]


@dataclass(slots=True)
class SourceSummary:
    """Metrics for one probability source."""

    source: str
    n: int
    mean_rps: float | None
    mean_brier: float | None
    ece: float | None
    weighted_clv: float | None
    clv_n: int
    delta_vs_market: dict[str, float | int | None] = field(default_factory=dict)


@dataclass(slots=True)
class OptaReference:
    """One local Opta-style reference row keyed to a fixture."""

    key: MatchKey
    probs: ProbabilityTriplet
    source_match_id: str | None = None


@dataclass(slots=True)
class BenchmarkReport:
    """Serializable benchmark report."""

    league: str
    generated_at: str
    devig_method: str
    coverage: dict[str, int]
    sources: dict[str, SourceSummary]
    opta_reference_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class _MetricValues:
    n: int
    mean_rps: float | None
    mean_brier: float | None
    ece: float | None


def market_implied_probs(
    row: Mapping[str, object],
    *,
    devig_method: DevigMethod,
) -> ProbabilityTriplet | None:
    """Return margin-adjusted closing-market probabilities for a backtest row."""
    odds = _extract_triplet(row, ODDS_FIELDS, min_value=1.0)
    if odds is None:
        return None
    try:
        return remove_margin(odds[0], odds[1], odds[2], method=devig_method)
    except ValueError:
        return None


def weighted_all_outcome_clv(
    probs: ProbabilityTriplet,
    row: Mapping[str, object],
) -> float | None:
    """Probability-weighted CLV across H/D/A for one match.

    The report intentionally counts only rows with complete opening and
    closing odds. Missing opening odds are excluded instead of falling back
    to closing odds.
    """
    opening = _extract_triplet(row, OPENING_ODDS_FIELDS, min_value=1.0)
    closing = _extract_triplet(row, ODDS_FIELDS, min_value=1.0)
    if opening is None or closing is None:
        return None
    return float(sum(p * ((o / c) - 1.0) for p, o, c in zip(probs, opening, closing, strict=True)))


def load_opta_reference(path: Path, league: str) -> list[OptaReference]:
    """Load a local Opta-style CSV or JSON probability reference."""
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as fh:
            return [
                ref
                for idx, row in enumerate(csv.DictReader(fh), start=2)
                if (ref := _parse_opta_row(row, league, row_number=idx)) is not None
            ]
    if suffix == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = _json_rows(raw)
        return [
            ref
            for idx, row in enumerate(rows, start=1)
            if (ref := _parse_opta_row(row, league, row_number=idx)) is not None
        ]
    raise ValueError(f"Unsupported Opta reference format: {path.suffix}")


def build_benchmark_report(
    league: str,
    rows: list[BacktestRow],
    *,
    devig_method: DevigMethod,
    opta_reference_path: Path | None = None,
) -> BenchmarkReport:
    """Build a benchmark report from freshly generated backtest rows."""
    league = league.upper()
    row_keys = [_row_key(row, league) for row in rows]
    key_set = {key for key in row_keys if key is not None}

    opta_refs: list[OptaReference] = []
    opta_by_key: dict[MatchKey, ProbabilityTriplet] = {}
    if opta_reference_path is not None:
        opta_refs = load_opta_reference(opta_reference_path, league)
        opta_by_key = {ref.key: ref.probs for ref in opta_refs}

    def our_probs(row: BacktestRow) -> ProbabilityTriplet | None:
        return _model_probs(row)

    def market_probs(row: BacktestRow) -> ProbabilityTriplet | None:
        return market_implied_probs(row, devig_method=devig_method)

    def opta_probs(row: BacktestRow) -> ProbabilityTriplet | None:
        key = _row_key(row, league)
        if key is None:
            return None
        return opta_by_key.get(key)

    sources: dict[str, SourceSummary] = {
        "our_model": _source_summary("our_model", rows, our_probs, devig_method=devig_method),
        "market_implied": _source_summary(
            "market_implied",
            rows,
            market_probs,
            devig_method=devig_method,
        ),
    }
    if opta_reference_path is not None:
        sources["opta_reference"] = _source_summary(
            "opta_reference",
            rows,
            opta_probs,
            devig_method=devig_method,
        )

    for source, summary in sources.items():
        if source == "market_implied":
            summary.delta_vs_market = {
                "n": summary.n,
                "clv_n": summary.clv_n,
                "mean_rps": 0.0 if summary.mean_rps is not None else None,
                "mean_brier": 0.0 if summary.mean_brier is not None else None,
                "ece": 0.0 if summary.ece is not None else None,
                "weighted_clv": 0.0 if summary.weighted_clv is not None else None,
            }
        else:
            resolver = opta_probs if source == "opta_reference" else our_probs
            summary.delta_vs_market = _delta_vs_market(
                rows,
                resolver,
                devig_method=devig_method,
            )

    coverage = {
        "n_predictions": len(rows),
        "n_scored": _count_rows(rows, our_probs, require_actual=True),
        "n_with_odds": sum(1 for row in rows if _extract_triplet(row, ODDS_FIELDS, min_value=1.0)),
        "n_with_opening_odds": sum(
            1
            for row in rows
            if _extract_triplet(row, ODDS_FIELDS, min_value=1.0)
            and _extract_triplet(row, OPENING_ODDS_FIELDS, min_value=1.0)
        ),
        "n_opta_matched": sum(1 for key in row_keys if key is not None and key in opta_by_key),
        "n_opta_unmatched": sum(1 for ref in opta_refs if ref.key not in key_set),
    }

    return BenchmarkReport(
        league=league,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        devig_method=devig_method,
        coverage=coverage,
        sources=sources,
        opta_reference_path=str(opta_reference_path) if opta_reference_path is not None else None,
    )


def render_markdown(report: BenchmarkReport) -> str:
    """Render the benchmark report as Markdown."""
    lines = [
        f"# Benchmark Report - {report.league}",
        "",
        f"- Generated: `{report.generated_at}`",
        f"- Devig method: `{report.devig_method}`",
        "",
        "## Coverage",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in report.coverage.items():
        lines.append(f"| `{key}` | {value} |")

    lines.extend(
        [
            "",
            "## Sources",
            "",
            (
                "| Source | n | RPS | Brier | ECE | Weighted CLV | CLV n | "
                "Delta RPS | Delta Brier | Delta ECE | Delta CLV |"
            ),
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name in ("our_model", "market_implied", "opta_reference"):
        summary = report.sources.get(name)
        if summary is None:
            continue
        delta = summary.delta_vs_market
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{summary.source}`",
                    str(summary.n),
                    _fmt(summary.mean_rps),
                    _fmt(summary.mean_brier),
                    _fmt(summary.ece),
                    _fmt(summary.weighted_clv, signed=True),
                    str(summary.clv_n),
                    _fmt(_maybe_float(delta.get("mean_rps")), signed=True),
                    _fmt(_maybe_float(delta.get("mean_brier")), signed=True),
                    _fmt(_maybe_float(delta.get("ece")), signed=True),
                    _fmt(_maybe_float(delta.get("weighted_clv")), signed=True),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def write_benchmark_report(
    report: BenchmarkReport,
    out_dir: Path,
    *,
    output_format: BenchmarkFormat = "all",
) -> dict[str, Path]:
    """Write the report to disk and return paths by format."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"benchmark_report_{report.league}"
    written: dict[str, Path] = {}
    if output_format in ("json", "all"):
        path = out_dir / f"{stem}.json"
        path.write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        written["json"] = path
    if output_format in ("markdown", "all"):
        path = out_dir / f"{stem}.md"
        path.write_text(render_markdown(report), encoding="utf-8")
        written["markdown"] = path
    return written


def _source_summary(
    source: str,
    rows: list[BacktestRow],
    probs_for_row: ProbabilityResolver,
    *,
    devig_method: DevigMethod,
) -> SourceSummary:
    scored = _score_rows(rows, probs_for_row)
    clv_values = [
        clv
        for row in rows
        if (probs := probs_for_row(row)) is not None
        if (clv := weighted_all_outcome_clv(probs, row)) is not None
    ]
    _ = devig_method
    return SourceSummary(
        source=source,
        n=scored.n,
        mean_rps=scored.mean_rps,
        mean_brier=scored.mean_brier,
        ece=scored.ece,
        weighted_clv=float(np.mean(clv_values)) if clv_values else None,
        clv_n=len(clv_values),
    )


def _delta_vs_market(
    rows: list[BacktestRow],
    probs_for_row: ProbabilityResolver,
    *,
    devig_method: DevigMethod,
) -> dict[str, float | int | None]:
    source_probs: list[ProbabilityTriplet] = []
    market_probs_list: list[ProbabilityTriplet] = []
    actuals: list[Outcome] = []
    source_clv: list[float] = []
    market_clv: list[float] = []

    for row in rows:
        source = probs_for_row(row)
        market = market_implied_probs(row, devig_method=devig_method)
        actual = _actual(row)
        if source is None or market is None or actual is None:
            continue
        source_probs.append(source)
        market_probs_list.append(market)
        actuals.append(actual)
        s_clv = weighted_all_outcome_clv(source, row)
        m_clv = weighted_all_outcome_clv(market, row)
        if s_clv is not None and m_clv is not None:
            source_clv.append(s_clv)
            market_clv.append(m_clv)

    source_metrics = _score_predictions(source_probs, actuals)
    market_metrics = _score_predictions(market_probs_list, actuals)
    source_clv_mean = float(np.mean(source_clv)) if source_clv else None
    market_clv_mean = float(np.mean(market_clv)) if market_clv else None

    return {
        "n": source_metrics.n,
        "clv_n": len(source_clv),
        "mean_rps": _diff(source_metrics.mean_rps, market_metrics.mean_rps),
        "mean_brier": _diff(source_metrics.mean_brier, market_metrics.mean_brier),
        "ece": _diff(source_metrics.ece, market_metrics.ece),
        "weighted_clv": _diff(source_clv_mean, market_clv_mean),
    }


def _score_rows(
    rows: list[BacktestRow],
    probs_for_row: ProbabilityResolver,
) -> _MetricValues:
    probs: list[ProbabilityTriplet] = []
    actuals: list[Outcome] = []
    for row in rows:
        actual = _actual(row)
        prob = probs_for_row(row)
        if actual is None or prob is None:
            continue
        probs.append(prob)
        actuals.append(actual)
    return _score_predictions(probs, actuals)


def _score_predictions(
    probs: list[ProbabilityTriplet],
    actuals: list[Outcome],
) -> _MetricValues:
    if not probs:
        return _MetricValues(n=0, mean_rps=None, mean_brier=None, ece=None)
    labels = np.asarray([OUTCOME_ORDER.index(actual) for actual in actuals], dtype=np.int64)
    probs_arr = np.asarray(probs, dtype=float)
    return _MetricValues(
        n=len(probs),
        mean_rps=float(
            np.mean(
                [
                    ranked_probability_score(prob, actual)
                    for prob, actual in zip(probs, actuals, strict=True)
                ]
            )
        ),
        mean_brier=float(
            np.mean(
                [brier_score(prob, actual) for prob, actual in zip(probs, actuals, strict=True)]
            )
        ),
        ece=expected_calibration_error(probs_arr, labels),
    )


def _model_probs(row: Mapping[str, object]) -> ProbabilityTriplet | None:
    return _prob_triplet([row.get(field) for field in PROB_FIELDS])


def _prob_triplet(values: list[object]) -> ProbabilityTriplet | None:
    floats: list[float] = []
    for value in values:
        coerced = _coerce_float(value)
        if coerced is None or not math.isfinite(coerced) or coerced < 0.0:
            return None
        floats.append(coerced)
    if not floats or sum(floats) <= 0.0:
        return None
    if max(floats) > 1.0:
        floats = [value / 100.0 for value in floats]
    total = sum(floats)
    if total <= 0.0:
        return None
    normalised = tuple(value / total for value in floats)
    return cast(ProbabilityTriplet, normalised)


def _extract_triplet(
    row: Mapping[str, object],
    fields: tuple[str, str, str],
    *,
    min_value: float,
) -> ProbabilityTriplet | None:
    values: list[float] = []
    for field_name in fields:
        value = _coerce_float(row.get(field_name))
        if value is None or not math.isfinite(value) or value <= min_value:
            return None
        values.append(value)
    return cast(ProbabilityTriplet, tuple(values))


def _coerce_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _actual(row: Mapping[str, object]) -> Outcome | None:
    raw = row.get("actual")
    if raw in OUTCOME_ORDER:
        return raw
    return None


def _count_rows(
    rows: list[BacktestRow],
    probs_for_row: ProbabilityResolver,
    *,
    require_actual: bool,
) -> int:
    total = 0
    for row in rows:
        if probs_for_row(row) is None:
            continue
        if require_actual and _actual(row) is None:
            continue
        total += 1
    return total


def _row_key(row: Mapping[str, object], league: str) -> MatchKey | None:
    raw_date = row.get("date")
    home = row.get("home_team")
    away = row.get("away_team")
    if raw_date is None or home is None or away is None:
        return None
    day = _date_key(raw_date)
    if day is None:
        return None
    return day, _team_key(league, str(home)), _team_key(league, str(away))


def _team_key(league: str, team: str) -> str:
    canonical = normalize(league, team.strip())
    return "".join(ch for ch in canonical.casefold() if ch.isalnum())


def _date_key(value: object) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            try:
                return date.fromisoformat(raw[:10]).isoformat()
            except ValueError:
                return None
    return None


def _json_rows(raw: object) -> list[Mapping[str, object]]:
    if isinstance(raw, list):
        return [cast(Mapping[str, object], row) for row in raw if isinstance(row, dict)]
    if isinstance(raw, dict):
        for key in ("rows", "predictions", "matches"):
            nested = raw.get(key)
            if isinstance(nested, list):
                return [
                    cast(Mapping[str, object], row)
                    for row in nested
                    if isinstance(row, dict)
                ]
    raise ValueError("Opta JSON reference must be a list or contain rows/predictions/matches")


def _parse_opta_row(
    row: Mapping[str, object],
    league: str,
    *,
    row_number: int,
) -> OptaReference | None:
    raw_league = row.get("league")
    if raw_league is not None and str(raw_league).strip().upper() != league.upper():
        return None
    missing = [
        field
        for field in ("date", "home_team", "away_team", "prob_home", "prob_draw", "prob_away")
        if row.get(field) in (None, "")
    ]
    if missing:
        raise ValueError(f"Opta reference row {row_number} missing fields: {', '.join(missing)}")
    key = _row_key(
        {
            "date": row["date"],
            "home_team": row["home_team"],
            "away_team": row["away_team"],
        },
        league,
    )
    if key is None:
        raise ValueError(f"Opta reference row {row_number} has an invalid match key")
    probs = _prob_triplet([row["prob_home"], row["prob_draw"], row["prob_away"]])
    if probs is None:
        raise ValueError(f"Opta reference row {row_number} has invalid probabilities")
    source_match_id = row.get("source_match_id")
    return OptaReference(
        key=key,
        probs=probs,
        source_match_id=str(source_match_id) if source_match_id not in (None, "") else None,
    )


def _diff(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


def _maybe_float(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _fmt(value: float | None, *, signed: bool = False) -> str:
    if value is None:
        return "-"
    prefix = "+" if signed else ""
    return f"{value:{prefix}.4f}"
