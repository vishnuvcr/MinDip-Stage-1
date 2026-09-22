# Phase 8 — Current Uploaded Screenshot Strategy

The latest uploaded screenshots supersede the earlier strategy interpretations for this backtest.

## Exact visible NIFTY basket

The editor screenshot shows NIFTY spot at 23,329 and four selected legs:

| Leg | Action | Expiry | Strike |
|---|---|---|---:|
| L1 | SELL | 27 Oct | 23,350 PE |
| L2 | BUY | 27 Oct | 23,250 CE |
| L3 | BUY | 06 Oct | 23,450 PE |
| L4 | SELL | 06 Oct | 23,350 CE |

The payoff screenshot shows the same four-leg basket and is labelled "MinDip Put Side".

## Generalized locked rule

For NIFTY:

- Strike interval = 50.
- ATM = nearest 50-point strike to the entry spot.
- L1 = **SELL monthly ATM PE**.
- L2 = **BUY monthly ATM − 2 strikes CE**.
- L3 = **BUY weekly ATM + 2 strikes PE**.
- L4 = **SELL weekly ATM CE**.

For SENSEX, the same payoff/position structure is generalized using its configured strike interval once its date-effective exchange expiry/contract calendar is validated.

## Screenshot consistency check

At NIFTY spot 23,329:

- nearest ATM = 23,350;
- monthly short PE = 23,350;
- monthly long CE = 23,250;
- weekly long PE = 23,450;
- weekly short CE = 23,350.

This is **not** the earlier strategy that was tested in Phases 1–6, and it is **not** the immediately previous Phase 7 interpretation.

The earlier results are explicitly superseded for the purpose of evaluating this uploaded strategy.

## Important distinction

The screenshot provides the exact example and therefore fixes the four positions. It does not prove that every future signal should use a particular expiry-day convention independently of the exchange contract master. The backtest continues to use date-effective exchange expiry rules and records the selected contracts.

## Execution model

The current backtest retains:
- 09:30 entry;
- simultaneous 15:15 weekly-expiry square-off;
- adverse premium slippage;
- ₹40 per leg fixed cost;
- historical lot size;
- no missing-leg imputation.

The primary Phase 8 result is the **current uploaded strategy only**.
