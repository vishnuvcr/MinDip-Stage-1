"""Multi-index, multi-expiry four-leg options backtester.

Reference implementation for the MinDip Stage 1 research program.

Input option dataframe columns:
    Date, Time, Ticker, Expiry_Date, Strike, Option_Type, Close

Spot can be embedded in the same dataframe by using:
    Option_Type in {"SPOT", "INDEX"}, Expiry_Date=NaT, Strike=NaN
or supplied as a separate dataframe with columns Date, Time, Ticker, Close.

The primary research rule is intentionally locked to the user specification:
- NIFTY: strike interval 50, two-strike ITM offset 100, weekly Tuesday,
  monthly last Tuesday, cycle entry Wednesday.
- SENSEX: strike interval 100, two-strike ITM offset 200, weekly Thursday,
  monthly last Thursday, cycle entry Friday.
- Entry 09:30, exit 15:15.
- 0.5% adverse slippage on every leg at entry and exit.
- ₹40 per leg, ₹160 total fixed cycle cost.
- ₹1,50,000 static capital/margin denominator.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, asdict
from datetime import time
from pathlib import Path
from typing import Callable, Iterable, Optional

import numpy as np
import pandas as pd


REQUIRED_OPTION_COLUMNS = [
    "Date",
    "Time",
    "Ticker",
    "Expiry_Date",
    "Strike",
    "Option_Type",
    "Close",
]

SPOT_OPTION_TYPES = {"SPOT", "INDEX"}

INDEX_CONFIGS = {
    "NIFTY": {
        "name": "NIFTY 50",
        "aliases": {"NIFTY", "NIFTY 50", "NIFTY50"},
        "strike_interval": 50.0,
        "itm_offset": 100.0,
        "weekly_expiry_weekday": 1,  # Tuesday
        "monthly_expiry_weekday": 1,
        "cycle_entry_weekday": 2,  # Wednesday
    },
    "SENSEX": {
        "name": "BSE SENSEX",
        "aliases": {"SENSEX", "BSE SENSEX", "S&P BSE SENSEX"},
        "strike_interval": 100.0,
        "itm_offset": 200.0,
        "weekly_expiry_weekday": 3,  # Thursday
        "monthly_expiry_weekday": 3,
        "cycle_entry_weekday": 4,  # Friday
    },
}


@dataclass(frozen=True)
class IndexConfig:
    key: str
    name: str
    strike_interval: float
    itm_offset: float
    weekly_expiry_weekday: int
    monthly_expiry_weekday: int
    cycle_entry_weekday: int


@dataclass(frozen=True)
class BacktestConfig:
    slippage_rate: float = 0.005
    fixed_cost_per_leg: float = 40.0
    initial_capital: float = 150_000.0
    lot_size: int = 1
    entry_time: time = time(9, 30)
    exit_time: time = time(15, 15)
    strict_strikes: bool = True
    require_all_legs: bool = True


@dataclass(frozen=True)
class LegSpec:
    name: str
    side: str
    expiry_key: str
    option_type: str
    strike_role: str


@dataclass
class BacktestResult:
    cycles: pd.DataFrame
    legs: pd.DataFrame
    skipped_cycles: pd.DataFrame
    metrics: dict


def normalize_ticker(value: str) -> str:
    cleaned = str(value).strip().upper()
    if cleaned in INDEX_CONFIGS:
        return cleaned
    for key, cfg in INDEX_CONFIGS.items():
        if cleaned in cfg["aliases"]:
            return key
    return cleaned


def get_index_config(ticker: str) -> IndexConfig:
    key = normalize_ticker(ticker)
    if key not in INDEX_CONFIGS:
        raise ValueError(
            f"Unsupported ticker {ticker!r}. Expected NIFTY/NIFTY 50 or SENSEX/BSE SENSEX."
        )
    cfg = INDEX_CONFIGS[key]
    return IndexConfig(key=key, **{k: v for k, v in cfg.items() if k != "aliases"})


def validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_OPTION_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _combine_timestamp(df: pd.DataFrame) -> pd.Series:
    dates = pd.to_datetime(df["Date"], errors="coerce").dt.normalize()
    time_text = df["Time"].astype(str).str.strip()
    timestamp = pd.to_datetime(
        dates.dt.strftime("%Y-%m-%d") + " " + time_text,
        errors="coerce",
    )
    return timestamp


def prepare_options_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    validate_columns(df)
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce").dt.normalize()
    out["Expiry_Date"] = pd.to_datetime(out["Expiry_Date"], errors="coerce").dt.normalize()
    out["Timestamp"] = _combine_timestamp(df)
    out["Ticker_Normalized"] = out["Ticker"].map(normalize_ticker)
    out["Option_Type_Normalized"] = out["Option_Type"].astype(str).str.strip().str.upper()
    out["Strike"] = pd.to_numeric(out["Strike"], errors="coerce")
    out["Close"] = pd.to_numeric(out["Close"], errors="coerce")
    bad = out["Timestamp"].isna()
    if bad.any():
        raise ValueError(f"Found {int(bad.sum())} rows with invalid Date/Time.")
    if out["Close"].isna().any():
        raise ValueError("Close contains NaN/non-numeric values; clean the dataset first.")
    return out.sort_values(["Ticker_Normalized", "Timestamp"]).reset_index(drop=True)


def prepare_spot_dataframe(spot_df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    if spot_df is None:
        return None
    required = {"Date", "Time", "Ticker", "Close"}
    missing = sorted(required - set(spot_df.columns))
    if missing:
        raise ValueError(f"Spot dataframe is missing columns: {missing}")
    out = spot_df.copy()
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce").dt.normalize()
    out["Timestamp"] = _combine_timestamp(out)
    out["Ticker_Normalized"] = out["Ticker"].map(normalize_ticker)
    out["Close"] = pd.to_numeric(out["Close"], errors="coerce")
    if out["Timestamp"].isna().any() or out["Close"].isna().any():
        raise ValueError("Spot dataframe contains invalid Date/Time/Close values.")
    return out.sort_values(["Ticker_Normalized", "Timestamp"]).reset_index(drop=True)


def nearest_strike(spot: float, interval: float) -> float:
    """Round to nearest strike, using half-up rounding for positive index levels."""
    return float(math.floor((float(spot) / interval) + 0.5) * interval)


def _last_weekday_of_month(year: int, month: int, weekday: int) -> pd.Timestamp:
    first = pd.Timestamp(year=year, month=month, day=1)
    next_month = first + pd.offsets.MonthBegin(1)
    last_day = next_month - pd.Timedelta(days=1)
    delta = (last_day.weekday() - weekday) % 7
    return (last_day - pd.Timedelta(days=delta)).normalize()


def roll_previous_trading_day(
    scheduled: pd.Timestamp,
    trading_dates: Iterable[pd.Timestamp],
) -> Optional[pd.Timestamp]:
    dates = pd.DatetimeIndex(pd.to_datetime(list(trading_dates))).normalize()
    eligible = dates[dates <= pd.Timestamp(scheduled).normalize()]
    if len(eligible) == 0:
        return None
    return pd.Timestamp(eligible.max()).normalize()


def next_weekly_expiry(
    after_date: pd.Timestamp,
    config: IndexConfig,
    trading_dates: Iterable[pd.Timestamp],
) -> Optional[pd.Timestamp]:
    after_date = pd.Timestamp(after_date).normalize()
    base = after_date + pd.Timedelta(days=1)
    delta = (config.weekly_expiry_weekday - base.weekday()) % 7
    scheduled = (base + pd.Timedelta(days=delta)).normalize()

    for _ in range(12):
        actual = roll_previous_trading_day(scheduled, trading_dates)
        if actual is not None and actual > after_date:
            return actual
        scheduled = scheduled + pd.Timedelta(days=7)
    return None


def monthly_expiry_for_or_after(
    after_date: pd.Timestamp,
    config: IndexConfig,
    trading_dates: Iterable[pd.Timestamp],
) -> Optional[pd.Timestamp]:
    after_date = pd.Timestamp(after_date).normalize()
    cursor = after_date

    for _ in range(24):
        candidate = _last_weekday_of_month(
            cursor.year, cursor.month, config.monthly_expiry_weekday
        )
        actual = roll_previous_trading_day(candidate, trading_dates)
        if actual is not None and actual > after_date:
            return actual
        cursor = (cursor + pd.offsets.MonthBegin(1)).normalize()
    return None


def scheduled_cycle_entry_dates(
    min_date: pd.Timestamp,
    max_date: pd.Timestamp,
    config: IndexConfig,
    trading_dates: Iterable[pd.Timestamp],
) -> list[pd.Timestamp]:
    """Generate actual entry dates after applying previous-trading-day holiday roll."""
    calendar_days = pd.date_range(
        pd.Timestamp(min_date).normalize(),
        pd.Timestamp(max_date).normalize(),
        freq="D",
    )
    actual = []
    for day in calendar_days:
        if day.weekday() == config.cycle_entry_weekday:
            shifted = roll_previous_trading_day(day, trading_dates)
            if shifted is not None and min_date <= shifted <= max_date:
                actual.append(shifted)
    return sorted(set(actual))


def entry_price_for_side(close: float, side: str, slippage_rate: float) -> float:
    if side.upper() == "BUY":
        return float(close) * (1.0 + slippage_rate)
    return float(close) * (1.0 - slippage_rate)


def exit_price_for_side(close: float, side: str, slippage_rate: float) -> float:
    if side.upper() == "BUY":
        return float(close) * (1.0 - slippage_rate)
    return float(close) * (1.0 + slippage_rate)


def pnl_per_unit(entry_exec: float, exit_exec: float, side: str) -> float:
    if side.upper() == "BUY":
        return float(exit_exec - entry_exec)
    return float(entry_exec - exit_exec)


def max_drawdown(equity: pd.Series) -> tuple[float, float]:
    if equity.empty:
        return 0.0, 0.0
    peak = equity.cummax()
    drawdown_abs = equity - peak
    drawdown_pct = equity / peak - 1.0
    return float(drawdown_abs.min()), float(drawdown_pct.min() * 100.0)


def summarize_cycles(
    cycles: pd.DataFrame,
    initial_capital: float,
) -> dict:
    if cycles.empty:
        return {
            "trades": 0,
            "total_net_pnl": 0.0,
            "total_return_roc_pct": 0.0,
            "win_rate_pct": 0.0,
            "max_drawdown_abs": 0.0,
            "max_drawdown_pct": 0.0,
            "average_profit": 0.0,
            "average_loss": 0.0,
            "average_profit_to_abs_loss": np.nan,
            "expectancy_per_trade": 0.0,
            "profit_factor": np.nan,
        }

    ordered = cycles.sort_values("entry_date").reset_index(drop=True)
    pnl = ordered["net_pnl"].astype(float)
    equity = float(initial_capital) + pnl.cumsum()
    dd_abs, dd_pct = max_drawdown(equity)

    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    avg_profit = float(wins.mean()) if not wins.empty else 0.0
    avg_loss = float(losses.mean()) if not losses.empty else 0.0
    loss_abs = abs(avg_loss)

    gross_profit = float(wins.sum()) if not wins.empty else 0.0
    gross_loss_abs = float(abs(losses.sum())) if not losses.empty else 0.0
    profit_factor = (
        gross_profit / gross_loss_abs if gross_loss_abs > 0 else np.nan
    )

    return {
        "trades": int(len(pnl)),
        "total_net_pnl": float(pnl.sum()),
        "total_return_roc_pct": float(pnl.sum() / initial_capital * 100.0),
        "win_rate_pct": float((pnl > 0).mean() * 100.0),
        "max_drawdown_abs": dd_abs,
        "max_drawdown_pct": dd_pct,
        "average_profit": avg_profit,
        "average_loss": avg_loss,
        "average_profit_to_abs_loss": (
            avg_profit / loss_abs if loss_abs > 0 else np.nan
        ),
        "expectancy_per_trade": float(pnl.mean()),
        "profit_factor": profit_factor,
    }


class FourLegReverseCalendarBacktester:
    def __init__(
        self,
        options_df: pd.DataFrame,
        spot_df: Optional[pd.DataFrame] = None,
        holidays: Optional[Iterable[pd.Timestamp]] = None,
        config: BacktestConfig = BacktestConfig(),
        spot_price_provider: Optional[Callable[[str, pd.Timestamp, pd.Timestamp], float]] = None,
    ) -> None:
        self.options = prepare_options_dataframe(options_df)
        self.spot = prepare_spot_dataframe(spot_df)
        self.holidays = set(
            pd.to_datetime(list(holidays), errors="coerce").normalize()
        ) if holidays is not None else set()
        self.config = config
        self.spot_price_provider = spot_price_provider

    def _trading_dates(self, ticker_key: str) -> pd.DatetimeIndex:
        dates = self.options.loc[
            self.options["Ticker_Normalized"] == ticker_key, "Date"
        ].dropna().drop_duplicates()
        dates = pd.DatetimeIndex(dates).normalize()
        if self.holidays:
            dates = dates[~dates.isin(pd.DatetimeIndex(self.holidays))]
        return dates.sort_values()

    def _spot_at_entry(self, ticker_key: str, entry_date: pd.Timestamp) -> float:
        start = pd.Timestamp.combine(entry_date.date(), self.config.entry_time)
        end = start + pd.Timedelta(days=1)

        if self.spot is not None:
            rows = self.spot[
                (self.spot["Ticker_Normalized"] == ticker_key)
                & (self.spot["Timestamp"] >= start)
                & (self.spot["Timestamp"] < end)
            ]
            if not rows.empty:
                return float(rows.sort_values("Timestamp").iloc[0]["Close"])

        embedded = self.options[
            (self.options["Ticker_Normalized"] == ticker_key)
            & (self.options["Option_Type_Normalized"].isin(SPOT_OPTION_TYPES))
            & (self.options["Timestamp"] >= start)
            & (self.options["Timestamp"] < end)
        ]
        if not embedded.empty:
            return float(embedded.sort_values("Timestamp").iloc[0]["Close"])

        if self.spot_price_provider is not None:
            value = self.spot_price_provider(ticker_key, entry_date, start)
            if value is None or not np.isfinite(value):
                raise ValueError(f"Spot provider returned no valid price for {ticker_key} on {entry_date.date()}.")
            return float(value)

        raise ValueError(
            f"No spot observation at/after {self.config.entry_time.strftime('%H:%M')} "
            f"on {entry_date.date()} for {ticker_key}. Supply spot_df, embedded SPOT rows, "
            "or a spot_price_provider."
        )

    def _available_strikes(
        self,
        ticker_key: str,
        expiry: pd.Timestamp,
        option_type: str,
    ) -> np.ndarray:
        rows = self.options[
            (self.options["Ticker_Normalized"] == ticker_key)
            & (self.options["Expiry_Date"] == pd.Timestamp(expiry).normalize())
            & (self.options["Option_Type_Normalized"] == option_type)
            & self.options["Strike"].notna()
        ]
        return np.sort(rows["Strike"].unique())

    def _resolve_strike(
        self,
        ticker_key: str,
        expiry: pd.Timestamp,
        option_type: str,
        requested: float,
    ) -> tuple[float, bool]:
        strikes = self._available_strikes(ticker_key, expiry, option_type)
        if len(strikes) == 0:
            raise ValueError(
                f"No strikes available for {ticker_key} {option_type} expiry {pd.Timestamp(expiry).date()}."
            )

        exact = strikes[np.isclose(strikes, requested, atol=1e-9)]
        if len(exact) > 0:
            return float(exact[0]), True

        if self.config.strict_strikes:
            raise ValueError(
                f"Required strike {requested:g} unavailable for {ticker_key} "
                f"{option_type} expiry {pd.Timestamp(expiry).date()}."
            )

        nearest = strikes[int(np.argmin(np.abs(strikes - requested)))]
        return float(nearest), False

    def _quote(
        self,
        ticker_key: str,
        entry_date: pd.Timestamp,
        expiry: pd.Timestamp,
        strike: float,
        option_type: str,
        when: pd.Timestamp,
        is_entry: bool,
    ) -> tuple[float, pd.Timestamp]:
        rows = self.options[
            (self.options["Ticker_Normalized"] == ticker_key)
            & (self.options["Expiry_Date"] == pd.Timestamp(expiry).normalize())
            & np.isclose(self.options["Strike"], strike, atol=1e-9)
            & (self.options["Option_Type_Normalized"] == option_type)
        ].copy()

        if rows.empty:
            raise ValueError(
                f"No quote rows for {ticker_key} {expiry.date()} {strike:g}{option_type}."
            )

        if is_entry:
            rows = rows[
                (rows["Date"] == pd.Timestamp(entry_date).normalize())
                & (rows["Timestamp"] >= when)
            ].sort_values("Timestamp")
            if rows.empty:
                raise ValueError(
                    f"No entry quote at/after {when} for {ticker_key} {strike:g}{option_type}."
                )
            row = rows.iloc[0]
        else:
            rows = rows[
                (rows["Date"] == pd.Timestamp(entry_date).normalize())
                & (rows["Timestamp"] <= when)
            ].sort_values("Timestamp")
            if rows.empty:
                raise ValueError(
                    f"No exit quote at/before {when} for {ticker_key} {strike:g}{option_type}."
                )
            row = rows.iloc[-1]

        return float(row["Close"]), pd.Timestamp(row["Timestamp"])

    def _build_leg_specs(self) -> list[LegSpec]:
        return [
            LegSpec("L1_MONTHLY_ATM_PE", "BUY", "monthly_expiry", "PE", "ATM"),
            LegSpec("L2_WEEKLY_ITM_PE", "SELL", "weekly_expiry", "PE", "ITM_PUT"),
            LegSpec("L3_WEEKLY_ATM_CE", "BUY", "weekly_expiry", "CE", "ATM"),
            LegSpec("L4_MONTHLY_ITM_CE", "SELL", "monthly_expiry", "CE", "ITM_CALL"),
        ]

    def _strike_for_role(
        self,
        spot: float,
        config: IndexConfig,
        role: str,
    ) -> float:
        atm = nearest_strike(spot, config.strike_interval)
        if role == "ATM":
            return atm
        if role == "ITM_PUT":
            return atm + config.itm_offset
        if role == "ITM_CALL":
            return atm - config.itm_offset
        raise KeyError(role)

    def _run_cycle(
        self,
        ticker_key: str,
        scheduled_entry_date: pd.Timestamp,
        entry_date: pd.Timestamp,
        weekly_expiry: pd.Timestamp,
        monthly_expiry: pd.Timestamp,
    ) -> tuple[dict, list[dict]]:
        config = get_index_config(ticker_key)
        spot = self._spot_at_entry(ticker_key, entry_date)
        atm = nearest_strike(spot, config.strike_interval)

        entry_ts = pd.Timestamp.combine(entry_date.date(), self.config.entry_time)
        exit_ts = pd.Timestamp.combine(weekly_expiry.date(), self.config.exit_time)

        leg_rows = []
        cycle_gross = 0.0

        for leg in self._build_leg_specs():
            expiry = weekly_expiry if leg.expiry_key == "weekly_expiry" else monthly_expiry
            requested_strike = self._strike_for_role(spot, config, leg.strike_role)
            selected_strike, exact = self._resolve_strike(
                ticker_key, expiry, leg.option_type, requested_strike
            )

            entry_close, actual_entry_ts = self._quote(
                ticker_key,
                entry_date,
                expiry,
                selected_strike,
                leg.option_type,
                entry_ts,
                is_entry=True,
            )
            exit_close, actual_exit_ts = self._quote(
                ticker_key,
                weekly_expiry,
                expiry,
                selected_strike,
                leg.option_type,
                exit_ts,
                is_entry=False,
            )

            entry_exec = entry_price_for_side(
                entry_close, leg.side, self.config.slippage_rate
            )
            exit_exec = exit_price_for_side(
                exit_close, leg.side, self.config.slippage_rate
            )
            leg_pnl = pnl_per_unit(entry_exec, exit_exec, leg.side) * self.config.lot_size
            cycle_gross += leg_pnl

            leg_rows.append(
                {
                    "ticker": ticker_key,
                    "scheduled_entry_date": scheduled_entry_date,
                    "entry_date": entry_date,
                    "weekly_expiry": weekly_expiry,
                    "monthly_expiry": monthly_expiry,
                    "leg": leg.name,
                    "side": leg.side,
                    "option_type": leg.option_type,
                    "expiry": expiry,
                    "requested_strike": requested_strike,
                    "selected_strike": selected_strike,
                    "strike_exact": exact,
                    "entry_quote_time": actual_entry_ts,
                    "exit_quote_time": actual_exit_ts,
                    "entry_close": entry_close,
                    "exit_close": exit_close,
                    "entry_exec": entry_exec,
                    "exit_exec": exit_exec,
                    "lot_size": self.config.lot_size,
                    "leg_pnl": leg_pnl,
                }
            )

        fixed_cycle_cost = self.config.fixed_cost_per_leg * 4.0
        net_pnl = cycle_gross - fixed_cycle_cost

        cycle = {
            "ticker": ticker_key,
            "scheduled_entry_date": scheduled_entry_date,
            "entry_date": entry_date,
            "weekly_expiry": weekly_expiry,
            "monthly_expiry": monthly_expiry,
            "spot": spot,
            "atm_strike": atm,
            "gross_pnl": cycle_gross,
            "fixed_cost": fixed_cycle_cost,
            "net_pnl": net_pnl,
        }
        return cycle, leg_rows

    def run(self, ticker: str) -> BacktestResult:
        ticker_key = normalize_ticker(ticker)
        config = get_index_config(ticker_key)
        trading_dates = self._trading_dates(ticker_key)
        if len(trading_dates) == 0:
            raise ValueError(f"No option observations found for {ticker_key}.")

        entries = scheduled_cycle_entry_dates(
            trading_dates.min(), trading_dates.max(), config, trading_dates
        )

        cycles = []
        legs = []
        skipped = []

        for scheduled_entry in entries:
            entry_date = roll_previous_trading_day(scheduled_entry, trading_dates)
            if entry_date is None:
                skipped.append({"ticker": ticker_key, "scheduled_entry_date": scheduled_entry, "reason": "No prior trading date"})
                continue

            weekly_expiry = next_weekly_expiry(entry_date, config, trading_dates)
            monthly_expiry = monthly_expiry_for_or_after(entry_date, config, trading_dates)

            if weekly_expiry is None or monthly_expiry is None:
                skipped.append({"ticker": ticker_key, "scheduled_entry_date": scheduled_entry, "reason": "Could not resolve expiry"})
                continue

            try:
                cycle, leg_rows = self._run_cycle(
                    ticker_key,
                    scheduled_entry,
                    entry_date,
                    weekly_expiry,
                    monthly_expiry,
                )
                cycles.append(cycle)
                legs.extend(leg_rows)
            except Exception as exc:
                skipped.append(
                    {
                        "ticker": ticker_key,
                        "scheduled_entry_date": scheduled_entry,
                        "entry_date": entry_date,
                        "weekly_expiry": weekly_expiry,
                        "monthly_expiry": monthly_expiry,
                        "reason": str(exc),
                    }
                )
                if self.config.require_all_legs:
                    continue

        cycles_df = pd.DataFrame(cycles)
        legs_df = pd.DataFrame(legs)
        skipped_df = pd.DataFrame(skipped)

        metrics = summarize_cycles(cycles_df, self.config.initial_capital)
        metrics.update(
            {
                "ticker": ticker_key,
                "index_name": config.name,
                "initial_capital": self.config.initial_capital,
                "fixed_cost_per_cycle": self.config.fixed_cost_per_leg * 4.0,
                "slippage_rate_pct": self.config.slippage_rate * 100.0,
            }
        )

        return BacktestResult(
            cycles=cycles_df,
            legs=legs_df,
            skipped_cycles=skipped_df,
            metrics=metrics,
        )


def compare_index_results(results: dict[str, BacktestResult]) -> pd.DataFrame:
    rows = [r.metrics for r in results.values()]
    if not rows:
        return pd.DataFrame()
    cols = [
        "ticker",
        "index_name",
        "trades",
        "total_net_pnl",
        "total_return_roc_pct",
        "win_rate_pct",
        "max_drawdown_abs",
        "max_drawdown_pct",
        "average_profit",
        "average_loss",
        "average_profit_to_abs_loss",
        "expectancy_per_trade",
        "profit_factor",
        "fixed_cost_per_cycle",
        "slippage_rate_pct",
    ]
    return pd.DataFrame(rows)[cols].sort_values("ticker").reset_index(drop=True)


def quantitative_cross_index_notes(
    results: dict[str, BacktestResult],
) -> str:
    """Produce a neutral, data-dependent comparison narrative.

    The function deliberately does not rank the indices. It reports what the
    supplied backtest actually measured and flags liquidity hypotheses that
    require bid/ask data to validate.
    """
    fixed_cost_drag = 40.0 * 4.0 / 150_000.0 * 100.0
    lines = [
        f"Fixed ₹160 cycle cost equals {fixed_cost_drag:.4f}% of the ₹1,50,000 capital denominator per cycle.",
        "The 0.5% premium slippage assumption is applied independently to entry and exit for all four legs; the resulting drag depends on each leg's premium level and therefore cannot be reduced to one constant ROC percentage.",
    ]
    for key in ["NIFTY", "SENSEX"]:
        if key in results:
            m = results[key].metrics
            lines.append(
                f"{key}: trades={m['trades']}, ROC={m['total_return_roc_pct']:.2f}%, "
                f"win rate={m['win_rate_pct']:.2f}%, max DD={m['max_drawdown_pct']:.2f}%, "
                f"expectancy={m['expectancy_per_trade']:.2f}."
            )
    lines.append(
        "Liquidity-vacuum and spread effects are not directly observable from Close-only data. "
        "To test the SENSEX deep-ITM monthly-leg hypothesis, add bid/ask or top-of-book observations "
        "and rerun the same locked strategy under spread-aware execution. Likewise, any claim that "
        "NIFTY's volatility surface is smoother must be tested from the dataset rather than assumed."
    )
    return " ".join(lines)


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Backtest the MinDip four-leg reverse-calendar strategy.")
    parser.add_argument("--input", required=True, help="CSV containing option observations.")
    parser.add_argument("--ticker", required=True, choices=["NIFTY", "SENSEX"])
    parser.add_argument("--spot-input", help="Optional CSV with Date, Time, Ticker, Close.")
    parser.add_argument("--output-dir", default="outputs/backtest")
    parser.add_argument("--lot-size", type=int, default=1)
    parser.add_argument("--slippage", type=float, default=0.005)
    parser.add_argument("--fixed-cost-per-leg", type=float, default=40.0)
    parser.add_argument("--initial-capital", type=float, default=150_000.0)
    parser.add_argument("--non-strict-strikes", action="store_true")
    args = parser.parse_args()

    options = pd.read_csv(args.input)
    spot = pd.read_csv(args.spot_input) if args.spot_input else None

    cfg = BacktestConfig(
        slippage_rate=args.slippage,
        fixed_cost_per_leg=args.fixed_cost_per_leg,
        initial_capital=args.initial_capital,
        lot_size=args.lot_size,
        strict_strikes=not args.non_strict_strikes,
    )

    result = FourLegReverseCalendarBacktester(options, spot_df=spot, config=cfg).run(args.ticker)

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    result.cycles.to_csv(output / f"{normalize_ticker(args.ticker)}_cycles.csv", index=False)
    result.legs.to_csv(output / f"{normalize_ticker(args.ticker)}_legs.csv", index=False)
    result.skipped_cycles.to_csv(output / f"{normalize_ticker(args.ticker)}_skipped.csv", index=False)
    pd.DataFrame([result.metrics]).to_csv(
        output / f"{normalize_ticker(args.ticker)}_metrics.csv", index=False
    )

    print(pd.Series(result.metrics).to_string())
    print()
    print(quantitative_cross_index_notes({normalize_ticker(args.ticker): result}))


if __name__ == "__main__":
    _cli()
