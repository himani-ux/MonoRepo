# shellcheck shell=sh
# uat-preflight_test.sh — uat-preflight.sh (spec DC-8), the composed
# single-entry UAT run preflight: lint-journey-map.sh + check-surface-
# staleness.sh + check-uat-preconditions.sh, in order, fail-closed, pass-
# through diagnostics. Model: surface-staleness_test.sh (surface-promote.sh
# fixture-build idiom) + uat-preconditions_test.sh (preflight fixture map +
# probe fixtures, reused rather than forked).

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
GATE="$TESTS_DIR/../bin/uat-preflight.sh"
SP="$TESTS_DIR/../bin/surface-promote.sh"
LINT_FX="$TESTS_DIR/fixtures/lint"
GENDIR="$TESTS_DIR/fixtures/gen"
SFX="$TESTS_DIR/fixtures/surface"
PFX="$TESTS_DIR/fixtures/preflight"
MAP="$PFX/map-preconditions.md"
PROBE_OK="$PFX/probe-ok.sh"
PROBE_AUTH_FAILS="$PFX/probe-auth-fails.sh"

_upf_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

# ── scratch: a freshly promoted TEST_SURFACE + provenance sibling, and a
#    STALE variant (APP_FLOW modified after promote), both anchored to the
#    same golden APP_FLOW/TEST_SURFACE pair surface-staleness_test.sh uses.
_upf_t=$(mktemp -d)
cp "$GENDIR/APP_FLOW.md" "$_upf_t/APP_FLOW.md"
FRESH_SURFACE="$_upf_t/TEST_SURFACE.md"
sh "$SP" "$_upf_t/APP_FLOW.md" "$SFX/TEST_SURFACE.golden.md" "$FRESH_SURFACE" --approve >/dev/null 2>&1
assert_eq 0 $? "setup: surface-promote.sh builds a fresh anchored TEST_SURFACE"

NO_PROV_SURFACE="$_upf_t/unanchored/TEST_SURFACE.md"
mkdir -p "$_upf_t/unanchored"
cp "$SFX/TEST_SURFACE.golden.md" "$NO_PROV_SURFACE"

# ── 1. wrong arg count → exit 2 ───────────────────────────────────────────
assert_exit 2 /bin/sh "$GATE"
assert_exit 2 /bin/sh "$GATE" "$MAP"
assert_exit 2 /bin/sh "$GATE" "$MAP" "$FRESH_SURFACE"
assert_exit 2 /bin/sh "$GATE" "$MAP" "$FRESH_SURFACE" "$_upf_t/APP_FLOW.md" extra-arg

# ── 2. missing MAP file → exit 2 ──────────────────────────────────────────
assert_exit 2 /bin/sh "$GATE" "$PFX/does-not-exist.md" "$FRESH_SURFACE" "$_upf_t/APP_FLOW.md"

# ── 3. missing TEST_SURFACE file → exit 2 ─────────────────────────────────
assert_exit 2 /bin/sh "$GATE" "$MAP" "$_upf_t/nope-surface.md" "$_upf_t/APP_FLOW.md"

# ── 4. missing APP_FLOW file → exit 2 ─────────────────────────────────────
assert_exit 2 /bin/sh "$GATE" "$MAP" "$FRESH_SURFACE" "$_upf_t/nope-flow.md"

# ── 5. step 1 (lint) fails → PREFLIGHT_FAILED: step 1, exit 1, lint's own
#    diagnostic passed through. Paired with a STALE surface too, to prove
#    ORDER — step 1's failure is reported, never step 2's. ────────────────
_upf_out=$(/bin/sh "$GATE" "$LINT_FX/bad-enum.md" "$NO_PROV_SURFACE" "$_upf_t/APP_FLOW.md" 2>&1); _upf_rc=$?
assert_eq "1" "$_upf_rc" "preflight: lint-failing map exits 1"
assert_contains "$_upf_out" "PREFLIGHT_FAILED: step 1 (lint-journey-map.sh)" \
  "preflight: reports step 1 failure"
assert_not_contains "$_upf_out" "PROVENANCE_MISSING" \
  "preflight: step 2 (surface staleness) never ran when step 1 already failed (composition order)"

