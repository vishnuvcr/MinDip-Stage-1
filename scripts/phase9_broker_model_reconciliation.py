from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm


LOT_SIZE = 65
SPOT = 23329.0
WEEKLY_FUT = 23436.90
MONTHLY_FUT = 23510.00
WEEKLY_EXPIRY = pd.Timestamp("2026-10-06")
MONTHLY_EXPIRY = pd.Timestamp("2026-10-27")
VALUATION_DATE = pd.Timestamp("2026-09-23")

SCREENSHOT_BREAKEVEN_LOW = 23448.0
SCREENSHOT_BREAKEVEN_HIGH = 23487.0
SCREENSHOT_SD_1 = 303.0
SCREENSHOT_MAX_PROFIT = 5961.0
SCREENSHOT_MAX_LOSS = -138.0
SCREENSHOT_POP = 0.96
SCREENSHOT_INTRINSIC = 12100.0
SCREENSHOT_TIME_VALUE = -351.0
SCREENSHOT_DELTA = -0.041
SCREENSHOT_THETA = 0.17
SCREENSHOT_DECAY = 2.3
SCREENSHOT_GAMMA = 0.0
SCREENSHOT_VEGA = -0.67

# Editor screenshot premiums.
PREMIUMS = {
    "L1_SELL_MONTHLY_ATM_PE": 226.60,
    "L2_BUY_MONTHLY_ATM_MINUS_2_CE": 451.00,
    "L3_BUY_WEEKLY_ATM_PLUS_2_PE": 179.00,
    "L4_SELL_WEEKLY_ATM_CE": 222.65,
}

CONTRACTS = [
    {
        "leg": "L1_SELL_MONTHLY_ATM_PE",
        "side": -1,
        "option": "put",
        "strike": 23350.0,
        "future": MONTHLY_FUT,
        "expiry": MONTHLY_EXPIRY,
    },
    {
        "leg": "L2_BUY_MONTHLY_ATM_MINUS_2_CE",
        "side": +1,
        "option": "call",
        "strike": 23250.0,
        "future": MONTHLY_FUT,
        "expiry": MONTHLY_EXPIRY,
    },
    {
        "leg": "L3_BUY_WEEKLY_ATM_PLUS_2_PE",
        "side": +1,
        "option": "put",
        "strike": 23450.0,
        "future": WEEKLY_FUT,
        "expiry": WEEKLY_EXPIRY,
    },
    {
        "leg": "L4_SELL_WEEKLY_ATM_CE",
        "side": -1,
        "option": "call",
        "strike": 23350.0,
        "future": WEEKLY_FUT,
        "expiry": WEEKLY_EXPIRY,
    },
]


@dataclass
class Calibration:
    leg: str
    future: float
    strike: float
    premium: float
    days_to_expiry: int
    implied_vol: float
    model_price: float
    abs_error: float


def year_fraction(expiry: pd.Timestamp, valuation: pd.Timestamp) -> float:
    days = max((pd.Timestamp(expiry).normalize() - pd.Timestamp(valuation).normalize()).days, 1)
    return days / 365.0


def black76_price(future: float, strike: float, sigma: float, t: float, option: str) -> float:
    if t <= 0:
        return max(future - strike, 0.0) if option == "call" else max(strike - future, 0.0)
    if sigma <= 0:
        return max(future - strike, 0.0) if option == "call" else max(strike - future, 0.0)

    root_t = math.sqrt(t)
    d1 = (math.log(future / strike) + 0.5 * sigma * sigma * t) / (sigma * root_t)
    d2 = d1 - sigma * root_t
    if option == "call":
        return future * norm.cdf(d1) - strike * norm.cdf(d2)
    return strike * norm.cdf(-d2) - future * norm.cdf(-d1)


def implied_vol(future: float, strike: float, premium: float, t: float, option: str) -> float:
    intrinsic = max(future - strike, 0.0) if option == "call" else max(strike - future, 0.0)
    if premium < intrinsic - 1e-8:
        raise ValueError(f"Premium below intrinsic for {option}: {premium} < {intrinsic}")

    fn = lambda sigma: black76_price(future, strike, sigma, t, option) - premium
    return brentq(fn, 1e-8, 5.0)


