# shellcheck shell=sh
# persona-run_test.sh — prompt contracts + stub-backend proofs for
# persona-run.sh (Increment 3). No model, no network.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
GEN="$TESTS_DIR/../gen"
GENDIR="$TESTS_DIR/fixtures/gen"
PFX="$TESTS_DIR/fixtures/persona"
PRUN="$GEN/runners/persona-run.sh"
PSLICE="$TESTS_DIR/../bin/persona-gen-slice.sh"

_pr_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

# ── prompt contracts ──────────────────────────────────────────────────────────
_PG=$(cat "$GEN/prompts/persona-journey-generator.md")
assert_contains "$_PG" "READ ONLY THIS BUNDLE" "persona prompt: bundle-only read boundary"
assert_contains "$_PG" "origin:          PERSONA" "persona prompt: worked example emits origin PERSONA"
assert_contains "$_PG" "author_status:   UNWRITTEN" "persona prompt: worked example stays UNWRITTEN"
assert_contains "$_PG" "happy path in costume" "persona prompt: misbehavior-ownership rule stated"
assert_contains "$_PG" "NEVER invent a token; NEVER borrow one" "persona prompt: token allowance is the bundle persona only"
assert_contains "$_PG" "CANDIDATE-FAILED: " "persona prompt: loud failure output defined"
assert_contains "$_PG" "not consumed here" "persona prompt: patience_budget not consumed (Increment 4)"
assert_contains "$_PG" "USER BEHAVIOR, not tested behavior" "persona prompt: core invariant stated"

_PR=$(cat "$GEN/prompts/refuter-persona-fidelity.md")
assert_contains "$_PR" "REFUTER-BLOCK:" "persona refuter: frozen BLOCK shape"
assert_contains "$_PR" "REFUTER-NO-BLOCK:" "persona refuter: frozen NO-BLOCK shape"
assert_contains "$_PR" "CHECKED_HASH" "persona refuter: hash supplied by the runner"
assert_contains "$_PR" "Misbehavior ownership" "persona refuter: ownership check in the procedure"
assert_contains "$_PR" "default to BLOCK on doubt" "persona refuter: refuter-framed"
assert_contains "$_PR" "NEVER generally bless" "persona refuter: never blesses"

# ── slicer proofs ─────────────────────────────────────────────────────────────
_t=$(mktemp -d)
JOURNEY_RUNNER=playwright sh "$PSLICE" "$GENDIR/SSOT.md" "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$_t/s1" >/dev/null 2>&1
assert_eq 0 $? "pslice-1: golden docs slice"
[ -f "$_t/s1/bundles/feat-001-p1.md" ] && [ -f "$_t/s1/bundles/feat-002-p1.md" ]
assert_eq 0 $? "pslice-1: (FEAT x P1) bundles emitted"
[ ! -f "$_t/s1/bundles/feat-001-p2.md" ]
assert_eq 0 $? "pslice-1: none-misbehavior persona P2 SKIPPED (cannot own a misbehavior step)"
_b=$(cat "$_t/s1/bundles/feat-001-p1.md")
assert_contains "$_b" "uploads-wrong-file-first" "pslice-1: bundle carries the persona's tokens"
assert_not_contains "$_b" "Finance Reviewer" "pslice-1: bundle carries THIS persona only"
assert_contains "$(jq -r '.skipped_personas[0].persona' "$_t/s1/persona-manifest.json")" "P2" "pslice-1: manifest records the skipped persona"

# ── runner gates ──────────────────────────────────────────────────────────────
assert_exit 0 env -u RUN_LLM_GEN sh "$PRUN"
RUN_LLM_GEN=1 sh "$PRUN" >/dev/null 2>&1; _pr_nonzero $? "persona-run: RUN_LLM_GEN=1 without backend fails closed"

