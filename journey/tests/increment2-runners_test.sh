# shellcheck shell=sh
# increment2-runners_test.sh — prompt contracts + stub-backend runner proofs
# for surface-run.sh / author-run.sh (Increment 2). No model, no network.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
GEN="$TESTS_DIR/../gen"
GENDIR="$TESTS_DIR/fixtures/gen"
SFX="$TESTS_DIR/fixtures/surface"
GSPEC="$TESTS_DIR/fixtures/author/journey-101.spec.golden.ts"
GMAP="$GENDIR/golden/expected-journey-map.generated.md"
SRUN="$GEN/runners/surface-run.sh"
ARUN="$GEN/runners/author-run.sh"

_r2_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

# ── prompt contracts (string locks on load-bearing tokens) ────────────────────
_SG=$(cat "$GEN/prompts/surface-generator.md")
assert_contains "$_SG" "READ ONLY THIS BUNDLE" "surface prompt: bundle-only read boundary"
assert_contains "$_SG" "SURFACE-FAILED: " "surface prompt: loud failure output defined"
assert_contains "$_SG" "## SURFACE: invoices_list" "surface prompt: worked example embedded"
assert_contains "$_SG" "Never invent a screen, route, endpoint" "surface prompt: no invention"
assert_contains "$_SG" "RUN_LLM_GEN=1" "surface prompt: opt-in gate named"

_TA=$(cat "$GEN/prompts/test-author.md")
assert_contains "$_TA" "READ ONLY THIS BUNDLE" "author prompt: bundle-only read boundary"
assert_contains "$_TA" "import { test, expect } from '@playwright/test';" "author prompt: frozen first line"
assert_contains "$_TA" "SPEC-FAILED: " "author prompt: loud failure output defined"
assert_contains "$_TA" "// ORACLE: " "author prompt: verbatim oracle comment rule"
assert_contains "$_TA" "NEVER invent a selector" "author prompt: never invents selectors"
assert_contains "$_TA" "NEVER weaken the oracle" "author prompt: never weakens the oracle"
assert_contains "$_TA" "page.evaluate" "author prompt: forbids page.evaluate"
assert_contains "$_TA" "src/" "author prompt: names the src/ blindness boundary"

_RF=$(cat "$GEN/prompts/refuter-test-fidelity.md")
assert_contains "$_RF" "REFUTER-BLOCK:" "refuter prompt: frozen BLOCK shape"
assert_contains "$_RF" "REFUTER-NO-BLOCK:" "refuter prompt: frozen NO-BLOCK shape"
assert_contains "$_RF" "checked_hash" "refuter prompt: hash echo required"
assert_contains "$_RF" "CHECKED_HASH" "refuter prompt: hash supplied by the runner"
assert_contains "$_RF" "default to BLOCK on doubt" "refuter prompt: refuter-framed"
assert_contains "$_RF" "NEVER generally bless" "refuter prompt: never blesses"
assert_contains "$_RF" "Oracle table first" "refuter prompt: dilution check is a procedure"

# ── no-op / fail-closed gates ─────────────────────────────────────────────────
assert_exit 0 env -u RUN_LLM_GEN sh "$SRUN"
assert_exit 0 env -u RUN_LLM_GEN sh "$ARUN"
RUN_LLM_GEN=1 sh "$SRUN" >/dev/null 2>&1; _r2_nonzero $? "surface-run: RUN_LLM_GEN=1 without backend fails closed"
RUN_LLM_GEN=1 sh "$ARUN" >/dev/null 2>&1; _r2_nonzero $? "author-run: RUN_LLM_GEN=1 without backend fails closed"

# ── stub backend ──────────────────────────────────────────────────────────────
_T=$(mktemp -d)
_STUB="$_T/stub.sh"
cat > "$_STUB" << 'STUB'
#!/bin/sh
case "$1" in
  *surface-generator.md)
    case "${STUB_SURFACE_MODE:-golden}" in
      golden) awk '/^## SURFACE: /, 0' "$GOLDEN_SURFACE" ;;
      prose)  printf 'Here is the surface I designed for you!\n' ;;
    esac ;;
  *test-author.md)
    case "${STUB_AUTHOR_MODE:-golden}" in
      golden) cat "$GOLDEN_SPEC" ;;
      prose)  printf 'I wrote a great test, here it is described in words.\n' ;;
    esac ;;
  *refuter-test-fidelity.md)
    _h=$(grep -m1 '^CHECKED_HASH:' "$2" | sed 's/^CHECKED_HASH:[[:space:]]*//')
    case "${STUB_REFUTER_MODE:-noblock}" in
      noblock)   printf 'REFUTER-NO-BLOCK:\n- journey_id: JOURNEY-101\n- checked_hash: %s\n' "$_h" ;;
      block)     printf 'REFUTER-BLOCK:\n- journey_id: JOURNEY-101\n- reason: oracle clause unencoded\n- evidence: "AC-2" (bundle FEAT-001)\n' ;;
      prose)     printf 'Looks good to me overall!\n' ;;
      wronghash) printf 'REFUTER-NO-BLOCK:\n- journey_id: JOURNEY-101\n- checked_hash: deadbeef\n' ;;
    esac ;;
  *) exit 1 ;;
