# shellcheck shell=sh
# surface-coverage_test.sh — check-surface-coverage.sh + surface-gen-slice.sh
# proofs (Increment 2). Anchors are re-derived from APP_FLOW; generator output
# is never trusted for coverage.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
CSC="$TESTS_DIR/../bin/check-surface-coverage.sh"
SGS="$TESTS_DIR/../bin/surface-gen-slice.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
SFX="$TESTS_DIR/fixtures/surface"

_sc_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

_t=$(mktemp -d)

# ── sc-1: golden APP_FLOW + golden surface → coverage passes ──────────────────
sh "$CSC" "$GENDIR/APP_FLOW.md" "$SFX/TEST_SURFACE.golden.md" >/dev/null 2>&1
assert_eq 0 $? "sc-1: golden surface covers the golden APP_FLOW screens"

# ── sc-2: invented screen (not in APP_FLOW) fails ─────────────────────────────
_o=$(sh "$CSC" "$GENDIR/APP_FLOW.md" "$SFX/TEST_SURFACE.invented-screen.md" 2>&1); _ec=$?
_sc_nonzero "$_ec" "sc-2: surface screen absent from APP_FLOW rejected"
assert_contains "$_o" "INVENTED_SCREEN" "sc-2: names INVENTED_SCREEN"

# ── sc-3: journey-touched screen missing from surface fails ───────────────────
cat > "$_t/APP_FLOW2.md" << 'DOC'
# APP_FLOW

## User Journeys

### AFJ-001 — "Corrected invoice upload"
covers_features: FEAT-001
steps:
  1. land on /invoices (state: EMPTY)
  2. open /admin to check quota
states: [EMPTY]

## Screens

### SCR-001 — "invoices_list"
route: /invoices
states: [EMPTY, ERROR, SUCCESS]

### SCR-002 — "admin_console"
route: /admin
states: [SUCCESS]
DOC
_o=$(sh "$CSC" "$_t/APP_FLOW2.md" "$SFX/TEST_SURFACE.golden.md" 2>&1); _ec=$?
_sc_nonzero "$_ec" "sc-3: touched screen with no surface entry fails"
assert_contains "$_o" "SURFACE_COVERAGE_GAP" "sc-3: names SURFACE_COVERAGE_GAP"
assert_contains "$_o" "admin_console" "sc-3: names the uncovered screen"

# ── sc-4: a VALID structured gap covers the missing screen ────────────────────
sh "$CSC" "$_t/APP_FLOW2.md" "$SFX/TEST_SURFACE.gap-valid.md" >/dev/null 2>&1
assert_eq 0 $? "sc-4: valid SURFACE-GAP satisfies the touched screen"

# ── sc-5: an EXPIRED gap is not a coverage credit ─────────────────────────────
_o=$(sh "$CSC" "$_t/APP_FLOW2.md" "$SFX/TEST_SURFACE.gap-expired.md" 2>&1); _ec=$?
_sc_nonzero "$_ec" "sc-5: expired gap is not a credit"

# ── sc-6: surface route contradicting APP_FLOW fails ──────────────────────────
sed 's|^route: /invoices$|route: /billing|' "$SFX/TEST_SURFACE.golden.md" > "$_t/route.md"
_o=$(sh "$CSC" "$GENDIR/APP_FLOW.md" "$_t/route.md" 2>&1); _ec=$?
_sc_nonzero "$_ec" "sc-6: surface route contradicting APP_FLOW rejected"
assert_contains "$_o" "ROUTE_MISMATCH" "sc-6: names ROUTE_MISMATCH"

# ── Slicer proofs ─────────────────────────────────────────────────────────────

# ── sg-1: golden docs slice into a per-screen bundle ──────────────────────────
sh "$SGS" "$GENDIR/APP_FLOW.md" "$GENDIR/DESIGN_SYSTEM.md" "$_t/out1" >/dev/null 2>&1
assert_eq 0 $? "sg-1: golden docs slice exits 0"
_b=$(cat "$_t/out1/bundles/scr-001.md" 2>/dev/null)
assert_contains "$_b" "invoices_list" "sg-1: bundle carries the screen name"
assert_contains "$_b" "route: /invoices" "sg-1: bundle carries the route"
assert_contains "$_b" "Upload invoice" "sg-1: bundle carries design-system enrichment"
assert_contains "$_b" "land on /invoices" "sg-1: bundle carries the touching journey steps"
assert_contains "$_b" "## SURFACE: " "sg-1: bundle inlines the frozen SURFACE entry format"

