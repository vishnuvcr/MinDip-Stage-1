# Phase 7 — Screenshot Strategy Reconciliation

## Why this phase exists

The earlier backtest implemented the original written parameterization. The newly supplied strategy slide is more specific and materially different.

The visible worked example has spot 25,049.55 and shows:

- Monthly PE: 25,000 PE
- Weekly ITM PE: 25,200 PE
- Weekly CE: 25,050 CE
- Monthly CE: 25,000 CE

The slide itself says:

1. Buy monthly PE which is ATM.
2. Sell ITM PE weekly.
3. Buy weekly call around ATM strike.
4. Sell monthly 1 or 2 strikes ITM versus Leg #3.

## Screenshot-derived implementation

For a spot between two strikes:

- monthly PE ATM = lower ATM strike;
- weekly CE ATM = upper ATM strike;
- weekly ITM PE = three strike intervals above the weekly CE ATM, because that reproduces the visible 25,200 PE example;
- monthly CE = one strike below the weekly CE ATM in the primary screenshot-exact variant;
- a two-strike monthly CE variant is also tested because the slide explicitly says 1 or 2 strikes.

For 25,049.55 on a 50-point grid this gives:

- monthly PE = 25,000;
- weekly ITM PE = 25,200;
- weekly CE = 25,050;
- monthly CE, 1-strike variant = 25,000;
- monthly CE, 2-strike variant = 24,950.

The primary variant is the one-strike monthly CE because that is the leg visible in the screenshot.

## Important uncertainty

The slide does not state a numeric universal offset for Leg 2. The value of three strikes above the weekly CE is therefore frozen as an inference from the visible worked example, not presented as a textual rule from the slide.

Changing that offset later would be a new candidate strategy and must not overwrite these results.
