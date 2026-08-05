# KLOSS Step 5 Drift Auditor

Run this weekly, pre-release, or whenever maintain-mode records may have drifted.

## Prompt

You are auditing whether reality and records still agree. Read-only except for `DRIFT_REPORT.md` and proposed entries.

1. Range: run `git log kloss-last-drift-audit..HEAD --oneline --stat`.
2. Ledger check: for each commit touching code paths, find its `Docs/progress.txt` entry and, for Tier 2 or Tier 3, its CR file. Missing entry is a DRIFT finding. Draft a retroactive entry from the diff and mark it `[RETRO]` for human approval. Do not silently backfill.
3. Cascade check: for each commit whose diff implies a doc update, verify that the doc changed in that commit. Code-without-doc is a DRIFT finding with the specific missing doc line.
4. Reverse check: sample 5 concrete claims from canonical docs, such as a column, endpoint, validation rule, state, or permission, and verify each against current code at file and line. Contradiction is a STALE-DOC finding `[X]`.
5. Exemption debt: list every unrepaid exemption tag with age. Anything older than 2 audits escalates to the top of the report.
6. Lessons check: any reverted commit in range without a `LESSONS.md` entry is a finding.
7. Emit `DRIFT_REPORT.md`: findings by severity, starting with STALE-DOC, then unrecorded changes, then debt. Each finding needs evidence and a proposed one-line fix. End with verdict `CLEAN`, `DRIFTING`, or `DECAYED`.
8. On human approval of fixes, apply them, then run `git tag -f kloss-last-drift-audit HEAD`.
