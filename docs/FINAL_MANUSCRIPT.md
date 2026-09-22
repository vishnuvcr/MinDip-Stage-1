# Research Manuscript — Four-Leg Multi-Expiry Reverse-Calendar Basket on NIFTY 50 and BSE SENSEX

## Abstract

This study evaluates a pre-specified four-leg, multi-expiry index-option basket on NIFTY 50 and BSE SENSEX. The strategy is intentionally locked before historical evaluation: on the designated cycle-entry day at 09:30 IST, it buys the monthly ATM put, sells the weekly put two strikes above ATM, buys the weekly ATM call, and sells the monthly call two strikes below ATM. All four legs are squared off at 15:15 on the weekly expiry. NIFTY uses the user-specified 50-point strike interval and Tuesday/last-Tuesday expiry schedule; SENSEX uses the user-specified 100-point interval and Thursday/last-Thursday schedule.

The primary empirical sample covers 2025-10-01 through 2026-05-27, the common coverage window of the pinned spot references. The data pipeline uses 1-minute option/spot data, explicit exchange-holiday inputs, date-dependent NIFTY lot sizes, and an adverse 0.5% premium slippage assumption at each entry and exit. A fixed ₹160 cost is charged per four-leg cycle, with ₹1,50,000 used as the capital/margin denominator.

The corrected sample contains 34 target cycles for each index. 33 NIFTY cycles and 28 SENSEX cycles have all four executable legs. Under the locked primary execution model, NIFTY produced total net P&L of ₹-44,822.58 (-29.88% ROC), a 36.36% win rate, maximum drawdown of ₹-44,857.28 (-30.65%), average winning trade of ₹1,846.11, average losing trade of ₹-3,189.33, and expectancy of ₹-1,358.26 per completed cycle. SENSEX produced ₹-33,425.66 (-22.28% ROC), a 25.00% win rate, maximum drawdown of ₹-41,917.04 (-27.38%), average winning trade of ₹2,093.82, average losing trade of ₹-2,289.64, and expectancy of ₹-1,193.77.

The key robustness result is that the negative outcome is not created solely by the assumed 0.5% slippage. At zero slippage and zero fixed cycle cost, aggregate P&L remains negative: ₹-16,904 for NIFTY and ₹-13,599 for SENSEX. The Phase 4 algebraic break-even slippage is negative for both samples, implying that the basket does not become profitable merely by making execution friction vanish. CPCV-style chronological stability tests further show only 6.7% positive paths for NIFTY and 20.0% for SENSEX, with negative median test Sharpe in both. A single-trial Probabilistic Sharpe Ratio diagnostic is 0.0074 for NIFTY and 0.0277 for SENSEX.

The evidence therefore does not support promoting this locked strategy to production trading on the tested dataset and assumptions. The principal finding is not that reverse calendars are universally ineffective, but that this exact four-leg specification does not demonstrate a statistically or economically persuasive edge in the present sample after the research controls were applied.

---

## 1. Research Question

Does the specified four-leg, multi-expiry reverse-calendar basket produce economically meaningful and robust returns on NIFTY 50 and BSE SENSEX after realistic execution friction, explicit expiry/holiday rules, and a fixed capital denominator?

### Secondary questions

1. Are the results positive before slippage and fixed cycle costs?
2. How sensitive is the basket to premium slippage and fixed costs?
3. Which individual legs contribute most of the gross P&L?
4. Does the result survive chronological combinatorial testing?
5. Are the observed differences between NIFTY and SENSEX consistent with execution/data limitations rather than a demonstrated structural superiority of one index?

---

## 2. Strategy Specification

### 2.1 Entry and expiry rules

| Parameter | NIFTY 50 | BSE SENSEX |
|---|---|---|
| Strike interval | 50 points | 100 points |
| ITM offset | 100 points | 200 points |
| Weekly expiry | Tuesday | Thursday |
| Monthly expiry | Last Tuesday | Last Thursday |
| Cycle entry day | Wednesday | Friday |
| Entry time | 09:30 IST | 09:30 IST |
| Exit time | 15:15 IST | 15:15 IST |

The historical implementation uses explicit holiday rolls to the previous trading day.

### 2.2 Four legs

| Leg | Side | Expiry | Strike |
|---|---|---|---|
| L1 | BUY | Monthly | ATM PE |
| L2 | SELL | Weekly | ATM + ITM offset PE |
| L3 | BUY | Weekly | ATM CE |
| L4 | SELL | Monthly | ATM − ITM offset CE |

### 2.3 Execution model

For a long option:
- Entry execution = Close × 1.005
- Exit execution = Close × 0.995

