# MinDip Project Operating Instructions

This file preserves the project-level operating rules that govern the research repository.

## Research workflow

- Form research questions and define aims/objectives.
- Perform literature, source, and data review before drawing empirical conclusions.
- Define methodology, statistical analysis, results, inference, discussion, strengths/limitations, conclusion, and future research.
- Maintain a detailed phase plan and keep execution aligned with it.
- Keep each research phase in its own Git branch.
- Give each phase a manual GitHub Actions workflow.
- Cache important datasets/artifacts in-repo where licensing and size permit; do not redownload unnecessarily.
- Log every error and corrective action in ERROR_LOG.md.
- Update the status and phase artifacts after each meaningful step and outcome.
- Keep the main README synchronized with the latest research status and links.
- Preserve a user-visible conversation/action log. Hidden chain-of-thought is not stored.
- Do not let the research run indefinitely; stop at the predefined phase gates.
- At completion, produce a structured research manuscript with methods, results, figures/tables, appendices, and supplements as appropriate.

## Market/trading scope

Where applicable, research should account for execution and market-structure effects including slippage, transaction costs, brokerage/taxes, cross-index inefficiencies, volatility regime, option surface, corporate actions, news, FII/DII flows, and global-market interactions.

## Reproducibility

- Use Python/pandas/numpy for the reference backtester.
- Keep deterministic tests and explicit assumptions.
- Never silently invent missing market data.
- Treat unsupported production claims as unverified.
- Preserve negative or inconclusive findings rather than optimizing them away.
