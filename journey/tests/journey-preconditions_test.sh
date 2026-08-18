#!/bin/sh
# journey-preconditions_test.sh — TDD proofs for lint-journey-map.sh Check 8
# (optional `preconditions:` field grammar: PRECONDITION_FORMAT,
# PRECONDITION_KIND_UNKNOWN, PRECONDITION_EMPTY).
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LINT="$TESTS_DIR/../bin/lint-journey-map.sh"
GOOD="$TESTS_DIR/fixtures/good/JOURNEY_MAP.md"
LINT_FX="$TESTS_DIR/fixtures/lint"

# ── Positive: well-formed preconditions block (all four kinds) ───────────
assert_exit 0 sh "$LINT" "$LINT_FX/preconditions-good.md"

# ── Regression lock: preconditions stays OPTIONAL — the existing good map
#    (which carries no preconditions: field at all) still passes ────────
assert_exit 0 sh "$LINT" "$GOOD"

# ── Negative: entry kind outside {auth, env, data, state} ────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/preconditions-bad-kind.md"
_jpc_kind_out="$(sh "$LINT" "$LINT_FX/preconditions-bad-kind.md" 2>&1)"
assert_contains "$_jpc_kind_out" "PRECONDITION_KIND_UNKNOWN" \
  "unknown precondition kind is reported"

# ── Negative: entry missing the ": " separator ────────────────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/preconditions-bad-format.md"
_jpc_format_out="$(sh "$LINT" "$LINT_FX/preconditions-bad-format.md" 2>&1)"
assert_contains "$_jpc_format_out" "PRECONDITION_FORMAT" \
  "malformed precondition entry (missing colon) is reported"

# ── Negative: preconditions: present with zero entry lines ───────────────
assert_exit 1 sh "$LINT" "$LINT_FX/preconditions-empty.md"
_jpc_empty_out="$(sh "$LINT" "$LINT_FX/preconditions-empty.md" 2>&1)"
assert_contains "$_jpc_empty_out" "PRECONDITION_EMPTY" \
  "empty preconditions block is reported"

# ── Negative: value contains a space ──────────────────────────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/preconditions-bad-value.md"
_jpc_value_out="$(sh "$LINT" "$LINT_FX/preconditions-bad-value.md" 2>&1)"
assert_contains "$_jpc_value_out" "PRECONDITION_FORMAT" \
  "precondition value with a space is reported as PRECONDITION_FORMAT"
