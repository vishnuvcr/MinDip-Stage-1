# Phase 5 — CPCV / DSR / PBO Validation

## Validation design

The strategy specification is frozen before validation. We use a 6-block chronology and enumerate all 2-block test-set combinations (15 paths per index) as a CPCV-style stability diagnostic.

Because there is no model selection inside the locked rule, this is not a full predictive-model CPCV implementation. It answers a simpler question: does the same rule remain economically positive across many chronological recombinations?

## DSR / PSR

A formal Deflated Sharpe Ratio requires a meaningful count of independent strategy trials. The primary study has one frozen strategy specification. Rather than fabricate a multiple-testing penalty, the repository reports a single-trial Probabilistic Sharpe Ratio diagnostic and explicitly records formal multi-trial DSR as not identifiable.

## PBO

Probability of Backtest Overfitting is likewise not identifiable for one frozen strategy. The cost/slippage grid is a robustness sensitivity analysis, not a set of independently selected candidate strategies, so it is not used to manufacture a PBO estimate.

## Promotion rule

A strategy remains unsupported when the negative primary expectancy is accompanied by predominantly negative CPCV test paths or a non-positive PSR diagnostic. A positive result in only a small subset of paths is preserved as a descriptive finding rather than a promotion signal.
