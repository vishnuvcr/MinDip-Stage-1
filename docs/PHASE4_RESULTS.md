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
