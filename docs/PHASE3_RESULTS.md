# Phase 3 — Historical Backtest

## Objective

Compute the locked primary historical result from the corrected Phase 2 cache without changing the strategy rules.

## Statistical outputs

The workflow produces:
- trade-level P&L and equity/drawdown path;
- monthly attribution;
- per-leg contribution;
- ROC, win rate, maximum drawdown, average profit/loss, expectancy, profit factor;
- per-trade Sharpe diagnostic and skewness;
- deterministic bootstrap 95% intervals for mean P&L and win rate.

## Primary interpretation rule

The Phase 2 sample is not a strategy-selection exercise. The rule is fixed in advance and the statistics are descriptive/inferential diagnostics of that single specification. No parameters are tuned to improve the result.

## Known limitations

- The primary dataset contains OHLC/close-based execution rather than full bid/ask.
- The locked 0.5% premium slippage is a deterministic execution proxy.
- SENSEX 2026 holiday rows are provisionally mirrored from the NSE market calendar and should be independently reconciled against direct BSE holiday records before a final manuscript.
- The completed trade counts are small, so confidence intervals are wide and CPCV/DSR/PBO promotion should be conservative.
