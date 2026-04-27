# Benchmark Report - CH

- Generated: `2026-04-27T17:18:45+00:00`
- Devig method: `power`

## Coverage

| Metric | Value |
| --- | ---: |
| `n_predictions` | 552 |
| `n_scored` | 552 |
| `n_with_odds` | 552 |
| `n_with_opening_odds` | 552 |
| `n_opta_matched` | 0 |
| `n_opta_unmatched` | 0 |

## Sources

| Source | n | RPS | Brier | ECE | Weighted CLV | CLV n | Delta RPS | Delta Brier | Delta ECE | Delta CLV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `our_model` | 552 | 0.2152 | 0.6362 | 0.0236 | -0.0132 | 552 | +0.0076 | +0.0185 | -0.0033 | -0.0065 |
| `market_implied` | 552 | 0.2075 | 0.6177 | 0.0268 | -0.0067 | 552 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
