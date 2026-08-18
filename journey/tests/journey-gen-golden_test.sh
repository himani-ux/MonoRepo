#!/bin/sh
# journey-gen-golden_test.sh — Task 5: freeze the deterministic fixture contract.
#
# Locks the golden expected artifacts (§5.1 gaps, §5.2 manifest, doc-derived
# JOURNEY_MAP candidate) and the adversarial diluted-oracle case that later
# generative tasks (6-10) must satisfy. DETERMINISTIC ONLY — no LLM, no
# RUN_LLM_GEN, no prompt execution, no generator orchestration.
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$TESTS_DIR/../bin"
LIB="$TESTS_DIR/../lib/journey-lib.sh"
GEN="$TESTS_DIR/fixtures/gen"                    # Task-3 golden doc-set
G="$GEN/golden"
ADV="$GEN/adversarial/diluted-oracle"

SLICE="$BIN/journey-gen-slice.sh"
LINT="$BIN/lint-journey-map.sh"
CJC="$BIN/check-journey-coverage.sh"

GMAP="$G/expected-journey-map.generated.md"
GMAN="$G/expected-coverage-manifest.json"
GGAP="$G/expected-gaps.md"

_err="$(mktemp)"

# value of one field of one journey in a given map (reuses the Increment-1 parser)
_field() { # MAP ID KEY
  ( JOURNEY_MAP="$1"; export JOURNEY_MAP; . "$LIB"; journey_field "$2" "$3" )
}

# ── Golden passes the slicer on its own doc-set ───────────────────────────────
_out=$(mktemp -d)
sh "$SLICE" "$GEN/SSOT.md" "$GEN/PRD.md" "$GEN/APP_FLOW.md" "$_out" >/dev/null 2>&1
assert_eq 0 $? "golden: slicer exits 0 on the doc-set"
assert_eq "FEAT-001 FEAT-002" \
  "$(jq -r '[.bundles[]|select(.source_type=="FEAT")|.id]|sort|join(" ")' "$_out/bundle-manifest.json")" \
  "golden: slicer bundles the P0/P1 FEATs (FEAT-003 P2 excluded)"
rm -rf "$_out"

# ── Golden map is schema-valid (lint) ─────────────────────────────────────────
assert_exit 0 sh "$LINT" "$GMAP"

# ── Authority property (where applicable): no runtime-truth field keys ────────
if grep -qE '^(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):' "$GMAP"; then
  printf 'FAIL: golden map reintroduces a runtime-truth field\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1))
else
  printf 'ok: golden map is free of runtime-truth field keys (runtime truth stays in the ledger)\n'
fi

# ── Golden map + §5.2 manifest + §5.1 gaps pass the coverage gate ─────────────
assert_exit 0 sh "$CJC" "$GEN/PRD.md" "$GEN/APP_FLOW.md" "$GMAP" "$GMAN" "$GGAP"

# ── Generated journeys are origin=DERIVED / author_status=UNWRITTEN ────────────
assert_eq DERIVED   "$(_field "$GMAP" JOURNEY-101 origin)"        "golden JOURNEY-101 origin=DERIVED"
assert_eq UNWRITTEN "$(_field "$GMAP" JOURNEY-101 author_status)" "golden JOURNEY-101 author_status=UNWRITTEN"
assert_eq DERIVED   "$(_field "$GMAP" JOURNEY-102 origin)"        "golden JOURNEY-102 origin=DERIVED"
assert_eq UNWRITTEN "$(_field "$GMAP" JOURNEY-102 author_status)" "golden JOURNEY-102 author_status=UNWRITTEN"

