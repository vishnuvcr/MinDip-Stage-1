from __future__ import annotations

import argparse
import itertools
from pathlib import Path

import numpy as np
import pandas as pd


RNG_SEED = 20260922


def assign_blocks(trades: pd.DataFrame, blocks: pd.DataFrame) -> pd.DataFrame:
    trades = trades.copy()
    trades["entry_date"] = pd.to_datetime(trades["entry_date"]).dt.normalize()
    blocks = blocks.copy()
    blocks["start"] = pd.to_datetime(blocks["start"]).dt.normalize()
    blocks["end"] = pd.to_datetime(blocks["end"]).dt.normalize()

    block_ids = []
    for d in trades["entry_date"]:
        hits = blocks[(blocks["start"] <= d) & (d <= blocks["end"])]
        block_ids.append(int(hits.iloc[0]["block"]) if not hits.empty else np.nan)
    trades["block"] = block_ids
    if trades["block"].isna().any():
        missing = trades.loc[trades["block"].isna(), "entry_date"].dt.strftime("%Y-%m-%d").tolist()
        raise ValueError(f"Trades not assigned to chronology blocks: {missing}")
    trades["block"] = trades["block"].astype(int)
    return trades


def summarize(pnl: pd.Series) -> dict:
    pnl = pd.Series(pnl, dtype=float)
    return {
        "trades": int(len(pnl)),
        "net_pnl": float(pnl.sum()) if len(pnl) else np.nan,
        "mean_pnl": float(pnl.mean()) if len(pnl) else np.nan,
        "win_rate_pct": float((pnl > 0).mean() * 100.0) if len(pnl) else np.nan,
        "std_pnl": float(pnl.std(ddof=1)) if len(pnl) > 1 else np.nan,
        "trade_sharpe": float(pnl.mean() / pnl.std(ddof=1)) if len(pnl) > 1 and pnl.std(ddof=1) > 0 else np.nan,
    }


def cpcv_one_index(ticker: str, trades: pd.DataFrame, blocks: pd.DataFrame, test_block_count: int = 2) -> pd.DataFrame:
    block_ids = sorted(blocks["block"].astype(int).unique())
    rows = []
    for test_blocks in itertools.combinations(block_ids, test_block_count):
        test_blocks = tuple(int(x) for x in test_blocks)
        # Purge immediate neighbors from the training set. No optimization is
        # performed on the training set because the strategy is locked.
        excluded = set(test_blocks)
        for b in test_blocks:
            excluded.add(b - 1)
            excluded.add(b + 1)
        train = trades[~trades["block"].isin(sorted(excluded))]
        test = trades[trades["block"].isin(test_blocks)]
        if test.empty:
            continue
        row = {
            "ticker": ticker,
            "test_block_1": test_blocks[0],
            "test_block_2": test_blocks[1],
            "purged_train_blocks": ",".join(str(x) for x in sorted(excluded)),
        }
        row.update({f"train_{k}": v for k, v in summarize(train["net_pnl"]).items()})
        row.update({f"test_{k}": v for k, v in summarize(test["net_pnl"]).items()})
        rows.append(row)
    return pd.DataFrame(rows)


def oos_distribution(cpcv: pd.DataFrame) -> dict:
    if cpcv.empty:
        return {}
    return {
        "cpcv_combinations": int(len(cpcv)),
        "positive_test_net_pnl_pct": float((cpcv["test_net_pnl"] > 0).mean() * 100.0),
        "median_test_mean_pnl": float(cpcv["test_mean_pnl"].median()),
        "q25_test_mean_pnl": float(cpcv["test_mean_pnl"].quantile(0.25)),
        "q75_test_mean_pnl": float(cpcv["test_mean_pnl"].quantile(0.75)),
        "median_test_sharpe": float(cpcv["test_trade_sharpe"].median()),
    }


def holdout_last_block(trades: pd.DataFrame) -> dict:
    last_block = int(trades["block"].max())
    holdout = trades[trades["block"] == last_block]
    result = summarize(holdout["net_pnl"])
    result.update(
        {
            "holdout_block": last_block,
            "holdout_start": holdout["entry_date"].min(),
            "holdout_end": holdout["entry_date"].max(),
        }
    )
    return result


