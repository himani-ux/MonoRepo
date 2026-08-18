#!/bin/sh
# shellcheck shell=sh
# check-journey-authority_test.sh — TDD proofs for check-journey-authority.sh (Task 5).
# All 11 proofs per brief §E. Run via: sh journey/tests/check-journey-authority_test.sh
# Also executed by journey/tests/run.sh (sourced, not subshell).

. "$(dirname "$0")/assert.sh"

# ── local helper: assert exit code is non-zero ────────────────────────────────
# (defined here to avoid polluting assert.sh; prefixed to avoid collision)
_t5_assert_nonzero() { # ACTUAL_CODE MSG
  if [ "$1" -ne 0 ]; then
    printf 'ok: %s\n' "$2"
  else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1))
  fi
}

# ── paths ─────────────────────────────────────────────────────────────────────
_T5_HERE="$(cd "$(dirname "$0")" && pwd)"
_T5_GATE="$_T5_HERE/../bin/check-journey-authority.sh"
_T5_FX_LEDGER="$_T5_HERE/fixtures/ledger"
_T5_FX_AUTH="$_T5_HERE/fixtures/authority"
_T5_GOOD_MAP="$_T5_HERE/fixtures/good/JOURNEY_MAP.md"
_T5_TEMPLATE="$_T5_HERE/../JOURNEY_MAP.template.md"

# ── temp-file registry ────────────────────────────────────────────────────────
_T5_TMPFILES=""
_t5_register_tmp() { _T5_TMPFILES="$_T5_TMPFILES $1"; }
# Note: trap is cleared after proof-4's non-destructive test to avoid interfering
# with run.sh when sourced; explicit cleanup is used for other temp files.

# Helper: write a temp conf file from KEY=value arguments (one per arg)
_t5_mk_conf() {
  _t5c=$(mktemp /tmp/t5-conf-XXXXXXXX)
  _t5_register_tmp "$_t5c"
  for _t5_line in "$@"; do
    printf '%s\n' "$_t5_line"
  done > "$_t5c"
  printf '%s\n' "$_t5c"
}

