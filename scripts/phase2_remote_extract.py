from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd


OPTION_URLS = {
    "NIFTY": [
        "https://huggingface.co/datasets/rissin/nse-options-intraday/resolve/main/upstox_intraday/NIFTY/NIFTY_2025.parquet",
        "https://huggingface.co/datasets/rissin/nse-options-intraday/resolve/main/upstox_intraday/NIFTY/NIFTY_2026.parquet",
    ],
    "SENSEX": [
        "https://huggingface.co/datasets/rissin/nse-options-intraday/resolve/main/upstox_intraday/SENSEX/SENSEX_2025.parquet",
        "https://huggingface.co/datasets/rissin/nse-options-intraday/resolve/main/upstox_intraday/SENSEX/SENSEX_2026.parquet",
    ],
}

SPOT_URLS = {
    "NIFTY": "https://huggingface.co/datasets/thetrademarkk/india-index-options-1m/resolve/main/index/NIFTY.parquet",
    "SENSEX": "https://huggingface.co/datasets/thetrademarkk/india-index-options-1m/resolve/main/index/SENSEX.parquet",
}


@dataclass(frozen=True)
class StrategyRule:
    key: str
    weekday_expiry: int
    cycle_entry_weekday: int
    interval: float
    offset: float


RULES = {
    "NIFTY": StrategyRule("NIFTY", 1, 2, 50.0, 100.0),
    "SENSEX": StrategyRule("SENSEX", 3, 4, 100.0, 200.0),
}


def half_up_strike(spot: float, interval: float) -> float:
    return float(int((spot / interval) + 0.5) * interval)


def last_weekday(year: int, month: int, weekday: int) -> pd.Timestamp:
    first_next = (
        pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthBegin(1)
    ).normalize()
    last = first_next - pd.Timedelta(days=1)
    return last - pd.Timedelta(days=(last.weekday() - weekday) % 7)


def previous_trading_day(
    scheduled: pd.Timestamp,
    trading_dates: set[pd.Timestamp],
) -> pd.Timestamp | None:
    x = pd.Timestamp(scheduled).normalize()
    for _ in range(10):
        if x in trading_dates:
            return x
        x -= pd.Timedelta(days=1)
    return None


def next_expiry_after(
    entry: pd.Timestamp,
    rule: StrategyRule,
    trading_dates: set[pd.Timestamp],
) -> pd.Timestamp | None:
    x = entry + pd.Timedelta(days=1)
    for _ in range(21):
        if x.weekday() == rule.weekday_expiry:
            actual = previous_trading_day(x, trading_dates)
            if actual is not None and actual > entry:
                return actual
        x += pd.Timedelta(days=1)
    return None


def next_monthly_after(
    entry: pd.Timestamp,
    rule: StrategyRule,
    trading_dates: set[pd.Timestamp],
) -> pd.Timestamp | None:
    cursor = entry
    for _ in range(24):
        candidate = last_weekday(cursor.year, cursor.month, rule.weekday_expiry)
        actual = previous_trading_day(candidate, trading_dates)
        if actual is not None and actual > entry:
            return actual
        cursor = (cursor + pd.offsets.MonthBegin(1)).normalize()
    return None


def trading_cycle_dates(
    min_day: pd.Timestamp,
    max_day: pd.Timestamp,
    rule: StrategyRule,
    trading_dates: set[pd.Timestamp],
):
    current = pd.Timestamp(min_day).normalize()
    out = []
    while current <= pd.Timestamp(max_day).normalize():
        if current.weekday() == rule.cycle_entry_weekday:
            actual = previous_trading_day(current, trading_dates)
            if actual is not None and min_day <= actual <= max_day:
                out.append((current, actual))
        current += pd.Timedelta(days=1)
    return out


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def parquet_relation(urls: list[str]) -> str:
    return "read_parquet([" + ",".join(sql_quote(u) for u in urls) + "])"


def spot_query(
    con: duckdb.DuckDBPyConnection,
    ticker: str,
    start: str,
    end: str,
) -> pd.DataFrame:
    relation = parquet_relation([SPOT_URLS[ticker]])
    sql = f"""
        SELECT
            timestamp,
            trading_day,
            symbol,
            open,
            high,
            low,
            close,
            volume,
            open_interest
        FROM {relation}
        WHERE symbol = {sql_quote(ticker)}
          AND CAST(trading_day AS DATE) BETWEEN DATE {sql_quote(start)} AND DATE {sql_quote(end)}
          AND EXTRACT(HOUR FROM timestamp) = 9
          AND EXTRACT(MINUTE FROM timestamp) BETWEEN 30 AND 35
        ORDER BY timestamp
    """
    return con.execute(sql).df()


