#!/bin/sh
# merge-dedup-prompt_test.sh — Task 7: deterministic validation of the merge +
# dedup PROMPT CONTRACT.
#
# Invokes NO model. Asserts the prompt asset MANDATES the merge contract
# (read-only inputs; preserve origin=DERIVED / author_status=UNWRITTEN; preserve
# FEAT-ID/AFJ-ID/AC/APP_FLOW anchors; never invent coverage; _index consistent
# with the forward per-journey mapping; conservative merge; surface ambiguity)
# and FORBIDS the prohibited things (runtime-truth fields, tested-status claims,
# TEST_SURFACE.md, executable tests, simulator/blind-authoring, fidelity-proof
# claims). Any live invocation is opt-in behind RUN_LLM_GEN=1 and never reached.
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
PROMPT="$TESTS_DIR/../gen/prompts/merge-dedup.md"

if [ ! -f "$PROMPT" ]; then
  printf 'FAIL: merge/dedup prompt asset missing: %s\n' "$PROMPT"
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
  P=""
else
  printf 'ok: merge/dedup prompt asset exists\n'
  P="$(cat "$PROMPT")"
fi

# ── REQUIRED — input/output contract ──────────────────────────────────────────
assert_contains "$P" "Read only the provided candidate" "prompt: read only candidate fragments + accounting inputs"
assert_contains "$P" "JOURNEY_MAP.generated.md"          "prompt: emits the generated journey-map candidate"
assert_contains "$P" "JOURNEY_COVERAGE_MANIFEST.json"    "prompt: emits the §5.2 coverage manifest"
assert_contains "$P" "JOURNEY_COVERAGE_GAPS.md"          "prompt: emits the §5.1 gaps file"

# ── REQUIRED — preserve the generated-journey contract + anchors ──────────────
assert_contains "$P" "origin: DERIVED"          "prompt: preserves origin=DERIVED"
assert_contains "$P" "author_status: UNWRITTEN" "prompt: preserves author_status=UNWRITTEN"
assert_contains "$P" "FEAT-ID and AFJ-ID"       "prompt: preserves FEAT-ID and AFJ-ID source anchors"
assert_contains "$P" "AC-<n>"                   "prompt: preserves PRD acceptance-criteria references"
assert_contains "$P" "APP_FLOW"                 "prompt: preserves APP_FLOW references"

# ── REQUIRED — no invented coverage; gaps explicit ────────────────────────────
assert_contains "$P" "Never invent"                          "prompt: never invents FEAT/AFJ/AC/APP_FLOW/coverage"
assert_contains "$P" "create coverage just to satisfy" "prompt: never fabricates coverage to pass the gate"
assert_contains "$P" "explicit records"                      "prompt: gaps are explicit records, not hidden omissions"
assert_contains "$P" "never drop a source reference"         "prompt: a merged journey never drops a source ref"

# ── REQUIRED — accounting truth / _index consistency ──────────────────────────
assert_contains "$P" "forward per-journey covers/flows"  "prompt: forward mapping is the accounting truth"
assert_contains "$P" "accounting truth"                  "prompt: names the accounting truth explicitly"
assert_contains "$P" "_index consistent with the forward" "prompt: _index consistent with forward mapping"
assert_contains "$P" "DOC_FORMAT"                        "prompt: DOC_FORMAT records addressed"
assert_contains "$P" "never a coverage credit"           "prompt: DOC_FORMAT stays blocking, never a credit"

# ── REQUIRED — conservative merge + surface ambiguity ─────────────────────────
assert_contains "$P" "materially the same"                "prompt: merge only when anchors + intent are materially the same"
assert_contains "$P" "merely because the text is similar" "prompt: do not merge on textual similarity"
assert_contains "$P" "Escalate"                           "prompt: escalate ambiguous duplicates"
assert_contains "$P" "keep them separate"                 "prompt: ambiguous candidates kept separate, not collapsed"
assert_contains "$P" "do not collide"                     "prompt: assigns non-colliding JOURNEY-IDs"

# ── REQUIRED — assurance framing ──────────────────────────────────────────────
assert_contains "$P" "accounting shape only, not semantic fidelity" "prompt: merge proves accounting shape only"
assert_contains "$P" "does NOT prove fidelity"                      "prompt: makes no fidelity-proof claim"
assert_contains "$P" "CANDIDATE"                                   "prompt: output stays candidate until promotion review"
assert_contains "$P" "RUN_LLM_GEN=1"                               "prompt: live invocation gated by RUN_LLM_GEN=1"

# ── FORBIDDEN — runtime-truth field keys ──────────────────────────────────────
for _rt in ci_status last_run ci_run_id ci_artifact failure_summary; do
  assert_contains "$P" "$_rt" "prompt: forbids runtime-truth field $_rt"
done

# ── FORBIDDEN — tested-status / test-surface / executable tests / engines ─────
assert_contains "$P" "tested, verified, passing" "prompt: forbids claiming a journey is tested"
assert_contains "$P" "TEST_SURFACE.md"           "prompt: forbids TEST_SURFACE.md"
assert_contains "$P" "executable"                "prompt: forbids emitting executable tests"
assert_contains "$P" "simulator"                 "prompt: forbids simulator engine claims"
assert_contains "$P" "blind"                     "prompt: forbids blind authoring"

# ── EMISSION — sentinel-delimited stdout contract (review C2) ─────────────────
assert_contains "$P" "=== FILE: JOURNEY_MAP.generated.md ===" "prompt: states the FILE sentinel for the map"
assert_contains "$P" "=== END FILE ==="                       "prompt: states the END FILE sentinel"
assert_contains "$P" "journey-gen-split.sh"                   "prompt: names the deterministic splitter"
assert_contains "$P" "MERGE-FAILED: "                         "prompt: defines the no-partial-output failure line"
assert_contains "$P" "no preamble"                            "prompt: forbids text outside the sentinels"

# ── GUARDRAIL — no LLM path runs unless RUN_LLM_GEN=1 (default suite green) ────
if [ "${RUN_LLM_GEN:-0}" = "1" ]; then
  printf 'ok: RUN_LLM_GEN=1 — live merge deferred to the Task-9 thin runner (no model invoked in Task 7)\n'
else
  printf 'ok: RUN_LLM_GEN unset — deterministic prompt-contract checks only, no model invoked\n'
fi

# ── Post-review contract locks (I5/I7/M1) ─────────────────────────────────────
assert_contains "$P" "existing-ids.txt"        "prompt: collision input is deterministic, never the map itself (I5)"
assert_contains "$P" "JOURNEY-101"             "prompt: id numbering rule stated (start at 101)"
assert_contains "$P" "ALL THREE hold"          "prompt: material-sameness is an operational three-part test (I7)"
assert_contains "$P" "Worked pair — MERGE"     "prompt: worked merge example present"
assert_contains "$P" "Worked pair — KEEP SEPARATE" "prompt: worked keep-separate example present"
assert_contains "$P" "source id"               "prompt: covered-and-gapped rule names a SOURCE ID, not a journey (M1)"
