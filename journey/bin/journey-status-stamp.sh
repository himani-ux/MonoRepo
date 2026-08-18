#!/bin/sh
# shellcheck shell=sh
# journey-status-stamp.sh — CI-ONLY ledger stamper.
#
# WARNING: This script is for CI use ONLY.
#          Do NOT run as an agent, human, or PR-triggered script.
#          It is the sole authorised writer to the runtime ledger.
#
# Usage:
#   JOURNEY_STATUS_FILE=<ledger-path>        \
#   JOURNEY_LEDGER_SOURCE=<source-id-string> \
#     journey-status-stamp.sh ID STATUS      \
#       [--run-id X] [--artifact Y] [--failure-summary Z]
#
# STATUS must be one of: NOT_RUN GREEN RED FLAKY
#
# Validation rules (enforced before any write):
#   GREEN  ⇒ --run-id and --artifact are REQUIRED.
#   RED    ⇒ --failure-summary is REQUIRED.
#   FLAKY  ⇒ --failure-summary is REQUIRED.
#   NOT_RUN ⇒ no field requirements.
#
# The stamper validates its own output and REFUSES to write an invalid record.
# If validation fails the ledger file is left unchanged (or uncreated).
#
# Full CI integration — publishing the stamped ledger to the protected branch or
# artifact store — is DEFERRED to Task 6 / CI wiring.  This script only writes
# to $JOURNEY_STATUS_FILE on the local filesystem.
#
# Deps: jq (1.5+), POSIX sh.

set -u
_SELF="$0"

_die() {
  printf '%s: %s\n' "$_SELF" "$1" >&2
  exit 1
}

# ── Validate required env vars ────────────────────────────────────────────────
[ -n "${JOURNEY_STATUS_FILE:-}" ] \
  || _die "JOURNEY_STATUS_FILE must be set"
[ -n "${JOURNEY_LEDGER_SOURCE:-}" ] \
  || _die "JOURNEY_LEDGER_SOURCE must be set"

# ── Parse positional args ─────────────────────────────────────────────────────
[ $# -ge 2 ] \
  || _die "usage: journey-status-stamp.sh ID STATUS [--run-id X --artifact Y --failure-summary Z]"

_ID="$1"
_STATUS="$2"
shift 2

case "$_STATUS" in
  NOT_RUN|GREEN|RED|FLAKY) ;;
  *) _die "STATUS must be one of: NOT_RUN GREEN RED FLAKY; got: $_STATUS" ;;
esac

# ── Parse optional flags ──────────────────────────────────────────────────────
_RUN_ID=""
_ARTIFACT=""
_FAILURE_SUMMARY=""

while [ $# -gt 0 ]; do
  case "$1" in
    --run-id)
      [ $# -ge 2 ] || _die "--run-id requires a value"
      _RUN_ID="$2"; shift 2 ;;
    --artifact)
      [ $# -ge 2 ] || _die "--artifact requires a value"
      _ARTIFACT="$2"; shift 2 ;;
    --failure-summary)
      [ $# -ge 2 ] || _die "--failure-summary requires a value"
      _FAILURE_SUMMARY="$2"; shift 2 ;;
    *) _die "unknown option: $1" ;;
  esac
done

# ── Load ledger library ───────────────────────────────────────────────────────
_LIBDIR="$(cd "$(dirname "$0")" && pwd)/../lib"
[ -f "$_LIBDIR/journey-ledger.sh" ] \
  || _die "cannot find journey-ledger.sh in $_LIBDIR"
# shellcheck disable=SC1090
. "$_LIBDIR/journey-ledger.sh"

# ── Get current UTC time ──────────────────────────────────────────────────────
_NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null) \
  || _die "cannot get current UTC time"

# ── Read or create the ledger ─────────────────────────────────────────────────
_LEDGER="$JOURNEY_STATUS_FILE"

if [ -f "$_LEDGER" ]; then
  _EXISTING=$(cat "$_LEDGER") \
    || _die "cannot read existing ledger: $_LEDGER"
  printf '%s\n' "$_EXISTING" | jq -e . >/dev/null 2>&1 \
    || _die "existing ledger is not valid JSON: $_LEDGER"
else
  _EXISTING=$(jq -n \
    --argjson sv 1 \
    --arg gb "ci" \
    --arg ga "$_NOW" \
    --arg src "$JOURNEY_LEDGER_SOURCE" \
    '{schema_version: $sv, generated_by: $gb, generated_at: $ga, source: $src, journeys: {}}') \
    || _die "failed to construct initial ledger JSON"
fi

# ── Build the record value ─────────────────────────────────────────────────────
# Represent optional string fields as JSON null when empty
_run_id_json="null"
[ -n "$_RUN_ID" ] && _run_id_json=$(jq -rn --arg v "$_RUN_ID" '$v | @json')

_artifact_json="null"
[ -n "$_ARTIFACT" ] && _artifact_json=$(jq -rn --arg v "$_ARTIFACT" '$v | @json')

_failure_json="null"
[ -n "$_FAILURE_SUMMARY" ] && _failure_json=$(jq -rn --arg v "$_FAILURE_SUMMARY" '$v | @json')

# ── Apply update ──────────────────────────────────────────────────────────────
_NEW_LEDGER=$(printf '%s\n' "$_EXISTING" | jq \
  --arg  id              "$_ID" \
  --arg  status          "$_STATUS" \
  --arg  now             "$_NOW" \
  --argjson run_id       "$_run_id_json" \
  --argjson artifact     "$_artifact_json" \
  --argjson failure_sum  "$_failure_json" \
  '.generated_at = $now |
   .journeys[$id] = {
     ci_status:       $status,
     last_run:        $now,
     ci_run_id:       $run_id,
     ci_artifact:     $artifact,
     failure_summary: $failure_sum
   }') \
  || _die "jq failed to construct updated ledger"

# ── Validate the candidate record, then publish atomically ───────────────────
# Write to a temp file in the SAME directory as the target so the final step is a
# same-filesystem rename (atomic) — never a torn in-place copy.
_LEDGER_DIR=$(dirname "$_LEDGER")
# Template's Xs are TERMINAL (P4 fix, M-T1-4/BSD-mktemp class): a run of Xs
# followed by a literal suffix (the old `.journey-stamp-XXXXXXXX.json`) is
# NOT randomized by BSD mktemp (macOS) — it mkstemp()s that literal filename
# verbatim every time, so a second/concurrent stamper invocation in the same
# ledger dir collides with `mkstemp failed ... File exists` instead of
# getting its own unique temp name. See journey/tests/ledger_test.sh's own
# P2 fix (same class, `ledger-stamp-XXXXXXXX.json` -> `ledger-stamp-json-XXXXXXXX`).
_TMPF=$(mktemp "$_LEDGER_DIR/.journey-stamp-json-XXXXXXXX") \
  || _die "mktemp failed in $_LEDGER_DIR (fail closed)"
[ -n "$_TMPF" ] || _die "mktemp returned empty path in $_LEDGER_DIR (fail closed)"
_stamp_cleanup() { rm -f "$_TMPF"; }
trap '_stamp_cleanup' EXIT INT TERM

printf '%s\n' "$_NEW_LEDGER" > "$_TMPF" \
  || _die "cannot write temp ledger"

if ! journey_ledger_validate "$_TMPF"; then
  _die "REFUSING write: updated ledger record is invalid (see above)"
fi

# Atomic publish: rename the validated temp onto the target (same filesystem).
mv "$_TMPF" "$_LEDGER" \
  || _die "failed to write ledger to: $_LEDGER"
