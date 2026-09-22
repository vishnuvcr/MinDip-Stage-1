from __future__ import annotations

import argparse
import itertools
import math
from pathlib import Path

import numpy as np
import pandas as pd


CAPITAL = 150_000.0


def sharpe(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=float)
    if len(values) < 2:
        return np.nan
    sd = values.std(ddof=1)
    return float(values.mean() / sd) if sd > 0 else np.nan


def binomial_two_sided_pvalue(wins: int, n: int, p: float = 0.5) -> float:
    def tail(k: int) -> float:
        return sum(
            math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
            for i in range(k, n + 1)
        )
    low_tail = tail(wins)
    high_tail = tail(n - wins)
    return float(min(1.0, 2.0 * min(low_tail, high_tail)))


def psr_under_zero(values: np.ndarray) -> float:
    """Probabilistic Sharpe Ratio diagnostic for a single frozen trial.

    This is reported instead of manufacturing a multi-trial Deflated Sharpe
    Ratio. With one locked strategy, the multiple-testing component of DSR is
    not identifiable from the research design.
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n < 3:
        return np.nan
    s = values.std(ddof=1)
    if s <= 0:
        return np.nan
    sr = values.mean() / s
    centered = values - values.mean()
    skew = float((centered ** 3).mean() / (values.std(ddof=0) ** 3))
    kurt = float((centered ** 4).mean() / (values.std(ddof=0) ** 4))
    denom = math.sqrt(max(1e-12, 1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr * sr))
    z = sr * math.sqrt(n - 1.0) / denom
    # Normal CDF without scipy.
    cdf = 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return float(cdf)


def load_trade_log(ticker: str, root: Path) -> pd.DataFrame:
    p = root / "data" / "cache" / "phase3" / f"{ticker}_trade_log.csv"
    df = pd.read_csv(p, parse_dates=["entry_date", "weekly_expiry", "monthly_expiry"])
    return df.sort_values("entry_date").reset_index(drop=True)


def cpcv_paths(trades: pd.DataFrame, n_blocks: int = 6, n_test_blocks: int = 2) -> pd.DataFrame:
    blocks = np.array_split(np.arange(len(trades)), min(n_blocks, len(trades)))
    block_ids = {i: set(block.tolist()) for i, block in enumerate(blocks)}
    records = []

    for test_block_tuple in itertools.combinations(sorted(block_ids), n_test_blocks):
        test_ids = sorted(set().union(*(block_ids[i] for i in test_block_tuple)))
        test = trades.iloc[test_ids]
        vals = test["net_pnl"].to_numpy(dtype=float)
        equity = CAPITAL + np.cumsum(vals)
        peak = np.maximum.accumulate(equity)
        dd = equity - peak

        records.append(
            {
                "ticker": trades["ticker"].iloc[0],
                "test_blocks": "-".join(str(i + 1) for i in test_block_tuple),
                "test_trades": len(vals),
                "test_mean_pnl": float(vals.mean()),
                "test_total_pnl": float(vals.sum()),
                "test_roc_pct": float(vals.sum() / CAPITAL * 100.0),
                "test_win_rate_pct": float((vals > 0).mean() * 100.0),
                "test_sharpe": sharpe(vals),
                "test_max_drawdown": float(dd.min()),
                "positive_path": bool(vals.sum() > 0),
            }
        )

    return pd.DataFrame(records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/cache/phase5")
    args = parser.parse_args()

    root = Path(".")
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    path_tables = []
    summary_rows = []
    psr_rows = []
    pbo_rows = []

    for ticker in ["NIFTY", "SENSEX"]:
        trades = load_trade_log(ticker, root)
        paths = cpcv_paths(trades, n_blocks=6, n_test_blocks=2)
        paths.to_csv(out / f"{ticker}_cpcv_paths.csv", index=False)
        path_tables.append(paths)

        positive_fraction = float(paths["positive_path"].mean()) if not paths.empty else np.nan
        summary_rows.append(
            {
                "ticker": ticker,
                "trades": len(trades),
                "cpcv_blocks": 6,
                "test_blocks_per_path": 2,
                "paths": len(paths),
                "positive_path_fraction_pct": positive_fraction * 100.0,
                "median_test_sharpe": float(paths["test_sharpe"].median()),
                "mean_test_sharpe": float(paths["test_sharpe"].mean()),
                "median_test_pnl": float(paths["test_total_pnl"].median()),
                "all_trade_sharpe": sharpe(trades["net_pnl"].to_numpy(dtype=float)),
            }
        )

        vals = trades["net_pnl"].to_numpy(dtype=float)
        wins = int((vals > 0).sum())
        psr_rows.append(
            {
                "ticker": ticker,
                "all_trade_sharpe": sharpe(vals),
                "psr_p_gt_zero": psr_under_zero(vals),
                "wins": wins,
                "trades": len(vals),
                "two_sided_binomial_pvalue_vs_50pct_winrate": binomial_two_sided_pvalue(
                    wins, len(vals)
                ),
                "interpretation": (
                    "single-frozen-trial PSR diagnostic; formal DSR multiple-testing adjustment is not identifiable"
                ),
            }
        )

        pbo_rows.append(
            {
                "ticker": ticker,
                "pbo_status": "not_estimable",
                "reason": "Only one locked primary strategy specification was tested; cost/slippage grid is sensitivity analysis, not independent strategy trials.",
                "positive_cpcv_path_fraction_pct": positive_fraction * 100.0,
            }
        )

    summary = pd.DataFrame(summary_rows)
    psr = pd.DataFrame(psr_rows)
    pbo = pd.DataFrame(pbo_rows)
    all_paths = pd.concat(path_tables, ignore_index=True)

    summary.to_csv(out / "cpcv_summary.csv", index=False)
    all_paths.to_csv(out / "cpcv_all_paths.csv", index=False)
    psr.to_csv(out / "psr_single_trial_diagnostic.csv", index=False)
    pbo.to_csv(out / "pbo_status.csv", index=False)

    print(summary.to_string(index=False))
    print(psr.to_string(index=False))
    print(pbo.to_string(index=False))


if __name__ == "__main__":
    main()
