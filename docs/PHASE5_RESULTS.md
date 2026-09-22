# Phase 5 Results

## CPCV-style stability

Using six chronological blocks and all 2-of-6 test-block combinations:

| Metric | NIFTY | SENSEX |
|---|---:|---:|
| Completed trades | 33 | 28 |
| Test paths | 15 | 15 |
| Positive P&L paths | 6.7% | 20.0% |
| Median test Sharpe | -0.429 | -0.583 |
| Mean test Sharpe | -0.425 | -0.438 |

## Single-trial PSR diagnostic

| Index | Sharpe | PSR P(Sharpe > 0) |
|---|---:|---:|
| NIFTY | -0.425 | 0.0074 |
| SENSEX | -0.400 | 0.0277 |

A formal multi-trial Deflated Sharpe Ratio is not identified by the study design because one strategy specification was locked before testing. Probability of Backtest Overfitting is likewise not estimable for one frozen strategy. The repository therefore reports these design limitations explicitly rather than fabricating multi-trial statistics.

The CPCV-style paths provide the practical stability result: positive P&L appears in only a small minority of chronological test combinations.
