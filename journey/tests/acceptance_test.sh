#!/bin/sh
# shellcheck shell=sh
# acceptance_test.sh — TDD proofs for journey-acceptance.sh + the CI wiring example.
# Run via: sh journey/tests/acceptance_test.sh   (also run by run.sh)

. "$(dirname "$0")/assert.sh"

_a8_assert_nonzero() { # CODE MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"
  else printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

_A8_HERE="$(cd "$(dirname "$0")" && pwd)"
_A8_GATE="$_A8_HERE/../bin/journey-acceptance.sh"
_A8_FX_LEDGER="$_A8_HERE/fixtures/ledger"
_A8_GOOD_MAP="$_A8_HERE/fixtures/good/JOURNEY_MAP.md"
_A8_GOOD_TESTS="$_A8_HERE/fixtures/good/tests/journeys"
_A8_LINT_FX="$_A8_HERE/fixtures/lint"
_A8_CI_DOC="$_A8_HERE/../docs/ci-journey-gates.example.yml"

_A8_TMP=""
_a8_conf() { # LEDGER_FILE
  _c=$(mktemp /tmp/a8-conf-XXXXXXXX); _A8_TMP="$_A8_TMP $_c"
  printf '%s\n' "LEDGER_SOURCE=test-fixture" "ALLOW_TEST_FIXTURE=1" \
    "EXPECTED_SOURCE=test-fixture://trusted" "LEDGER_PATH=$_A8_FX_LEDGER/$1" > "$_c"
  printf '%s\n' "$_c"
}

# ── Proof 1: acceptance PASSES on the shipped good example ────────────────────
_a8_c_green=$(_a8_conf green.json)
_a8_out1=$(sh "$_A8_GATE" "$_a8_c_green" "$_A8_GOOD_MAP" "$_A8_GOOD_TESTS" 2>&1)
_a8_ec1=$?
assert_eq "0" "$_a8_ec1" "proof-1: acceptance passes on good fixture → exit 0"
assert_contains "$_a8_out1" "ACCEPTANCE PASSED" "proof-1: prints ACCEPTANCE PASSED"

# ── Proof 2: lint failure makes acceptance fail (attributed to lint) ─────────
_a8_out2=$(sh "$_A8_GATE" "$_a8_c_green" "$_A8_LINT_FX/missing-field.md" "$_A8_GOOD_TESTS" 2>&1)
_a8_ec2=$?
_a8_assert_nonzero "$_a8_ec2" "proof-2: lint failure → acceptance fails"
assert_contains "$_a8_out2" "FAILED at gate: lint-journey-map" "proof-2: names the lint gate"

# ── Proof 3: authority failure makes acceptance fail (lint passes first) ─────
# good map passes lint; an untrusted ledger makes check-journey-authority fail.
_a8_c_untrusted=$(_a8_conf untrusted-source.json)
_a8_out3=$(sh "$_A8_GATE" "$_a8_c_untrusted" "$_A8_GOOD_MAP" "$_A8_GOOD_TESTS" 2>&1)
_a8_ec3=$?
_a8_assert_nonzero "$_a8_ec3" "proof-3: authority failure → acceptance fails"
assert_contains "$_a8_out3" "FAILED at gate: check-journey-authority" "proof-3: names the authority gate"

# ── Proof 4: reconciliation failure makes acceptance fail (lint+authority pass)
# empty-journeys ledger is trusted+valid but JOURNEY-001 is absent → NOT_RUN.
_a8_c_empty=$(_a8_conf empty-journeys.json)
_a8_out4=$(sh "$_A8_GATE" "$_a8_c_empty" "$_A8_GOOD_MAP" "$_A8_GOOD_TESTS" 2>&1)
_a8_ec4=$?
_a8_assert_nonzero "$_a8_ec4" "proof-4: reconciliation failure → acceptance fails"
assert_contains "$_a8_out4" "FAILED at gate: check-journeys" "proof-4: names the check-journeys gate"

# ── Proof 5-8: CI wiring example exists and states the trust model ───────────
_a8_ci="$(cat "$_A8_CI_DOC")"
assert_contains "$_a8_ci" "journey-status" "proof-5: CI example mentions the protected branch / ledger location"
assert_contains "$_a8_ci" "read-only" "proof-6: CI example states the PR gate is read-only"
assert_contains "$_a8_ci" "non-PR-controllable" "proof-7: CI example requires non-PR-controllable config"
assert_contains "$_a8_ci" "fails closed" "proof-8: CI example states fail-closed behavior"

# cleanup
# shellcheck disable=SC2086
rm -f $_A8_TMP
