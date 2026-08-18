# shellcheck shell=sh
# journey-test-promote_test.sh — human-gated spec promotion proofs (Increment 2).

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
JTP="$TESTS_DIR/../bin/journey-test-promote.sh"
AB="$TESTS_DIR/../bin/author-bundle.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
SFX="$TESTS_DIR/fixtures/surface"
GSPEC="$TESTS_DIR/fixtures/author/journey-101.spec.golden.ts"
GMAP="$GENDIR/golden/expected-journey-map.generated.md"

_jt_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}
_sha() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }

_t=$(mktemp -d)
cp "$GMAP" "$_t/map.md"
mkdir -p "$_t/tests/journeys"
sh "$AB" "$_t/map.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t" >/dev/null 2>&1
BUNDLE="$_t/author-bundle-journey-101.md"

_mk_refuter() { # DEST SPEC [JID]
  { printf 'REFUTER-NO-BLOCK:\n- journey_id: %s\n- checked_hash: %s\n' "${3:-JOURNEY-101}" "$(_sha "$2")"; } > "$1"
}

# ── jt-1: no --approve → refused, nothing written ─────────────────────────────
_mk_refuter "$_t/ref-ok.md" "$GSPEC"
_o=$(sh "$JTP" JOURNEY-101 "$GSPEC" "$BUNDLE" "$_t/ref-ok.md" "$_t/map.md" "$_t/tests/journeys" 2>&1); _ec=$?
_jt_nonzero "$_ec" "jt-1: all gates pass but no --approve → refused"
[ ! -f "$_t/tests/journeys/journey-101.spec.ts" ]
assert_eq 0 $? "jt-1: no spec installed without --approve"

# ── jt-2: refuter BLOCK → refused ─────────────────────────────────────────────
printf 'REFUTER-BLOCK:\n- journey_id: JOURNEY-101\n- reason: oracle encodes only half the intent\n- evidence: "AC-2" (bundle FEAT-001)\n' > "$_t/ref-block.md"
_o=$(sh "$JTP" --approve JOURNEY-101 "$GSPEC" "$BUNDLE" "$_t/ref-block.md" "$_t/map.md" "$_t/tests/journeys" 2>&1); _ec=$?
_jt_nonzero "$_ec" "jt-2: refuter BLOCK refuses promotion"

# ── jt-3: stale refuter hash (different spec) → refused ───────────────────────
printf 'x\n' > "$_t/other.ts"
_mk_refuter "$_t/ref-stale.md" "$_t/other.ts"
_o=$(sh "$JTP" --approve JOURNEY-101 "$GSPEC" "$BUNDLE" "$_t/ref-stale.md" "$_t/map.md" "$_t/tests/journeys" 2>&1); _ec=$?
_jt_nonzero "$_ec" "jt-3: stale refuter hash refused"
assert_contains "$_o" "STALE_REFUTER" "jt-3: names STALE_REFUTER"

# ── jt-4: refuter silent on this journey → refused ────────────────────────────
_mk_refuter "$_t/ref-other.md" "$GSPEC" "JOURNEY-102"
_o=$(sh "$JTP" --approve JOURNEY-101 "$GSPEC" "$BUNDLE" "$_t/ref-other.md" "$_t/map.md" "$_t/tests/journeys" 2>&1); _ec=$?
_jt_nonzero "$_ec" "jt-4: refuter silent on the journey refused"

# ── jt-5: lint-failing spec → refused ─────────────────────────────────────────
sed "s|page.getByTestId('upload-error')|page.locator('div.err')|" "$GSPEC" > "$_t/bad.ts"
_mk_refuter "$_t/ref-bad.md" "$_t/bad.ts"
_o=$(sh "$JTP" --approve JOURNEY-101 "$_t/bad.ts" "$BUNDLE" "$_t/ref-bad.md" "$_t/map.md" "$_t/tests/journeys" 2>&1); _ec=$?
_jt_nonzero "$_ec" "jt-5: lint-failing spec refused"

# ── jt-6: happy path — installs spec + flips ONLY the target journey ──────────
_mk_refuter "$_t/ref-ok.md" "$GSPEC"
sh "$JTP" --approve JOURNEY-101 "$GSPEC" "$BUNDLE" "$_t/ref-ok.md" "$_t/map.md" "$_t/tests/journeys" >/dev/null 2>&1
assert_eq 0 $? "jt-6: golden spec promotes with --approve"
cmp -s "$_t/tests/journeys/journey-101.spec.ts" "$GSPEC"
assert_eq 0 $? "jt-6: installed spec is byte-identical"
_lib="$TESTS_DIR/../lib/journey-lib.sh"
_f101=$( (JOURNEY_MAP="$_t/map.md"; export JOURNEY_MAP; . "$_lib"; journey_field JOURNEY-101 author_status) )
_f102=$( (JOURNEY_MAP="$_t/map.md"; export JOURNEY_MAP; . "$_lib"; journey_field JOURNEY-102 author_status) )
assert_eq "WRITTEN" "$_f101" "jt-6: JOURNEY-101 flipped to WRITTEN"
assert_eq "UNWRITTEN" "$_f102" "jt-6: JOURNEY-102 untouched"
_diff_lines=$(diff "$GMAP" "$_t/map.md" | grep -c '^[<>]')
assert_eq "2" "$_diff_lines" "jt-6: map changed by exactly one line (byte-preserving flip)"

# ── jt-7: already WRITTEN → refused (idempotence guard) ───────────────────────
_o=$(sh "$JTP" --approve JOURNEY-101 "$GSPEC" "$BUNDLE" "$_t/ref-ok.md" "$_t/map.md" "$_t/tests/journeys" 2>&1); _ec=$?
_jt_nonzero "$_ec" "jt-7: already-WRITTEN journey refused"
assert_contains "$_o" "ALREADY_WRITTEN" "jt-7: names ALREADY_WRITTEN"

# ── jt-8: existing spec with DIFFERENT content → refused, no overwrite ────────
cp "$GMAP" "$_t/map2.md"
printf '// a different pre-existing spec\n' > "$_t/tests/journeys2.dir.ts" 2>/dev/null || true
mkdir -p "$_t/tj2"
printf '// different content\n' > "$_t/tj2/journey-101.spec.ts"
_o=$(sh "$JTP" --approve JOURNEY-101 "$GSPEC" "$BUNDLE" "$_t/ref-ok.md" "$_t/map2.md" "$_t/tj2" 2>&1); _ec=$?
_jt_nonzero "$_ec" "jt-8: existing different spec refused (no silent overwrite)"
assert_contains "$_o" "EXISTING_SPEC_DIFFERS" "jt-8: names EXISTING_SPEC_DIFFERS"
assert_contains "$(cat "$_t/tj2/journey-101.spec.ts")" "different content" "jt-8: pre-existing spec untouched"

# ── jt-9: unknown journey → refused ───────────────────────────────────────────
_o=$(sh "$JTP" --approve JOURNEY-999 "$GSPEC" "$BUNDLE" "$_t/ref-ok.md" "$_t/map.md" "$_t/tests/journeys" 2>&1); _ec=$?
_jt_nonzero "$_ec" "jt-9: unknown journey refused"

rm -rf "$_t"