For a short option:
- Entry execution = Close × 0.995
- Exit execution = Close × 1.005

A fixed ₹40 charge is assigned to each of the four legs, or ₹160 per completed basket.

Capital/margin denominator = ₹1,50,000.

The production backtest accepts the actual date-appropriate lot size. NIFTY is assigned 75 through the retained 30-Dec-2025 expiry transition and 65 after that transition; SENSEX is assigned 20 in the current model.

---

## 3. Data and Provenance

### 3.1 Option data

The Phase 2 pipeline uses a pinned revision of the public Hugging Face dataset rissin/nse-options-intraday, sourced from 1-minute NIFTY/SENSEX option data. The repository records immutable revision URLs rather than floating main URLs.

### 3.2 Spot data

The Phase 2 pipeline uses pinned 1-minute NIFTY and SENSEX index reference files from thetrademarkk/india-index-options-1m.

### 3.3 Calendar

The corrected pipeline does not infer exchange holidays from missing market observations. This was a critical methodology correction. An explicit holiday file is stored in data/calendar/exchange_holidays.csv.

The 2026 SENSEX holiday rows in the current file are transparently marked as mirrored from the common Indian exchange holiday schedule and pending direct BSE confirmation. They are not presented as an independently verified BSE-only source.

### 3.4 Common sample window

The final cross-index sample is 2025-10-01 through 2026-05-27. This avoids giving one index a later spot-data endpoint than the other.

---

## 4. Scientific Methodology

The research was executed as a sequence of locked phases:

### Phase 0 — Governance and reproducibility

Repository rules, phase control, error logging, deterministic unit tests, and manual workflows were established.

### Phase 1 — Strategy engine

The four-leg logic, expiry mathematics, holiday rolls, execution model, costs, lot-size handling, and metrics were implemented and tested.

### Phase 2 — Data audit

Point-in-time spot and option observations were checked for target cycles and required legs. The first implementation error — treating absent spot data as holidays — was detected and corrected before the final result was used.

### Phase 3 — Historical performance

Completed cycles were evaluated on the locked assumptions. Outputs include trade logs, equity paths, monthly attribution, per-leg contribution, drawdown and bootstrap intervals.

### Phase 4 — Robustness

Slippage and fixed-cost grids, break-even execution analysis, chronology blocks, and a descriptive prior-volatility regime context were calculated without modifying the primary strategy.

### Phase 5 — Statistical validation

A 6-block, all-2-of-6 combinatorial chronology diagnostic was applied. A single-trial PSR diagnostic was used because there was only one frozen strategy specification. Formal PBO and multi-trial DSR were marked not estimable rather than manufactured.

---

## 5. Performance Results

### 5.1 Primary performance

| Metric | NIFTY | SENSEX |
|---|---:|---:|
| Target cycles | 34 | 34 |
| Complete baskets | 33 | 28 |
| Total net P&L | ₹-44,822.58 | ₹-33,425.66 |
| ROC | -29.88% | -22.28% |
| Win rate | 36.36% | 25.00% |
| Maximum drawdown | ₹-44,857.28 | ₹-41,917.04 |
| Maximum drawdown % | -30.65% | -27.38% |
| Average profit | ₹1,846.11 | ₹2,093.82 |
| Average loss | ₹-3,189.33 | ₹-2,289.64 |
| Average profit / absolute loss | 0.579 | 0.914 |
| Expectancy per trade | ₹-1,358.26 | ₹-1,193.77 |
| Profit factor | 0.331 | 0.305 |
| Trade Sharpe diagnostic | -0.425 | -0.400 |

### 5.2 Bootstrap uncertainty

Deterministic bootstrap intervals for mean cycle P&L:

| Index | Mean P&L | 95% bootstrap interval |
|---|---:|---:|
| NIFTY | ₹-1,358.26 | ₹-2,421.79 to ₹-292.76 |
| SENSEX | ₹-1,193.77 | ₹-2,266.61 to ₹-97.38 |

The intervals remain below zero in this sample. This does not prove that the true future expectancy is negative; it indicates that the observed sample is inconsistent with a zero-mean trade outcome under the empirical bootstrap assumptions used.

### Figure 1 — Equity curve

[Equity curves SVG](figures/equity_curves.svg)

### 5.3 Monthly attribution

NIFTY:

| Month | Net P&L |
|---|---:|
| 2025-10 | ₹-15,849.89 |
| 2025-11 | ₹-10,760.08 |
| 2025-12 | ₹-5,847.09 |
| 2026-01 | ₹+980.65 |
| 2026-02 | ₹-775.70 |
| 2026-03 | ₹-9,091.25 |
| 2026-04 | ₹-2,909.57 |
| 2026-05 | ₹-569.63 |

