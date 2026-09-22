from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

CAPITAL = 150_000.0
SLIPPAGE = 0.005
FIXED_COST = 160.0

def nearest_atm(spot: float, interval: float) -> float:
    return float(np.floor((float(spot) / interval) + 0.5) * interval)

def lot_size(ticker: str, expiry: pd.Timestamp) -> int:
    expiry = pd.Timestamp(expiry).normalize()
    if ticker == "NIFTY":
        return 75 if expiry <= pd.Timestamp("2025-12-30") else 65
    if ticker == "SENSEX":
        return 20
    raise ValueError(ticker)

def metrics(cycles: pd.DataFrame) -> dict:
    if cycles.empty:
        return {"trades":0,"net_pnl":0.0,"roc_pct":0.0,"win_rate_pct":0.0,"expectancy":0.0,
                "max_drawdown":0.0,"max_drawdown_pct":0.0,"avg_win":0.0,"avg_loss":0.0}
    p = cycles["net_pnl"].astype(float)
    eq = CAPITAL + p.cumsum()
    peak = eq.cummax()
    wins = p[p > 0]
    losses = p[p < 0]
    return {
        "trades": int(len(p)),
        "net_pnl": float(p.sum()),
        "roc_pct": float(p.sum() / CAPITAL * 100.0),
        "win_rate_pct": float((p > 0).mean() * 100.0),
        "expectancy": float(p.mean()),
        "max_drawdown": float((eq - peak).min()),
        "max_drawdown_pct": float(((eq / peak) - 1).min() * 100.0),
        "avg_win": float(wins.mean()) if not wins.empty else 0.0,
        "avg_loss": float(losses.mean()) if not losses.empty else 0.0,
    }

