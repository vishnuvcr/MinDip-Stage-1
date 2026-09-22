# MinDip — Stage 1

Research repository for a reproducible, cost-aware, multi-leg index-options backtesting program covering NIFTY 50 and BSE SENSEX.

## Current status

- Phase 0 — Governance & reproducibility: **complete**
- Phase 1 — Four-leg reverse-calendar implementation: **complete pending CI/data validation**
- Primary strategy specification: locked from the user request; no optimization has been performed.
- Data status: no production market dataset is committed yet. Deterministic synthetic tests are included; historical performance is not claimed.

## Repository map

| Area | Purpose |
|---|---|
| RESEARCH_PLAN.md | Master research phases, gates, and stop conditions |
| STATUS.md | Current phase/status ledger |
| ERROR_LOG.md | Mistakes, failures, and corrective actions |
| MIN_DIP_PROJECT_INSTRUCTIONS.md | Project operating instructions retained in-repo |
| research/CONVERSATION_LOG.md | User-visible request/action ledger (private chain-of-thought is not stored) |
| src/ | Backtesting library |
| scripts/ | CLI entry points |
| tests/ | Deterministic unit tests |
| data/ | Cached input/output data layout |
| docs/ | Strategy, assumptions, sources, and phase results |
| .github/workflows/ | Manual/CI research workflows |

## Phase 1 implementation

The reference engine in src/multileg_options_backtest.py supports both NIFTY and SENSEX dynamically. It implements:

- ATM strike selection from the 09:30 spot observation;
- monthly ATM PE buy;
- weekly ATM+2-strike PE sell;
- weekly ATM CE buy;
- monthly ATM−2-strike CE sell;
- Tuesday/Thursday weekly and last-Tuesday/last-Thursday monthly expiry math;
- previous-trading-day holiday roll;
- first quote at/after 09:30 for entry and last quote at/before 15:15 for exit;
- 0.5% adverse slippage per leg at entry and exit;
- ₹40 per leg, ₹160 per cycle fixed cost;
- ₹1,50,000 ROC denominator;
- trade-level and leg-level outputs plus skipped-cycle diagnostics.

## Important implementation note

The requested 50-point NIFTY and 100-point SENSEX strike intervals are treated as **research assumptions**. Exchange contract specifications can change, so a production dataset must be reconciled with the exchange contract master and date-specific lot sizes.

Phase 2 is the data-audit gate. Historical results are intentionally deferred until point-in-time option/spot data and calendar validation are available.


## Phase 2 — Data audit

Phase 2 is now active. The repository queries a pinned public 1-minute option dataset remotely and caches only a reduced strategy-specific extract, provenance metadata, checksums, and audit outputs. Raw third-party Parquet files are not copied into the repository. See `docs/DATA_SOURCE_REGISTRY.md`, `docs/PHASE2_DATA_AUDIT.md`, and the manual workflow `.github/workflows/phase2-data-audit.yml`.


### Latest Phase 2 execution
The first end-to-end remote extraction completed successfully and produced a small strategy-specific cache, but its automated push hit a branch-race. The workflow now rebases before pushing generated data. The provisional extraction observed 34 NIFTY and 38 SENSEX target cycles, with 29 fully executable four-leg cycles in each index; these counts are not yet treated as final until the cache is committed and audited.


## Phase 2 corrected result

The corrected common-window extraction (2025-10-01 to 2026-05-27) completed successfully in GitHub Actions. It produced 34 target cycles for each index; 33 NIFTY cycles and 28 SENSEX cycles had all four executable legs. The locked 0.5% slippage plus ₹160 cycle-cost model produced provisional net ROC of -29.88% for NIFTY and -22.28% for SENSEX over those executed samples. These are Phase 2 historical observations, not a promoted strategy recommendation; robustness and validation remain in later phases.


## Phase 3–4 completed findings

The corrected 2025-10-01 to 2026-05-27 locked backtest produced 33 complete NIFTY cycles and 28 complete SENSEX cycles. Under the locked 0.5% adverse slippage and ₹160/cycle cost, net P&L was approximately ₹-44,823 and ₹-33,426 respectively. Phase 4 showed that both samples remained negative even at 0% slippage and ₹0 cost; the break-even slippage was negative for both indices. Robustness outputs are in `data/cache/phase4/` and `docs/PHASE4_RESULTS.md`. Phase 5 is now the next gate.


## Phase 5 result

CPCV over 15 two-block test combinations remained predominantly negative: positive test-block net P&L occurred in 6.7% of combinations for NIFTY and 20.0% for SENSEX. The untouched final chronology block was negative for both. Multiple-trial DSR and PBO are correctly marked not estimable because the research contains one prespecified strategy rather than a post-hoc candidate family. Sign-flip permutation p-values were 0.02077 (NIFTY) and 0.04251 (SENSEX); these are diagnostics, not a strategy-selection device. Phase 6 is the final manuscript gate.


## Important Phase 7 correction

The Phase 6 numerical conclusion applies to the originally written ATM ±2-strike parameterization, not to the screenshot strategy just supplied. That mismatch is now explicitly corrected in Phase 7. The screenshot-exact example maps 25,049.55 spot to 25,000 monthly PE, 25,200 weekly PE, 25,050 weekly CE, and 25,000 monthly CE. A fresh backtest is running before any conclusion is retained for the screenshot strategy.

## Final Phase 6 conclusion

The complete research manuscript is in research/MIN_DIP_RESEARCH_MANUSCRIPT.md and the final conclusion is in docs/FINAL_CONCLUSION.md. The locked specification did not pass the historical promotion gate: both NIFTY and SENSEX were negative under the primary model, negative under the zero-friction counterfactual, and predominantly negative under chronology robustness diagnostics. No alternative parameter set is promoted from the observed sample.
