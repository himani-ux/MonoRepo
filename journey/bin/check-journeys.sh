#!/bin/sh
# shellcheck shell=sh
# check-journeys.sh — Three-source journey gate (Task 6).
#
# Usage: check-journeys.sh CONF MAP TESTS_DIR [--all]
#
#   CONF      — ledger configuration file (Task-3 format); passed to the adapter
#               and to check-journey-authority.sh.
#   MAP       — JOURNEY_MAP.md (canonical intent SSOT).
#   TESTS_DIR — the tests/journeys/ directory to scan for orphan specs.
#   --all     — optional: also enforce P2/P3 journeys (default enforces P0/P1 only).
#
# Exit 0 only if all checks pass.  Accumulates all blocking problems, prints each
# to stderr, exits non-zero (fail closed).  Warnings (non-blocking) print to stderr
# prefixed WARN:.
#
# Composition (in order, before the per-journey join):
#   1. lint-journey-map.sh MAP        — fail closed if map is not schema-valid.
#   2. check-journey-authority.sh CONF MAP — fail closed if authority checks fail.
#   3. journey-ledger-fetch.sh CONF   — fail closed if adapter fails for any reason.
# Runtime truth comes ONLY from the fetched ledger.  This gate NEVER reads runtime
# status (ci_status, last_run, etc.) from JOURNEY_MAP.md or any map file.
#
# CI-topology seam
# ─────────────────
# Production CI must source ledger configuration and gate environment from a
# non-PR-controllable control plane.
# Repo-local config is acceptable only for tests or local development.
#
# Deps: sh, awk, grep, jq (1.5+), git (via authority gate).

set -u
_SELF="$0"
_BINDIR="$(cd "$(dirname "$0")" && pwd)"
_JOURNEY_ROOT="$(cd "$_BINDIR/.." && pwd)"
_LINT="$_JOURNEY_ROOT/bin/lint-journey-map.sh"
_AUTHORITY="$_JOURNEY_ROOT/bin/check-journey-authority.sh"
_FETCH="$_JOURNEY_ROOT/lib/journey-ledger-fetch.sh"
_LIB="$_JOURNEY_ROOT/lib/journey-lib.sh"
_LEDGER_LIB="$_JOURNEY_ROOT/lib/journey-ledger.sh"

_die() { printf '%s: %s\n' "$_SELF" "$1" >&2; exit 1; }

