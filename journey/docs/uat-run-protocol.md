# UAT run protocol — operator ceremony

The operator-facing chain for a browser-UAT pass, staleness through
citation: what to run, in what order, and what each step's green actually
means. Sibling of `journey/docs/uat-report-format.md` (the report/verifier
contract this protocol drives) and `journey/docs/journey-inbox-format.md`;
same house style. Every step below names its executable gate — nothing
here is prose-only law with no machine check behind it.

**Motivating incident (spec G1):** a real browser-UAT pass burned
wall-clock time on 401s because an existing dev-auth bridge was
unconfigured — nothing checked declared preconditions before the run
started. This protocol, and specifically step 1, is that check.

---

## The chain

### 0. Preconditions declared

Before any run, the journeys the pass will exercise must carry a
`preconditions:` block (and, where oracle clauses need browser-vs-lower
classification, an `oracle_classes:` field) — grammar defined and validated
by `lint-journey-map.sh` Checks 8 and 9. See `journey/JOURNEY_MAP.template.md`
for the field schema (`  - <kind>: <value>`, kind in
`{auth, env, data, state}`) and worked examples. A journey with no
declared preconditions is invisible to step 1's per-entry checks — only its
anti-vacuous backstop (`NO_PRECONDITIONS`) catches a map that should have
declared them but doesn't (`journey/docs/uat-report-format.md` §5.7).

### 1. Preflight

```
sh journey/bin/uat-preflight.sh JOURNEY_MAP.md TEST_SURFACE.md docs/APP_FLOW.md
```

The single entry command. Composes, in order, as executables,
fail-closed: `lint-journey-map.sh` → `check-surface-staleness.sh` →
`check-uat-preconditions.sh`. First failure prints the failing gate's own
diagnostic, then `PREFLIGHT_FAILED: step <n> (<gate name>)`, exit 1. All
three green: `UAT-PREFLIGHT: green (<map> <surface>)`, exit 0.

Static checks (`env:` preconditions, the map/surface/provenance grammar)
always run. Live probes (`auth:`/`data:`/`state:` preconditions) are
opt-in — set `RUN_UAT_PREFLIGHT=1` and point `UAT_PREFLIGHT_PROBE` at a
single executable (invoked as `"$UAT_PREFLIGHT_PROBE" <kind> <value>`, exit
0 = met) before driving the app for real. `uat-preflight.sh` does not read
either variable itself; both flow straight through to
`check-uat-preconditions.sh` untouched (`journey/docs/uat-report-format.md`
§5.7). Without `RUN_UAT_PREFLIGHT=1` the gate still exits 0 on a
lint/surface/env-clean map — it prints an explicit `SKIP: live probes not
run` line so an unprobed `auth`/`data`/`state` entry is never a silent
pass — but a genuinely broken dev-auth bridge will not be caught until the
probe actually runs. **This is the gate the 401-burn archetype needed**:
run with `RUN_UAT_PREFLIGHT=1` before any pass that depends on an
`auth:`/`data:`/`state:` precondition actually holding, not just being
declared.

### 2. Drive

An operator or an agent drives the app, persona-agnostic, against the
preflighted `TEST_SURFACE.md` and the declared journeys — collecting
session notes and evidence artifacts (screenshots, logs, exports) as they
go.

**The law, restated:** browser-UAT observations are evidence only. Nothing
in this step, or any step before the human promote ceremony (step 7),
writes to `JOURNEY_MAP.md` or the CI ledger. A UAT pass can propose a gap;
it cannot mark anything green, and it cannot mark anything RUN. Runtime
truth comes from the CI ledger alone, exactly as it always has
(`journey/docs/uat-report-format.md` §6).

### 3. Write

Turn the session notes + evidence into a report in the exact
`uat-report-format.md` §2 grammar — either hand-authored, or mechanized:

```
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> REPORT_DATE=<YYYY-MM-DD> \
  [JOURNEY_MAP=<path>] \
  sh journey/gen/runners/uat-write-run.sh NOTES_FILE EVIDENCE_DIR REPO_ROOT OUTDIR
```

Mechanizes AUTHORING only (`journey/docs/uat-report-format.md` §5.9): raw
session notes and runner-computed evidence hashes go in, a report gated by
the same checks a hand-written report already had to clear comes out. The
writer never verifies its own claims and never promotes — those are steps
5 and 7 below, unconditionally separate. `RUN_LLM_GEN` unset is a
deterministic no-op (SKIP, exit 0, no model, no network); a
`WRITER-FAILED:` result installs nothing.

### 4. Author gates

Whether hand-authored or written by step 3, the report must independently
clear:

```
sh journey/bin/lint-uat-report.sh UAT_REPORT_<date>.md
sh journey/bin/check-uat-evidence.sh UAT_REPORT_<date>.md <repo_root>
```

Schema (§5.1) and then re-verified author evidence against the pinned
`repo_commit` — never the working tree (§5.2). `uat-write-run.sh` already
composes both before it installs anything; a hand-authored report clears
them here for the first time.