# ── 6. step 2 (surface staleness) fails → PREFLIGHT_FAILED: step 2, exit 1,
#    check-surface-staleness.sh's own PROVENANCE_MISSING passed through ───
_upf_out=$(/bin/sh "$GATE" "$MAP" "$NO_PROV_SURFACE" "$_upf_t/APP_FLOW.md" 2>&1); _upf_rc=$?
assert_eq "1" "$_upf_rc" "preflight: unanchored surface exits 1"
assert_contains "$_upf_out" "PROVENANCE_MISSING" \
  "preflight: step 2's own diagnostic (PROVENANCE_MISSING) passed through"
assert_contains "$_upf_out" "PREFLIGHT_FAILED: step 2 (check-surface-staleness.sh)" \
  "preflight: reports step 2 failure"

# ── 7. step 3 (preconditions) fails → PREFLIGHT_FAILED: step 3, exit 1,
#    check-uat-preconditions.sh's own PRECONDITION_ENV_UNSET passed through ─
_upf_out=$(env -u UAT_BASE_URL /bin/sh "$GATE" "$MAP" "$FRESH_SURFACE" "$_upf_t/APP_FLOW.md" 2>&1); _upf_rc=$?
assert_eq "1" "$_upf_rc" "preflight: unset UAT_BASE_URL (step 3 fails) exits 1"
assert_contains "$_upf_out" "PRECONDITION_ENV_UNSET" \
  "preflight: step 3's own diagnostic (PRECONDITION_ENV_UNSET) passed through"
assert_contains "$_upf_out" "PREFLIGHT_FAILED: step 3 (check-uat-preconditions.sh)" \
  "preflight: reports step 3 failure"

# ── 8. all three green → UAT-PREFLIGHT: green (<map> <surface>), exit 0 ──
_upf_out=$(env -u RUN_UAT_PREFLIGHT UAT_BASE_URL=http://127.0.0.1:3002 \
  /bin/sh "$GATE" "$MAP" "$FRESH_SURFACE" "$_upf_t/APP_FLOW.md" 2>&1); _upf_rc=$?
assert_eq "0" "$_upf_rc" "preflight: all three gates green → exit 0"
assert_contains "$_upf_out" "UAT-PREFLIGHT: green ($MAP $FRESH_SURFACE)" \
  "preflight: exact summary line names the map and surface"

# ── 9. env passthrough — RUN_UAT_PREFLIGHT / UAT_PREFLIGHT_PROBE reach
#    check-uat-preconditions.sh untouched; this wrapper adds nothing ──────
# 9a: a failing probe surfaces step 3's own PRECONDITION_UNMET
_upf_out=$(UAT_BASE_URL=http://127.0.0.1:3002 RUN_UAT_PREFLIGHT=1 \
  UAT_PREFLIGHT_PROBE="$PROBE_AUTH_FAILS" \
  /bin/sh "$GATE" "$MAP" "$FRESH_SURFACE" "$_upf_t/APP_FLOW.md" 2>&1); _upf_rc=$?
assert_eq "1" "$_upf_rc" "preflight: env-passthrough failing probe exits 1"
assert_contains "$_upf_out" "PRECONDITION_UNMET" \
  "preflight: env-passthrough — RUN_UAT_PREFLIGHT/UAT_PREFLIGHT_PROBE actually reached the probe"
assert_contains "$_upf_out" "PREFLIGHT_FAILED: step 3 (check-uat-preconditions.sh)" \
  "preflight: env-passthrough failing probe reports step 3 failure"

# 9b: a passing probe still reaches full green (proves the wrapper doesn't
# swallow or override RUN_UAT_PREFLIGHT/UAT_PREFLIGHT_PROBE on success either)
assert_exit 0 env UAT_BASE_URL=http://127.0.0.1:3002 RUN_UAT_PREFLIGHT=1 \
  UAT_PREFLIGHT_PROBE="$PROBE_OK" /bin/sh "$GATE" "$MAP" "$FRESH_SURFACE" "$_upf_t/APP_FLOW.md"

rm -rf "$_upf_t"
