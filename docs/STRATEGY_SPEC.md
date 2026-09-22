# Phase 1 Strategy Specification

## Locked trade rule

At 09:30 IST on the configured cycle-entry day:

| Leg | Action | Expiry | Strike |
|---|---|---|---|
| 1 | Buy | Next monthly expiry strictly after entry | ATM PE |
| 2 | Sell | Next weekly expiry strictly after entry | ATM + 2 strikes PE |
| 3 | Buy | Next weekly expiry strictly after entry | ATM CE |
| 4 | Sell | Next monthly expiry strictly after entry | ATM − 2 strikes CE |

Cycle exits all four legs at 15:15 IST on the selected weekly expiry date.

## Index configuration

NIFTY:
- 50-point strike interval.
- 2-strike ITM offset = 100 points.
- Weekly expiry Tuesday.
- Monthly expiry = last Tuesday.
- Cycle entry Wednesday.

SENSEX:
- 100-point strike interval.
- 2-strike ITM offset = 200 points.
- Weekly expiry Thursday.
- Monthly expiry = last Thursday.
- Cycle entry Friday.

## Holiday logic

The scheduled entry/expiry day is rolled backward to the latest observed trading date. For this implementation, observed trading dates come from the option dataset after any explicit holiday exclusion. This avoids forward-looking holiday assumptions but creates a data-quality dependency: a missing data date can look like a holiday. Phase 2 therefore requires an exchange calendar audit.

## Execution

Entry uses the first available Close observation at or after 09:30 on the entry date. Exit uses the last available Close observation at or before 15:15 on the exit date.

Because the input is Close-only, the backtest cannot directly measure the true bid/ask spread. The 0.5% adverse premium slippage is therefore a deterministic execution proxy, not a microstructure reconstruction.

## Slippage and fixed cost

For a long option:
- entry execution = Close × (1 + 0.005)
- exit execution = Close × (1 − 0.005)

For a short option:
- entry execution = Close × (1 − 0.005)
- exit execution = Close × (1 + 0.005)

A fixed ₹40 cost is charged per leg for the cycle, i.e. ₹160 total per completed basket.

## Capital and lot size

ROC uses ₹1,50,000 as the fixed capital/margin denominator.

The engine takes lot_size as a parameter. Default 1 means one contract unit, not an exchange lot. For a production result, pass the date-appropriate exchange lot size so option premium P&L is scaled correctly. Lot sizes can change over time.

## Missing-data rule

The primary backtest is all-or-nothing at the cycle level. If any required leg cannot be resolved under strict strike matching, the cycle is skipped and the reason is preserved in skipped_cycles.csv.

A non-strict strike mode is available for diagnostic work, but it is not the locked primary rule.