def single_trial_dsr_assessment(trades: pd.DataFrame) -> dict:
    pnl = trades["net_pnl"].astype(float)
    std = pnl.std(ddof=1)
    skew = float(((pnl - pnl.mean()) ** 3).mean() / (pnl.std(ddof=0) ** 3)) if len(pnl) > 2 and pnl.std(ddof=0) > 0 else np.nan
    kurt = float(((pnl - pnl.mean()) ** 4).mean() / (pnl.std(ddof=0) ** 4) - 3.0) if len(pnl) > 3 and pnl.std(ddof=0) > 0 else np.nan
    sr = float(pnl.mean() / std) if len(pnl) > 1 and std > 0 else np.nan
    return {
        "status": "not_estimable_as_multiple_trial_DSR",
        "reason": "Only one prespecified primary strategy exists; stress assumptions are not independent strategy trials.",
        "trials": 1,
        "observations": int(len(pnl)),
        "observed_trade_sharpe": sr,
        "skewness": skew,
        "excess_kurtosis": kurt,
    }


def pbo_assessment(tickers: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ticker": t,
                "status": "not_estimable",
                "reason": "PBO requires a family of candidate strategies plus in-sample selection; the research plan has one locked primary strategy and no post-hoc strategy selection.",
            }
            for t in tickers
        ]
    )


def permutation_zero_mean_pvalue(values: np.ndarray, n_perm: int = 100_000, seed: int = RNG_SEED) -> float:
    if len(values) == 0:
        return np.nan
    rng = np.random.default_rng(seed)
    observed = abs(values.mean())
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_perm, len(values)))
    null_means = np.abs((signs * values).mean(axis=1))
    return float((null_means >= observed).mean())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/cache/phase5")
    parser.add_argument("--permutations", type=int, default=100000)
    args = parser.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    base = Path("data/cache/phase3")
    block_path = Path("data/cache/phase4/chronology_blocks.csv")
    blocks = pd.read_csv(block_path)

    cpcv_rows = []
    stability_rows = []
    holdout_rows = []
    dsr_rows = []
    perm_rows = []

    for ticker in ["NIFTY", "SENSEX"]:
        trades = pd.read_csv(base / f"{ticker}_trade_log.csv", parse_dates=["entry_date"])
        blocks_t = blocks[blocks["ticker"] == ticker].copy()
        trades = assign_blocks(trades, blocks_t)
        cpcv = cpcv_one_index(ticker, trades, blocks_t, test_block_count=2)
        cpcv.to_csv(out / f"{ticker}_cpcv_combinations.csv", index=False)
        cpcv_rows.append(cpcv)

        stab = {"ticker": ticker, **oos_distribution(cpcv)}
        stability_rows.append(stab)

        hold = {"ticker": ticker, **holdout_last_block(trades)}
        holdout_rows.append(hold)

        dsr = single_trial_dsr_assessment(trades)
        dsr["ticker"] = ticker
        dsr_rows.append(dsr)

        pval = permutation_zero_mean_pvalue(trades["net_pnl"].to_numpy(), n_perm=args.permutations, seed=RNG_SEED + (1 if ticker == "SENSEX" else 0))
        perm_rows.append({"ticker": ticker, "sign_flip_permutation_pvalue": pval})

    pd.concat(cpcv_rows, ignore_index=True).to_csv(out / "cross_index_cpcv_combinations.csv", index=False)
    pd.DataFrame(stability_rows).to_csv(out / "cpcv_stability_summary.csv", index=False)
    pd.DataFrame(holdout_rows).to_csv(out / "untouched_last_block_holdout.csv", index=False)
    pd.DataFrame(dsr_rows).to_csv(out / "dsr_assessment.csv", index=False)
    pbo_assessment(["NIFTY", "SENSEX"]).to_csv(out / "pbo_assessment.csv", index=False)
    pd.DataFrame(perm_rows).to_csv(out / "sign_flip_permutation.csv", index=False)

    print("CPCV stability")
    print(pd.DataFrame(stability_rows).to_string(index=False))
    print("\nUntouched final-block holdout")
    print(pd.DataFrame(holdout_rows).to_string(index=False))
    print("\nDSR assessment")
    print(pd.DataFrame(dsr_rows).to_string(index=False))
    print("\nPBO assessment")
    print(pbo_assessment(["NIFTY", "SENSEX"]).to_string(index=False))
    print("\nSign-flip permutation")
    print(pd.DataFrame(perm_rows).to_string(index=False))


if __name__ == "__main__":
    main()
