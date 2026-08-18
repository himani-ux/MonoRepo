# JOURNEY_INBOX format + lint — contract

Operator-facing contract for the stochastic-candidate inbox layer: how the
Step 3 user-simulator engine stages candidate journeys, how a human triages
them, and how `lint-journey-inbox.sh` proves the schema before any candidate
is ever eligible for promotion. Sibling of `journey/docs/uat-report-format.md`
and `journey/JOURNEY_MAP.template.md`; same house style.

---

## 1. Purpose

`JOURNEY_MAP.md` is the canonical intent SSOT — it is written by a human
(`origin=PERSONA`), derived from canonical docs (`origin=DERIVED`), or
confirmed from a real failure (`origin=REALITY`). Only ONE capture source is
stochastic: the Step 3 user-simulator, an LLM-driven actor that drives the
running app *as a persona* and can fumble, hallucinate a workflow that
doesn't exist, or mistake noise for a real gap. Per the design spec (§4.2,
§5.2): *"A stochastic discovery engine must never directly mutate the
SSOT."* `JOURNEY_INBOX.md` is the noise filter — every `origin=SIMULATOR`
candidate lands here first, unconfirmed, and only a human-triaged
`promotion_status: ACCEPTED` entry is ever eligible to become a real
`JOURNEY-<n>` block.

This layer never gates on the simulator itself (that would make CI flaky —
the stochastic discovery → deterministic gate boundary, spec §3.3). It gates
on the STAGED ARTIFACT: `lint-journey-inbox.sh` proves the inbox file is
schema-valid before any triage decision is trusted, exactly as
`lint-journey-map.sh` does for the canonical map.

