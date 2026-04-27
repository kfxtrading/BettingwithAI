# Benchmark Report - BL

- Generated: `2026-04-27T17:03:29+00:00`
- Devig method: `power`

## Coverage

| Metric | Value |
| --- | ---: |
| `n_predictions` | 306 |
| `n_scored` | 306 |
| `n_with_odds` | 306 |
| `n_with_opening_odds` | 306 |
| `n_opta_matched` | 0 |
| `n_opta_unmatched` | 0 |

## Sources

| Source | n | RPS | Brier | ECE | Weighted CLV | CLV n | Delta RPS | Delta Brier | Delta ECE | Delta CLV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `our_model` | 306 | 0.2183 | 0.6257 | 0.0695 | -0.0059 | 306 | +0.0162 | +0.0350 | +0.0108 | -0.0060 |
| `market_implied` | 306 | 0.2021 | 0.5907 | 0.0588 | +0.0001 | 306 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
