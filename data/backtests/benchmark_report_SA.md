# Benchmark Report - SA

- Generated: `2026-04-27T17:19:28+00:00`
- Devig method: `power`

## Coverage

| Metric | Value |
| --- | ---: |
| `n_predictions` | 380 |
| `n_scored` | 380 |
| `n_with_odds` | 380 |
| `n_with_opening_odds` | 380 |
| `n_opta_matched` | 0 |
| `n_opta_unmatched` | 0 |

## Sources

| Source | n | RPS | Brier | ECE | Weighted CLV | CLV n | Delta RPS | Delta Brier | Delta ECE | Delta CLV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `our_model` | 380 | 0.1988 | 0.6009 | 0.1264 | -0.0040 | 380 | +0.0150 | +0.0346 | +0.0998 | -0.0034 |
| `market_implied` | 380 | 0.1838 | 0.5662 | 0.0266 | -0.0006 | 380 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
