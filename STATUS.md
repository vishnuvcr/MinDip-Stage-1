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
| 6 Manuscript | Complete for written-rule experiment | Full manuscript for the original written parameterization |

## Software verification status

Deterministic tests are committed in tests/test_multileg_options_backtest.py. The repository also contains a manual Phase 1 GitHub Actions workflow that runs the unit suite and, when a cached CSV is present, can execute the requested index backtest.

## Empirical status

Historical research results are committed for the corrected public-source sample. No live/production performance claim is made; direct bid/ask and exact historical broker-ledger reconstruction remain deployment prerequisites.

## Known execution limitation

The local container cannot reach github.com directly, so local clone-based execution was unavailable. Verification is therefore delegated to the committed GitHub Actions workflow rather than presented as a locally executed test result.

## Latest completed step

Phase 9 broker-model reconciliation and close-based execution stress are complete for the current screenshot strategy. The remaining evidence gap is historical bid/ask/spread and exact date-specific all-in charges. The Phase 6 written-rule conclusion is not applicable to the current screenshot strategy.

| 7 Screenshot strategy reconciliation | Superseded | Earlier screenshot interpretation superseded by latest uploaded screenshots |

| 8 Current uploaded screenshot strategy | Complete | Exact latest screenshot basket backtested; NIFTY -7.34% ROC, SENSEX -4.15% ROC under 0.5% slippage + ₹160/cycle |

- New screenshot evidence confirms broker-model valuation uses separate target futures for weekly and monthly legs; this is now a required Phase 9 validation item.

| 9 Broker model & execution realism | In progress | Black-76 calibration reproduces screenshot intrinsic/delta/vega/POP closely; execution-cost stress added; bid/ask validation remains |

- Phase 9 model reconciliation: **gate passed** — screenshot intrinsic/delta/vega/POP closely reproduced with separate expiry futures.
- Phase 9 execution stress: **complete for close-based sensitivity** — current brokerage-only and locked-cost slippage thresholds calculated.
- Phase 9 remaining: **historical bid/ask/spread reconstruction and date-specific all-in fee validation**.

- Phase 9 corrected-strategy robustness: **complete** — bootstrap, 6-block CPCV, and untouched final-block holdout run on the current uploaded four-leg strategy.
