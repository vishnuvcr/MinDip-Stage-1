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

## Superseded Phase 1 specification

The original Phase 1 engine remains archived for reproducibility, but its leg directions are **not** the current strategy. It implemented the original prose specification and must not be used for the current screenshot strategy.

## Current strategy specification

The authoritative current strategy is locked from the latest uploaded Paytm Money screenshots:

- SELL monthly ATM PE;
- BUY monthly ATM−2-strike CE;
- BUY weekly ATM+2-strike PE;
- SELL weekly ATM CE;
- nearest strike is used as ATM.

The Phase 8/9 implementation and results supersede the earlier written-rule experiment for the current research question.

## Archived Phase 1 implementation

The historical Phase 1 engine supports both NIFTY and SENSEX dynamically and remains available only for reproducibility of the superseded experiment. It implements the earlier leg-direction specification plus:

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


## Phase 8 — current screenshot strategy

The latest screenshots are now the authoritative strategy specification. The current basket is: **SELL monthly ATM PE; BUY monthly ATM−2-strike CE; BUY weekly ATM+2-strike PE; SELL weekly ATM CE**. For the visible NIFTY example at 23,329 with 50-point strikes this maps to 23,350 PE sold, 23,250 CE bought, 23,450 PE bought, and 23,350 CE sold. The previous Phase 6/7 results are not applicable to this current strategy.


## Phase 8 completed — latest uploaded strategy

The latest screenshots supersede all earlier strategy interpretations. The exact current rule is: **SELL monthly ATM PE; BUY monthly ATM−2 CE; BUY weekly ATM+2 PE; SELL weekly ATM CE**. The corrected historical test over 2025-10-01 to 2026-05-27 produced 33 complete NIFTY cycles and 28 complete SENSEX cycles. With 0.5% adverse premium slippage and ₹160/cycle fixed cost, ROC was **-7.34% NIFTY** and **-4.15% SENSEX**. At 0% slippage with the same ₹160 fixed cost, both were positive; break-even slippage was approximately 0.257% NIFTY and 0.297% SENSEX. Thus the current research issue is execution realism, not merely strategy direction. See docs/PHASE8_RESULTS.md.


### New payoff-model finding
The latest screenshots show the broker explicitly using separate target-day futures: 06-Oct FUT 23,436.90 and 27-Oct FUT 23,510.00. The ₹12,100 Intrinsic Value can be reproduced exactly to rounding from the four legs when weekly options are valued against the 06-Oct future and monthly options against the 27-Oct future. This confirms that the broker payoff is a multi-expiry forward/futures valuation, not a single-spot payoff. Phase 9 must reproduce this convention before comparing the backtest with the app.


## Phase 9 progress

The broker-style model has now been independently calibrated with Black-76 using the separate weekly/monthly futures shown in the screenshots. It reproduces ₹12,100 intrinsic to within ₹3, portfolio delta (-0.04094 vs displayed -0.041), portfolio vega (-0.6685 vs -0.67), and the displayed 96% POP approximately (95.38%). The remaining uncertainty is the exact broker theta/decay convention and the exact payoff/max-profit/max-loss curve. Execution-cost stress is now being run using current Paytm brokerage as a separate operational scenario; direct historical bid/ask data and date-specific statutory charges remain outstanding.


### Phase 9 execution result
The broker model calibration is now complete and the close-based execution stress is complete. Using current Paytm Money's stated ₹10 per unique executed F&O order as a brokerage-only operational reference, eight entry/exit orders imply ₹80 brokerage per basket before other statutory/exchange charges. Break-even premium slippage is approximately **0.315% NIFTY / 0.370% SENSEX** in that brokerage-only scenario. Under the locked ₹160 research-cost proxy it is **0.2567% / 0.2971%**. Historical bid/ask and all-in charge reconstruction remains the final Phase 9 evidence gap.


### Phase 9 robustness result
For the current uploaded strategy at 0.5% slippage + ₹160/cycle, 6-block CPCV produced positive test-block P&L in 40.0% of NIFTY and 46.7% of SENSEX combinations; median test mean P&L remained negative. The untouched final block was negative in both indices (-₹5,003 NIFTY; -₹2,991 SENSEX). Bootstrap 95% intervals for mean trade P&L included zero. Thus the current evidence is **execution-sensitive and statistically inconclusive**, not a robustly validated positive edge.
