# UAT report format + verifier — contract

Operator-facing contract for the UAT report layer: how a browser-UAT gap
report is written, graded, machine-verified, and — only after a human
approves it — cited downstream. Sibling of
`journey/docs/journey-gen-doc-format.md`; same house style.

---

## 1. Purpose

Browser UAT is agent prose: an agent drives the app and writes down what it
saw. In the framework's first field run, the generated gap report claimed
the browser-UAT auth/dev-auth token bridge was missing when it existed in
code (`ENABLE_DEV_AUTH_BYPASS` et al.) but was merely unconfigured, and it
claimed stale route expectations against journeys that had already moved
on. Nothing in the framework graded those claims or forced evidence, so the
overstatements flowed toward the handover fix list unchecked until a human
re-verified every one of them by hand (GAPS.txt). Per the first law —
nothing is true because an agent said it — this layer mechanizes that hand
pass: a claim grammar that requires evidence, deterministic gates that
re-verify every citation against a pinned commit before any model is spent,
and a code-reading verifier for everything the gates cannot settle alone.

---

## 2. The report

A UAT report is one file, `UAT_REPORT_<YYYY-MM-DD>[-<n>].md`, one per
browser-UAT pass. It carries a required header block, free narrative prose
(no authority), and one or more claim blocks — the only load-bearing
content in the file.

### 2.1 Header

```
# UAT-REPORT
report_date: 2026-07-08
repo_commit: <full 40-hex sha of the app repo state the claims are about>
app_target: http://127.0.0.1:3002
```

- The FIRST LINE of the file must be exactly `# UAT-REPORT`.
- `report_date` must be a valid `YYYY-MM-DD` and must equal the filename
  date.
- `repo_commit` must be a full 40-hex sha — the pinned commit every claim in
  the report is checked against.
- Same-day reruns append `-<n>` (n >= 2) to the filename; the header date is
  unchanged.
- Free prose (narrative, status matrices) is allowed anywhere in the file,
  but ONLY claim blocks carry authority — an assertion outside a claim
  block is not a claim and cannot be cited.

### 2.2 Claim grammar

One block per gap:

```
## UAT-CLAIM-<n>: <title>
- journey_ids: JOURNEY-106, JOURNEY-107        (or [none: <reason>])
- grade: [C] | [C-absent] | [I] | [G] | [X]
- claim: <one-sentence assertion>
- evidence: <path>:<line> — "<verbatim single-line quote>"
- evidence: artifact <relpath> sha256:<64hex>
- search: grep -rFn -- "<literal>" <relpath>
- sample: <n> instances
- oracle_clause: JOURNEY-<n>#<k>
```

- `## UAT-CLAIM-<n>: <title>` ids are unique within the report; `<n>` is a
  positive integer.
- `- claim: <one-sentence assertion>` is required on every block — a block
  missing it is rejected (see the `HEADER_MISSING` reuse note under gate
  4.1 below).
- Quote evidence: `<path>` is repo-relative (no leading `/`, no `..`
  segments); `<line>` is a positive integer; the quote is single-line,
  extracted as the text between the FIRST `"` after the em-dash and the
  LAST `"` on the line (embedded quotes survive).
- Artifact evidence: `<relpath>` resolves relative to the report's own
  directory; a `sha256:<64hex>` of the artifact's bytes is required.
- Search lines: `grep -rFn -- "<literal>" <relpath>` only. `<literal>` is a
  non-empty fixed string — no `"`, no backslash — matched with `grep -F`
  semantics (no regex); `<relpath>` is repo-relative with no metacharacters
  or whitespace. Multiple search lines are allowed and each is
  independently re-executed.
- `- oracle_clause: JOURNEY-<n>#<k>` is OPTIONAL (spec G4, oracle
  observability classes). `<k>` is a 1-based, positive-integer index into
  the named journey's own ` AND `-split `oracle:` clauses on
  `JOURNEY_MAP.md`. `lint-uat-report.sh` (gate 4.1) checks this field's
  FORMAT only; `check-uat-oracle-scope.sh` (§5.8 below) is the gate that
  resolves the reference against the map and adjudicates scope — a claim
  with no `- oracle_clause:` line at all is untouched by either check
  beyond format (there is nothing to check).

### 2.3 Worked example — the golden fixture

`journey/tests/fixtures/uat/golden/UAT_REPORT_2026-07-08.md`, byte-for-byte,
exercising all five grades:

```
# UAT-REPORT
report_date: 2026-07-08
repo_commit: 0123456789012345678901234567890123456789
app_target: http://127.0.0.1:3002

Narrative prose is allowed here and carries no authority.

## UAT-CLAIM-1: Send action surfaced HTTP 500
- journey_ids: JOURNEY-106
- grade: [C]
- claim: Clicking Send on the PDA screen returned HTTP 500 to the user.
- evidence: src/pda/send.ts:12 — "throw new Error('portal timeout')"
- evidence: artifact evidence/journey-106-send-500.png sha256:4d3c2b1a4d3c2b1a4d3c2b1a4d3c2b1a4d3c2b1a4d3c2b1a4d3c2b1a4d3c2b1a

## UAT-CLAIM-2: No dev-auth bypass exists for UAT
- journey_ids: JOURNEY-106, JOURNEY-107
- grade: [C-absent]
- claim: The app has no development auth bypass usable for browser UAT.
- search: grep -rFn -- "PORTAL_MAGIC_BYPASS" config/

## UAT-CLAIM-3: Docs promise CSV export but code rejects it
- journey_ids: JOURNEY-109
- grade: [X]
- claim: PRD says invoices export to CSV; the export handler rejects csv.
- evidence: docs/PRD.md:8 — "invoices can be exported as CSV"
- evidence: src/export.ts:22 — "if (fmt === 'csv') reject()"

## UAT-CLAIM-4: Save errors likely redirect without message
- journey_ids: JOURNEY-114
- grade: [I]
- claim: Admin save failures redirect with a query flag and no visible error.
- evidence: artifact evidence/journey-114-save-error.png sha256:1a2b3c4d1a2b3c4d1a2b3c4d1a2b3c4d1a2b3c4d1a2b3c4d1a2b3c4d1a2b3c4d
- sample: 4 instances

## UAT-CLAIM-5: Tariff editor data source undetermined
- journey_ids: JOURNEY-113
- grade: [G]
- claim: Cannot determine from the browser whether tariff data load uses the versioned register.
```

