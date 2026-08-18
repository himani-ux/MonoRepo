#!/bin/sh
# shellcheck shell=sh
# runner-resolve_test.sh — TDD proofs for journey-runner-resolve.sh + convention doc.
# Run via: sh journey/tests/runner-resolve_test.sh   (also run by run.sh)

. "$(dirname "$0")/assert.sh"

_rr_assert_nonzero() { # CODE MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"
  else printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

_RR_HERE="$(cd "$(dirname "$0")" && pwd)"
_RR_RESOLVE="$_RR_HERE/../bin/journey-runner-resolve.sh"
_RR_DOC="$_RR_HERE/../docs/tests-journeys-convention.md"

_RR_TMP=""
_rr_ts() { _f=$(mktemp /tmp/rr-ts-XXXXXXXX); _RR_TMP="$_RR_TMP $_f"; printf '%s\n' "$@" > "$_f"; printf '%s\n' "$_f"; }

# valid resolves
_ts=$(_rr_ts "JOURNEY_RUNNER: playwright")
assert_eq "playwright" "$(sh "$_RR_RESOLVE" "$_ts")" "valid JOURNEY_RUNNER resolves to playwright"

# case + whitespace + inline comment are normalized safely
_ts=$(_rr_ts "JOURNEY_RUNNER:    Playwright    # the web runner")
assert_eq "playwright" "$(sh "$_RR_RESOLVE" "$_ts")" "whitespace/comment/case normalized to playwright"

# another valid runner
_ts=$(_rr_ts "JOURNEY_RUNNER: http")
assert_eq "http" "$(sh "$_RR_RESOLVE" "$_ts")" "http runner resolves"

# missing JOURNEY_RUNNER fails closed
_ts=$(_rr_ts "SOME_OTHER_KEY: value")
sh "$_RR_RESOLVE" "$_ts" >/dev/null 2>&1; _rr_assert_nonzero $? "missing JOURNEY_RUNNER → fail closed"

# blank JOURNEY_RUNNER fails closed
_ts=$(_rr_ts "JOURNEY_RUNNER:")
sh "$_RR_RESOLVE" "$_ts" >/dev/null 2>&1; _rr_assert_nonzero $? "blank JOURNEY_RUNNER → fail closed"

# whitespace-only value fails closed
_ts=$(_rr_ts "JOURNEY_RUNNER:      ")
sh "$_RR_RESOLVE" "$_ts" >/dev/null 2>&1; _rr_assert_nonzero $? "whitespace-only JOURNEY_RUNNER → fail closed"

# unknown JOURNEY_RUNNER fails closed
_ts=$(_rr_ts "JOURNEY_RUNNER: selenium")
sh "$_RR_RESOLVE" "$_ts" >/dev/null 2>&1; _rr_assert_nonzero $? "unknown JOURNEY_RUNNER → fail closed"

# stub WITHOUT ALLOW_STUB_RUNNER fails closed
_ts=$(_rr_ts "JOURNEY_RUNNER: stub")
sh "$_RR_RESOLVE" "$_ts" >/dev/null 2>&1; _rr_assert_nonzero $? "stub without ALLOW_STUB_RUNNER → fail closed"

# stub WITH ALLOW_STUB_RUNNER=1 resolves (local/fixture context only)
_ts=$(_rr_ts "JOURNEY_RUNNER: stub")
assert_eq "stub" "$(ALLOW_STUB_RUNNER=1 sh "$_RR_RESOLVE" "$_ts")" "stub allowed only with ALLOW_STUB_RUNNER=1"

# convention doc exists and mentions the required concepts
assert_contains "$(cat "$_RR_DOC")" "tests/journeys/" "convention doc mentions tests/journeys/"
assert_contains "$(cat "$_RR_DOC")" "JOURNEY-ID" "convention doc mentions JOURNEY-ID"
assert_contains "$(cat "$_RR_DOC")" "JOURNEY_MAP.md" "convention doc mentions JOURNEY_MAP.md"
assert_contains "$(cat "$_RR_DOC")" "deterministic" "convention doc mentions deterministic journey tests"

# cleanup
# shellcheck disable=SC2086
rm -f $_RR_TMP