# ── Trusted test conf (used for proofs 1, 2, 3, 4, 11) ───────────────────────
_T5_TRUSTED_CONF=$(_t5_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T5_FX_LEDGER/green.json")

# ── Proof 1: clean maps + trusted ledger PASS ─────────────────────────────────
# Proves: runtime field names are allowed INSIDE negative fixtures that are NOT
# passed as MAP args (e.g. fixtures/lint/runtime-field.md exists in the tree
# but is not scanned because it is not a MAP arg).
_t5_out1=$(sh "$_T5_GATE" "$_T5_TRUSTED_CONF" "$_T5_GOOD_MAP" "$_T5_TEMPLATE" 2>&1)
_t5_ec1=$?
assert_eq "0" "$_t5_ec1" "proof-1: clean maps + trusted ledger → exit 0"

# ── Proof 2: runtime field in JOURNEY_MAP.md FAILS ───────────────────────────
_t5_out2=$(sh "$_T5_GATE" "$_T5_TRUSTED_CONF" "$_T5_FX_AUTH/map-with-runtime.md" 2>&1)
_t5_ec2=$?
_t5_assert_nonzero "$_t5_ec2" "proof-2: runtime field in map → exit non-zero"
assert_contains "$_t5_out2" "ci_status" "proof-2: message names the runtime field (ci_status)"

# ── Proof 3: runtime field in template FAILS ─────────────────────────────────
_t5_out3=$(sh "$_T5_GATE" "$_T5_TRUSTED_CONF" "$_T5_FX_AUTH/template-with-runtime.md" 2>&1)
_t5_ec3=$?
_t5_assert_nonzero "$_t5_ec3" "proof-3: runtime field in template → exit non-zero"
assert_contains "$_t5_out3" "last_run" "proof-3: message names the runtime field (last_run)"

# ── Proof 4: tracked JOURNEY_STATUS.json FAILS (non-destructive) ──────────────
# This proof stages a temp JOURNEY_STATUS.json at the repo root, runs the gate,
# then cleans up completely, leaving the working tree untouched.
_t5_p4_root=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$_t5_p4_root" ]; then
  printf 'SKIP: proof-4: not a git repo (git rev-parse failed)\n'
else
  _t5_p4_file="$_t5_p4_root/JOURNEY_STATUS.json"
  # Cleanup function used both by trap and explicit call
  _t5_p4_cleanup() {
    git -C "$_t5_p4_root" rm --cached --ignore-unmatch -q "JOURNEY_STATUS.json" 2>/dev/null || true
    rm -f "$_t5_p4_file"
  }
  # Create the file and stage it (intent-to-add so content is minimal)
  printf '{"test":"authority-gate-proof-4"}\n' > "$_t5_p4_file"
  git -C "$_t5_p4_root" add -N "$_t5_p4_file" 2>/dev/null
  # Set safety trap (fires on EXIT if something goes wrong before explicit cleanup)
  trap '_t5_p4_cleanup' EXIT
  # Run the gate — expect non-zero because JOURNEY_STATUS.json is now tracked
  _t5_out4=$(sh "$_T5_GATE" "$_T5_TRUSTED_CONF" "$_T5_GOOD_MAP" "$_T5_TEMPLATE" 2>&1)
  _t5_ec4=$?
  # Explicitly clean up and clear the trap
  _t5_p4_cleanup
  trap - EXIT
  # Assertions
  _t5_assert_nonzero "$_t5_ec4" "proof-4: tracked JOURNEY_STATUS.json → exit non-zero"
  assert_contains "$_t5_out4" "tracked" "proof-4: message mentions tracked ledger"
  # Verify the working tree is clean — no JOURNEY_STATUS.json
  _t5_p4_status=$(git -C "$_t5_p4_root" status --porcelain 2>/dev/null)
  assert_not_contains "$_t5_p4_status" "JOURNEY_STATUS.json" \
    "proof-4: working tree clean (no JOURNEY_STATUS.json) after test"
fi

# ── Proof 5: runtime field in negative fixture NOT scanned (covered by proof 1) ──
# Fixtures containing runtime field names (e.g. fixtures/lint/runtime-field.md)
# are allowed in the repo as long as they are NOT passed as MAP args.
# Proof 1 above already demonstrates this: the gate passes with those files
# present in the working tree. This assertion is redundant but explicit.
assert_eq "0" "$_t5_ec1" "proof-5: negative fixture with runtime field allowed when not a MAP arg (same as proof-1)"

# ── Proof 6: missing trusted ledger FAILS CLOSED ─────────────────────────────
_t5_conf6=$(_t5_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T5_FX_LEDGER/DOES_NOT_EXIST.json")
_t5_out6=$(sh "$_T5_GATE" "$_t5_conf6" "$_T5_GOOD_MAP" "$_T5_TEMPLATE" 2>&1)
_t5_ec6=$?
_t5_assert_nonzero "$_t5_ec6" "proof-6: missing ledger → exit non-zero (fail closed)"

# ── Proof 7: malformed trusted ledger FAILS CLOSED ───────────────────────────
_t5_conf7=$(_t5_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T5_FX_LEDGER/malformed.json")
_t5_out7=$(sh "$_T5_GATE" "$_t5_conf7" "$_T5_GOOD_MAP" "$_T5_TEMPLATE" 2>&1)
_t5_ec7=$?
_t5_assert_nonzero "$_t5_ec7" "proof-7: malformed ledger → exit non-zero (fail closed)"

# ── Proof 8: untrusted source FAILS CLOSED ───────────────────────────────────
_t5_conf8=$(_t5_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T5_FX_LEDGER/untrusted-source.json")
_t5_out8=$(sh "$_T5_GATE" "$_t5_conf8" "$_T5_GOOD_MAP" "$_T5_TEMPLATE" 2>&1)
_t5_ec8=$?
_t5_assert_nonzero "$_t5_ec8" "proof-8: untrusted source → exit non-zero (fail closed)"

# ── Proof 9: stale trusted ledger FAILS CLOSED ───────────────────────────────
_t5_conf9=$(_t5_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_MAX_AGE_SECONDS=3600" \
  "LEDGER_PATH=$_T5_FX_LEDGER/stale.json")
_t5_out9=$(sh "$_T5_GATE" "$_t5_conf9" "$_T5_GOOD_MAP" "$_T5_TEMPLATE" 2>&1)
_t5_ec9=$?
_t5_assert_nonzero "$_t5_ec9" "proof-9: stale ledger (max-age 3600s) → exit non-zero (fail closed)"

# ── Proof 10: test-fixture mode WITHOUT ALLOW_TEST_FIXTURE=1 FAILS CLOSED ────
_t5_conf10=$(_t5_mk_conf \
  "LEDGER_SOURCE=test-fixture" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$_T5_FX_LEDGER/green.json")
# NOTE: ALLOW_TEST_FIXTURE intentionally absent
_t5_out10=$(sh "$_T5_GATE" "$_t5_conf10" "$_T5_GOOD_MAP" "$_T5_TEMPLATE" 2>&1)
_t5_ec10=$?
_t5_assert_nonzero "$_t5_ec10" "proof-10: test-fixture without ALLOW_TEST_FIXTURE=1 → exit non-zero (fail closed)"

# ── Proof 11: gate NEVER reads runtime status from JOURNEY_MAP.md ─────────────
# Pass map-with-runtime.md (contains ci_status: GREEN) as a MAP arg.
# The gate MUST FAIL (exit non-zero) because the runtime field KEY is present
# in the map — NOT because the gate read the value GREEN.
# If the gate were reading GREEN and treating it as a pass, it would exit 0.
# This proves the gate checks for key ABSENCE, not status values.
_t5_out11=$(sh "$_T5_GATE" "$_T5_TRUSTED_CONF" "$_T5_FX_AUTH/map-with-runtime.md" 2>&1)
_t5_ec11=$?
_t5_assert_nonzero "$_t5_ec11" "proof-11: map with ci_status: GREEN → exit non-zero (gate never reads GREEN)"
assert_contains "$_t5_out11" "ci_status" \
  "proof-11: failure message names ci_status (not a pass-by-reading-GREEN)"

# ── Proof 11b: INDENTED runtime field in map FAILS (N-1) ─────────────────────
# A runtime-truth key with leading whitespace must still be rejected, consistent
# with journey-gen-promote.sh's `^[[:space:]]*` scan.
_t5_out11b=$(sh "$_T5_GATE" "$_T5_TRUSTED_CONF" "$_T5_FX_AUTH/map-with-indented-runtime.md" 2>&1)
_t5_ec11b=$?
_t5_assert_nonzero "$_t5_ec11b" "proof-11b: INDENTED runtime field in map → exit non-zero"
assert_contains "$_t5_out11b" "last_run" "proof-11b: message names the indented runtime field (last_run)"

# ── Proof 12: mktemp failure FAILS CLOSED (regression-locks the guard) ─────────
# With a bogus TMPDIR the gate's mktemp fails; the guard must _die (exit non-zero)
# BEFORE any check, rather than silently dropping problem-writes and exiting 0.
_t5_out12=$(TMPDIR=/nonexistent/authority-no-such-dir \
  sh "$_T5_GATE" "$_T5_TRUSTED_CONF" "$_T5_GOOD_MAP" "$_T5_TEMPLATE" 2>&1)
_t5_ec12=$?
_t5_assert_nonzero "$_t5_ec12" "proof-12: mktemp failure (bogus TMPDIR) → exit non-zero (fail closed)"

# ── Proof 13: AUTHORITY_FIXTURE_DIR kill-switch rejected ──────────────────────
# Setting the fixture dir to the repo root would (pre-fix) exempt every tracked
# path and disable Check 2. The gate must now reject any value outside <journey>/tests.
_t5_repo_root=$(git rev-parse --show-toplevel 2>/dev/null)
_t5_journey_root=$(cd "$_T5_HERE/.." && pwd)
if [ -n "$_t5_repo_root" ]; then
  _t5_out13=$(AUTHORITY_FIXTURE_DIR="$_t5_repo_root" \
    sh "$_T5_GATE" "$_T5_TRUSTED_CONF" "$_T5_GOOD_MAP" "$_T5_TEMPLATE" 2>&1)
  _t5_ec13=$?
  _t5_assert_nonzero "$_t5_ec13" "proof-13: AUTHORITY_FIXTURE_DIR=<repo-root> → exit non-zero (kill-switch rejected)"
  assert_contains "$_t5_out13" "AUTHORITY_FIXTURE_DIR" "proof-13: message explains the rejected fixture dir"
fi
# Legit value (within journey/tests) still works:
#
# KNOWN-FLAKE (P6, sim-reality-engines fix wave; ledger V-T7/T8 finding
# LESSONS-1): this exact assertion was observed to fail once in three
# full-suite (`sh journey/tests/run.sh`) runs during V-T7/T8 verification
# (expected exit 0, got 1), and passed standalone every time. P6's
# investigation (this fix wave) could NOT reproduce it deterministically
# despite effort well past the ~5-suite-run timebox:
#   - 3 full `journey/tests/run.sh` runs: 2 clean; 1 showed a RELATED
#     failure in a DIFFERENT proof going through the SAME gate
#     (check-journeys_test.sh proof-4: check-journeys.sh's Step C.2 call
#     into check-journey-authority.sh returned non-zero when it should
#     have passed) — observed only while THREE heavy processes were
#     running concurrently against this one working tree at once (two
#     full suite runs + a targeted bisect, all self-induced by the
#     investigation, not a normal single `run.sh` invocation).
#   - A 20-iteration bisect sourcing the four alphabetically-preceding
#     test files (acceptance_test.sh, author-bundle_test.sh,
#     check-doc-format_test.sh, check-inbox-triaged_test.sh) then this
#     file into ONE shared shell, mirroring run.sh's own sourcing model
#     exactly: 0/20 proof-13b failures.
#   - Direct concurrency probes firing 40 and then 120 parallel
#     invocations of check-journey-authority.sh / check-journeys.sh
#     against the real repo (same conf/map fixtures proof-1/13b/
#     check-journeys proof-4 use): 0 unexpected failures either time.
#   - Static review of the four preceding files: no stray `cd` (all git
#     scratch-repo work is subshell- or `( cd ... )`-scoped), no env-var
#     export, no `_t5_`/`_T5_`/AUTHORITY_FIXTURE_DIR/TMPDIR/trap
#     collisions with this file's own namespace.
# Best-evidence read: NOT a deterministic order-dependence bug in this
# test file's own logic (AUTHORITY_FIXTURE_DIR handling is static,
# absolute-path, unaffected by cwd or prior files) — the one
# reproduction correlates with heavy concurrent process load against the
# same working tree, consistent with a transient subprocess-spawn hiccup
# somewhere in the composed chain (git / jq / mktemp /
# journey-ledger-fetch.sh) that the gate's fail-closed design cannot
# distinguish from a real authority violation. Left AS-IS per instruction:
# no retry loop, no assertion weakening. If this fires again, capture the
# gate's own stderr (not just the exit code) — none of P6's evidence
# includes it because the historical V-T7/T8 sighting only recorded
# "expected 0 got 1".
_t5_out13b=$(AUTHORITY_FIXTURE_DIR="$_t5_journey_root/tests/fixtures" \
  sh "$_T5_GATE" "$_T5_TRUSTED_CONF" "$_T5_GOOD_MAP" "$_T5_TEMPLATE" 2>&1)
_t5_ec13b=$?
assert_eq "0" "$_t5_ec13b" "proof-13b: AUTHORITY_FIXTURE_DIR within journey/tests → still passes clean maps"
if [ "$_t5_ec13b" != "0" ]; then
  printf 'proof-13b diagnostic (KNOWN-FLAKE, capture for the ledger): %s\n' "$_t5_out13b"
fi

# ── Proof 14: missing/unreadable MAP arg FAILS CLOSED ─────────────────────────
_t5_out14=$(sh "$_T5_GATE" "$_T5_TRUSTED_CONF" "$_T5_HERE/fixtures/NO_SUCH_MAP.md" 2>&1)
_t5_ec14=$?
_t5_assert_nonzero "$_t5_ec14" "proof-14: missing MAP arg → exit non-zero (fail closed)"
assert_contains "$_t5_out14" "not readable" "proof-14: message names the unreadable map"

# ── Temp-file cleanup ─────────────────────────────────────────────────────────
# shellcheck disable=SC2086
rm -f $_T5_TMPFILES
