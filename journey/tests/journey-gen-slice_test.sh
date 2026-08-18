#!/bin/sh
# journey-gen-slice_test.sh — TDD proofs for journey-gen-slice.sh
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
SLICE="$TESTS_DIR/../bin/journey-gen-slice.sh"
FX="$TESTS_DIR/fixtures/gen"

# ── Golden fixtures: exit 0, correct bundles and exclusions ──────────────────
_out=$(mktemp -d)
sh "$SLICE" "$FX/SSOT.md" "$FX/PRD.md" "$FX/APP_FLOW.md" "$_out" >/dev/null 2>&1
assert_eq 0 $? "slicer exits 0 on golden docs"

# P0/P1 FEAT-IDs bundled, P2/P3 excluded
assert_eq "FEAT-001 FEAT-002" \
  "$(jq -r '[.bundles[]|select(.source_type=="FEAT")|.id]|sort|join(" ")' \
      "$_out/bundle-manifest.json")" \
  "P0/P1 FEATs bundled (FEAT-003 P2 excluded)"
assert_eq "FEAT-003" \
  "$(jq -r '.excluded_features[0].id' "$_out/bundle-manifest.json")" \
  "FEAT-003 (P2) in excluded_features"

# Bundle carries BOTH sides: PRD oracle material and APP_FLOW steps
assert_contains "$(cat "$_out/bundles/feat-001.md")" "acceptance_criteria" \
  "feat bundle has PRD oracle material"
assert_contains "$(cat "$_out/bundles/feat-001.md")" "AFJ-001" \
  "feat bundle has linked APP_FLOW steps"
rm -rf "$_out"

# ── Fail-closed: PRD with no priority field (PRD_PRIORITY_UNPARSEABLE) ───────
_t=$(mktemp -d)
assert_exit 1 sh "$SLICE" \
  "$FX/SSOT.md" "$FX/bad/PRD-no-priority.md" "$FX/APP_FLOW.md" "$_t"
rm -rf "$_t"

# ── Fail-closed: APP_FLOW with un-id'd journey heading (APP_FLOW_UNIDDED) ────
_t=$(mktemp -d)
assert_exit 1 sh "$SLICE" \
  "$FX/SSOT.md" "$FX/PRD.md" "$FX/bad/APP_FLOW-unidded.md" "$_t"
rm -rf "$_t"

# ── Fail-closed: missing input file ──────────────────────────────────────────
_t=$(mktemp -d)
assert_exit 1 sh "$SLICE" \
  "$FX/SSOT.md" "$FX/PRD.md" "$FX/NOPE.md" "$_t"
rm -rf "$_t"

# ── Unlinked: P0 FEAT with no FEAT<->AFJ link → recorded but no partial bundle
_uout=$(mktemp -d)
sh "$SLICE" \
  "$FX/SSOT.md" "$FX/unlinked/PRD.md" "$FX/unlinked/APP_FLOW.md" "$_uout" \
  >/dev/null 2>&1
assert_eq 0 $? \
  "slicer exits 0 when a P0 FEAT has no links (unlinked, not an error)"
assert_contains \
  "$(jq -r '[.unlinked[].id]|join(" ")' "$_uout/bundle-manifest.json")" \
  "FEAT-004" \
  "FEAT-004 recorded in unlinked[]"
assert_contains \
  "$(jq -r '.unlinked[]|select(.id=="FEAT-004")|.reason' \
      "$_uout/bundle-manifest.json")" \
  "no" \
  "FEAT-004 unlinked entry has a reason string"
_partial="yes"
[ -f "$_uout/bundles/feat-004.md" ] || _partial="no"
assert_eq "no" "$_partial" "unlinked FEAT-004 emits no partial bundle"
rm -rf "$_uout"

# ── Dangling FEAT→AFJ: FEAT-005 covers_flows: AFJ-999 (no AFJ-999 block) ────
_dout=$(mktemp -d)
sh "$SLICE" \
  "$FX/SSOT.md" "$FX/dangling/feat-to-missing/PRD.md" \
  "$FX/dangling/feat-to-missing/APP_FLOW.md" "$_dout" >/dev/null 2>&1
assert_eq 0 $? \
  "dangling FEAT->AFJ: slicer exits 0 (dangling is unlinked, not an error)"
assert_contains \
  "$(jq -r '[.unlinked[].id]|join(" ")' "$_dout/bundle-manifest.json")" \
  "FEAT-005" \
  "dangling FEAT->AFJ: FEAT-005 in unlinked[]"
assert_contains \
  "$(jq -r '.unlinked[]|select(.id=="FEAT-005")|.reason' \
      "$_dout/bundle-manifest.json")" \
  "not found" \
  "dangling FEAT->AFJ: FEAT-005 reason mentions missing counterpart"
_partial="yes"
[ -f "$_dout/bundles/feat-005.md" ] || _partial="no"
assert_eq "no" "$_partial" "dangling FEAT->AFJ: no partial bundle emitted for FEAT-005"
rm -rf "$_dout"

# ── Dangling AFJ→FEAT: AFJ-005 covers_features: FEAT-999 (no FEAT-999 block) ─
_dout=$(mktemp -d)
sh "$SLICE" \
  "$FX/SSOT.md" "$FX/dangling/afj-to-missing/PRD.md" \
  "$FX/dangling/afj-to-missing/APP_FLOW.md" "$_dout" >/dev/null 2>&1
