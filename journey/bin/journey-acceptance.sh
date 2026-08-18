#!/bin/sh
# shellcheck shell=sh
# journey-acceptance.sh CONF MAP TESTS_DIR
#
# Increment-1 acceptance gate: runs the full gate chain IN ORDER on one journey map
# and FAILS CLOSED at the first failing gate, naming which gate failed.
#   1. lint-journey-map.sh        (intent schema)
#   2. check-journey-authority.sh (no runtime truth in tree; trusted-fetch chain)
#   3. check-journeys.sh          (three-source join: intent ∧ test ∧ trusted GREEN ledger)
#
# Succeeds only when the example journey has: valid intent in JOURNEY_MAP.md, no
# runtime-truth fields in the map, a mapped test file that exists, a trusted CI-owned
# ledger that resolves, and a ledger GREEN with required evidence fields.
#
# This command does NOT publish or write runtime truth — it only reads (via the
# Task-3 adapter) and reconciles. See ci-journey-gates.example.yml for the
# forge-proof two-job CI model and the non-PR-controllable trust requirements.
set -u
_SELF="$0"
_BIN="$(cd "$(dirname "$0")" && pwd)"

[ $# -ge 3 ] || { echo "$_SELF: usage: journey-acceptance.sh CONF MAP TESTS_DIR" >&2; exit 2; }
_CONF="$1"; _MAP="$2"; _TESTS_DIR="$3"

_run_gate() { # LABEL CMD...
  _label="$1"; shift
  if ! "$@"; then
    printf 'ACCEPTANCE FAILED at gate: %s\n' "$_label" >&2
    exit 1
  fi
  printf '  ok: %s\n' "$_label"
}

printf 'Increment-1 acceptance for %s\n' "$_MAP"
_run_gate "lint-journey-map"        sh "$_BIN/lint-journey-map.sh"        "$_MAP"
_run_gate "check-journey-authority" sh "$_BIN/check-journey-authority.sh" "$_CONF" "$_MAP"
_run_gate "check-journeys"          sh "$_BIN/check-journeys.sh"          "$_CONF" "$_MAP" "$_TESTS_DIR"
printf 'ACCEPTANCE PASSED: %s through lint -> authority -> check-journeys\n' "$_MAP"
exit 0
