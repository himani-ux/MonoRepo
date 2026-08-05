# AGENTS.md

## MAINTAIN MODE

This repository is in KLOSS Step 5 Maintain Mode after shipment. The docs must describe the current system after every change. Classify the request before code is changed, cascade affected docs in the same commit, and record the change in the progress ledger.

Repo conventions for this activation:
- Progress ledger: `Docs/progress.txt`
- CR directory: `crs/`
- Code roots watched by the commit hook: `psc-backend/`, `psc-frontend/`, plus common roots `src/`, `apps/`, `lib/`, `app/`, `backend/`, `frontend/`

### Change Intake

Every incoming request, including bug reports, feature asks, tweaks, and dependency bumps, must be classified before code is read.

Tier 1 - fix/chore. None of the Tier 2 or Tier 3 triggers apply. Examples: typos, copy changes, style fixes, bug fixes that restore documented behavior, and dependency patches.

Required ceremony:
- For bugs, run the debug protocol: reproduce, blast radius, root cause, fix.
- Every bugfix carries a regression test: the reproduction becomes a failing test before the fix, and the test and fix commit together.
- Record one `Docs/progress.txt` entry line.
- Cascade docs only if a doc described the broken behavior as correct. If so, fix that doc in the same commit and log it as an `[X]` finding.

Tier 2 - small feature or behavior change. Any of these triggers apply: new or changed DB column, new endpoint or changed contract, new screen or new screen state, changed role permission, new non-patch dependency, changed validation rule, or new analytics event.

Required ceremony:
- Open a CR file before coding.
- Run a mini-interrogation of only the affected Step 1 domains.
- Propose-and-confirm defaults are allowed; tag accepted defaults.
- Code, cascade docs, record progress.

Tier 3 - structural. Any of these triggers apply: new table or migration touching existing data, auth/session model change, cross-module contract change, new external integration, or anything that contradicts `IMPLEMENTATION_PLAN` or an existing canonical doc statement.

Required ceremony:
- Do everything required for Tier 2.
- Add an append-only `IMPLEMENTATION_PLAN` amendment. Do not edit original phases. Add `## Amendment <n> - <date>` with what changed, triggering discovery, and which phases or steps it supersedes.
- If interrogation-level decisions are invalidated, add superseding SSOT decision entries. Never edit or delete the old decision.

If a change is discovered to be under-classified, stop, reclassify, open the required CR, then continue.

### CR Format

Use sequential files named `crs/CR-###.md`.

Required sections:
- **What & why** - one paragraph, plain language.
- **Tier + triggers** - which objective triggers fired.
- **Domains touched** - Step 1 domain numbers; this drives mini-interrogation and doc cascade.
- **Decisions** - any new decision gets the project's next decision ID; supersessions must be named explicitly.
- **Doc cascade** - every canonical doc updated, with one line each explaining what changed. Also list expected docs not updated with `unchanged because...`.
- **Tests** - regression or new tests added.
- **Fidelity check** - for Tier 2 and Tier 3, re-read mini-interrogation answers against doc updates side by side and list missing or weakened details. If none, state `no deltas`.
- **Exemptions** - any `DOCS-EXEMPT`, `TEST-EXEMPT`, or `STATES-EXEMPT` used, with reason and repayment plan.

### Recording Rules

`Docs/progress.txt` is append-only. Add one entry per change using this schema:

```text
<date> | MAINTAIN | CR-### or T1 | <what changed, one line> | docs: <list or "none - reason"> | exemptions: <tags or "none">
```

Doc cascade must land in the same commit as the code change. A later docs commit is not allowed.

Docs describe what is true after the change ships. Future ideas belong in the CR as future-work notes, not in canonical docs.

Append to `LESSONS.md` when any of these happen:
- A change is reverted.
- The user corrects the approach.
- A bug traces to a pattern an existing lesson should have prevented. Strengthen that lesson and note the recurrence.
- A tier was misclassified.

Exemption tags are debt. Each exemption needs a reason and appears in every drift audit until repaid. Three unrepaid exemptions means stop and repay before new work.

### Goal

For each change, the completion condition is:

```text
The change is committed with tests passing including any required regression test; Docs/progress.txt entry appended; CR file complete for Tier 2/3 with empty or resolved fidelity-check deltas; all cascaded docs in the same commit; commit accepted by the commit-msg hook without exemption tags, or exemptions logged in the CR.
```
