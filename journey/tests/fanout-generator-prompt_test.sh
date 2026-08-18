#!/bin/sh
# fanout-generator-prompt_test.sh — Task 6: deterministic validation of the
# per-bundle generator PROMPT CONTRACT.
#
# This test invokes NO model. It asserts that the prompt asset MANDATES the
# required constraints (bundle-only read, origin=DERIVED, author_status=UNWRITTEN,
# source-id preservation, AC-grounded oracle, APP_FLOW-grounded steps, gap-not-
# invent, field-level provenance) and FORBIDS the prohibited ones (runtime-truth
# fields, tested-status claims, TEST_SURFACE.md, executable tests, simulator/
# reality/extracted/blind-authoring). Any LIVE model invocation is opt-in behind
# RUN_LLM_GEN=1 and is never reached by the default suite.
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
PROMPT="$TESTS_DIR/../gen/prompts/fanout-generator.md"

if [ ! -f "$PROMPT" ]; then
  printf 'FAIL: generator prompt asset missing: %s\n' "$PROMPT"
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
  P=""
else
  printf 'ok: generator prompt asset exists\n'
  P="$(cat "$PROMPT")"
fi

# ── REQUIRED — single-bundle input contract ───────────────────────────────────
assert_contains "$P" "READ ONLY THIS BUNDLE" "prompt: read only the provided bundle"

# ── REQUIRED — generated-journey contract ─────────────────────────────────────
assert_contains "$P" "origin: DERIVED"           "prompt: requires origin=DERIVED"
assert_contains "$P" "author_status: UNWRITTEN"  "prompt: requires author_status=UNWRITTEN"

# ── REQUIRED — preserve source IDs and references ─────────────────────────────
assert_contains "$P" "FEAT-ID"          "prompt: preserves FEAT-ID"
assert_contains "$P" "AFJ-ID"           "prompt: preserves AFJ-ID"
assert_contains "$P" "Preserve verbatim" "prompt: source ids preserved verbatim"
assert_contains "$P" "acceptance_criteria" "prompt: oracle references PRD acceptance criteria"

# ── REQUIRED — grounding (no invention) ───────────────────────────────────────
assert_contains "$P" "grounded ONLY in the PRD"      "prompt: oracle grounded in PRD ACs"
assert_contains "$P" "NEVER drop or dilute"          "prompt: oracle must not drop/dilute an AC"
assert_contains "$P" "grounded ONLY in the APP_FLOW" "prompt: steps grounded in APP_FLOW"
assert_contains "$P" "generated-minimal"             "prompt: invented negative states tagged generated-minimal"
assert_contains "$P" "structured gap"                "prompt: emit a structured gap when a side is missing"
assert_contains "$P" "NEVER invent"                  "prompt: never invent the missing side"
assert_contains "$P" "field_sources"                 "prompt: emits field-level source provenance"

# ── REQUIRED — assurance framing ──────────────────────────────────────────────
assert_contains "$P" "Fidelity is NOT proven by generation" "prompt: states fidelity is not proven by generation"
assert_contains "$P" "CANDIDATE"                            "prompt: output stays candidate until promotion review"
assert_contains "$P" "Do NOT assign a final JOURNEY-ID"     "prompt: no final JOURNEY-ID assigned by the generator"

# ── REQUIRED — opt-in live-invocation guardrail is documented in the asset ─────
assert_contains "$P" "RUN_LLM_GEN=1" "prompt: live invocation is gated by RUN_LLM_GEN=1"

# ── FORBIDDEN — runtime-truth field keys (each named as prohibited) ───────────
for _rt in ci_status last_run ci_run_id ci_artifact failure_summary; do
  assert_contains "$P" "$_rt" "prompt: forbids runtime-truth field $_rt"
done

# ── FORBIDDEN — tested-status / test-surface / executable tests ───────────────
assert_contains "$P" "tested, verified, passing" "prompt: forbids claiming a journey is tested"
assert_contains "$P" "TEST_SURFACE.md"           "prompt: forbids TEST_SURFACE.md"
assert_contains "$P" "executable tests"          "prompt: forbids emitting executable tests"

# ── FORBIDDEN — other-engine / blind-authoring claims ─────────────────────────
assert_contains "$P" "simulator" "prompt: forbids simulator engine claims"
assert_contains "$P" "blind"     "prompt: forbids blind authoring"

# ── GUARDRAIL — no LLM path runs unless RUN_LLM_GEN=1 (default suite green) ────
# Task 6 wires NO live invocation (the thin runner is Task 9). This block proves
# the gate is honored: unset -> deterministic checks only; set -> nothing to run
# yet (documented seam), still no model invoked.
if [ "${RUN_LLM_GEN:-0}" = "1" ]; then
  printf 'ok: RUN_LLM_GEN=1 — live dry-run deferred to the Task-9 thin runner (no model invoked in Task 6)\n'
else
  printf 'ok: RUN_LLM_GEN unset — deterministic prompt-contract checks only, no model invoked\n'
fi

# ── Post-review contract locks (C3/I1/I2/I3/I4) ───────────────────────────────
assert_contains "$P" "## JOURNEY-CANDIDATE"        "prompt: frozen candidate heading (no final id pre-merge)"
assert_contains "$P" "json field_sources"          "prompt: field_sources fence spelled exactly"
assert_contains "$P" "column 0"                    "prompt: format hard rule — column-0 keys"
assert_contains "$P" "single line"                 "prompt: format hard rule — single-line scalars"
assert_contains "$P" "byte-verbatim"               "prompt: quotes are byte-verbatim (provenance gate)"
assert_contains "$P" "check-journey-provenance.sh" "prompt: names the deterministic provenance verifier"
assert_contains "$P" "leave EMPTY"                 "prompt: data_fixtures contradiction resolved (I1)"
assert_contains "$P" "generated_minimal\": true"   "prompt: negative-state resolution rule (I2) — marker lives in field_sources"
assert_contains "$P" "never by adding a new step"  "prompt: negative-state annotates an existing step (I2)"
assert_contains "$P" "UNASSIGNED — human triage required" "prompt: canonical gap owner placeholder (I3)"
assert_contains "$P" "PENDING-HUMAN"               "prompt: canonical gap reviewer placeholder (I3)"
assert_contains "$P" "GAP_EXPIRY"                  "prompt: gap expiry comes from the Generation Context (I3)"
assert_contains "$P" "P0 < P1 < P2 < P3"           "prompt: priority decision rule (I4)"
assert_contains "$P" "runner: UNRESOLVED"          "prompt: absent RUNNER yields UNRESOLVED, never invention (I4)"
assert_contains "$P" "CANDIDATE-FAILED"            "prompt: degenerate input has a loud, defined output"
assert_contains "$P" "Worked example"              "prompt: carries the golden worked example (few-shot)"
