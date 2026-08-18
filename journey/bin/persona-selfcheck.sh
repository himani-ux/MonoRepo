#!/bin/sh
# shellcheck shell=sh
# persona-selfcheck.sh SSOT PRD JOURNEY_MAP PERSONA_COVERAGE_GAPS
#
# Step 1 Domain 12 self-check (Increment 3): runs the persona gate chain in
# order and attributes any failure to the gate that failed. Step 1 output is
# verifiable the moment it is written.
#
#   1. lint-personas.sh SSOT
#   2. lint-journey-map.sh JOURNEY_MAP
#   3. check-persona-journeys.sh JOURNEY_MAP SSOT
#   4. check-persona-coverage.sh PRD SSOT JOURNEY_MAP PERSONA_COVERAGE_GAPS
#
# Exit 0 only if every gate passes. PERSONA journeys model USER BEHAVIOR, not
# tested behavior — nothing here reads or writes runtime truth.

set -u
_here=$(cd "$(dirname "$0")" && pwd)

[ $# -eq 4 ] || {
  printf 'usage: persona-selfcheck.sh SSOT PRD JOURNEY_MAP PERSONA_COVERAGE_GAPS\n' >&2; exit 1; }
SSOT="$1"; PRD="$2"; MAP="$3"; GAPS="$4"

_gate() { # NAME CMD...
  _name="$1"; shift
  if ! "$@"; then
    printf 'persona-selfcheck: FAILED at gate: %s (fix the diagnostics above and re-run)\n' "$_name" >&2
    exit 1
  fi
}

_gate "lint-personas"          sh "$_here/lint-personas.sh" "$SSOT"
_gate "lint-journey-map"       sh "$_here/lint-journey-map.sh" "$MAP"
_gate "check-persona-journeys" sh "$_here/check-persona-journeys.sh" "$MAP" "$SSOT"
_gate "check-persona-coverage" sh "$_here/check-persona-coverage.sh" "$PRD" "$SSOT" "$MAP" "$GAPS"

printf 'persona-selfcheck: all gates pass (personas + persona journeys + coverage are consistent)\n'
exit 0