---

## 3. Grades

Reuses Step 0's grade vocabulary verbatim (`Step 0.txt`) — the first use of
that vocabulary outside Step 0:

- `[C]` CONFIRMED — direct evidence at file:line (or, in this layer only,
  an artifact). Nothing is `[C]` without evidence.
- `[C-absent]` — confirmed absence: the claim is that something does NOT
  exist in the code, backed by a stated search that found nothing.
- `[I]` INFERRED — supported by a recurring pattern, sample size stated
  (n >= 3; fewer than 3 instances is `[G]`, per Step 0 law).
- `[G]` GAP — cannot be determined safely from the browser or the code.
  Recorded, never guessed.
- `[X]` CONTRADICTED — documentation/UI says one thing, code does another.

UAT-specific evidence-count rules (lint-enforced, gate 4.1):

- `[C]` requires >= 1 evidence line of EITHER kind — a code quote or an
  artifact. Runtime observations like "Send surfaced HTTP 500" are
  legitimately `[C]` on artifact evidence alone: a screenshot or log of
  what the browser showed. See the artifact-evidence seam immediately below
  for exactly what that kind of evidence does and does not prove.
- `[X]` requires >= 2 evidence lines — both sides of the contradiction.
  Lint proves the evidence COUNT (>= 2) only: it does not, and cannot,
  adjudicate that one evidence line is really the "doc side" and the other
  the "code side" of a genuine contradiction — that judgment is
  verifier-adjudicated, not lint-proven. This is a stated seam, not an
  oversight.
- `[C-absent]` requires >= 1 search line.
- `[I]` requires a `- sample: <n> instances` line with n >= 3.

**The artifact-evidence seam:** a `sha256` binds the artifact's BYTES, not
its MEANING — a screenshot proves nothing about what it depicts beyond its
own existence and byte-for-byte unaltered-ness since the claim was written.
A claim graded `[C]` on artifact evidence alone rests on a runtime
observation that code reading can neither prove nor disprove; only the
code-checkable slice of a report is ever adjudicated by these gates or by
the verifier.

---

## 4. The verification

Paired to the report by basename: `UAT_REPORT_2026-07-08.md` →
`UAT_REPORT_2026-07-08.verification.md`. Its first TWO lines are stamped by
the runner into a temp file that gate 4.3 then re-checks before the
rename — neither is ever written by the model (see §5.6):

```
reviewed_sha256: <sha256 of the report file>
repo_root: <absolute physical path of REPO_ROOT>
```

`repo_root` (line 2, fix-wave W1/D2) is the runner's own `REPO_ROOT`
argument resolved to an absolute PHYSICAL path (`cd` + `pwd -P` — symlinks
resolved, never a relative or symlinked string trusted verbatim). Gate 4.3
resolves its own `<repo_root>` argument the identical way and requires an
exact match; before this line existed, a live agentic backend launched from
the wrong working directory could confidently reason about an entirely
different repository and nothing would notice — the report's own
`repo_commit` pin only proves the WORKING TREE matched at runner-precondition
time, never which filesystem path the model actually read from.

Then exactly one verdict block per claim — silence is not a review:

```
UAT-VERDICT: UAT-CLAIM-<n>
- verdict: confirm | downgrade | refute
- regrade: <grade>                     (downgrade only; must differ)
- reason: <one sentence>
- evidence: <path>:<line> — "<quote>"  (required when the verdict asserts code reality)
- search: grep -rFn -- "<literal>" <relpath>   (required when confirming an absence)
- residual: <one sentence>             (optional, refute/downgrade only)
- checked_hash: <echoed sha>
```

- `- search:` lines are legal ONLY on a `confirm` verdict of a `[C-absent]`
  claim: anywhere else, any `- search:` line at all is `SEARCH_FORMAT`; a
  `confirm` of `[C-absent]` with none at all is `ABSENCE_NO_SEARCH`. A
  refute of a claimed absence carries its proof as a quote-evidence line
  instead of a search line.
- **Every `refute` or `downgrade` verdict requires >= 1 `- evidence:` line**
  (fix-wave W2/D3-a) — a verdict that asserts something IS or IS NOT true of
  code reality must cite code reality it can point to; anything less is
  `CITATION_MISSING`. `confirm` is unchanged. Report-internal deficiencies
  (sample counts, formatting, missing fields) are LINT's jurisdiction (gate
  4.1) — never a legitimate reason to downgrade or refute a claim.
- `- residual:` is an explicitly-unverified hypothesis about the true cause
  when a claim is false as written but points at something real. It is
  forbidden on `confirm` (`RESIDUAL_ON_CONFIRM`), and it must say plainly
  that it is unverified; it carries no authority of its own.
- `- checked_hash:` echoes the `CHECKED_HASH:` value the verifier was
  handed; the gate recomputes the report's hash independently every time
  and requires an exact match, on the header line and on every echoed
  value.

### 4.1 The promotion marker

Written only by `uat-report-promote.sh --approve`, paired by basename
(`<report-basename>.promotion`):

```
report_sha256: <sha256 of the report>
verification_sha256: <sha256 of the verification file>
approved: yes
```

No timestamps anywhere — nothing in this layer depends on wall-clock.
Re-runs overwrite the report/verification/promotion trio in place; git
history is the audit trail of what used to be there.