# ── sg-2: screen heading without SCR id fails ─────────────────────────────────
sed 's|^### SCR-001 — "invoices_list"$|### invoices list screen|' "$GENDIR/APP_FLOW.md" > "$_t/unidded.md"
_o=$(sh "$SGS" "$_t/unidded.md" "$GENDIR/DESIGN_SYSTEM.md" "$_t/out2" 2>&1); _ec=$?
_sc_nonzero "$_ec" "sg-2: screen heading without SCR-<n> id fails"
assert_contains "$_o" "SCREEN_UNIDDED" "sg-2: names SCREEN_UNIDDED"

# ── sg-3: screen without route fails ──────────────────────────────────────────
sed 's|^route: /invoices$||' "$GENDIR/APP_FLOW.md" > "$_t/noroute.md"
_o=$(sh "$SGS" "$_t/noroute.md" "$GENDIR/DESIGN_SYSTEM.md" "$_t/out3" 2>&1); _ec=$?
_sc_nonzero "$_ec" "sg-3: screen without route fails"
assert_contains "$_o" "SCREEN_NO_ROUTE" "sg-3: names SCREEN_NO_ROUTE"

# ── sg-4: duplicate screen id fails ───────────────────────────────────────────
{ cat "$GENDIR/APP_FLOW.md"; printf '\n### SCR-001 — "dup_screen"\nroute: /dup\nstates: [EMPTY]\n'; } > "$_t/dup.md"
_o=$(sh "$SGS" "$_t/dup.md" "$GENDIR/DESIGN_SYSTEM.md" "$_t/out4" 2>&1); _ec=$?
_sc_nonzero "$_ec" "sg-4: duplicate SCR id fails"
assert_contains "$_o" "DUPLICATE_SCREEN_ID" "sg-4: names DUPLICATE_SCREEN_ID"

# ── sg-5: zero screens fails (anti-vacuous) ───────────────────────────────────
sed '/^## Screens$/,$d' "$GENDIR/APP_FLOW.md" > "$_t/noscreens.md"
_o=$(sh "$SGS" "$_t/noscreens.md" "$GENDIR/DESIGN_SYSTEM.md" "$_t/out5" 2>&1); _ec=$?
_sc_nonzero "$_ec" "sg-5: APP_FLOW without screens fails"
assert_contains "$_o" "NO_SCREENS" "sg-5: names NO_SCREENS"

# ── sg-6: no design-system material still builds (enrichment, not oracle) ────
printf '# Design System\n\nNothing about invoices here.\n' > "$_t/ds-empty.md"
sh "$SGS" "$GENDIR/APP_FLOW.md" "$_t/ds-empty.md" "$_t/out6" >/dev/null 2>&1
assert_eq 0 $? "sg-6: screen without design material still bundles"
[ -f "$_t/out6/bundles/scr-001.md" ]
assert_eq 0 $? "sg-6: bundle file exists"

# ── sg-7: prefixed SCR id (project prefix) slices like a bare id ───────────────
# Parser parity with the preflight (check-doc-format.sh §3b): a project using
# SCR-SMS-1 must slice, not die SCREEN_UNIDDED.
cat > "$_t/prefixed.md" << 'DOC'
# APP_FLOW

## User Journeys

### AFJ-001 — "SMS registration"
covers_features: FEAT-SMS-001
steps:
  1. land on /register (state: EMPTY)
states: [EMPTY]

## Screens

### SCR-SMS-1 — "register"
route: /register
states: [EMPTY, SUCCESS]
DOC
sh "$SGS" "$_t/prefixed.md" "$GENDIR/DESIGN_SYSTEM.md" "$_t/out7" >/dev/null 2>&1
assert_eq 0 $? "sg-7: prefixed SCR-SMS-1 slices, exits 0"
_b7=$(cat "$_t/out7/bundles/scr-sms-1.md" 2>/dev/null)
assert_contains "$_b7" "register" "sg-7: bundle carries the screen name"
assert_contains "$_b7" "route: /register" "sg-7: bundle carries the route"
assert_contains "$_b7" "land on /register" "sg-7: bundle carries the touching journey steps"

rm -rf "$_t"
