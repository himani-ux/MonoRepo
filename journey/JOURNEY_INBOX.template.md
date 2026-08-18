# JOURNEY-INBOX

This file holds **stochastic candidate journeys** proposed by the
Step 3 user-simulator engine — it is NOT the canonical intent SSOT.
`JOURNEY_MAP.md` is the SSOT; this inbox is the noise filter for the one
noisy capture source (spec §4.2). Only `origin=SIMULATOR` routes through
here — `PERSONA` is human-confirmed at spec time and `REALITY` comes from a
confirmed real failure; both write straight to the map.

A stochastic discovery engine must never directly mutate the SSOT. A
candidate becomes a `JOURNEY-<n>` block only after a human marks it
`promotion_status: ACCEPTED` and the triage gate
(`journey/bin/journey-inbox-triage.sh`) promotes it.

Runtime truth (`ci_status`, `last_run`, `ci_run_id`, `ci_artifact`,
`failure_summary`) is **never** stored here — same law as `JOURNEY_MAP.md`.
`lint-journey-inbox.sh` rejects any of those field keys anywhere in the
file (`RUNTIME_FIELD`).

`journey/bin/lint-journey-inbox.sh JOURNEY_INBOX.md` validates every entry
in this file against the grammar below. See
`journey/docs/journey-inbox-format.md` for the full contract and the
closed code list.

## Field ownership

| Field | Owner |
|---|---|
| promotion_status | human triage reviewer |
| rejected_reason (REJECTED only) | human triage reviewer |
| origin | simulator runner — always `SIMULATOR` in this file |
| persona, goal | simulator runner, from the persona + goal it was given |
| priority, covers | inherited from the persona/feature the simulator targeted |
| oracle_surface, negative_states, steps, oracle | simulator runner (candidate intent, unconfirmed) |
| evidence | simulator runner (trace/screenshot paths) |
| test | simulator runner — normally empty until promotion assigns one |
| runner | TECH_STACK |
| author_status | simulator runner — always `UNWRITTEN` in this file |
| simulator_trace | simulator runner — the run record backing the candidate |
| **runtime truth** (ci_status, last_run, ci_run_id, ci_artifact, failure_summary) | **CI only — no agent/human write path; never appears here** |

## Required fields (per entry)

`promotion_status, origin, persona, goal, priority, covers, oracle_surface,
negative_states, steps, oracle, evidence, test, runner, author_status,
simulator_trace`.

This is the same required set as `JOURNEY_MAP.template.md`'s required
fields, minus `flows`/`data_fixtures`/`exemptions` (not carried by a
pre-promotion candidate), plus `promotion_status` and `simulator_trace`
(inbox-only).

## Entry header

```
## INBOX-<n> — "<title>"
```

`<n>` is a unique positive integer within the file (`DUPLICATE_INBOX_ID` on
a repeat). The literal string `## JOURNEY-` must never appear anywhere in
this file, in a heading or otherwise — inbox entries never carry map
headers, so a paste-promotion bypass (pasting a real `## JOURNEY-<n>` block
in here to dodge triage) is structurally impossible
(`FORBIDDEN_JOURNEY_HEADER`).

## `promotion_status:`

Single-line field, one of `PROPOSED | ACCEPTED | REJECTED`
(`BAD_PROMOTION_STATUS` otherwise):

- `PROPOSED` — the default; not yet triaged.
- `ACCEPTED` — a human reviewer confirmed this candidate is worth
  promoting; the triage gate promotes it into `JOURNEY_MAP.md` on its next
  run.
- `REJECTED` — a human reviewer decided against promotion. A `REJECTED`
  entry additionally REQUIRES a `rejected_reason:` line with a non-empty
  value (`REJECTED_REASON_MISSING` otherwise).

## `promoted_as:` (optional, gate-written — never author this by hand)

After `journey/bin/journey-inbox-triage.sh` promotes an `ACCEPTED` entry, it
stamps a `promoted_as: JOURNEY-<n>` line directly after that entry's
`promotion_status:` line — an audit trail naming the id the candidate
became in `JOURNEY_MAP.md`. Malformed, or present on a non-`ACCEPTED`
entry, is `PROMOTED_AS_INVALID`. See
`journey/docs/journey-inbox-format.md` §2.3a for the full grammar.

## The shared journey fields

`origin, persona, goal, priority, covers, oracle_surface, negative_states,
steps, oracle, evidence, test, runner, author_status` carry the same
grammar as `JOURNEY_MAP.template.md`, with two restrictions tightened for
this file:

- `origin:` — the ONLY allowed value in this file is `SIMULATOR`
  (`BAD_ORIGIN` otherwise). A stochastic candidate can only ever have come
  from the simulator; any other origin means it does not belong in this
  file.
