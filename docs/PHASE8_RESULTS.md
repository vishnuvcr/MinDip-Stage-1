# Phase 8 Results — Current Uploaded Screenshot Strategy

## Strategy locked from latest screenshots

The latest editor screenshot shows NIFTY 23,329 and exactly these four contracts:

| Leg | Action | Expiry | Strike |
|---|---|---|---:|
| L1 | SELL | Monthly | 23,350 PE |
| L2 | BUY | Monthly | 23,250 CE |
| L3 | BUY | Weekly | 23,450 PE |
| L4 | SELL | Weekly | 23,350 CE |

Generalized rule used in the current backtest:

- nearest ATM strike from 09:30 spot;
- SELL monthly ATM PE;
- BUY monthly ATM − 2 strike intervals CE;
- BUY weekly ATM + 2 strike intervals PE;
- SELL weekly ATM CE.

For NIFTY the interval is 50 points. For SENSEX the same four-position geometry is scaled to its configured 100-point interval.

## Exact screenshot consistency check

At spot 23,329:

- nearest ATM = 23,350;
- monthly short PE = 23,350;
- monthly long CE = 23,250;
- weekly long PE = 23,450;
- weekly short CE = 23,350.

The cached validation rows all pass the exact strike-mapping check.

## Backtest window

2025-10-01 through 2026-05-27.

The calculation reuses the Phase 2 point-in-time option quote cache because it contains the same four underlying contracts for each cycle. This avoids a second remote extraction and ensures the strategy comparison uses identical source observations.

## Primary execution model

- Entry: 09:30 IST.
- Exit: 15:15 IST on weekly expiry.
- One lot per leg using date-effective lot size.
- 0.5% adverse premium slippage on every leg at entry and exit.
- ₹40 per leg, ₹160 per completed four-leg cycle.
- Missing-leg cycles are skipped rather than imputed.
- Capital denominator: ₹1,50,000.

NSE's current NIFTY contract specification confirms Tuesday weekly expiry and last-Tuesday monthly expiry, with previous-trading-day adjustment when Tuesday is a holiday. The Phase 2 contract/date cache is used for the historical sample.

## Results

| Metric | NIFTY | SENSEX |
|---|---:|---:|
| Target cached cycles | 34 | 32 |
| Complete cycles | 33 | 28 |
| Net P&L | ₹-11,014.58 | ₹-6,227.26 |
| ROC | -7.34% | -4.15% |
| Win rate | 42.42% | 39.29% |
| Positive trades | 14 | 11 |
| Negative trades | 19 | 17 |
| Average profit | ₹2,739.06 | ₹2,434.35 |
| Average loss | ₹-2,597.97 | ₹-1,941.48 |
| Expectancy/trade | ₹-333.78 | ₹-222.40 |
| Profit factor | 0.777 | 0.811 |
| Maximum drawdown | ₹-32,805.10 | ₹-18,786.89 |
| Maximum drawdown (%) | -19.10% | -11.56% |

## Friction decomposition

The sign pattern is important.

| Execution assumption | NIFTY | SENSEX |
|---|---:|---:|
| 0.00% slippage + ₹160 cost | ₹11,624.00 | ₹9,119.20 |
| 0.10% slippage + ₹160 cost | ₹7,096.28 | ₹6,049.91 |
| 0.25% slippage + ₹160 cost | ₹304.71 | ₹1,445.97 |
| 0.50% slippage + ₹160 cost | ₹-11,014.58 | ₹-6,227.26 |

With the ₹160 fixed cycle cost retained, the algebraic break-even premium slippage is approximately:

- NIFTY: 0.2567%
- SENSEX: 0.2971%

Thus the current uploaded strategy is positive before the 0.5% slippage assumption, but the declared 0.5% adverse premium-slippage model pushes the aggregate result negative.

## Interpretation

The current screenshot strategy has a much smaller historical loss than the earlier incorrectly interpreted structure. More importantly, the result is highly execution-sensitive: the historical gross signal survives a 0.25% slippage assumption but not 0.5% in this sample.

That makes direct bid/ask validation the key next research step. Close-only data cannot establish whether 0.25% or 0.50% was historically executable, especially on the deep-ITM/near-ATM legs.

## Research status

This result is the corrected primary result for the latest uploaded screenshot strategy. It should be used for any subsequent robustness, CPCV, DSR/PBO, and manuscript work concerning this strategy. Older Phase 6 and Phase 7 numerical results remain archived as superseded experiments.