# Phase 2 Data Audit

## Objective

Produce a point-in-time, strategy-specific dataset without copying the complete third-party option archive.

## Acceptance checks

1. Spot observation exists at/after 09:30 for each eligible cycle.
2. Entry and exit option observations exist for all four target contracts.
3. Expiry fields are strictly after the entry date.
4. No duplicate contract/timestamp observations remain.
5. Strike and option-type fields are valid.
6. NIFTY and SENSEX symbols map unambiguously.
7. Source revision and file URLs are recorded.
8. Actual selected option expiry agrees with the user-defined weekly/monthly calendar after holiday roll, or the cycle is explicitly skipped and logged.
9. Lot size is assigned by expiry date and provenance is recorded.
10. No look-ahead occurs when selecting ATM or contracts.

## Primary calendar interpretation

The research rule, not a data-provider calendar, determines the target expiry:
- NIFTY weekly Tuesday; monthly last Tuesday; entry Wednesday.
- SENSEX weekly Thursday; monthly last Thursday; entry Friday.
- Holiday on target date: roll backward to the previous available trading date.

The source data are then used to check whether the exchange actually listed the selected expiry/contract and whether an executable observation is available.

## Execution proxy

The input is OHLC, not bid/ask. The locked primary execution model applies 0.5% adverse premium slippage to every leg on both entry and exit. A later phase must repeat the test with bid/ask or spread-aware execution before production claims.
