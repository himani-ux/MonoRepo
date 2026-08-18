# shellcheck shell=sh
# lint-test-surface_test.sh — TEST_SURFACE format lint proofs (Increment 2).

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LTS="$TESTS_DIR/../bin/lint-test-surface.sh"
SFX="$TESTS_DIR/fixtures/surface"

_ts_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

# ── ts-1: golden surface passes ───────────────────────────────────────────────
sh "$LTS" "$SFX/TEST_SURFACE.golden.md" >/dev/null 2>&1
assert_eq 0 $? "ts-1: golden TEST_SURFACE passes lint"

# ── ts-2: missing required key (route) fails ──────────────────────────────────
_o=$(sh "$LTS" "$SFX/TEST_SURFACE.missing-key.md" 2>&1); _ec=$?
_ts_nonzero "$_ec" "ts-2: missing route key fails"
assert_contains "$_o" "route" "ts-2: names the missing key"

# ── ts-3: raw CSS selector fails the grammar ──────────────────────────────────
_o=$(sh "$LTS" "$SFX/TEST_SURFACE.css-selector.md" 2>&1); _ec=$?
_ts_nonzero "$_ec" "ts-3: raw CSS selector rejected"
assert_contains "$_o" "SELECTOR_GRAMMAR" "ts-3: names SELECTOR_GRAMMAR"

# ── ts-4: XPath selector fails ────────────────────────────────────────────────
_t=$(mktemp -d)
sed 's|testid=invoice-list|xpath=//div[@id="x"]|' "$SFX/TEST_SURFACE.golden.md" > "$_t/xp.md"
_o=$(sh "$LTS" "$_t/xp.md" 2>&1); _ec=$?
_ts_nonzero "$_ec" "ts-4: XPath selector rejected"

# ── ts-5: duplicate screen fails ──────────────────────────────────────────────
_o=$(sh "$LTS" "$SFX/TEST_SURFACE.dup-screen.md" 2>&1); _ec=$?
_ts_nonzero "$_ec" "ts-5: duplicate SURFACE screen rejected"
assert_contains "$_o" "DUPLICATE_SCREEN" "ts-5: names DUPLICATE_SCREEN"

# ── ts-6: valid structured gap passes ─────────────────────────────────────────
sh "$LTS" "$SFX/TEST_SURFACE.gap-valid.md" >/dev/null 2>&1
assert_eq 0 $? "ts-6: valid structured gap passes lint"

# ── ts-7: expired gap fails ───────────────────────────────────────────────────
_o=$(sh "$LTS" "$SFX/TEST_SURFACE.gap-expired.md" 2>&1); _ec=$?
_ts_nonzero "$_ec" "ts-7: expired gap fails"
assert_contains "$_o" "GAP_EXPIRED" "ts-7: names GAP_EXPIRED"

# ── ts-8: gap with unknown reason enum fails ──────────────────────────────────
sed 's/"NOT_IMPLEMENTED"/"LATER"/' "$SFX/TEST_SURFACE.gap-valid.md" > "$_t/badreason.md"
_o=$(sh "$LTS" "$_t/badreason.md" 2>&1); _ec=$?
_ts_nonzero "$_ec" "ts-8: unknown gap reason rejected"

# ── ts-9: gap with blank owner fails ──────────────────────────────────────────
sed 's/  owner: "prince"/  owner: ""/' "$SFX/TEST_SURFACE.gap-valid.md" > "$_t/blankowner.md"
_o=$(sh "$LTS" "$_t/blankowner.md" 2>&1); _ec=$?
_ts_nonzero "$_ec" "ts-9: blank gap owner rejected"

# ── ts-10: empty surface (zero screens, zero gaps) fails (anti-vacuous) ───────
printf '# TEST_SURFACE\n\nprose only\n' > "$_t/empty.md"
_o=$(sh "$LTS" "$_t/empty.md" 2>&1); _ec=$?
_ts_nonzero "$_ec" "ts-10: empty surface fails (anti-vacuous)"

rm -rf "$_t"
