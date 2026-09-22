# Phase 9 — Execution Cost Stress

## Current Paytm brokerage reference

Paytm Money's current F&O FAQ states ₹10 brokerage per unique F&O order. Assuming one unique executed order per leg for entry and one per leg for exit gives eight unique orders per completed four-leg basket, or a **₹80 brokerage-only** scenario before statutory/regulatory/exchange charges. This is a current operational reference, not a historical all-in tariff reconstruction.

## Stress grid

Premium slippage tested:
0.00%, 0.05%, 0.10%, 0.15%, 0.20%, 0.25%, 0.30%, 0.40%, 0.50%.

Fixed-cost scenarios:
- current Paytm brokerage-only illustration: ₹80/cycle;
- locked research cost: ₹160/cycle;
- doubled stress: ₹320/cycle.

## Break-even slippage

| Fixed-cost scenario | NIFTY | SENSEX |
|---|---:|---:|
| ₹80 current brokerage-only | 0.3150% | 0.3701% |
| ₹160 locked research cost | 0.2567% | 0.2971% |
| ₹320 stress cost | 0.1401% | 0.1511% |

At the current ₹80 brokerage-only illustration, the strategy therefore tolerates more execution friction than under the original ₹160 research proxy. However, this does not establish that historical all-in execution was achievable at those thresholds.

## Key operational scenarios

| Slippage | NIFTY, ₹80 cost | SENSEX, ₹80 cost |
|---|---:|---:|
| 0.00% | ₹14,264 | ₹11,359 |
| 0.25% | ₹2,945 | ₹3,686 |
| 0.30% | ₹681 | ₹2,151 |
| 0.40% | ₹-3,847 | ₹-918 |
| 0.50% | ₹-8,375 | ₹-3,987 |

Under the locked ₹160/cycle model:
- 0.25%: NIFTY +₹305; SENSEX +₹1,446.
- 0.30%: NIFTY -₹1,959; SENSEX -₹89.
- 0.50%: NIFTY -₹11,015; SENSEX -₹6,227.

## Interpretation

The current strategy has a narrow but observable execution-cost boundary. The next research gate is therefore historical spread reconstruction, not parameter optimization.

Close-only option data cannot determine whether the required slippage thresholds were executable. The critical missing variables are bid/ask spread, queue position, partial fills, market impact, and exact date-specific statutory charges.
