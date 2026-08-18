# Journey Layer — Real-Project Shakedown Guide

**Audience:** the team running the first real-project test of the KLOSS Journey
Validation layer (Increments 1–3).
**Goal:** prove on a REAL project what has so far only been proven on the
framework's own fixtures — and log every point of friction so it can be fixed
before Increment 4 (simulator) builds on top.

> The framework's first law applies to the framework itself: nothing is true
> because an agent said it. The suite is green on fixtures; this shakedown is
> the executable evidence for real docs, a real model, and a real app.

---

## 0. What you are testing (and what "pass" means)

| # | Claim under test | Proven when |
|---|---|---|
| 1 | Real PRD/APP_FLOW/SSOT docs can be made to pass the preflights without unreasonable pain | `check-doc-format.sh` and `lint-personas.sh` exit 0 on your docs |
| 2 | A live model (your CLI backend) produces gate-clean journey candidates | `fanout-run.sh` and `persona-run.sh` complete with exit 0 |
| 3 | Human-gated promotion works and stays intent-only | promoted journeys land in `JOURNEY_MAP.md` as `UNWRITTEN`; nothing touches runtime status |
| 4 | The blind-authoring loop closes against YOUR running app | a blind-authored spec passes Playwright against the app |
| 5 | Runtime truth flows only through the ledger | `check-journeys.sh` passes only after a real GREEN stamp |

**The shakedown "passes" even if steps fail** — PROVIDED every failure is a
loud, named diagnostic and you log it. A silent pass, a confusing error, or a
gate that lets something wrong through is the real bug. Log everything in the
findings template (§9).

---

## 1. Prerequisites

- The project's canonical docs: `PRD.md`, `APP_FLOW.md`, the Step-1 SSOT,
  and (for TEST_SURFACE) `DESIGN_SYSTEM.md`.
- POSIX shell, `git`, `awk`, `sed`, `grep`, **`jq` 1.5+** (the only hard dep).
- A model CLI for live generation — Claude Code (`claude`) or Codex.
- Node 18+ **only** for Increment-2 app verification (kept inside
  `journey/surface-check/`; nothing else needs node).
- macOS and Linux are both supported (BSD/GNU date etc. already handled).

## 2. Setup

```sh
# 1. Copy the journey tree into the project repo root (it is self-contained;
#    every script resolves its own paths)
cp -R <framework-repo>/journey <project-repo>/journey

# 2. Sanity: the self-suite must be green in your copy BEFORE you start
sh journey/tests/run.sh          # expect: "all assertions passed" (791)

# 3. Create the model backend wrapper — a single executable taking
#    <prompt-file> <input-path> and printing the model's output to stdout
cat > journey/bin/backend-claude.sh << 'EOF'
#!/bin/sh
# JOURNEY_GEN_BACKEND wrapper: claude CLI, print-mode, no session.
# $1 = prompt file, $2 = input file or directory
set -u
{ cat "$1"; printf '\n\n---\n\n# INPUT\n\n'
  if [ -d "$2" ]; then for f in "$2"/*; do printf '## %s\n\n' "$f"; cat "$f"; printf '\n'; done
  else cat "$2"; fi
} | claude -p --output-format text
EOF
chmod +x journey/bin/backend-claude.sh
# (Codex twin: replace the last line with `codex exec -` or your equivalent.)

# 4. Smoke-test the wrapper
printf 'Reply with exactly: BACKEND-OK\n' > /tmp/ping.md
journey/bin/backend-claude.sh /tmp/ping.md /tmp/ping.md   # expect: BACKEND-OK
```

**Environment variables you will use throughout:**

| Var | Meaning |
|---|---|
| `RUN_LLM_GEN=1` | opt-in to ANY live model call (default: everything is a no-op) |
| `JOURNEY_GEN_BACKEND` | path to the wrapper above |
| `JOURNEY_RUNNER` | `playwright` (web) — required by generation and authoring |
| `RUN_APP_CHECK=1` | opt-in to node/Playwright app verification |
| `APP_BASE_URL` | where your app is running (default `http://localhost:4173`) |
| `JOURNEY_TARGET_MAP` | path to the canonical map (default `JOURNEY_MAP.md`) |

---

## 3. Phase 1 — doc preflight (expect friction HERE first)

```sh
sh journey/bin/check-doc-format.sh PRD.md APP_FLOW.md
```

It lists EVERY violation at once, per-id, with the fix named. You will likely
need to:

- convert the PRD's feature list into machine-readable **FEAT blocks**
  (`## FEAT-<n> — "<title>"`, `priority: P0..P3` — never must/should/nice,
  `user_story:`, `acceptance_criteria:` with `- AC-<n>:` labels);
- add a **`## User Journeys`** section to APP_FLOW
  (`### AFJ-<n> — "<title>"`, `covers_features:`, `steps:`);
- add a **`## Screens`** section to APP_FLOW
  (`### SCR-<n> — "<name>"`, `route:`) — needed for TEST_SURFACE;
- link every P0/P1 FEAT to an AFJ from at least one side (or run with
  `--allow-unlinked` and author coverage gaps deliberately).

