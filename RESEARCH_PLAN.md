# Research Plan — Reverse Calendar Four-Leg Index Options

## Research question

Does the specified four-leg, multi-expiry reverse-calendar basket produce economically meaningful and robust returns on NIFTY 50 and BSE SENSEX after realistic implementation frictions, with the exact user-defined expiry, holiday, strike, timing, slippage, and fixed-cost rules?

## Aims

1. Implement the strategy deterministically for both indices.
2. Verify expiry/holiday/strike selection without look-ahead.
3. Quantify gross and net trade-level performance.
4. Compare cost and liquidity sensitivity between the two indices.
5. Preserve enough diagnostics for later CPCV/DSR/PBO robustness work.

## Phase gates

### Phase 0 — Governance & reproducibility
Status: Complete

### Phase 1 — Strategy engine
Status: Complete pending CI/data validation
Gate achieved:
- input schema validation;
- dynamic NIFTY/SENSEX configuration;
- weekly/monthly expiry date math;
- holiday roll;
- ATM/ITM strike selection;
- timestamp-aware execution;
- 0.5% adverse slippage on every leg at both entry and exit;
- ₹40/leg cycle cost;
- ₹1,50,000 static margin denominator;
- deterministic unit tests and a manual workflow.

### Phase 2 — Data audit & cached data
Status: Complete with calendar-source caveat
Gate:
- point-in-time dataset provenance;
- spot coverage at entry;
- option-chain coverage for all four legs;
- duplicate/missing timestamp audit;
- contract-master/lot-size validation;
- corporate-action/news/calendar audit where applicable.

### Phase 3 — Historical backtest
Status: Complete
Gate:
- NIFTY and SENSEX trade logs;
- equity curves;
- ROC, win rate, max drawdown, average win/loss, expectancy;
- monthly/weekly attribution;
- missing-data and skipped-cycle report.

### Phase 4 — Robustness & cost stress
Status: Complete
Gate:
- slippage stress;
- spread/liquidity stress;
- alternative execution timestamp;
- bootstrap confidence intervals;
- regime-conditioned results;
- parameter sensitivity that does not change the locked primary result.

### Phase 5 — CPCV / DSR / PBO
Status: Complete
Gate:
- chronology-safe cross-validation;
- multiple-testing correction;
- out-of-sample/untouched holdout analysis;
- explicit promotion/rejection decision based on predeclared tests.

### Phase 6 — Manuscript & research conclusion
Status: Complete for original written-rule experiment

### Phase 7 — Screenshot strategy reconciliation
Status: Superseded by Phase 8

### Phase 8 — Current uploaded screenshot strategy
Status: Complete
Gate achieved:
- latest editor/payoff screenshots used as authoritative;
- exact four legs locked: SELL monthly ATM PE; BUY monthly ATM-2 CE; BUY weekly ATM+2 PE; SELL weekly ATM CE;
- nearest strike used as ATM;
- historical sample rerun from the existing point-in-time contract cache;
- exact mapping independently validated;
- separate current-strategy metrics and friction decomposition produced.

### Phase 9 — Current-strategy robustness
Status: Complete with execution-data limitation
Conclusion: execution-sensitive and statistically inconclusive. No parameter optimization or production promotion. Further research requires historical bid/ask/market-depth or equivalent execution-quality data and exact date-specific all-in fee reconstruction.
Completed in this phase:
- separate weekly/monthly futures recognized;
- Black-76 leg IV calibration;
- screenshot intrinsic value validation;
- portfolio delta and vega validation;
- screenshot POP approximation;
- predefined slippage/cost stress.
Remaining gate:
- direct bid/ask or spread-aware execution;
- historical broker/statutory fee reconstruction;
- chronology/CPCV and untouched holdout for the corrected strategy — complete;
- exact payoff/max-profit/max-loss replication if possible;
- separate current-strategy manuscript addendum.

## Stop condition

For the **current uploaded screenshot strategy**, the research stops after the declared Phase 9 evidence gate is completed. Phase 9 will not optimize the strategy. If the required execution-quality evidence cannot be reconstructed, the conclusion will explicitly remain inconclusive rather than assuming favourable fills.
