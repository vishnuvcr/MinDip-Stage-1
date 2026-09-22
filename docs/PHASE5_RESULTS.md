# Phase 5 — CPCV / DSR / PBO

## Goal

Assess chronology stability and guard against over-interpreting a single historical sample.

## CPCV implementation

The corrected trade logs are divided into six chronology blocks per index. All 2-of-6 test-block combinations are evaluated. Immediate neighboring blocks are purged from the training subset. Because the strategy has no parameters fitted on the training set, train statistics are reported only as diagnostics; test statistics provide the cross-validated stability distribution.

A separate untouched final-block holdout is reported and is not used to alter the strategy.

## DSR

A standard Deflated Sharpe Ratio is a multiple-trial correction and is most meaningful when several candidate strategies have been selected. This research has one prespecified primary strategy. The Phase 5 output therefore reports the observed trade-level Sharpe, skewness and excess kurtosis, but explicitly marks multiple-trial DSR as not estimable rather than manufacturing an artificial trial count.

## PBO

Probability of Backtest Overfitting likewise needs a candidate family plus a model-selection step. Implementation-friction stress points are not independent strategy candidates. With one locked primary specification, PBO is therefore reported as not estimable.

## Additional diagnostic

A sign-flip permutation test for zero mean trade P&L is included as a distribution-free diagnostic. It does not replace the preregistered cost/robustness analysis and does not create a strategy-selection loop.

## Decision discipline

No Phase 5 diagnostic is used to tune the primary parameters. If the diagnostics disagree with the aggregate historical result, the discrepancy is recorded as uncertainty rather than used to choose a more favorable variant.
