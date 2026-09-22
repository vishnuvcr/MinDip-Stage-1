# Research Status

Repository: vishnuvcr/MinDip-Stage-1
As of: 2026-09-22

| Phase | Status | Notes |
|---|---|---|
| 0 Governance | Complete | Plan, instructions, status, errors, action log, CI scaffold created |
| 1 Strategy engine | Complete pending CI/data validation | Dynamic NIFTY/SENSEX engine, cost model, expiry math, tests, workflow |
| 2 Data audit | Complete with caveat | Corrected holiday calendar, provenance, missing-data audit, reduced cache |
| 3 Historical backtest | Complete | 33 NIFTY and 28 SENSEX complete cycles; trade-level statistics and bootstrap diagnostics cached |
| 4 Robustness | Complete | Cost/slippage grid, break-even friction, chronology blocks, volatility context; bid/ask limitation retained |
| 5 CPCV/DSR/PBO | Complete | CPCV stability, untouched holdout, DSR diagnostic, PBO identifiability, permutation test |
| 6 Manuscript | Complete | Full manuscript, figures, appendices, final conclusion, reproducibility map |

## Software verification status

Deterministic tests are committed in tests/test_multileg_options_backtest.py. The repository also contains a manual Phase 1 GitHub Actions workflow that runs the unit suite and, when a cached CSV is present, can execute the requested index backtest.

## Empirical status

Historical research results are committed for the corrected public-source sample. No live/production performance claim is made; direct bid/ask and exact historical broker-ledger reconstruction remain deployment prerequisites.

## Known execution limitation

The local container cannot reach github.com directly, so local clone-based execution was unavailable. Verification is therefore delegated to the committed GitHub Actions workflow rather than presented as a locally executed test result.

## Latest completed step

Phase 6 manuscript gate is complete. The final conclusion is that the locked specification did not pass the historical promotion gate. A new strategy candidate must start a separate research experiment.
