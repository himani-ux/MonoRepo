#!/bin/sh
# shellcheck shell=sh
# check-journeys_test.sh — TDD proofs for check-journeys.sh (Task 6).
# All 16 proofs per brief §H. Run via: sh journey/tests/check-journeys_test.sh
# Also executed by journey/tests/run.sh (sourced, not subshell).

. "$(dirname "$0")/assert.sh"

# ── local helper: assert exit code is non-zero ────────────────────────────────
_t6_assert_nonzero() { # ACTUAL_CODE MSG
  if [ "$1" -ne 0 ]; then
    printf 'ok: %s\n' "$2"
  else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1))
  fi
}

# ── paths ─────────────────────────────────────────────────────────────────────
_T6_HERE="$(cd "$(dirname "$0")" && pwd)"
_T6_GATE="$_T6_HERE/../bin/check-journeys.sh"
_T6_FX_LEDGER="$_T6_HERE/fixtures/ledger"
_T6_GOOD_MAP="$_T6_HERE/fixtures/good/JOURNEY_MAP.md"
_T6_GOOD_TESTS="$_T6_HERE/fixtures/good/tests/journeys"
_T6_P2_MAP="$_T6_HERE/fixtures/journeys-p2/JOURNEY_MAP.md"
_T6_P2_TESTS="$_T6_HERE/fixtures/journeys-p2/tests/journeys"

# ── temp-file/dir registry ────────────────────────────────────────────────────
_T6_TMPFILES=""
_T6_TMPDIRS=""
_t6_register_tmp()  { _T6_TMPFILES="$_T6_TMPFILES $1"; }
_t6_register_tmpd() { _T6_TMPDIRS="$_T6_TMPDIRS $1"; }

# Helper: write a temp conf file from KEY=value arguments (one per arg)
_t6_mk_conf() {
  _t6c=$(mktemp /tmp/t6-conf-XXXXXXXX)
  _t6_register_tmp "$_t6c"
  for _t6_line in "$@"; do printf '%s\n' "$_t6_line"; done > "$_t6c"
  printf '%s\n' "$_t6c"
}

# ── Reusable confs ─────────────────────────────────────────────────────────────
_T6_CONF_GREEN=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T6_FX_LEDGER/green.json")

# ── PROOF 1: valid P0/P1 + mapped test + GREEN ledger → exit 0 ─────────────────
_t6_out1=$(sh "$_T6_GATE" "$_T6_CONF_GREEN" "$_T6_GOOD_MAP" "$_T6_GOOD_TESTS" 2>&1)
_t6_ec1=$?
assert_eq "0" "$_t6_ec1" "proof-1: GREEN ledger + mapped test → exit 0"

# ── PROOF 2: missing ledger record (empty-journeys.json) → NOT_RUN → exit non-zero
_T6_CONF_EMPTY=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T6_FX_LEDGER/empty-journeys.json")
_t6_out2=$(sh "$_T6_GATE" "$_T6_CONF_EMPTY" "$_T6_GOOD_MAP" "$_T6_GOOD_TESTS" 2>&1)
_t6_ec2=$?
_t6_assert_nonzero "$_t6_ec2" "proof-2: absent ledger record → NOT_RUN → exit non-zero"
assert_contains "$_t6_out2" "NOT_RUN" "proof-2: output mentions NOT_RUN"

# ── PROOF 3: RED → exit non-zero + surfaces failure_summary ───────────────────
_T6_CONF_RED=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T6_FX_LEDGER/red.json")
_t6_out3=$(sh "$_T6_GATE" "$_T6_CONF_RED" "$_T6_GOOD_MAP" "$_T6_GOOD_TESTS" 2>&1)
_t6_ec3=$?
_t6_assert_nonzero "$_t6_ec3" "proof-3: RED ledger → exit non-zero"
assert_contains "$_t6_out3" "RED" "proof-3: output mentions RED"
assert_contains "$_t6_out3" "Step 3 assertion failed" "proof-3: output surfaces failure_summary"

# ── PROOF 4: FLAKY → exit non-zero + surfaces failure_summary ─────────────────
_T6_CONF_FLAKY=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T6_FX_LEDGER/flaky.json")
_t6_out4=$(sh "$_T6_GATE" "$_T6_CONF_FLAKY" "$_T6_GOOD_MAP" "$_T6_GOOD_TESTS" 2>&1)
_t6_ec4=$?
_t6_assert_nonzero "$_t6_ec4" "proof-4: FLAKY ledger → exit non-zero"
assert_contains "$_t6_out4" "FLAKY" "proof-4: output mentions FLAKY"
assert_contains "$_t6_out4" "Intermittent timeout" "proof-4: output surfaces failure_summary"