def build_cycles(
    spot: pd.DataFrame,
    ticker: str,
    start: str,
    end: str,
) -> pd.DataFrame:
    rule = RULES[ticker]
    days = set(pd.to_datetime(spot["trading_day"]).dt.normalize())
    pairs = trading_cycle_dates(pd.Timestamp(start), pd.Timestamp(end), rule, days)
    cycles = []

    for scheduled, entry in pairs:
        weekly = next_expiry_after(entry, rule, days)
        monthly = next_monthly_after(entry, rule, days)
        if weekly is None or monthly is None or weekly > pd.Timestamp(end):
            continue

        rows = spot[
            spot["trading_day"].eq(entry.strftime("%Y-%m-%d"))
        ].sort_values("timestamp")
        rows = rows[rows["timestamp"].dt.time >= pd.Timestamp("09:30:00").time()]
        if rows.empty:
            continue

        snap = rows.iloc[0]
        cycles.append(
            {
                "ticker": ticker,
                "scheduled_entry_date": scheduled,
                "entry_date": entry,
                "weekly_expiry": weekly,
                "monthly_expiry": monthly,
                "spot": float(snap["close"]),
                "spot_timestamp": pd.Timestamp(snap["timestamp"]),
                "atm_strike": half_up_strike(float(snap["close"]), rule.interval),
            }
        )

    return pd.DataFrame(cycles)


