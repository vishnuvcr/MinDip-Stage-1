# Phase 2 Data Audit

## Objective

Produce a point-in-time, strategy-specific dataset without copying the complete third-party option archive.

## Final corrected sample

- Common window: 2025-10-01 through 2026-05-27.
- Target cycles: 34 NIFTY, 34 SENSEX.
- Fully executable baskets: 33 NIFTY, 28 SENSEX.
- NIFTY incomplete cycles: 1 (missing monthly 26,000 PE quote for the Dec-30-2025 expiry cycle).
- SENSEX incomplete cycles: 5 among the target set: one missing 09:30 spot observation and four contract/exit quote-coverage gaps.

## Critical methodology correction

The first Phase 2 extractor used observed spot dates as a trading calendar. That was wrong because missing spot observations are data gaps, not proof of exchange holidays. This caused incorrect monthly expiry assignments in the first result.

The corrected implementation uses the explicit holiday file data/calendar/exchange_holidays.csv and keeps spot availability separate from the exchange calendar.

Examples affected by the superseded logic included SENSEX October 2025 and NIFTY May 2026 monthly expiry assignment. Those outputs were discarded and overwritten by the corrected cache.

## Data acceptance checks

1. Spot observation exists at/after 09:30 for each eligible cycle.
2. Entry and exit option observations exist for all four target contracts.
3. Expiry fields are strictly after entry where applicable.
4. No duplicate contract/timestamp observations remain in the selected execution rows.
5. Strike and option-type fields are valid.
6. NIFTY and SENSEX symbols map unambiguously.
7. Source revision and file URLs are pinned.
8. Target expiry agrees with the locked Tuesday/Thursday calendar after explicit holiday roll.
9. Date-appropriate lot size is assigned.
10. Missing observations are logged rather than filled.

## Execution limitation

The input contains Close/OHLC observations rather than synchronized bid/ask. The locked 0.5% slippage model is therefore an execution proxy. Spread-aware production validation remains future work.

## Calendar caveat

The 2026 SENSEX holiday rows in the current explicit calendar are mirrored from the common Indian market holiday schedule and remain pending direct BSE confirmation. This caveat is retained throughout the manuscript.
