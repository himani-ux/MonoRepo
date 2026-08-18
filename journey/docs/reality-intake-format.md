# Reality intake — entry-file contract (fix-wave W5, D5 rider)

Operator-facing contract for the reality-capture path: how a confirmed real
workflow failure (an incident, a bug report, a telemetry drop-off) becomes a
new `## JOURNEY-<n>` block straight in `JOURNEY_MAP.md`, without passing
through the stochastic inbox at all. Sibling of
`journey/docs/journey-inbox-format.md` and `journey/docs/uat-report-format.md`;
same house style.

---

## 1. Purpose

Per the parent spec (§5.3, journey-validation design doc): a **REALITY**
journey exists because something already broke in production or was
confirmed by a real incident — it is not a candidate to be triaged, it is
already true. `journey/bin/journey-reality-intake.sh MAP ENTRY_FILE
[--approve]` is the gate that turns a written-up entry into a canonical
`JOURNEY_MAP.md` block: human-approved, id-assigned, deduplicated against
what the map already knows, and lint-clean before the write ever lands.

Unlike the Step-3 simulator's candidates (`journey/docs/journey-inbox-format.md`),
a REALITY entry never sits in `JOURNEY_INBOX.md` awaiting triage — the
confirmation already happened outside this framework (a support ticket, a
server log, an on-call page). This gate's job is capturing that confirmed
fact into the SSOT correctly, not deciding whether to trust it.

Until now this contract existed ONLY as `journey-reality-intake.sh`'s own
header comment — complete as a comment, but not an operator-facing doc, the
one gap in an otherwise fully-documented framework (every sibling capture
path — inbox, UAT report, PRD/APP_FLOW — has one). This file closes that
gap (D5).

---

## 2. The entry file

