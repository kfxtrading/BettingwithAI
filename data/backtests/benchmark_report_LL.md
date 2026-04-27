# Benchmark Report - LL

- Generated: `2026-04-27T17:20:11+00:00`
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
| `our_model` | 380 | 0.1976 | 0.5810 | 0.0567 | -0.0040 | 380 | +0.0104 | +0.0225 | +0.0194 | -0.0053 |
| `market_implied` | 380 | 0.1872 | 0.5585 | 0.0372 | +0.0013 | 380 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
