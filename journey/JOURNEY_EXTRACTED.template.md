# JOURNEY-EXTRACTED
extraction_commit: 0000000000000000000000000000000000000000
manifest_sha256:   0000000000000000000000000000000000000000000000000000000000000000

This file holds **code-extracted candidate journeys** staged by Step 0's
Stage 4b (the brownfield harness) — it is NOT the canonical intent SSOT.
`JOURNEY_MAP.md` is the SSOT; this staging file is the human-confirmation
gate for the one origin with no human intent behind it at all (spec §4.2,
§1). An extracted journey is a hypothesis about intent reverse-engineered
from mechanism — code proves what the system does, never that anyone wants
it, that it works at runtime, or that a user validated it. It is the
**lowest-trust origin** in the framework.

A code-extraction engine must never directly mutate the SSOT. A candidate
becomes a `JOURNEY-5xx` block only after a human marks it
`confirmation_status: CONFIRMED` and the confirm gate
(`journey/bin/journey-extracted-confirm.sh`) promotes it.

Runtime truth (`ci_status`, `last_run`, `ci_run_id`, `ci_artifact`,
`failure_summary`) is **never** stored here — same law as `JOURNEY_MAP.md`.
`lint-journey-extracted.sh` rejects any of those field keys anywhere in the
file (`RUNTIME_FIELD`).

`journey/bin/lint-journey-extracted.sh JOURNEY_EXTRACTED.md` validates
every entry in this file against the grammar below. See
`journey/docs/journey-extracted-format.md` for the full contract and the
closed code list.

## Field ownership

| Field | Owner |
|---|---|
| needs_human_confirm | Stage 4b — always `true` here; immutable birth-state field (I2) |
| confirmation_status | human confirmation reviewer |
| rejected_reason (REJECTED only) | human confirmation reviewer |
| grade | Stage 4b (Step 0 vocabulary); may be upgraded by a human via `resolution:`/`resolved_from:` |
| origin | Stage 4b — always `EXTRACTED` in this file |
| persona, goal, priority, covers, flows, oracle_surface, negative_states, steps, oracle/oracle_gap | Stage 4b (candidate intent, unconfirmed) |
| evidence | Stage 4b (normally `[]` — extraction citations live in `extraction_sources`, not here) |
| test | Stage 4b — normally the `<n>` placeholder until confirmation assigns one |
| runner | TECH_STACK |
| author_status | Stage 4b — always `UNWRITTEN` in this file |
| extraction_sources | Stage 4b — the byte-provenance backing the candidate (I1, I9) |
| prior_e2e (optional) | Stage 4b — staging-only; never copied to the map (§9.3, review M1) |
| resolution, resolved_from (optional together) | human confirmation reviewer, when resolving a former `[X]`/`[I]`/`[G]` (locks 2/3) |
| promoted_as (optional, gate-written) | `journey-extracted-confirm.sh` — never author this by hand |
| **runtime truth** (ci_status, last_run, ci_run_id, ci_artifact, failure_summary) | **CI only — no agent/human write path; never appears here** |

## Required fields (per entry)

`confirmation_status, grade, origin, persona, goal, priority, covers,
flows, oracle_surface, negative_states, steps, evidence, test, runner,
author_status`, plus exactly one of `oracle` / `oracle_gap`, plus
`needs_human_confirm` and `extraction_sources` (both carry their own
dedicated codes — see the format doc).

This is the same required set as `JOURNEY_MAP.template.md`'s required
fields, minus `data_fixtures`/`exemptions` (not carried by a
pre-confirmation candidate), plus this file's own envelope fields.

## Header

The first line is exactly `# JOURNEY-EXTRACTED`. Two required header
fields follow immediately:

- `extraction_commit:` — the full 40-hex sha of the audited repo every
  entry's citations are pinned against (`EXTRACTION_COMMIT_INVALID` if
  malformed).
- `manifest_sha256:` — the 64-hex sha256 of MANIFEST.md's machine block
  this staging run was checked against — the staleness anchor
  (`MANIFEST_SHA_INVALID` if malformed).

## Entry header

```
## EXTRACTED-<n> — "<title>"
```

`<n>` is a unique positive integer within the file (`DUPLICATE_EXTRACTED_ID`
on a repeat). The literal string `## JOURNEY-` must never appear anywhere
in this file, in a heading or otherwise — extracted entries never carry map
headers, so a paste-confirmation bypass is structurally impossible
(`FORBIDDEN_JOURNEY_HEADER`).

## `needs_human_confirm:` (I2)

Always `true` — the only legal value. Missing, or any other value,
is `NEEDS_CONFIRM_INVALID`. Nothing the staging pipeline does can ever set
this to `false`; it is a statement of origin, not a workflow state.

## `confirmation_status:`

Single-line field, one of `PENDING | CONFIRMED | REJECTED`
(`CONFIRM_STATUS_INVALID` otherwise; see `journey-extracted-format.md` §2
for why this file's vocabulary differs from the inbox's
`promotion_status`):

- `PENDING` — the default; not yet confirmed by a human.
- `CONFIRMED` — a human reviewer verified the citations back the claim; the
  confirm gate promotes it into `JOURNEY_MAP.md` (grade `[C]` and a real
  `oracle:` also required at that point).