**Per-project artifact.** `JOURNEY_INBOX.md` itself is written at the root
of an adopting project (sibling of that project's `JOURNEY_MAP.md`) — it is
NOT shipped by the framework. The framework ships the template
(`journey/JOURNEY_INBOX.template.md`), this contract doc, and the lint
(`journey/bin/lint-journey-inbox.sh`).

---

## 2. The inbox

An inbox is one file (conventionally `JOURNEY_INBOX.md`), carrying a
required header line, free narrative prose (no authority — same rule as a
UAT report's narrative), and zero or more `## INBOX-<n>` candidate blocks.

### 2.1 Header

- The FIRST LINE of the file must be exactly `# JOURNEY-INBOX`
  (`BAD_HEADER` otherwise — mirrors the `# UAT-REPORT` / `# JOURNEY_MAP`
  first-line laws elsewhere in this framework).
- The literal string `## JOURNEY-` must never appear anywhere in the file,
  in a heading or in prose (`FORBIDDEN_JOURNEY_HEADER`). Inbox entries are
  headed `## INBOX-<n>`, never `## JOURNEY-<n>` — a real map heading has no
  legitimate reason to appear here. This closes a paste-promotion bypass: an
  agent or human cannot dodge triage by pasting a real-looking
  `## JOURNEY-<n>` block directly into the inbox and hoping a downstream
  reader treats it as already-promoted.
- A file that exists but declares zero `## INBOX-<n>` entries is itself a
  failure (`NO_INBOX_ENTRIES`) — an empty inbox file should not exist at
  all; delete it instead of leaving a vacuous shell.

### 2.2 Entry grammar

One block per candidate:

```
## INBOX-<n> — "<title>"
promotion_status: PROPOSED | ACCEPTED | REJECTED
rejected_reason: <non-empty>          (REQUIRED when promotion_status is REJECTED)
origin:          SIMULATOR            (the ONLY allowed value in this file)
persona:         P2 (impatient ops user)
goal:            <what the simulator was trying to accomplish>
priority:        P1
covers:          invoices_list        (a SURFACE screen name — the runner has
                                       no FEAT side; a human re-anchors to
                                       FEAT ids at triage, §6.1)
oracle_surface:  UI+API
negative_states: schema_error, retry_upload
steps:
  1. land on /invoices
  2. upload malformed.csv → inject schema_error
  3. re-upload corrected.csv
  4. observe retry_upload → ACCEPTED
oracle:          row status=ACCEPTED AND GET /invoices returns the row
evidence:        traces/inbox-1-sim.zip
test:            tests/journeys/journey-<n>.spec.ts   (literal <n>; the triage
                                       gate substitutes the assigned id, §6.1)
runner:          playwright
author_status:   UNWRITTEN             (the ONLY allowed value in this file)
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

- `## INBOX-<n> — "<title>"` — `<n>` is a unique positive integer within the
  file (`DUPLICATE_INBOX_ID` on a repeat; `BAD_INBOX_ID` if `<n>` is zero).
- Required fields (every entry): `promotion_status, origin, persona, goal,
  priority, covers, oracle_surface, negative_states, steps, oracle,
  evidence, test, runner, author_status, simulator_trace`. This is the same
  required set as `JOURNEY_MAP.template.md`'s required fields, minus
  `flows`/`data_fixtures`/`exemptions` (not carried by a pre-promotion
  candidate), plus `promotion_status` and `simulator_trace` (inbox-only). A
  missing field key is `MISSING_FIELD: <id>: <field>`.
- A subset of those fields must additionally be non-blank when present:
  `promotion_status, origin, persona, goal, priority, covers,
  oracle_surface, oracle, runner, author_status` (same non-empty subset as
  `lint-journey-map.sh`'s `NONEMPTY_FIELDS`, plus `promotion_status`). A
  present-but-blank value is `BLANK_FIELD: <id>: <field>` — reported instead
  of, never in addition to, `MISSING_FIELD` for the same field.
- The remaining map-inherited fields (`priority`, `oracle_surface`,
  `runner`, ...) are NOT re-validated for enum/business-rule correctness by
  this lint — only for presence/non-blankness above. Their full schema is
  `lint-journey-map.sh`'s job, re-run by the triage gate
  (`journey-inbox-triage.sh`) on the promoted block once it becomes a real
  `JOURNEY-<n>` entry, so the two lints can never disagree about what a
  valid value looks like.

### 2.3 `promotion_status:` and `rejected_reason:`

Single-line field, exactly one of `PROPOSED | ACCEPTED | REJECTED`
(`BAD_PROMOTION_STATUS` otherwise):

- `PROPOSED` — the default; not yet triaged by a human.
- `ACCEPTED` — a human reviewer confirmed the candidate is worth promoting.
  `journey-inbox-triage.sh` promotes only `ACCEPTED` entries.
- `REJECTED` — a human reviewer decided against promotion. A `REJECTED`
  entry additionally REQUIRES a `rejected_reason:` line with a non-empty
  value (`REJECTED_REASON_MISSING` otherwise) — a rejection with no stated
  reason loses the debt-tracking value of having triaged it at all.

### 2.3a `promoted_as:` — the promotion audit trail (T2, append-only)

OPTIONAL single-line field, added by `journey/bin/journey-inbox-triage.sh`
(spec DC-2) — never authored by the simulator runner or a human triager.
When the triage gate promotes an `ACCEPTED` entry, it stamps a
`promoted_as: JOURNEY-<n>` line directly after that entry's
`promotion_status:` line, naming the id it was assigned in `JOURNEY_MAP.md`.
This is a pure audit trail: it lets a reader looking at the inbox alone see
where a candidate ended up, without cross-referencing the map.

Grammar: `promoted_as: JOURNEY-<n>` where `<n>` is one or more digits
(`^JOURNEY-[0-9]+$`). Absence is always legal — most entries never carry it
(only ever-promoted `ACCEPTED` entries do). When present:

- The value must match `^JOURNEY-[0-9]+$`, or `PROMOTED_AS_INVALID: <id>:
  <value>` (malformed).
- The entry's `promotion_status` (read via the SAME first-match accessor as
  every other promotion_status check in this lint — see the L11 note in
  `journey-inbox-triage.sh`'s header) must be exactly `ACCEPTED`, or
  `PROMOTED_AS_INVALID: <id>: promoted_as present but promotion_status is
  <value> (must be ACCEPTED)`. A `promoted_as` line on a `PROPOSED` or
  `REJECTED` entry is nonsensical — nothing was promoted — and is rejected
  the same way a malformed value is.

This is an append-only extension of the T1 contract: `promoted_as:` is not
in `REQUIRED_FIELDS` or `NONEMPTY_FIELDS`, so no existing entry (which never
carries the key) is affected, and every one of T1's original 22 codes still
fires exactly as before.

### 2.4 `origin:` and `author_status:` — restricted in this file only

- `origin:` — the ONLY allowed value is `SIMULATOR`
  (`BAD_ORIGIN: <id>: <value>` otherwise — the code name mirrors
  `journey-gen-check-candidate.sh`'s `BAD_ORIGIN`, the same class of check
  for a different generation pipeline). A stochastic candidate can only ever
  have come from the simulator; any other origin does not belong in this
  file (`PERSONA` and `REALITY` write straight to `JOURNEY_MAP.md`, per
  spec §4.2).
- `author_status:` — the ONLY allowed value is `UNWRITTEN`
  (`BAD_AUTHOR_STATUS: <id>: <value>` otherwise — mirrors the candidate
  checker's `BAD_AUTHOR_STATUS`). Pre-promotion candidates never have a test
  written against them.

### 2.5 `simulator_trace:` — the run record

Block field, same shape as `steps:` / `preconditions:`: the
`simulator_trace:` line followed by one or more 2-space-indented
`  - <key>: <value>` entries.

**Scalar entries — REQUIRED EXACTLY ONCE each:**

| Key | Value | Violation codes |
|---|---|---|
| `persona` | `<token>` — the persona id the simulator ran as | `TRACE_FIELD_MISSING` / `TRACE_FIELD_DUPLICATE` / `TRACE_TOKEN_INVALID` |
| `goal` | `<text>` — the goal it was given (free text) | `TRACE_FIELD_MISSING` / `TRACE_FIELD_DUPLICATE` |
| `app_build` | `<token>` — the app build/commit identifier it ran against | `TRACE_FIELD_MISSING` / `TRACE_FIELD_DUPLICATE` / `TRACE_TOKEN_INVALID` |
| `runner` | `<token>` — the hands driver used (e.g. `playwright`) | `TRACE_FIELD_MISSING` / `TRACE_FIELD_DUPLICATE` / `TRACE_TOKEN_INVALID` |
| `patience_budget` | `<positive integer>` — the abandonment budget it was bound by | `TRACE_FIELD_MISSING` / `TRACE_FIELD_DUPLICATE` / `TRACE_PATIENCE_BUDGET_INVALID` |

A `<token>` is a single run of `[A-Za-z0-9._/-]` characters — no
whitespace. `<text>` may contain spaces.

**List entries — repeatable:**

| Key | Value | Cardinality | Violation codes |
|---|---|---|---|
| `path` | `<step>` — one step of the path actually driven (free text) | REQUIRED, >= 1 | `TRACE_PATH_EMPTY` |
| `stuck_point` | `<text>` — where the simulator hesitated, retried, or nearly abandoned | OPTIONAL, >= 0 | (none — always legal) |
| `evidence` | `<relpath>` — a trace/screenshot path backing the candidate | REQUIRED, >= 1 | `TRACE_EVIDENCE_EMPTY` / `TRACE_EVIDENCE_INVALID` |

An `evidence:` value must not start with `/` and must not contain a `..`
segment (`TRACE_EVIDENCE_INVALID` otherwise — the same repo-relative-path
discipline `uat-report-format.md` §2.2 applies to quote/artifact evidence).

**Structural checks:**

- `simulator_trace:` absent entirely from an entry: `TRACE_MISSING: <id>`
  (the sole code for this — presence of `simulator_trace` is intentionally
  NOT re-checked by the flat `MISSING_FIELD` pass, to avoid double-reporting
  the same root cause under two codes).
- An entry line under `simulator_trace:` that doesn't match
  `  - <key>: <value>` at all (missing dash, missing colon, wrong indent):
  `TRACE_FORMAT: <id>: <line>`.
- A well-formed entry line whose key is outside the eight recognized keys:
  `TRACE_KEY_UNKNOWN: <id>: <key>`.

---

## 3. Runtime truth is never staged here

Same law as `JOURNEY_MAP.md`: `ci_status`, `last_run`, `ci_run_id`,
`ci_artifact`, `failure_summary` never appear in this file. A candidate is
non-deterministic by construction — it has no runtime status until it is
promoted, frozen into a scripted test, and run by CI. Any of the five
runtime-field keys anywhere in the file is rejected as `RUNTIME_FIELD` — the
same code name `journey-gen-check-candidate.sh` and `lint-journey-tests.sh`
use for this exact class of violation, so a reader who has seen either of
those gates already recognizes this one.

---

## 4. `lint-journey-inbox.sh <inbox>` — the gate

POSIX `sh` against stock `/bin/sh`, fail-closed, `CODE: message` on stderr,
non-zero exit on any violation. All violations are accumulated before
exiting (fail-slow, never fail-fast) via `for`/heredoc-`while` — never
`| while read` (a pipeline subshell loses counter mutations; a known
fail-open class in this framework). Success prints nothing and exits 0.

Parsing reuses the identical block-extraction idiom `lint-journey-map.sh`
uses, via two new shared accessors added to `journey/lib/journey-lib.sh`:
`inbox_ids` / `inbox_block` / `inbox_field`, siblings of that file's
`journey_ids` / `journey_block` / `journey_field` (same awk, different
heading prefix: `## INBOX-<n>` instead of `## JOURNEY-<n>`, and a different
default file variable, `JOURNEY_INBOX` instead of `JOURNEY_MAP`). The two
lints can never disagree about how a block is extracted, because they share
the extraction code.

Usage error or missing file: exit 2 (matches `lint-journey-map.sh`'s
convention). Schema violations: exit 1.

### 4.1 Closed code list

File-level:

- `BAD_HEADER` — first line is not exactly `# JOURNEY-INBOX`.
- `FORBIDDEN_JOURNEY_HEADER` — literal `## JOURNEY-` found anywhere.
- `RUNTIME_FIELD` — a runtime-truth field key found anywhere.
- `DUPLICATE_INBOX_ID` — an `INBOX-<n>` id appears more than once.
- `BAD_INBOX_ID` — an `INBOX-<n>` id is not a positive integer (zero).
- `NO_INBOX_ENTRIES` — anti-vacuous: a valid header but zero entries.

Per-entry schema:

- `MISSING_FIELD: <id>: <field>` — a required field key is absent.
- `BLANK_FIELD: <id>: <field>` — a required-nonblank field's value is blank.
- `BAD_ORIGIN: <id>: <value>` — origin present but not exactly `SIMULATOR`.
- `BAD_AUTHOR_STATUS: <id>: <value>` — author_status present but not
  exactly `UNWRITTEN`.
- `BAD_PROMOTION_STATUS: <id>: <value>` — not one of
  `PROPOSED | ACCEPTED | REJECTED`.
- `REJECTED_REASON_MISSING: <id>` — `promotion_status: REJECTED` with no
  non-blank `rejected_reason:`.
- `PROMOTED_AS_INVALID: <id>: <value>` — `promoted_as:` is present but
  either malformed (not `JOURNEY-<n>`) or the entry's `promotion_status` is
  not `ACCEPTED` (T2, append-only — §2.3a).

`simulator_trace:` grammar:

- `TRACE_MISSING: <id>` — the `simulator_trace:` field is entirely absent.
- `TRACE_FORMAT: <id>: <line>` — an entry line doesn't match
  `  - <key>: <value>`.
- `TRACE_KEY_UNKNOWN: <id>: <key>` — a well-formed entry with a key outside
  the eight recognized keys.
- `TRACE_FIELD_MISSING: <id>: <key>` — a required-exactly-once scalar key
  has zero occurrences.
- `TRACE_FIELD_DUPLICATE: <id>: <key>` — a required-exactly-once scalar key
  appears more than once.
- `TRACE_TOKEN_INVALID: <id>: <key>: <value>` — a `persona`/`app_build`/
  `runner` value contains whitespace or a character outside
  `[A-Za-z0-9._/-]`.
- `TRACE_PATIENCE_BUDGET_INVALID: <id>: <value>` — `patience_budget` is not
  a positive integer.
- `TRACE_PATH_EMPTY: <id>` — zero `path:` entries (required >= 1).
- `TRACE_EVIDENCE_EMPTY: <id>` — zero `evidence:` entries (required >= 1).
- `TRACE_EVIDENCE_INVALID: <id>: <value>` — an evidence relpath starts with
  `/` or contains a `..` segment.

### 4.2 What this gate deliberately does not check

- The map-inherited enum fields (`priority`, `oracle_surface`, `runner`,
  ...) are checked for presence/non-blankness only, never for membership in
  their allowed value sets — that re-validation happens once, at promotion
  time, via the composed `lint-journey-map.sh` (§2.2 above). Duplicating the
  enum check here would risk the two gates drifting apart on what counts as
  valid.
- The anti-happy-path rule (a declared `negative_states` value must appear
  in a step) is a `JOURNEY_MAP.md`-only check (`lint-journey-map.sh` Check
  4). A pre-promotion candidate's steps are themselves unconfirmed
  simulator output; the map lint re-applies this rule once the entry is
  promoted.
- The `## INBOX-<n> — "<title>"` heading's title text is not
  grammar-checked beyond the id — `lint-journey-map.sh` does not
  grammar-check `## JOURNEY-<n>` heading titles either; this lint follows
  that precedent.

---

## 5. Composition (the triage gate)

This contract covers the schema layer only. The triage gate
(`journey/bin/journey-inbox-triage.sh MAP INBOX [--approve]`, spec DC-2,
shipped) and the simulator runner (`journey/gen/runners/simulator-run.sh`,
a separate deliverable) COMPOSE `lint-journey-inbox.sh` as an executable —
never re-implement its parsing. A promoted entry is re-validated in full by
`lint-journey-map.sh` after the triage gate writes it into `JOURNEY_MAP.md`,
so a schema drift between the two files is caught immediately, not
discovered later.

`journey-inbox-triage.sh` reads `promotion_status:` via the SAME first-match
`inbox_field` accessor this lint uses (never a raw `grep` over a block) —
otherwise an entry carrying a duplicate `promotion_status:` scalar line
(`PROPOSED` first, `ACCEPTED` second — this lint does not flag that
duplication; see §4.2) would promote on its SECOND line while every reader
of the file, including this lint, classifies it by its FIRST. On success,
the gate stamps `promoted_as: JOURNEY-<n>` (§2.3a) onto each promoted
entry's `promotion_status:` line and re-runs this lint on the result before
renaming it over the inbox — a triage run that produced a schema-invalid
inbox is refused, not written.

---

## 6. How entries get here (T3, spec DC-3 — append-only, no code/semantic change)

Every `## INBOX-<n>` entry in this file was written by ONE producer:
`journey/gen/runners/simulator-run.sh` (the thin runner for the Step-3
user-simulator engine; brain prompt `journey/gen/prompts/simulator-brain.md`,
slicer `journey/bin/simulator-gen-slice.sh`, portability contract
`journey/gen/runners/simulator.workflow.md`). Nothing else writes to this
file — there is no second producer, no hand-authoring convention, and no
other engine targets `JOURNEY_INBOX.md` (PERSONA and REALITY write straight
to `JOURNEY_MAP.md`, per §1).

The runner validates each raw candidate with `journey-gen-check-candidate.sh
--origin SIMULATOR` (the same shared, frozen `## JOURNEY-CANDIDATE` +
`field_sources` grammar every generator in this framework produces) and its
own `## SIM-TRACE` block (re-verified against the facts the runner itself
injected into the bundle — never the model's echo of them) BEFORE any of the
assembly below happens. Assembly is deterministic — there is no model-merge
step, mirroring `persona-run.sh`'s own assembly discipline, with one
structural difference from that pipeline: **there is no refuter stage.**
Every accepted candidate lands here as `promotion_status: PROPOSED`; a human
triage decision (§5, above) is the ONLY filter between a candidate and the
canonical map — never a second model pass.

**Runner-owned facts** — never the model's to set, and never silently
rewritten if a model output tries to claim one of them (a candidate that
DOES try is rejected outright, before assembly, as a validation failure):

- **`## INBOX-<n>` ids** — assigned next-free against the target inbox file
  (skipping ids already present), continuing across separate runner
  invocations (append semantics: multiple simulator passes accumulate into
  the same file rather than overwriting it).
- **`promotion_status: PROPOSED`** — forced on every assembled entry,
  regardless of what the (already schema-validated) candidate said. A model
  emitting ANY `promotion_status:` line at all — even `PROPOSED` — is
  treated as an attempt to assert authority over the human triage decision
  and fails the whole run closed; the runner does not silently strip or
  overwrite it.
- **`origin: SIMULATOR` / `author_status: UNWRITTEN`** — forced, the same
  defensive posture `journey-inbox-triage.sh` uses when it forces these two
  fields at promotion time (§5).
- **Transcript evidence injection** — the runner writes each candidate's raw
  backend output verbatim to `transcripts/INBOX-<n>.transcript.md` (relative
  to the generation `OUTDIR`) and injects that relpath as the FIRST
  `evidence:` entry, in BOTH the entry's top-level `evidence:` field and its
  `simulator_trace:` block — this is the provenance trail back to exactly
  what the model produced. Any additional `evidence:` lines the model itself
  supplied pass through afterward, and are schema-checked like any other
  evidence entry by this lint (§2.5) on the fully assembled file before it
  is ever renamed into place.

This section documents an existing producer; it changes no T1/T2 schema,
adds no new field, and introduces no new lint code — `lint-journey-inbox.sh`
still owns the same closed code list (§4.1) it always has.

### 6.1 The triage-time re-anchor law (V1 F3)

A promoted SIMULATOR journey lands in `JOURNEY_MAP.md` carrying THREE
triage-time placeholders a human must resolve. `journey-inbox-triage.sh`
promotes an ACCEPTED entry's fields verbatim (plus the forced/blank fields
already documented in §5 above) — it does not itself re-anchor `covers:`
or `flows:`, and substitutes only the one exact token described below.

- **`covers:`** — the runner emits `## SURFACE: <screen>` name(s) (sim
  bundles have no PRD/FEAT side to anchor against — see
  `simulator-brain.md`'s `covers:` grammar). A human MUST re-anchor this
  to real `FEAT-<n>` id(s) at triage before the journey can be
  blind-authored, or `journey/bin/author-bundle.sh` fails closed with
  `ANCHOR_TOKEN_INVALID` on the ungrammatical non-FEAT anchor (V-T4b:
  every anchor token must full-match its field's canonical id grammar —
  `FEAT-([A-Z]+-)?<n>` for covers, `AFJ-<n>` for flows, per
  `check-doc-format.sh` — before reaching any matcher; `MISSING_ANCHOR`
  stays reserved for a grammatical id absent from the doc).
- **`flows:`** — forced to `[]` at promotion (§5 above; not carried by a
  pre-promotion candidate). `journey/bin/author-bundle.sh` treats `[]` as
  zero AFJ anchors, never as a match against every APP_FLOW heading (V1
  F1) — a human MAY optionally re-anchor `flows:` to real `AFJ-<n>` id(s)
  at triage; leaving it `[]` is legal and simply means the bundle carries
  no APP_FLOW anchors. Any other non-`AFJ-<n>` token (e.g. the YAML-list
  typo `[AFJ-001]`) is `ANCHOR_TOKEN_INVALID`, fail closed.
- **`test:`** — may carry the literal placeholder token `<n>` (the
  simulator cannot know its future `JOURNEY-<n>` id at generation time).
  `journey-inbox-triage.sh` substitutes ONLY that exact token with the id
  it assigns at promotion (e.g. `journey-<n>.spec.ts` ->
  `journey-301.spec.ts`); a candidate whose `test:` value carries no `<n>`
  token is copied through byte-identical (V1 F4).

This is documentation only — it changes no schema, no lint code, and no
promotion behavior beyond the `test:` substitution itself (V1 F4, already
shipped in `journey-inbox-triage.sh`).
