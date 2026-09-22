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

### E-0009 — Final validation records formal DSR/PBO as not estimable
- The study contains one locked strategy rather than a set of independently selected candidate strategies.
- Formal multi-trial DSR and PBO are therefore not identified by the design.
- Fix: report a single-trial PSR diagnostic and CPCV-style path stability instead of fabricating multi-trial estimates.