# ── Args ──────────────────────────────────────────────────────────────────────
[ $# -ge 3 ] || _die "usage: check-journeys.sh CONF MAP TESTS_DIR [--all]"
_CONF="$1"
_MAP="$2"
_TESTS_DIR="$3"
_ALL=0
[ "${4:-}" = "--all" ] && _ALL=1

[ -r "$_CONF" ] || _die "conf not readable: $_CONF"
[ -r "$_MAP"  ] || _die "map not readable: $_MAP"

# ── Problem accumulator ────────────────────────────────────────────────────────
_TMPF=$(mktemp "${TMPDIR:-/tmp}/cj-XXXXXXXX") || _die "mktemp failed (fail closed)"
trap 'rm -f "$_TMPF"' EXIT INT TERM
_add_problem() { printf '%s\n' "$1" >> "$_TMPF"; }

# ── Step C.1: Lint ─────────────────────────────────────────────────────────────
if ! sh "$_LINT" "$_MAP" >/dev/null 2>&1; then
  _add_problem "lint-journey-map.sh failed (fail closed): MAP must be schema-valid"
  cat "$_TMPF" >&2
  exit 1
fi

# ── Step C.2: Authority ────────────────────────────────────────────────────────
if ! sh "$_AUTHORITY" "$_CONF" "$_MAP" >/dev/null 2>&1; then
  _add_problem "check-journey-authority.sh failed (fail closed): authority checks did not pass"
  cat "$_TMPF" >&2
  exit 1
fi

# ── Step C.3: Fetch validated ledger ──────────────────────────────────────────
# The gate NEVER reads runtime status from JOURNEY_MAP.md — runtime truth comes
# ONLY from the adapter-fetched ledger returned here.
_ledger=$(sh "$_FETCH" "$_CONF" 2>/dev/null)
_fetch_ec=$?
if [ "$_fetch_ec" -ne 0 ]; then
  _add_problem "journey-ledger-fetch.sh failed (fail closed): missing/malformed/untrusted/stale/unknown/no-ALLOW"
  cat "$_TMPF" >&2
  exit 1
fi

# ── Source libs ────────────────────────────────────────────────────────────────
JOURNEY_MAP="$_MAP"
export JOURNEY_MAP
# shellcheck disable=SC1090
. "$_LIB"
# shellcheck disable=SC1090
. "$_LEDGER_LIB"

_MAP_DIR="$(cd "$(dirname "$_MAP")" && pwd)"

# Collect all journey IDs for use in join, orphan scan, and stale runtime scan
_ids=$(journey_ids)

# ── Per-journey join ───────────────────────────────────────────────────────────
for _id in $_ids; do
  _astatus=$(journey_field "$_id" author_status 2>/dev/null) || _astatus=""
  _priority=$(journey_field "$_id" priority 2>/dev/null) || _priority=""

  # EXEMPT → skip enforcement (lint already validated exemption metadata)
  [ "$_astatus" = "EXEMPT" ] && continue

  # Determine if required. A non-EXEMPT journey with a blank/unknown priority
  # must NOT silently downgrade to non-required (that would be a fail-open) —
  # fail closed instead. The gate does not rely on lint tolerating blank values.
  _required=0
  case "$_priority" in
    P0|P1) _required=1 ;;
    P2|P3) [ "$_ALL" = "1" ] && _required=1 ;;
    *) _add_problem "$_id: missing/invalid priority '$_priority' (non-EXEMPT journey must declare P0-P3)"; continue ;;
  esac

  if [ "$_required" = "1" ]; then
    # Check 1: test field and file existence
    _test=$(journey_field "$_id" test 2>/dev/null) || _test=""
    if [ -z "$_test" ]; then
      _add_problem "$_id: test field empty (required journey missing test mapping)"
    elif [ ! -f "$_MAP_DIR/$_test" ]; then
      _add_problem "$_id: mapped test file missing: $_test (resolved: $_MAP_DIR/$_test)"
    fi

    # Check 2: ledger status (runtime truth from adapter — NEVER from MAP)
    _status=$(journey_ledger_status "$_ledger" "$_id")
    case "$_status" in
      GREEN)
        # Defense-in-depth: re-confirm evidence fields (adapter guarantees, but verify)
        _lr=$(printf '%s\n' "$_ledger" | jq -r --arg id "$_id" \
          '.journeys[$id].last_run // empty' 2>/dev/null)
        _ri=$(printf '%s\n' "$_ledger" | jq -r --arg id "$_id" \
          '.journeys[$id].ci_run_id // empty' 2>/dev/null)
        _af=$(printf '%s\n' "$_ledger" | jq -r --arg id "$_id" \
          '.journeys[$id].ci_artifact // empty' 2>/dev/null)
        if [ -z "$_lr" ] || [ -z "$_ri" ] || [ -z "$_af" ]; then
          _add_problem "$_id: GREEN status missing required evidence fields (last_run/ci_run_id/ci_artifact)"
        fi
        # GREEN with full fields → pass (no problem added)
        ;;
      RED|FLAKY)
        _summary=$(printf '%s\n' "$_ledger" | jq -r --arg id "$_id" \
          '.journeys[$id].failure_summary // "no failure_summary"' 2>/dev/null)
        _add_problem "$_id: ledger status=$_status — $_summary"
        ;;
      NOT_RUN)
        _add_problem "$_id: ledger status=NOT_RUN (not yet run in CI)"
        ;;
      *)
        _add_problem "$_id: unknown ledger status: $_status"
        ;;
    esac
  else
    # Non-required (P2/P3 in default mode): report status, WARN if non-GREEN
    _status=$(journey_ledger_status "$_ledger" "$_id")
    if [ "$_status" != "GREEN" ]; then
      printf 'WARN: %s: ledger status=%s (%s non-blocking in default mode)\n' \
        "$_id" "$_status" "$_priority" >&2
    fi
  fi
done

# ── Orphan scan ────────────────────────────────────────────────────────────────
# Every file matching TESTS_DIR/*.spec.* must be the test: of EXACTLY ONE journey.
# Zero matches → blocking orphan.  More than one match → blocking duplicate.
if [ -d "$_TESTS_DIR" ]; then
  for _spec in "$_TESTS_DIR"/*.spec.*; do
    [ -f "$_spec" ] || continue
    _bn=$(basename "$_spec")
    _expected_test="tests/journeys/$_bn"
    _count=0
    for _id in $_ids; do
      _t=$(journey_field "$_id" test 2>/dev/null) || continue
      [ "$_t" = "$_expected_test" ] && _count=$((_count + 1))
    done
    if [ "$_count" -eq 0 ]; then
      _add_problem "orphan journey test (no matching journey in MAP): $_expected_test"
    elif [ "$_count" -gt 1 ]; then
      _add_problem "duplicate test mapping ($_count journeys claim $_expected_test)"
    fi
  done
fi

# ── Stale runtime scan ─────────────────────────────────────────────────────────
# Every JOURNEY-ID present in the ledger but absent from MAP → WARN (non-blocking).
# Increment-1 does not require stale ledger entries to block.
_ledger_ids=$(printf '%s\n' "$_ledger" | jq -r '.journeys | keys[]' 2>/dev/null) || _ledger_ids=""
for _lid in $_ledger_ids; do
  _found=0
  for _id in $_ids; do
    [ "$_id" = "$_lid" ] && _found=1 && break
  done
  if [ "$_found" = "0" ]; then
    printf 'WARN: stale runtime status for %s (not in map)\n' "$_lid" >&2
  fi
done

# ── Result ─────────────────────────────────────────────────────────────────────
if [ -s "$_TMPF" ]; then
  cat "$_TMPF" >&2
  exit 1
fi
exit 0
