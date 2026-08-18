#!/bin/sh
# shellcheck shell=sh
# journey-ledger-fetch.sh — Trusted fetch adapter for the CI-owned runtime ledger.
#
# Usage: journey-ledger-fetch.sh CONF
#
# On success: print the VALIDATED ledger JSON to stdout, exit 0.
#             Also writes to $LEDGER_OUT (conf or env var) when set.
# On failure: exit non-zero, print reason to stderr, write NOTHING to stdout.
#             Failures: unreadable conf, unknown LEDGER_SOURCE, unreadable/
#             missing/malformed/invalid/untrusted/stale ledger.
#
# Trust model
# ────────────
# PRODUCTION trust roots:
#   git-branch  — ledger is read from a PROTECTED ref via `git fetch origin`.
#                 PRs cannot push the protected ref, so the content is CI-owned.
#   ci-artifact — ledger is read from a path populated by a trusted CI job that
#                 uses OIDC / signed artifacts.  PRs cannot write another job's
#                 artifacts.
# TEST-ONLY mode:
#   test-fixture — reads from a local fixture file.  REQUIRES ALLOW_TEST_FIXTURE=1
#                  in the conf.  NEVER set this in a production conf.
#
# RESIDUAL AUTHORITY SEAM (brief §E.2)
# ──────────────────────────────────────
# journey-ledger.conf is a file inside the repository and is therefore
# PR-editable.  In production the CI gate MUST load the conf from a source that
# a PR cannot control — the protected-branch copy of the conf, a CI org-level
# secret, or OIDC-bound configuration.  A PR that can modify the conf being used
# at gate-time could set test-fixture mode or repoint EXPECTED_SOURCE.
# Task 3 builds the mechanism; ensuring the conf itself is non-PR-controllable
# is a CI-topology requirement deferred to the Task-6 / CI wiring.
#
# LEDGER_MAX_AGE_SECONDS (optional conf key)
# ─────────────────────────────────────────────
# When set, the adapter fails closed if the ledger's generated_at timestamp is
# older than LEDGER_MAX_AGE_SECONDS seconds.  Timestamp parsing requires either
# GNU date (-d flag) or BSD date (-j flag); if neither is available the adapter
# fails closed rather than passing an unverified age.
# When NOT set, staleness is NOT enforced — document this in your ops runbook as
# a known limitation.
#
# Deps: jq (1.5+), git (git-branch mode only), POSIX sh.

set -u
_SELF="$0"

_die() {
  printf '%s: %s\n' "$_SELF" "$1" >&2
  exit 1
}

# ── Load ledger library ───────────────────────────────────────────────────────
_LIBDIR="$(cd "$(dirname "$0")" && pwd)"
if [ ! -f "$_LIBDIR/journey-ledger.sh" ]; then
  _die "cannot find journey-ledger.sh in $_LIBDIR"
fi
# shellcheck disable=SC1090
. "$_LIBDIR/journey-ledger.sh"

