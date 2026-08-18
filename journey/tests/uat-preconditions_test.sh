#!/bin/sh
# uat-preconditions_test.sh — check-uat-preconditions.sh (spec G1), the UAT
# run preflight over declared `preconditions:` entries. No model, no
# network — RUN_UAT_PREFLIGHT=1 cases here use local shell-script probe
# fixtures only.
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
GATE="$TESTS_DIR/../bin/check-uat-preconditions.sh"
GOOD="$TESTS_DIR/fixtures/good/JOURNEY_MAP.md"
LINT_FX="$TESTS_DIR/fixtures/lint"
PFX="$TESTS_DIR/fixtures/preflight"
MAP="$PFX/map-preconditions.md"
PROBE_OK="$PFX/probe-ok.sh"
PROBE_AUTH_FAILS="$PFX/probe-auth-fails.sh"

# ── 1. wrong arg count -> usage on stderr, exit 2 ─────────────────────────
assert_exit 2 /bin/sh "$GATE"
assert_exit 2 /bin/sh "$GATE" "$MAP" extra-arg

# ── 2. missing map file -> exit 2 ─────────────────────────────────────────
assert_exit 2 /bin/sh "$GATE" "$PFX/does-not-exist.md"

# ── 3. lint-failing map -> LINT_FAILED, exit 1 (composes lint-journey-map.sh
#    first; bad-enum.md is an existing lint-red fixture, reused not forked) ─
_upf_out="$(/bin/sh "$GATE" "$LINT_FX/bad-enum.md" 2>&1)"; _upf_rc=$?
assert_eq "1" "$_upf_rc" "preflight: lint-failing map exits 1"
assert_contains "$_upf_out" "LINT_FAILED" "preflight: lint-failing map reports LINT_FAILED"

# ── 4. zero-preconditions map -> NO_PRECONDITIONS, exit 1 (anti-vacuous law;
#    journey/tests/fixtures/good/JOURNEY_MAP.md carries no preconditions:
#    field at all, so it is reused rather than a new fixture) ─────────────
_upf_out="$(/bin/sh "$GATE" "$GOOD" 2>&1)"; _upf_rc=$?
assert_eq "1" "$_upf_rc" "preflight: zero-preconditions map exits 1"
assert_contains "$_upf_out" "NO_PRECONDITIONS" "preflight: zero-preconditions map reports NO_PRECONDITIONS"

# ── 5. map-preconditions.md, UAT_BASE_URL unset -> PRECONDITION_ENV_UNSET ──
_upf_out="$(env -u UAT_BASE_URL /bin/sh "$GATE" "$MAP" 2>&1)"; _upf_rc=$?
assert_eq "1" "$_upf_rc" "preflight: UAT_BASE_URL unset exits 1"
assert_contains "$_upf_out" "PRECONDITION_ENV_UNSET" \
  "preflight: UAT_BASE_URL unset reports PRECONDITION_ENV_UNSET"

# ── 6. UAT_BASE_URL set, RUN_UAT_PREFLIGHT unset (default) -> exit 0,
#    explicit UNPROBED skip line (never a silent skip) ────────────────────
_upf_out="$(env -u RUN_UAT_PREFLIGHT UAT_BASE_URL=http://127.0.0.1:3002 /bin/sh "$GATE" "$MAP" 2>&1)"
_upf_rc=$?
assert_eq "0" "$_upf_rc" "preflight: default run (no RUN_UAT_PREFLIGHT) exits 0"
assert_contains "$_upf_out" "UNPROBED" "preflight: default run reports UNPROBED skip line"

# ── 7. RUN_UAT_PREFLIGHT=1, UAT_PREFLIGHT_PROBE unset -> PROBE_MISSING,
#    exit 1 (opt-in probing fails loud on a missing dependency) ───────────
_upf_out="$(env -u UAT_PREFLIGHT_PROBE UAT_BASE_URL=http://127.0.0.1:3002 RUN_UAT_PREFLIGHT=1 \
  /bin/sh "$GATE" "$MAP" 2>&1)"
_upf_rc=$?
assert_eq "1" "$_upf_rc" "preflight: RUN_UAT_PREFLIGHT=1 with no probe set exits 1"
assert_contains "$_upf_out" "PROBE_MISSING" \
  "preflight: RUN_UAT_PREFLIGHT=1 with no probe set reports PROBE_MISSING"

# ── 8. RUN_UAT_PREFLIGHT=1, probe=probe-auth-fails.sh (the 401 archetype)
#    -> PRECONDITION_UNMET naming the auth entry, exit 1 ──────────────────
_upf_out="$(UAT_BASE_URL=http://127.0.0.1:3002 RUN_UAT_PREFLIGHT=1 \
  UAT_PREFLIGHT_PROBE="$PROBE_AUTH_FAILS" /bin/sh "$GATE" "$MAP" 2>&1)"
_upf_rc=$?
assert_eq "1" "$_upf_rc" "preflight: failing auth probe exits 1"
assert_contains "$_upf_out" "PRECONDITION_UNMET" \
  "preflight: failing auth probe reports PRECONDITION_UNMET"
assert_contains "$_upf_out" "auth: dev-login-bridge" \
  "preflight: failing auth probe names the unmet entry"

# ── 9. RUN_UAT_PREFLIGHT=1, probe=probe-ok.sh, env set -> exit 0 ──────────
assert_exit 0 env UAT_BASE_URL=http://127.0.0.1:3002 RUN_UAT_PREFLIGHT=1 \
  UAT_PREFLIGHT_PROBE="$PROBE_OK" /bin/sh "$GATE" "$MAP"

# ── 10. RUN_UAT_PREFLIGHT=1, UAT_PREFLIGHT_PROBE=/nonexistent ->
#     PROBE_MISSING, exit 1 (not executable, not merely unset) ───────────
_upf_out="$(UAT_BASE_URL=http://127.0.0.1:3002 RUN_UAT_PREFLIGHT=1 \
  UAT_PREFLIGHT_PROBE=/nonexistent /bin/sh "$GATE" "$MAP" 2>&1)"
_upf_rc=$?
assert_eq "1" "$_upf_rc" "preflight: nonexistent probe path exits 1"
assert_contains "$_upf_out" "PROBE_MISSING" \
  "preflight: nonexistent probe path reports PROBE_MISSING"