SENSEX:

| Month | Net P&L |
|---|---:|
| 2025-10 | ₹-7,112.91 |
| 2025-11 | ₹-298.20 |
| 2025-12 | ₹-9,961.98 |
| 2026-01 | ₹-7,485.96 |
| 2026-02 | ₹-12,309.73 |
| 2026-03 | ₹-1,651.05 |
| 2026-04 | ₹+7,752.28 |
| 2026-05 | ₹-2,358.11 |

The negative result is therefore not driven by one isolated month.

---

## 6. Leg-Level Decomposition

| Index | Leg | Net P&L |
|---|---|---:|
| NIFTY | L1 monthly ATM PE buy | ₹+115,865.64 |
| NIFTY | L2 weekly ITM PE sell | ₹-133,147.86 |
| NIFTY | L3 weekly ATM CE buy | ₹-205,473.34 |
| NIFTY | L4 monthly ITM CE sell | ₹+180,344.34 |
| SENSEX | L1 monthly ATM PE buy | ₹+1,634.26 |
| SENSEX | L2 weekly ITM PE sell | ₹-11,554.67 |
| SENSEX | L3 weekly ATM CE buy | ₹-108,140.75 |
| SENSEX | L4 monthly ITM CE sell | ₹+116,852.08 |

The common feature is a negative contribution from L3, the weekly ATM call buy, and a positive contribution from L4, the monthly ITM call sale. This is a decomposition of the locked basket; it is not evidence that changing, removing, or reweighting the legs would improve future performance.

---

## 7. Execution and Cost Robustness

### 7.1 Zero-friction test

| Index | 0% slippage / ₹0 cost | 0% slippage / ₹160 cost | Primary 0.5% / ₹160 |
|---|---:|---:|---:|
| NIFTY | ₹-16,904 | ₹-22,184 | ₹-44,823 |
| SENSEX | ₹-13,599 | ₹-18,079 | ₹-33,426 |

This is the most important robustness finding. The strategy is already negative before the primary slippage assumption.

### Figure 2 — Slippage stress

[Slippage stress SVG](figures/slippage_stress.svg)

### 7.2 Break-even slippage

The calculated aggregate break-even slippage is approximately:
- NIFTY: -0.490%
- SENSEX: -0.589%

Because these values are negative, the observed basket would need an economically favorable execution improvement rather than merely zero slippage to reach aggregate break-even in this sample.

### 7.3 Fixed-cost and slippage grid

The full grid is stored under data/cache/phase4/. It varies slippage from 0% to 1% and fixed cycle cost from ₹0 to ₹320.

Both indices remain negative at every tested grid point. This indicates that the sign of the result is not a narrow consequence of the exact ₹160 / 0.5% assumptions.

---

## 8. Regime-Sensitivity Analysis

A descriptive prior-4-cycle spot-volatility measure was calculated without using future observations.

NIFTY aggregate P&L by descriptive regime:

| Regime | Trades | Net P&L | Mean P&L |
|---|---:|---:|---:|
| LOW | 14 | ₹-20,964.53 | ₹-1,497.47 |
| HIGH | 14 | ₹-8,008.16 | ₹-572.01 |
| UNCLASSIFIED | 5 | ₹-15,849.89 | ₹-3,169.98 |

SENSEX:

| Regime | Trades | Net P&L | Mean P&L |
|---|---:|---:|---:|
| LOW | 12 | ₹-29,070.33 | ₹-2,422.53 |
| HIGH | 10 | ₹+1,656.47 | ₹+165.65 |
| UNCLASSIFIED | 6 | ₹-6,011.80 | ₹-1,001.97 |

The SENSEX high-volatility slice is mildly positive, but it contains only 10 trades and was not selected ex ante. It is therefore a hypothesis for future research, not a validated regime rule.

No current-result claim is made about FII/DII flow, India VIX, gold, global markets, news, or corporate actions because those features were not used to select or explain the locked trade sample. They belong in the next conditional strategy-selection study rather than being retrofitted to the present result.

---

### Figure 3 — Leg-level decomposition

[Leg contribution SVG](figures/leg_contribution.svg)

## 9. CPCV-Style Stability

The research enumerated all 2-of-6 test-block combinations, giving 15 chronological test paths per index.

| Metric | NIFTY | SENSEX |
|---|---:|---:|
| Paths | 15 | 15 |
| Positive P&L paths | 6.7% | 20.0% |
| Median test Sharpe | -0.429 | -0.583 |
| Mean test Sharpe | -0.425 | -0.438 |
| Median test P&L | ₹-17,317 | ₹-10,083 |

