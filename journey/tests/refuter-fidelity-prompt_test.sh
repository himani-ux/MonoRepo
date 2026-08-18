#!/bin/sh
# refuter-fidelity-prompt_test.sh — Task 8: deterministic validation of the
# refuter fidelity PROMPT CONTRACT + its frozen adversarial target.
#
# Invokes NO model. Asserts the prompt asset MANDATES the fidelity checks
# (bundles-as-ground-truth; detect oracle dilution / ungrounded steps / invented
# content / dropped source ids / over-merge; adjudicate gaps + MERGE-REVIEW),
# CLASSIFIES findings block/warn/correct with source evidence, PRODUCES review
# findings only (no rewrites, no promotion), and FORBIDS the prohibited things.
# It also re-confirms — deterministically — the Task-5 diluted-oracle fixture the
# LIVE refuter must flag. Any live invocation is opt-in behind RUN_LLM_GEN=1.
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
PROMPT="$TESTS_DIR/../gen/prompts/refuter-fidelity.md"
LIB="$TESTS_DIR/../lib/journey-lib.sh"
ADV="$TESTS_DIR/fixtures/gen/adversarial/diluted-oracle"

if [ ! -f "$PROMPT" ]; then
  printf 'FAIL: refuter prompt asset missing: %s\n' "$PROMPT"
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
  P=""
else
  printf 'ok: refuter prompt asset exists\n'
  P="$(cat "$PROMPT")"
fi

# ── REQUIRED — refuter framing + read-only ground-truth inputs ─────────────────
assert_contains "$P" "BLIND"                "prompt: refuter is a separate agent, blind to the generator"
assert_contains "$P" "block on doubt"       "prompt: refuter-framed, default to block on doubt"
assert_contains "$P" "Read ONLY"            "prompt: read only source bundles + generated candidate artifacts"
assert_contains "$P" "fidelity ground truth" "prompt: source bundles are the fidelity ground truth"

# ── REQUIRED — the fidelity checks ────────────────────────────────────────────
assert_contains "$P" "acceptance criteria"   "prompt: checks PRD acceptance-criteria preservation"
assert_contains "$P" "ORACLE DILUTION"       "prompt: checks for oracle dilution"
assert_contains "$P" "dropped from the generated oracle" "prompt: detect an AC dropped from the generated oracle"
assert_contains "$P" "present in the source bundle"      "prompt: ...while still present in the source bundle"
assert_contains "$P" "APP_FLOW"              "prompt: checks steps grounded in APP_FLOW"
assert_contains "$P" "invented"              "prompt: checks nothing is invented"
assert_contains "$P" "DROPPED SOURCE ID"     "prompt: checks source ids are not dropped"
assert_contains "$P" "over-merge"            "prompt: checks for over-merge"
assert_contains "$P" "ambiguous collapse"    "prompt: checks for ambiguous collapse"
assert_contains "$P" "hide a generated omission" "prompt: gaps must not hide a generated omission"
assert_contains "$P" "DOC_FORMAT"            "prompt: DOC_FORMAT addressed"
assert_contains "$P" "never a coverage credit" "prompt: DOC_FORMAT stays blocking, never a credit"

# ── REQUIRED — output = findings only, classified, evidence-backed ────────────
assert_contains "$P" "JOURNEY_FIDELITY_REVIEW.md"          "prompt: writes the fidelity review artifact"
assert_contains "$P" "findings, not rewrites"              "prompt: produces review findings, not rewrites"
assert_contains "$P" "Do NOT rewrite"                      "prompt: forbids rewriting/fixing the candidate"
assert_contains "$P" "block"                               "prompt: severity vocabulary includes block"
assert_contains "$P" "warn"                                "prompt: severity vocabulary includes warn"
assert_contains "$P" "correct"                             "prompt: severity vocabulary includes correct"
assert_contains "$P" "quote or reference the source evidence" "prompt: each finding cites source evidence"