### 5. Verify

```
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> \
  sh journey/gen/runners/uat-verify-run.sh UAT_REPORT_<date>.md <repo_root>
```

A second, independent pass (never the author) re-checks every claim
against the pinned commit and writes verdict blocks
(`UAT_REPORT_<date>.verification.md`), gated by `check-uat-verification.sh`
before anything lands on disk (`uat-report-format.md` §5.3, §5.6). Any
`refute` or `downgrade` sends the report back to step 3/4 — editing a
claim, accepting a regrade, or deleting the claim outright are all
legitimate resolutions (§4.2's convergence loop).

### 6. Scope

```
sh journey/bin/check-uat-oracle-scope.sh UAT_REPORT_<date>.md JOURNEY_MAP.md
```

Required whenever the report carries any `- oracle_clause:` reference
(§2.2). The false-gap killer (spec G4): rejects a `[C-absent]` claim that
cites an oracle clause the map has classified `lower` (verified below the
UI) rather than `browser` — a browser UAT pass cannot assert a below-the-UI
absence as a gap (§5.8). RUN THIS STEP ONLY when the report carries at
least one `- oracle_clause:` line: invoking the gate on a ref-free report
fails `NO_CLAUSE_REFS` by design (the anti-vacuous law — an invoked gate
never passes vacuously), so a clean ref-free report skips this step, and
the operator judgment "should this report have carried refs?" is what the
backstop exists to force. (Wording corrected 2026-07-12: this passage
previously said a ref-free report is "untouched by this step," which
contradicted the gate's shipped anti-vacuous behavior — a doc/gate [X]
caught during field-run kit verification.)

### 7. Promote

```
sh journey/bin/uat-report-promote.sh UAT_REPORT_<date>.md <repo_root> --approve
```

The human trust elevation — **only a human runs this**. Refuses before any
other work when `--approve` is absent. With it: re-runs gates 4.1/4.2/4.3
in full, requires zero `refute`/`downgrade` verdicts and at least one
evidenced claim (`[C]`, `[C-absent]`, or `[X]`), then writes the promotion
marker via temp+trap+`mv` (§5.4). This is the same O2 ceremony as
`journey-gen-promote.sh` / `journey-test-promote.sh` — nothing upstream of
this step carries authority.

### 8. Cite

```
sh journey/bin/check-uat-citation.sh UAT_REPORT_<date>.md <repo_root>
```

The gate any downstream consumer runs before citing the report. Green
means, stated bluntly (verbatim, §6): **hash-consistent, gate-clean,
human-approved.** NOT independently verified in a forge-proof sense: a
determined operator controls every input locally, on their own machine —
the same trust posture as every other local stamp in this framework.
Forge-proofing is a CI control-plane concern, deferred here exactly as it
was for the journey ledger. On success this prints exactly
`UAT-CITATION: green <report_sha256>` — the only string a consumer should
ever match on.

---

## What this protocol does NOT do

- **No runtime truth.** No step in this chain — preflight, drive, write,
  verify, promote, or cite — ever marks `JOURNEY_MAP.md` or the CI ledger
  green. The ledger remains the only runtime authority; a citable UAT
  report is evidence, not a test result.
- **No ledger writes.** Nothing in this protocol calls
  `journey-status-stamp.sh` or touches `JOURNEY_STATUS.json` in any mode.
  Browser-UAT observations are evidence only — that is now law, not
  manners (`uat-report-format.md` §6).
- **No CI gating of stochastic steps.** Steps 3 and 5 (write, verify) are
  the only two that may invoke a model, and both are opt-in
  (`RUN_LLM_GEN=1`) with a deterministic SKIP no-op otherwise. Per house
  law, a stochastic step is never the gate — the gates are steps 1, 4, 6,
  7, and 8, all deterministic, all runnable with no model and no network.

---

## Seams

Documented, bounded, not eliminated — same posture as
`uat-report-format.md` §7:

- Step 1's `env:`/grammar checks are static and always run; its
  `auth`/`data`/`state` PROBE checks are opt-in
  (`RUN_UAT_PREFLIGHT=1`) — a default preflight run can still be green on a
  precondition that would fail live if never probed. Run with
  `RUN_UAT_PREFLIGHT=1` before any pass that depends on one actually
  holding, not just declared.
- Step 1 checks DECLARED preconditions only (`uat-report-format.md` §5.7's
  own trust statement); a journey that should declare a precondition but
  doesn't is invisible to the per-entry checks — only the anti-vacuous
  `NO_PRECONDITIONS` backstop catches a map with zero preconditions
  anywhere.
- Everything downstream of step 2 inherits the seams already documented in
  `uat-report-format.md` §7 (verifier search quality is model-bounded,
  artifact hashes bind bytes not meaning, local green is not forge-proof)
  — this protocol composes those gates, it does not loosen or re-litigate
  any of them.