The small percentage of positive paths is consistent with the negative full-sample result being distributed across time rather than isolated to a single subperiod.

### Figure 4 — CPCV path Sharpe

[CPCV path Sharpe SVG](figures/cpcv_path_sharpe.svg)

### Single-trial PSR diagnostic

| Index | Sharpe | PSR, P(Sharpe > 0) |
|---|---:|---:|
| NIFTY | -0.425 | 0.0074 |
| SENSEX | -0.400 | 0.0277 |

A formal multi-trial DSR is intentionally not reported because the study did not search over multiple independent candidate strategies before validation. Likewise, formal PBO is not estimable for one frozen strategy. The repository records this limitation rather than using cost-sensitivity variants as fake independent trials.

---

## 10. Cross-Index Discussion

The two indices exhibit the same sign of primary expectancy but different magnitudes and distributions.

NIFTY has a larger negative total P&L and larger negative ROC in the sample. Its average winning trade is smaller than its average losing trade in absolute terms, and its leg decomposition is dominated by a large negative L3 contribution partially offset by L4 and L1.

SENSEX has fewer completed baskets because of source-level contract/quote gaps and one missing 09:30 spot observation. Its average profit is larger relative to its average loss, yet the win rate is substantially lower. Its L3 contribution is again strongly negative and L4 strongly positive.

These results do not establish a universal liquidity ranking. The current data are close-based and do not contain synchronized bid/ask quotes. Consequently, the specific hypothesis that SENSEX deep-ITM monthly legs experience wider effective spreads or more frequent liquidity vacuums has not been quantified in this study.

The evidence instead supports a narrower statement: both markets produced negative expected trade P&L in the sampled period under the locked close-based execution model.

---

## 11. Strengths

1. The strategy specification was frozen before the historical performance analysis.
2. The exchange calendar is an explicit data input rather than being inferred from missing observations.
3. The data source revisions are pinned and recorded.
4. Contract lot-size changes are modeled rather than ignored.
5. Slippage and fixed costs are included in the primary result.
6. Missing legs are never backfilled with invented prices.
7. The research preserves skipped cycles and data-quality failures.
8. Statistical validation is separated from parameter optimization.
9. Every research phase is reproducible through a GitHub Actions workflow.
10. The final conclusion is based on the corrected result rather than an initially favorable or unfavorable implementation.

---

## 12. Limitations

### 12.1 Sample size

Only 33 NIFTY and 28 SENSEX completed baskets are available in the common primary window. The resulting confidence intervals and CPCV paths are necessarily wide and low-powered.

### 12.2 Execution data

The option input is OHLC/Close rather than synchronized order-book data. A 0.5% slippage proxy is therefore not a replacement for actual spread and queue-position modeling.

### 12.3 SENSEX 2026 calendar provenance

The current SENSEX 2026 holiday rows are transparently marked as mirrored from the common Indian market calendar and remain pending direct BSE confirmation.

### 12.4 Vendor/source constraints

The reduced cache is derived from public third-party data rather than an exchange-native point-in-time order book. Any discrepancies between vendor normalization and exchange identifiers can affect availability.

### 12.5 Strategy scope

The study tests one exact basket, not a family of nearby strike offsets, entry times, expiry pairings or dynamic hedging rules. The conclusion therefore applies to the tested specification, not to the entire reverse-calendar strategy class.

### 12.6 Unmodeled information

The primary rule does not condition on India VIX, realized volatility forecasts, FII/DII positioning, global equity futures, FX, rates, gold, macro releases, news, or corporate actions. Those are appropriate inputs for a separate strategy-selection phase, but adding them retroactively would contaminate the locked test.

---

## 13. Conclusion

The corrected historical evidence does not support promotion of the locked four-leg reverse-calendar basket as a production strategy for the tested NIFTY 50 and SENSEX sample.

The central result is robust in a particularly important sense: both indices remain negative even when the assumed 0.5% premium slippage and ₹160 fixed cycle cost are removed. Under the primary friction model, NIFTY loses approximately 29.9% of the ₹1,50,000 capital denominator and SENSEX approximately 22.3% over the completed trades. Expectancy is negative in both, maximum drawdown exceeds 27% of capital, and combinatorial chronological paths are predominantly negative.

The appropriate scientific conclusion is:

The exact locked four-leg specification did not demonstrate a durable positive historical edge in the corrected sample and should not be promoted to production without a materially stronger hypothesis and a new, independently validated test.

