#!/bin/sh
# lint-journey-inbox_test.sh — TDD proofs for lint-journey-inbox.sh (DC-1)
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LINT="$TESTS_DIR/../bin/lint-journey-inbox.sh"
GOOD="$TESTS_DIR/fixtures/inbox/good/JOURNEY_INBOX.golden.md"
FX="$TESTS_DIR/fixtures/inbox/lint"

# ── Positive: valid inbox passes ──────────────────────────────────────────
assert_exit 0 sh "$LINT" "$GOOD"
_good_out="$(sh "$LINT" "$GOOD" 2>&1)"
assert_eq "" "$_good_out" "golden inbox: zero diagnostics on a clean pass"

# ── Usage / missing-file: exit 2 (matches lint-journey-map.sh) ───────────
assert_exit 2 sh "$LINT"
assert_exit 2 sh "$LINT" a b
assert_exit 2 sh "$LINT" "$FX/does-not-exist.md"

# ── File-level checks ──────────────────────────────────────────────────────

assert_exit 1 sh "$LINT" "$FX/bad-header.md"
_out="$(sh "$LINT" "$FX/bad-header.md" 2>&1)"
assert_contains "$_out" "BAD_HEADER" "bad first line -> BAD_HEADER"

assert_exit 1 sh "$LINT" "$FX/forbidden-journey-header.md"
_out="$(sh "$LINT" "$FX/forbidden-journey-header.md" 2>&1)"
assert_contains "$_out" "FORBIDDEN_JOURNEY_HEADER" "smuggled '## JOURNEY-' -> FORBIDDEN_JOURNEY_HEADER"

assert_exit 1 sh "$LINT" "$FX/runtime-field.md"
_out="$(sh "$LINT" "$FX/runtime-field.md" 2>&1)"
assert_contains "$_out" "RUNTIME_FIELD" "runtime-truth key -> RUNTIME_FIELD (same code name as journey-gen-check-candidate.sh)"

assert_exit 1 sh "$LINT" "$FX/duplicate-id.md"
_out="$(sh "$LINT" "$FX/duplicate-id.md" 2>&1)"
assert_contains "$_out" "DUPLICATE_INBOX_ID" "repeated INBOX-<n> id -> DUPLICATE_INBOX_ID"

assert_exit 1 sh "$LINT" "$FX/bad-inbox-id.md"
_out="$(sh "$LINT" "$FX/bad-inbox-id.md" 2>&1)"
assert_contains "$_out" "BAD_INBOX_ID" "INBOX-0 -> BAD_INBOX_ID (positive-integer ids)"

assert_exit 1 sh "$LINT" "$FX/no-entries.md"
_out="$(sh "$LINT" "$FX/no-entries.md" 2>&1)"
assert_contains "$_out" "NO_INBOX_ENTRIES" "valid header + zero entries -> NO_INBOX_ENTRIES (anti-vacuous)"
# anti-vacuous tested both ways: the golden fixture HAS entries and must
# never trip this code.
assert_not_contains "$_good_out" "NO_INBOX_ENTRIES" "golden inbox (non-zero entries) never trips NO_INBOX_ENTRIES"

# ── Per-entry schema checks ─────────────────────────────────────────────────

assert_exit 1 sh "$LINT" "$FX/missing-field.md"
_out="$(sh "$LINT" "$FX/missing-field.md" 2>&1)"
assert_contains "$_out" "MISSING_FIELD: INBOX-1: covers" "a required field key absent -> MISSING_FIELD"

assert_exit 1 sh "$LINT" "$FX/blank-field.md"
_out="$(sh "$LINT" "$FX/blank-field.md" 2>&1)"
assert_contains "$_out" "BLANK_FIELD: INBOX-1: priority" "a required-nonempty field with a blank value -> BLANK_FIELD"
assert_not_contains "$_out" "MISSING_FIELD: INBOX-1: priority" "blank (present) field does NOT also emit MISSING_FIELD noise"

assert_exit 1 sh "$LINT" "$FX/bad-origin.md"
_out="$(sh "$LINT" "$FX/bad-origin.md" 2>&1)"
assert_contains "$_out" "BAD_ORIGIN: INBOX-1: PERSONA" "origin other than SIMULATOR -> BAD_ORIGIN (mirrors candidate checker's code name)"

assert_exit 1 sh "$LINT" "$FX/bad-author-status.md"
_out="$(sh "$LINT" "$FX/bad-author-status.md" 2>&1)"
assert_contains "$_out" "BAD_AUTHOR_STATUS: INBOX-1: WRITTEN" "author_status other than UNWRITTEN -> BAD_AUTHOR_STATUS"

assert_exit 1 sh "$LINT" "$FX/bad-promotion-status.md"
_out="$(sh "$LINT" "$FX/bad-promotion-status.md" 2>&1)"
assert_contains "$_out" "BAD_PROMOTION_STATUS: INBOX-1: MAYBE" "promotion_status outside the enum -> BAD_PROMOTION_STATUS"

assert_exit 1 sh "$LINT" "$FX/rejected-reason-missing.md"
_out="$(sh "$LINT" "$FX/rejected-reason-missing.md" 2>&1)"
assert_contains "$_out" "REJECTED_REASON_MISSING: INBOX-1" "REJECTED with no rejected_reason -> REJECTED_REASON_MISSING"
# positive: the golden inbox's REJECTED entry (INBOX-2) carries a reason and
# must never trip this code.
assert_not_contains "$_good_out" "REJECTED_REASON_MISSING" "golden REJECTED entry (has a reason) never trips REJECTED_REASON_MISSING"