def compute_current_strategy_from_phase2(ticker: str, input_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = input_root / f"{ticker}_selected_legs.csv"
    if not source.exists():
        raise FileNotFoundError(source)

    old = pd.read_csv(
        source,
        parse_dates=["entry_date","weekly_expiry","monthly_expiry","expiry","entry_timestamp","exit_timestamp"],
    )

    required = {
        "ticker","leg","side","option_type","expiry","strike","entry_date",
        "weekly_expiry","monthly_expiry","spot","entry_close","exit_close",
        "entry_available","exit_available","lot_size"
    }
    missing = sorted(required - set(old.columns))
    if missing:
        raise ValueError(f"{ticker}: Phase 2 cache missing {missing}")

    # The latest uploaded screenshot uses the same four contracts as the original
    # strike set, but reverses the direction of every leg and rearranges the labels:
    # sell monthly ATM PE; buy monthly ATM-2 CE; buy weekly ATM+2 PE; sell weekly ATM CE.
    mapping = {
        "L1": ("L1_SELL_MONTHLY_ATM_PE","SELL"),
        "L4": ("L2_BUY_MONTHLY_ATM_MINUS_2_CE","BUY"),
        "L2": ("L3_BUY_WEEKLY_ATM_PLUS_2_PE","BUY"),
        "L3": ("L4_SELL_WEEKLY_ATM_CE","SELL"),
    }
    old = old[old["leg"].isin(mapping)].copy()
    old["new_leg"] = old["leg"].map(lambda x: mapping[x][0])
    old["new_side"] = old["leg"].map(lambda x: mapping[x][1])

    interval = 50.0 if ticker == "NIFTY" else 100.0
    expected_atm = old["spot"].astype(float).map(lambda x: nearest_atm(x, interval))
    rules = {
        "L1_SELL_MONTHLY_ATM_PE": ("PE", 0),
        "L2_BUY_MONTHLY_ATM_MINUS_2_CE": ("CE", -2),
        "L3_BUY_WEEKLY_ATM_PLUS_2_PE": ("PE", 2),
        "L4_SELL_WEEKLY_ATM_CE": ("CE", 0),
    }
    old["expected_option_type"] = old["new_leg"].map(lambda x: rules[x][0])
    old["expected_strike"] = [
        float(a + rules[leg][1] * interval)
        for a, leg in zip(expected_atm, old["new_leg"])
    ]
    old["mapping_ok"] = (
        old["option_type"].eq(old["expected_option_type"])
        & np.isclose(old["strike"].astype(float), old["expected_strike"].astype(float))
    )
    bad = old.loc[~old["mapping_ok"]]
    if not bad.empty:
        raise ValueError(f"{ticker}: {len(bad)} rows failed the current screenshot mapping")

    rows = []
    for _, r in old.iterrows():
        side = r["new_side"]
        entry = float(r["entry_close"]) if pd.notna(r["entry_close"]) else np.nan
        exit_ = float(r["exit_close"]) if pd.notna(r["exit_close"]) else np.nan
        if bool(r["entry_available"]) and bool(r["exit_available"]):
            lot = lot_size(ticker, r["expiry"])
            if side == "BUY":
                entry_exec = entry * (1 + SLIPPAGE)
                exit_exec = exit_ * (1 - SLIPPAGE)
                pnl = (exit_exec - entry_exec) * lot
            else:
                entry_exec = entry * (1 - SLIPPAGE)
                exit_exec = exit_ * (1 + SLIPPAGE)
                pnl = (entry_exec - exit_exec) * lot
        else:
            entry_exec = np.nan
            exit_exec = np.nan
            pnl = np.nan

        q = r.to_dict()
        q.update({
            "strategy_id": "current_uploaded_screenshot",
            "leg": r["new_leg"],
            "side": side,
            "entry_exec": entry_exec,
            "exit_exec": exit_exec,
            "leg_pnl": pnl,
            "atm_strike": float(expected_atm.loc[r.name]),
            "strike_mapping": "PASS",
        })
        rows.append(q)

    legs = pd.DataFrame(rows)
    cycles = []
    for key, grp in legs.groupby(["ticker","entry_date","weekly_expiry","monthly_expiry"]):
        if len(grp) != 4:
            continue
        if not (grp["entry_available"] & grp["exit_available"]).all():
            continue
        cycles.append({
            "ticker": ticker,
            "entry_date": key[1],
            "weekly_expiry": key[2],
            "monthly_expiry": key[3],
            "spot": float(grp["spot"].iloc[0]),
            "atm_strike": float(grp["atm_strike"].iloc[0]),
            "gross_pnl": float(grp["leg_pnl"].sum()),
            "fixed_cost": FIXED_COST,
            "net_pnl": float(grp["leg_pnl"].sum() - FIXED_COST),
        })
    return pd.DataFrame(cycles), legs

def demo() -> dict:
    spot = 23329.0
    interval = 50.0
    atm = nearest_atm(spot, interval)
    return {
        "spot": spot,
        "atm": atm,
        "sell_monthly_pe": atm,
        "buy_monthly_ce": atm - 2 * interval,
        "buy_weekly_pe": atm + 2 * interval,
        "sell_weekly_ce": atm,
    }

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1_048_576), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2025-10-01")
    ap.add_argument("--end", default="2026-05-27")
    ap.add_argument("--output", default="data/cache/phase8")
    ap.add_argument("--ticker", choices=["NIFTY","SENSEX","BOTH"], default="BOTH")
    args = ap.parse_args()

    input_root = Path("data/cache/phase2")
    output_root = Path(args.output)
    output_root.mkdir(parents=True, exist_ok=True)
    tickers = ["NIFTY","SENSEX"] if args.ticker == "BOTH" else [args.ticker]

    all_metrics = []
    for ticker in tickers:
        cycles, legs = compute_current_strategy_from_phase2(ticker, input_root)
        legs.to_csv(output_root / f"{ticker}_current_legs.csv", index=False)
        cycles.to_csv(output_root / f"{ticker}_current_cycles.csv", index=False)
        m = metrics(cycles)
        m.update({
            "ticker": ticker,
            "strategy_id": "current_uploaded_screenshot",
            "target_cached_cycles": int(legs["entry_date"].nunique()) if not legs.empty else 0,
            "complete_cycles": int(len(cycles)),
            "sample_start": args.start,
            "sample_end": args.end,
        })
        all_metrics.append(m)

    pd.DataFrame(all_metrics).to_csv(output_root / "cross_index_metrics.csv", index=False)
    (output_root / "screenshot_strike_demo.json").write_text(json.dumps(demo(), indent=2))
    manifest = {"strategy":"current_uploaded_screenshot","sample_start":args.start,"sample_end":args.end,"files":{}}
    for p in sorted(output_root.glob("*")):
        manifest["files"][p.name] = {"bytes":p.stat().st_size,"sha256":sha(p)}
    (output_root / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(pd.DataFrame(all_metrics).to_string(index=False))

if __name__ == "__main__":
    main()
