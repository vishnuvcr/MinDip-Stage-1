# Cached Data Layout

Production backtests should use point-in-time market data stored under this directory when licensing and repository size permit.

Recommended files:
- data/options/options_quotes.csv
- data/spot/spot_quotes.csv
- data/calendar/holidays.csv
- data/contracts/contract_master.csv

Required options schema:
Date, Time, Ticker, Expiry_Date, Strike, Option_Type, Close

Recommended additional fields for later execution research:
Bid, Ask, Volume, Open_Interest, Contract_Code, Lot_Size, Source

The Phase 1 engine does not synthesize missing market data. If a required leg, spot observation, or execution quote is missing, the cycle is logged in the skipped-cycle output.

Do not commit licensed data that cannot legally be redistributed.
