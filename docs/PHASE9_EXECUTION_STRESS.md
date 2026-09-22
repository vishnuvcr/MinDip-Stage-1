[object Object]
## Corrected-strategy robustness

At the primary 0.5% slippage + ₹160/cycle execution model:

| Diagnostic | NIFTY | SENSEX |
|---|---:|---:|
| Trades | 33 | 28 |
| Mean P&L/trade | ₹-333.78 | ₹-222.40 |
| Bootstrap 95% CI for mean | [-₹1,396.06, ₹747.92] | [-₹1,345.09, ₹874.45] |
| CPCV positive test combinations | 40.0% | 46.7% |
| Median CPCV test mean | ₹-525.70 | ₹-328.66 |
| Q25–Q75 CPCV test mean | [-₹1,137.99, ₹370.48] | [-₹730.26, ₹504.74] |
| Untouched final block trades | 3 | 4 |
| Untouched final-block P&L | ₹-5,002.63 | ₹-2,991.38 |
| Untouched final-block win rate | 33.3% | 25.0% |

The chronology evidence is mixed rather than uniformly negative, but the untouched final block is negative for both indices and the bootstrap intervals are wide enough to include zero. This is a small-sample robustness warning, not evidence of a stable positive edge.

The previous Phase 5 CPCV/DSR/PBO outputs are **not applicable** to this current uploaded strategy because they were computed on a different leg definition. These Phase 9 current-strategy diagnostics supersede them for the current research question.