esac
STUB
chmod +x "$_STUB"
export GOLDEN_SURFACE="$SFX/TEST_SURFACE.golden.md" GOLDEN_SPEC="$GSPEC"

# ── sr-1: surface-run golden replay → candidate assembled + gated ─────────────
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" \
  sh "$SRUN" "$GENDIR/APP_FLOW.md" "$GENDIR/DESIGN_SYSTEM.md" "$_T/s1" >/dev/null 2>&1
assert_eq 0 $? "sr-1: surface-run golden replay passes end-to-end"
[ -f "$_T/s1/TEST_SURFACE.candidate.md" ]
assert_eq 0 $? "sr-1: candidate TEST_SURFACE materialized"
assert_contains "$(cat "$_T/s1/TEST_SURFACE.candidate.md")" "## SURFACE: invoices_list" "sr-1: candidate carries the screen entry"

# ── sr-2: prose surface output → fail closed pre-assembly ─────────────────────
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" STUB_SURFACE_MODE=prose \
  sh "$SRUN" "$GENDIR/APP_FLOW.md" "$GENDIR/DESIGN_SYSTEM.md" "$_T/s2" 2>&1 >/dev/null); _ec=$?
_r2_nonzero "$_ec" "sr-2: prose surface entry fails closed"
assert_contains "$_o" "prose or drift" "sr-2: failure names the validation"

# ── ar-1: author-run golden replay → candidate + hash-bound refuter ───────────
cp "$GMAP" "$_T/map.md"
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" \
  sh "$ARUN" "$_T/map.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_T/a1" >/dev/null 2>&1
assert_eq 0 $? "ar-1: author-run golden replay passes end-to-end"
[ -f "$_T/a1/journey-101.spec.candidate.ts" ] && [ -f "$_T/a1/refuter-result-journey-101.md" ]
assert_eq 0 $? "ar-1: candidate spec + refuter result materialized"
assert_contains "$(cat "$_T/a1/refuter-result-journey-101.md")" "REFUTER-NO-BLOCK" "ar-1: refuter result is the frozen shape"

# ── ar-2: prose author output → fail closed before lint/refuter ───────────────
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" STUB_AUTHOR_MODE=prose \
  sh "$ARUN" "$_T/map.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_T/a2" 2>&1 >/dev/null); _ec=$?
_r2_nonzero "$_ec" "ar-2: prose spec candidate fails closed"

# ── ar-3: refuter BLOCK → runner fails, artifacts kept for triage ─────────────
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" STUB_REFUTER_MODE=block \
  sh "$ARUN" "$_T/map.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_T/a3" 2>&1 >/dev/null); _ec=$?
_r2_nonzero "$_ec" "ar-3: refuter BLOCK fails the run"
assert_contains "$_o" "BLOCKED" "ar-3: failure names the block"

# ── ar-4: refuter prose (neither shape) → fail closed ─────────────────────────
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" STUB_REFUTER_MODE=prose \
  sh "$ARUN" "$_T/map.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_T/a4" 2>&1 >/dev/null); _ec=$?
_r2_nonzero "$_ec" "ar-4: refuter prose fails closed (prose is not a review)"

# ── ar-5: refuter echoing a wrong hash → fail closed ──────────────────────────
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" STUB_REFUTER_MODE=wronghash \
  sh "$ARUN" "$_T/map.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_T/a5" 2>&1 >/dev/null); _ec=$?
_r2_nonzero "$_ec" "ar-5: mis-echoed checked_hash fails closed"
assert_contains "$_o" "does not match" "ar-5: failure names the hash mismatch"

unset GOLDEN_SURFACE GOLDEN_SPEC
rm -rf "$_T"

# ── Opt-in LIVE model regeneration (RUN_LLM_GEN=1 + real backend) ─────────────
if [ "${RUN_LLM_GEN:-0}" = "1" ] && [ -n "${JOURNEY_GEN_BACKEND:-}" ]; then
  _L=$(mktemp -d)
  RUN_LLM_GEN=1 sh "$SRUN" "$GENDIR/APP_FLOW.md" "$GENDIR/DESIGN_SYSTEM.md" "$_L/s" >/dev/null 2>&1
  assert_eq 0 $? "live: surface-run generates a lint+coverage-clean candidate"
  cp "$GMAP" "$_L/map.md"
  RUN_LLM_GEN=1 sh "$ARUN" "$_L/map.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
    JOURNEY-101 "$_L/a" >/dev/null 2>&1
  assert_eq 0 $? "live: author-run produces a lint-clean, hash-bound-refuted candidate spec"
  rm -rf "$_L"
else
  printf 'ok: live model regeneration SKIPPED (RUN_LLM_GEN=1 + JOURNEY_GEN_BACKEND both required)\n'
fi
