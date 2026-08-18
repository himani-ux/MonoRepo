#!/bin/sh
# check-journey-coverage_test.sh — TDD proofs for check-journey-coverage.sh
#
# The gate proves COMPLETENESS ONLY (coverage is accounting, not fidelity):
# every P0/P1 FEAT-ID and every AFJ-ID must map to a JOURNEY-ID or a well-formed
# structured gap. It must fail closed on malformed docs, malformed gaps, invalid
# source ids, orphans, DOC_FORMAT diagnostics, and any ambiguous/inconsistent
# accounting that would weaken determinism.
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
CJC="$TESTS_DIR/../bin/check-journey-coverage.sh"
FX="$TESTS_DIR/fixtures/gen/coverage"
_ERR="$(mktemp)"

# Runs the gate over a fixture dir; sets _EC and captures stderr to $_ERR.
_gate() { # DIR
  sh "$CJC" "$1/PRD.md" "$1/APP_FLOW.md" "$1/JOURNEY_MAP.generated.md" \
    "$1/JOURNEY_COVERAGE_MANIFEST.json" "$1/JOURNEY_COVERAGE_GAPS.md" \
    >/dev/null 2>"$_ERR"
  _EC=$?
}

# Asserts a fixture fails closed AND emits a specific diagnostic token.
_fails_with() { # NAME TOKEN
  _gate "$FX/$1"
  if [ "$_EC" -ne 0 ]; then
    printf 'ok: %s fails closed (exit %s)\n' "$1" "$_EC"
  else
    printf 'FAIL: %s exited 0 (expected non-zero)\n' "$1"
    ASSERT_FAILS=$((ASSERT_FAILS + 1))
  fi
  assert_contains "$(cat "$_ERR")" "$2" "$1 diagnostic mentions $2"
}

# ── PASS ─────────────────────────────────────────────────────────────────────
# Both axes satisfied two ways each: FEAT-001(P0) journeyed + FEAT-003(P1) gapped;
# AFJ-001/002 journeyed + AFJ-003 gapped. FEAT-004(P2) is uncovered but NOT required.
_gate "$FX/pass"
assert_eq 0 "$_EC" "pass: every P0/P1 FEAT and every AFJ is journeyed or well-formed-gapped"

# ── Coverage axes: FEAT and AFJ each enforced independently ───────────────────
_fails_with fail-missing-feat "COVERAGE_GAP"   # a P0/P1 FEAT with no journey and no gap
_fails_with fail-missing-afj  "COVERAGE_GAP"   # an AFJ with no journey and no gap

# ── Source-reference integrity ────────────────────────────────────────────────
_fails_with fail-invalid-src "INVALID_SOURCE_ID"   # journey covers FEAT-999 (not in PRD)
_fails_with fail-orphan      "ORPHAN_JOURNEY"      # journey traces to no valid source id

# ── Structured gaps satisfy coverage ONLY when well-formed ────────────────────
_fails_with fail-malformed-gap "MALFORMED_GAP"     # gap missing a required §5.1 field

# ── DOC_FORMAT diagnostics are blocking, NEVER a coverage credit ──────────────
_fails_with fail-docformat-gap "DOC_FORMAT_GAP"    # present even when all ids covered → fail

# ── Doc-format anchors re-derived and fail-closed (same rules as the slicer) ──
_fails_with fail-priority-unparseable "PRD_PRIORITY_UNPARSEABLE"
_fails_with fail-appflow-unidded      "APP_FLOW_UNIDDED"

# ── Determinism: ambiguous / contradictory / inconsistent accounting fails ────
_fails_with fail-ambiguous-gap        "AMBIGUOUS_GAP"          # one id in two gap records
_fails_with fail-journeyed-and-gapped "JOURNEYED_AND_GAPPED"   # id both covered and gapped
_fails_with fail-index-inconsistent   "INDEX_INCONSISTENT"     # _index misreports coverage
_fails_with fail-map-manifest-mismatch "MAP_MANIFEST_MISMATCH" # map journey absent from manifest

rm -f "$_ERR"

# ── Anti-vacuous (review C4): empty anchor universe is a failure, not a pass ──
# Docs with zero FEAT anchors AND zero AFJ anchors previously made every check
# vacuously true (nothing required → nothing violated → exit 0).
_av=$(mktemp -d)
printf '# PRD\nprose, no FEAT blocks\n' > "$_av/PRD.md"
printf '# APP_FLOW\nprose, no User Journeys\n' > "$_av/APP_FLOW.md"
printf '# JOURNEY_MAP — generated (empty)\n' > "$_av/JOURNEY_MAP.generated.md"
printf '{"_index":{}}\n' > "$_av/JOURNEY_COVERAGE_MANIFEST.json"
printf '# no gaps\n' > "$_av/JOURNEY_COVERAGE_GAPS.md"
_gate "$_av"
if [ "$_EC" -ne 0 ]; then printf 'ok: anti-vacuous: empty anchor universe fails closed\n'; else
  printf 'FAIL: anti-vacuous: empty anchor universe passed (vacuous exit 0)\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
assert_contains "$(cat "$_ERR")" "NO_ANCHORS" "anti-vacuous: diagnostic names NO_ANCHORS"
rm -rf "$_av"