The full format contract: `journey/docs/journey-gen-doc-format.md`.
**Log:** how long this took, which diagnostics were unclear, anything the
format could not express about your real docs.

## 4. Phase 2 — personas

Add a `## Personas` section to the SSOT (**at least 2** personas; 2–5 is the
recommended range — more than 5 still passes and merely warns `TOO_MANY_PERSONAS`,
owner ruling 2026-07-14):

```
### P1 — "<name>"
goal:             <what they're trying to get done>
context:          <where/how they work>
tech_savviness:   low | medium | high
error_tendency:   low | medium | high
patience_budget:  <integer retries before abandoning>
known_misbehaviors:
  - <kebab-case-token>            # or: known_misbehaviors: [none: <reason>]
```

```sh
sh journey/bin/lint-personas.sh SSOT.md
```

Markdown **thematic breaks** (`---`, `***`, `___`, with any surrounding
whitespace, and the spaced `- - -`) are prose punctuation and are **ignored** by
the lint — you may close the persona section with one (owner ruling 2026-07-14,
item 1). They are skipped *before* the misbehavior list-item regex, so a trailing
`---` is no longer parsed as the token `--`. The token grammar is unchanged: real
list items are still kebab-validated, and a `known_misbehaviors:` list holding
nothing but breaks still fails closed with `MISBEHAVIORS_BLANK`.

Base them on real support tickets / user research if you have any — the
misbehavior tokens are the whole value. **Log:** any real misbehavior you
couldn't express as a token.

## 5. Phase 3 — DERIVED journey generation (first live model run)

```sh
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=journey/bin/backend-claude.sh JOURNEY_RUNNER=playwright \
  sh journey/gen/runners/fanout-run.sh SSOT.md PRD.md APP_FLOW.md out/derived/
```

Every model output is validated deterministically before the next stage; a
failure names the gate that refused. Then **read the candidate yourself**
(`out/derived/JOURNEY_MAP.generated.md` + `JOURNEY_FIDELITY_REVIEW.md`) and,
only if satisfied:

```sh
sh journey/bin/journey-gen-promote.sh PRD.md APP_FLOW.md \
  out/derived/JOURNEY_MAP.generated.md out/derived/JOURNEY_COVERAGE_MANIFEST.json \
  out/derived/JOURNEY_COVERAGE_GAPS.md out/derived/JOURNEY_FIDELITY_REVIEW.md \
  JOURNEY_MAP.md --approve
```

### If your journey map is hand-authored or frozen

The generation pipeline above emits `JOURNEY_COVERAGE_MANIFEST.json` as one of
its three artifacts. If you did **not** generate your journey map — it is
hand-authored, or frozen from an earlier phase — you still need a manifest, and
you must **never type one**: it is generated evidence, not an authored document
(owner ruling 2026-07-14, item 3). Derive it:

```sh
sh journey/bin/generate-journey-coverage-manifest.sh \
  docs/PRD.md docs/APP_FLOW.md JOURNEY_MAP.md JOURNEY_COVERAGE_GAPS.md \
  > JOURNEY_COVERAGE_MANIFEST.json

# ...and in CI, verify the committed copy against its sources BEFORE the gate:
sh journey/bin/generate-journey-coverage-manifest.sh \
  docs/PRD.md docs/APP_FLOW.md JOURNEY_MAP.md JOURNEY_COVERAGE_GAPS.md \
  --check JOURNEY_COVERAGE_MANIFEST.json     # exit 1 = MANIFEST_STALE
```

The producer derives coverage **only** from your journey map's own `covers:` and
`flows:` fields. It will not guess: if `flows:` is empty, your AFJs are
uncovered and `check-journey-coverage.sh` will say so. That is the point — a
producer that inferred the mapping would manufacture coverage you never
declared. See `journey/docs/journey-gen-doc-format.md` §5.2.

**Log:** every runner failure (which gate, was the diagnostic actionable),
every refuter block (real catch or false alarm), and every infidelity YOU
catch during review that the gates and refuter missed — those misses are the
most valuable findings of the whole shakedown.

## 6. Phase 4 — PERSONA journey generation

```sh
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=journey/bin/backend-claude.sh JOURNEY_RUNNER=playwright \
  sh journey/gen/runners/persona-run.sh SSOT.md PRD.md APP_FLOW.md out/persona/ PERSONA_COVERAGE_GAPS.md
# review, then:
sh journey/bin/journey-gen-promote.sh --origin PERSONA PRD.md APP_FLOW.md \
  out/persona/JOURNEY_MAP.generated.md out/persona/JOURNEY_COVERAGE_MANIFEST.json \
  <doc-derived-gaps-file> out/persona/JOURNEY_FIDELITY_REVIEW.md JOURNEY_MAP.md --approve
sh journey/bin/persona-selfcheck.sh SSOT.md PRD.md JOURNEY_MAP.md PERSONA_COVERAGE_GAPS.md
```

Review question for every persona journey: *are these mistakes ones this
persona actually makes?* The gates prove token ownership; realism is yours.

## 7. Phase 5 — TEST_SURFACE + the running app

