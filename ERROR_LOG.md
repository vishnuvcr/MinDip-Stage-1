# Error Log

## 2026-09-22

### E-0001 — Empty Git repository could not create first phase branch
- Observed: GitHub rejected branch creation because the repository had no commits.
- Cause: repository initialized but empty.
- Fix: created an initial README.md commit on main, then created phase-0-governance.
- Prevention: verify the repository has an initial commit before branch creation.

### E-0002 — No production option dataset available in target repository
- Observed: repository contents endpoint returned 404 because the repo was empty before initialization.
- Research implication: no real backtest result is claimed at this stage.
- Fix: build the engine and deterministic tests first; defer historical results until cached data is added.

### E-0003 — Local clone/network verification unavailable
- Observed: a container git clone of github.com failed with DNS/network resolution error.
- Research implication: no claim is made that tests were locally executed in this session.
- Fix: commit deterministic tests and a manual/push GitHub Actions workflow so CI can perform the authoritative software check.
- Prevention: treat external-network execution as optional; keep reproducible CI in the repository.


### E-0004 — Phase 2 schema review found provider-field mismatch before CI
- Observed: the first Phase 2 extractor draft assumed `symbol`, `trading_day`, and `open_interest` fields in the primary rissin options dataset.
- Correct schema: `underlying`, `date`, and `oi`.
- Fix: patched the option query before relying on any empirical output.
- Prevention: pin and audit provider schemas before extracting historical results.

### E-0005 — Spot source schema mismatch
- Observed: Phase 2 workflow failed because the selected spot file does not expose `open_interest` in its index table.
- Cause: the source tree contains OHLCV index rows without that field in the queried file.
- Fix: removed `open_interest` from the spot query and pinned both source families to immutable revisions.
- Prevention: treat each file partition's schema independently; do not infer option-chain columns from spot schema.

### E-0006 — Phase 2 extraction succeeded but cache commit lost a race
- Observed: the full remote extraction completed and produced a 364 KB reduced cache with 29 complete cycles for each index, but the GitHub Actions push was rejected because the branch changed while the job was running.
- Cause: the workflow committed data from an older checkout while later documentation commits had advanced the branch.
- Fix: changed the workflow to fetch, rebase onto the current remote branch, and then push the cache commit.
- Prevention: never push generated research artifacts from a long-running workflow without rebasing against the latest branch tip.


### E-0007 — Missing spot observations were initially misclassified as holidays
- Observed: The first Phase 2 calendar logic derived trading dates from the spot dataset itself. This produced incorrect expiry rolls when the spot source had a missing day.
- Impact: Several monthly expiries were assigned to the wrong calendar date, including SENSEX October 2025 and NIFTY May 2026.
- Fix: Added an explicit exchange holiday calendar and separated holiday logic from spot-data availability. The sample end was also aligned to the common spot-data coverage date of 2026-05-27.
- Prevention: Never infer exchange calendars from missing market observations; calendar provenance is now an independent research input.


### E-0008 — Corrected extraction changes the historical result
- After the calendar correction, the locked sample produced 33 NIFTY and 28 SENSEX complete baskets rather than the initial 29/29.
- The corrected primary result is retained; the superseded result must not be used in later analysis.
- The superseded cache was overwritten by the corrected workflow output and the provenance manifest was refreshed.


### E-0009 — Research-status files lagged completed Phase 3/4 branches
- Observed: The Phase 4 branch inherited stale status text from before the corrected Phase 3/4 runs.
- Fix: synchronized README, STATUS, RESEARCH_PLAN, and CONVERSATION_LOG with the completed empirical phases before starting Phase 5.
- Prevention: phase branches must refresh the status ledger immediately after each workflow gate.


### E-0010 — DSR/PBO identifiability must not be manufactured
- Observation: the research has only one prespecified strategy, so standard multiple-trial DSR and PBO cannot be validly estimated.
- Fix: report them as not estimable and provide the observed Sharpe/skew/kurtosis plus CPCV and permutation diagnostics instead.
- Prevention: do not create artificial candidate trials from cost/slippage stress cells.

### E-0011 — Phase 7 workflow input escaping
- Observed: the first screenshot-exact workflow passed the literal strings "\2025-10-01" and "\2026-05-27" to the Python script.
- Cause: GitHub Actions expressions were over-escaped when embedded in the repository-management command.
- Fix: rewrote the workflow so the GitHub expression is emitted literally as ${{ ... }}.
- Prevention: inspect rendered workflow YAML before running a data-extraction phase.


### E-0012 — Phase 6 conclusion was over-applied to a different strategy specification
- Observation: the screenshot's worked example uses 25,000 monthly PE, 25,200 weekly PE, 25,050 weekly CE and 25,000 monthly CE at spot 25,049.55. The Phase 6 backtest used a different ATM/offset convention.
- Impact: the Phase 6 numerical conclusion cannot be treated as a conclusion about the screenshot strategy.
- Fix: created Phase 7 with a screenshot-derived strike mapping and fresh historical extraction.
- Prevention: keep screenshot-derived specifications separate from prose-derived parameterizations and reconcile them before empirical conclusions.

### E-0013 — Phase 7 cache push race
- Observed: The screenshot-exact extraction completed successfully, but the generated cache push lost a race with another branch update.
- Fix: reduced the cache to strategy-specific outputs rather than full spot archives and changed the workflow to force-with-lease after rebasing.
- Prevention: do not cache entire minute-level spot histories when the strategy output only needs the selected cycle observations.
