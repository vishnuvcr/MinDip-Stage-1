# Phase 1 Results

## Status

Implementation complete pending external-data validation.

## Software verification

Deterministic unit tests cover:
- NIFTY and SENSEX configuration.
- ATM strike rounding.
- Weekly and monthly expiry mathematics.
- Previous-trading-day holiday roll.
- Complete four-leg cycle execution.
- Adverse 0.5% slippage at entry and exit.
- ₹160 fixed cycle cost.
- ROC, win rate, and expectancy calculations.
- Cycle skipping when a required leg is unavailable.

## Empirical results

No historical empirical result is reported in Phase 1 because the target repository contains no production market dataset yet. Any synthetic fixture output is test evidence only and must not be interpreted as trading performance.

## Next gate

Phase 2 requires a point-in-time option dataset with reliable spot observations, exchange holiday/calendar validation, contract-master validation, and lot-size history.
