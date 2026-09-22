# Sources & Assumption Audit

## Exchange expiry rules

- NSE states that NIFTY 50 index options have Tuesday weekly expiries and last-Tuesday monthly expiry, with a previous-trading-day holiday adjustment.
- BSE's June 23, 2025 notice documents the switch for SENSEX weekly contracts to Thursday and SENSEX monthly contracts to the last Thursday for expiries after September 1, 2025.
- SEBI's May 26, 2025 circular sets the regulatory framework for exchange-chosen Tuesday/Thursday expiry days.

## Locked research assumptions

- NIFTY strike interval = 50 points.
- SENSEX strike interval = 100 points.
- Two-strike ITM offset = 100 / 200 respectively.
- Cycle entry time = 09:30 IST.
- Exit time = 15:15 IST.
- Adverse slippage = 0.5% of option premium at every execution.
- Fixed cost = ₹40 per leg, ₹160 per cycle.
- Initial capital/margin denominator = ₹1,50,000.
- One lot per leg; actual contract lot size must be supplied separately if the premium data are quoted per unit.

## Important distinction

The code uses the user's fixed strike intervals as a backtest assumption. Exchange strike intervals and contract sizes may change; production runs should reconcile the dataset with the exchange's contract master for each date.

## Research context retained from prior project work

Prior project research emphasized that option strategies can look attractive before execution costs and then degrade materially under slippage/tail stress; the new backtest therefore treats friction as a first-class variable rather than an afterthought.
