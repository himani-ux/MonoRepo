# JOURNEY_EXTRACTED format + lint — contract

Operator-facing contract for the code-extraction staging layer: how Step 0's
Stage 4b (brownfield harness) stages reverse-engineered journey candidates,
how a human confirms or rejects them, and how `lint-journey-extracted.sh`
proves the schema before any entry is ever eligible for promotion. Sibling
of `journey/docs/journey-inbox-format.md` and `journey/docs/reality-intake-format.md`;
same house style. Spec: `docs/superpowers/specs/2026-07-11-extracted-baseline-design.md`
(§4.2, §7.1, §14 — the ratification record supersedes any body text it
contradicts, notably the field name below).

---

## 1. Purpose and trust statement (B3)

`JOURNEY_MAP.md` is the canonical intent SSOT. Four of its five origins are
grounded in a human or a confirmed real event: `PERSONA` (a human wrote it),
`DERIVED` (generated from canonical docs a human wrote and approved),
`SIMULATOR` (a stochastic actor, but triaged by a human before promotion —
see `journey-inbox-format.md`), `REALITY` (a confirmed real failure). The
fifth, `EXTRACTED`, is different in kind, not just in provenance mechanics:

> An extracted journey is a hypothesis about intent reverse-engineered from
> mechanism. Code proves what the system does, never that anyone wants it,
> that it works at runtime, or that a user validated it. An extracted
> journey is the *lowest-trust* origin in the framework — the only one whose
> intent no human has ever stated.

This is spec §1's B3 law, verbatim. Every artifact in this contract exists
to enforce it structurally, not just state it:

- Every staged entry is born `needs_human_confirm: true` (I2) — an
  immutable birth-state field the lint rejects if it is ever anything else,
  including absent.
- The ONLY path from a staged entry to a real `JOURNEY-5xx` map block is a
  human explicitly marking it `confirmation_status: CONFIRMED` and running
  `journey-extracted-confirm.sh --approve` (I3, a later task, E5). Nothing
  in this contract's lint or template can promote anything — this file
  defines the STAGING schema only.
- A promoted entry never claims runtime truth: `author_status: UNWRITTEN`,
  `evidence: []`, no ledger record (I4). Extraction citations are
  provenance for the human reviewing the candidate, never evidence that
  anything works.

**Per-project artifact.** `JOURNEY_EXTRACTED.md` is written at the root of
an adopting project (sibling of that project's `JOURNEY_MAP.md` and
`JOURNEY_INBOX.md`, per spec §14 Q4) — it is NOT shipped by the framework.
The framework ships the template (`journey/JOURNEY_EXTRACTED.template.md`),
this contract doc, and the lint (`journey/bin/lint-journey-extracted.sh`).

This layer never gates on the extraction model itself (same stochastic
discovery -> deterministic gate boundary as the inbox, spec §3.3 of the
parent journey-validation design). It gates on the STAGED ARTIFACT:
`lint-journey-extracted.sh` proves the staging file is schema-valid before
any human confirmation decision is trusted, exactly as `lint-journey-map.sh`
does for the canonical map and `lint-journey-inbox.sh` does for the
stochastic inbox.

---

## 2. Why `confirmation_status`, not `promotion_status` (spec §14 Q1)

`JOURNEY_INBOX.md` uses `promotion_status: PROPOSED | ACCEPTED | REJECTED`
— a human is *selecting* which stochastic candidates are worth promoting
out of a batch the simulator generated with no claim of individual
correctness. `JOURNEY_EXTRACTED.md` uses a deliberately different word,
**`confirmation_status: PENDING | CONFIRMED | REJECTED`**, because the
human's act here is qualitatively different: they are *confirming a specific
factual claim the extractor made about the code* — "yes, this describes what
route/test/state-matrix X actually does" — not selecting among options. The
inbox's vocabulary is about editorial selection; this file's vocabulary is
about verifying an assertion against evidence already cited in the same
entry. Same three-state shape (a pending default, an accept path, a reject
path with a reason), different verb, because the human act it names is
different. This ruling is binding per spec §14 Q1: the field name is
`confirmation_status`, not the design draft's `confirm_status`.

The map entry that results from confirmation carries no live
`needs_human_confirm` or `confirmation_status` field — those are
staging-only. Promotion IS the ratification event. The promoted block does
retain one optional audit trail field, `extraction_provenance:` (a later
task, E5/E6 — see spec §14 Q1) — out of scope for this staging contract.

---

## 3. The staging file

One file (conventionally `JOURNEY_EXTRACTED.md`), carrying a required
two-line header, free narrative prose (no authority — same rule as a UAT
report's narrative or the inbox's), and zero or more `## EXTRACTED-<n>`
candidate blocks.

### 3.1 Header

```
# JOURNEY-EXTRACTED
extraction_commit: <40-hex sha of the audited repo>
manifest_sha256:   <64-hex sha256 of MANIFEST.md's machine block>
```

- The FIRST LINE of the file must be exactly `# JOURNEY-EXTRACTED`
  (`BAD_HEADER` otherwise — mirrors the `# JOURNEY-INBOX` / `# UAT-REPORT`
  first-line laws elsewhere in this framework).
- `extraction_commit:` binds every entry's citations to one pinned commit —
  the full 40-hex sha the extraction was run against. Malformed (not
  exactly 40 lowercase hex characters) is `EXTRACTION_COMMIT_INVALID`.
  Provenance re-verification against this pinned commit is a later gate's
  job (`check-extracted-provenance.sh`, task E2) — this lint validates
  GRAMMAR only.
- `manifest_sha256:` binds the staging file to the MANIFEST.md machine
  block it was checked against at staging time — the staleness anchor (spec
  I5/B5). Malformed (not exactly 64 lowercase hex characters) is
  `MANIFEST_SHA_INVALID`. Drift detection against the live MANIFEST.md is a
  later gate's job (`check-extraction-coverage.sh`, task E3) — this lint
  validates GRAMMAR only.
- The literal string `## JOURNEY-` must never appear anywhere in the file,
  in a heading or in prose (`FORBIDDEN_JOURNEY_HEADER`) — the same
  paste-promotion bypass guard `journey-inbox-format.md` §2.1 documents,
  applied here: an agent or human cannot dodge human confirmation by pasting
  a real-looking `## JOURNEY-<n>` block directly into this file.
- A file that exists but declares zero `## EXTRACTED-<n>` entries is itself
  a failure (`NO_EXTRACTED_ENTRIES`) — an empty staging file should not
  exist at all; delete it instead of leaving a vacuous shell (anti-vacuous,
  tested both ways — the golden fixture must never trip this code).

### 3.2 Entry heading grammar (L23)

```
## EXTRACTED-<n> — "<title>"
```

`<n>` is a unique positive integer within the file (`DUPLICATE_EXTRACTED_ID`
on a repeat; `BAD_EXTRACTED_ID` if `<n>` is zero). The heading is validated
to the canonical, character-exact form — a spaced em-dash (U+2014) and a
double-quoted, non-empty title — UP FRONT, as the first check on every
entry, before any field-level check runs (`ENTRY_HEADING_INVALID`
otherwise). This is the same discipline `journey-reality-intake.sh` and
`journey-inbox-triage.sh` apply to their own heading grammar (V-T5 F1 / L23):
the block-extraction accessor (`extracted_block` in `journey-lib.sh`) reads
headings PERMISSIVELY (`^## EXTRACTED-<n>([^0-9]|$)`, so a glued heading
like `## EXTRACTED-3—"t"` still extracts a block), but any later
id-rewriting step (a mutator, not this lint) would only match the canonical
spaced form. Validating the strict grammar here — independent of, and
before, the lenient extraction used to find the id at all — means a glued
heading can never silently survive past staging.

### 3.3 Entry field grammar

```
## EXTRACTED-<n> — "<title>"
needs_human_confirm: true
confirmation_status: PENDING | CONFIRMED | REJECTED
rejected_reason:     <non-empty>          (REJECTED only)
grade:               [C] | [I] | [G] | [X]
origin:              EXTRACTED             (the ONLY allowed value)
persona:             <text>
goal:                <text>
priority:            P2                    (model default until a human sets it)
covers:               FEAT-014             (manifest FEAT/screen anchors)
flows:                []                   (manifest AFJ anchors, or [])
oracle_surface:       UI+API
negative_states:      schema_error
steps:
  1. land on /invoices
  2. ...
oracle:               <success signal>     (EXACTLY ONE of oracle:/oracle_gap:)
evidence:             []
test:                 tests/journeys/journey-<n>.spec.ts
runner:               playwright
author_status:        UNWRITTEN             (the ONLY allowed value)
extraction_sources:
  - <path>:<line> — "<verbatim quote>"
  - <path>#<heading>
prior_e2e:            <relpath>             (optional, staging-only)
resolution:           <text>                (required with resolved_from)
resolved_from:        [X] | [G] | [I]       (required with resolution)
promoted_as:          JOURNEY-<id>          (gate-stamped; CONFIRMED only)
```