def black76_greeks(future: float, strike: float, sigma: float, t: float, option: str) -> dict:
    root_t = math.sqrt(t)
    d1 = (math.log(future / strike) + 0.5 * sigma * sigma * t) / (sigma * root_t)
    pdf = norm.pdf(d1)
    if option == "call":
        delta = norm.cdf(d1)
    else:
        delta = norm.cdf(d1) - 1.0
    gamma = pdf / (future * sigma * root_t)
    vega_per_1pct = (future * pdf * root_t) / 100.0
    # Black-76 theta with fixed forward and zero discount rate, expressed per day.
    theta_per_day = (-future * pdf * sigma / (2.0 * root_t)) / 365.0
    return {
        "delta": float(delta),
        "gamma": float(gamma),
        "vega_per_1pct": float(vega_per_1pct),
        "theta_per_day": float(theta_per_day),
    }


def intrinsic_value_at_futures() -> float:
    total = 0.0
    for c in CONTRACTS:
        f = c["future"]
        k = c["strike"]
        if c["option"] == "call":
            intrinsic = max(f - k, 0.0)
        else:
            intrinsic = max(k - f, 0.0)
        total += c["side"] * intrinsic
    return total * LOT_SIZE


def calibrate() -> tuple[pd.DataFrame, dict]:
    rows = []
    total_delta = total_gamma = total_vega = total_theta = 0.0

    for c in CONTRACTS:
        t = year_fraction(c["expiry"], VALUATION_DATE)
        premium = PREMIUMS[c["leg"]]
        iv = implied_vol(c["future"], c["strike"], premium, t, c["option"])
        model = black76_price(c["future"], c["strike"], iv, t, c["option"])
        g = black76_greeks(c["future"], c["strike"], iv, t, c["option"])

        total_delta += c["side"] * g["delta"]
        total_gamma += c["side"] * g["gamma"]
        total_vega += c["side"] * g["vega_per_1pct"]
        total_theta += c["side"] * g["theta_per_day"]

        rows.append(
            asdict(
                Calibration(
                    leg=c["leg"],
                    future=c["future"],
                    strike=c["strike"],
                    premium=premium,
                    days_to_expiry=(c["expiry"] - VALUATION_DATE).days,
                    implied_vol=iv,
                    model_price=model,
                    abs_error=abs(model - premium),
                )
            )
        )

    table = pd.DataFrame(rows)

    intrinsic = intrinsic_value_at_futures()
    entry_value = (
        -PREMIUMS["L1_SELL_MONTHLY_ATM_PE"]
        + PREMIUMS["L2_BUY_MONTHLY_ATM_MINUS_2_CE"]
        + PREMIUMS["L3_BUY_WEEKLY_ATM_PLUS_2_PE"]
        - PREMIUMS["L4_SELL_WEEKLY_ATM_CE"]
    ) * LOT_SIZE

    broker_time_value = entry_value - intrinsic

    # POP reconstruction from the screenshot's one-SD range and two displayed
    # expiry breakevens. Profit occurs outside the breakeven interval in the
    # screenshot. This is a model reconciliation, not an empirical probability.
    pop = norm.cdf((SCREENSHOT_BREAKEVEN_LOW - SPOT) / SCREENSHOT_SD_1) + (
        1.0 - norm.cdf((SCREENSHOT_BREAKEVEN_HIGH - SPOT) / SCREENSHOT_SD_1)
    )

    summary = {
        "valuation_date": str(VALUATION_DATE.date()),
        "spot": SPOT,
        "weekly_future": WEEKLY_FUT,
        "monthly_future": MONTHLY_FUT,
        "weekly_expiry": str(WEEKLY_EXPIRY.date()),
        "monthly_expiry": str(MONTHLY_EXPIRY.date()),
        "entry_net_premium_per_point": 180.75,
        "entry_net_premium_rupees": float(entry_value),
        "intrinsic_value_reconstructed": float(intrinsic),
        "screenshot_intrinsic_value": SCREENSHOT_INTRINSIC,
        "intrinsic_abs_error": float(abs(intrinsic - SCREENSHOT_INTRINSIC)),
        "time_value_reconstructed": float(broker_time_value),
        "screenshot_time_value": SCREENSHOT_TIME_VALUE,
        "time_value_abs_error": float(abs(broker_time_value - SCREENSHOT_TIME_VALUE)),
        "portfolio_delta": total_delta,
        "screenshot_delta": SCREENSHOT_DELTA,
        "delta_abs_error": float(abs(total_delta - SCREENSHOT_DELTA)),
        "portfolio_gamma": total_gamma,
        "screenshot_gamma": SCREENSHOT_GAMMA,
        "portfolio_vega_per_1pct": total_vega,
        "screenshot_vega": SCREENSHOT_VEGA,
        "vega_abs_error": float(abs(total_vega - SCREENSHOT_VEGA)),
        "portfolio_theta_per_day": total_theta,
        "screenshot_theta": SCREENSHOT_THETA,
        "theta_abs_error": float(abs(total_theta - SCREENSHOT_THETA)),
        "screen_pop": SCREENSHOT_POP,
        "pop_reconstructed": float(pop),
        "pop_abs_error": float(abs(pop - SCREENSHOT_POP)),
        "screen_max_profit": SCREENSHOT_MAX_PROFIT,
        "screen_max_loss": SCREENSHOT_MAX_LOSS,
        "screen_decay": SCREENSHOT_DECAY,
        "screen_breakeven_low": SCREENSHOT_BREAKEVEN_LOW,
        "screen_breakeven_high": SCREENSHOT_BREAKEVEN_HIGH,
        "screen_sd_1": SCREENSHOT_SD_1,
    }
    return table, summary


