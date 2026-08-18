# Canonical source-doc format for doc-derived journey generation (Step-2 amendment)

The machine-readable format that the slicer (`journey-gen-slice.sh`, a later task) parses to
bundle PRD features with their APP_FLOW journeys. This is a **Step-2 doc-format amendment**: the
PRD and APP_FLOW that Step 2 produces must conform to it before journey generation can run.

Runtime truth never lives in these docs or in `JOURNEY_MAP.md` — it lives only in the CI-owned
ledger. This format defines journey **intent** sources only.

---

## 1. PRD — FEAT block format

Each product feature is a block headed by its `FEAT-ID`:

```
## FEAT-001 — "Invoice upload"
priority: P0                          # REQUIRED — one of P0 | P1 | P2 | P3
covers_flows: AFJ-001, AFJ-002        # optional if the APP_FLOW journeys back-link via covers_features
user_story: As an ops user, I upload an invoice and see it accepted.
acceptance_criteria:
  - AC-1: a valid CSV is accepted
  - AC-2: the row shows status=ACCEPTED
edge_cases:                           # where applicable
  - malformed CSV is rejected with row-level reasons
```

- `## FEAT-<n> — "<title>"` — the block heading carries a stable `FEAT-<n>` id. An optional uppercase domain prefix is first-class: the recognized form is `FEAT-([A-Z]+-)?<n>` (e.g. `FEAT-001` or `FEAT-SMS-001`).
- `priority:` — **REQUIRED**, machine-readable, exactly one of `P0 | P1 | P2 | P3`.
- `covers_flows:` — comma-separated `AFJ-ID`s this feature is exercised by (the FEAT→AFJ link). Optional *only if* the relevant APP_FLOW journeys back-link to this feature via `covers_features`.
- `user_story:`, `acceptance_criteria:` — the source of the journey `goal` and `oracle`.
- `edge_cases:` — where applicable; the source of `negative_states`.

**Rule:** a FEAT block whose `priority:` is missing or not one of `P0..P3` will later **fail closed** as `PRD_PRIORITY_UNPARSEABLE`. The slicer never guesses a priority.

**Gate conformance (owner ruling A, 2026-07-14).** `FEAT-([A-Z]+-)?<n>` is the *canonical* feature-id grammar for the whole framework, and **every** script that anchors on FEAT ids parses it: `check-doc-format.sh`, `check-persona-coverage.sh`, `check-journey-coverage.sh`, `check-journey-provenance.sh`, `journey-gen-slice.sh`, `persona-gen-slice.sh`, `mocks/bin/check-mock-coverage.sh`, `author-bundle.sh`, `journey-extracted-confirm.sh`. Until 2026-07-14 the coverage gates and the two slicers anchored on the narrower `^## FEAT-[0-9]`, which silently ignored every **prefixed** id: a 122-feature PRD of `FEAT-AUD-*` blocks derived *zero* anchors, so `check-persona-coverage.sh` died `NO_ANCHORS` ("the PRD is empty") and `check-journey-coverage.sh` reported every real journey's `covers` as `INVALID_SOURCE_ID` ("not a FEAT-ID in PRD") — each gate blaming the docs for its own regex. The near-misses remain **non-ids** and are never anchored: `FEAT-abc`, `FEATURE-001`, `FEAT-`, `FEAT-AUD-` (prefix, no number), `FEAT-AUD` (no separator, no number). Regression evidence: `journey/tests/feat-anchor-grammar_test.sh`.

---

## 2. APP_FLOW — user journey format

Documented user journeys live under a dedicated section:

```
## User Journeys

### AFJ-001 — "Corrected invoice upload"
covers_features: FEAT-001              # comma-separated FEAT-IDs (the AFJ→FEAT link)
steps:
  1. land on /invoices (state: EMPTY)
  2. upload malformed.csv -> schema_error
  3. re-upload corrected.csv
  4. observe ACCEPTED
states: [EMPTY, ERROR, SUCCESS]        # where applicable
```

- There MUST be a `## User Journeys` section.
- Each journey is headed `### AFJ-<n> — "<title>"` — the heading MUST carry a stable `AFJ-<n>` id.
- `covers_features:` — comma-separated `FEAT-ID`s this journey exercises (the AFJ→FEAT link).
- `steps:` — the ordered path; the source of the journey `steps`.
- `states:` — where applicable; a source of `negative_states`.

**Rule:** any journey entry under `## User Journeys` **without** an `AFJ-ID` in its heading will later **fail closed** as `APP_FLOW_UNIDDED`. The slicer never invents an id for an un-id'd journey.

---

## 3. FEAT ↔ AFJ traceability rule

A journey needs BOTH sides — the PRD acceptance criteria (its **oracle**) and the APP_FLOW path
(its **steps**) — so a FEAT and an AFJ must be **bundleable**:

- A FEAT and an AFJ are bundleable iff **at least one explicit link direction exists**:
  - PRD `covers_flows:` (FEAT → AFJ), **or**
  - APP_FLOW `covers_features:` (AFJ → FEAT).
- If **no link exists in either direction**, the slicer **must not fabricate a bundle** (a
  single-source bundle would force the generator to invent the missing oracle or steps).
- An **unlinked** P0/P1 FEAT-ID or AFJ-ID must later become a **structured coverage gap**
  (owner/expiry/reviewer), **never an invented journey**. Fix the docs (add a link) or log the gap.

---

## 3b. APP_FLOW — `## Screens` section (Increment-2 amendment)

Deterministic TEST_SURFACE derivation needs structured screens:

```
## Screens

### SCR-001 — "invoices_list"
route: /invoices
states: [EMPTY, LOADING, ERROR, SUCCESS]
```

