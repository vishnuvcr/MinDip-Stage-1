# MinDip — Stage 1

Research repository for a reproducible, cost-aware, multi-leg index-options backtesting program covering NIFTY 50 and BSE SENSEX.

## Current status

- Phase 0 — Governance & reproducibility: **complete**
- Phase 1 — Four-leg reverse-calendar implementation: **complete pending CI/data validation**
- Primary strategy specification: locked from the user request; no optimization has been performed.
- Data status: no production market dataset is committed yet. Deterministic synthetic tests are included; historical performance is not claimed.

## Repository map

| Area | Purpose |
|---|---|
| RESEARCH_PLAN.md | Master research phases, gates, and stop conditions |
| STATUS.md | Current phase/status ledger |
| ERROR_LOG.md | Mistakes, failures, and corrective actions |
| MIN_DIP_PROJECT_INSTRUCTIONS.md | Project operating instructions retained in-repo |
| research/CONVERSATION_LOG.md | User-visible request/action ledger (private chain-of-thought is not stored) |
| src/ | Backtesting library |
| scripts/ | CLI entry points |
| tests/ | Deterministic unit tests |
| data/ | Cached input/output data layout |
| docs/ | Strategy, assumptions, sources, and phase results |
| .github/workflows/ | Manual/CI research workflows |

## Phase 1 implementation

The reference engine in src/multileg_options_backtest.py supports both NIFTY and SENSEX dynamically. It implements:

- ATM strike selection from the 09:30 spot observation;
- monthly ATM PE buy;
- weekly ATM+2-strike PE sell;
- weekly ATM CE buy;
- monthly ATM−2-strike CE sell;
- Tuesday/Thursday weekly and last-Tuesday/last-Thursday monthly expiry math;
- previous-trading-day holiday roll;
- first quote at/after 09:30 for entry and last quote at/before 15:15 for exit;
- 0.5% adverse slippage per leg at entry and exit;
- ₹40 per leg, ₹160 per cycle fixed cost;
- ₹1,50,000 ROC denominator;
- trade-level and leg-level outputs plus skipped-cycle diagnostics.

## Important implementation note

The requested 50-point NIFTY and 100-point SENSEX strike intervals are treated as **research assumptions**. Exchange contract specifications can change, so a production dataset must be reconciled with the exchange contract master and date-specific lot sizes.

Phase 2 is the data-audit gate. Historical results are intentionally deferred until point-in-time option/spot data and calendar validation are available.


## Phase 2 — Data audit

Phase 2 is now active. The repository queries a pinned public 1-minute option dataset remotely and caches only a reduced strategy-specific extract, provenance metadata, checksums, and audit outputs. Raw third-party Parquet files are not copied into the repository. See `docs/DATA_SOURCE_REGISTRY.md`, `docs/PHASE2_DATA_AUDIT.md`, and the manual workflow `.github/workflows/phase2-data-audit.yml`.


### Latest Phase 2 execution
The first end-to-end remote extraction completed successfully and produced a small strategy-specific cache, but its automated push hit a branch-race. The workflow now rebases before pushing generated data. The provisional extraction observed 34 NIFTY and 38 SENSEX target cycles, with 29 fully executable four-leg cycles in each index; these counts are not yet treated as final until the cache is committed and audited.