# ── PROOF 5: explicit NOT_RUN (not-run.json) → exit non-zero ──────────────────
_T6_CONF_NOTRUN=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T6_FX_LEDGER/not-run.json")
_t6_out5=$(sh "$_T6_GATE" "$_T6_CONF_NOTRUN" "$_T6_GOOD_MAP" "$_T6_GOOD_TESTS" 2>&1)
_t6_ec5=$?
_t6_assert_nonzero "$_t6_ec5" "proof-5: explicit NOT_RUN → exit non-zero"
assert_contains "$_t6_out5" "NOT_RUN" "proof-5: output mentions NOT_RUN"

# ── PROOF 6: GREEN missing ci_run_id → exit non-zero (fails closed via adapter) ─
_T6_CONF_MISS_RID=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T6_FX_LEDGER/green-missing-runid.json")
sh "$_T6_GATE" "$_T6_CONF_MISS_RID" "$_T6_GOOD_MAP" "$_T6_GOOD_TESTS" >/dev/null 2>&1
_t6_ec6=$?
_t6_assert_nonzero "$_t6_ec6" "proof-6: GREEN missing ci_run_id → exit non-zero (adapter fails closed)"

# ── PROOF 7: GREEN missing ci_artifact → exit non-zero (fails closed via adapter) ─
_T6_CONF_MISS_ART=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T6_FX_LEDGER/green-missing-artifact.json")
sh "$_T6_GATE" "$_T6_CONF_MISS_ART" "$_T6_GOOD_MAP" "$_T6_GOOD_TESTS" >/dev/null 2>&1
_t6_ec7=$?
_t6_assert_nonzero "$_t6_ec7" "proof-7: GREEN missing ci_artifact → exit non-zero (adapter fails closed)"

# ── PROOF 8: missing mapped test file → exit non-zero ─────────────────────────
_t6_d8=$(mktemp -d /tmp/t6-d8-XXXXXXXX)
_t6_register_tmpd "$_t6_d8"
cp -R "$_T6_HERE/fixtures/good/." "$_t6_d8/"
rm -f "$_t6_d8/tests/journeys/journey-001.spec.ts"
_t6_out8=$(sh "$_T6_GATE" "$_T6_CONF_GREEN" "$_t6_d8/JOURNEY_MAP.md" \
  "$_t6_d8/tests/journeys" 2>&1)
_t6_ec8=$?
_t6_assert_nonzero "$_t6_ec8" "proof-8: missing mapped test file → exit non-zero"
assert_contains "$_t6_out8" "journey-001" "proof-8: message references the missing spec"

# ── PROOF 9: orphan spec under tests/journeys/ → exit non-zero + "orphan" ──────
_t6_d9=$(mktemp -d /tmp/t6-d9-XXXXXXXX)
_t6_register_tmpd "$_t6_d9"
cp -R "$_T6_HERE/fixtures/good/." "$_t6_d9/"
printf '// orphan spec\n' > "$_t6_d9/tests/journeys/journey-999.spec.ts"
_t6_out9=$(sh "$_T6_GATE" "$_T6_CONF_GREEN" "$_t6_d9/JOURNEY_MAP.md" \
  "$_t6_d9/tests/journeys" 2>&1)
_t6_ec9=$?
_t6_assert_nonzero "$_t6_ec9" "proof-9: orphan spec file → exit non-zero"
assert_contains "$_t6_out9" "orphan" "proof-9: message says 'orphan'"

# ── PROOF 10: malformed ledger → fail closed ──────────────────────────────────
_T6_CONF_MALFORM=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T6_FX_LEDGER/malformed.json")
sh "$_T6_GATE" "$_T6_CONF_MALFORM" "$_T6_GOOD_MAP" "$_T6_GOOD_TESTS" >/dev/null 2>&1
_t6_ec10=$?
_t6_assert_nonzero "$_t6_ec10" "proof-10: malformed ledger → fail closed"

# ── PROOF 11: untrusted source → fail closed ──────────────────────────────────
_T6_CONF_UNTRUST=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T6_FX_LEDGER/untrusted-source.json")
sh "$_T6_GATE" "$_T6_CONF_UNTRUST" "$_T6_GOOD_MAP" "$_T6_GOOD_TESTS" >/dev/null 2>&1
_t6_ec11=$?
_t6_assert_nonzero "$_t6_ec11" "proof-11: untrusted source → fail closed"

# ── PROOF 12: stale ledger + LEDGER_MAX_AGE_SECONDS=3600 → fail closed ─────────
_T6_CONF_STALE=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_MAX_AGE_SECONDS=3600" \
  "LEDGER_PATH=$_T6_FX_LEDGER/stale.json")