# ── REQUIRED — assurance framing (no bless / no promote / not proof) ──────────
assert_contains "$P" "Refuter review is NOT executable proof" "prompt: refuter review is not executable proof"
assert_contains "$P" "does NOT prove runtime correctness"     "prompt: bounds fidelity risk, not runtime correctness"
assert_contains "$P" "NEVER mark coverage green"              "prompt: can never mark coverage green"
assert_contains "$P" "no promotion path"                     "prompt: no automatic promotion"
assert_contains "$P" "review-only"                           "prompt: output is review-only"
assert_contains "$P" "human promotes"                        "prompt: candidate stays until a human promotes"
assert_contains "$P" "RUN_LLM_GEN=1"                         "prompt: live invocation gated by RUN_LLM_GEN=1"

# ── FORBIDDEN — runtime-truth field keys ──────────────────────────────────────
for _rt in ci_status last_run ci_run_id ci_artifact failure_summary; do
  assert_contains "$P" "$_rt" "prompt: forbids runtime-truth field $_rt"
done

# ── FORBIDDEN — tested-status / test-surface / executable / engines ───────────
assert_contains "$P" "tested, verified, passing" "prompt: forbids claiming a journey is tested"
assert_contains "$P" "TEST_SURFACE.md"           "prompt: forbids TEST_SURFACE.md"
assert_contains "$P" "executable"                "prompt: forbids executable tests"
assert_contains "$P" "simulator"                 "prompt: forbids simulator engine claims"
assert_contains "$P" "blind"                     "prompt: forbids blind authoring"

# ── FROZEN ADVERSARIAL TARGET — the Task-5 diluted-oracle fixture ─────────────
# The refuter's regression case. Deterministically confirm the drop it must
# flag `block` (live block-detection is the RUN_LLM_GEN path, locked in Task 10).
AC2="immediately after upload"     # FEAT-001 AC-2 clause
assert_exit 0 test -f "$ADV/JOURNEY_MAP.generated.md"
assert_exit 0 test -f "$ADV/bundle-feat-001.md"
_dil_oracle="$( JOURNEY_MAP="$ADV/JOURNEY_MAP.generated.md"; export JOURNEY_MAP; . "$LIB"; journey_field JOURNEY-101 oracle )"
assert_not_contains "$_dil_oracle" "$AC2" \
  "adversarial: diluted JOURNEY-101 oracle drops AC-2 (the refuter's block target)"
assert_contains "$(cat "$ADV/bundle-feat-001.md")" "$AC2" \
  "adversarial: source bundle still carries AC-2 (fidelity ground truth)"

# ── GUARDRAIL — no LLM path runs unless RUN_LLM_GEN=1 (default suite green) ────
if [ "${RUN_LLM_GEN:-0}" = "1" ]; then
  printf 'ok: RUN_LLM_GEN=1 — live refuter dry-run (block on the diluted oracle) deferred to the Task-9/10 runner; no model invoked in Task 8\n'
else
  printf 'ok: RUN_LLM_GEN unset — deterministic prompt-contract checks only, no model invoked\n'
fi

# ── Post-review contract locks (I6/I7) ────────────────────────────────────────
assert_contains "$P" "AC table first"        "prompt: dilution detection is a PROCEDURE, not an obligation (I7)"
assert_contains "$P" "EVERY journey gets at least one finding line" "prompt: per-journey completeness mandated (I6)"
assert_contains "$P" "EMPTY-CANDIDATE"       "prompt: zero-journey candidate has a defined blocking output"
assert_contains "$P" "MISSING-ARTIFACT"      "prompt: missing inputs have a defined blocking output"
assert_contains "$P" "Worked examples"       "prompt: golden clean + blocking reviews embedded few-shot (I7)"
assert_contains "$P" "block: JOURNEY-101 — oracle dropped FEAT-001 AC-2" "prompt: the blocking example is the golden fixture line"
assert_contains "$P" "Ignore every other file" "prompt: input list matches what the runner hands over (M6)"
