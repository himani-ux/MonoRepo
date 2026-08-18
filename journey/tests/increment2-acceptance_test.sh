# shellcheck shell=sh
# increment2-acceptance_test.sh — Increment-2 FULL-LOOP acceptance (opt-in).
#
# Default (RUN_APP_CHECK unset): a single skip line — the default suite stays
# POSIX-only, node-free, model-free.
#
# RUN_APP_CHECK=1: the first executable proof of the layer's core claim:
#   promoted intent → blind-authored spec → lint → real Playwright run
#   against the fixture app → CI stamper writes GREEN → check-journeys.sh
#   passes. Requires node + `npm install` + `npx playwright install chromium`
#   inside journey/surface-check/ (explicit opt-in ⇒ missing deps FAIL loud).

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$TESTS_DIR/../bin"
ISLAND="$TESTS_DIR/../surface-check"
GENDIR="$TESTS_DIR/fixtures/gen"
SFX="$TESTS_DIR/fixtures/surface"
GSPEC="$TESTS_DIR/fixtures/author/journey-101.spec.golden.ts"
GMAP="$GENDIR/golden/expected-journey-map.generated.md"

if [ "${RUN_APP_CHECK:-0}" != "1" ]; then
  printf 'ok: Increment-2 full-loop acceptance SKIPPED (RUN_APP_CHECK unset) — POSIX-only default suite, no node/playwright\n'
else

_i2_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}
_sha() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }

# ── explicit opt-in ⇒ missing deps fail LOUD, never silently skip ─────────────
command -v node >/dev/null 2>&1 || { printf 'FAIL: RUN_APP_CHECK=1 but node is missing\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1)); }
[ -d "$ISLAND/node_modules/@playwright/test" ] || {
  printf 'FAIL: RUN_APP_CHECK=1 but playwright is not installed — run: (cd journey/surface-check && npm install && npx playwright install chromium)\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1)); }

if command -v node >/dev/null 2>&1 && [ -d "$ISLAND/node_modules/@playwright/test" ]; then

# AUTHORITY_FIXTURE_DIR must live under journey/tests — put the whole loop there
_T=$(mktemp -d "$TESTS_DIR/.i2-accept-XXXXXX")
_PORT=4179
_BASE="http://localhost:$_PORT"

PORT=$_PORT node "$ISLAND/fixture-app/server.mjs" >/dev/null 2>&1 &
_SRV=$!
trap 'kill "$_SRV" 2>/dev/null; rm -rf "$_T"' EXIT INT TERM
_up=0
for _i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if curl -s -o /dev/null "$_BASE/invoices"; then _up=1; break; fi
  sleep 0.25
done
assert_eq 1 "$_up" "i2-0: fixture app is reachable at $_BASE"

# ── i2-1: golden TEST_SURFACE execution-verifies against the running app ─────
RUN_APP_CHECK=1 JOURNEY_RUNNER=playwright APP_BASE_URL="$_BASE" \
  sh "$BIN/check-test-surface.sh" "$SFX/TEST_SURFACE.golden.md" >/dev/null 2>&1
assert_eq 0 $? "i2-1: golden surface — every selector resolves in the running app"

# ── i2-2: a stale selector fails loudly ───────────────────────────────────────
sed 's/  - testid=upload-input/  - testid=upload-input\n  - testid=phantom-widget/' \
  "$SFX/TEST_SURFACE.golden.md" > "$_T/stale.md"
_o=$(RUN_APP_CHECK=1 JOURNEY_RUNNER=playwright APP_BASE_URL="$_BASE" \
  sh "$BIN/check-test-surface.sh" "$_T/stale.md" 2>&1); _ec=$?
_i2_nonzero "$_ec" "i2-2: stale selector fails the execution verifier"
assert_contains "$_o" "SELECTOR_STALE" "i2-2: names SELECTOR_STALE"

# ── i2-3: THE FULL LOOP — intent → blind spec → run → GREEN → gate ───────────
# one-journey map (JOURNEY-101 only)
awk '/^## JOURNEY-101/ { inb = 1 } /^## JOURNEY-102/ { inb = 0 } NR <= 8 || inb { print }' \
  "$GMAP" > "$_T/JOURNEY_MAP.md"
mkdir -p "$_T/tests/journeys"
# node resolution: specs outside the island need a node_modules on their
# walk-up path (consuming projects have their own; this is harness-only)
ln -s "$ISLAND/node_modules" "$_T/node_modules"

sh "$BIN/author-bundle.sh" "$_T/JOURNEY_MAP.md" "$SFX/TEST_SURFACE.golden.md" \
  "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" JOURNEY-101 "$_T" >/dev/null 2>&1
assert_eq 0 $? "i2-3a: blind author bundle built"

{ printf 'REFUTER-NO-BLOCK:\n- journey_id: JOURNEY-101\n- checked_hash: %s\n' "$(_sha "$GSPEC")"; } > "$_T/refuter.md"
sh "$BIN/journey-test-promote.sh" --approve JOURNEY-101 "$GSPEC" \
  "$_T/author-bundle-journey-101.md" "$_T/refuter.md" "$_T/JOURNEY_MAP.md" "$_T/tests/journeys" >/dev/null 2>&1
assert_eq 0 $? "i2-3b: spec promoted (lint + hash-bound refuter + --approve)"

( cd "$ISLAND" && JOURNEY_TESTS_DIR="$_T/tests/journeys" APP_BASE_URL="$_BASE" \
  npx playwright test --config=playwright.config.mjs ) >/dev/null 2>&1
_run_ec=$?
assert_eq 0 "$_run_ec" "i2-3c: blind-authored spec PASSES against the fixture app"

if [ "$_run_ec" -eq 0 ]; then
  JOURNEY_STATUS_FILE="$_T/JOURNEY_STATUS.json" \
  JOURNEY_LEDGER_SOURCE="test-fixture://trusted" \
    sh "$BIN/journey-status-stamp.sh" JOURNEY-101 GREEN \
      --run-id i2-acceptance-local --artifact playwright-report/ >/dev/null 2>&1
  assert_eq 0 $? "i2-3d: CI stamper wrote GREEN for JOURNEY-101"

  { printf 'LEDGER_SOURCE=test-fixture\nALLOW_TEST_FIXTURE=1\nLEDGER_PATH=%s\nEXPECTED_SOURCE=test-fixture://trusted\n' \
      "$_T/JOURNEY_STATUS.json"; } > "$_T/ledger.conf"
  AUTHORITY_FIXTURE_DIR="$_T" \
    sh "$BIN/check-journeys.sh" "$_T/ledger.conf" "$_T/JOURNEY_MAP.md" "$_T/tests/journeys" >/dev/null 2>&1
  assert_eq 0 $? "i2-3e: check-journeys.sh passes — intent ∧ blind proof ∧ trusted GREEN (FULL LOOP CLOSED)"
fi

kill "$_SRV" 2>/dev/null
trap - EXIT INT TERM
rm -rf "$_T"
fi
fi