This is the same "full journey field set" `JOURNEY_MAP.template.md`
requires (`origin, persona, goal, priority, covers, flows, oracle_surface,
negative_states, steps, oracle, evidence, test, runner, author_status`),
minus `data_fixtures`/`exemptions` (not carried by a pre-confirmation
candidate — same rationale `journey-inbox-format.md` gives for dropping
those two from the inbox's required set), plus this file's own envelope
fields (`needs_human_confirm`, `confirmation_status`, `grade`,
`extraction_sources`) and optional fields (`rejected_reason`, `prior_e2e`,
`resolution`, `resolved_from`, `promoted_as`). `flows` IS required-present
here (unlike the inbox, which omits it) because Stage 4b anchors every
candidate against MANIFEST-declared screen/FEAT ids — an extracted
candidate always has something to anchor `covers:`/`flows:` against, even
if `flows:` legitimately resolves to `[]`.

- Required fields (key must be present; `MISSING_FIELD: <id>: <field>`
  otherwise): `confirmation_status, grade, origin, persona, goal, priority,
  covers, flows, oracle_surface, negative_states, steps, evidence, test,
  runner, author_status`. (`needs_human_confirm` and `extraction_sources`
  have their OWN dedicated codes — see below — that already cover total
  absence, so they are deliberately excluded from this generic list to
  avoid double-reporting the same root cause under two codes, the same
  precedent `journey-inbox-format.md` §2.5 documents for
  `simulator_trace`/`TRACE_MISSING`. `oracle`/`oracle_gap` are likewise
  excluded — `ORACLE_EXACTLY_ONE` below covers their joint absence.)
- Non-blank required subset (`BLANK_FIELD: <id>: <field>` when present but
  blank): `confirmation_status, grade, origin, persona, goal, priority,
  covers, oracle_surface, runner, author_status`. (`flows`, `negative_states`,
  `evidence`, `test` may be blank/`[]` — same optional-content precedent as
  `JOURNEY_MAP.template.md`/`journey-inbox-format.md`.)
- The map-inherited fields (`priority`, `oracle_surface`, `runner`, ...) are
  NOT re-validated for enum/business-rule correctness by this lint — only
  for presence/non-blankness above. Their full schema is
  `lint-journey-map.sh`'s job, re-run by the confirm gate (task E5) on the
  promoted block, so the two lints can never disagree about what a valid
  value looks like — same precedent as `journey-inbox-format.md` §2.2.

---

## 4. Field-by-field grammar

### 4.1 `needs_human_confirm:` (I2, immutable birth-state)

Single-line field. Must be present and its value EXACTLY the literal string
`true` — anything else (`false`, `True`, blank, or the key missing
entirely) is `NEEDS_CONFIRM_INVALID`. Unlike every other envelope field in
this file, absence is folded directly into this ONE code (not
`MISSING_FIELD`) — spec §14/I2's law is that this field states an origin
fact, not a workflow state that starts blank and gets filled in: an entry
that never carried it is exactly as wrong as one that carries `false`.

### 4.2 `confirmation_status:` and `rejected_reason:`

Single-line field, exactly one of `PENDING | CONFIRMED | REJECTED`
(`CONFIRM_STATUS_INVALID` otherwise, checked via the SAME first-match
`extracted_field` accessor described in §6 below — L11 discipline):

- `PENDING` — the default; not yet confirmed by a human.
- `CONFIRMED` — a human reviewer verified the citations back the claim.
  `journey-extracted-confirm.sh` (task E5) promotes only `CONFIRMED`
  entries, and only when `grade` is `[C]` and the oracle is real (no
  `oracle_gap:`) — see spec §4.3.
- `REJECTED` — a human reviewer decided the candidate does not describe a
  real journey. A `REJECTED` entry additionally REQUIRES a
  `rejected_reason:` line with a non-empty value
  (`REJECTED_REASON_MISSING` otherwise) — a rejection with no stated reason
  loses the debt-tracking value of having reviewed it at all. REJECTED is
  terminal (spec §6): there is no flip-back. A wrongly rejected entry is
  recovered by **deleting the REJECTED entry by hand, then re-staging** —
  the still-present candidate returns as a NEW entry. The stage runner
  enforces that ordering deliberately: re-staging a candidate whose
  normalized key still matches the REJECTED sibling fails loud with
  `REJECTED_KEY_COLLISION` (§10.7) instead of silently skipping it — spec
  §6's "deliberate friction": the human must consciously delete the
  rejection record before the candidate can come back.

### 4.3 `grade:` (Step 0 vocabulary, entry-level)

Single-line field, exactly one of `[C] | [I] | [G] | [X]` (`GRADE_UNKNOWN`
otherwise) — the literal bracketed Step 0 grade tokens: Confirmed,
Incomplete, Guessed, conflicting/Cross-source (`[X]`). Only a `[C]`-graded,
`CONFIRMED` entry is promotable (task E5's job to enforce at promotion —
this lint validates the token's membership in the enum only).

### 4.4 `origin:` and `author_status:` — restricted in this file only

- `origin:` — the ONLY allowed value is `EXTRACTED` (`BAD_ORIGIN: <id>:
  <value>` otherwise, guarded on non-blank so an absent value is reported
  once, via `MISSING_FIELD`, not twice).
- `author_status:` — the ONLY allowed value is `UNWRITTEN`
  (`BAD_AUTHOR_STATUS: <id>: <value>` otherwise, same guard). A
  pre-confirmation candidate never has a test written against it — B3 again:
  extraction proves what code does, never that it has been validated.

### 4.5 `oracle:` / `oracle_gap:` — EXACTLY ONE (spec §9.4, review L5)

Every entry carries EXACTLY ONE of `oracle:` (a real outside-in success
signal) or `oracle_gap:` (the question a human must answer when no oracle
is derivable from the cited evidence). Neither present, or both present, is
`ORACLE_EXACTLY_ONE`. When exactly `oracle:` is present, its value must be
non-blank (`BLANK_FIELD: <id>: oracle` otherwise — reusing the generic
blank-field code, since once we know `oracle:` is the chosen field it
behaves like any other required-nonblank field). When exactly `oracle_gap:`
is present, its value must be non-blank (`ORACLE_GAP_FORMAT: <id>`
otherwise — a blank `oracle_gap:` states no question at all, defeating its
entire purpose: "recorded, never guessed").

`lint-journey-extracted.sh` accepts the `oracle_gap:` form in staging; the
confirm gate (E5) refuses to promote any entry still carrying one
(`ORACLE_GAP_UNRESOLVED`) until a human supplies a real `oracle:`.

### 4.6 `extraction_sources:` — provenance block (I1, I9)

Block field (2-space-indented entries, same shape as `steps:` /
`preconditions:` elsewhere in this framework):

```
extraction_sources:
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', ...)"
  - docs/FLW.md#Invoice resubmission
  - search: grep -rFn -- "sendEmail" src/routes/invoices.ts
```

Three line grammars, all fixed-string safe (I9 — the citer must disambiguate
with a line-cite rather than rely on a regex-interpolated heading match; see
`check-extracted-provenance.sh`, task E2, for the byte-verification this
lint does NOT perform):

- **code-cite**: `  - <path>:<line> — "<verbatim quote>"` — grammar
  `^  - [A-Za-z0-9._/-]+:[0-9]+ — ".+"$`. `<path>` may not start with `/`
  and may not contain a `..` segment.
- **section-cite**: `  - <path>#<heading>` — grammar
  `^  - [A-Za-z0-9._/-]+#[^#]+$`. Same path restriction; `<heading>` is
  free text. A heading containing a literal `"` is rejected as
  `SOURCE_FORMAT` with a dedicated message ("looks like a hybrid cite —
  use a line-cite", DX-1/DX-5 live-characterization fix wave) — a model
  gluing a quote onto a `#heading` reference formally still matches this
  grammar (the heading is free text) but can never match a real ATX
  heading, so it is caught here instead of surfacing as a confusing
  `SECTION_HEADING_MISSING` at the provenance gate.
- **search-cite** (DX-1, live-characterization fix wave): `  - search:
  grep -rFn -- "<literal>" <relpath>` — grammar `^  - search: grep -rFn
  -- "[^"\\]+" [A-Za-z0-9._/-]+$`. Reuses
  `journey/docs/uat-report-format.md` §2.2's own restricted search-line
  grammar verbatim: `<literal>` is a non-empty fixed string with no `"`
  or backslash inside it (matched `grep -F`); `<relpath>` is
  repo-relative (no leading `/`, no `..` segment; `.` is legal and means
  the whole repo root — the W3 lesson). This is the ONLY legal form for
  absence evidence (evidence_rules #2's `[C-absent]` law, and the `[X]`
  two-sided rule below both require it) — never freeform prose
  describing what was searched. A search-cite counts toward this
  section's cardinality rules identically to a code-cite or section-cite
  — an `[X]` entry's code side is legitimately a search-cite.
  RATIFIED SEMANTICS (owner, 2026-07-12): zero hits prove only the
  BOUNDED absence claim — that literal, that path, that commit — never
  broader semantic truth. An entry whose sources are ALL search-cites
  (an all-absence `[X]`) may exist in staging but remains non-promotable
  while graded `[X]` (`GRADE_NOT_C`): human adjudication must explicitly
  resolve and re-grade it before promotion — the human confirm is the
  only semantic guard against a one-sided `[X]` built from two absences.

A line matching none of the three grammars is `SOURCE_FORMAT: <id>: <line>`.

**Cardinality** (`SOURCES_MISSING: <id>` unless stated):

- At least 1 `extraction_sources` line is required on EVERY entry — zero
  lines (including the field being entirely absent) is `SOURCES_MISSING`.
  I1: no citation, no entry.
- At least 2 lines are required when `grade:` is `[X]` — a conflicting/
  cross-source entry MUST show both sides, or it is `X_ONE_SIDED` (a
  distinct code from `SOURCES_MISSING`, naming the specific "grade [X]
  entries are structurally required to be two-sided" rule, spec §9.1).
- At least 2 lines are ALSO required whenever a `resolution:` line is
  present (§4.7/§4.8 below, locks 2/3) — reported via `SOURCES_MISSING`
  (the same code as the base ≥1 rule; the message states which threshold
  was missed). Rationale: a human resolution must not be allowed to delete
  the disagreement evidence it resolved — the historical two-sided record
  survives the edit.

### 4.7 `prior_e2e:` — staging-only, never promoted (spec §9.3, review M1)

OPTIONAL single-line field: the relative path of a pre-existing E2E test
that already covers this candidate journey, when Stage 4b's manifest names
one. Grammar: no leading `/`, no `..` segment
(`^[A-Za-z0-9._/-]+$`) — `PRIOR_E2E_FORMAT` otherwise (also fires on a
present-but-blank value). Absence is always legal.

**Why this is staging-only and never reaches the map**: the blind author
reads `JOURNEY_MAP.md`'s `evidence:` field to decide what to write, never
this file. A readable test path in the map's `evidence:` would hand the
blind pipeline the exact behavior encoding for precisely the journeys most
likely to already have one — laundering non-blind knowledge through the
blindness invariant (I4, Lock 4). The confirm gate (task E5) forces
`evidence: []` on every promoted entry unconditionally; `prior_e2e:` is one
of the fields that never survives promotion (§5 below).

### 4.8 `resolution:` and `resolved_from:` — grade-history preservation (spec §14 locks 2/3)

An `[X]`-graded (disagreement) entry, or an `[I]`/`[G]`-graded (incomplete/
guessed) entry, is never promoted AS THAT GRADE. A human resolves it by
editing the entry into a new `[C]` state — but the history of what it was
resolved FROM must survive the edit, not be silently overwritten:

```
resolution:    the code path in src/routes/invoices.ts is current; the
               conflicting doc (docs/FLW.md#Invoice resubmission, cited
               above) describes a route removed in commit a1b2c3d — code
               wins per Step 0 staleness rules
resolved_from: [X]
grade:         [C]
confirmation_status: CONFIRMED
```

- `resolution:` present without `resolved_from:` is `RESOLVED_FROM_MISSING`.
- `resolved_from:` present without `resolution:` is `RESOLVED_FROM_MISSING`
  (same code — a lone `resolved_from:` with no accompanying explanation is
  exactly as broken as a lone `resolution:` with no history marker; there is
  no legitimate reason to carry one field without the other).
- `resolved_from:` present but not one of `[X] | [G] | [I]` is also
  `RESOLVED_FROM_MISSING` (a bad token is folded into the same code — there
  is no separate enum-violation code for this field).
- Both present and well-formed: no violation from this check. §4.6's
  `SOURCES_MISSING` (≥2) rule still applies whenever `resolution:` is
  present, regardless of which grade it was resolved from.

**The oracle-gap-repair shape** (spec §6, `PENDING/oracle_gap ──human
supplies oracle──▶ [C]+CONFIRMED`): when a human resolves an `oracle_gap:`
entry by supplying a real `oracle:`, the SAME `resolution:` +
`resolved_from:` mechanism applies — `resolved_from:` in this case is
whichever grade the entry carried before resolution (commonly `[I]` or
`[G]`, since an ungroundable oracle is itself a form of incompleteness), and
the `resolution:` line's text MUST carry the original gap question (not
just the new answer) so a later reader can see what was asked and how it
was answered, e.g.:

```
resolution:    original question: "what does a successful resubmission
               return to the caller?" — confirmed via
               src/routes/invoices.ts:58, a 200 with the updated row
resolved_from: [I]
```

This shape (retaining the original question inside `resolution:`) is a
documentation convention, not a separately lint-checked grammar — whether a
`resolution:` line actually preserves the original question is exactly the
kind of judgment the human-authority seam (§9.1 below) states the lint
cannot verify.

**Note on scope**: whether a human's `resolution:` reflects *sound
judgment* is not lint-checkable (spec §7.1's seam note, review L1) — this
lint enforces only that a resolution retains its structural history marker
and its two-sided provenance. The judgment itself is out of scope for any
gate; §9.1 states this explicitly.

### 4.9 `promoted_as:` (optional, gate-written — never author this by hand)

After `journey-extracted-confirm.sh` (task E5) promotes a `CONFIRMED`
entry, it stamps a `promoted_as: JOURNEY-<n>` line onto that entry — an
audit trail naming the id the candidate became in `JOURNEY_MAP.md`, and
marking the entry terminal for promotion purposes (spec §14 Q7: re-staging
still re-verifies a terminal entry's citations; only re-PROMOTION is
skipped).

- The value must match `^JOURNEY-[0-9]+$`, or `PROMOTED_AS_INVALID: <id>:
  <value>` (malformed).
- The entry's `confirmation_status` (read via the SAME first-match
  accessor as every other `confirmation_status` check in this lint, §6
  below) must be exactly `CONFIRMED`, or `PROMOTED_AS_INVALID: <id>:
  promoted_as present but confirmation_status is <value> (must be
  CONFIRMED)`. A `promoted_as` line on a `PENDING` or `REJECTED` entry is
  nonsensical — nothing was promoted.

### 4.10 Runtime truth is never staged here

Same law as `JOURNEY_MAP.md` and `JOURNEY_INBOX.md`: `ci_status`,
`last_run`, `ci_run_id`, `ci_artifact`, `failure_summary` never appear in
this file. Any of the five runtime-field keys anywhere in the file is
rejected as `RUNTIME_FIELD` — the same code name (and the same five-key
list) `check-journey-authority.sh`, `lint-journey-map.sh`,
`lint-journey-inbox.sh`, and `lint-journey-tests.sh` all use for this exact
class of violation.

---

## 5. What a confirmed entry copies to the map (informative — E5's job)

Documented here for context; enforced by `journey-extracted-confirm.sh`
(task E5), not by this lint. On promotion: `origin: EXTRACTED` and
`author_status: UNWRITTEN` are forced (already required exactly those
values in staging, so this is a no-op in practice); `evidence:` is forced
to `[]` unconditionally (Lock 4) regardless of what the staging entry
carried. Staging-only fields — `needs_human_confirm`, `confirmation_status`,
`grade`, `extraction_sources`, `prior_e2e`, `resolution`, `resolved_from`,
`rejected_reason` — are NEVER copied to the map. Every other field
(`persona`, `goal`, `priority`, `covers`, `flows`, `oracle_surface`,
`negative_states`, `steps`, `oracle`, `runner`) lands unchanged; `test:`
also copies, but its `<n>` placeholder is substituted with the assigned
numeric id at promotion — it does not land byte-identical. Promotion
also injects two fields no staging entry ever carries: `data_fixtures:
[]` and `exemptions: []`. Normative details: §11.7.

---

## 6. `lint-journey-extracted.sh <path>` — the gate

POSIX `sh` against stock `/bin/sh`, fail-closed, `CODE: message` on stderr,
non-zero exit on any violation. All violations are accumulated before
exiting (fail-slow, never fail-fast) via `for`/heredoc-`while` — never
`| while read` (a pipeline subshell loses counter mutations; a known
fail-open class in this framework, house rule 2). Success prints nothing
and exits 0.

Parsing reuses the identical block-extraction idiom `lint-journey-map.sh`
and `lint-journey-inbox.sh` use, via three new shared accessors added to
`journey/lib/journey-lib.sh`: `extracted_ids` / `extracted_block` /
`extracted_field`, siblings of that file's `journey_ids`/`inbox_ids` etc.
(same awk, different heading prefix `## EXTRACTED-<n>`, different default
file variable `JOURNEY_EXTRACTED`). Every gate that reads this file uses
the SAME first-match `extracted_field` accessor (L11 discipline) — never a
raw `grep` over a block — so a `confirmation_status:` line duplicated
within one entry (e.g. `PENDING` first, `CONFIRMED` second, a paste error)
is classified consistently by its FIRST occurrence everywhere, including a
future promotion gate; there is no code path where the lint and the
promoter could read two different values for the same field on the same
entry.

Usage error or missing file: exit 2 (matches `lint-journey-map.sh` /
`lint-journey-inbox.sh`). Schema violations: exit 1.

### 6.1 Closed code list (25 codes, append-only forever — spec §7.1/§14)

File-level:

- `BAD_HEADER` — first line is not exactly `# JOURNEY-EXTRACTED`.
- `EXTRACTION_COMMIT_INVALID` — `extraction_commit:` header value is not
  exactly 40 lowercase hex characters.
- `MANIFEST_SHA_INVALID` — `manifest_sha256:` header value is not exactly
  64 lowercase hex characters.
- `FORBIDDEN_JOURNEY_HEADER` — literal `## JOURNEY-` found anywhere.
- `RUNTIME_FIELD` — a runtime-truth field key found anywhere.
- `DUPLICATE_EXTRACTED_ID` — an `EXTRACTED-<n>` id appears more than once.
- `BAD_EXTRACTED_ID` — an `EXTRACTED-<n>` id is not a positive integer
  (zero).
- `NO_EXTRACTED_ENTRIES` — anti-vacuous: a valid header but zero entries.

Per-entry:

- `ENTRY_HEADING_INVALID` — heading is not the canonical
  `## EXTRACTED-<digits> — "<title>"` form (checked up front, §3.2, L23).
- `NEEDS_CONFIRM_INVALID` — `needs_human_confirm` missing, or present but
  not exactly `true`.
- `CONFIRM_STATUS_INVALID` — `confirmation_status` present but not one of
  `PENDING | CONFIRMED | REJECTED`.
- `REJECTED_REASON_MISSING` — `confirmation_status: REJECTED` with no
  non-blank `rejected_reason:`.
- `GRADE_UNKNOWN` — `grade` present but not one of `[C] | [I] | [G] | [X]`.
- `MISSING_FIELD: <id>: <field>` — a required field key is absent.
- `BLANK_FIELD: <id>: <field>` — a required-nonblank field's value is
  blank.
- `BAD_ORIGIN: <id>: <value>` — `origin` present but not exactly
  `EXTRACTED`.
- `BAD_AUTHOR_STATUS: <id>: <value>` — `author_status` present but not
  exactly `UNWRITTEN`.
- `SOURCES_MISSING: <id>` — fewer than the required number of
  `extraction_sources` lines (≥1 always; ≥2 when `grade` is `[X]` or a
  `resolution:` line is present).
- `SOURCE_FORMAT: <id>: <line>` — an `extraction_sources` entry line
  matches none of the code-cite, section-cite, or search-cite grammar
  (also fires, with a dedicated message, on a section-cite whose heading
  contains a literal `"` — a hybrid line-cite/section-cite paste, DX-5
  live-characterization fix wave).
- `X_ONE_SIDED: <id>` — `grade: [X]` with fewer than 2 `extraction_sources`
  lines (a distinct code from `SOURCES_MISSING`, naming the two-sided-proof
  requirement specifically).
- `ORACLE_EXACTLY_ONE: <id>` — neither, or both, of `oracle:`/`oracle_gap:`
  present.
- `ORACLE_GAP_FORMAT: <id>` — `oracle_gap:` present but its value is blank.
- `PROMOTED_AS_INVALID: <id>: <value>` — `promoted_as:` malformed, or
  present on a non-`CONFIRMED` entry.
- `PRIOR_E2E_FORMAT: <id>: <value>` — `prior_e2e:` present but blank, or
  its value starts with `/` or contains a `..` segment.
- `RESOLVED_FROM_MISSING: <id>` — `resolution:` without `resolved_from:`,
  `resolved_from:` without `resolution:`, or `resolved_from:` present but
  not one of `[X] | [G] | [I]`.

That is 25 codes total (8 file-level + 17 per-entry).

### 6.2 What this gate deliberately does not check

- The map-inherited enum fields (`priority`, `oracle_surface`, `runner`,
  ...) are checked for presence/non-blankness only, never for membership in
  their allowed value sets — re-validated once at promotion, via the
  composed `lint-journey-map.sh` (same precedent as `journey-inbox-format.md`
  §4.2).
- The FEAT-grammar/existence enforcement on `covers:` (spec §14 Q6,
  `COVERS_UNKNOWN_FEAT`/`COVERS_DUPLICATE`) is the confirm gate's job (task
  E5), not this lint's — a staging candidate may legitimately anchor to a
  manifest SCREEN id before a human re-anchors it to a FEAT id.
- Byte-verification of `extraction_sources` citations against the pinned
  `extraction_commit` (I1, I9) is `check-extracted-provenance.sh`'s job
  (task E2) — this lint validates citation GRAMMAR only, never reads the
  working tree or any git history.
- MANIFEST chain / staleness checks (I5, B5) are
  `check-extraction-coverage.sh`'s job (task E3).
- Whether a human's `resolution:` reflects sound judgment (§4.8, §9.1) is
  never lint-checkable — the human-authority seam, stated explicitly here
  so no future gate mistakes silence for a green light on content it cannot
  see.

---

## 7. The human-resolution seam (spec §9.1)

Sources disagreeing, an oracle being ungroundable from cited evidence, or a
grade sitting at `[I]`/`[G]` with no `[C]`-worthy citation yet, are all
DEGENERATE INPUT STATES this framework defines explicitly rather than
silently papering over (spec §9, I10):

1. **Disagreement** (`[X]`) — a human resolves by editing the entry to the
   chosen truth, adding `resolution:` + `resolved_from: [X]` (§4.8), and
   re-grading `[C]`. The lint cannot verify the human judged well; it can
   only verify the historical record — both sides' provenance — survived
   the edit (`SOURCES_MISSING` ≥2 whenever `resolution:` is present).
2. **Ungroundable oracle** (`oracle_gap:`) — a human supplies a real
   `oracle:`, following the same `resolution:`/`resolved_from:` mechanism
   when the entry's prior grade was `[I]`/`[G]`/`[X]` (§4.8's "oracle-gap-
   repair shape").
3. **`[I]`/`[G]` with no upgrade possible** — the entry is *recorded, never
   promoted*: it stays in staging as audit and surfaces in
   `EXTRACTED_GAPS.md` (a later task) as a Step-1 question. `GRADE_UNKNOWN`
   is not the relevant backstop here — `[I]`/`[G]` are valid, lint-clean
   grades; `GRADE_NOT_C` (a confirm-gate code, task E5) is the intended,
   permanent backstop preventing promotion of anything less than `[C]`.

No gate in this contract — including this lint — adjudicates whether a
human's editorial judgment was correct. That is deliberate: the same
framework-wide principle that a UAT report's narrative carries no authority
(`journey-inbox-format.md` §2, `uat-report-format.md` §1) applies here to a
human's `resolution:` text. What IS enforced, always, mechanically: the
BEFORE state (the disagreement, the gap, the incompleteness) is never
silently erased by the AFTER state (the resolution) — it survives as
citable history.

---

## 8. `check-extracted-provenance.sh EXTRACTED REPO_ROOT` — the provenance gate (task E2, spec §4.3/§7.2)

Where §6's lint proves the staging file is well-FORMED, this gate proves its
`extraction_sources:` citations are well-FOUNDED — that every quoted line
and every cited heading actually exists at the pinned `extraction_commit`,
for every entry in the file, byte-verified, never trusting the working
tree.

**Composition.** This gate composes `lint-journey-extracted.sh` FIRST, as an
executable (never reimplemented) — grammar (`SOURCE_FORMAT`,
`ENTRY_HEADING_INVALID`, ...) is that gate's job; a non-zero lint exit is
reported as `LINT_FAILED` and this gate stops. **`LINT_FAILED` is not one of
spec §7.2's enum members** — it is the same house composition-idiom
pass-through code `check-uat-preconditions.sh` uses for
`lint-journey-map.sh` (precedent, not a new schema code).

**What it verifies, for EVERY `## EXTRACTED-<n>` entry — including
`confirmation_status: REJECTED` and `promoted_as:`-stamped (terminal)
entries (spec §14 Q7: re-staging still re-verifies a terminal entry's
citations; only re-PROMOTION is skipped) — and EVERY
`extraction_sources:` line on it:**

- **code-cite** (`  - <path>:<line> — "<quote>"`): byte-verified by REUSING
  `journey/lib/uat-lib.sh`'s pinned-commit quote checker
  (`uat_check_quote_line`) unchanged. The staging-file line is adapted into
  the shape that checker expects (its `"  - "` prefix swapped for
  `uat-lib.sh`'s `"- evidence: "` prefix — both grammars share the identical
  `<path>:<line> — "<quote>"` tail) and handed to the checker as-is; the
  byte verification itself still runs entirely inside `uat-lib.sh`, so this
  gate and `check-uat-evidence.sh` can never disagree about what counts as
  a verified quote. `QUOTE_UNVERIFIED` (not found anywhere in the file at
  the pinned commit) and `LINE_MISMATCH` (found, but not at the cited line)
  are `uat-lib.sh`'s own distinct codes, unchanged.
- **section-cite** (`  - <path>#<heading>`): the cited file must exist at
  the pinned commit (`SECTION_FILE_MISSING` otherwise); its heading lines —
  ATX `#` lines OUTSIDE fenced code blocks (``` or ~~~); fence-aware by
  construction, so a `#` line inside a fence is code, never a heading
  (V-E2 F1) — are stripped of leading `#`s + whitespace and matched
  against the cited heading text via `grep -Fx` — FIXED-STRING, whole-line,
  case-sensitive equality, **never a regex or ERE** (spec I9/§5; the same
  injection discipline L22 names for id tokens —
  `.superpowers/sdd/sim-reality-progress.md` L22 — applied here to a
  heading, which is free text an operator or model fully controls). Zero
  matches -> `SECTION_HEADING_MISSING`; two or more -> `SECTION_AMBIGUOUS`
  (fail closed; the citer must disambiguate with a line-cite instead).
  Known simplification: fence LENGTH is not matched — a 4+-tick fence
  embedding 3-tick lines is mis-tracked; ruled residual (V-E2).
- **search-cite** (`  - search: grep -rFn -- "<literal>" <relpath>`,
  DX-1, live-characterization fix wave — the absence-evidence form):
  byte-verified by REUSING `journey/lib/uat-lib.sh`'s pinned-commit
  search checker (`uat_check_search_line`) unchanged, called with
  `expect="zero"`. The staging-file line is adapted the same way the
  code-cite line above is (its `"  - "` prefix swapped for a bare `"- "`
  prefix — both grammars share the identical `search: grep -rFn --
  "<literal>" <relpath>` tail), and the re-execution itself (including
  the `.`-relpath root-tree special case) runs entirely inside
  `uat-lib.sh`. `<relpath>` must exist at the pinned commit
  (`SEARCH_ERROR` otherwise, or on a `git grep` internal error); the
  literal is then re-run as `git grep -Fn` against that commit — ANY hit
  is `SEARCH_DIVERGED` (an absence cite that finds something is wrong by
  construction — same name/semantics as the UAT layer's own evidence and
  verification gates). This is the fix for the RATIFIED spec's C1-class
  false premise: §5's original grammar admitted no absence-cite form at
  all, while evidence_rules #2 and the `[X]` two-sided law both require
  one — an honest model could not comply (see the spec §5 amendment
  note). Never reimplemented; both `check-uat-evidence.sh` and this gate
  call the identical `uat-lib.sh` function.
- **`prior_e2e:`** (optional, staging-only, spec §9.3): verified for
  existence-at-commit only (it claims a discovered test file, not a quote
  or a heading).

**All reads are pinned to `extraction_commit`** — `git show`/`git cat-file`
against that one commit, exactly like `check-uat-evidence.sh`. The working
tree is never read; editing a cited file in the working tree after the
commit that citation is pinned to cannot silently invalidate or fake a
citation (the same D2-class guarantee this framework applies everywhere a
commit is pinned).

### 8.1 Four additions to spec §7.2's drafted enum (append-only, closed forever)

Spec §7.2's draft (`COMMIT_UNKNOWN QUOTE_UNVERIFIED LINE_MISMATCH
SECTION_FILE_MISSING SECTION_HEADING_MISSING SECTION_AMBIGUOUS TOOL_MISSING
MKTEMP_FAILED`) predates four things that turned out to need their own
codes. All four are appended here, append-only, never replacing or
renumbering anything (the same append-only law spec §7's header states for
every enum in this framework):

- **`PRIOR_E2E_MISSING: <id>: <path>`** — the draft enum predates
  `prior_e2e:` existing in the entry grammar at all (it was added later,
  §4.2/§9.3 of this doc). A missing `prior_e2e:` path is not a citation-
  cardinality problem (`SOURCES_MISSING`'s shape) and not a quote problem
  (`QUOTE_UNVERIFIED`'s shape) — it is a bare path-existence claim, so it
  gets its own code.
- **`NO_SOURCE_LINES`** — an anti-vacuous backstop: zero total
  `extraction_sources` lines across the WHOLE file. Unreachable through
  normal composition (the composed lint's own `SOURCES_MISSING` demands
  >=1 line per entry, and `NO_EXTRACTED_ENTRIES` demands >=1 entry, so a
  lint-clean file always has >=1 total source line) — but if the lint
  composition were ever bypassed, this gate must still refuse to pass
  vacuously rather than silently report "0 entries, 0 citations, OK".
  Exercised directly in the test suite via an honest, documented bypass of
  the lint composition step (a stub `lint-journey-extracted.sh` that always
  exits 0, in an isolated copy of the gate — not a production escape
  hatch; the real gate has no such flag).
- **`SEARCH_DIVERGED: <id>: "<literal>" found in <relpath>`** (DX-1,
  live-characterization fix wave) — a search-cite's literal WAS found at
  the pinned commit: an absence claim that is not, in fact, absent.
  `uat-lib.sh`'s own code, unchanged, reused here for the identical
  meaning.
- **`SEARCH_ERROR: <id>: ...`** (DX-1, live-characterization fix wave) —
  a search-cite's `<relpath>` does not exist at the pinned commit, or the
  re-executed `git grep` itself errored. `uat-lib.sh`'s own code,
  unchanged, reused here for the identical meaning.

### 8.2 Closed code list (13 codes total)

`LINT_FAILED` (composition pass-through, not a schema code) `COMMIT_UNKNOWN`
`QUOTE_UNVERIFIED` `LINE_MISMATCH` `SEARCH_DIVERGED` `SEARCH_ERROR`
`SECTION_FILE_MISSING` `SECTION_HEADING_MISSING` `SECTION_AMBIGUOUS`
`PRIOR_E2E_MISSING` `NO_SOURCE_LINES` `TOOL_MISSING` (git not found on
PATH) `MKTEMP_FAILED` (the fail-slow accumulator itself could not be
created — mirrors `check-uat-evidence.sh`'s M-T1-4 guard).

Usage error, missing `EXTRACTED` file, or missing `REPO_ROOT` directory:
exit 2. Any violation: exit 1, fail-slow accumulation (never `| while
read`, house rule 2). Success: one `OK: <n> entries, <n> code-cite(s), <n>
section-cite(s), <n> search-cite(s), <n> prior_e2e checked` summary line,
exit 0.

---

## 9. `check-extraction-coverage.sh MANIFEST EXTRACTED [GAPS]` — the manifest consumer chain (task E3, spec §4.3/§7.3/§8, §14 Q3)

Where §6's lint proves the staging file is well-FORMED and §8's provenance
gate proves its citations are well-FOUNDED, this gate proves the staging
file is well-ACCOUNTED FOR against the one artifact neither of those gates
ever reads: Step 0's `MANIFEST.md` machine block (spec §4.1). Coverage is
accounting, not fidelity (doc-derived lesson, restated here): this gate
never judges whether a staged candidate is a *good* reverse-engineering of
a journey — that is the human confirmation step's job (a later task, E5).
RATIFIED SCOPE (owner, 2026-07-12): transitive screen credit through a
shared AFJ token is coverage ACCOUNTING only — it must never be
represented as direct extraction evidence, direct screen validation, or
runtime proof.
It only proves that every behavior-bearing FEAT and every flow-bearing
screen the manifest declares is accounted for by at least one staged
candidate or an explicit, expiring gap — and that the staging file's own
claims never point at an anchor the manifest doesn't recognize.

### 9.1 Composition

Composes `lint-journey-extracted.sh EXTRACTED` FIRST, as an executable
(never reimplemented) — grammar is that gate's job. A non-zero lint exit
is reported as `LINT_FAILED` and this gate stops. `LINT_FAILED` is not one
of spec §7.3's enum members — the same house composition-idiom
pass-through code `check-uat-preconditions.sh` and
`check-extracted-provenance.sh` (task E2) both use.

### 9.2 The chain: four fail-closed stages, in order (spec §8)

Each stage is a hard gate over the one before it. A stage that finds any
violation accumulates ALL of that stage's violations (fail-slow WITHIN the
stage — never `| while read`, house rule 2) and then halts the run; a
later stage never runs against data an earlier stage has already proven
untrustworthy. This is deliberately NOT one flat fail-slow pass across the
whole gate — stage 2's duplicate/commit checks are meaningless over a
block stage 1 couldn't even parse, and stage 4's completeness accounting
is meaningless over a manifest stage 3 has already proven stale.

**Stage 1 — parse.** `MANIFEST` must exist as a file
(`MANIFEST_MISSING` — a CHAIN code, exit 1, deliberately **not** the same
exit-2 class as a missing `EXTRACTED`/`GAPS` path below: a brand-new
project legitimately has no `MANIFEST.md` yet, and the chain names that as
its own deterministic state, not a caller mistake) and must carry a
well-formed `EXTRACTION-MANIFEST BEGIN`/`END` block
(`MANIFEST_BLOCK_MISSING` otherwise) — **exactly one** such block. Block
cardinality is counted BEFORE anything is extracted: a manifest with more
than one complete `BEGIN`/`END` pair, or with stray surplus delimiter
lines (a surplus `BEGIN` is a second, unclosed block whose content would
escape accounting), is `MANIFEST_BLOCK_AMBIGUOUS: <n> blocks found
(exactly one required; ...)`. This code is an append-only addition to spec
§7.3's drafted enum (documented per the same precedent as task E2's two
additions and this gate's own `NO_GAP_ENTRIES`): §8's prose names the
"ambiguous" fail-closed class explicitly, but the draft enum assigned it
no code — without one, a first-`END`-wins extractor silently parses only
block 1 and block 2's behavior-bearing anchors escape the completeness
accounting entirely at exit 0 (V-E3 F1). Every non-blank line inside the
block (the two delimiter lines themselves are never validated as content)
must match the fixed grammar — exactly one `manifest_version: <value>`
line, exactly one `extraction_commit: <40-hex>` line, and any number of
`feat:` / `screen:` / `e2e_test:` lines, each **pipe-delimited with FIXED
keys** (never a freeform key set):

```
manifest_version: 1
extraction_commit: <40-hex sha of the audited repo>
feat:     <id> | behaviors=<int> | states_filled=<int> | grade_counts=<value>
screen:   <id> | route=<value> [| flows=<value>]
e2e_test: <path> | framework=<value>
```

Every VALUE matches `^[A-Za-z0-9._/:=,-]+$` (spec §4.1, character-exact) —
no whitespace, no `|` inside a value, no quoting/escaping mechanism.
`behaviors=`/`states_filled=` are additionally constrained to `[0-9]+`
(needed for the `>=1` completeness comparison in stage 4 to be
well-defined — still the same `MANIFEST_FORMAT` code, not a new one).
`screen:`'s `flows=` segment is the ONE optional pipe-field in the whole
grammar — a screen with no declared flows simply omits it (a 2-field
`screen: <id> | route=<value>` line is legal); this is how a
BACKEND_ONLY screen with no user-journey flows is represented, and it is
also what makes that screen NOT a required completeness anchor in stage 4
(§9.4 below). Any line matching none of these shapes, and any header key
appearing zero times or more than once, is `MANIFEST_FORMAT: <line>` — one
message per offending line, fail-slow within this stage.

Values are **never interpolated into a regex or ERE** (L22 —
`.superpowers/sdd/sim-reality-progress.md`): every grammar pattern above is
a STATIC, author-written ERE checked against the whole line via `grep -qE`;
field EXTRACTION (getting the id/behaviors/flows value back out of an
already-shape-validated line) is done by literal-string field splitting on
`" | "` (an escaped-pipe awk regex literal, `/ \| /` — the task's own
guidance: "parse by field splitting on ` | ` and fixed-string compares"),
never by feeding a manifest-derived value back into a second regex.

**Stage 2 — soundness.** No id/path may repeat within the block:
`MANIFEST_DUPLICATE: feat <id> ...` / `screen <id> ...` / `e2e_test <path>
...` (one message per duplicate, fail-slow). Nor may a token appear in
MORE THAN ONE namespace: an id byte-identical as both a `feat:` id and a
`screen:` id (or either and an `e2e_test:` path) is also
`MANIFEST_DUPLICATE`, with its own cross-namespace message (V-E3 F3) —
without this check, one staging `covers:` token would credit TWO required
anchors at once, a one-token-two-credits accounting fail-open. Each kind's
id list is deduplicated before the cross-namespace comparison, so an
intra-kind duplicate reports once under its own message, never twice. The
block's own `extraction_commit:` must equal `EXTRACTED`'s own header
`extraction_commit:` — `MANIFEST_COMMIT_MISMATCH` otherwise (the manifest
this staging file was checked against must be the SAME extraction run the
staging file itself is pinned to; a manifest pinned to a different commit
is not evidence about this staging file at all).

**Stage 3 — freshness.** `EXTRACTED`'s `manifest_sha256:` header must equal
the CURRENT sha256 of the manifest's machine block — the exact bytes from
the `EXTRACTION-MANIFEST BEGIN` line through the `EXTRACTION-MANIFEST END`
line, **inclusive** (the same "sha256 of MANIFEST.md's machine block"
§3.1 defines, not the whole file). A mismatch is `EXTRACTION_STALE`
(message: re-stage); no sha256 tool on `PATH` is `TOOL_MISSING` (fails
closed rather than skipping the freshness check).

**Stage 4 — completeness, both directions (the B5 core).** See §9.3/§9.4.

### 9.3 Direction (a): every staged anchor exists in the manifest

Every entry's `covers:` and `flows:` values are comma-split into individual
tokens (exact-match, **never substring** — Q6's spirit applied here too).

**Whitelist before use (V-E3 F2, L22).** Staging `covers:`/`flows:` values
are free text no earlier gate has constrained — so every token is
whitelisted against `^[A-Za-z0-9._-]+$` BEFORE any membership check runs;
a nonconforming token is `ANCHOR_TOKEN_INVALID: EXTRACTED-<n>: <token>`
and never enters any membership test or credit pool (whitelist-first also
means an invalid token gets its ONE primary code, never a confusing
`UNKNOWN_ANCHOR` on top). The code's name and class are precedented by
`journey/bin/author-bundle.sh`'s identical `ANCHOR_TOKEN_INVALID` from the
T4c ERE-closure wave (L22: any operator/model-supplied token is validated
against a strict whitelist before use, fail closed on non-conforming) —
an append-only addition to spec §7.3's drafted enum, same precedent as the
others in this doc. The token loops additionally run under `set -f`
(pathname expansion disabled): without it, a staging value like
`covers: *` glob-expands against the CALLER'S working directory, and a cwd
file named `FEAT-100` becomes a false coverage credit at exit 0 — the
whitelist catches the `*` regardless, but the `set -f` layer guarantees no
expansion ever happens before the whitelist sees the raw token.

Every `covers:` token must exist in the union of the manifest's `feat:` ids
AND `screen:` ids — staging entries may legitimately still be
screen-anchored pre-confirmation (spec §9.5: FEAT-grammar enforcement is
the confirm gate's job, task E5, not this gate's). Every `flows:` token
must exist in the union of every screen's declared `flows=` values. A
token found in neither pool is `UNKNOWN_ANCHOR: EXTRACTED-<n>: <token>` —
including when the relevant pool is **empty** (e.g. no screen in the whole
manifest declares any `flows=` at all): a nonempty token must still fail
closed against an empty pool, never pass vacuously because there was
nothing to check it against.

`[]` — the field's empty-list literal — is the ONE token string that is
**always** filtered out before this check runs, contributing zero tokens
in either direction (L20: an empty-list sentinel must mean NO anchors,
never a token that could ever match anything).

### 9.4 Direction (b): every manifest anchor is accounted for

The required-anchor set is exactly two subsets of the manifest:

- every `feat:` line with `behaviors>=1`;
- every `screen:` line that DOES declare a `flows=` value (a screen with
  no `flows=` segment at all — §9.2 — is not required to be covered by
  anything; it has nothing for a journey to have exercised).

Each required anchor must be covered by **>=1 staged entry** — checked
across ALL entries regardless of `confirmation_status` (a `REJECTED` or
`promoted_as`-stamped terminal entry still counts as "this anchor was
extraction-attempted"; spec §14 Q7's "terminal entries still
integrity-checked" applies to accounting the same way it applies to
provenance) — OR by a valid, unexpired `EXTRACTED_GAPS.md` entry (§9.5),
only when the optional `GAPS` arg was given. An anchor satisfying neither
is `MISSING_EXTRACTION: <anchor>`. When `GAPS` was never given, gap credit
is simply unavailable — every otherwise-uncovered anchor fails as a plain
`MISSING_EXTRACTION`, and the message says so.

**The flows-membership design (this gate's own reading of spec §4.3's
"covers/flows membership" parenthetical — the design spec leaves the exact
mechanics open, so the ruling is recorded here, not silently assumed):**

- A **FEAT** anchor is covered iff some staged entry's `covers:` set
  contains that FEAT id.
- A **SCREEN** anchor (one that declares `flows=`) is covered via EITHER
  of two paths:
  1. **direct** — some entry's `covers:` set contains the screen's own id
     (the "screen-anchored covers entry credits a screen" case, spec
     §9.5); or
  2. **indirect** — some entry's `flows:` set contains ANY ONE of that
     screen's declared `flows=` tokens (an entry that flows through one of
     a screen's AFJ ids has, by construction, exercised that screen, even
     without ever naming the screen id in its own `covers:`).

Both paths are proven independently in
`journey/tests/check-extraction-coverage_test.sh`'s golden fixture: one
entry credits a screen ONLY via path 1 (no `flows:` token names the
screen's AFJ id at all — proven in isolation by a case that drops every
OTHER entry and shows the screen stays covered); a second entry credits a
DIFFERENT screen ONLY via path 2 (its `covers:` never names that screen's
id — proven by a case that removes exactly this entry and shows the
screen becomes `MISSING_EXTRACTION`, i.e. nothing else was covering it).

### 9.5 `EXTRACTED_GAPS.md` — the gaps artifact (spec §14 Q3, own artifact)

`EXTRACTED_GAPS.md` is a per-project, per-artifact file (sibling of
`JOURNEY_EXTRACTED.md` and `PERSONA_COVERAGE_GAPS.md`) — passed as this
gate's optional third argument by any project that keeps gap entries. It is
**never** `PERSONA_COVERAGE_GAPS.md` and never the doc-derived
`JOURNEY_COVERAGE_GAPS.md`: each coverage gate in this framework owns its
own gaps artifact, never reads another gate's.

**The grammar and the expiry mechanics are INHERITED, byte-for-byte,
from `journey/bin/check-persona-coverage.sh`'s `PERSONA_COVERAGE_GAPS.md`
precedent (spec §14 Q3, binding: "gap expiry inherits PERSONA_COVERAGE_GAPS
exactly... no second duration literal, no EXTRACTED-specific config"):**

```
source_id: FEAT-020
source_type: FEAT | SCREEN
reason: <non-empty>
owner: <non-empty>
reviewer: <non-empty>
expires: YYYY-MM-DD
```

Records are parsed with the SAME `source_id:`-triggered group-emit `awk`
idiom `check-persona-coverage.sh` uses (a new record begins at each
`source_id:` line; the previous record is flushed first). `expires:` is
compared to today via the IDENTICAL string comparison
(`[ "$_gex" \< "$_today" ]` — `YYYY-MM-DD` sorts lexically as a string, no
date-arithmetic tool needed) — no second duration constant exists anywhere
in this gate, and none may ever be added without a spec amendment.

**The one deliberate widening**: `source_type` accepts `FEAT` **or**
`SCREEN` (the persona precedent hardcodes `FEAT` only, because persona
coverage only ever gaps FEATs). This gate's required-anchor set spans both
feat and flow-bearing-screen anchors (§9.4), so the enum is widened to
match — the parsing idiom, the date-comparison mechanics, and every other
rule are otherwise unchanged.

- Malformed (bad `source_type`, a blank `reason`/`owner`/`reviewer`, or an
  `expires:` value not shaped `YYYY-MM-DD`) is `GAP_FORMAT: gap <id> ...`.
- Well-formed but `expires:` before today is `GAP_EXPIRED: gap <id> expired
  <date> (today: <date>) — an expired gap is not a coverage credit` — same
  wording, same semantics as `PERSONA_COVERAGE_GAP`'s `GAP_EXPIRED`.
- A `GAPS` path that was explicitly GIVEN but declares **zero** gap
  records is its own loud failure: `NO_GAP_ENTRIES`.

**`NO_GAP_ENTRIES` — one append to spec §7.3's drafted enum, append-only,
documented here per the same precedent task E2 set for its own two
additions (`PRIOR_E2E_MISSING`/`NO_SOURCE_LINES`) to spec §7.2's draft:**
unlike `check-persona-coverage.sh` (where a *missing* gaps file silently
means zero gaps — a project that has never needed a persona gap never has
to create the file), this gate's `GAPS` arg is OPTIONAL and its presence is
itself a project's deliberate declaration: "I keep gap entries here". A
file that EXISTS, was explicitly PASSED, and carries zero entries is
indistinguishable from a forgotten or emptied file — the same
anti-vacuous shape as an empty `JOURNEY_EXTRACTED.md`
(`NO_EXTRACTED_ENTRIES`) or a zero-anchor PRD/SSOT (`NO_ANCHORS`): a loud
failure, not a silent "0 gaps, nothing to check" pass. When the `GAPS` arg
is omitted entirely, this code never fires at all — omission and
emptiness are different, deliberately: omission means "this project does
not use gaps", emptiness-while-declared means "something is wrong with the
file this project said it uses".

**Forward pointer (Q3's clock rule — enforcement is a LATER task's duty,
not this gate's):** a gap entry's `expires:` date is set at the entry's
FIRST successful staging and MUST survive re-staging unchanged — manifest
edits, re-verification, and formatting changes never reset it (spec §14
Q3, binding). This gate only READS and COMPARES whatever `expires:` value
is present at run time; it has no write path and cannot enforce that the
date was never rewritten. Enforcing survival-across-re-staging is
`journey-extracted-stage.sh`'s job (task E4, the stage runner — **§10
below**) — noted here as the explicit forward pointer so a future
implementer does not mistake this gate's silence on the point for the
rule not existing. §10.4 restates this from the runner's side: because
`EXTRACTED_GAPS.md` is human-authored and this runner never writes it, the
`expires:` date's survival is *structural*, not enforced code — the runner
simply never touches the file, so there is nothing in its own write path
that COULD reset the date.

### 9.6 Closed code list (15 codes total)

`LINT_FAILED` (composition pass-through, not a schema code)
`MANIFEST_MISSING` `MANIFEST_BLOCK_MISSING` `MANIFEST_BLOCK_AMBIGUOUS`
(append-only, §9.2 — the §8 "ambiguous" class had prose but no code)
`MANIFEST_FORMAT` `MANIFEST_DUPLICATE` (intra-kind AND cross-namespace,
§9.2) `MANIFEST_COMMIT_MISMATCH`
`EXTRACTION_STALE`
`ANCHOR_TOKEN_INVALID` (append-only, §9.3 — author-bundle/T4c precedent)
`UNKNOWN_ANCHOR` `MISSING_EXTRACTION`
`GAP_FORMAT` `GAP_EXPIRED` `NO_GAP_ENTRIES`
`TOOL_MISSING` (no sha256sum/shasum on `PATH`, or `date` itself fails —
fails closed rather than skipping freshness/expiry checks).

No temp files are used anywhere in this gate (pure shell variables and
command substitution, the same no-`mktemp` style `lint-journey-extracted.sh`
uses) — `MKTEMP_FAILED` is deliberately NOT shipped (ship it only if temps
are used, per task instruction; this gate needs none).

Usage error, a missing `EXTRACTED` file, or a `GAPS` path that was GIVEN
but does not exist: exit 2 (the same "missing-files exit 2" symmetry
`check-extracted-provenance.sh`, task E2, applies to its `EXTRACTED`/
`REPO_ROOT` args). `MANIFEST`'s absence is deliberately **not** in this
class — see `MANIFEST_MISSING`, §9.2, above. Any chain violation: exit 1,
fail-slow WITHIN each of the four stages (never fail-fast mid-stage), but
a failing stage still halts BEFORE the next stage runs (§9.2). Success:
one `OK: <n> anchor(s) required (<n> feat, <n> screen), <n> staged entries
checked, <n> gap(s) credited` summary line, exit 0.

---

## 10. `journey-extracted-stage.sh CANDIDATES MANIFEST REPO_ROOT OUT_EXTRACTED [GAPS] [--regenerate]` — the stage runner (task E4, spec §4.3/§6.1/§14)

Where §6/§8/§9 are gates over an ALREADY-STAGED `JOURNEY_EXTRACTED.md`,
this runner is what PRODUCES that file in the first place: the
deterministic bridge between Stage 4b's model output
(`step0-out/journey-candidates.md`) and a lint-clean, provenance-verified,
manifest-accounted-for staging file. This runner itself is
**deterministic** — Stage 4b's model work happens in another harness
entirely; `CANDIDATES` is a plain input file here, exactly as `MANIFEST`
is. There is no `RUN_LLM_GEN`, no backend, no network anywhere in this
script.

### 10.1 The CANDIDATES grammar (spec §4.1)

```
extraction_commit: <40-hex sha of the audited repo>

## JOURNEY-CANDIDATE — "<title>"
origin:          EXTRACTED
persona:         ...
goal:            ...
priority:        ...
covers:          ...
flows:           ...
oracle_surface:  ...
negative_states: ...
grade:           [C] | [I] | [G] | [X]
steps:
  1. ...
oracle:          ...                (or oracle_gap: ...)
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

```json field_sources
{}
```

## EXTRACTION-SOURCES
  - <path>:<line> — "<verbatim quote>"
  - <path>#<heading>
prior_e2e:       <relpath>            (optional — see §10.2)

## JOURNEY-CANDIDATE — "<next title>"
...
```

A shared `extraction_commit:` header line precedes the first
`## JOURNEY-CANDIDATE` heading; everything from there to the next such
heading (or EOF) is ONE candidate's slice, ALWAYS containing both the
frozen `## JOURNEY-CANDIDATE` block (SAME field grammar DERIVED/PERSONA/
SIMULATOR candidates use, plus this file's own `grade:` field — the
extractor grades, and grade is not part of the generic candidate schema
those other origins carry) and its own `## EXTRACTION-SOURCES` block.

**The `json field_sources` fence is still required** (design decision):
`journey-gen-check-candidate.sh`'s `MISSING_FIELD_SOURCES` check is not
origin-gated — restrict-never-broaden means DERIVED/PERSONA/SIMULATOR/
EXTRACTED behavior of that check is byte-identical (§10.5). An EXTRACTED
candidate therefore still needs a `json field_sources` fence to clear the
unmodified checker, even though EXTRACTED's REAL provenance is the
`## EXTRACTION-SOURCES` block, never this fence. Stage 4b's worked example
emits `{}` (a trivially valid, empty JSON object) here — satisfying the
checker's structural requirement without duplicating provenance the
EXTRACTION-SOURCES block already carries byte-verifiably. This mirrors the
SIMULATOR precedent exactly: `simulator-run.sh`'s own candidates ALSO
carry a `json field_sources` fence even though their real provenance is
the appended `## SIM-TRACE` block, not the fence
(`journey/tests/fixtures/simulator/expected-candidate-p1.md`).

### 10.2 The candidate-side `prior_e2e:` syntax (this runner's own design decision)

The design spec fixes the STAGED entry's `prior_e2e:` shape (§4.7 above)
but leaves the CANDIDATE-side syntax open. This runner's ruling: `prior_e2e:`
is written as the LAST line of a candidate's own `## EXTRACTION-SOURCES`
block, after its citation lines — never inside the `## JOURNEY-CANDIDATE`
field block itself. Rationale: `prior_e2e:` is extraction PROVENANCE
(Stage 4b discovers it via the manifest's own `e2e_test:` lines), not a
generic journey-intent field any other origin's candidate ever carries —
it belongs structurally beside the rest of the provenance the
EXTRACTION-SOURCES block carries. This placement also means
`journey-gen-check-candidate.sh` (which knows nothing about `prior_e2e:`)
never needs to special-case it: like the EXTRACTION-SOURCES citation
lines themselves, it is simply inert content to that checker's `^field:`
pattern matches. The runner copies it into the staged entry's own
`prior_e2e:` field verbatim; grammar is re-validated there by the composed
lint's `PRIOR_E2E_FORMAT` check, never re-implemented in this runner.

### 10.3 Runner argument/composition order (booby-trap-provable)

1. **Args validated, exit 2**: `CANDIDATES` must exist; `REPO_ROOT` must
   be a directory; `GAPS`, if given, must exist. `REPO_ROOT`'s check
   happens HERE — before any candidate is read, before any gate is
   composed — proven by a dedicated test: a `git` PATH-shim that touches a
   sentinel file is never touched when `REPO_ROOT` is missing (not even
   `journey-gen-check-candidate.sh` runs once). `MANIFEST` is deliberately
   **not** checked here — see §10.6.
2. **Degenerate whole-file tokens** (§10.4).
3. **Mode determined**: `OUT_EXTRACTED`'s existence + `--regenerate`
   decide fresh vs restage vs regenerate-then-fresh (§10.7).
   `REGENERATE_REFUSED` is checked here, against the EXISTING file only,
   before `CANDIDATES`' own header or body is parsed at all.
4. **`CANDIDATES` header `extraction_commit:`** validated (40-hex
   required; `EXTRACTION_COMMIT_INVALID` otherwise — reusing
   `lint-journey-extracted.sh`'s own code name for the identical grammar
   violation, applied to a different file's header).
5. **`CANDIDATES` split** into per-candidate slices (one per
   `## JOURNEY-CANDIDATE` heading through the next such heading or EOF —
   INCLUDING that candidate's own `## EXTRACTION-SOURCES` block, mirroring
   how `simulator-run.sh` feeds its whole per-bundle candidate output,
   `## SIM-TRACE` included, to the same checker). Zero slices found ->
   `NO_CANDIDATE_BLOCK` (reusing `journey-gen-check-candidate.sh`'s own
   code name, applied at CANDIDATES-file granularity instead of
   per-slice — the two scopes never actually collide in practice, since
   every slice this runner builds always starts with a real
   `## JOURNEY-CANDIDATE` heading by construction).
6. **Per-candidate, IN ORDER, FAIL-FAST** on the first bad candidate
   (mirrors `simulator-run.sh`'s per-bundle loop, deliberately NOT the
   schema-lint gates' fail-slow-within-one-file style — a runner
   assembling NEW content stops at the first bad input, exactly like
   every other generation runner in this framework):
   1. `journey-gen-check-candidate.sh SLICE --origin EXTRACTED` (compose,
      fail closed; pass-through diagnostics).
   2. `CANDIDATE_WORKFLOW_FIELD` — `needs_human_confirm:`/
      `confirmation_status:`/`promoted_as:`/`resolution:`/
      `resolved_from:` anywhere in the slice is fail-closed (workflow
      state is never the model's to set — the SIMULATOR
      `PROMOTION_STATUS_FORBIDDEN` precedent, generalized to five field
      names).
   3. **Normalized-key dedup** — `norm_covers`/`norm_oracle`
      (`journey-lib.sh`, the SAME accessors `journey-inbox-triage.sh`/
      `journey-reality-intake.sh` use, covers and oracle compared as a
      PAIR via two `[ = ]` tests, never collapsed into one joined
      string): a match against a PRESERVED entry (restage mode only) is
      an idempotent `SKIPPED` line, never an error; a match against an
      earlier candidate already kept THIS run is `STAGED_DUP_KEY` (fail
      closed). The oracle side of the key is whichever of `oracle:` /
      `oracle_gap:` the candidate carries (§4.5) — both are legitimate
      grounds for a match.
   4. **Next-free id assignment** — starts scanning from `EXTRACTED-1` and
      skips every id already in the preserved set OR already assigned
      this run (`simulator-run.sh`'s own `_next_free` idiom, gap-filling:
      a preserved set with a hole at `EXTRACTED-2` gets that hole filled
      before a new id is minted past the preserved maximum — this runner
      does NOT pre-seed `_next` at "preserved max + 1", which would have
      silently abandoned gap-filling).
   5. The entry is appended to the in-progress assembly buffer, fields
      copied from the candidate slice in the canonical
      `JOURNEY_EXTRACTED.md` field order (§3.3 above);
      `needs_human_confirm: true` + `confirmation_status: PENDING` are
      FORCED regardless of candidate content; `grade:` is copied verbatim
      from the candidate (the extractor grades — `GRADE_UNKNOWN` is the
      composed lint's job to catch, never re-validated here; a composed
      gate's own check is never re-implemented).
7. **`manifest_sha256` stamp** — real, or a syntactically-valid
   placeholder (§10.6).
8. **Restage mode only**: preserved entries are written into the assembly
   buffer BYTE-FOR-BYTE (§10.7's mechanism).
9. **Composed gates**, in order, ALL green before any rename (§10.8).
10. **Temp + trap + mv** (house rule 8) — `manifest_sha256` is therefore
    only ever durably "re-stamped" at the moment of a successful rename,
    never before.

### 10.4 Degenerate whole-file tokens

Mirrors `simulator-run.sh`'s `EMPTY-CANDIDATE` loneness idiom exactly
(`grep -vcE '^[[:space:]]*$'` must count exactly 1 non-blank line, and that
line must match the token): a `CANDIDATES` file whose only non-blank
content is a lone `EXTRACTION-FAILED: <reason>` line is a loud,
attributable failure (exit 1 — mirrors `journey-gen-check-candidate.sh`'s
own `CANDIDATE-FAILED` / `simulator-run.sh`'s `SIM-FAILED`). A file whose
only non-blank content is a lone `NO-JOURNEYS-FOUND` line (legitimate —
e.g. a BACKEND_ONLY project with no user-facing flows, spec §4.1) appends
one line (`ATTEMPTED: <CANDIDATES path> — NO-JOURNEYS-FOUND`) to
`OUT_EXTRACTED`'s SIBLING `EXTRACTED_ATTEMPTS.md` (the
`SIMULATOR_ATTEMPTS.md` precedent, adapted to whole-run granularity — there
is no per-bundle concept here) and exits 0. `OUT_EXTRACTED` itself, and
everything else, is left completely untouched — including
re-verification of any PRESERVED entries from a prior run against a
possibly-changed `MANIFEST.md`: a `NO-JOURNEYS-FOUND` pass is a pure
attempts-log append, nothing more. This is a deliberate, documented
limitation: an operator who wants existing entries forced through
re-verification with zero new candidates has no dedicated path through
this runner for that — they would need to re-run with a real (even if
net-zero-after-dedup) candidates file.

### 10.5 The candidate checker composition (§7.1's E1 extension)

`journey-gen-check-candidate.sh` gains `EXTRACTED` as a fourth `--origin`
value (usage string updated); every check inside it keys off
`$EXPECT_ORIGIN` exactly as before, so `DERIVED`/`PERSONA`/`SIMULATOR`
behavior is byte-unchanged (diff-locked by the pre-existing suite,
re-confirmed green, unmodified, alongside this increment). `EXTRACTED`
just becomes a fourth legal value of the same variable — the restrict-
never-broaden discipline the `SIMULATOR` addition established.

### 10.6 `manifest_sha256` stamping and the deliberate absence of an early `MANIFEST` check

The runner computes `manifest_sha256` via the IDENTICAL byte-range recipe
`check-extraction-coverage.sh` uses (the `EXTRACTION-MANIFEST BEGIN`..`END`
lines, inclusive). When `MANIFEST` does not exist, has no machine block, or
no `sha256sum`/`shasum` tool is on `PATH`, the runner stamps a
syntactically-valid 64-zero PLACEHOLDER instead of failing immediately —
this is safe because that temp file is NEVER renamed to `OUT_EXTRACTED` in
that case: the composed `check-extraction-coverage.sh` call (step 9,
`MANIFEST` passed as its own first positional arg, read directly, never
through this runner's stamp) independently and honestly reports
`MANIFEST_MISSING` / `MANIFEST_BLOCK_MISSING` / `TOOL_MISSING`, and the run
fails before any rename. This lets the runner avoid ever duplicating
`check-extraction-coverage.sh`'s OWN `MANIFEST_MISSING` message: that
code is deliberately a CHAIN code (§9.2), not a usage-class exit-2
check — a brand-new project legitimately has no `MANIFEST.md` yet — and
this runner's composition inherits that exact posture by construction
rather than adding its own early exit-2 guard that would pre-empt and
shadow it.

**The `EXTRACTED_GAPS.md` clock-rule forward pointer, closed (spec §14
Q3):** this runner never writes `EXTRACTED_GAPS.md` — it is a human-authored
artifact (§9.5 above), and `GAPS` is passed through to
`check-extraction-coverage.sh` unmodified, read-only. Because this runner
has no write path to that file at all, an `expires:` date's survival
across re-staging is *structural*, not a rule this runner enforces in
code: there is nothing in the runner's own write surface that could ever
reset it. §9.5's forward pointer is closed by this fact, not by new logic.

### 10.7 The §6.1 re-stage contract — implementation

**Preserved-entry byte-for-byte survival (the load-bearing mechanism).**
When `OUT_EXTRACTED` already exists (and `--regenerate` was not given, or
was given but refused), the runner is in RESTAGE mode. Preserved entries
are copied into the new assembled temp file via a **direct awk stream**,
never through an intermediate shell variable:

```sh
awk '/^## EXTRACTED-/{f=1} f{print}' "$OUT_EXTRACTED"
```

run INSIDE the same `{ ... } > "$_full_tmp"` block that writes the new
header and (via `cat`) the newly-assembled entries — piped straight to the
output file. This is deliberately NOT `_region="$(awk ...)"` followed by
`printf '%s\n' "$_region"`: a `$(...)` command substitution strips ALL
trailing newlines from its captured output, which would silently disturb
the exact byte content at EOF of the preserved region on every re-stage —
a `$(...)` round-trip is safe for VALUES (field extraction, ids, keys —
this runner uses it everywhere else, correctly) but not for an entire
multi-line, human-edited REGION whose byte-for-byte survival is the
guarantee under test. The direct-stream form reproduces every preserved
line exactly, including whatever `resolution:`, supplied `oracle:`,
edited `covers:`, or `promoted_as:` a human wrote, verbatim — because
those bytes are never parsed, never reconstructed field-by-field, and
never pass through a variable at all on their way into the new file.
`journey-lib.sh`'s `extracted_ids`/`extracted_block`/`extracted_field`
accessors ARE used during restage — but read-ONLY, purely to compute ids
and normalized covers/oracle keys for the dedup/next-free logic; they never
touch what gets WRITTEN for a preserved entry.

**Re-verification.** Because preserved entries are copied into the SAME
temp file as newly-staged ones, and `lint-journey-extracted.sh` /
`check-extracted-provenance.sh` / `check-extraction-coverage.sh` all
iterate over EVERY `## EXTRACTED-<n>` entry in whatever file they are
given — unconditionally, regardless of `confirmation_status` or a
`promoted_as:` stamp — a single composed run of the three gates against
the fully-assembled temp file re-verifies preserved entries and new
entries identically. There is no separate code path that would skip a
`REJECTED` or `promoted_as:`-stamped preserved entry (spec §14 Q7:
"terminal entries still integrity-checked").

**`ORPHANED_AFTER_RESTAGE`.** If any of the three composed gates fails,
the runner scans that gate's own diagnostic text for every PRESERVED id
(`EXTRACTED-<n>`, digit-boundary-guarded via `grep -qE
"${_pid}([^0-9]|$)"` — so `EXTRACTED-1` can never falsely match a mention
of `EXTRACTED-10`) and prints `ORPHANED_AFTER_RESTAGE: EXTRACTED-<n>` for
each one implicated, IN ADDITION TO (never instead of) the underlying
gate's own pass-through diagnostic. The human sees both WHAT failed (a
`QUOTE_UNVERIFIED`, an `UNKNOWN_ANCHOR`, a `MISSING_EXTRACTION`, ...) and
THAT it constitutes a regression against previously-staged content, not a
brand-new candidate simply failing validation for the first time. Nothing
is renamed; the scratch temp file is trap-cleaned; `OUT_EXTRACTED` is
byte-unchanged.

**Idempotent skip vs. `STAGED_DUP_KEY` vs. `REJECTED_KEY_COLLISION`.** A
new candidate whose normalized covers+oracle pair matches a PRESERVED
entry whose `confirmation_status` is `PENDING` or `CONFIRMED` (including
a `promoted_as:`-stamped terminal entry) is silently skipped (a
`SKIPPED: <title> — already staged as EXTRACTED-<n>` line, informational,
never an error) — re-presenting the same extraction output on a later
Stage 4b pass is idempotent. A match against a **`REJECTED`** preserved
sibling is different in kind (V-E4 F1, append-only code): it fails loud
with `REJECTED_KEY_COLLISION: candidate <title> matches REJECTED
EXTRACTED-<n> — delete the REJECTED entry first to re-stage (deliberate
friction, spec §6)`, run FAILS, `OUT_EXTRACTED` byte-unchanged. This is
spec §6's owner-approved text made mechanical: "the normalized-key dedup
against a REJECTED sibling surfaces, forcing the human to delete the
REJECTED entry first: deliberate friction" — a silent skip here would
block §4.2's documented recovery path for a wrongly-rejected entry
(delete the REJECTED entry by hand → re-stage → the candidate returns as
a NEW entry) behind a mislabeled "idempotent re-run" message. The matched
sibling's status is read via the SAME first-match `extracted_field`
accessor every gate uses (L11). Two DISTINCT candidates within the SAME
`CANDIDATES` file sharing a normalized key is `STAGED_DUP_KEY` instead —
this is checked ONLY against candidates already kept (assigned an id) this
run, so a candidate that matches a PRESERVED entry and gets skipped is
correctly never counted toward a same-run duplicate: if a second candidate
also matches that same preserved entry, it too is silently skipped, not
flagged as a duplicate against the first (already-skipped) one.

### 10.8 `--regenerate` (spec §14 Q5 — no other override exists)

Refuses (`REGENERATE_REFUSED`, fail-slow — every offending preserved entry
is named, not just the first) when ANY existing entry's
`confirmation_status` is not exactly `PENDING`, or carries a `promoted_as:`
or `resolution:` line. With an all-`PENDING`, unresolved, unpromoted file,
the runner discards the existing entries entirely and rebuilds from
`CANDIDATES` alone — identical in every respect to fresh-stage assembly
(ids from 1, no preserved-entry logic runs at all). A missing
`OUT_EXTRACTED` makes `--regenerate` an inert no-op, since fresh stage is
already exactly that. There is deliberately no force flag, no override
beyond `--regenerate` itself, and no way to bypass a refusal except
deleting `OUT_EXTRACTED` by hand (Q5, binding) — this runner adds no
escape hatch of any kind.

### 10.9 Codes

Own (append-only, closed): `CANDIDATE_WORKFLOW_FIELD`, `STAGED_DUP_KEY`,
`REJECTED_KEY_COLLISION` (append-only addition, V-E4 F1 — the
REJECTED-sibling carve-out of the idempotent-skip path, §10.7; spec §6's
"deliberate friction" made mechanical), `ORPHANED_AFTER_RESTAGE`,
`REGENERATE_REFUSED`. Reused verbatim from an
existing gate for an identical meaning at a different scope:
`MKTEMP_FAILED` (check-extracted-provenance.sh's own scratch-space-
creation-failure code), `EXTRACTION_COMMIT_INVALID`
(lint-journey-extracted.sh's own header-grammar code, applied to the
`CANDIDATES` file's header instead of `OUT_EXTRACTED`'s), `NO_CANDIDATE_BLOCK`
(journey-gen-check-candidate.sh's own code, applied at CANDIDATES-file
granularity instead of per-slice). Plus a bare `EXTRACTION-FAILED:
<reason>` pass-through of the model's own token (SIM-FAILED style, not a
`CODE:` line) and every pass-through code `journey-gen-check-candidate.sh`
/ `lint-journey-extracted.sh` / `check-extracted-provenance.sh` /
`check-extraction-coverage.sh` emit.

Usage error, a missing `CANDIDATES` file, a missing `REPO_ROOT` directory,
or a `GAPS` path that was GIVEN but does not exist: exit 2. Any other
failure: exit 1. Success: one summary line naming how many new entries
were staged (and how many were skipped as already-staged, when nonzero),
exit 0.

---

## 11. `journey-extracted-confirm.sh MAP EXTRACTED MANIFEST [GAPS] [--approve]` — the confirm gate (task E5, spec §4.3/§14)

Where §6/§8/§9/§10 stage, verify, and account for candidates, this gate is
the ONLY path from a `confirmation_status: CONFIRMED` staged entry to a
real `## JOURNEY-5xx` block in `JOURNEY_MAP.md` (I3, B4) — the human
confirmation act itself, made mechanical. It composes every prior gate
(never re-implementing schema, provenance, or coverage logic) and adds one
new kind of check none of them perform: FEAT-grammar `covers:` enforcement
against the manifest at the moment of promotion (spec §14 Q6), because a
promoted journey feeds `author-bundle.sh`'s blind pipeline, which requires
FEAT-anchored covers unconditionally.

### 11.1 Signature note — a §14-forced deviation from the spec §4.3 draft

The design spec's §4.3 draft text names this gate `journey-extracted-
confirm.sh MAP EXTRACTED [--approve]`. §14 Q6 ratifies gate-enforced
FEAT-grammar covers, including existence of every referenced FEAT id in
the manifest's OWN `feat:` lines (`COVERS_UNKNOWN_FEAT`) — a check this
gate cannot perform without reading `MANIFEST` directly, since neither
`MAP` nor `EXTRACTED` carries the manifest's own anchor list. The ratified
signature therefore adds `MANIFEST` as a new required positional arg, and
`GAPS` as an optional fourth positional (passed straight through to the
composed `check-extraction-coverage.sh`, unchanged): `journey-extracted-
confirm.sh MAP EXTRACTED MANIFEST [GAPS] [--approve]`. `--approve` may
appear in any argument position (mirrors `journey-inbox-triage.sh` /
`journey-reality-intake.sh`); `GAPS` is distinguished from `--approve`
purely by NOT starting with `--` — the remaining positional args keep
their original relative order.

### 11.2 Composition (fail-closed, in order)

1. `lint-journey-extracted.sh EXTRACTED` — `LINT_FAILED` on non-zero.
2. `lint-journey-map.sh MAP` — `LINT_FAILED` on non-zero.
3. `check-extraction-coverage.sh MANIFEST EXTRACTED [GAPS]` — pass-through
   of its own chain codes (`MANIFEST_MISSING`, `MANIFEST_BLOCK_AMBIGUOUS`,
   `EXTRACTION_STALE`, `UNKNOWN_ANCHOR`, `MISSING_EXTRACTION`, ...). This
   single composed call brings the ENTIRE manifest chain — parse,
   soundness, freshness, completeness — "for free"; this gate never
   duplicates any of it. Because `check-extraction-coverage.sh` itself
   iterates over every entry in `EXTRACTED` regardless of
   `confirmation_status` or a `promoted_as` stamp (§9.4), this one
   composed call is also how a `promoted_as`-stamped terminal entry's
   citations and manifest bindings get re-verified on every confirm run —
   spec §14 Q7's "integrity was re-checked by the composed gates", made
   concrete.

`MANIFEST`'s existence is deliberately **not** an early exit-2 usage
check — same posture `journey-extracted-stage.sh` takes (§10.6):
`MANIFEST_MISSING` is a CHAIN code belonging to
`check-extraction-coverage.sh`, not a caller mistake this gate pre-empts.

### 11.3 Selection and the terminal/anti-vacuous shape (spec §14 Q7)

An entry is **promotable** iff its `confirmation_status` (read via the
SAME first-match `extracted_field` accessor every gate in this framework
uses, L11) is exactly `CONFIRMED` and it carries NO `promoted_as:` line.
An entry carrying a `promoted_as:` line is **terminal for promotion
only** — composition already guarantees that stamp is well-formed and
sits on a `CONFIRMED` entry (`lint-journey-extracted.sh`'s
`PROMOTED_AS_INVALID` check, §6.1, ran in composition step 1 above) — it
is skipped, and printed as inventory (`ALREADY PROMOTED: EXTRACTED-<n> ->
JOURNEY-<id> (terminal; skipped)`).

- **Zero promotable AND zero terminal** → `NO_CONFIRMED_ENTRIES`
  (anti-vacuous: an invoked confirm run with nothing to confirm never
  passes vacuously).
- **Zero promotable, but >=1 terminal** → a legitimate no-op: the
  inventory prints, exit 0. An all-promoted staging file is not a vacuous
  pass — every entry in it was, at some point, a real confirmation.
- **>=1 promotable** → proceeds to per-entry checks below; any terminal
  entries still print as inventory alongside the promotion.

### 11.4 Per-entry promotion checks (fail-slow)

Every PROMOTABLE entry (never a terminal one — its checks already ran at
a prior confirmation) must pass, independently and accumulated:

- **`grade` must be exactly `[C]`** (`GRADE_NOT_C: <id>: <grade>`
  otherwise) — an `[I]`/`[G]`/`[X]` entry is never promotable as that
  grade (spec §9.6, §14 locks 2/3); a human resolves it into `[C]` first
  (§4.8 above).
- **the entry must carry `oracle:`, not `oracle_gap:`**
  (`ORACLE_GAP_UNRESOLVED: <id>` otherwise). Composition already
  guarantees exactly one of the two is present (`ORACLE_EXACTLY_ONE`,
  §4.5) — this check only asks WHICH one.
- **`covers:` — Q6's five requirements, all enforced here** (spec §14 Q6,
  stricter than the SIMULATOR human-law precedent, L18 — EXTRACTED has a
  deterministic consumer chain, so the gate enforces what SIMULATOR
  leaves to triage-time human judgment):
  1. every token matches the anchored FEAT grammar
     `^FEAT-([A-Z]+-)?[0-9]+$` (`COVERS_NOT_FEAT: <id>: <token>`
     otherwise);
  2. matching is exact-token, **never substring** — a token is compared
     via `grep -qxF` against the manifest's own `feat:` id list, whole
     line, fixed string;
  3. every grammatically-valid token must EXIST in `MANIFEST`'s own
     `feat:` lines (`COVERS_UNKNOWN_FEAT: <id>: <token>` otherwise — new
     code, spec §7.4);
  4. no duplicate tokens within one entry's `covers:` (`COVERS_DUPLICATE:
     <id>: <token>` — new code, spec §7.4);
  5. at least one valid FEAT anchor is required. **Whitelist-before-use
     discipline (L22, the SAME pattern as `check-extraction-coverage.sh`'s
     `ANCHOR_TOKEN_INVALID`):** a token is checked against the grammar
     FIRST; a token that fails grammar is reported as `COVERS_NOT_FEAT`
     and never ALSO checked for existence — so a lone invalid token (e.g.
     a screen-anchored `covers: SCR-login` that a human forgot to
     re-anchor before confirming) yields exactly its ONE primary code,
     never a confusing second "zero valid anchors" violation on top.

### 11.5 Collisions (I8)

Every promotable entry's `norm_covers`+`norm_oracle` key (the SAME shared
`journey-lib.sh` normalization every dedup pass in this framework uses,
never forked) is compared against:

1. **every existing map journey, any origin** — `EXTRACTED_COLLIDES:
   EXTRACTED-<n> vs JOURNEY-<id>`;
2. **every OTHER promotable entry in the SAME run** (sibling comparison,
   `i<j` only, one report per pair) — `EXTRACTED_COLLIDES: EXTRACTED-<n>
   vs EXTRACTED-<m>`.

`promoted_as`-stamped (terminal) entries are excluded from the comparison
set — not because collisions with them don't matter, but because they
were never selected as promotable to begin with (§11.3); the map journey
they already became IS the thing being compared against in check 1 above.
Any collision refuses the WHOLE run (fail-slow, accumulated with every
other per-entry violation from §11.4) — human adjudication is required
(edit `covers:`/`oracle:`, or reject the candidate), never silent
merge or skip (Lock 1).

### 11.6 Id assignment and the bounded range (spec §14 §5 tightening)

`JOURNEY-501` upward, skipping ALL existing map ids of any block (the
same "century overflow cannot collide" discipline every other origin's
promotion gate uses) and every id already assigned earlier in the SAME
run. **EXTRACTED map ids are 501-599 inclusive** — an assignment that
would exceed 599 is `RANGE_EXHAUSTED` (message: "extension requires
separate owner ratification"), and refuses the WHOLE run, still before
any write.

### 11.7 What gets promoted (§5 above, now normative — this gate's own job)

Per promoted entry: `persona, goal, priority, covers, flows,
oracle_surface, negative_states, steps, oracle, runner` copy unchanged.
Forced regardless of staging content: `origin: EXTRACTED`,
`author_status: UNWRITTEN`, `evidence: []` (Lock 4). **Injected** (L25 —
mirrors `journey-inbox-triage.sh`'s own `_write_promoted_block` at its
lines 312/332 exactly): `data_fixtures: []` and `exemptions: []` — both
are `REQUIRED_FIELDS` in `lint-journey-map.sh`'s schema, but no staging
entry ever carries them (§3.3 above lists the staging field set, which
omits both) — without this injection, every promotion would dead-end at
the composed map-lint self-check below (proven empirically, V-E1).
`test:`'s literal `<n>` placeholder token is substituted with the
assigned numeric id (commit 4b08dcb's precedent — a concrete `test:`
value carrying no `<n>` token copies through byte-identical). Staging-only
fields (`needs_human_confirm`, `confirmation_status`, `grade`,
`extraction_sources`, `prior_e2e`, `resolution`, `resolved_from`,
`rejected_reason`) are NEVER copied — they simply are not read while
building the promoted block.

**New field, this gate's own write (spec §14 Q1):**

```
extraction_provenance: EXTRACTED-<n> commit:<40-hex> confirmed:<12-hex>
```

- `EXTRACTED-<n>` — the staging entry this block was promoted from.
- `commit:<40-hex>` — `EXTRACTED`'s own header `extraction_commit:`,
  copied verbatim (the pinned commit every citation in the staging file
  was verified against).
- `confirmed:<12-hex>` — the first 12 hex characters of a sha256 of
  `EXTRACTED`'s bytes AS THEY EXISTED when this run started (before this
  run's own `promoted_as:` stamping) — computed by THIS gate (never
  trusted from staging input), via `sha256sum`/`shasum` fail-closed to
  `TOOL_MISSING` if neither is on `PATH`. Every entry promoted in the SAME
  run shares the identical `confirmed:` value — they were all promoted
  from the same reviewed snapshot of `EXTRACTED`.

Validated (optional field, when present) by `lint-journey-map.sh`'s own
additive Check 10 (§11.9 below) — never re-implemented as a second parser.

### 11.8 Write discipline (house rule 8, L17)

Both temp files are created together (`.map-XXXXXXXX` / `.extracted-
XXXXXXXX`, `mktemp` in each file's own directory), one combined
`trap ... EXIT INT TERM`. Order: build the temp map (existing `MAP` +
every promoted block appended) → composed `lint-journey-map.sh`
self-check (`LINT_FAILED` on failure, temps cleaned, `MAP` untouched) →
L23 postcondition (every assigned `JOURNEY-<id>` block asserted non-empty
in the temp map — defense in depth on top of the heading-grammar guarantee
composition already established) → build the temp staging (existing
`EXTRACTED` with a `promoted_as: JOURNEY-<id>` line stamped directly after
each promoted entry's FIRST `confirmation_status:` line, matching
`extracted_field`'s own first-match semantics, L11) → composed
`lint-journey-extracted.sh` self-check on the temp staging (re-linted
pre-rename; `LINT_FAILED` on failure, temps cleaned, both files
untouched) → `mv` `MAP` first, THEN `mv` `EXTRACTED` second (L17: the map
write is the SSOT mutation; the staging update is only the audit-trail
annotation of a fact the map write already established — this ordering
means a process interrupted between the two renames leaves the map, not
the staging file, as the single source of truth for "did this promote").

### 11.9 `lint-journey-map.sh` Check 10 — `extraction_provenance:` (additive, append-only)

Mirrors the `preconditions:`/`oracle_classes:` optional-field precedent
(Checks 8/9): `extraction_provenance:` is NOT in `REQUIRED_FIELDS` or
`NONEMPTY_FIELDS` — absent is fine, and every map that predates this
field lints byte-identically to before this check existed (existing
`lint-journey-map_test.sh` assertions are unmodified and pass unchanged).
When present, it is a single-line field (`journey_field`'s accessor
pattern) validated for GRAMMAR only:

```
^EXTRACTED-[0-9]+ commit:[0-9a-f]{40} confirmed:[0-9a-f]{12}$
```

`EXTRACTION_PROVENANCE_FORMAT: <id>: <value>` otherwise. This check does
NOT verify the referenced `EXTRACTED-<n>` id, commit, or hash against
anything live — it is a grammar check on an audit trail, exactly as
Checks 8/9 validate `preconditions:`/`oracle_classes:` grammar without
probing whether the referenced auth/env/data/state actually exists.

### 11.10 Codes (closed enum, this gate)

`APPROVE_REQUIRED` `LINT_FAILED` (pass-through wrapper, composition steps
1-2) `NO_CONFIRMED_ENTRIES` (anti-vacuous; a legitimate all-terminal file
is its own no-op, not this code) `GRADE_NOT_C` `ORACLE_GAP_UNRESOLVED`
`COVERS_NOT_FEAT` `COVERS_UNKNOWN_FEAT` `COVERS_DUPLICATE`
`EXTRACTED_COLLIDES` `RANGE_EXHAUSTED` `TOOL_MISSING` `MKTEMP_FAILED`,
plus every pass-through code `check-extraction-coverage.sh` (composition
step 3) emits (`MANIFEST_MISSING`, `MANIFEST_BLOCK_AMBIGUOUS`,
`MANIFEST_FORMAT`, `MANIFEST_DUPLICATE`, `MANIFEST_COMMIT_MISMATCH`,
`EXTRACTION_STALE`, `ANCHOR_TOKEN_INVALID`, `UNKNOWN_ANCHOR`,
`MISSING_EXTRACTION`, `GAP_FORMAT`, `GAP_EXPIRED`, `NO_GAP_ENTRIES`). Plus
`EXTRACTION_PROVENANCE_FORMAT`, owned by `lint-journey-map.sh` (§11.9), a
map-side code this gate can trigger indirectly (its own self-check
composes that lint) but never emits directly itself.

Usage error, a missing `MAP`/`EXTRACTED`, or a `GAPS` path that was GIVEN
but does not exist: exit 2. `MANIFEST`'s absence is deliberately NOT in
this class (§11.2). Any gate violation: exit 1, fail-slow accumulation
within each check group (never `| while read`, house rule 2). Success:
one `PROMOTED: EXTRACTED-<n> -> JOURNEY-<id>` line per promotion plus a
summary line, exit 0.
