# shellcheck shell=sh
# surface-promote_test.sh — surface-promote.sh + check-test-surface.sh proofs.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
SP="$TESTS_DIR/../bin/surface-promote.sh"
CTS="$TESTS_DIR/../bin/check-test-surface.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
SFX="$TESTS_DIR/fixtures/surface"

_sp_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

_t=$(mktemp -d)

# ── sp-1: promotion is NEVER automatic — missing --approve refused ────────────
_o=$(sh "$SP" "$GENDIR/APP_FLOW.md" "$SFX/TEST_SURFACE.golden.md" "$_t/TEST_SURFACE.md" 2>&1); _ec=$?
_sp_nonzero "$_ec" "sp-1: all gates pass but no --approve → refused"
assert_contains "$_o" "approve" "sp-1: refusal names the missing --approve"
[ ! -f "$_t/TEST_SURFACE.md" ]
assert_eq 0 $? "sp-1: no write without --approve"

# ── sp-2: lint-failing candidate refused even with --approve ──────────────────
_o=$(sh "$SP" "$GENDIR/APP_FLOW.md" "$SFX/TEST_SURFACE.css-selector.md" "$_t/TEST_SURFACE.md" --approve 2>&1); _ec=$?
_sp_nonzero "$_ec" "sp-2: lint-failing candidate refused"
[ ! -f "$_t/TEST_SURFACE.md" ]
assert_eq 0 $? "sp-2: no write on lint refusal"

# ── sp-3: coverage-failing candidate refused ──────────────────────────────────
_o=$(sh "$SP" "$GENDIR/APP_FLOW.md" "$SFX/TEST_SURFACE.invented-screen.md" "$_t/TEST_SURFACE.md" --approve 2>&1); _ec=$?
_sp_nonzero "$_ec" "sp-3: coverage-failing candidate refused"

# ── sp-4: golden candidate + --approve installs byte-identically ──────────────
sh "$SP" "$GENDIR/APP_FLOW.md" "$SFX/TEST_SURFACE.golden.md" "$_t/TEST_SURFACE.md" --approve >/dev/null 2>&1
assert_eq 0 $? "sp-4: golden candidate promotes with --approve"
cmp -s "$_t/TEST_SURFACE.md" "$SFX/TEST_SURFACE.golden.md"
assert_eq 0 $? "sp-4: installed surface is byte-identical (no repair, no merge)"

# ── cts-1: RUN_APP_CHECK unset → clear skip, exit 0 ──────────────────────────
_o=$(env -u RUN_APP_CHECK sh "$CTS" "$SFX/TEST_SURFACE.golden.md" 2>&1); _ec=$?
assert_eq 0 "$_ec" "cts-1: RUN_APP_CHECK unset → exit 0"
assert_contains "$_o" "skip" "cts-1: prints a clear skip message"

# ── cts-2: non-playwright runner → RUNNER_UNSUPPORTED ─────────────────────────
_o=$(RUN_APP_CHECK=1 JOURNEY_RUNNER=maestro sh "$CTS" "$SFX/TEST_SURFACE.golden.md" 2>&1); _ec=$?
_sp_nonzero "$_ec" "cts-2: non-playwright runner fails closed"
assert_contains "$_o" "RUNNER_UNSUPPORTED" "cts-2: names RUNNER_UNSUPPORTED"

# ── cts-3: lint-invalid surface fails BEFORE driving any app ──────────────────
_o=$(RUN_APP_CHECK=1 JOURNEY_RUNNER=playwright sh "$CTS" "$SFX/TEST_SURFACE.css-selector.md" 2>&1); _ec=$?
_sp_nonzero "$_ec" "cts-3: invalid surface rejected before app check"

# ── cts-4: node missing → fail closed, never a silent pass ────────────────────
_o=$(env PATH="/usr/bin:/bin" RUN_APP_CHECK=1 JOURNEY_RUNNER=playwright sh "$CTS" "$SFX/TEST_SURFACE.golden.md" 2>&1); _ec=$?
if command -v node >/dev/null 2>&1 && env PATH="/usr/bin:/bin" command -v node >/dev/null 2>&1; then
  printf 'ok: cts-4 skipped (node present on stripped PATH)\n'
else
  _sp_nonzero "$_ec" "cts-4: missing node fails closed under RUN_APP_CHECK=1"
fi

rm -rf "$_t"
