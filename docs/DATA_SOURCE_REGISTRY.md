# Phase 2 — Data Source Registry

## Primary option source

Hugging Face: rissin/nse-options-intraday, revision 8f7739c.

The dataset documents 1-minute NIFTY/SENSEX option data from October 2024 onward, assembled from Upstox historical API candles. The yearly Parquet files used by the pilot are:

- upstox_intraday/NIFTY/NIFTY_2025.parquet
- upstox_intraday/NIFTY/NIFTY_2026.parquet
- upstox_intraday/SENSEX/SENSEX_2025.parquet
- upstox_intraday/SENSEX/SENSEX_2026.parquet

The raw data are queried remotely; only a reduced, strategy-specific extract is cached in this repository. This avoids copying a multi-gigabyte third-party dataset into Git.

## Spot source

Hugging Face: thetrademarkk/india-index-options-1m.

Spot files:
- index/NIFTY.parquet
- index/SENSEX.parquet

The dataset card states that these are 1-minute index OHLCV(+OI) bars and includes a timestamp field in IST.

## Exchange validation sources

- NSE historical F&O reports expose historical contract-wise price/volume information and the UDiFF transition.
- NSE Circular 128/2024 set NIFTY's revised market lot at 75 from new contracts introduced from 20-Nov-2024.
- NSE Circular 176/2025 revised NIFTY's lot to 65; the new lot applies after the specified transition and existing weekly/monthly expiries through 30-Dec-2025 retained 75.
- BSE documentation records SENSEX market lot 20 since the 2015 revision; the Phase 2 contract audit still checks the actual source rows.

## Data policy

The repository does not redistribute the raw third-party Parquet files. The workflow queries the public source remotely and caches only the reduced strategy extract, provenance metadata, checksums, and audit report.

## Scope for the primary test

Primary sample window:
- start: 2025-10-01
- end: 2026-09-22

This window is chosen so the locked Tuesday NIFTY and Thursday SENSEX expiry conventions apply to the whole primary sample.

## Calendar and coverage correction

The first Phase 2 extractor used observed spot dates as a trading calendar. That was corrected after audit because missing spot observations must not be interpreted as exchange holidays. The locked calendar now uses the explicit holiday file at data/calendar/exchange_holidays.csv, while missing spot observations are separately logged as data gaps.

The comparable Phase 2 sample ends on 2026-05-27, the common spot-data endpoint used by the current pinned reference files. Later SENSEX observations are not used to create an unequal cross-index window.

The 2026 SENSEX holiday rows in the current calendar are mirrored from the corresponding NSE market holiday schedule and are marked as provisional pending direct BSE confirmation; this remains a Phase 2 data-audit item rather than a hidden assumption.
