"""Command-line wrapper for running one or both index backtests."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.multileg_options_backtest import (
    BacktestConfig,
    FourLegReverseCalendarBacktester,
    compare_index_results,
    quantitative_cross_index_notes,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Options CSV")
    parser.add_argument("--ticker", choices=["NIFTY", "SENSEX", "BOTH"], default="BOTH")
    parser.add_argument("--spot-input", help="Optional Spot CSV")
    parser.add_argument("--output-dir", default="outputs/backtest")
    parser.add_argument("--lot-size", type=int, default=1)
    args = parser.parse_args()

    options = pd.read_csv(args.input)
    spot = pd.read_csv(args.spot_input) if args.spot_input else None

    cfg = BacktestConfig(lot_size=args.lot_size)
    tickers = ["NIFTY", "SENSEX"] if args.ticker == "BOTH" else [args.ticker]

    results = {}
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for ticker in tickers:
        result = FourLegReverseCalendarBacktester(options, spot_df=spot, config=cfg).run(ticker)
        results[ticker] = result
        result.cycles.to_csv(out / f"{ticker}_cycles.csv", index=False)
        result.legs.to_csv(out / f"{ticker}_legs.csv", index=False)
        result.skipped_cycles.to_csv(out / f"{ticker}_skipped.csv", index=False)
        pd.DataFrame([result.metrics]).to_csv(out / f"{ticker}_metrics.csv", index=False)

    comparison = compare_index_results(results)
    comparison.to_csv(out / "cross_index_comparison.csv", index=False)

    print(comparison.to_string(index=False))
    print()
    print(quantitative_cross_index_notes(results))


if __name__ == "__main__":
    main()
