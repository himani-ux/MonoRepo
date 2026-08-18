#!/bin/sh
# lint-journey-map_test.sh — TDD proofs for lint-journey-map.sh
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LINT="$TESTS_DIR/../bin/lint-journey-map.sh"
GOOD="$TESTS_DIR/fixtures/good/JOURNEY_MAP.md"
LINT_FX="$TESTS_DIR/fixtures/lint"

# ── Positive: valid map passes ────────────────────────────────────────────
assert_exit 0 sh "$LINT" "$GOOD"

# ── Negative: missing required field ─────────────────────────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/missing-field.md"

# ── Negative: invalid enum value (priority) ───────────────────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/bad-enum.md"

# ── Negative: forbidden runtime-truth field ───────────────────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/runtime-field.md"

# ── Negative: empty negative_states (non-exempt) ─────────────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/empty-negstates.md"

# ── Negative: declared negative state NOT in steps ───────────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/negstate-no-step.md"

# ── Positive: declared negative state present in steps (good/) ───────────
assert_exit 0 sh "$LINT" "$GOOD"

# ── Negative: missing data fixture file ───────────────────────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/missing-fixture.md"

# ── Positive: existing data fixture (good/) ──────────────────────────────
assert_exit 0 sh "$LINT" "$GOOD"

# ── Negative: WRITTEN with empty test field ───────────────────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/written-empty-test.md"

# ── Negative: EXEMPT with incomplete exemption metadata ───────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/exempt-incomplete.md"

# ── Positive: EXEMPT with complete exemption metadata ────────────────────
assert_exit 0 sh "$LINT" "$LINT_FX/exempt-complete.md"

# ── Negative: EXEMPT with an EXPIRED exemption (MIN-3) ────────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/exempt-expired.md"
_ee_out="$(sh "$LINT" "$LINT_FX/exempt-expired.md" 2>&1)"
assert_contains "$_ee_out" "expired" "expired EXEMPT exemption is reported by lint"

# ── Negative: MISSING enum field reports ONLY missing (no double enum error) ──
_mef_out="$(sh "$LINT" "$LINT_FX/missing-enum-field.md" 2>&1)"
assert_exit 1 sh "$LINT" "$LINT_FX/missing-enum-field.md"
assert_contains "$_mef_out" "missing required field: origin" \
  "missing enum field reports the missing-field error"
assert_not_contains "$_mef_out" "invalid origin" \
  "missing enum field does NOT also emit invalid-enum noise"

# ── Negative: invalid oracle_surface (enforced independently of priority) ─────
_bos_out="$(sh "$LINT" "$LINT_FX/bad-oracle-surface.md" 2>&1)"
assert_exit 1 sh "$LINT" "$LINT_FX/bad-oracle-surface.md"
assert_contains "$_bos_out" "invalid oracle_surface value: DB" \
  "oracle_surface enum is enforced (DB rejected)"

# ── Negative: blank priority VALUE fails (defense-in-depth; no enum double) ────
_bp_out="$(sh "$LINT" "$LINT_FX/blank-priority.md" 2>&1)"
assert_exit 1 sh "$LINT" "$LINT_FX/blank-priority.md"
assert_contains "$_bp_out" "required field is blank: priority" \
  "blank priority value → blank-required-field error"
assert_not_contains "$_bp_out" "invalid priority" \
  "blank priority value does NOT also emit invalid-enum noise"

# ── Negative: blank goal VALUE fails ─────────────────────────────────────────
_bg_out="$(sh "$LINT" "$LINT_FX/blank-goal.md" 2>&1)"
assert_exit 1 sh "$LINT" "$LINT_FX/blank-goal.md"
assert_contains "$_bg_out" "required field is blank: goal" \
  "blank goal value → blank-required-field error"

# ── Positive: DERIVED origin is accepted ─────────────────────────────────────
assert_exit 0 sh "$LINT" "$LINT_FX/derived-origin.md"

# ── Negative: DUPLICATE JOURNEY-ID (review finding #3 — smuggled 2nd block) ──
assert_exit 1 sh "$LINT" "$LINT_FX/duplicate-id.md"
_dup_err=$(sh "$LINT" "$LINT_FX/duplicate-id.md" 2>&1)
assert_contains "$_dup_err" "DUPLICATE_JOURNEY_ID" "lint: duplicate id names DUPLICATE_JOURNEY_ID"

# ── Negative: runner not in the allowed enum (review I4) ─────────────────────
assert_exit 1 sh "$LINT" "$LINT_FX/bad-runner.md"
_run_err=$(sh "$LINT" "$LINT_FX/bad-runner.md" 2>&1)
assert_contains "$_run_err" "runner" "lint: invalid runner value reported"