# ── §5.2 consistency enforced: a lying _index cannot fabricate coverage ────────
# Forward journey mapping (covers/flows) is the accounting truth; _index is only
# a checked redundancy. Under-report a covered id in _index -> the gate rejects it.
_bad=$(mktemp)
jq '._index."FEAT-001".journeys=[]' "$GMAN" > "$_bad"
sh "$CJC" "$GEN/PRD.md" "$GEN/APP_FLOW.md" "$GMAP" "$_bad" "$GGAP" >/dev/null 2>"$_err"
assert_eq 1 $? "golden: coverage rejects a manifest whose _index under-reports a covered id"
assert_contains "$(cat "$_err")" "INDEX_INCONSISTENT" \
  "golden: forward mapping (not _index) is the accounting truth"
rm -f "$_bad"

# ── §5.1 validity enforced: a structurally invalid gap is not a credit ─────────
_badgaps=$(mktemp)
{ cat "$GGAP"
  printf '\nsource_id:    FEAT-002\nsource_type:  FEAT\nreason:       gap missing its owner field\nexpiry:       2026-12-01\nreviewer:     bob\n'
} > "$_badgaps"
sh "$CJC" "$GEN/PRD.md" "$GEN/APP_FLOW.md" "$GMAP" "$GMAN" "$_badgaps" >/dev/null 2>"$_err"
assert_eq 1 $? "golden: coverage rejects a §5.1 gap missing a required field"
assert_contains "$(cat "$_err")" "MALFORMED_GAP" \
  "golden: §5.1 gaps count only when structurally valid"
rm -f "$_badgaps"

# ── DOC_FORMAT records remain blocking diagnostics, never coverage credits ─────
_df=$(mktemp)
{ cat "$GGAP"
  printf '\nsource_id:    APP_FLOW_UNIDDED\nsource_type:  DOC_FORMAT\nreason:       a journey heading lacked an AFJ-id\nowner:        alice\nexpiry:       2026-12-01\nreviewer:     bob\n'
} > "$_df"
sh "$CJC" "$GEN/PRD.md" "$GEN/APP_FLOW.md" "$GMAP" "$GMAN" "$_df" >/dev/null 2>"$_err"
assert_eq 1 $? "golden: a DOC_FORMAT gap flips the otherwise-complete set to fail"
assert_contains "$(cat "$_err")" "DOC_FORMAT_GAP" \
  "golden: DOC_FORMAT records are blocking, not coverage credits"
rm -f "$_df"

# ── Adversarial diluted-oracle: present, schema-valid, coverage-complete, yet
#    the dropped AC is detectable against the frozen golden ─────────────────────
AC2="immediately after upload"   # FEAT-001 AC-2 clause

# The dilution slips past BOTH deterministic completeness gates (by design):
assert_exit 0 sh "$LINT" "$ADV/JOURNEY_MAP.generated.md"
assert_exit 0 sh "$CJC" "$GEN/PRD.md" "$GEN/APP_FLOW.md" \
  "$ADV/JOURNEY_MAP.generated.md" "$ADV/JOURNEY_COVERAGE_MANIFEST.json" "$ADV/JOURNEY_COVERAGE_GAPS.md"

# The frozen golden IS the deterministic review scaffolding: measured against it,
# the diluted oracle's dropped AC-2 is detectable.
assert_contains    "$(_field "$GMAP" JOURNEY-101 oracle)" "$AC2" \
  "golden JOURNEY-101 oracle preserves FEAT-001 AC-2"
assert_not_contains "$(_field "$ADV/JOURNEY_MAP.generated.md" JOURNEY-101 oracle)" "$AC2" \
  "diluted JOURNEY-101 oracle DROPS FEAT-001 AC-2 (fails the golden-oracle comparison)"
assert_contains    "$(_field "$ADV/JOURNEY_MAP.generated.md" JOURNEY-101 oracle)" "status=ACCEPTED" \
  "diluted oracle is still plausible (AC-1 retained) — the dilution is silent"
assert_contains    "$(cat "$ADV/bundle-feat-001.md")" "$AC2" \
  "diluted fixture ships the source bundle (AC-2 present) for the refuter to compare"

rm -f "$_err"