# ── Parse args ────────────────────────────────────────────────────────────────
[ $# -ge 1 ] || _die "usage: journey-ledger-fetch.sh CONF"
_CONF="$1"
[ -r "$_CONF" ] || _die "conf not readable: $_CONF"

# ── Conf helpers ──────────────────────────────────────────────────────────────
_conf_get() {
  # _conf_get KEY — prints the value or exits 1 if absent/empty.
  # Strips trailing inline comments (whitespace + '#' + rest) and surrounding
  # whitespace.  A '#' NOT preceded by whitespace is kept (part of the value).
  _cv=$(grep -m1 "^${1}=" "$_CONF" 2>/dev/null | cut -d= -f2- \
        | sed 's/[[:space:]]\{1,\}#.*$//;s/^[[:space:]]*//;s/[[:space:]]*$//')
  [ -n "$_cv" ] || return 1
  printf '%s\n' "$_cv"
}

# ── Validate conf keys ────────────────────────────────────────────────────────
_LEDGER_SOURCE=$(_conf_get LEDGER_SOURCE) \
  || _die "LEDGER_SOURCE not set in conf (fail closed)"

_EXPECTED_SOURCE=$(_conf_get EXPECTED_SOURCE) \
  || _die "EXPECTED_SOURCE not set in conf (fail closed)"

# LEDGER_OUT: env var takes precedence over conf value
_LEDGER_OUT="${LEDGER_OUT:-}"
if [ -z "$_LEDGER_OUT" ]; then
  _LEDGER_OUT=$(_conf_get LEDGER_OUT) || _LEDGER_OUT=""
fi

# ── Temp-file management ──────────────────────────────────────────────────────
_CREATED_TMPF=""
_fetch_cleanup() { [ -z "$_CREATED_TMPF" ] || rm -f "$_CREATED_TMPF"; }
trap '_fetch_cleanup' EXIT INT TERM

# ── Obtain raw JSON per LEDGER_SOURCE mode ────────────────────────────────────
case "$_LEDGER_SOURCE" in

  git-branch)
    # Production mode: staleness enforcement is REQUIRED (spec §4.5 — a stale
    # ledger fails closed by default, not opt-in).
    _conf_get LEDGER_MAX_AGE_SECONDS >/dev/null \
      || _die "git-branch mode: LEDGER_MAX_AGE_SECONDS not set in conf (staleness must be enforced in production modes — fail closed)"
    _LEDGER_REF=$(_conf_get LEDGER_REF) \
      || _die "git-branch mode: LEDGER_REF not set in conf"
    _LEDGER_PATH=$(_conf_get LEDGER_PATH) \
      || _die "git-branch mode: LEDGER_PATH not set in conf"
    # Fetch the protected ref — never read from the working tree.
    # The ref MUST be fully qualified: with a short name, git's resolution
    # prefers refs/tags/ over refs/heads/, so a PR author who pushes a TAG
    # named like the protected branch would shadow it into FETCH_HEAD.
    # Branch protection does not cover the tag namespace, so refs/tags/*
    # is never a trust root here.
    case "$_LEDGER_REF" in
      refs/tags/*)
        _die "git-branch mode: refs/tags/* is not a trust root (branch protection does not cover tags): $_LEDGER_REF" ;;
      refs/*)
        _QREF="$_LEDGER_REF" ;;
      *)
        _QREF="refs/heads/$_LEDGER_REF" ;;
    esac
    git fetch -q origin "$_QREF" 2>/dev/null \
      || _die "git fetch failed for ref: $_QREF"
    _RAW=$(git show "FETCH_HEAD:$_LEDGER_PATH" 2>/dev/null) \
      || _die "git show failed for $_LEDGER_PATH on FETCH_HEAD"
    # Template's Xs are TERMINAL (P4 fix, M-T1-4/BSD-mktemp class): a run of
    # Xs followed by a literal suffix (the old
    # `journey-ledger-XXXXXXXX.json`) is NOT randomized by BSD mktemp
    # (macOS) — it mkstemp()s that literal filename verbatim every time, so
    # a second/concurrent fetch in the same TMPDIR collides with `mkstemp
    # failed ... File exists` instead of getting its own unique temp name.
    _TMPF=$(mktemp "${TMPDIR:-/tmp}/journey-ledger-json-XXXXXXXX") \
      || _die "mktemp failed (fail closed)"
    [ -n "$_TMPF" ] || _die "mktemp returned empty path (fail closed)"
    _CREATED_TMPF="$_TMPF"
    printf '%s\n' "$_RAW" > "$_TMPF"
    ;;

  ci-artifact)
    # Production mode: staleness enforcement is REQUIRED (spec §4.5).
    _conf_get LEDGER_MAX_AGE_SECONDS >/dev/null \
      || _die "ci-artifact mode: LEDGER_MAX_AGE_SECONDS not set in conf (staleness must be enforced in production modes — fail closed)"
    _LEDGER_ARTIFACT=$(_conf_get LEDGER_ARTIFACT) \
      || _die "ci-artifact mode: LEDGER_ARTIFACT not set in conf"
    [ -r "$_LEDGER_ARTIFACT" ] \
      || _die "ci-artifact not readable: $_LEDGER_ARTIFACT"
    _TMPF="$_LEDGER_ARTIFACT"
    ;;

  test-fixture)
    # !! TEST-ONLY mode — NEVER use in production !!
    _ALLOW=$(_conf_get ALLOW_TEST_FIXTURE) || _ALLOW=""
    if [ "$_ALLOW" != "1" ]; then
      _die "test-fixture mode requires ALLOW_TEST_FIXTURE=1 in conf. NEVER set in production."
    fi
    _LEDGER_PATH=$(_conf_get LEDGER_PATH) \
      || _die "test-fixture mode: LEDGER_PATH not set in conf"
    [ -r "$_LEDGER_PATH" ] \
      || _die "test-fixture file not readable: $_LEDGER_PATH"
    _TMPF="$_LEDGER_PATH"
    ;;

  *)
    _die "unknown LEDGER_SOURCE: $_LEDGER_SOURCE (must be: git-branch | ci-artifact | test-fixture)"
    ;;
esac

# ── Validate ledger ───────────────────────────────────────────────────────────
journey_ledger_validate "$_TMPF" || exit 1

# ── Verify source identity ────────────────────────────────────────────────────
_ACTUAL_SRC=$(jq -r '.source // empty' "$_TMPF" 2>/dev/null)
if [ "$_ACTUAL_SRC" != "$_EXPECTED_SOURCE" ]; then
  printf '%s: UNTRUSTED source: expected [%s], got [%s]\n' \
    "$_SELF" "$_EXPECTED_SOURCE" "$_ACTUAL_SRC" >&2
  exit 1
fi

# ── Staleness check (optional) ────────────────────────────────────────────────
_MAX_AGE=$(_conf_get LEDGER_MAX_AGE_SECONDS) || _MAX_AGE=""
if [ -n "$_MAX_AGE" ]; then
  # Fix 2: reject non-numeric LEDGER_MAX_AGE_SECONDS (fail closed)
  case "$_MAX_AGE" in
    *[!0-9]*) _die "LEDGER_MAX_AGE_SECONDS must be a non-negative integer: $_MAX_AGE" ;;
  esac

  _GEN_AT=$(jq -r '.generated_at // empty' "$_TMPF" 2>/dev/null)
  [ -n "$_GEN_AT" ] || _die "staleness check: generated_at is empty"

  _NOW_EPOCH=$(date +%s 2>/dev/null) \
    || _die "staleness check: cannot get current epoch time (date +%s failed)"

  # Fix 1: parse generated_at as UTC on both GNU and BSD date.
  # GNU date (-d) already honors the trailing Z.
  # BSD date (-j): use TZ=UTC with format "%Y-%m-%dT%H:%M:%SZ" (Z in format
  #   matches the literal Z in the timestamp) so the result is a UTC epoch.
  # If neither parser yields a UTC epoch, FAIL CLOSED.
  _GEN_EPOCH=$(date -d "$_GEN_AT" +%s 2>/dev/null) \
    || _GEN_EPOCH=$(TZ=UTC date -j -f "%Y-%m-%dT%H:%M:%SZ" "$_GEN_AT" +%s 2>/dev/null) \
    || _die "staleness check: cannot parse generated_at timestamp: $_GEN_AT"

  _AGE=$((_NOW_EPOCH - _GEN_EPOCH))
  # Fix (MIN-2): a future generated_at yields a negative age; do NOT treat it as
  # fresh. Fail closed on clock skew or a forged future timestamp.
  if [ "$_AGE" -lt 0 ]; then
    _die "ledger generated_at is in the FUTURE ($_GEN_AT); fail closed (clock skew or forged timestamp)"
  fi
  if [ "$_AGE" -gt "$_MAX_AGE" ]; then
    _die "ledger is stale: age ${_AGE}s exceeds LEDGER_MAX_AGE_SECONDS=${_MAX_AGE}s"
  fi
fi

# ── Emit ──────────────────────────────────────────────────────────────────────
_JSON=$(cat "$_TMPF")

if [ -n "$_LEDGER_OUT" ]; then
  printf '%s\n' "$_JSON" > "$_LEDGER_OUT" \
    || _die "failed to write LEDGER_OUT: $_LEDGER_OUT"
fi

printf '%s\n' "$_JSON"
