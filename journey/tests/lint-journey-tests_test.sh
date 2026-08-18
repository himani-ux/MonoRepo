# shellcheck shell=sh
# lint-journey-tests_test.sh — blindness + discipline lint proofs (Increment 2).
# The spec's entire allowance comes from its author bundle; anything beyond it
# is a blindness violation.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LJT="$TESTS_DIR/../bin/lint-journey-tests.sh"
AB="$TESTS_DIR/../bin/author-bundle.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
SFX="$TESTS_DIR/fixtures/surface"
GSPEC="$TESTS_DIR/fixtures/author/journey-101.spec.golden.ts"
GMAP="$GENDIR/golden/expected-journey-map.generated.md"

_lj_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

_t=$(mktemp -d)
sh "$AB" "$GMAP" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t" >/dev/null 2>&1
BUNDLE="$_t/author-bundle-journey-101.md"

# ── lj-1: golden blind spec passes ────────────────────────────────────────────
sh "$LJT" "$GSPEC" "$BUNDLE" >/dev/null 2>&1
assert_eq 0 $? "lj-1: golden blind spec passes the lint"

# ── lj-2: non-playwright import fails ─────────────────────────────────────────
sed "s|import { test, expect } from '@playwright/test';|import { test, expect } from '@playwright/test';\nimport { db } from '../../src/db';|" "$GSPEC" > "$_t/s2.ts"
_o=$(sh "$LJT" "$_t/s2.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-2: source-code import rejected"
assert_contains "$_o" "FORBIDDEN_IMPORT" "lj-2: names FORBIDDEN_IMPORT"

# ── lj-3: fs / child_process rejected ─────────────────────────────────────────
sed "s|import { test, expect } from '@playwright/test';|import { test, expect } from '@playwright/test';\nimport fs from 'fs';|" "$GSPEC" > "$_t/s3.ts"
_o=$(sh "$LJT" "$_t/s3.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-3: fs import rejected"

# ── lj-4: page.evaluate rejected ──────────────────────────────────────────────
sed "s|await page.goto('/invoices');|await page.goto('/invoices');\n  await page.evaluate(() => window.__state);|" "$GSPEC" > "$_t/s4.ts"
_o=$(sh "$LJT" "$_t/s4.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-4: page.evaluate rejected"
assert_contains "$_o" "EVALUATE_FORBIDDEN" "lj-4: names EVALUATE_FORBIDDEN"

# ── lj-5: raw CSS locator rejected ────────────────────────────────────────────
sed "s|page.getByTestId('upload-error')|page.locator('div.error > span')|" "$GSPEC" > "$_t/s5.ts"
_o=$(sh "$LJT" "$_t/s5.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-5: raw CSS locator rejected"
assert_contains "$_o" "RAW_LOCATOR" "lj-5: names RAW_LOCATOR"

# ── lj-6: selector outside the bundle's surface rejected ──────────────────────
sed "s|page.getByTestId('upload-error')|page.getByTestId('admin-panel')|" "$GSPEC" > "$_t/s6.ts"
_o=$(sh "$LJT" "$_t/s6.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-6: testid outside the allowed surface rejected"
assert_contains "$_o" "SELECTOR_OUT_OF_SURFACE" "lj-6: names SELECTOR_OUT_OF_SURFACE"

# ── lj-7: role selector outside the surface rejected ──────────────────────────
sed "s|// step 4. observe status=ACCEPTED in the invoice list|await page.getByRole('button', { name: 'Delete all' }).click();|" "$GSPEC" > "$_t/s7.ts"
_o=$(sh "$LJT" "$_t/s7.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-7: role selector outside the surface rejected"

# ── lj-8: route outside the bundle rejected ───────────────────────────────────
sed "s|await page.goto('/invoices');|await page.goto('/admin');|" "$GSPEC" > "$_t/s8.ts"
_o=$(sh "$LJT" "$_t/s8.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-8: route outside the surface rejected"
assert_contains "$_o" "ROUTE_OUT_OF_SURFACE" "lj-8: names ROUTE_OUT_OF_SURFACE"

# ── lj-9: API call outside public_api rejected ────────────────────────────────
sed "s|await page.goto('/invoices');|await page.goto('/invoices');\n  await page.request.post('/internal/reset');|" "$GSPEC" > "$_t/s9.ts"
_o=$(sh "$LJT" "$_t/s9.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-9: API outside public_api rejected"
assert_contains "$_o" "API_OUT_OF_SURFACE" "lj-9: names API_OUT_OF_SURFACE"

# ── lj-10: missing ORACLE comment rejected ────────────────────────────────────
grep -v '// ORACLE:' "$GSPEC" > "$_t/s10.ts"
_o=$(sh "$LJT" "$_t/s10.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-10: missing ORACLE comment rejected"
assert_contains "$_o" "ORACLE_COMMENT_MISSING" "lj-10: names ORACLE_COMMENT_MISSING"

# ── lj-11: ORACLE comment that does not match the journey oracle rejected ─────
sed 's|// ORACLE: .*|// ORACLE: something the author made up|' "$GSPEC" > "$_t/s11.ts"
_o=$(sh "$LJT" "$_t/s11.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-11: paraphrased ORACLE comment rejected"
assert_contains "$_o" "ORACLE_TEXT_MISMATCH" "lj-11: names ORACLE_TEXT_MISMATCH"

# ── lj-12: ORACLE comment without a nearby assertion rejected ─────────────────
awk '{ print } /\/\/ ORACLE:/ { print "});" ; exit }' "$GSPEC" > "$_t/s12.ts"
_o=$(sh "$LJT" "$_t/s12.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-12: ORACLE comment without adjacent expect rejected"
assert_contains "$_o" "ORACLE_ASSERTION_MISSING" "lj-12: names ORACLE_ASSERTION_MISSING"

# ── lj-13: zero-assertion spec rejected ───────────────────────────────────────
grep -v 'await expect(' "$GSPEC" > "$_t/s13.ts"
_o=$(sh "$LJT" "$_t/s13.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-13: zero-assertion spec rejected"
assert_contains "$_o" "ZERO_ASSERTIONS" "lj-13: names ZERO_ASSERTIONS"

# ── lj-14: runtime-truth key in a spec rejected ───────────────────────────────
sed "s|// step 1. land on /invoices (state: EMPTY)|// ci_status: GREEN|" "$GSPEC" > "$_t/s14.ts"
_o=$(sh "$LJT" "$_t/s14.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-14: runtime-truth key rejected"

# ── lj-15: dynamic import / eval rejected ─────────────────────────────────────
sed "s|await page.goto('/invoices');|const m = await import('node:fs');\n  await page.goto('/invoices');|" "$GSPEC" > "$_t/s15.ts"
_o=$(sh "$LJT" "$_t/s15.ts" "$BUNDLE" 2>&1); _ec=$?
_lj_nonzero "$_ec" "lj-15: dynamic import rejected"

rm -rf "$_t"