### 4.2 The convergence loop

Author writes or edits the report → lint (4.1) + evidence (4.2) gates → a
verifier pass → the verification gate (4.3) → if any verdict is `refute` or
`downgrade`, the author fixes the report: editing a claim, accepting a
regrade, or **deleting the claim outright — deletion is a legitimate
resolution; the report simply asserts less afterward** → the edit changes
the report's hash → the old verification is stale by construction
(`STALE_VERIFICATION` on the next gate run) → a fresh verifier pass is
required → once every verdict is `confirm`, a human runs
`uat-report-promote.sh --approve` → `check-uat-citation.sh` goes green.

---

## 5. Gates

All in `journey/bin/` (plus the runner in `journey/gen/runners/`), POSIX
`sh` against stock `/bin/sh`, fail-closed, `CODE: message` on stderr, exit
non-zero. Shared parse/hash/pinned-commit-search helpers live in
`journey/lib/uat-lib.sh`. Every repo read in every gate is against the
**pinned commit** named by the report's `repo_commit` — never the working
tree.

### 5.1 `lint-uat-report.sh <report>` — gate 4.1

Schema only, no repo access:

- First line must be exactly `# UAT-REPORT`.
- Header fields present: `report_date`, `repo_commit` (40-hex),
  `app_target`.
- `report_date` is `YYYY-MM-DD` and the filename matches
  `UAT_REPORT_<date>[-<n>].md`.
- At least one `## UAT-CLAIM-<n>:` block exists; claim ids are unique.
- Every claim's `grade` is one of the five tokens.
- Every claim has a `- claim: ` line.
- Every evidence line (quote or artifact) is well-formed; quote-line paths
  are repo-relative.
- Every search line matches the restricted
  `grep -rFn -- "<literal>" <relpath>` grammar, wherever it appears.
- Per-grade minimum evidence: `[C]` >= 1 evidence line (either kind); `[X]`
  >= 2 evidence lines (count only — see the Grades §3 seam above);
  `[C-absent]` >= 1 search line; `[I]` a `- sample: <n> instances` line
  with n >= 3.
- Every `- oracle_clause: <ref>` line (OPTIONAL, spec G4), wherever it
  appears, matches `JOURNEY-<digits>#<positive-int>`. This is a FORMAT
  check only — no journey-map lookup, no scope adjudication; a report with
  no `- oracle_clause:` lines at all is unaffected (zero new behavior).

Codes: `HEADER_MISSING` `DATE_INVALID` `NO_CLAIMS` `DUPLICATE_CLAIM_ID`
`GRADE_UNKNOWN` `CLAIM_NO_EVIDENCE` `CONTRADICTION_ONE_SIDED`
`ABSENCE_NO_SEARCH` `SAMPLE_MISSING` `SAMPLE_TOO_SMALL` `EVIDENCE_FORMAT`
`SEARCH_FORMAT` `ORACLE_CLAUSE_FORMAT`.

