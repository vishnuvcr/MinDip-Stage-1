# MinDip — Stage 1

Research repository for a reproducible, cost-aware, multi-leg index-options backtesting program covering NIFTY 50 and BSE SENSEX.

## Current status

- Phase 0 — Governance & reproducibility: **complete**
- Phase 1 — Four-leg reverse-calendar implementation: **in progress**
- Primary strategy specification: locked from the user request; no optimization has been performed.
- Data status: no market dataset is committed yet. Unit tests use deterministic synthetic fixtures; production results require a point-in-time option dataset plus spot observations.

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

## Research scope

The backtest models four legs:

1. Buy monthly ATM PE.
2. Sell weekly ITM PE at ATM + 2 strikes.
3. Buy weekly ATM CE at ATM strike.
4. Sell monthly ITM CE at ATM − 2 strikes.

Entry is 09:30 IST on the configured cycle-entry day; exit is 15:15 IST on the following weekly-expiry day, with previous-trading-day holiday rolls. Slippage and fixed cycle costs are modeled explicitly.

## Important implementation note

The requested 50-point NIFTY and 100-point SENSEX strike intervals are treated as **research assumptions**. Exchange contract specifications can change, so the production dataset must be checked against the exchange contract master before live use.

See the phase branch 'phase-1-reverse-calendar-backtest' for the implementation.