# ── stub backend ──────────────────────────────────────────────────────────────
_STUB="$_t/stub.sh"
cat > "$_STUB" << 'STUB'
#!/bin/sh
case "$1" in
  *persona-journey-generator.md)
    case "${STUB_PGEN_MODE:-golden}" in
      golden)
        case "$2" in
          *feat-001-p1*) cat "$PCAND1" ;;
          *feat-002-p1*) cat "$PCAND2" ;;
          *) exit 1 ;;
        esac ;;
      prose)   printf 'Here is a lovely persona journey narrative...\n' ;;
      foreign) sed 's/(misbehavior: double-clicks-submit)/(misbehavior: ignores-audit-trail)/' "$PCAND1" ;;
    esac ;;
  *refuter-persona-fidelity.md)
    _h=$(grep -m1 '^CHECKED_HASH:' "$2" | sed 's/^CHECKED_HASH:[[:space:]]*//')
    case "${STUB_PREF_MODE:-noblock}" in
      noblock)
        for _j in $(grep -oE '^## JOURNEY-[0-9]+' "$2" | sed 's/^## //' | sort -u); do
          printf 'REFUTER-NO-BLOCK:\n- journey_id: %s\n- checked_hash: %s\n' "$_j" "$_h"
        done ;;
      wronghash) printf 'REFUTER-NO-BLOCK:\n- journey_id: JOURNEY-201\n- checked_hash: deadbeef\n' ;;
    esac ;;
  *) exit 1 ;;
esac
STUB
chmod +x "$_STUB"
export PCAND1="$PFX/expected-candidate-feat-001-p1.md" PCAND2="$PFX/expected-candidate-feat-002-p1.md"

# ── pr-1: golden replay end-to-end (all gates + hash-bound fidelity) ──────────
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright \
  sh "$PRUN" "$GENDIR/SSOT.md" "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$_t/r1" >/dev/null 2>&1
assert_eq 0 $? "pr-1: golden replay passes end-to-end"
_g=$(cat "$_t/r1/JOURNEY_MAP.generated.md" 2>/dev/null)
assert_contains "$_g" "## JOURNEY-201" "pr-1: ids assigned from 201"
assert_contains "$_g" "## JOURNEY-202" "pr-1: second candidate gets 202"
assert_contains "$_g" "origin:          PERSONA" "pr-1: assembled journeys are PERSONA"
assert_not_contains "$_g" "JOURNEY-CANDIDATE" "pr-1: candidate headings replaced by assigned ids"
assert_contains "$(cat "$_t/r1/JOURNEY_FIDELITY_REVIEW.md")" "reviewed_sha256: " "pr-1: fidelity is hash-stamped"
assert_contains "$(cat "$_t/r1/JOURNEY_FIDELITY_REVIEW.md")" "correct: JOURNEY-202" "pr-1: fidelity covers every journey"

# ── pr-2: prose candidate fails closed before assembly ────────────────────────
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright STUB_PGEN_MODE=prose \
  sh "$PRUN" "$GENDIR/SSOT.md" "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$_t/r2" 2>&1 >/dev/null); _ec=$?
_pr_nonzero "$_ec" "pr-2: prose candidate fails closed"
assert_contains "$_o" "format check" "pr-2: attributed to the candidate format check"

# ── pr-3: foreign misbehavior token fails at check-persona-journeys ───────────
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright STUB_PGEN_MODE=foreign \
  sh "$PRUN" "$GENDIR/SSOT.md" "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$_t/r3" 2>&1 >/dev/null); _ec=$?
_pr_nonzero "$_ec" "pr-3: foreign-token candidate fails closed"
assert_contains "$_o" "check-persona-journeys" "pr-3: attributed to the persona-journeys gate"

# ── pr-4: refuter echoing a wrong hash fails closed ───────────────────────────
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright STUB_PREF_MODE=wronghash \
  sh "$PRUN" "$GENDIR/SSOT.md" "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$_t/r4" 2>&1 >/dev/null); _ec=$?
_pr_nonzero "$_ec" "pr-4: mis-echoed checked_hash fails closed"

unset PCAND1 PCAND2
rm -rf "$_t"