def option_extract(
    con: duckdb.DuckDBPyConnection,
    cycles: pd.DataFrame,
    ticker: str,
) -> pd.DataFrame:
    if cycles.empty:
        return pd.DataFrame()

    rule = RULES[ticker]
    wanted = []

    for _, c in cycles.iterrows():
        atm = float(c.atm_strike)
        legs = [
            ("L1", "BUY", "PE", c.monthly_expiry, atm),
            ("L2", "SELL", "PE", c.weekly_expiry, atm + rule.offset),
            ("L3", "BUY", "CE", c.weekly_expiry, atm),
            ("L4", "SELL", "CE", c.monthly_expiry, atm - rule.offset),
        ]
        for leg, side, opt_type, expiry, strike in legs:
            wanted.append(
                {
                    "ticker": ticker,
                    "leg": leg,
                    "side": side,
                    "option_type": opt_type,
                    "expiry": pd.Timestamp(expiry).strftime("%Y-%m-%d"),
                    "strike": float(strike),
                    "entry_date": pd.Timestamp(c.entry_date).strftime("%Y-%m-%d"),
                    "exit_date": pd.Timestamp(c.weekly_expiry).strftime("%Y-%m-%d"),
                    "monthly_expiry": pd.Timestamp(c.monthly_expiry).strftime("%Y-%m-%d"),
                    "weekly_expiry": pd.Timestamp(c.weekly_expiry).strftime("%Y-%m-%d"),
                    "scheduled_entry_date": pd.Timestamp(c.scheduled_entry_date).strftime("%Y-%m-%d"),
                    "spot": float(c.spot),
                    "atm_strike": float(c.atm_strike),
                    "spot_timestamp": pd.Timestamp(c.spot_timestamp),
                }
            )

    wanted_df = pd.DataFrame(wanted)
    dates = sorted(set(wanted_df["entry_date"]) | set(wanted_df["exit_date"]))
    expiries = sorted(set(wanted_df["expiry"]))

    date_list = ",".join("DATE " + sql_quote(d) for d in dates)
    expiry_list = ",".join("DATE " + sql_quote(d) for d in expiries)

    relation = parquet_relation(OPTION_URLS[ticker])
    sql = f"""
        SELECT
            timestamp,
            CAST(trading_day AS DATE) AS trading_day,
            symbol,
            CAST(expiry AS DATE) AS expiry,
            strike,
            option_type,
            open,
            high,
            low,
            close,
            volume,
            open_interest,
            source,
            granularity
        FROM {relation}
        WHERE symbol = {sql_quote(ticker)}
          AND CAST(trading_day AS DATE) IN ({date_list})
          AND CAST(expiry AS DATE) IN ({expiry_list})
          AND (
              (EXTRACT(HOUR FROM timestamp) = 9 AND EXTRACT(MINUTE FROM timestamp) BETWEEN 30 AND 35)
              OR
              (EXTRACT(HOUR FROM timestamp) = 15 AND EXTRACT(MINUTE FROM timestamp) BETWEEN 10 AND 15)
          )
    """

    observed = con.execute(sql).df()
    if observed.empty:
        return observed

    observed["timestamp"] = pd.to_datetime(observed["timestamp"])
    observed["trading_day"] = pd.to_datetime(observed["trading_day"]).dt.normalize()
    observed["expiry"] = pd.to_datetime(observed["expiry"]).dt.normalize()
    observed["key_strike"] = observed["strike"].astype(float)

    wanted_df["expiry"] = pd.to_datetime(wanted_df["expiry"]).dt.normalize()
    wanted_df["entry_date"] = pd.to_datetime(wanted_df["entry_date"]).dt.normalize()
    wanted_df["exit_date"] = pd.to_datetime(wanted_df["exit_date"]).dt.normalize()

    rows = []

    for _, w in wanted_df.iterrows():
        cand = observed[
            (observed["symbol"] == ticker)
            & (observed["expiry"] == w["expiry"])
            & observed["key_strike"].eq(float(w["strike"]))
            & (observed["option_type"] == w["option_type"])
            & observed["trading_day"].isin([w["entry_date"], w["exit_date"]])
        ].sort_values("timestamp")

        entry = cand[
            (cand["trading_day"] == w["entry_date"])
            & (cand["timestamp"].dt.time >= pd.Timestamp("09:30:00").time())
        ]
        exit_ = cand[
            (cand["trading_day"] == w["exit_date"])
            & (cand["timestamp"].dt.time <= pd.Timestamp("15:15:00").time())
        ]

        row = dict(w)

        if not entry.empty:
            e = entry.iloc[0]
            row.update(
                {
                    "entry_timestamp": e["timestamp"],
                    "entry_close": float(e["close"]),
                    "entry_volume": float(e["volume"]),
                    "entry_oi": None if pd.isna(e["open_interest"]) else float(e["open_interest"]),
                    "entry_source": e["source"],
                }
            )

        if not exit_.empty:
            x = exit_.iloc[-1]
            row.update(
                {
                    "exit_timestamp": x["timestamp"],
                    "exit_close": float(x["close"]),
                    "exit_volume": float(x["volume"]),
                    "exit_oi": None if pd.isna(x["open_interest"]) else float(x["open_interest"]),
                    "exit_source": x["source"],
                }
            )

        row["entry_available"] = "entry_close" in row
        row["exit_available"] = "exit_close" in row
        rows.append(row)

    return pd.DataFrame(rows)


def assign_lot_size(ticker: str, expiry: pd.Timestamp) -> int:
    expiry = pd.Timestamp(expiry).normalize()
    if ticker == "NIFTY":
        return 75 if expiry <= pd.Timestamp("2025-12-30") else 65
    if ticker == "SENSEX":
        return 20
    raise ValueError(ticker)