def build_payoff_curve(
    calibration: pd.DataFrame,
    points: int = 401,
) -> pd.DataFrame:
    # Broker-style instantaneous strategy value over a target spot grid.
    # Each expiry gets its own forward basis (current future - current spot).
    # IVs are held fixed for this diagnostic; this is not a forecast.
    spot_grid = np.linspace(22100.0, 24100.0, points)
    weekly_basis = WEEKLY_FUT - SPOT
    monthly_basis = MONTHLY_FUT - SPOT
    iv_map = calibration.set_index("leg")["implied_vol"].to_dict()

    rows = []
    for s in spot_grid:
        value_points = 0.0
        for c in CONTRACTS:
            basis = weekly_basis if c["future"] == WEEKLY_FUT else monthly_basis
            f = s + basis
            t = year_fraction(c["expiry"], VALUATION_DATE)
            iv = iv_map[c["leg"]]
            value_points += c["side"] * black76_price(f, c["strike"], iv, t, c["option"])
        pnl_rupees = (value_points - 180.75) * LOT_SIZE
        rows.append({"target_spot": s, "strategy_value_points": value_points, "pnl_rupees": pnl_rupees})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="data/cache/phase9")
    args = ap.parse_args()

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    calibration, summary = calibrate()
    calibration.to_csv(out / "black76_leg_calibration.csv", index=False)
    (out / "broker_model_reconciliation.json").write_text(json.dumps(summary, indent=2))

    payoff = build_payoff_curve(calibration)
    payoff.to_csv(out / "broker_style_payoff_curve.csv", index=False)

    with pd.ExcelWriter(out / "phase9_reconciliation.xlsx") as writer:
        calibration.to_excel(writer, index=False, sheet_name="IV_Calibration")
        payoff.to_excel(writer, index=False, sheet_name="Payoff_Curve")
        pd.DataFrame([summary]).to_excel(writer, index=False, sheet_name="Summary")

    print(json.dumps(summary, indent=2))
    print("\\nLeg calibration:")
    print(calibration.to_string(index=False))


if __name__ == "__main__":
    main()
