# shellcheck shell=sh
# persona-origin_test.sh — --origin flag proofs (Increment 3, A3/A4).
# The flag RESTRICTS, never broadens: PERSONA promotion rejects DERIVED
# candidates and vice versa; origin is runner-declared, never inferred.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$TESTS_DIR/../bin"
CC="$BIN/journey-gen-check-candidate.sh"
PROMOTE2="$BIN/journey-gen-promote.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
PFX="$TESTS_DIR/fixtures/persona"
GC="$GENDIR/golden/expected-candidate-feat-001.md"
PMAP2="$PFX/JOURNEY_MAP.persona.md"
PMAN="$PFX/JOURNEY_COVERAGE_MANIFEST.json"
PGAP2="$PFX/JOURNEY_COVERAGE_GAPS.md"

_po_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}
_sha_po() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }

_t=$(mktemp -d)
sed 's/^origin:          DERIVED$/origin:          PERSONA/' "$GC" > "$_t/persona.candidate"

# ── oc-1: default stays DERIVED (back-compat) ─────────────────────────────────
sh "$CC" "$GC" >/dev/null 2>&1
assert_eq 0 $? "oc-1: DERIVED candidate passes with no flag (back-compat)"
sh "$CC" "$GC" --origin DERIVED >/dev/null 2>&1
assert_eq 0 $? "oc-1: DERIVED candidate passes explicit --origin DERIVED"

# ── oc-2: PERSONA candidate needs the flag ────────────────────────────────────
_o=$(sh "$CC" "$_t/persona.candidate" 2>&1); _ec=$?
_po_nonzero "$_ec" "oc-2: PERSONA candidate fails the DERIVED default"
sh "$CC" "$_t/persona.candidate" --origin PERSONA >/dev/null 2>&1
assert_eq 0 $? "oc-2: PERSONA candidate passes --origin PERSONA"

# ── oc-3: cross-origin rejected both ways ─────────────────────────────────────
_o=$(sh "$CC" "$GC" --origin PERSONA 2>&1); _ec=$?
_po_nonzero "$_ec" "oc-3: DERIVED candidate rejected under --origin PERSONA"
_o=$(sh "$CC" "$_t/persona.candidate" --origin DERIVED 2>&1); _ec=$?
_po_nonzero "$_ec" "oc-3: PERSONA candidate rejected under --origin DERIVED"

# ── op-1: PERSONA promotion — intent-only, author_status stays UNWRITTEN ─────
_sha_po "$PMAP2" > /dev/null  # (warm sha helper)
{ printf 'reviewed_sha256: %s\n' "$(_sha_po "$PMAP2")"
  printf 'correct: JOURNEY-201 — misbehavior routing owned by P1; oracle preserves AC-1/AC-2 — evidence: "the file appears in the invoice list immediately after upload" (bundle FEAT-001 AC-2)\n'
} > "$_t/fidelity.md"
sh "$PROMOTE2" --origin PERSONA "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$PMAP2" "$PMAN" "$PGAP2" \
  "$_t/fidelity.md" "$_t/target.md" --approve >/dev/null 2>&1
assert_eq 0 $? "op-1: PERSONA candidate promotes under --origin PERSONA"
_lib="$TESTS_DIR/../lib/journey-lib.sh"
_as=$( (JOURNEY_MAP="$_t/target.md"; export JOURNEY_MAP; . "$_lib"; journey_field JOURNEY-201 author_status) )
assert_eq "UNWRITTEN" "$_as" "op-1: promoted PERSONA journey stays author_status UNWRITTEN (intent-only)"
_org=$( (JOURNEY_MAP="$_t/target.md"; export JOURNEY_MAP; . "$_lib"; journey_field JOURNEY-201 origin) )
assert_eq "PERSONA" "$_org" "op-1: promoted journey keeps origin PERSONA"
if grep -qE '^[[:space:]]*(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):' "$_t/target.md"; then
  printf 'FAIL: op-1: runtime-truth key leaked into the target map\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1))
else
  printf 'ok: op-1: no runtime-truth key in the promoted map (PERSONA creates intent, never truth)\n'
fi

# ── op-2: ORIGIN_MISMATCH both directions ─────────────────────────────────────
_o=$(sh "$PROMOTE2" --origin PERSONA "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" \
  "$GENDIR/golden/expected-journey-map.generated.md" \
  "$GENDIR/golden/expected-coverage-manifest.json" "$GENDIR/golden/expected-gaps.md" \
  "$_t/fidelity.md" "$_t/t2.md" --approve 2>&1 >/dev/null); _ec=$?
_po_nonzero "$_ec" "op-2: --origin PERSONA rejects a DERIVED candidate"
assert_contains "$_o" "ORIGIN_MISMATCH" "op-2: names ORIGIN_MISMATCH (PERSONA vs DERIVED)"
_o=$(sh "$PROMOTE2" "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$PMAP2" "$PMAN" "$PGAP2" \
  "$_t/fidelity.md" "$_t/t3.md" --approve 2>&1 >/dev/null); _ec=$?
_po_nonzero "$_ec" "op-2: default (DERIVED) rejects a PERSONA candidate"
assert_contains "$_o" "ORIGIN_MISMATCH" "op-2: names ORIGIN_MISMATCH (DERIVED vs PERSONA)"

# ── op-3: mixed-origin candidate rejected ─────────────────────────────────────
{ cat "$PMAP2"; printf '\n'
  awk '/^## JOURNEY-101/, /^## JOURNEY-102/' "$GENDIR/golden/expected-journey-map.generated.md" \
    | sed '$d'; } > "$_t/mixed.md"
{ printf 'reviewed_sha256: %s\n' "$(_sha_po "$_t/mixed.md")"
  printf 'correct: JOURNEY-201 — checked — evidence: "x" (bundle FEAT-001)\n'
  printf 'correct: JOURNEY-101 — checked — evidence: "x" (bundle FEAT-001)\n'
} > "$_t/fidelity-mixed.md"
_o=$(sh "$PROMOTE2" --origin PERSONA "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$_t/mixed.md" "$PMAN" "$PGAP2" \
  "$_t/fidelity-mixed.md" "$_t/t4.md" --approve 2>&1 >/dev/null); _ec=$?
_po_nonzero "$_ec" "op-3: mixed-origin candidate rejected"
assert_contains "$_o" "ORIGIN_MISMATCH" "op-3: names ORIGIN_MISMATCH"

rm -rf "$_t"