def apply_execution_and_metrics(
    legs: pd.DataFrame,
    cycles: pd.DataFrame,
    slippage: float = 0.005,
):
    if legs.empty:
        return cycles.iloc[0:0].copy(), pd.DataFrame(), {}

    leg_records = []

    for _, r in legs.iterrows():
        if not (r["entry_available"] and r["exit_available"]):
            continue

        side = r["side"]
        entry = r["entry_close"]
        exit_ = r["exit_close"]
        lot = assign_lot_size(r["ticker"], r["expiry"])

        if side == "BUY":
            entry_exec = entry * (1 + slippage)
            exit_exec = exit_ * (1 - slippage)
            pnl = (exit_exec - entry_exec) * lot
        else:
            entry_exec = entry * (1 - slippage)
            exit_exec = exit_ * (1 + slippage)
            pnl = (entry_exec - exit_exec) * lot

        q = dict(r)
        q.update(
            {
                "lot_size": lot,
                "entry_exec": entry_exec,
                "exit_exec": exit_exec,
                "leg_pnl": pnl,
            }
        )
        leg_records.append(q)

    selected = pd.DataFrame(leg_records)
    if selected.empty:
        return cycles.iloc[0:0].copy(), selected, {}

    out_cycles = []

    for cycle_key, grp in selected.groupby(
        ["ticker", "entry_date", "weekly_expiry", "monthly_expiry"]
    ):
        if set(grp["leg"]) != {"L1", "L2", "L3", "L4"}:
            continue

        net = float(grp["leg_pnl"].sum()) - 160.0
        row = cycles[
            (cycles["ticker"] == cycle_key[0])
            & (cycles["entry_date"] == pd.Timestamp(cycle_key[1]))
            & (cycles["weekly_expiry"] == pd.Timestamp(cycle_key[2]))
            & (cycles["monthly_expiry"] == pd.Timestamp(cycle_key[3]))
        ].iloc[0].to_dict()

        row.update(
            {
                "gross_pnl": float(grp["leg_pnl"].sum()),
                "fixed_cost": 160.0,
                "net_pnl": net,
                "legs_completed": len(grp),
            }
        )
        out_cycles.append(row)

    result = pd.DataFrame(out_cycles)
    metrics = {}

    if not result.empty:
        result = result.sort_values("entry_date").reset_index(drop=True)
        pnl = result["net_pnl"].astype(float)
        equity = 150000 + pnl.cumsum()
        peak = equity.cummax()
        dd = equity - peak
        wins = pnl[pnl > 0]
        losses = pnl[pnl < 0]

        metrics = {
            "trades": int(len(pnl)),
            "total_net_pnl": float(pnl.sum()),
            "roc_pct": float(pnl.sum() / 150000 * 100),
            "win_rate_pct": float((pnl > 0).mean() * 100),
            "max_drawdown": float(dd.min()),
            "max_drawdown_pct": float((equity / peak - 1).min() * 100),
            "average_profit": float(wins.mean()) if not wins.empty else 0.0,
            "average_loss": float(losses.mean()) if not losses.empty else 0.0,
            "average_profit_to_abs_loss": (
                float(wins.mean() / abs(losses.mean()))
                if not wins.empty and not losses.empty
                else None
            ),
            "expectancy_per_trade": float(pnl.mean()),
        }

    return result, selected, metrics


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2025-10-01")
    parser.add_argument("--end", default="2026-09-22")
    parser.add_argument("--output", default="data/cache/phase2")
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    con.execute("PRAGMA threads=4")

    all_metrics = []
    audit = []

    for ticker in ["NIFTY", "SENSEX"]:
        spot = spot_query(con, ticker, args.start, args.end)
        spot.to_csv(out / f"{ticker}_spot_0930.csv", index=False)

        cycles = build_cycles(spot, ticker, args.start, args.end)
        cycles.to_csv(out / f"{ticker}_cycles_target.csv", index=False)

        legs = option_extract(con, cycles, ticker)
        legs.to_csv(out / f"{ticker}_legs_quotes.csv", index=False)

        completed, selected, metrics = apply_execution_and_metrics(legs, cycles)
        completed.to_csv(out / f"{ticker}_completed_cycles.csv", index=False)
        selected.to_csv(out / f"{ticker}_selected_legs.csv", index=False)

        m = dict(metrics)
        m["ticker"] = ticker
        m["target_cycles"] = int(len(cycles))
        m["selected_legs"] = int(len(selected))
        m["complete_cycles"] = int(len(completed))
        all_metrics.append(m)

        audit.append(
            {
                "ticker": ticker,
                "spot_rows": int(len(spot)),
                "target_cycles": int(len(cycles)),
                "selected_leg_rows": int(len(selected)),
                "complete_cycles": int(len(completed)),
                "source_option_urls": json.dumps(OPTION_URLS[ticker]),
                "source_spot_url": SPOT_URLS[ticker],
            }
        )

    comparison = pd.DataFrame(all_metrics)
    comparison.to_csv(out / "cross_index_metrics.csv", index=False)
    pd.DataFrame(audit).to_csv(out / "data_audit_summary.csv", index=False)

    manifest = {
        "start": args.start,
        "end": args.end,
        "strategy": "locked four-leg reverse-calendar",
        "slippage_rate": 0.005,
        "fixed_cost_per_cycle": 160.0,
        "capital_denominator": 150000.0,
        "options_source_revision": "8f7739c",
        "files": {},
    }

    for p in sorted(out.glob("*")):
        manifest["files"][p.name] = {
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        }

    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
