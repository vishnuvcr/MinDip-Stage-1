# Phase 9 Conclusion — Current Uploaded Screenshot Strategy

## Strategy identity

The current authoritative strategy is the latest uploaded four-leg NIFTY/SENSEX structure:

- SELL monthly ATM PE
- BUY monthly ATM−2-strike CE
- BUY weekly ATM+2-strike PE
- SELL weekly ATM CE

For the NIFTY screenshot at 23,329, the visible contracts are 23,350 PE sold, 23,250 CE bought, 23,450 PE bought, and 23,350 CE sold.

## Broker-model conclusion

The broker's multi-expiry valuation architecture is strongly supported by the screenshots.

Using separate futures 23,436.90 for the weekly expiry and 23,510.00 for the monthly expiry:

- intrinsic value reconstructs to ₹12,103 vs displayed ₹12,100;
- time value reconstructs to about -₹354 vs displayed -₹351;
- portfolio delta reconstructs to -0.04094 vs displayed -0.041;
- portfolio vega reconstructs to -0.6685 per 1 vol point vs displayed -0.67;
- POP reconstructs to about 95.38% vs displayed 96%.

This is sufficient to treat the broker chart as a multi-expiry Black-76-like valuation model for research purposes. It is not proof of the broker's proprietary implementation.

The exact theta/decay convention and exact max-profit/max-loss curve remain only partially identified.

## Historical performance conclusion

For 2025-10-01 through 2026-05-27:

| Metric | NIFTY | SENSEX |
|---|---:|---:|
| Complete cycles | 33 | 28 |
| Net P&L at 0.5% slippage + ₹160 cost | ₹-11,014.58 | ₹-6,227.26 |
| ROC | -7.34% | -4.15% |
| Win rate | 42.42% | 39.29% |
| Mean trade | ₹-333.78 | ₹-222.40 |
| Untouched final block | ₹-5,002.63 | ₹-2,991.38 |

## Execution threshold

The strategy is positive before sufficient execution friction is applied.

Under the current Paytm brokerage-only illustration of ₹80 per completed basket:

- NIFTY break-even slippage ≈ 0.3150%;
- SENSEX break-even slippage ≈ 0.3701%.

Under the locked ₹160 research-cost proxy:

- NIFTY ≈ 0.2567%;
- SENSEX ≈ 0.2971%.

At 0.50% slippage the historical result is negative for both indices.

## Robustness conclusion

Six-block CPCV was mixed:

- positive test-block combinations: 40.0% NIFTY, 46.7% SENSEX;
- median test mean P&L remained negative;
- untouched final chronology block was negative for both;
- bootstrap 95% intervals for mean trade P&L included zero.

Therefore the evidence does not establish a stable, out-of-sample positive edge.

## Execution-data limitation

The current historical source contains 1-minute OHLC/volume data rather than historical bid/ask quotes. Upstox documentation confirms that bid/ask fields exist in live/full market feeds, but the historical dataset used in this research was assembled from 1-minute OHLC candles and does not contain those quote fields. Exact historical spread/queue/market-impact reconstruction therefore remains unavailable from the current cached source.

## Final research disposition

The strategy should be classified as **execution-sensitive and statistically inconclusive**, not as a validated production strategy and not as disproven.

The strongest current finding is:

> The payoff structure and broker valuation are coherent, and the historical gross signal is positive before enough execution friction is applied; however, the observed margin over execution cost is too small to establish robust tradability without historical bid/ask and exact all-in fee reconstruction.

No parameter optimization is authorized from this result. A new candidate strategy must be a separate research experiment.
