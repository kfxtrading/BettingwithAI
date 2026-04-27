# Benchmark Report - PL

- Generated: `2026-04-27T17:17:42+00:00`
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
| `our_model` | 380 | 0.2156 | 0.6143 | 0.0322 | -0.0072 | 380 | +0.0194 | +0.0389 | -0.0004 | -0.0065 |
| `market_implied` | 380 | 0.1962 | 0.5754 | 0.0326 | -0.0007 | 380 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
