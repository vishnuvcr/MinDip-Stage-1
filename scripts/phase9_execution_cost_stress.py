from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

CAPITAL = 150_000.0
PAYTM_CURRENT_BROKERAGE_PER_UNIQUE_ORDER = 10.0
PAYTM_BROKERAGE_ONLY_PER_CYCLE = 8 * PAYTM_CURRENT_BROKERAGE_PER_UNIQUE_ORDER


def cycle_terms(path: Path, ticker: str) -> pd.DataFrame:
    legs = pd.read_csv(path, parse_dates=["entry_date", "weekly_expiry", "monthly_expiry", "expiry"])
    required = {"leg", "side", "entry_close", "exit_close", "lot_size", "entry_available", "exit_available",
                "entry_date", "weekly_expiry", "monthly_expiry"}
    missing = required - set(legs.columns)
    if missing:
        raise ValueError(f"{ticker}: missing columns {sorted(missing)}")

    expected_legs = {
        "L1_SELL_MONTHLY_ATM_PE",
        "L2_BUY_MONTHLY_ATM_MINUS_2_CE",
        "L3_BUY_WEEKLY_ATM_PLUS_2_PE",
        "L4_SELL_WEEKLY_ATM_CE",
    }

    rows = []
    for key, g in legs.groupby(["entry_date", "weekly_expiry", "monthly_expiry"]):
        if len(g) != 4 or set(g["leg"]) != expected_legs:
            continue
        if not (g["entry_available"] & g["exit_available"]).all():
            continue

        raw = 0.0
        friction_coeff = 0.0
        for _, r in g.iterrows():
            e = float(r["entry_close"])
            x = float(r["exit_close"])
            lot = float(r["lot_size"])
            if r["side"] == "BUY":
                raw += (x - e) * lot
            else:
                raw += (e - x) * lot
            friction_coeff -= (e + x) * lot

        rows.append({
            "ticker": ticker,
            "entry_date": key[0],
            "weekly_expiry": key[1],
            "monthly_expiry": key[2],
            "raw_gross_pnl": raw,
            "slippage_pnl_per_1pct": friction_coeff,
        })

    return pd.DataFrame(rows)


def stress_table(base: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for ticker, g in base.groupby("ticker"):
        for slip in [0.0, 0.0005, 0.001, 0.0015, 0.002, 0.0025, 0.003, 0.004, 0.005]:
            for fixed_cost_name, fixed_cost in [
                ("paytm_brokerage_only_current", PAYTM_BROKERAGE_ONLY_PER_CYCLE),
                ("locked_research_cost", 160.0),
                ("two_times_locked_cost", 320.0),
            ]:
                pnl = g["raw_gross_pnl"] + g["slippage_pnl_per_1pct"] * slip - fixed_cost
                equity = CAPITAL + pnl.cumsum()
                peak = equity.cummax()
                rows.append({
                    "ticker": ticker,
                    "slippage_pct": slip * 100.0,
                    "fixed_cost": fixed_cost,
                    "fixed_cost_name": fixed_cost_name,
                    "trades": int(len(pnl)),
                    "net_pnl": float(pnl.sum()),
                    "roc_pct": float(pnl.sum() / CAPITAL * 100.0),
                    "win_rate_pct": float((pnl > 0).mean() * 100.0),
                    "expectancy": float(pnl.mean()),
                    "max_drawdown": float((equity - peak).min()),
                    "profit_factor": (
                        float(pnl[pnl > 0].sum() / abs(pnl[pnl < 0].sum()))
                        if (pnl < 0).any() else np.inf
                    ),
                })
    return pd.DataFrame(rows)


def break_even_slippage(base: pd.DataFrame, fixed_cost: float) -> pd.DataFrame:
    rows = []
    for ticker, g in base.groupby("ticker"):
        raw = float(g["raw_gross_pnl"].sum())
        coeff = float(g["slippage_pnl_per_1pct"].sum())
        s = (raw - fixed_cost) / (-coeff) if coeff < 0 else np.nan
        rows.append({
            "ticker": ticker,
            "fixed_cost": fixed_cost,
            "break_even_slippage_pct": float(s * 100.0) if np.isfinite(s) else np.nan,
            "break_even_slippage_bps": float(s * 10_000.0) if np.isfinite(s) else np.nan,
        })
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="data/cache/phase9_execution")
    args = ap.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    paths = {
        "NIFTY": Path("data/cache/phase8/NIFTY/NIFTY_current_legs.csv"),
        "SENSEX": Path("data/cache/phase8/NIFTY/SENSEX_current_legs.csv"),
    }

    rows = []
    for ticker, path in paths.items():
        if not path.exists():
            raise FileNotFoundError(path)
        rows.append(cycle_terms(path, ticker))

    base = pd.concat(rows, ignore_index=True)
    base.to_csv(out / "current_strategy_cycle_terms.csv", index=False)

    stress = stress_table(base)
    stress.to_csv(out / "execution_cost_stress.csv", index=False)

    be = pd.concat(
        [
            break_even_slippage(base, PAYTM_BROKERAGE_ONLY_PER_CYCLE),
            break_even_slippage(base, 160.0),
            break_even_slippage(base, 320.0),
        ],
        ignore_index=True,
    )
    be.to_csv(out / "break_even_slippage.csv", index=False)

    pd.DataFrame(
        [{
            "paytm_current_brokerage_per_unique_order": PAYTM_CURRENT_BROKERAGE_PER_UNIQUE_ORDER,
            "assumed_unique_orders_per_completed_cycle": 8,
            "paytm_current_brokerage_only_per_cycle": PAYTM_BROKERAGE_ONLY_PER_CYCLE,
            "note": "Brokerage-only illustration. Current statutory/regulatory/exchange charges are additional and are levied at actuals; historical all-in costs require date-specific tariff reconstruction.",
        }]
    ).to_csv(out / "paytm_fee_assumption.csv", index=False)

    print(stress[stress["fixed_cost_name"] == "paytm_brokerage_only_current"].to_string(index=False))
    print("\nBreak-even slippage:")
    print(be.to_string(index=False))


if __name__ == "__main__":
    main()
