from __future__ import annotations

import argparse
import itertools
from pathlib import Path

import numpy as np
import pandas as pd

CAPITAL = 150_000.0
SEED = 20260923


def bootstrap_mean(values: np.ndarray, n: int, seed: int) -> tuple[float,float,float]:
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(n, len(values)), replace=True).mean(axis=1)
    return float(values.mean()), float(np.quantile(samples, .025)), float(np.quantile(samples, .975))


def metrics(p):
    p = pd.Series(p, dtype=float)
    wins, losses = p[p > 0], p[p < 0]
    return {
        "trades": int(len(p)),
        "net_pnl": float(p.sum()) if len(p) else np.nan,
        "mean_pnl": float(p.mean()) if len(p) else np.nan,
        "win_rate_pct": float((p > 0).mean() * 100) if len(p) else np.nan,
        "profit_factor": float(wins.sum()/abs(losses.sum())) if len(losses) and losses.sum() < 0 else np.nan,
        "trade_sharpe": float(p.mean()/p.std(ddof=1)) if len(p)>1 and p.std(ddof=1)>0 else np.nan,
    }


def cpcv(trades: pd.DataFrame, blocks: int = 6) -> pd.DataFrame:
    t = trades.sort_values("entry_date").copy()
    t["block"] = pd.qcut(np.arange(len(t)), q=blocks, labels=False, duplicates="drop") + 1

    rows = []
    block_ids = sorted(t["block"].unique())
    for test in itertools.combinations(block_ids, 2):
        test = tuple(int(x) for x in test)
        excluded = set(test)
        for b in test:
            excluded.update({b-1, b+1})
        train = t[~t["block"].isin(excluded)]["net_pnl"]
        out = t[t["block"].isin(test)]["net_pnl"]
        m = metrics(out)
        rows.append({
            "test_block_1": test[0],
            "test_block_2": test[1],
            "purged_blocks": ",".join(map(str, sorted(excluded))),
            "train_trades": len(train),
            "test_trades": len(out),
            **{f"test_{k}": v for k,v in m.items()},
        })
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="data/cache/phase9_current_robustness")
    ap.add_argument("--bootstrap", type=int, default=10000)
    args = ap.parse_args()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    all_rows = []
    cpcv_rows = []
    holdout_rows = []

    for ticker in ["NIFTY", "SENSEX"]:
        p = Path(f"data/cache/phase8/NIFTY/{ticker}_current_cycles.csv")
        t = pd.read_csv(p, parse_dates=["entry_date","weekly_expiry","monthly_expiry"])
        t = t.sort_values("entry_date").reset_index(drop=True)
        t.to_csv(out / f"{ticker}_current_trade_log.csv", index=False)

        m = metrics(t["net_pnl"])
        mean, lo, hi = bootstrap_mean(t["net_pnl"].to_numpy(), args.bootstrap, SEED)
        m.update({"ticker":ticker,"bootstrap_mean":mean,"bootstrap_ci_low":lo,"bootstrap_ci_high":hi})
        all_rows.append(m)

        cv = cpcv(t, blocks=6)
        cv.insert(0,"ticker",ticker)
        cv.to_csv(out / f"{ticker}_cpcv.csv", index=False)
        cpcv_rows.append(cv)

        last_block = t.index // max(1, len(t)//6)
        last_id = int(last_block.max())
        hold = t[last_block == last_id]
        hm = metrics(hold["net_pnl"])
        hm.update({"ticker":ticker,"holdout_block":last_id,"holdout_start":str(hold["entry_date"].min().date()),
                   "holdout_end":str(hold["entry_date"].max().date())})
        holdout_rows.append(hm)

    pd.DataFrame(all_rows).to_csv(out / "primary_robustness_summary.csv", index=False)
    pd.concat(cpcv_rows, ignore_index=True).to_csv(out / "cross_index_cpcv.csv", index=False)
    pd.DataFrame(holdout_rows).to_csv(out / "untouched_last_block.csv", index=False)

    for ticker, g in pd.concat(cpcv_rows, ignore_index=True).groupby("ticker"):
        print(ticker)
        print({
            "cpcv_combinations": int(len(g)),
            "positive_test_pct": float((g["test_net_pnl"] > 0).mean()*100),
            "median_test_mean": float(g["test_mean_pnl"].median()),
            "median_test_sharpe": float(g["test_trade_sharpe"].median()),
        })


if __name__ == "__main__":
    main()