- `REJECTED` — a human reviewer decided against the candidate. A
  `REJECTED` entry additionally REQUIRES a `rejected_reason:` line with a
  non-empty value (`REJECTED_REASON_MISSING` otherwise).

## `grade:`

One of `[C] | [I] | [G] | [X]` — the Step 0 vocabulary (Confirmed,
Incomplete, Guessed, conflicting/cross-source), applied at the entry level
(`GRADE_UNKNOWN` otherwise).

## `promoted_as:` (optional, gate-written — never author this by hand)

After `journey/bin/journey-extracted-confirm.sh` promotes a `CONFIRMED`
entry, it stamps a `promoted_as: JOURNEY-<n>` line onto that entry —
an audit trail naming the id the candidate became in `JOURNEY_MAP.md`.
Malformed, or present on a non-`CONFIRMED` entry, is `PROMOTED_AS_INVALID`.

## The shared journey fields

`origin, persona, goal, priority, covers, flows, oracle_surface,
negative_states, steps, oracle/oracle_gap, evidence, test, runner,
author_status` carry the same grammar as `JOURNEY_MAP.template.md`, with
two restrictions tightened for this file:

- `origin:` — the ONLY allowed value in this file is `EXTRACTED`
  (`BAD_ORIGIN` otherwise). A code-extracted candidate can only ever have
  come from Stage 4b; any other origin means it does not belong in this
  file.
- `author_status:` — the ONLY allowed value in this file is `UNWRITTEN`
  (`BAD_AUTHOR_STATUS` otherwise). Pre-confirmation candidates never have a
  test written against them.

`oracle:` and `oracle_gap:` are mutually exclusive — EXACTLY ONE must be
present (`ORACLE_EXACTLY_ONE` otherwise; see the format doc §4.5).

## `extraction_sources:` — the provenance block

Block field (2-space-indented entries, same shape as `steps:`):

```
extraction_sources:
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', ...)"
  - docs/FLW.md#Invoice resubmission
  - search: grep -rFn -- "sendEmail" src/routes/invoices.ts
```

The third line above is the absence-evidence form (DX-1, live-characterization
fix wave): `  - search: grep -rFn -- "<literal>" <relpath>`, re-executed at
the pinned `extraction_commit` — any hit means the absence claim was wrong
(`SEARCH_DIVERGED`). This is the ONLY legal way to cite a `[C-absent]`
claim or the absence side of an `[X]` disagreement; never freeform prose.

At least one line is always required (`SOURCES_MISSING`); at least two when
`grade: [X]` (`X_ONE_SIDED`) or a `resolution:` line is present
(`SOURCES_MISSING`, ≥2 threshold). Full grammar and rationale:
`journey/docs/journey-extracted-format.md` §4.6.

## `resolution:` and `resolved_from:` — grade-history preservation

Optional together (never one without the other — `RESOLVED_FROM_MISSING`
otherwise). Written by a human resolving a former `[X]`/`[I]`/`[G]` entry
into a `[C]`+`CONFIRMED` state; `resolved_from:` names the grade being
resolved FROM (`[X] | [G] | [I]`), preserving the history the edit would
otherwise silently overwrite. Full grammar, the oracle-gap-repair shape,
and the human-resolution seam: `journey/docs/journey-extracted-format.md`
§4.8, §7.

## Allowed enum values (this file only)

- `origin` = `EXTRACTED` (the only value)
- `author_status` = `UNWRITTEN` (the only value)
- `needs_human_confirm` = `true` (the only value)
- `confirmation_status ∈ {PENDING, CONFIRMED, REJECTED}`
- `grade ∈ {[C], [I], [G], [X]}`
- `resolved_from ∈ {[X], [G], [I]}` (when present)

All other enums (`priority`, `oracle_surface`, `runner`, ...) follow
`JOURNEY_MAP.template.md`; this lint does not re-validate them — the
composed `lint-journey-map.sh` re-checks the full schema once an entry is
promoted, so the two can never disagree.

## Anti-vacuous

A staging file that exists with a valid `# JOURNEY-EXTRACTED` header but
zero `## EXTRACTED-<n>` entries is itself a failure (`NO_EXTRACTED_ENTRIES`)
— an empty staging file should not exist at all.

## Example (delete when seeding a real project)

## EXTRACTED-1 — "Invoice resubmission after a schema-error rejection"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [C]
origin:              EXTRACTED
persona:              ops user (inferred from the route's auth middleware)
goal:                 resubmit a corrected invoice after a schema-error rejection
priority:             P2
covers:               FEAT-014
flows:                []
oracle_surface:       UI+API
negative_states:      schema_error
steps:
  1. land on /invoices
  2. upload malformed.csv -> inject schema_error
  3. re-upload corrected.csv
  4. observe the row transition to ACCEPTED
oracle:               row status=ACCEPTED AND GET /invoices returns the row
evidence:             []
test:                 tests/journeys/journey-<n>.spec.ts
runner:               playwright
author_status:        UNWRITTEN
extraction_sources:
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)"
  - tests/e2e/invoice-resubmit.spec.ts:12 — "expect(row.status).toBe('ACCEPTED')"
prior_e2e:            tests/e2e/invoice-resubmit.spec.ts
