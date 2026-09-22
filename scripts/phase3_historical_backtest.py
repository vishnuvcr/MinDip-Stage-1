from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


CAPITAL = 150_000.0
FIXED_COST = 160.0
DEFAULT_BOOTSTRAPS = 10_000
RNG_SEED = 20260922


def max_drawdown(pnl: pd.Series) -> tuple[float, float]:
    equity = CAPITAL + pnl.cumsum()
    peak = equity.cummax()
    dd = equity - peak
    dd_pct = equity / peak - 1.0
    return float(dd.min()), float(dd_pct.min() * 100.0)


def trade_metrics(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {
            "trades": 0,
            "total_net_pnl": 0.0,
            "roc_pct": 0.0,
            "win_rate_pct": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "average_profit": 0.0,
            "average_loss": 0.0,
            "average_profit_to_abs_loss": np.nan,
            "expectancy_per_trade": 0.0,
            "profit_factor": np.nan,
            "trade_sharpe": np.nan,
            "skewness": np.nan,
        }

    pnl = trades["net_pnl"].astype(float)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    dd, dd_pct = max_drawdown(pnl)

    gross_profit = float(wins.sum()) if not wins.empty else 0.0
    gross_loss_abs = float(abs(losses.sum())) if not losses.empty else 0.0

    return {
        "trades": int(len(pnl)),
        "total_net_pnl": float(pnl.sum()),
        "roc_pct": float(pnl.sum() / CAPITAL * 100.0),
        "win_rate_pct": float((pnl > 0).mean() * 100.0),
        "max_drawdown": dd,
        "max_drawdown_pct": dd_pct,
        "average_profit": float(wins.mean()) if not wins.empty else 0.0,
        "average_loss": float(losses.mean()) if not losses.empty else 0.0,
        "average_profit_to_abs_loss": (
            float(wins.mean() / abs(losses.mean()))
            if not wins.empty and not losses.empty
            else np.nan
        ),
        "expectancy_per_trade": float(pnl.mean()),
        "profit_factor": (
            gross_profit / gross_loss_abs if gross_loss_abs > 0 else np.nan
        ),
        "trade_sharpe": (
            float(pnl.mean() / pnl.std(ddof=1))
            if len(pnl) > 1 and pnl.std(ddof=1) > 0
            else np.nan
        ),
        "skewness": (
            float((((pnl - pnl.mean()) ** 3).mean()) / (pnl.std(ddof=0) ** 3))
            if len(pnl) > 2 and pnl.std(ddof=0) > 0
            else np.nan
        ),
    }


def bootstrap_mean(values: np.ndarray, n_bootstrap: int, seed: int) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(n_bootstrap, len(values)), replace=True)
    means = samples.mean(axis=1)
    return float(values.mean()), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def bootstrap_win_rate(values: np.ndarray, n_bootstrap: int, seed: int) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    if len(values) == 0:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    wins = (values > 0).astype(float)
    samples = rng.choice(wins, size=(n_bootstrap, len(wins)), replace=True)
    rates = samples.mean(axis=1)
    return float(wins.mean()), float(np.quantile(rates, 0.025)), float(np.quantile(rates, 0.975))