`ENTRY_FILE` is **not** the `JOURNEY_INBOX.md` candidate format and **not**
the `JOURNEY-CANDIDATE` generator format
(`journey-gen-check-candidate.sh`) — it is exactly ONE journey block in the
full `JOURNEY_MAP.md` grammar (`JOURNEY_MAP.template.md`'s schema), authored
directly by a human or a UAT/incident write-up process. There is no
generator to compose against here; a REALITY entry is hand-written because
the fact it records already happened.

### 2.1 Heading grammar

The FIRST LINE of the entry's block must match, character-exact:

```
## JOURNEY-<digits> — "<title>"
```

— a spaced em-dash (U+2014) and a double-quoted, non-empty title, the same
form every existing map heading and the template's `JOURNEY-000` example
use. The digits are a **throwaway placeholder** — this gate reassigns the
real id from the 401 block upward (§4 below); write any digits you like
(`999` is a common placeholder choice), they are discarded.

**Why this is a hard, gate-enforced regex and not "close enough":** the
reader (`journey_block` in `journey-lib.sh`) accepts headings permissively
(`^## <id>([^0-9]|$)`), but the id-rewrite step (§4 below) substitutes only
on the canonical spaced form (`^## <id> `). A glued heading — `##
JOURNEY-999—"title"` (em-dash or hyphen glued directly to the digits, no
space) — would pass every read/field check, silently no-op the rewrite, and
land in the map under the placeholder id with an empty success line at exit
0 (V-T5 F1, a real bug this contract closes). `ENTRY_HEADING_INVALID`
catches it before any write.

### 2.2 Required fields

The entry block carries the same field set `lint-journey-map.sh` validates
for any `JOURNEY_MAP.md` block (`JOURNEY_MAP.template.md`'s full schema —
`priority`, `covers`, `flows`, `oracle`, `steps`, `test`, `runner`, ...),
plus three fields this gate tightens specifically because the entry is
REALITY:

| Field | Required value | Why |
|---|---|---|
| `origin:` | exactly `REALITY` | this gate exists only to capture confirmed real failures — no other origin belongs here |
| `author_status:` | exactly `UNWRITTEN` | a REALITY journey is captured before its regression test is written, same convention as every other origin |
| `evidence:` | non-empty, and not the literal `[]` | **the WHY**: a REALITY journey exists BECAUSE of a confirmed real failure. Evidence carries the bug/incident/support-ticket/log references that made this a REALITY entry in the first place — a REALITY entry with no evidence has nothing distinguishing it from a guess, and the whole point of this origin is that it isn't one. (Contrast `PERSONA`/`SIMULATOR` journeys, where evidence may legitimately be blank — a REALITY entry is the one origin where it is load-bearing.) |

The general schema (enum values for `priority`, `oracle_surface`, etc.) is
NOT re-validated by this gate directly — it is proven once, by composing
`lint-journey-map.sh` on the fully-assembled temp map (§4 below), so the
entry-specific checks above and the general schema can never silently
disagree about what a valid value looks like.

---

## 3. The closed code list (verify against the script)

POSIX `sh` against stock `/bin/sh`, fail-closed, `CODE: message` (or a bare
`CODE` prefix) on stderr, non-zero exit on any violation. Every violation
in step 4 of the ceremony below (heading, origin, author_status, evidence)
accumulates fail-slow — all four run before refusing, never short-circuits
on the first.

- `APPROVE_REQUIRED` — `--approve` absent. Refuses before any other work:
  nothing is read (not even a file-existence check), nothing is written
  (house rule 7).
- `NO_ENTRY_BLOCK` — `ENTRY_FILE` has zero `## JOURNEY-<n>` blocks
  (anti-vacuous — exactly one is required).
- `MULTIPLE_BLOCKS` — `ENTRY_FILE` has more than one `## JOURNEY-<n>`
  block.
- `ENTRY_HEADING_INVALID` — the entry heading is not the canonical
  `## JOURNEY-<digits> — "<title>"` form (§2.1 above).
- `ORIGIN_NOT_REALITY` — the entry's `origin:` is not exactly `REALITY`.
- `AUTHOR_STATUS_NOT_UNWRITTEN` — the entry's `author_status:` is not
  exactly `UNWRITTEN`.
- `EVIDENCE_EMPTY` — the entry's `evidence:` is blank or the literal `[]`.
- `DUPLICATE_JOURNEY: entry matches <journey-id>` — the entry's normalized
  `covers:` + `oracle:` collide with an existing map journey (§5 below);
  message directs the operator to attach the regression to the existing
  journey instead of minting a new one.
- `LINT_FAILED` — the temp map (existing `MAP` + the new entry) failed
  `lint-journey-map.sh`'s own self-check; the composed lint's own
  diagnostic (a bad enum value, a smuggled runtime-truth field, ...) prints
  first, this gate's own `LINT_FAILED` line wraps it.

That is 9 codes total. Usage error, or `MAP`/`ENTRY_FILE` missing: exit 2
(house convention, matches `lint-journey-map.sh`). Any code above: exit 1.
Success: exit 0.

This gate never touches runtime fields, the CI-owned ledger, or
`JOURNEY_INBOX.md` — it reads and writes `MAP` only.

---

## 4. Id assignment and the `<n>` placeholder

Ids are assigned **401 upward**, skipping any id already present in `MAP`
(the same next-free idiom `journey-inbox-triage.sh` uses for its own
301-block, and `persona-run.sh` for PERSONA journeys) — REALITY is base
401, distinct from SIMULATOR's 301 and PERSONA's 101, so all three origins'
ids can never collide even when triaged/intaken in any order.

If the entry's `test:` field value contains the literal placeholder token
`<n>` (the author cannot know the future assigned id at write time), ONLY
that token is substituted with the assigned numeric id —
`tests/journeys/journey-<n>.spec.ts` becomes
`tests/journeys/journey-401.spec.ts`. A `test:` value with no `<n>` token
at all copies through byte-identical (mirrors commit 4b08dcb,
`journey-inbox-triage.sh`'s identical convention). Nothing else in the
block is rewritten or forced — the checks in §2.2 already proved
`origin`/`author_status`/`evidence` are exactly what this gate requires, so
every other field (`priority`, `covers`, `steps`, `oracle`, ...) lands
unchanged from what the author wrote.

---

## 5. Dedup semantics

Before any write, the entry's `covers:` and `oracle:` are normalized via
the SAME shared `journey-lib.sh` accessors (`norm_covers`/`norm_oracle`)
`journey-inbox-triage.sh` uses for its own dedup — never a forked
implementation, so the two gates can never disagree about what counts as a
duplicate. A match on **both** keys against an existing `MAP` journey
(any origin) is `DUPLICATE_JOURNEY`, whole-run refusal: the operator is
directed to attach the regression as evidence on the existing journey
instead of minting a duplicate one. All matches accumulate (fail-slow); any
match refuses the whole run.

---

## 6. The ceremony — who runs `--approve`, and when

`--approve` gates everything (house rule 7): absent, the gate refuses
before reading or writing anything at all — `APPROVE_REQUIRED`. The flag
may appear in any argument position (mirrors
`journey-inbox-triage.sh`/`uat-report-promote.sh`).

The ceremony this gate serves is `Step 5.txt` Part B's **WORKFLOW BUG**
rule (journey-granularity regression-test lift, spec §5.3): when an
incoming bug is a failure in a user-facing multi-step flow — not a pure
internal defect — the fix cannot close until, in order:

1. a `JOURNEY-<n>` covering the failing workflow exists in
   `JOURNEY_MAP.md`. A NEW workflow failure mints one via
   `sh journey/bin/journey-reality-intake.sh JOURNEY_MAP.md <entry-file>
   --approve` (origin `REALITY`, evidence carrying the bug/incident refs)
   — **or** a `JOURNEY-EXEMPT: <reason>` is logged as debt (owner +
   expiry, house exemption style), when minting a journey is genuinely not
   applicable.
2. a deterministic journey test reproduces the bug or encodes the missing
   workflow.
3. the test fails before the fix (or is technically impossible, with the
   exemption logged).
4. the test passes after the fix.
5. runtime truth for that journey lands only via the CI ledger — this
   layer (the report/citation layer) never marks anything green by
   assertion.

The human running `--approve` here is the same maintenance engineer who
classified the incoming bug as a WORKFLOW BUG in Step 5's intake — the
approval is the human act of confirming "yes, this real failure deserves a
canonical journey," not an automatic consequence of writing the entry file.
`journey-reality-intake.sh` itself never infers approval from anything else
— no gate success elsewhere substitutes for the flag.

---

## 7. Worked example — a valid entry

```
## JOURNEY-999 — "Receptionist double-books room 3 because the conflict warning fires only after save"
origin: REALITY
priority: P1
covers: FEAT-014
flows: [AFJ-003]
persona: P1 (low-tech impatient receptionist)
goal: book a room without double-booking it
oracle_surface: UI+API
negative_states: double_submit
data_fixtures: []
steps:
  1. open the booking form for room 3
  2. submit a booking that conflicts with an existing one
  3. observe no warning until AFTER the save completes → double_submit
oracle: room 3's booking list shows exactly one entry for the conflicting slot
evidence: incident T-4411, server log excerpt confirming duplicate INSERT
test: tests/journeys/journey-<n>.spec.ts
runner: playwright
author_status: UNWRITTEN
exemptions: []
```

Run with `sh journey/bin/journey-reality-intake.sh JOURNEY_MAP.md
entry.md --approve`. On success: `INTAKE: JOURNEY-401 — "Receptionist
double-books room 3 because the conflict warning fires only after save"`
on stderr (the heading id reassigned from the `999` placeholder to the
next-free 401 id; `journey-401.spec.ts` substituted for the `<n>` token in
`test:`), exit 0. Re-running the identical entry a second time refuses —
`DUPLICATE_JOURNEY: entry matches JOURNEY-401` — the map stays
byte-unchanged.

---

## 8. What this gate deliberately does not do

- It does not write `JOURNEY_INBOX.md` or read it — REALITY and SIMULATOR
  are entirely separate capture paths (§1).
- It does not write a regression test, and does not check that one exists
  — `author_status: UNWRITTEN` is enforced, and the ceremony in §6 is what
  requires a test to follow, but writing it is a separate, later step.
- It does not touch the CI-owned ledger or any runtime-truth field —
  composition with `lint-journey-map.sh` (Check 3) rejects a smuggled
  runtime field via `LINT_FAILED`, this gate carries no direct check of its
  own for that class (precedent: `journey-inbox-triage.sh` does the same).
- It does not re-validate the general `JOURNEY_MAP.md` schema itself
  (enum values, cross-field consistency) beyond the three REALITY-specific
  tightenings in §2.2 — that is `lint-journey-map.sh`'s job, composed as an
  executable, never re-implemented.
