import pandas as pd
import numpy as np
import pytest

from src.multileg_options_backtest import (
    BacktestConfig,
    FourLegReverseCalendarBacktester,
    get_index_config,
    monthly_expiry_for_or_after,
    next_weekly_expiry,
    nearest_strike,
    roll_previous_trading_day,
)

def trading_dates(start, end, holidays=()):
    dates = pd.date_range(start, end, freq="B")
    holiday_index = pd.DatetimeIndex(pd.to_datetime(list(holidays))).normalize()
    return dates[~dates.isin(holiday_index)]

def test_index_specific_configuration():
    nifty = get_index_config("NIFTY 50")
    sensex = get_index_config("BSE SENSEX")
    assert nifty.strike_interval == 50
    assert nifty.itm_offset == 100
    assert nifty.weekly_expiry_weekday == 1
    assert nifty.cycle_entry_weekday == 2
    assert sensex.strike_interval == 100
    assert sensex.itm_offset == 200
    assert sensex.weekly_expiry_weekday == 3
    assert sensex.cycle_entry_weekday == 4

def test_strike_rounding():
    assert nearest_strike(25024, 50) == 25000
    assert nearest_strike(25025, 50) == 25050
    assert nearest_strike(81449, 100) == 81400
    assert nearest_strike(81450, 100) == 81500

def test_nifty_expiry_math():
    td = trading_dates("2026-09-01", "2026-10-31")
    after = pd.Timestamp("2026-09-23")
    assert next_weekly_expiry(after, get_index_config("NIFTY"), td) == pd.Timestamp("2026-09-29")
    assert monthly_expiry_for_or_after(after, get_index_config("NIFTY"), td) == pd.Timestamp("2026-09-29")

def test_sensex_expiry_math():
    td = trading_dates("2026-09-01", "2026-11-30")
    after = pd.Timestamp("2026-09-25")
    assert next_weekly_expiry(after, get_index_config("SENSEX"), td) == pd.Timestamp("2026-10-01")
    assert monthly_expiry_for_or_after(after, get_index_config("SENSEX"), td) == pd.Timestamp("2026-10-29")

def test_holiday_roll_to_previous_trading_day():
    holiday = pd.Timestamp("2026-09-29")
    td = trading_dates("2026-09-21", "2026-10-06", holidays=[holiday])
    assert roll_previous_trading_day(holiday, td) == pd.Timestamp("2026-09-28")

def make_nifty_fixture():
    rows = [{
        "Date": "2026-09-23", "Time": "09:30:00", "Ticker": "NIFTY",
        "Expiry_Date": np.nan, "Strike": np.nan, "Option_Type": "SPOT", "Close": 25000.0,
    }]
    specs = [
        ("2026-09-29", 25000.0, "PE", 100.0, 120.0),
        ("2026-09-29", 25100.0, "PE", 50.0, 20.0),
        ("2026-09-29", 25000.0, "CE", 100.0, 80.0),
        ("2026-09-29", 24900.0, "CE", 200.0, 150.0),
    ]
    for expiry, strike, opt_type, entry_px, exit_px in specs:
        rows.append({
            "Date": "2026-09-23", "Time": "09:30:00", "Ticker": "NIFTY",
            "Expiry_Date": expiry, "Strike": strike, "Option_Type": opt_type, "Close": entry_px,
        })
        rows.append({
            "Date": "2026-09-29", "Time": "15:15:00", "Ticker": "NIFTY",
            "Expiry_Date": expiry, "Strike": strike, "Option_Type": opt_type, "Close": exit_px,
        })
    return pd.DataFrame(rows)

def test_full_cycle_and_cost_model():
    cfg = BacktestConfig(lot_size=1, slippage_rate=0.005, fixed_cost_per_leg=40)
    result = FourLegReverseCalendarBacktester(make_nifty_fixture(), config=cfg).run("NIFTY")
    assert len(result.cycles) == 1
    cycle = result.cycles.iloc[0]
    assert cycle["entry_date"] == pd.Timestamp("2026-09-23")
    assert cycle["weekly_expiry"] == pd.Timestamp("2026-09-29")
    assert cycle["monthly_expiry"] == pd.Timestamp("2026-09-29")
    assert cycle["atm_strike"] == 25000
    assert cycle["fixed_cost"] == 160
    assert cycle["gross_pnl"] == pytest.approx(75.90)
    assert cycle["net_pnl"] == pytest.approx(-84.10)
    assert result.metrics["trades"] == 1
    assert result.metrics["total_return_roc_pct"] == pytest.approx(-84.10 / 150000 * 100)
    assert result.metrics["win_rate_pct"] == 0
    assert result.metrics["expectancy_per_trade"] == pytest.approx(-84.10)

def test_missing_required_contract_causes_cycle_skip():
    df = make_nifty_fixture()
    df = df[~((df["Strike"] == 24900) & (df["Option_Type"] == "CE"))].copy()
    result = FourLegReverseCalendarBacktester(df, config=BacktestConfig()).run("NIFTY")
    assert result.cycles.empty
    assert len(result.skipped_cycles) == 1
    assert "24900" in result.skipped_cycles.iloc[0]["reason"]
