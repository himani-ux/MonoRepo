#!/bin/sh
# shellcheck shell=sh
# check-journey-authority.sh — Working-tree authority gate (Task 5).
#
# Usage: check-journey-authority.sh CONF MAP [MAP2 ...]
#
#   CONF    — ledger configuration file (same format as journey-ledger.conf),
#             passed to journey-ledger-fetch.sh for trusted-fetch verification.
#   MAP...  — canonical map file(s) (e.g. JOURNEY_MAP.md + JOURNEY_MAP.template.md)
#             that MUST be free of runtime-truth field keys.
#
# Exit 0 only if ALL checks pass. Accumulates every problem, prints each to
# stderr (one line per problem), then exits non-zero (fail closed).
#
# Checks performed
# ─────────────────
# 1. Runtime-field reintroduction — each MAP arg is scanned for runtime field
#    keys (ci_status, last_run, ci_run_id, ci_artifact, failure_summary).
#    The gate NEVER reads a runtime STATUS VALUE from a map; it only checks for
#    the ABSENCE of those field keys. A map with ci_status: GREEN fails because
#    the KEY is present, not because the gate read "GREEN".
#    A MAP arg that is not a readable file is itself a failure.
# 2. Tracked runtime ledger — scans git ls-files at the repo root. Fails if any
#    tracked file's basename is a forbidden ledger name (JOURNEY_STATUS.json,
#    journey-status.json, or basename of conf's LEDGER_PATH) unless the file
#    resides under AUTHORITY_FIXTURE_DIR.
#    The tracked-ledger scan is NOT overridable by a PR-controllable env var.
# 3. Trusted-fetch verification — delegates entirely to the Task-3 adapter
#    journey-ledger-fetch.sh "$CONF" (stdout discarded). If it exits non-zero
#    (missing / malformed / untrusted / stale / unknown-source-mode /
#    test-fixture-without-ALLOW_TEST_FIXTURE), this gate fails closed. The gate
#    NEVER synthesizes a pass, and NEVER reads runtime status from JOURNEY_MAP.md.
#
# CI-topology seam
# ─────────────────
# Production CI must load ledger configuration from a non-PR-controllable source,
# such as protected CI settings, a protected branch, OIDC-attested configuration,
# or an equivalent trusted control plane. Repo-local configuration is acceptable
# only for tests or local development and must not be treated as the production
# trust root.
#
# Optional env
# ─────────────
# AUTHORITY_FIXTURE_DIR  (default: <journey>/tests/fixtures)
#   Tracked files under this directory are EXEMPT from the tracked-ledger check.
#   MUST resolve to <journey>/tests or a strict subdirectory thereof — any value
#   outside that subtree (e.g. repo root, /, /tmp) is rejected with a fatal error.
#   This is the ONLY override carve-out; it is not PR-controllable at gate-time
#   because CI jobs set it via protected settings, not PR-modified files.
#
# Deps: sh, grep, git, jq (via journey-ledger-fetch.sh).

set -u
_SELF="$0"
_BINDIR="$(cd "$(dirname "$0")" && pwd)"
_JOURNEY_ROOT="$(cd "$_BINDIR/.." && pwd)"
_FETCH="$_JOURNEY_ROOT/lib/journey-ledger-fetch.sh"

_die() { printf '%s: %s\n' "$_SELF" "$1" >&2; exit 1; }