This conclusion does not falsify volatility-risk-premium research or reverse-calendar structures in general. It identifies the current specification as unsupported under the data, execution assumptions and validation framework used here.

---

## 14. Future Research

### 14.1 Bid/ask-aware execution

Acquire synchronized bid/ask, quote size, trade volume and order-book snapshots for all four legs. Replace the 0.5% premium slippage proxy with executable spread-aware fills.

### 14.2 Implied-volatility surface modelling

Reconstruct IV, skew, term structure and calendar slope at entry. Test whether the current basket is systematically entering when the weekly/monthly relative-value relationship is unfavorable.

### 14.3 Regime-conditioned strategy selection

Build a separate frozen model using only information known at entry:
- India VIX / realized-volatility state;
- trend and jump-risk state;
- FII/DII positioning;
- global index futures;
- USD/INR and rates;
- gold and cross-asset stress;
- news/event flags.

The strategy should be selected from a pre-registered candidate set, followed by untouched holdout validation.

### 14.4 Wider historical sample

Extend the sample backward using exchange-native historical F&O files and a reconciled contract master. The current 1-minute source begins too recently to support a long-horizon conclusion.

### 14.5 Execution-cost calibration

Replace the fixed ₹40/leg proxy with the actual broker/exchange/tax schedule applicable to the user's execution setup and the date of each trade, including brokerage, STT, exchange charges, GST and SEBI charges.

### 14.6 Cross-market inefficiency research

Compare the NIFTY and SENSEX surfaces conditional on the same macro regime. Investigate whether apparent cross-index differences are explained by liquidity, contract design, participant mix, or information timing rather than alpha.

### 14.7 Corporate actions and event risk

Flag expiry cycles overlapping major corporate events, index rebalances, macro announcements and exceptional settlement changes.

### 14.8 Production gate

Only consider paper trading after all of the following are satisfied:
1. direct bid/ask validation;
2. exchange-calendar and contract-master reconciliation;
3. larger historical sample;
4. walk-forward / CPCV validation;
5. untouched holdout;
6. realistic broker cost and slippage model;
7. independent reproduction of the result.

---

## Appendix A — Repository Reproducibility

Core research artifacts are stored in:
- src/multileg_options_backtest.py
- scripts/phase2_remote_extract.py
- scripts/phase3_historical_backtest.py
- scripts/phase4_robustness_stress.py
- scripts/phase5_cpcv_validation.py

Research outputs are stored under:
- data/cache/phase2/
- data/cache/phase3/
- data/cache/phase4/
- data/cache/phase5/

Manual workflows:
- .github/workflows/phase0-protocol-check.yml
- .github/workflows/phase1-backtest.yml
- .github/workflows/phase2-data-audit.yml
- .github/workflows/phase3-historical-backtest.yml
- .github/workflows/phase4-robustness-stress.yml
- .github/workflows/phase5-cpcv-validation.yml
- .github/workflows/phase6-manuscript.yml

---

## Appendix B — Source References

1. NSE, Equity Derivatives Contract Specifications: https://www.nseindia.com/static/products-services/equity-derivatives-contract-specifications
2. NSE, NIFTY 50 derivatives product information: https://www.nseindia.com/static/products-services/equity-derivatives-nifty50
3. BSE, June 23 2025 notice on SENSEX expiry-day revision: https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20250623-59
4. NSE Circular 176/2025 on revised NIFTY lot-size transition.
5. Hugging Face dataset rissin/nse-options-intraday, pinned revision 8f7739cab3f38abdcbc6332a6d0a83e1341326e3.
6. Hugging Face dataset thetrademarkk/india-index-options-1m, pinned revision 904fbfbf7d448e7007cd3dd197849ba561b30c06.
7. Lo (2004), Adaptive Markets Hypothesis.
8. Bollerslev, Tauchen & Zhou (2009), Variance Risk Premia.
9. Bailey et al. (2017), Probability of Backtest Overfitting.
10. Bailey & López de Prado (2014), Deflated Sharpe Ratio.
11. López de Prado (2018), Advances in Financial Machine Learning.

---

## Appendix C — Superseded Result Control

A pre-correction Phase 2 result was generated by incorrectly inferring exchange holidays from missing spot observations. It produced incorrect monthly expiry dates in several cycles and was explicitly superseded. The corrected extraction is the only result permitted for manuscript interpretation.

---

## Supplement — Research Control Principles

The study uses a locked primary specification, explicit missing-data handling, source revision pinning, deterministic costs, chronology-preserving validation, and an explicit stop condition. The repository logs every material implementation error and correction so that a later research branch cannot silently reproduce the same mistake.