- Each screen is headed `### SCR-<n> — "<name>"` — a stable `SCR-<n>` id AND a
  quoted machine-readable name (the TEST_SURFACE `## SURFACE:` key). An optional
  uppercase domain prefix is first-class: the recognized form is
  `SCR-([A-Z]+-)?<n>` (e.g. `SCR-001` or `SCR-SMS-1`).
- `route:` — **REQUIRED**; the screen's public route.
- `states:` — where applicable.
- A journey **touches** a screen iff the screen's `route` token appears in that
  journey's `steps`. Every gate re-derives this rule from APP_FLOW directly —
  no generator output is ever trusted for it.
- A screen heading without an `SCR-<n>` id, a missing `route:`, or a duplicate
  screen id **fails closed**. **Enforced at preflight by `check-doc-format.sh`,
  not only at slice time** (`surface-gen-slice.sh`): the preflight reports
  `SCREENS_SECTION_MISSING`, `SCREEN_UNIDDED`, `SCREEN_UNNAMED`,
  `SCREEN_NO_ROUTE`, and `DUPLICATE_SCREEN_ID` at once, and fails a screen whose
  route is touched by no AFJ step (`SCREEN_UNTOUCHED`) unless `--allow-unlinked`
  defers it to the structured coverage-gap workflow.

## 4. DOC_FORMAT gap rule

`PRD_PRIORITY_UNPARSEABLE` and `APP_FLOW_UNIDDED` are **blocking document-format diagnostics**:

- They are **NOT coverage credits** — unlike a legitimate `FEAT`/`AFJ` gap (which accounts for an
  id that genuinely has no faithful journey), a `DOC_FORMAT` diagnostic means the *source document
  is malformed*.
- They **halt generation and promotion** until the source doc is fixed and the pipeline re-run.
- The coverage gate treats any `DOC_FORMAT` gap present as a hard failure — it can never satisfy an
  id's coverage.

## 5. Gap records — `expires:` is canonical

A structured coverage-gap record (`JOURNEY_COVERAGE_GAPS.md`, `PERSONA_COVERAGE_GAPS.md`) carries
`source_id:` / `source_type:` / `reason:` / `owner:` / `reviewer:` / **`expires:`** (`YYYY-MM-DD`),
all non-blank.

**`expires:` is the CANONICAL spelling for new records.** `expiry:` is accepted as a **legacy
synonym** by both coverage gates and by `journey-gen-check-candidate.sh` (owner ruling 2026-07-14,
item 2) — compatibility is additive, and no existing project is forced to rewrite a record. A record
with **neither** spelling still fails; a record carrying **both with different dates** is ambiguous
and **fails closed** (one record cannot expire on two days, and an ambiguous record must never
become a coverage credit); both with the same date is redundant and is accepted.

## 5.2 `JOURNEY_COVERAGE_MANIFEST.json` — GENERATED EVIDENCE, never authored

The coverage manifest is the artifact `check-journey-coverage.sh` reconciles against. Its shape:

```json
{
  "JOURNEY-<n>": { "covers": ["FEAT-…"], "flows": ["AFJ-…"] },
  "_index": { "<FEAT|AFJ id>": { "journeys": ["JOURNEY-…"], "gap": "<id>|null" } }
}
```

**It is generated evidence, not a manually authored SSOT** (owner ruling 2026-07-14, item 3).
Anything a human can type to make a gate pass is not evidence — a hand-written coverage manifest is
merely a *claim* about coverage wearing the costume of proof. The producer is:

```sh
sh journey/bin/generate-journey-coverage-manifest.sh PRD APP_FLOW JOURNEY_MAP GAPS \
  > JOURNEY_COVERAGE_MANIFEST.json
```

It derives the manifest **only** from canonical machine-readable anchors: the PRD's `FEAT` ids and
their `priority:`, APP_FLOW's `AFJ` ids, the journey map's own `covers:` / `flows:` fields, and
formally recorded gap records. It **never infers a mapping from a structural coincidence** — a
journey covers an AFJ when its `flows:` field *says so*. (Inferring the journey↔AFJ mapping from,
say, matching covers-sets or equal ordinals would let the framework manufacture coverage the project
never declared. An empty `flows:` means the AFJs are uncovered, and the gate must say so.)

Output is **deterministic**: identical inputs ⇒ byte-identical output. Stable key order, sorted and
deduped arrays, fixed indent, and **no timestamps, paths, usernames or other environment-dependent
values**.

The producer **fails closed** rather than emit something a gate would swallow: `MISSING_SOURCE`,
`PRD_PRIORITY_UNPARSEABLE`, `APP_FLOW_UNIDDED`, `NO_ANCHORS`, `DUPLICATE_JOURNEY_ID`,
`INVALID_SOURCE_ID` (a journey mapping to an unknown feature/AFJ, or a gap naming a non-existent
anchor), `MALFORMED_GAP`, `AMBIGUOUS_GAP`, `DOC_FORMAT_GAP`.

### Drift check + required CI order

A committed manifest must be **verified against its sources**, never trusted:

```sh
sh journey/bin/generate-journey-coverage-manifest.sh PRD APP_FLOW JOURNEY_MAP GAPS \
  --check JOURNEY_COVERAGE_MANIFEST.json     # exit 1 = MANIFEST_STALE
```

**CI order is binding:** manifest generation-or-drift-verification **first**, then
`check-journey-coverage.sh` **against the verified manifest**. A coverage gate run against a stale
or hand-edited manifest proves nothing about the code that was actually committed — the drift check
is what makes the manifest evidence rather than assertion. See
`journey/docs/ci-journey-gates.example.yml`.