- `author_status:` — the ONLY allowed value in this file is `UNWRITTEN`
  (`BAD_AUTHOR_STATUS` otherwise). Pre-promotion candidates never have a
  test written against them.

## `simulator_trace:` — the run record

Block field (2-space-indented entries, same shape as `steps:` /
`preconditions:` on `JOURNEY_MAP.template.md`):

```
simulator_trace:
  - persona: P2
  - goal: upload a corrected invoice after the first was rejected
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 3
  - path: land on /invoices
  - path: upload malformed.csv
  - path: re-upload corrected.csv
  - stuck_point: hesitated after the schema_error toast
  - evidence: traces/inbox-1-sim.zip
```

Scalar entries — REQUIRED EXACTLY ONCE each:

- `persona: <token>` — the persona id the simulator ran as.
- `goal: <text>` — the goal it was given (free text).
- `app_build: <token>` — the app build/commit identifier it ran against.
- `runner: <token>` — the hands driver used (e.g. `playwright`).
- `patience_budget: <positive integer>` — the abandonment budget it was
  bound by.

List entries — repeatable:

- `path: <step>` — REQUIRED, at least one. Each is one step of the path
  actually driven (free text).
- `stuck_point: <text>` — OPTIONAL, zero or more. Where the simulator
  hesitated, retried, or nearly abandoned.
- `evidence: <relpath>` — REQUIRED, at least one. A trace/screenshot path
  relative to the repo, backing the candidate. No leading `/`, no `..`
  segments.

A `<token>` value is a single run of `[A-Za-z0-9._/-]` characters (no
spaces) — see `journey/docs/journey-inbox-format.md` for the full grammar
and closed code list.

## Allowed enum values (this file only)

- `origin` = `SIMULATOR` (the only value)
- `author_status` = `UNWRITTEN` (the only value)
- `promotion_status ∈ {PROPOSED, ACCEPTED, REJECTED}`

All other enums (`priority`, `oracle_surface`, `runner`, ...) follow
`JOURNEY_MAP.template.md`; this lint does not re-validate them — the
composed `lint-journey-map.sh` re-checks the full schema once an entry is
promoted, so the two can never disagree.

## Anti-vacuous

An inbox file that exists with a valid `# JOURNEY-INBOX` header but zero
`## INBOX-<n>` entries is itself a failure (`NO_INBOX_ENTRIES`) — an empty
inbox file should not exist at all.

## The triage-time re-anchor law (V1 F3)

A candidate as the simulator runner emits it is NOT yet triage-ready: its
`covers:` is a `## SURFACE: <screen>` name (e.g. `invoices_list`), not a
`FEAT-<n>` id — a sim bundle has no PRD/FEAT side to anchor against (see
`journey/gen/prompts/simulator-brain.md`). A human MUST re-anchor
`covers:` to real `FEAT-<n>` id(s) at triage before the journey can be
blind-authored, or `journey/bin/author-bundle.sh` fails closed
(`ANCHOR_TOKEN_INVALID`) on the ungrammatical non-FEAT anchor — every
anchor token must full-match its field's canonical id grammar before it
reaches any matcher. `flows:` is forced to `[]` at
promotion and MAY optionally be re-anchored to real `AFJ-<n>` id(s) at the
same time (leaving it `[]` is legal — `author-bundle.sh` treats it as zero
anchors). `test:` carries the literal placeholder token `<n>`
(`tests/journeys/journey-<n>.spec.ts`), which `journey-inbox-triage.sh`
substitutes with the assigned `JOURNEY-<n>` id at promotion — no human
action needed for that one field. Full grammar and rationale:
`journey/docs/journey-inbox-format.md` §6.1.

## Example (delete when seeding a real project)

## INBOX-1 — "Persona P2 stalls on invoice re-upload after schema error"
promotion_status: PROPOSED
origin:          SIMULATOR
persona:         P2 (impatient ops user)
goal:            upload a corrected invoice after the first was rejected, and see it accepted
priority:        P1
covers:          invoices_list
oracle_surface:  UI+API
negative_states: schema_error, retry_upload
steps:
  1. land on /invoices
  2. upload malformed.csv → inject schema_error
  3. re-upload corrected.csv
  4. observe retry_upload → ACCEPTED
oracle:          row status=ACCEPTED AND GET /invoices returns the row
evidence:        traces/inbox-1-sim.zip
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P2
  - goal: upload a corrected invoice after the first was rejected
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 3
  - path: land on /invoices
  - path: upload malformed.csv
  - path: re-upload corrected.csv
  - stuck_point: hesitated after the schema_error toast
  - evidence: traces/inbox-1-sim.zip