**Reuse note:** a missing `- claim: ` line inside an otherwise well-formed
claim block is reported as `HEADER_MISSING` (message: "missing claim
line") — the same code used for the file-level header checks. There is no
dedicated per-claim code for this.

### 5.2 `check-uat-evidence.sh <report> <repo_root>` — gate 4.2

Verifies the AUTHOR's evidence before any model run is spent. All reads
pinned to the report's `repo_commit`; the working tree is never read:

- `repo_commit` resolves to a real commit in `<repo_root>`. HEAD equality
  and tree cleanliness are deliberately NOT required here — every read
  below is against the pinned commit, so a report about commit X stays
  verifiable (and citable) after the project advances past X.
- Every quote evidence line: the cited path exists at the pinned commit;
  the quote (whitespace-normalized both sides) is a substring of the
  content of the cited LINE — wrong line is a distinct code from
  not-found-anywhere.
- Every artifact evidence line: the file exists relative to the report's
  own directory; its sha256 matches the cited hash.
- Every search line: the relpath exists at the pinned commit; the search is
  re-executed as `git grep -Fn -e "<literal>" <commit> -- "<relpath>"`
  (argv-only, never eval/sh -c); a match found under a `[C-absent]` claim
  is a divergence.
- Fails closed if no sha256 tool is on PATH — never a silent pass.

Codes: `COMMIT_UNKNOWN` `QUOTE_UNVERIFIED` `LINE_MISMATCH`
`ARTIFACT_MISSING` `ARTIFACT_HASH_MISMATCH` `SEARCH_ERROR`
`SEARCH_DIVERGED` `TOOL_MISSING` `MKTEMP_FAILED`.

### 5.3 `check-uat-verification.sh <report> <verification> <repo_root>` — gate 4.3

The verifier's own evidence held to the identical discipline as gate 4.2,
plus hash-bound verdict coverage:

- `repo_commit` resolves in `<repo_root>` (same precondition as 4.2 — this
  gate is safe to run standalone, not only after 4.2).
- The verification file's FIRST LINE must be exactly
  `reviewed_sha256: <sha of the report, recomputed>` — never trusted from
  the file, always recomputed.
- The verification file's SECOND LINE must be exactly
  `repo_root: <resolved path>`, where `<resolved path>` is the gate's OWN
  `<repo_root>` argument resolved to an absolute physical path via `cd` +
  `pwd -P` (fix-wave W1/D2) — never trusted from the file, always
  re-resolved. A missing line 2 or a line 2 that resolves to a different
  physical path is `ROOT_MISMATCH` (the message text distinguishes
  "missing" from "mismatched"). Physical resolution means a relative
  `<repo_root>` argument and a symlinked one that both point at the same
  real directory compare equal.
- Every `- checked_hash:` line in every verdict block must equal that same
  recomputed hash.
- Exactly one verdict block per report claim id — membership (does the id
  even exist in the report) is checked BEFORE coverage (is every claim
  covered), so an id that doesn't exist in the report gets the more
  specific diagnosis.
- `- verdict:` vocabulary is exactly `confirm | downgrade | refute`.
- `downgrade` requires a `- regrade:` that is one of the five grade tokens
  AND differs from the claim's own author-assigned grade.
- **`refute` or `downgrade` requires >= 1 `- evidence:` line** (fix-wave
  W2/D3-a) — `CITATION_MISSING` otherwise. `confirm` is unchanged.
- `- residual:` is forbidden on a `confirm` verdict.
- Every `- evidence:` line in a verdict is checked exactly like gate 4.2's
  quote checker, against the same pinned commit.
- `- search:` lines are legal ONLY on a `confirm` verdict of a
  `[C-absent]` claim (>= 1 required there, and each is re-executed exactly
  like gate 4.2's search checker); anywhere else, any `- search:` line at
  all is rejected. A search relpath of `.` (the whole tree) is supported
  (fix-wave W3/D3-b — the existence pre-check special-cases the git
  root-tree syntax `<commit>:` rather than the non-working `<commit>:.`).

Codes: `STALE_VERIFICATION` `VERDICT_INCOMPLETE` `DUPLICATE_VERDICT`
`UNKNOWN_CLAIM` `VERDICT_UNKNOWN` `REGRADE_MISSING` `RESIDUAL_ON_CONFIRM`
`SEARCH_FORMAT` `ABSENCE_NO_SEARCH` `COMMIT_UNKNOWN` `TOOL_MISSING`
`MKTEMP_FAILED` `ROOT_MISMATCH` `CITATION_MISSING`, plus
reused `QUOTE_UNVERIFIED` `LINE_MISMATCH` `SEARCH_ERROR` `SEARCH_DIVERGED`
from the shared pinned-commit checkers gate 4.2 also uses.

**Doc-vs-spec note:** `SEARCH_FORMAT` and `ABSENCE_NO_SEARCH` are both
real, implemented codes on this gate — a `- search:` line outside a
`confirm`-of-`[C-absent]` verdict, and a `confirm`-of-`[C-absent]` verdict
carrying none, respectively. The original design spec's §4.3 code
enumeration did not name either one explicitly. The code as shipped is the
source of truth; this doc follows the code, not the spec text, here.

### 5.4 `uat-report-promote.sh <report> <repo_root> --approve` — gate 4.4

The human trust elevation (O2), matching the `journey-gen-promote.sh` /
`journey-test-promote.sh` ceremony. `--approve` may appear in any argument
position. Refuses BEFORE any other work — nothing is read, nothing is
written — when `--approve` is absent. With `--approve`:

- Re-runs gates 4.1 and 4.2 in full, as executables (never re-implemented).
- Requires a verification file to exist at all, then re-runs gate 4.3 in
  full against it.
- Requires zero `refute`/`downgrade` verdicts — every verdict must be
  `confirm`.
- Requires >= 1 claim graded `[C]`, `[C-absent]`, or `[X]` in the report —
  a report of only `[G]`/`[I]` claims has nothing evidenced to promote.
- Writes the promotion marker only after all of the above hold, via a temp
  file + trap + `mv` — on any failure nothing new exists on disk.

Codes (own): `VERIFICATION_MISSING` `NON_CONFIRM_VERDICT`
`NO_EVIDENCED_CLAIMS`. It also directly emits `TOOL_MISSING` if its own
sha256 calls fail, plus whatever `lint-uat-report.sh` /
`check-uat-evidence.sh` / `check-uat-verification.sh` pass through.

### 5.5 `check-uat-citation.sh <report> <repo_root>` — gate 4.5

The authority check a downstream consumer runs. Green ONLY when: the
promotion marker exists, both of its recorded hashes match recomputed
reality right now, and gates 4.1 + 4.2 + 4.3 (composed as executables) pass
right now. It never trusts the marker alone — it re-verifies every time. On
success it prints exactly `UAT-CITATION: green <report_sha256>` to stdout.

Codes (own): `PROMOTION_MISSING` `PROMOTION_STALE`. It also directly emits
`TOOL_MISSING` if its own sha256 calls fail, plus pass-through of gates
4.1/4.2/4.3.

### 5.6 `uat-verify-run.sh <report> <repo_root>` — opt-in verifier runner (§5.2)

Usage: `RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> uat-verify-run.sh <report> <repo_root>`.

- **SKIP behavior:** `RUN_LLM_GEN` unset → deterministic no-op — prints a
  SKIP message, exit 0, invokes no model and no network.
- `RUN_LLM_GEN=1` without `JOURNEY_GEN_BACKEND` set → fails closed, exit 1,
  no network.
- With both set: checks the report file exists first (before any hashing);
  resolves `<repo_root>` to an absolute PHYSICAL path (`cd` + `pwd -P` —
  fix-wave W1/D2, never the raw, possibly-relative or symlinked argument),
  then checks that resolved root's HEAD equals the report's `repo_commit`
  and the working tree is clean — BOTH preconditions run BEFORE any backend
  call, so the live agent's view of the tree provably equals the pinned
  commit the gates check.
- Computes the report's sha256 itself (never trusts the model to compute
  it), hands the backend one file: `CHECKED_HASH: <sha>`, then
  `REPO_ROOT: <abs path>` (fix-wave W1/D2 — the resolved physical path,
  IN-BAND, never an ambient convention the backend must already know), then
  the report verbatim.
- Stamps `reviewed_sha256:` and `repo_root:` itself into a scratch temp
  file ahead of the backend's raw output (never trusts the model to echo
  either as the file's own header lines), then runs gate 4.3
  (`check-uat-verification.sh`) against that temp file.
- Only after gate 4.3 passes are the temp files renamed (`mv`) into their
  final `<report-basename>.verification.md` /
  `<report-basename>.verifier-raw.md` names — write-then-rename; a trap
  cleans up every temp file on any exit, so on any failure path nothing
  with those final names ever exists on disk.

Codes (own): `MISSING-REPORT` `REPO_MISMATCH` `TREE_DIRTY`
`MKTEMP_FAILED` `WRITE_FAILED` `BACKEND_FAILED`. Plus pass-through: the
prompt's own degenerate-input tokens `MISSING-REPORT` / `MISSING-HASH` /
`MISSING-ROOT` (the model declaring it received no usable report, no
`CHECKED_HASH:` line, or no `REPO_ROOT:` line — fix-wave W1/D2), whatever
`check-uat-verification.sh` emits, and `TOOL_MISSING` from its own
`uat_sha256` call.

### 5.7 `check-uat-preconditions.sh PATH_TO_MAP` — the UAT run preflight (spec G1)

The gate the field run was missing: a whole browser-UAT pass once burned
wall-clock time on 401s because an existing dev-auth bridge was
unconfigured — nothing checked declared preconditions before the run. This
gate preflights the `preconditions:` block field on `JOURNEY_MAP.md`
(grammar defined and validated by `lint-journey-map.sh` Check 8: the
`preconditions:` line followed by one or more indented `  - <kind>: <value>`
entries, kind in `{auth, env, data, state}`) before a UAT pass starts.

**TRUST STATEMENT:** this gate checks DECLARED preconditions only. A
journey with no `preconditions:` block at all is invisible to it — the
anti-vacuous `NO_PRECONDITIONS` check below is the only backstop for a map
that should have declared preconditions but doesn't.

Semantics:

1. Exactly one positional arg (the map path). Wrong arg count or a missing
   map file exits 2 (matching `lint-journey-map.sh`'s own convention), not
   1 — these are usage errors, not gate violations.
2. Composes `lint-journey-map.sh` FIRST, as an executable (never
   re-implemented), the same composition style `uat-report-promote.sh` uses
   for its own sub-gates. Non-zero → `LINT_FAILED` and exit 1. Grammar is
   lint's job, not this gate's — this gate trusts a lint-clean map.
3. Parses every journey block's `preconditions:` entries using
   `journey/lib/journey-lib.sh` accessors plus the identical awk
   block-extraction idiom `lint-journey-map.sh` Check 8 uses, so the two
   can never disagree about what a `preconditions:` block contains.
4. Anti-vacuous law (same law as `NO_SURFACE_BLOCKS` / `NO_CLAIMS`
   elsewhere in this framework — an invoked gate never passes vacuously):
   zero preconditions entries anywhere in the whole map → `NO_PRECONDITIONS`
   and exit 1.
5. STATIC checks (always run, no opt-in required): every `env:` entry's
   named environment variable must be set and non-empty in the gate's own
   environment, else `PRECONDITION_ENV_UNSET: <id>: <name>`. All violations
   are accumulated (fail-slow); exit 1 at the end if any.
6. PROBE checks for `auth`/`data`/`state` entries — opt-in only:
   - Default (`RUN_UAT_PREFLIGHT` unset or != `1`): no live probe runs. An
     explicit `SKIP: live probes not run (RUN_UAT_PREFLIGHT not set); <n>
     auth/state/data precondition(s) UNPROBED` line is always printed —
     never a silent skip. Exit 0 if the static checks passed.
   - `RUN_UAT_PREFLIGHT=1`: opt-in is explicit, so a missing probe
     dependency FAILS LOUD rather than skipping: `UAT_PREFLIGHT_PROBE` must
     be set, non-empty, and an executable file, else `PROBE_MISSING` and
     exit 1. Probe contract: a single executable, invoked once per
     `auth`/`data`/`state` entry as `"$UAT_PREFLIGHT_PROBE" <kind> <value>`
     — exit 0 means met, non-zero means unmet. `env:` entries are never
     probed (the static check in step 5 already covers them). Each unmet
     entry accumulates `PRECONDITION_UNMET: <id>: <kind>: <value>`; exit 1
     at the end if any.
7. Success: a one-line summary of checked counts, exit 0.

Codes (own): `LINT_FAILED` `NO_PRECONDITIONS` `PRECONDITION_ENV_UNSET`
`PROBE_MISSING` `PRECONDITION_UNMET`, plus usage/missing-map-file exit 2
(no code token — matches `lint-journey-map.sh`'s own usage-error
convention).

### 5.8 `check-uat-oracle-scope.sh <report> <journey_map>` — the false-gap killer (spec G4)

The gate a real browser-UAT pass was missing: oracle clauses that are only
verifiable BELOW the browser (hash computation, exclusion logic — the kind
of thing unit/integration tests cover) were reported as false "gaps"
because nothing classified a clause as browser-observable vs lower-level.
A human had to hand-verify every one of them. This gate makes that
classification machine-checkable: `JOURNEY_MAP.md`'s optional
`oracle_classes:` field (`lint-journey-map.sh` Check 9 — grammar: class
tokens `browser`/`lower` joined by literal ` AND `, positionally matching
`oracle:`'s own ` AND `-split clauses) plus a report claim's optional
`- oracle_clause: JOURNEY-<n>#<k>` reference (§2.2, §5.1 above) together
let this gate reject a `[C-absent]` claim that cites a `lower`-classed
clause as a browser gap — the false-gap killer.

**TRUST STATEMENT:** adjudication exists ONLY for claims that carry an
`- oracle_clause:` ref. A claim with no ref at all is invisible to the
per-claim adjudication below — the anti-vacuous `NO_CLAUSE_REFS` check is
the only backstop for a report that should have carried refs but doesn't.

Semantics:

1. Exactly two positional args (report, then journey map). Wrong arg count
   or either input file missing exits 2 (matching `lint-journey-map.sh` /
   `check-uat-preconditions.sh`'s own usage-error convention), not 1.
2. Composes `lint-journey-map.sh` FIRST, as an executable (never
   re-implemented), the same composition style `check-uat-preconditions.sh`
   uses for itself. Non-zero → `LINT_FAILED` and exit 1. The
   `oracle_classes:` GRAMMAR (Check 9: token membership, positional
   clause-count match) is lint's job, not this gate's — this gate trusts a
   lint-clean map.
3. Parses claim blocks with `journey/lib/uat-lib.sh`'s `uat_claim_ids` /
   `uat_claim_block` — the identical accessors `lint-uat-report.sh` uses —
   plus the `uat_oc_*` reference helpers shared with that gate's own
   `- oracle_clause:` FORMAT check, and resolves journey clauses via
   `journey/lib/journey-lib.sh`'s `journey_field` / `split_and` (the same
   ` AND `-splitter `lint-journey-map.sh` Check 9 uses), so the map side
   and the report side can never disagree about a clause count or a
   positional class.
4. Anti-vacuous law (same law as `NO_PRECONDITIONS` / `NO_SURFACE_BLOCKS` /
   `NO_CLAIMS` elsewhere in this framework — an invoked gate never passes
   vacuously): zero `- oracle_clause: ` lines anywhere in the whole report
   → `NO_CLAUSE_REFS` and exit 1.
5. Every `- oracle_clause:` ref found inside a claim block is fail-closed:
   - malformed (not `JOURNEY-<digits>#<positive-int>`) →
     `ORACLE_CLAUSE_FORMAT: UAT-CLAIM-<n>: <ref>`.
   - the journey id is not present in the (lint-clean) map →
     `ORACLE_CLAUSE_UNKNOWN_JOURNEY: UAT-CLAIM-<n>: <id>`.
   - the index `<k>` exceeds that journey's ` AND `-split `oracle:` clause
     count → `ORACLE_CLAUSE_OUT_OF_RANGE: UAT-CLAIM-<n>: <ref>`.
   - the journey has no `oracle_classes:` declared at all →
     `ORACLE_CLASS_UNDECLARED: UAT-CLAIM-<n>: <id>` (fail closed: scope
     cannot be adjudicated without a declaration).
   - **ADJUDICATION** (the false-gap killer): claim `grade` is
     `[C-absent]` AND the referenced clause's class is `lower` →
     `ORACLE_CLASS_OUT_OF_SCOPE: UAT-CLAIM-<n>: <ref> is a lower-level
     clause; a browser UAT absence claim cannot assert it as a gap — route
     to lower-level evidence`. Grades other than `[C-absent]` with a valid
     ref are allowed (positive evidence, e.g. `[C]`, citing a `lower`
     clause is legitimate — the claim isn't asserting an absence).
     `[C-absent]` against a `browser`-classed clause is allowed (a genuine
     browser gap).
6. All violations are accumulated (fail-slow, not fail-fast — a plain
   `for`/heredoc-fed `while` loop, deliberately not a `| while read` pipe:
   a counter-mutation-lost failure inside a pipeline subshell is a known
   fail-open class in this repo, same idiom as `check-uat-preconditions.sh`
   and `lint-journey-map.sh` Checks 8/9). Exit 1 if any violation
   accumulated; else a one-line summary of checked counts, exit 0.

Codes (own): `LINT_FAILED` `NO_CLAUSE_REFS` `ORACLE_CLAUSE_FORMAT`
`ORACLE_CLAUSE_UNKNOWN_JOURNEY` `ORACLE_CLAUSE_OUT_OF_RANGE`
`ORACLE_CLASS_UNDECLARED` `ORACLE_CLASS_OUT_OF_SCOPE`, plus usage/missing-
file exit 2 (no code token — matches `lint-journey-map.sh`'s own
usage-error convention). `ORACLE_CLAUSE_FORMAT` is the same code
`lint-uat-report.sh` (§5.1) emits for the identical malformed-ref case —
shared, not duplicated, because both gates validate the ref grammar with
the exact same `uat_oc_wellformed` helper.

**Out of scope for this gate:** generation pipelines do not emit
`oracle_classes:` in v1 (it is authored by the journey-spec author, same
as `oracle:` itself — see `JOURNEY_MAP.template.md`); this gate does not
write or suggest classifications, only adjudicates declared ones.

### 5.9 `uat-write-run.sh NOTES_FILE EVIDENCE_DIR REPO_ROOT OUTDIR` — opt-in report-WRITER runner (spec DC-7)

Usage: `RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> REPORT_DATE=<YYYY-MM-DD>
[JOURNEY_MAP=<path>] uat-write-run.sh NOTES_FILE EVIDENCE_DIR REPO_ROOT
OUTDIR`. Mechanizes report AUTHORING: raw browser-UAT session notes +
runner-computed evidence hashes go in, one report in the exact §2 grammar
comes out — gated by the SAME checks a hand-written report already had to
clear. `journey/gen/prompts/uat-writer.md` is the model side; this runner
is the disciplined harness around it, mirroring `uat-verify-run.sh` (§5.6)
exactly.

- **SKIP behavior:** `RUN_LLM_GEN` unset → deterministic no-op — prints a
  SKIP message, exit 0, invokes no model and no network.
- `RUN_LLM_GEN=1` without `JOURNEY_GEN_BACKEND` set → fails closed, exit 1,
  no network.
- `REPORT_DATE` is required and must be `YYYY-MM-DD` — checked BEFORE any
  hashing or backend call. This layer never derives dates itself; there is
  no wall-clock anywhere in it.
- `REPO_ROOT` must be a usable git repo with a clean working tree — the
  runner derives `REPO_COMMIT` itself as HEAD's own full sha (never taking
  it from the model), mirroring `uat-verify-run.sh`'s own
  `REPO_MISMATCH`/`TREE_DIRTY` precondition posture: the report pins what
  the tree provably is.
- The bundle handed to the backend carries `REPORT_DATE:`/`REPO_COMMIT:`
  lines (runner-owned facts the model must echo verbatim into the report
  header — never invented, never re-derived), an ARTIFACT MANIFEST (every
  file under `EVIDENCE_DIR`, runner-computed `sha256` — the ONLY artifact
  evidence lines the model may ever emit), the session notes verbatim, and
  — when `JOURNEY_MAP` is set — a JOURNEY MAP EXCERPT.
- Deterministic validation runs BEFORE any final-named file exists: (1) a
  header echo check (the model's `report_date:`/`repo_commit:` must equal
  the runner's own `REPORT_DATE`/`REPO_COMMIT` — a mismatch dies before
  lint even runs; the model never gets authority over pinned facts); (2)
  `lint-uat-report.sh` (§5.1); (3) `check-uat-evidence.sh` (§5.2); (4)
  `check-uat-oracle-scope.sh` (§5.8), composed ONLY when the model's output
  carries any `- oracle_clause:` ref — a ref present with `JOURNEY_MAP`
  unset is a fail-closed precondition, never a silent skip.
- Artifact evidence relpaths are resolved by copying `EVIDENCE_DIR`'s
  contents into an `evidence/` directory that lives alongside the report at
  every stage — inside the scratch dir during validation, and inside
  `OUTDIR` after install — so `check-uat-evidence.sh`'s
  `dirname(report)`-relative resolution rule holds identically before AND
  after the rename, and the installed `OUTDIR` is a self-contained,
  portable artifact independent of `EVIDENCE_DIR`'s original location.
- Only after ALL gates pass: the scratch report is renamed into
  `OUTDIR/UAT_REPORT_<REPORT_DATE>.md`, the raw backend output is installed
  alongside it as `<basename>.writer-raw.md` (mirroring `verifier-raw`,
  §5.6), and the staged `evidence/` directory is merged into
  `OUTDIR/evidence/`. A trap cleans the entire scratch directory on any
  exit — nothing with a final `OUTDIR` name exists on any failure path.
- `WRITER-FAILED: <reason>` in the model's output → loud exit 1, nothing
  installed — the prompt's own degenerate token (`uat-writer.md`), mirroring
  `MISSING-REPORT`/`MISSING-HASH` in `uat-verifier.md`.

This runner mints **no new gate codes** (rule 4: closed enums and code
unions are append-only). Its own preconditions reuse the existing
closed-enum codes wherever the semantics genuinely match — `DATE_INVALID`
(malformed or echo-mismatched `REPORT_DATE`), `REPO_MISMATCH` /
`TREE_DIRTY` (the same two codes `uat-verify-run.sh` uses for the identical
git-repo/clean-tree precondition shape, reused here rather than
duplicated), `TOOL_MISSING`, `MKTEMP_FAILED`, `WRITE_FAILED`,
`BACKEND_FAILED` — plus pass-through of whatever `lint-uat-report.sh` /
`check-uat-evidence.sh` / `check-uat-oracle-scope.sh` emit. Preconditions
with no existing code to reuse (bad usage, a missing `NOTES_FILE` /
`EVIDENCE_DIR`, an `oracle_clause` ref with no `JOURNEY_MAP` set) fail with
a plain `uat-write-run: <reason>` message and no dedicated code token — the
same uncoded-message idiom `uat-verify-run.sh` itself already uses for its
own backend-unset precondition.

### 5.10 `uat-preflight.sh MAP TEST_SURFACE APP_FLOW` — the composed UAT run preflight (spec DC-8)

The single entry command a UAT operator runs before driving the app. Pure
composition, no new logic beyond ordering + reporting: three existing
gates, run in order as EXECUTABLES (never re-implemented), fail-closed,
each step's own diagnostics passed through unchanged —
`lint-journey-map.sh MAP` → `check-surface-staleness.sh TEST_SURFACE
APP_FLOW` (§5.7 above's staleness gate; verified against the shipped gate:
it derives `<TEST_SURFACE>.provenance` itself from `TEST_SURFACE`'s own
path, so there is no separate `PROVENANCE` positional arg here) →
`check-uat-preconditions.sh MAP` (§5.7 above — the 401-burn archetype this
whole chain exists to kill).

First failure: the failing gate's own stderr/stdout prints first (passed
through verbatim), then exactly one line —
`PREFLIGHT_FAILED: step <n> (<gate name>)` — and exit 1; steps after the
first failure never run. All three green: one summary line —
`UAT-PREFLIGHT: green (<map> <surface>)` — and exit 0.

Env passthrough: `RUN_UAT_PREFLIGHT` / `UAT_PREFLIGHT_PROBE` are consumed
entirely by `check-uat-preconditions.sh` (step 3, §5.7 above); this
wrapper reads neither, sets neither, and adds no env contract of its own.

Codes: this gate mints **no new gate codes** — it is composition, not a
new check. Its own preconditions reuse the existing usage/missing-file
`exit 2` convention (`lint-journey-map.sh` / `check-uat-preconditions.sh` /
`check-surface-staleness.sh`'s own posture) plus the
`PREFLIGHT_FAILED: step <n> (<gate name>)` line above, which is not a
closed-enum code token — it is a step pointer into whichever gate already
reported its own code.

See `journey/docs/uat-run-protocol.md` for the full operator ceremony this
gate is step 1 of.

---

## 6. Authority

The convergence loop's payoff: author writes/edits report → lint (4.1) +
evidence (4.2) gates → verifier run (5.2) → verification gate (4.3) → when
everything is clean, a human runs the promote ceremony (4.4) → the citation
gate (4.5) goes green.

What green means, stated bluntly: **hash-consistent, gate-clean, human-approved.**
NOT independently verified in a forge-proof sense: a determined operator
controls every input locally, on their own machine — the same trust
posture as every other local stamp in this framework. Forge-proofing is a
CI control-plane concern, deferred here exactly as it was for the journey
ledger.

**Consumer convention:** v1 wires no consumer mechanically. Any downstream
artifact that wants to cite a UAT report records the line
`uat_report: <path> sha256:<hash>` and may only cite when
`check-uat-citation.sh` passes at that hash. (The natural future consumer
is the Handover layer's packager — a UAT report shipped in a handover
package is already byte-covered by `PROVENANCE-MANIFEST.sha256`; wiring
"citation gate green" into that packager's checklist is a one-line future
amendment, not part of this layer.)

**Runtime truth is untouched:** a citable UAT report never marks
`JOURNEY_MAP.md` or the CI ledger green; the citation gate does not read
the ledger, and the ledger remains the only runtime authority.
"Browser UAT observations are evidence only" is now law, not manners.

---

## 7. Seams

Documented, bounded, not eliminated:

- Verifier search quality is model-bounded: a lazy narrow search that
  happens to confirm an absence passes deterministic re-run just as
  honestly as a thorough one. Bounded by: the author's own searches are
  also re-run, the verifier prompt requires a superset of the author's
  searches plus its own broader ones, and promotion is human-consumed.
  The mirror seam is comment-collision (re-characterization D6): a repo
  comment that merely names an absent feature makes any bare-word search
  literal non-zero-hit — an honest broad search dies `SEARCH_DIVERGED` —
  bounded, not eliminated, by the verifier prompt's search-literal
  discipline law (re-execute before emission, zero-hit only,
  implementation-shaped literals); search quality remains model-bounded.
- Artifact hashes bind bytes, not meaning — a screenshot proves nothing
  about what it depicts; artifact evidence is provenance, not proof.
- `- residual:` hypotheses are unverified by construction and must say so
  in their own text.
- Claims graded from runtime observation (artifact-evidenced) are checked
  for consistency and provenance only; code reading can neither prove nor
  disprove a runtime observation. Only the code-checkable slice of the
  report is ever adjudicated.
- Local green is not forge-proof (see Authority above).
- The verification file is never linted the way the report is: gate 4.1's
  schema lint (`lint-uat-report.sh`) runs only against the REPORT. The
  verification file's own quote and search lines get re-execution
  semantics only — `check-uat-verification.sh` re-checks each one against
  the pinned commit exactly as gate 4.2 does for the report — but there is
  no separate structural schema pass over the verification file itself.
  This is a narrower instance of the model-bounded search-quality seam
  above.

---

## 8. Out of scope

This contract defines the report FORMAT and its verification, not the UAT
run itself. Explicitly out of scope: TEST_SURFACE staleness gating; oracle
observability classification; mechanical consumer enforcement; any change
to `JOURNEY_MAP.md`, the ledger, existing promote gates, existing
refuters, or the Handover layer.

The UAT run protocol and environment preflight, and fixture-precondition
schemas, are NO LONGER out of scope as of spec G1: the `preconditions:`
grammar on `JOURNEY_MAP.md` (`lint-journey-map.sh` Check 8) plus
`check-uat-preconditions.sh` (§5.7 above) together cover declared-fixture
preflighting before a UAT run starts.

Oracle observability classification is NO LONGER out of scope as of spec
G4: the `oracle_classes:` grammar on `JOURNEY_MAP.md`
(`lint-journey-map.sh` Check 9), the optional `- oracle_clause:` claim
reference (§2.2, §5.1), and `check-uat-oracle-scope.sh` (§5.8 above)
together classify each oracle clause as browser-observable or
below-the-UI, and reject a browser-UAT `[C-absent]` claim that asserts a
below-the-UI clause as a gap. Still out of scope: generation pipelines do
not emit `oracle_classes:` in v1 — the field is authored by the
journey-spec author, human-confirmed, same as `oracle:` itself.

A report-WRITER prompt is NO LONGER out of scope as of spec DC-7:
`journey/gen/prompts/uat-writer.md` plus its gated runner
`journey/gen/runners/uat-write-run.sh` (§5.9 above) mechanize report
AUTHORING into the exact §2 grammar — raw session notes and
runner-computed evidence hashes go in, a report gated by the same
`lint-uat-report.sh` / `check-uat-evidence.sh` / `check-uat-oracle-scope.sh`
checks a hand-written report already had to clear comes out. Still out of
scope: **the writer never verifies its own claims and never promotes** —
those remain the separate verifier pass (§5.6) and the human promote
ceremony (§5.4) respectively. Author authority is unchanged: a human
operator reviews the written report exactly as they would review one they
typed themselves, before it ever enters the verify/promote loop (§4.2).
The writer is convenience — it mechanizes AUTHORING to a contract a human
author already had to hit by hand — not a new source of authority.

The UAT run protocol itself is NO LONGER out of scope as of spec DC-8:
`journey/docs/uat-run-protocol.md` documents the full operator ceremony —
preconditions declared, preflight, drive, write, author gates, verify,
scope, promote, cite — each step naming its executable gate, and
`journey/bin/uat-preflight.sh` (§5.10 above) composes `lint-journey-map.sh`
+ `check-surface-staleness.sh` + `check-uat-preconditions.sh` into the
single entry command the protocol names as step 1. §5.7's own G1 note above
already covered the fixture-precondition preflight in isolation; this
closes the remaining "run protocol" looseness by giving the FULL chain —
staleness through citation — one named document and one composed entry
point, not five gates an operator had to remember to run in the right
order by hand. Still out of scope, restated from the protocol doc itself:
no step in this chain marks `JOURNEY_MAP.md` or the CI ledger green, none
of it writes to the ledger, and CI never gates on steps 3 or 5 (write,
verify) — the only two that may invoke a model, and both remain opt-in
with a deterministic SKIP no-op otherwise, per house law that a stochastic
step is never the gate.
