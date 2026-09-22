# Phase 4 — Robustness and Cost Stress

## Design

The primary rule remains locked at 0.5% adverse premium slippage and ₹160 fixed cost per completed basket. Phase 4 does not select a different parameter.

Sensitivity grids vary:
- slippage: 0%, 0.25%, 0.50%, 0.75%, 1.00%;
- fixed cycle cost: ₹0, ₹80, ₹160, ₹240, ₹320.

Additional diagnostics:
- algebraic break-even slippage;
- chronology blocks;
- a descriptive prior-4-cycle spot-volatility regime context that uses only information available before each cycle.

## Execution-data limitation

No full bid/ask history is currently in the Phase 2 cache. Spread/liquidity stress cannot be measured directly. The 0.5% premium slippage remains the locked proxy. This is an explicit limitation, not a missing-data substitution.

## Interpretation rule

A negative result at 0% slippage and ₹0 fixed cost is materially different from a result that fails only after transaction costs. The Phase 4 report will preserve that distinction.


## Corrected primary findings

Across the complete-cycle sample, the fixed strategy is already negative before the primary execution friction is imposed:

| Index | Complete trades | P&L at 0% slippage / ₹0 cost | P&L at 0% slippage / ₹160 cost | P&L at primary 0.5% / ₹160 cost |
|---|---:|---:|---:|---:|
| NIFTY | 33 | ₹-16,904 | ₹-22,184 | ₹-44,823 |
| SENSEX | 28 | ₹-13,599 | ₹-18,079 | ₹-33,426 |

The algebraic break-even slippage is negative for both samples (approximately -0.490% for NIFTY and -0.589% for SENSEX). This means the basket would still have negative aggregate P&L after setting slippage to zero; the 0.5% execution proxy worsens an already-negative close-to-close result.

The descriptive prior-4-cycle spot-volatility split is not used for selection. NIFTY remains negative in both the low- and high-volatility partitions. SENSEX is negative in the low-volatility partition and mildly positive in the small high-volatility partition; this is descriptive and not sufficient to support a regime-conditioned strategy because the sample is small and the regime label is derived from a simple historical spot proxy.

## Cross-index interpretation

The primary evidence is that both indices show negative aggregate expectancy under the locked rule, with different magnitudes and leg contributions. NIFTY's largest negative contribution comes from L3 (weekly ATM CE); SENSEX also has a large negative L3 contribution. L4 contributes positively in both samples. These are descriptive decomposition results, not a strategy reweighting recommendation.

Direct bid/ask or spread stress remains unavailable from the current source, so the data do not establish the magnitude of any SENSEX-specific liquidity-vacuum effect. That question remains for a later execution-data study.
