# shellcheck shell=sh
# journey-gen-candidate_test.sh — candidate-format contract proofs (review C3).
#
# The generator→merge hop is the highest-traffic model↔model seam. The frozen
# candidate format (## JOURNEY-CANDIDATE + one json field_sources fence) is
# validated deterministically by check-candidate.sh BEFORE the merge model
# ever consumes a candidate.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
CC="$TESTS_DIR/../bin/journey-gen-check-candidate.sh"
GC="$TESTS_DIR/fixtures/gen/golden/expected-candidate-feat-001.md"

_cc_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

_t=$(mktemp -d)

# ── cc-1: golden candidate passes ─────────────────────────────────────────────
sh "$CC" "$GC" >/dev/null 2>&1
assert_eq 0 $? "cc-1: golden candidate passes the format check"

# ── cc-2: free-prose output (weak-executor default failure) fails ─────────────
printf 'Here is a journey I designed for the invoice upload feature...\n' > "$_t/prose.candidate"
_o=$(sh "$CC" "$_t/prose.candidate" 2>&1); _ec=$?
_cc_nonzero "$_ec" "cc-2: free-prose candidate rejected"
assert_contains "$_o" "NO_CANDIDATE_BLOCK" "cc-2: names NO_CANDIDATE_BLOCK"

# ── cc-3: a final JOURNEY-ID is forbidden pre-merge ───────────────────────────
sed 's/^## JOURNEY-CANDIDATE — /## JOURNEY-101 — /' "$GC" > "$_t/withid.candidate"
_o=$(sh "$CC" "$_t/withid.candidate" 2>&1); _ec=$?
_cc_nonzero "$_ec" "cc-3: candidate carrying a final JOURNEY-ID rejected"
assert_contains "$_o" "FORBIDDEN_JOURNEY_ID" "cc-3: names FORBIDDEN_JOURNEY_ID"

# ── cc-4: candidate block without its field_sources fence fails ──────────────
sed '/^```json field_sources$/,/^```$/d' "$GC" > "$_t/nofs.candidate"
_o=$(sh "$CC" "$_t/nofs.candidate" 2>&1); _ec=$?
_cc_nonzero "$_ec" "cc-4: candidate without field_sources fence rejected"
assert_contains "$_o" "MISSING_FIELD_SOURCES" "cc-4: names MISSING_FIELD_SOURCES"

# ── cc-5: invalid JSON in the field_sources fence fails ───────────────────────
sed 's/"from": "PRD"/"from": PRD/' "$GC" > "$_t/badjson.candidate"
_o=$(sh "$CC" "$_t/badjson.candidate" 2>&1); _ec=$?
_cc_nonzero "$_ec" "cc-5: unparseable field_sources JSON rejected"
assert_contains "$_o" "BAD_FIELD_SOURCES_JSON" "cc-5: names BAD_FIELD_SOURCES_JSON"

# ── cc-6: wrong origin / author_status fails ─────────────────────────────────
sed 's/^origin:          DERIVED/origin:          PERSONA/' "$GC" > "$_t/origin.candidate"
_o=$(sh "$CC" "$_t/origin.candidate" 2>&1); _ec=$?
_cc_nonzero "$_ec" "cc-6: non-DERIVED candidate rejected"
sed 's/^author_status:   UNWRITTEN/author_status:   WRITTEN/' "$GC" > "$_t/status.candidate"
_o=$(sh "$CC" "$_t/status.candidate" 2>&1); _ec=$?
_cc_nonzero "$_ec" "cc-6: non-UNWRITTEN candidate rejected"

# ── cc-7: runtime-truth keys are rejected ─────────────────────────────────────
{ cat "$GC"; printf 'ci_status: GREEN\n'; } > "$_t/runtime.candidate"
_o=$(sh "$CC" "$_t/runtime.candidate" 2>&1); _ec=$?
_cc_nonzero "$_ec" "cc-7: runtime-truth key in a candidate rejected"

# ── cc-8: an explicit CANDIDATE-FAILED declaration is a loud failure ──────────
printf 'CANDIDATE-FAILED: bundle contradicts itself (AC-1 vs step 3)\n' > "$_t/failed.candidate"
_o=$(sh "$CC" "$_t/failed.candidate" 2>&1); _ec=$?
_cc_nonzero "$_ec" "cc-8: CANDIDATE-FAILED declaration exits non-zero"
assert_contains "$_o" "generator declared failure" "cc-8: failure reason surfaced"

# ── cc-9: a pure structured-gap candidate (no journey) passes ─────────────────
cat > "$_t/gap.candidate" << 'GAP'
source_id:    FEAT-004
source_type:  FEAT
reason:       bundle has no acceptance_criteria side; no faithful oracle derivable
owner:        UNASSIGNED — human triage required
expiry:       2026-08-02
reviewer:     PENDING-HUMAN
GAP
sh "$CC" "$_t/gap.candidate" >/dev/null 2>&1
assert_eq 0 $? "cc-9: structured-gap-only candidate passes (gap, never invention)"

rm -rf "$_t"