def build_outputs(ticker: str, root: Path, n_bootstrap: int) -> dict:
    base = root / "data" / "cache" / "phase2"
    cycles_path = base / f"{ticker}_completed_cycles.csv"
    legs_path = base / f"{ticker}_selected_legs.csv"

    cycles = pd.read_csv(cycles_path, parse_dates=["entry_date", "weekly_expiry", "monthly_expiry"])
    legs = pd.read_csv(legs_path, parse_dates=["entry_date", "weekly_expiry", "monthly_expiry", "expiry"])

    if cycles.empty:
        raise ValueError(f"No completed cycles for {ticker}.")

    cycles = cycles.sort_values("entry_date").reset_index(drop=True)
    cycles["equity"] = CAPITAL + cycles["net_pnl"].cumsum()
    peak = cycles["equity"].cummax()
    cycles["drawdown"] = cycles["equity"] - peak
    cycles["drawdown_pct"] = cycles["equity"] / peak - 1.0
    cycles["year_month"] = cycles["entry_date"].dt.to_period("M").astype(str)

    monthly = (
        cycles.groupby("year_month", as_index=False)
        .agg(
            trades=("net_pnl", "size"),
            net_pnl=("net_pnl", "sum"),
            mean_pnl=("net_pnl", "mean"),
            win_rate=("net_pnl", lambda x: float((x > 0).mean() * 100.0)),
            min_trade=("net_pnl", "min"),
            max_trade=("net_pnl", "max"),
        )
        .sort_values("year_month")
    )
    monthly["cumulative_pnl"] = monthly["net_pnl"].cumsum()
    monthly["cumulative_roc_pct"] = monthly["cumulative_pnl"] / CAPITAL * 100.0

    leg_contribution = (
        legs.groupby(["leg", "side", "option_type"], as_index=False)
        .agg(
            observations=("leg_pnl", "size"),
            net_pnl=("leg_pnl", "sum"),
            mean_pnl=("leg_pnl", "mean"),
            median_pnl=("leg_pnl", "median"),
            win_rate=("leg_pnl", lambda x: float((x > 0).mean() * 100.0)),
        )
        .sort_values("leg")
    )

    metrics = trade_metrics(cycles)
    mean, ci_low, ci_high = bootstrap_mean(
        cycles["net_pnl"].to_numpy(),
        n_bootstrap,
        RNG_SEED,
    )
    wr, wr_low, wr_high = bootstrap_win_rate(
        cycles["net_pnl"].to_numpy(),
        n_bootstrap,
        RNG_SEED + 1,
    )

    metrics.update(
        {
            "ticker": ticker,
            "capital_denominator": CAPITAL,
            "fixed_cost_per_cycle": FIXED_COST,
            "mean_pnl_bootstrap": mean,
            "mean_pnl_bootstrap_ci_low": ci_low,
            "mean_pnl_bootstrap_ci_high": ci_high,
            "win_rate_bootstrap": wr * 100.0,
            "win_rate_bootstrap_ci_low": wr_low * 100.0,
            "win_rate_bootstrap_ci_high": wr_high * 100.0,
            "first_entry": cycles["entry_date"].min(),
            "last_entry": cycles["entry_date"].max(),
            "positive_trades": int((cycles["net_pnl"] > 0).sum()),
            "negative_trades": int((cycles["net_pnl"] < 0).sum()),
            "zero_trades": int((cycles["net_pnl"] == 0).sum()),
        }
    )

    return {
        "cycles": cycles,
        "monthly": monthly,
        "legs": leg_contribution,
        "metrics": pd.DataFrame([metrics]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="+", choices=["NIFTY", "SENSEX"], default=["NIFTY", "SENSEX"])
    parser.add_argument("--output", default="data/cache/phase3")
    parser.add_argument("--bootstraps", type=int, default=DEFAULT_BOOTSTRAPS)
    args = parser.parse_args()

    root = Path(".")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    metric_rows = []
    all_trades = []
    all_monthly = []
    all_legs = []

    for ticker in args.tickers:
        result = build_outputs(ticker, root, args.bootstraps)
        result["cycles"].to_csv(out / f"{ticker}_trade_log.csv", index=False)
        result["monthly"].to_csv(out / f"{ticker}_monthly_attribution.csv", index=False)
        result["legs"].to_csv(out / f"{ticker}_leg_contribution.csv", index=False)
        result["metrics"].to_csv(out / f"{ticker}_metrics.csv", index=False)

        metric_rows.append(result["metrics"])
        all_trades.append(result["cycles"].assign(ticker=ticker))
        all_monthly.append(result["monthly"].assign(ticker=ticker))
        all_legs.append(result["legs"].assign(ticker=ticker))

    comparison = pd.concat(metric_rows, ignore_index=True)
    comparison.to_csv(out / "cross_index_metrics.csv", index=False)
    pd.concat(all_trades, ignore_index=True).to_csv(out / "cross_index_trade_log.csv", index=False)
    pd.concat(all_monthly, ignore_index=True).to_csv(out / "cross_index_monthly_attribution.csv", index=False)
    pd.concat(all_legs, ignore_index=True).to_csv(out / "cross_index_leg_contribution.csv", index=False)

    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