# ── simulator_trace: grammar checks ─────────────────────────────────────────

assert_exit 1 sh "$LINT" "$FX/trace-missing.md"
_out="$(sh "$LINT" "$FX/trace-missing.md" 2>&1)"
assert_contains "$_out" "TRACE_MISSING: INBOX-1" "no simulator_trace: field at all -> TRACE_MISSING"
assert_not_contains "$_out" "MISSING_FIELD: INBOX-1: simulator_trace" "absent simulator_trace does NOT also emit MISSING_FIELD noise"

assert_exit 1 sh "$LINT" "$FX/trace-format.md"
_out="$(sh "$LINT" "$FX/trace-format.md" 2>&1)"
assert_contains "$_out" "TRACE_FORMAT: INBOX-1:" "malformed trace entry line -> TRACE_FORMAT"

assert_exit 1 sh "$LINT" "$FX/trace-key-unknown.md"
_out="$(sh "$LINT" "$FX/trace-key-unknown.md" 2>&1)"
assert_contains "$_out" "TRACE_KEY_UNKNOWN: INBOX-1: device_type" "trace entry with an unrecognized key -> TRACE_KEY_UNKNOWN"

assert_exit 1 sh "$LINT" "$FX/trace-field-missing.md"
_out="$(sh "$LINT" "$FX/trace-field-missing.md" 2>&1)"
assert_contains "$_out" "TRACE_FIELD_MISSING: INBOX-1: goal" "a required-once scalar key with zero occurrences -> TRACE_FIELD_MISSING"

assert_exit 1 sh "$LINT" "$FX/trace-field-duplicate.md"
_out="$(sh "$LINT" "$FX/trace-field-duplicate.md" 2>&1)"
assert_contains "$_out" "TRACE_FIELD_DUPLICATE: INBOX-1: persona" "a required-once scalar key appearing twice -> TRACE_FIELD_DUPLICATE"

assert_exit 1 sh "$LINT" "$FX/trace-token-invalid.md"
_out="$(sh "$LINT" "$FX/trace-token-invalid.md" 2>&1)"
assert_contains "$_out" "TRACE_TOKEN_INVALID: INBOX-1: persona:" "persona value containing whitespace -> TRACE_TOKEN_INVALID"

assert_exit 1 sh "$LINT" "$FX/trace-patience-budget-invalid.md"
_out="$(sh "$LINT" "$FX/trace-patience-budget-invalid.md" 2>&1)"
assert_contains "$_out" "TRACE_PATIENCE_BUDGET_INVALID: INBOX-1: 0" "patience_budget of zero -> TRACE_PATIENCE_BUDGET_INVALID (positive integer required)"

assert_exit 1 sh "$LINT" "$FX/trace-path-empty.md"
_out="$(sh "$LINT" "$FX/trace-path-empty.md" 2>&1)"
assert_contains "$_out" "TRACE_PATH_EMPTY: INBOX-1" "zero path: entries -> TRACE_PATH_EMPTY (required >= 1)"

assert_exit 1 sh "$LINT" "$FX/trace-evidence-empty.md"
_out="$(sh "$LINT" "$FX/trace-evidence-empty.md" 2>&1)"
assert_contains "$_out" "TRACE_EVIDENCE_EMPTY: INBOX-1" "zero evidence: entries -> TRACE_EVIDENCE_EMPTY (required >= 1)"

assert_exit 1 sh "$LINT" "$FX/trace-evidence-invalid.md"
_out="$(sh "$LINT" "$FX/trace-evidence-invalid.md" 2>&1)"
assert_contains "$_out" "TRACE_EVIDENCE_INVALID: INBOX-1: /etc/passwd" "absolute evidence path -> TRACE_EVIDENCE_INVALID"

# ── promoted_as: grammar (OPTIONAL field, T2 append-only extension) ────────

assert_exit 1 sh "$LINT" "$FX/promoted-as-invalid.md"
_out="$(sh "$LINT" "$FX/promoted-as-invalid.md" 2>&1)"
assert_contains "$_out" "PROMOTED_AS_INVALID: INBOX-1: not-a-journey-id" "promoted_as value not matching JOURNEY-<n> -> PROMOTED_AS_INVALID"

assert_exit 1 sh "$LINT" "$FX/promoted-as-not-accepted.md"
_out="$(sh "$LINT" "$FX/promoted-as-not-accepted.md" 2>&1)"
assert_contains "$_out" "PROMOTED_AS_INVALID: INBOX-1: promoted_as present but promotion_status is PROPOSED" "promoted_as on a non-ACCEPTED entry -> PROMOTED_AS_INVALID"

assert_exit 0 sh "$LINT" "$FX/promoted-as-ok.md"
_out="$(sh "$LINT" "$FX/promoted-as-ok.md" 2>&1)"
assert_eq "" "$_out" "well-formed promoted_as on an ACCEPTED entry -> zero diagnostics"

# ── Fail-slow: multiple independent violations in one file all accumulate ──
# (house rule 2 — for/heredoc-while, never `| while read`; this proves the
# accumulator actually survives to the final exit, not just the first hit).
assert_exit 1 sh "$LINT" "$FX/multi-violation.md"
_multi_out="$(sh "$LINT" "$FX/multi-violation.md" 2>&1)"
assert_contains "$_multi_out" "BAD_ORIGIN" "fail-slow: first independent violation present"
assert_contains "$_multi_out" "BAD_AUTHOR_STATUS" "fail-slow: second independent violation present in the SAME run"
