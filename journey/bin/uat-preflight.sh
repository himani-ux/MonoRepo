#!/bin/sh
# shellcheck shell=sh
# uat-preflight.sh MAP TEST_SURFACE APP_FLOW — the single entry command a
# UAT operator runs before driving the app (spec DC-8). Pure composition,
# no new logic beyond ordering + reporting: three existing gates, run in
# order as EXECUTABLES (never re-implemented), fail-closed, each step's own
# diagnostics passed through unchanged.
#
#   1. lint-journey-map.sh MAP
#   2. check-surface-staleness.sh TEST_SURFACE APP_FLOW
#        (spec G2 — verified against the real gate: it derives
#        <TEST_SURFACE>.provenance itself from TEST_SURFACE's own path; there
#        is no separate PROVENANCE positional arg on the shipped gate, so
#        this wrapper takes none either — MAP TEST_SURFACE APP_FLOW, not
#        MAP TEST_SURFACE PROVENANCE APP_FLOW.)
#   3. check-uat-preconditions.sh MAP
#        (spec G1 — the 401-burn archetype this preflight exists to kill)
#
# Env passthrough: RUN_UAT_PREFLIGHT / UAT_PREFLIGHT_PROBE are consumed
# entirely by check-uat-preconditions.sh (step 3) — this wrapper reads
# neither, sets neither, and adds no env contract of its own; whatever the
# operator has exported flows straight through.
#
# Reporting: the failing gate's own stderr/stdout prints first (passed
# through verbatim), then this script adds exactly one line and stops —
# steps after the first failure never run:
#   PREFLIGHT_FAILED: step <n> (<gate name>)
# exit 1. All three green: one summary line
#   UAT-PREFLIGHT: green (<map> <surface>)
# exit 0.
#
# Usage / missing-file errors: exit 2 (house convention — matches
# lint-journey-map.sh / check-uat-preconditions.sh / check-surface-staleness.sh
# usage-error posture; checked here BEFORE any gate runs, same as
# check-uat-preconditions.sh checks its own MAP arg before composing lint).
set -u

usage() { printf 'Usage: uat-preflight.sh MAP TEST_SURFACE APP_FLOW\n' >&2; exit 2; }
[ $# -eq 3 ] || usage

MAP="$1"; TS="$2"; APP_FLOW="$3"

_here="$(cd "$(dirname "$0")" && pwd)"

for _f in "$MAP" "$TS" "$APP_FLOW"; do
  [ -f "$_f" ] || {
    printf 'uat-preflight: file not found: %s\n' "$_f" >&2
    exit 2
  }
done

/bin/sh "$_here/lint-journey-map.sh" "$MAP" || {
  printf 'PREFLIGHT_FAILED: step 1 (lint-journey-map.sh)\n' >&2
  exit 1
}

/bin/sh "$_here/check-surface-staleness.sh" "$TS" "$APP_FLOW" || {
  printf 'PREFLIGHT_FAILED: step 2 (check-surface-staleness.sh)\n' >&2
  exit 1
}

/bin/sh "$_here/check-uat-preconditions.sh" "$MAP" || {
  printf 'PREFLIGHT_FAILED: step 3 (check-uat-preconditions.sh)\n' >&2
  exit 1
}

printf 'UAT-PREFLIGHT: green (%s %s)\n' "$MAP" "$TS"
exit 0