# ── Args ──────────────────────────────────────────────────────────────────────
[ $# -ge 2 ] || _die "usage: check-journey-authority.sh CONF MAP [MAP2 ...]"
_AUTH_CONF="$1"; shift
[ -r "$_AUTH_CONF" ] || _die "conf not readable: $_AUTH_CONF"

# ── Sanity: adapter must exist ────────────────────────────────────────────────
[ -f "$_FETCH" ] || _die "journey-ledger-fetch.sh not found: $_FETCH"

# ── Problem accumulator (temp file avoids subshell-variable isolation) ────────
# Fix 1: guard mktemp — failure here fails CLOSED (exit 1) before any check runs.
_AUTH_TMPF=$(mktemp "${TMPDIR:-/tmp}/authority-XXXXXXXX") || _die "mktemp failed (fail closed)"
trap 'rm -f "$_AUTH_TMPF"' EXIT INT TERM
_add_problem() { printf '%s\n' "$1" >> "$_AUTH_TMPF"; }

# ── Conf helper (strips inline comments + surrounding whitespace) ─────────────
_auth_conf_get() {
  _acv=$(grep -m1 "^${1}=" "$_AUTH_CONF" 2>/dev/null | cut -d= -f2- \
         | sed 's/[[:space:]]\{1,\}#.*$//;s/^[[:space:]]*//;s/[[:space:]]*$//')
  [ -n "$_acv" ] || return 1
  printf '%s\n' "$_acv"
}

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1 — Runtime-field reintroduction
#
# Scan each MAP arg for runtime field keys. The gate NEVER reads the value of
# any runtime field — it only checks that the key is absent. A map containing
# ci_status: GREEN fails because the key is present; the value "GREEN" is
# irrelevant and never read.
# Fix 3: A MAP arg that is not a readable file is itself a failure (fail closed).
# ─────────────────────────────────────────────────────────────────────────────
_RT_PAT='^[[:space:]]*(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):'

for _auth_map in "$@"; do
  if [ ! -r "$_auth_map" ]; then
    _add_problem "map file not readable: $_auth_map"
    continue
  fi
  if grep -qE "$_RT_PAT" "$_auth_map" 2>/dev/null; then
    _auth_field=$(grep -Em1 "$_RT_PAT" "$_auth_map" | sed 's/^[[:space:]]*//;s/[[:space:]].*//;s/:$//')
    _add_problem "runtime-field reintroduction in $_auth_map: ${_auth_field} (field key must not appear in map)"
  fi
done

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2 — Tracked runtime ledger
#
# Run git ls-files in the repo root. Forbidden basenames (case-insensitive):
#   - JOURNEY_STATUS.json / journey_status.json (any case)
#   - journey-status.json (any case)
#   - basename of conf's LEDGER_PATH (any case)
# Exception: tracked files under AUTHORITY_FIXTURE_DIR are exempt.
# AUTHORITY_FIXTURE_DIR MUST be within <journey>/tests — any wider value is
# rejected (fail closed) so it cannot disable Check 2.
# The scan is NOT overridable by a PR-controllable env var.
# Fix 4: NUL-delimited git ls-files + case-insensitive basename comparison.
# ─────────────────────────────────────────────────────────────────────────────
_auth_repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || _auth_repo_root=""

if [ -z "$_auth_repo_root" ]; then
  _add_problem "tracked-ledger check: git rev-parse --show-toplevel failed (not in a git repo?)"
else
  # Resolve fixture-dir exemption (default: <journey>/tests/fixtures)
  _auth_fix_dir="${AUTHORITY_FIXTURE_DIR:-$_JOURNEY_ROOT/tests/fixtures}"
  _auth_fix_dir_abs=$(cd "$_auth_fix_dir" 2>/dev/null && pwd) || _auth_fix_dir_abs="$_auth_fix_dir"

  # Fix 2: AUTHORITY_FIXTURE_DIR must be within <journey>/tests (not repo root, /, /tmp, etc.)
  _journey_tests_dir="$_JOURNEY_ROOT/tests"
  case "$_auth_fix_dir_abs" in
    "$_journey_tests_dir"|"$_journey_tests_dir"/*)
      : ;; # permitted subtree
    *)
      _die "AUTHORITY_FIXTURE_DIR must be within <journey>/tests (fail closed): $_auth_fix_dir_abs"
      ;;
  esac

  # Get conf's LEDGER_PATH basename for the forbidden list (lowercased for comparison)
  _auth_conf_lp=$(_auth_conf_get LEDGER_PATH) || _auth_conf_lp=""
  _auth_conf_lb=""
  _auth_conf_lb_lower=""
  if [ -n "$_auth_conf_lp" ]; then
    _auth_conf_lb=$(basename "$_auth_conf_lp")
    _auth_conf_lb_lower=$(printf '%s' "$_auth_conf_lb" | tr '[:upper:]' '[:lower:]')
  fi

  # Fix 4: quotePath=false keeps non-ASCII paths raw (no octal-quoting that would
  # break basename matching). Newline-delimited + `IFS= read -r` is POSIX and
  # handles spaces; filenames containing a literal newline are not handled, which
  # is negligible for fixed ledger basenames. (Avoids the non-POSIX `read -d`.)
  _auth_ls_tmp=$(mktemp "${TMPDIR:-/tmp}/authority-ls-XXXXXXXX") || _die "mktemp failed (fail closed)"
  git -c core.quotePath=false -C "$_auth_repo_root" ls-files > "$_auth_ls_tmp" 2>/dev/null
  while IFS= read -r _auth_tf; do
    _auth_tb=$(basename "$_auth_tf")
    # Fix 4: case-insensitive comparison — lowercase both sides
    _auth_tb_lower=$(printf '%s' "$_auth_tb" | tr '[:upper:]' '[:lower:]')
    _auth_forbidden=0
    case "$_auth_tb_lower" in
      journey_status.json|journey-status.json)
        _auth_forbidden=1
        ;;
      *)
        if [ -n "$_auth_conf_lb_lower" ] && [ "$_auth_tb_lower" = "$_auth_conf_lb_lower" ]; then
          _auth_forbidden=1
        fi
        ;;
    esac
    if [ "$_auth_forbidden" = "1" ]; then
      _auth_full="$_auth_repo_root/$_auth_tf"
      case "$_auth_full" in
        "$_auth_fix_dir_abs/"*)
          : ;; # exempt — test fixture, not a production ledger
        *)
          _add_problem "tracked runtime ledger in working tree: $_auth_tf"
          ;;
      esac
    fi
  done < "$_auth_ls_tmp"
  rm -f "$_auth_ls_tmp"
fi

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3 — Trusted-fetch verification (delegates to Task-3 adapter)
#
# Runtime trust is obtained ONLY via journey-ledger-fetch.sh. The gate never
# reads a status value from JOURNEY_MAP.md or any map file. If the adapter
# exits non-zero for any reason, this gate fails closed — no exceptions.
# ─────────────────────────────────────────────────────────────────────────────
if ! sh "$_FETCH" "$_AUTH_CONF" >/dev/null 2>&1; then
  _add_problem "trusted-fetch verification failed (fail closed): journey-ledger-fetch.sh returned non-zero"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Result — emit all problems and exit
# ─────────────────────────────────────────────────────────────────────────────
if [ -s "$_AUTH_TMPF" ]; then
  cat "$_AUTH_TMPF" >&2
  exit 1
fi
exit 0
