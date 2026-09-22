[object Object]

## Verified CI result

The GitHub Actions calculation completed successfully before the cache rebase failure. Canonical outputs are stored in `data/cache/phase9/`. Verified values:
- intrinsic reconstructed ₹12,103 vs displayed ₹12,100;
- time value reconstructed -₹354.25 vs displayed -₹351;
- delta -0.040943 vs displayed -0.041;
- vega -0.66855 per 1 vol point vs displayed -0.67;
- POP reconstructed 95.38% vs displayed 96%.

The exact max-profit/max-loss curve and theta/decay convention are not yet fully reverse-engineered.

## Current Paytm execution-fee scenario

Paytm Money's current F&O FAQ says brokerage is ₹10 per unique executed F&O order. A four-leg entry plus four-leg exit therefore gives a brokerage-only illustration of ₹80 per completed basket, before statutory/regulatory/exchange charges, assuming one executed unique order per leg per side. This is a current operational reference, not a historical all-in fee schedule.
