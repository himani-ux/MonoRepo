#!/bin/sh
# shellcheck shell=sh
# journey-runner-resolve.sh TECH_STACK_FILE
#
# Reads JOURNEY_RUNNER from the project's tech-stack file, normalizes and validates
# it, and prints the normalized runner value on success (exit 0). Fails closed
# (exit 1, reason on stderr) if JOURNEY_RUNNER is missing, blank, or unknown.
#
# This script DOES NOT execute the runner — it only resolves and validates the
# declared value for later tasks (e.g. the CI wiring) to consume.
#
# Allowed runners: playwright | maestro | appium | pty | http | stub
#   `stub` is for local/fixture use during Increment 1 ONLY and requires
#   ALLOW_STUB_RUNNER=1 in the environment; it is not a production runner and must
#   never be a production escape hatch.
#
# Normalization: the value is taken from the first `JOURNEY_RUNNER:` line, with any
# trailing inline `# comment` stripped, surrounding whitespace trimmed, and lowercased.
set -u

TS="${1:-}"
[ -n "$TS" ] || { echo "journey-runner-resolve: usage: journey-runner-resolve.sh TECH_STACK_FILE" >&2; exit 1; }
[ -r "$TS" ] || { echo "journey-runner-resolve: tech-stack file not readable: $TS" >&2; exit 1; }

_raw=$(grep -m1 '^JOURNEY_RUNNER:' "$TS" 2>/dev/null | sed 's/^JOURNEY_RUNNER:[[:space:]]*//')
_val=$(printf '%s' "$_raw" \
  | sed 's/[[:space:]]\{1,\}#.*$//;s/^[[:space:]]*//;s/[[:space:]]*$//' \
  | tr '[:upper:]' '[:lower:]')

if [ -z "$_val" ]; then
  echo "journey-runner-resolve: JOURNEY_RUNNER is missing or blank in $TS (fail closed)" >&2
  exit 1
fi

case "$_val" in
  playwright|maestro|appium|pty|http)
    : ;;  # valid production runner
  stub)
    if [ "${ALLOW_STUB_RUNNER:-}" != "1" ]; then
      echo "journey-runner-resolve: 'stub' runner requires ALLOW_STUB_RUNNER=1 (local/fixtures only; not a production runner)" >&2
      exit 1
    fi
    ;;
  *)
    echo "journey-runner-resolve: unknown JOURNEY_RUNNER '$_val' (allowed: playwright|maestro|appium|pty|http|stub)" >&2
    exit 1
    ;;
esac

printf '%s\n' "$_val"
