from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


CAPITAL = 150_000.0
PRIMARY_SLIPPAGE = 0.005
PRIMARY_COST = 160.0


def load_complete_legs(ticker: str, root: Path) -> pd.DataFrame:
    path = root / "data" / "cache" / "phase2" / f"{ticker}_selected_legs.csv"
    df = pd.read_csv(path, parse_dates=["entry_date", "weekly_expiry", "monthly_expiry", "expiry"])
    key = ["entry_date", "weekly_expiry", "monthly_expiry"]

    good_keys = (
        df.groupby(key)
        .filter(
            lambda x: len(x) == 4
            and set(x["leg"]) == {"L1", "L2", "L3", "L4"}
            and bool(x["entry_available"].all())
            and bool(x["exit_available"].all())
        )[key]
        .drop_duplicates()
    )
    return df.merge(good_keys, on=key, how="inner").sort_values(["entry_date", "leg"]).reset_index(drop=True)


def leg_pnl(row: pd.Series, slippage: float) -> float:
    entry = float(row["entry_close"])
    exit_ = float(row["exit_close"])
    lot = float(row["lot_size"])
    if row["side"] == "BUY":
        return (exit_ * (1.0 - slippage) - entry * (1.0 + slippage)) * lot
    return (entry * (1.0 - slippage) - exit_ * (1.0 + slippage)) * lot


def cycle_grid(legs: pd.DataFrame, slippages: list[float], costs: list[float]) -> pd.DataFrame:
    records = []
    keys = ["ticker", "entry_date", "weekly_expiry", "monthly_expiry"]
    for key, grp in legs.groupby(keys):
        raw = float(sum(leg_pnl(r, 0.0) for _, r in grp.iterrows()))
        for s in slippages:
            gross = float(sum(leg_pnl(r, s) for _, r in grp.iterrows()))
            for cost in costs:
                net = gross - cost
                records.append(
                    {
                        "ticker": key[0],
                        "entry_date": key[1],
                        "weekly_expiry": key[2],
                        "monthly_expiry": key[3],
                        "slippage_pct": s * 100.0,
                        "fixed_cost_per_cycle": cost,
                        "gross_pnl": gross,
                        "net_pnl": net,
                        "raw_close_pnl_no_slippage": raw,
                    }
                )
    return pd.DataFrame(records)


def summarize_grid(grid: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (ticker, s, cost), g in grid.groupby(["ticker", "slippage_pct", "fixed_cost_per_cycle"]):
        pnl = g["net_pnl"]
        rows.append(
            {
                "ticker": ticker,
                "slippage_pct": s,
                "fixed_cost_per_cycle": cost,
                "trades": len(pnl),
                "total_net_pnl": float(pnl.sum()),
                "roc_pct": float(pnl.sum() / CAPITAL * 100.0),
                "win_rate_pct": float((pnl > 0).mean() * 100.0),
                "expectancy": float(pnl.mean()),
                "max_drawdown": float((CAPITAL + pnl.cumsum() - (CAPITAL + pnl.cumsum()).cummax()).min()),
            }
        )
    return pd.DataFrame(rows).sort_values(["ticker", "slippage_pct", "fixed_cost_per_cycle"])


def break_even_slippage(legs: pd.DataFrame, cost: float) -> dict:
    total_base = 0.0
    total_coeff = 0.0
    trades = 0
    for _, grp in legs.groupby(["ticker", "entry_date", "weekly_expiry", "monthly_expiry"]):
        trades += 1
        for _, r in grp.iterrows():
            e = float(r["entry_close"])
            x = float(r["exit_close"])
            lot = float(r["lot_size"])
            if r["side"] == "BUY":
                total_base += (x - e) * lot
            else:
                total_base += (e - x) * lot
            total_coeff -= (e + x) * lot
    # total P&L = total_base + s * total_coeff - cost * trades.
    # Since total_coeff is negative, solve total P&L=0.
    s = (-(total_base - cost * trades) / total_coeff) if total_coeff != 0 else np.nan
    return {
        "ticker": legs["ticker"].iloc[0],
        "trades": trades,
        "zero_slippage_zero_cost_pnl": total_base,
        "zero_slippage_primary_cost_pnl": total_base - cost * trades,
        "break_even_slippage_decimal": s,
        "break_even_slippage_pct": s * 100.0,
    }


def chronology_blocks(legs: pd.DataFrame, n_blocks: int = 6) -> pd.DataFrame:
    cycles = (
        legs.groupby(["ticker", "entry_date"], as_index=False)
        .agg(
            net_raw_pnl=("entry_close", "size"),
            entry_date=("entry_date", "first"),
        )
        .sort_values(["ticker", "entry_date"])
    )
    out = []
    for ticker, g in cycles.groupby("ticker"):
        g = g.sort_values("entry_date").reset_index(drop=True)
        idx = np.array_split(np.arange(len(g)), min(n_blocks, len(g)))
        for block_id, ids in enumerate(idx):
            if len(ids) == 0:
                continue
            out.append(
                {
                    "ticker": ticker,
                    "block": block_id + 1,
                    "start": g.loc[ids[0], "entry_date"],
                    "end": g.loc[ids[-1], "entry_date"],
                    "trades": len(ids),
                }
            )
    return pd.DataFrame(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/cache/phase4")
    args = parser.parse_args()

    root = Path(".")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    slippages = [0.0, 0.0025, 0.005, 0.0075, 0.01]
    costs = [0.0, 80.0, 160.0, 240.0, 320.0]

    all_legs = []
    summaries = []
    break_evens = []

    for ticker in ["NIFTY", "SENSEX"]:
        legs = load_complete_legs(ticker, root)
        all_legs.append(legs)
        grid = cycle_grid(legs, slippages, costs)
        grid.to_csv(out / f"{ticker}_slippage_cost_grid.csv", index=False)
        summaries.append(summarize_grid(grid))
        break_evens.append(break_even_slippage(legs, PRIMARY_COST))

        # A non-forward-looking descriptive regime proxy:
        # 4-cycle rolling standard deviation of log spot-entry returns, using
        # only observations available before the current cycle.
        target = pd.read_csv(
            root / "data" / "cache" / "phase2" / f"{ticker}_cycles_target.csv",
            parse_dates=["entry_date"],
        ).sort_values("entry_date")
        target["log_return"] = np.log(target["spot"]).diff()
        target["prior_4cycle_vol"] = target["log_return"].rolling(4, min_periods=4).std().shift(1)
        target["vol_regime"] = np.where(
            target["prior_4cycle_vol"].notna(),
            np.where(
                target["prior_4cycle_vol"] > target["prior_4cycle_vol"].median(),
                "HIGH",
                "LOW",
            ),
            "UNCLASSIFIED",
        )
        target[["ticker", "entry_date", "spot", "log_return", "prior_4cycle_vol", "vol_regime"]].to_csv(
            out / f"{ticker}_regime_context.csv", index=False
        )

    summary = pd.concat(summaries, ignore_index=True)
    summary.to_csv(out / "cross_index_slippage_cost_summary.csv", index=False)
    pd.DataFrame(break_evens).to_csv(out / "break_even_slippage.csv", index=False)
    chronology_blocks(pd.concat(all_legs, ignore_index=True)).to_csv(
        out / "chronology_blocks.csv", index=False
    )

    print(summary.to_string(index=False))
    print(pd.DataFrame(break_evens).to_string(index=False))


if __name__ == "__main__":
    main()