sh "$_T6_GATE" "$_T6_CONF_STALE" "$_T6_GOOD_MAP" "$_T6_GOOD_TESTS" >/dev/null 2>&1
_t6_ec12=$?
_t6_assert_nonzero "$_t6_ec12" "proof-12: stale ledger (max-age 3600s) → fail closed"

# ── PROOF 13: runtime field in MAP → fails via the authority dependency ────────
_t6_out13=$(sh "$_T6_GATE" "$_T6_CONF_GREEN" \
  "$_T6_HERE/fixtures/authority/map-with-runtime.md" \
  "$_T6_GOOD_TESTS" 2>&1)
_t6_ec13=$?
_t6_assert_nonzero "$_t6_ec13" "proof-13: runtime field in MAP → exit non-zero (lint/authority)"

# ── PROOF 14: stale runtime ID not in map → exit 0 + WARN: for JOURNEY-999 ────
_T6_CONF_PLUSORPHAN=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T6_FX_LEDGER/green-plus-orphan.json")
_t6_out14=$(sh "$_T6_GATE" "$_T6_CONF_PLUSORPHAN" "$_T6_GOOD_MAP" "$_T6_GOOD_TESTS" 2>&1)
_t6_ec14=$?
assert_eq "0" "$_t6_ec14" "proof-14: stale runtime ID → exit 0 (non-blocking)"
assert_contains "$_t6_out14" "WARN:" "proof-14: output contains WARN:"
assert_contains "$_t6_out14" "JOURNEY-999" "proof-14: WARN mentions JOURNEY-999"

# ── PROOF 15: P2 non-GREEN does NOT block in default mode → exit 0 ─────────────
# journeys-p2: JOURNEY-001 P0 GREEN, JOURNEY-002 P2 absent→NOT_RUN; default=no --all
_T6_CONF_P2=$(_t6_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T6_FX_LEDGER/green.json")
_t6_out15=$(sh "$_T6_GATE" "$_T6_CONF_P2" "$_T6_P2_MAP" "$_T6_P2_TESTS" 2>&1)
_t6_ec15=$?
assert_eq "0" "$_t6_ec15" "proof-15: P2 non-GREEN default mode → exit 0 (non-blocking)"
assert_contains "$_t6_out15" "WARN:" "proof-15: P2 non-GREEN emits WARN"

# ── PROOF 16: --all blocks P2 non-GREEN → exit non-zero ───────────────────────
_t6_out16=$(sh "$_T6_GATE" "$_T6_CONF_P2" "$_T6_P2_MAP" "$_T6_P2_TESTS" --all 2>&1)
_t6_ec16=$?
_t6_assert_nonzero "$_t6_ec16" "proof-16: --all blocks P2 non-GREEN → exit non-zero"
assert_contains "$_t6_out16" "JOURNEY-002" "proof-16: output names the blocked journey"

# ── PROOF 17: blank priority on non-EXEMPT journey FAILS CLOSED ────────────────
# Regression-locks the fail-open found in review: a WRITTEN, non-EXEMPT journey
# with a blank priority VALUE must not fall through to WARN-only while NOT_RUN.
_t6_d17=$(mktemp -d "${TMPDIR:-/tmp}/t6-d17-XXXXXXXX")
_t6_register_tmpd "$_t6_d17"
cp -R "$_T6_HERE/fixtures/good/." "$_t6_d17/"
# Blank the priority VALUE but keep the key present (so lint still sees the field).
sed 's/^priority:.*/priority:/' "$_t6_d17/JOURNEY_MAP.md" > "$_t6_d17/JOURNEY_MAP.md.x" \
  && mv "$_t6_d17/JOURNEY_MAP.md.x" "$_t6_d17/JOURNEY_MAP.md"
# _T6_CONF_EMPTY → empty-journeys.json → JOURNEY-001 absent → NOT_RUN.
_t6_out17=$(sh "$_T6_GATE" "$_T6_CONF_EMPTY" "$_t6_d17/JOURNEY_MAP.md" "$_t6_d17/tests/journeys" 2>&1)
_t6_ec17=$?
_t6_assert_nonzero "$_t6_ec17" "proof-17: blank-priority non-EXEMPT journey (NOT_RUN) → exit non-zero (fail closed)"
# With the lint hardening, blank priority is now caught at the lint dependency
# (lint rejects blank required values); check-journeys' own blank/unknown-priority
# join arm remains a backstop. Either way the gate fails closed.
assert_contains "$_t6_out17" "lint-journey-map.sh failed" \
  "proof-17: blank priority caught at the lint dependency (defense-in-depth)"

# ── Temp-file/dir cleanup ─────────────────────────────────────────────────────
# shellcheck disable=SC2086
rm -f $_T6_TMPFILES
for _t6_d in $_T6_TMPDIRS; do rm -rf "$_t6_d"; done
unset _t6_d