```sh
# one-time node setup (contained in the island)
( cd journey/surface-check && npm install && npx playwright install chromium )

# generate + promote the surface
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=journey/bin/backend-claude.sh \
  sh journey/gen/runners/surface-run.sh APP_FLOW.md DESIGN_SYSTEM.md out/surface/
sh journey/bin/surface-promote.sh APP_FLOW.md out/surface/TEST_SURFACE.candidate.md \
  journey/TEST_SURFACE.md --approve

# execution-verify against YOUR running app
RUN_APP_CHECK=1 JOURNEY_RUNNER=playwright APP_BASE_URL=http://localhost:<port> \
  sh journey/bin/check-test-surface.sh journey/TEST_SURFACE.md
```

`SELECTOR_STALE` here means the design-derived contract doesn't match the
built app — that's a FINDING about your app or your docs, not about the tool.
Decide which is wrong and fix it in the same commit. **Log:** the stale count
on first run (this number is the design↔implementation drift you've been
shipping blind).

`surface-promote.sh` also stamps a sibling `journey/TEST_SURFACE.md.provenance`
(one line: `app_flow_sha256: <64-hex>`) anchoring the promoted surface to the
exact APP_FLOW it was reviewed against. Re-run
`sh journey/bin/check-surface-staleness.sh journey/TEST_SURFACE.md APP_FLOW.md`
whenever APP_FLOW changes — `SURFACE_STALE` means re-run the surface gates
and re-promote; `PROVENANCE_MISSING` means the surface was never promoted
through `surface-promote.sh` in the first place (a hand-copied `.current.md`
never passes).

## 8. Phase 6 — blind authoring, the run, and the ledger

```sh
# author one UNWRITTEN journey blind
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=journey/bin/backend-claude.sh \
  sh journey/gen/runners/author-run.sh JOURNEY_MAP.md journey/TEST_SURFACE.md \
  APP_FLOW.md PRD.md JOURNEY-101 out/author/
# review the spec + refuter result, then promote (installs + flips to WRITTEN)
sh journey/bin/journey-test-promote.sh --approve JOURNEY-101 \
  out/author/journey-101.spec.candidate.ts out/author/author-bundle-journey-101.md \
  out/author/refuter-result-journey-101.md JOURNEY_MAP.md tests/journeys

# run it against the app
( cd journey/surface-check && JOURNEY_TESTS_DIR=../../tests/journeys \
  APP_BASE_URL=http://localhost:<port> npx playwright test --config=playwright.config.mjs )

# stamp GREEN — in CI this is the trusted two-job wiring
# (journey/docs/ci-journey-gates.example.yml); locally ONLY as a drill:
JOURNEY_STATUS_FILE=JOURNEY_STATUS.local.json JOURNEY_LEDGER_SOURCE="local-drill" \
  sh journey/bin/journey-status-stamp.sh JOURNEY-101 GREEN \
  --run-id local-drill --artifact playwright-report/

# close the loop (test-fixture conf pointing at the drill ledger)
sh journey/bin/check-journeys.sh <ledger.conf> JOURNEY_MAP.md tests/journeys
```

**A local GREEN is a drill, not truth.** Production trust requires the
two-job CI wiring with a protected ledger branch **plus a tag ruleset**, and
conf/env sourced from a non-PR-controllable control plane — until then, do
not advertise the gate as a forge-proof merge blocker.

---

## 9. Findings log (fill as you go — this is the deliverable)

Create `SHAKEDOWN-FINDINGS.md` in the project repo; one entry per finding:

```
## F-<n>: <one-line title>
phase:     1-6
severity:  BLOCKER | FRICTION | PAPERCUT | GATE-MISS
what:      <what happened, with the exact command and diagnostic>
expected:  <what you expected instead>
evidence:  <paste the output / file snippet>
```

- **GATE-MISS** is the highest-value category: anything wrong that a gate,
  lint, or refuter LET THROUGH and a human caught. These become new
  deterministic checks.
- Also record per phase: wall-clock time spent, number of doc edits needed,
  number of model re-runs needed.

## 10. Rules that protect the test (do not bend these)

1. Every promotion needs a human `--approve` after actually reading the
   artifact. Rubber-stamping invalidates the shakedown.
2. Never hand-edit `JOURNEY_MAP.md` runtime state, the ledger, or a promoted
   artifact to "get past" a gate — if a gate is wrong, that's a finding.
3. Never run `journey-status-stamp.sh` outside CI except as the §8 drill.
4. If a script crashes rather than failing with a named diagnostic, capture
   the full output — a crash is a bug even when the input was bad.
5. The default test suite (`sh journey/tests/run.sh`) must stay green in your
   copy the whole time; if it goes red, stop and report.

## 11. Done when

- [ ] Phases 1–6 each either completed or ended in a logged, named diagnostic
- [ ] At least one DERIVED and one PERSONA journey promoted after real review
- [ ] At least one blind-authored spec ran against the real app
- [ ] `SHAKEDOWN-FINDINGS.md` returned — including phase timings and any
      GATE-MISS entries (or an explicit "none found")
