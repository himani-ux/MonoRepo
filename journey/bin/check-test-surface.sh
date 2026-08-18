#!/bin/sh
# shellcheck shell=sh
# check-test-surface.sh TEST_SURFACE_FILE
#
# Execution verifier for the canonical TEST_SURFACE (Increment 2): every
# allowed selector must RESOLVE on its screen in the RUNNING app, so the
# contract is executable evidence, not prose that can rot.
#
#   RUN_APP_CHECK unset  -> clear skip, exit 0 (default CI stays node-free).
#   RUN_APP_CHECK=1      -> requires JOURNEY_RUNNER=playwright (anything else
#                           is RUNNER_UNSUPPORTED in Increment 2), node, and
#                           the app reachable at APP_BASE_URL
#                           (default http://localhost:4173).
#
# Failure classes (from journey/surface-check/check-surface.mjs):
#   APP_UNREACHABLE  — the app did not answer at APP_BASE_URL (infra).
#   SELECTOR_STALE   — a selector did not resolve on its screen (contract).
#   RUNNER_UNSUPPORTED / NODE_MISSING — environment (fail closed here).
# A crashed run is NEVER a pass: any non-zero from the checker fails.

set -u
_die() { printf 'check-test-surface: %s\n' "$*" >&2; exit 1; }
_here=$(cd "$(dirname "$0")" && pwd)

[ $# -eq 1 ] || _die "usage: check-test-surface.sh TEST_SURFACE_FILE"
TS="$1"
[ -r "$TS" ] || _die "file not readable: $TS"

if [ "${RUN_APP_CHECK:-0}" != "1" ]; then
  printf 'check-test-surface: skip (RUN_APP_CHECK not set). No app or node invoked.\n'
  printf 'Opt-in: RUN_APP_CHECK=1 JOURNEY_RUNNER=playwright APP_BASE_URL=<url> %s %s\n' "$0" "$TS"
  exit 0
fi

# the surface must be internally valid before any app is driven
sh "$_here/lint-test-surface.sh" "$TS" >/dev/null 2>&1 || \
  _die "TEST_SURFACE fails lint — fix the contract before execution-verifying it (fail closed)"

case "${JOURNEY_RUNNER:-}" in
  playwright) : ;;
  "") _die "RUNNER_UNSUPPORTED: JOURNEY_RUNNER is unset (Increment 2 supports: playwright)" ;;
  *)  _die "RUNNER_UNSUPPORTED: JOURNEY_RUNNER='$JOURNEY_RUNNER' (Increment 2 supports: playwright)" ;;
esac

command -v node >/dev/null 2>&1 || \
  _die "NODE_MISSING: RUN_APP_CHECK=1 requires node (the checker lives in journey/surface-check/) — fail closed"

_MJS="$_here/../surface-check/check-surface.mjs"
[ -r "$_MJS" ] || _die "checker missing: $_MJS (fail closed)"

APP_BASE_URL="${APP_BASE_URL:-http://localhost:4173}" node "$_MJS" "$TS" || \
  _die "surface verification FAILED (see diagnostics above — a crashed run is never a pass)"

printf 'check-test-surface: every allowed selector resolved on its screen (%s)\n' "$TS"
exit 0