assert_eq 0 $? \
  "dangling AFJ->FEAT: slicer exits 0 (dangling is unlinked, not an error)"
assert_contains \
  "$(jq -r '[.unlinked[].id]|join(" ")' "$_dout/bundle-manifest.json")" \
  "AFJ-005" \
  "dangling AFJ->FEAT: AFJ-005 in unlinked[]"
assert_contains \
  "$(jq -r '.unlinked[]|select(.id=="AFJ-005")|.reason' \
      "$_dout/bundle-manifest.json")" \
  "not found" \
  "dangling AFJ->FEAT: AFJ-005 reason mentions missing counterpart"
_partial="yes"
[ -f "$_dout/bundles/afj-005.md" ] || _partial="no"
assert_eq "no" "$_partial" "dangling AFJ->FEAT: no partial bundle emitted for AFJ-005"
rm -rf "$_dout"

# ── Anti-vacuous (review C4): absent blocks fail closed like malformed ones ──
# A PRD with zero FEAT blocks / an APP_FLOW with zero AFJ journeys previously
# produced ZERO bundles and exit 0 — the whole pipeline then passed vacuously.
_t=$(mktemp -d)
printf '# PRD\n\nProse only. No FEAT blocks at all.\n' > "$_t/PRD-empty.md"
printf '# APP_FLOW\n\n## User Journeys\n\n### AFJ-001 — Upload\nsteps.\n' > "$_t/AFJ-ok.md"
_err=$(sh "$SLICE" "$FX/SSOT.md" "$_t/PRD-empty.md" "$_t/AFJ-ok.md" "$_t/out1" 2>&1 >/dev/null); _ec=$?
assert_nonzero_slice() { if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else printf 'FAIL: %s (expected non-zero, got 0)\n' "$2"; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi }
assert_nonzero_slice "$_ec" "anti-vacuous: PRD with zero FEAT blocks fails closed"
assert_contains "$_err" "PRD_NO_FEAT_BLOCKS" "anti-vacuous: diagnostic names PRD_NO_FEAT_BLOCKS"

printf '# PRD\n\n## FEAT-001 — Upload\npriority: P0\nuser_story: as a user I upload\nacceptance_criteria:\n- AC-1: it uploads\nflows: AFJ-001\n' > "$_t/PRD-ok.md"
printf '# APP_FLOW\n\nProse. No User Journeys section.\n' > "$_t/AFJ-empty.md"
_err=$(sh "$SLICE" "$FX/SSOT.md" "$_t/PRD-ok.md" "$_t/AFJ-empty.md" "$_t/out2" 2>&1 >/dev/null); _ec=$?
assert_nonzero_slice "$_ec" "anti-vacuous: APP_FLOW with zero AFJ journeys fails closed"
assert_contains "$_err" "APP_FLOW_NO_JOURNEYS" "anti-vacuous: diagnostic names APP_FLOW_NO_JOURNEYS"

printf '# PRD\n\n## FEAT-001 — Later\npriority: P2\nuser_story: later\nacceptance_criteria:\n- AC-1: later\nflows: AFJ-001\n' > "$_t/PRD-p2only.md"
_err=$(sh "$SLICE" "$FX/SSOT.md" "$_t/PRD-p2only.md" "$_t/AFJ-ok.md" "$_t/out3" 2>&1 >/dev/null); _ec=$?
assert_nonzero_slice "$_ec" "anti-vacuous: all-P2/P3 PRD (zero required FEATs) fails closed"
assert_contains "$_err" "NO_P01_FEATURES" "anti-vacuous: diagnostic names NO_P01_FEATURES"
rm -rf "$_t"

# ── Generation Context injection (review C3/I3/I4) ────────────────────────────
# Bundles must carry: the INLINED template schema (the generator may read ONLY
# the bundle — a SCHEMA: pointer contradicted the read boundary), a
# deterministic GAP_EXPIRY date, and a resolved RUNNER when JOURNEY_RUNNER is
# set (validated against the resolver's enum; the generator copies verbatim).
_gc=$(mktemp -d)
JOURNEY_RUNNER=playwright sh "$SLICE" "$FX/SSOT.md" "$FX/PRD.md" "$FX/APP_FLOW.md" "$_gc" >/dev/null 2>&1
assert_eq 0 $? "gen-context: slicer exits 0 with JOURNEY_RUNNER set"
_b=$(cat "$_gc/bundles/feat-001.md")
assert_contains "$_b" "RUNNER: playwright" "gen-context: bundle carries the resolved RUNNER"
assert_contains "$_b" "GAP_EXPIRY: 20" "gen-context: bundle carries a deterministic GAP_EXPIRY date"
assert_contains "$_b" "oracle_surface ∈ {UI, API, UI+API}" "gen-context: template schema is INLINED (not a pointer)"
assert_not_contains "$_b" "SCHEMA: journey/JOURNEY_MAP.template.md" "gen-context: the SCHEMA pointer is gone"
rm -rf "$_gc"

_gc=$(mktemp -d)
JOURNEY_RUNNER=cypress sh "$SLICE" "$FX/SSOT.md" "$FX/PRD.md" "$FX/APP_FLOW.md" "$_gc" >/dev/null 2>&1
_ec=$?
if [ "$_ec" -ne 0 ]; then printf 'ok: gen-context: unknown JOURNEY_RUNNER fails closed\n'; else
  printf 'FAIL: gen-context: unknown JOURNEY_RUNNER accepted\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
rm -rf "$_gc"
