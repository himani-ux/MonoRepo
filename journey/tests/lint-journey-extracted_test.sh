#!/bin/sh
# lint-journey-extracted_test.sh — TDD proofs for lint-journey-extracted.sh (E1)
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LINT="$TESTS_DIR/../bin/lint-journey-extracted.sh"
GOOD="$TESTS_DIR/fixtures/extracted/good/JOURNEY_EXTRACTED.golden.md"
FX="$TESTS_DIR/fixtures/extracted/lint"

# ── Positive: valid staging file passes ────────────────────────────────────
assert_exit 0 sh "$LINT" "$GOOD"
_good_out="$(sh "$LINT" "$GOOD" 2>&1)"
assert_eq "" "$_good_out" "golden staging file: zero diagnostics on a clean pass"

# ── Usage / missing-file: exit 2 (matches lint-journey-map.sh / -inbox.sh) ─
assert_exit 2 sh "$LINT"
assert_exit 2 sh "$LINT" a b
assert_exit 2 sh "$LINT" "$FX/does-not-exist.md"

# ── File-level checks ───────────────────────────────────────────────────────

assert_exit 1 sh "$LINT" "$FX/bad-header.md"
_out="$(sh "$LINT" "$FX/bad-header.md" 2>&1)"
assert_contains "$_out" "BAD_HEADER" "bad first line -> BAD_HEADER"

assert_exit 1 sh "$LINT" "$FX/extraction-commit-invalid.md"
_out="$(sh "$LINT" "$FX/extraction-commit-invalid.md" 2>&1)"
assert_contains "$_out" "EXTRACTION_COMMIT_INVALID" "39-char extraction_commit -> EXTRACTION_COMMIT_INVALID"

assert_exit 1 sh "$LINT" "$FX/manifest-sha-invalid.md"
_out="$(sh "$LINT" "$FX/manifest-sha-invalid.md" 2>&1)"
assert_contains "$_out" "MANIFEST_SHA_INVALID" "uppercase-hex manifest_sha256 -> MANIFEST_SHA_INVALID"

assert_exit 1 sh "$LINT" "$FX/forbidden-journey-header.md"
_out="$(sh "$LINT" "$FX/forbidden-journey-header.md" 2>&1)"
assert_contains "$_out" "FORBIDDEN_JOURNEY_HEADER" "smuggled '## JOURNEY-' -> FORBIDDEN_JOURNEY_HEADER"

assert_exit 1 sh "$LINT" "$FX/runtime-field.md"
_out="$(sh "$LINT" "$FX/runtime-field.md" 2>&1)"
assert_contains "$_out" "RUNTIME_FIELD" "runtime-truth key -> RUNTIME_FIELD (same five-key list as check-journey-authority.sh)"

assert_exit 1 sh "$LINT" "$FX/duplicate-id.md"
_out="$(sh "$LINT" "$FX/duplicate-id.md" 2>&1)"
assert_contains "$_out" "DUPLICATE_EXTRACTED_ID" "repeated EXTRACTED-<n> id -> DUPLICATE_EXTRACTED_ID"

assert_exit 1 sh "$LINT" "$FX/bad-extracted-id.md"
_out="$(sh "$LINT" "$FX/bad-extracted-id.md" 2>&1)"
assert_contains "$_out" "BAD_EXTRACTED_ID" "EXTRACTED-0 -> BAD_EXTRACTED_ID (positive-integer ids)"

assert_exit 1 sh "$LINT" "$FX/no-entries.md"
_out="$(sh "$LINT" "$FX/no-entries.md" 2>&1)"
assert_contains "$_out" "NO_EXTRACTED_ENTRIES" "valid header + zero entries -> NO_EXTRACTED_ENTRIES (anti-vacuous)"
# anti-vacuous tested both ways: the golden fixture HAS entries and must
# never trip this code.
assert_not_contains "$_good_out" "NO_EXTRACTED_ENTRIES" "golden staging file (non-zero entries) never trips NO_EXTRACTED_ENTRIES"

# ── Per-entry checks ─────────────────────────────────────────────────────────

assert_exit 1 sh "$LINT" "$FX/entry-heading-invalid.md"
_out="$(sh "$LINT" "$FX/entry-heading-invalid.md" 2>&1)"
assert_contains "$_out" "ENTRY_HEADING_INVALID: EXTRACTED-1" "glued em-dash heading -> ENTRY_HEADING_INVALID (checked up front, L23)"

assert_exit 1 sh "$LINT" "$FX/needs-confirm-invalid.md"
_out="$(sh "$LINT" "$FX/needs-confirm-invalid.md" 2>&1)"
assert_contains "$_out" "NEEDS_CONFIRM_INVALID: EXTRACTED-1" "needs_human_confirm: false -> NEEDS_CONFIRM_INVALID (I2)"

assert_exit 1 sh "$LINT" "$FX/confirm-status-invalid.md"
_out="$(sh "$LINT" "$FX/confirm-status-invalid.md" 2>&1)"
assert_contains "$_out" "CONFIRM_STATUS_INVALID: EXTRACTED-1: MAYBE" "confirmation_status outside the enum -> CONFIRM_STATUS_INVALID"

assert_exit 1 sh "$LINT" "$FX/rejected-reason-missing.md"
_out="$(sh "$LINT" "$FX/rejected-reason-missing.md" 2>&1)"
assert_contains "$_out" "REJECTED_REASON_MISSING: EXTRACTED-1" "REJECTED with no rejected_reason -> REJECTED_REASON_MISSING"
# positive: the golden staging file's REJECTED entry (EXTRACTED-4) carries a
# reason and must never trip this code.
assert_not_contains "$_good_out" "REJECTED_REASON_MISSING" "golden REJECTED entry (has a reason) never trips REJECTED_REASON_MISSING"

assert_exit 1 sh "$LINT" "$FX/grade-unknown.md"
_out="$(sh "$LINT" "$FX/grade-unknown.md" 2>&1)"
assert_contains "$_out" "GRADE_UNKNOWN: EXTRACTED-1: [Z]" "grade outside {[C],[I],[G],[X]} -> GRADE_UNKNOWN"

assert_exit 1 sh "$LINT" "$FX/missing-field.md"
_out="$(sh "$LINT" "$FX/missing-field.md" 2>&1)"
assert_contains "$_out" "MISSING_FIELD: EXTRACTED-1: covers" "a required field key absent -> MISSING_FIELD"

assert_exit 1 sh "$LINT" "$FX/blank-field.md"
_out="$(sh "$LINT" "$FX/blank-field.md" 2>&1)"
assert_contains "$_out" "BLANK_FIELD: EXTRACTED-1: covers" "a required-nonempty field with a blank value -> BLANK_FIELD"
assert_not_contains "$_out" "MISSING_FIELD: EXTRACTED-1: covers" "blank (present) field does NOT also emit MISSING_FIELD noise"

assert_exit 1 sh "$LINT" "$FX/bad-origin.md"
_out="$(sh "$LINT" "$FX/bad-origin.md" 2>&1)"
assert_contains "$_out" "BAD_ORIGIN: EXTRACTED-1: PERSONA" "origin other than EXTRACTED -> BAD_ORIGIN"

assert_exit 1 sh "$LINT" "$FX/bad-author-status.md"
_out="$(sh "$LINT" "$FX/bad-author-status.md" 2>&1)"
assert_contains "$_out" "BAD_AUTHOR_STATUS: EXTRACTED-1: WRITTEN" "author_status other than UNWRITTEN -> BAD_AUTHOR_STATUS"

assert_exit 1 sh "$LINT" "$FX/sources-missing.md"
_out="$(sh "$LINT" "$FX/sources-missing.md" 2>&1)"
assert_contains "$_out" "SOURCES_MISSING: EXTRACTED-1" "zero extraction_sources lines -> SOURCES_MISSING (>=1 always)"

assert_exit 1 sh "$LINT" "$FX/source-format.md"
_out="$(sh "$LINT" "$FX/source-format.md" 2>&1)"
assert_contains "$_out" "SOURCE_FORMAT: EXTRACTED-1" "malformed extraction_sources line -> SOURCE_FORMAT"

# ── DX-1: search-cite (absence-evidence) grammar ────────────────────────────
# Positive: the golden fixture's EXTRACTED-6 carries a well-formed
# search-cite (`- search: grep -rFn -- "rateLimit" src`) and the whole file
# is already asserted zero-diagnostics above ($_good_out) — no separate
# positive fixture needed; asserted explicitly here too for locality.
assert_not_contains "$_good_out" "SOURCE_FORMAT" "golden EXTRACTED-6 search-cite (well-formed) never trips SOURCE_FORMAT"
assert_contains "$(cat "$GOOD")" '- search: grep -rFn -- "rateLimit" src' \
  "golden fixture carries a real search-cite line (DX-1 positive proof)"

assert_exit 1 sh "$LINT" "$FX/search-cite-format.md"
_out="$(sh "$LINT" "$FX/search-cite-format.md" 2>&1)"
assert_contains "$_out" "SOURCE_FORMAT: EXTRACTED-1" "malformed search-cite (missing -rFn --) -> SOURCE_FORMAT (DX-1)"

# ── DX-5: hybrid section-cite/line-cite paste — RED with the REAL
# attempt-2 live-characterization output line (a model glued a quote onto
# a `#heading` section-cite: `docs/FLW.md#Booking — "A member books an
# open class from the class detail screen."`). Formally it still matched
# the section-cite grammar (`[^#]+` accepts a literal '"'), silently
# "validating" into a heading string that could never match a real ATX
# heading — a confusing downstream SECTION_HEADING_MISSING instead of a
# clear grammar error. Caught here instead, with an actionable message.
assert_exit 1 sh "$LINT" "$FX/hybrid-section-cite.md"
_out="$(sh "$LINT" "$FX/hybrid-section-cite.md" 2>&1)"
assert_contains "$_out" "SOURCE_FORMAT: EXTRACTED-1" "hybrid section-cite (heading contains a quote) -> SOURCE_FORMAT (DX-5)"
assert_contains "$_out" "looks like a hybrid cite — use a line-cite" "hybrid section-cite: actionable message names the fix"

assert_exit 1 sh "$LINT" "$FX/x-one-sided.md"
_out="$(sh "$LINT" "$FX/x-one-sided.md" 2>&1)"
assert_contains "$_out" "X_ONE_SIDED: EXTRACTED-1" "grade [X] with only 1 source -> X_ONE_SIDED (distinct from SOURCES_MISSING)"
assert_not_contains "$_out" "SOURCES_MISSING" "grade [X] one-sided is X_ONE_SIDED, not also SOURCES_MISSING"

assert_exit 1 sh "$LINT" "$FX/oracle-exactly-one.md"
_out="$(sh "$LINT" "$FX/oracle-exactly-one.md" 2>&1)"
assert_contains "$_out" "ORACLE_EXACTLY_ONE: EXTRACTED-1" "both oracle: and oracle_gap: present -> ORACLE_EXACTLY_ONE"

assert_exit 1 sh "$LINT" "$FX/oracle-gap-format.md"
_out="$(sh "$LINT" "$FX/oracle-gap-format.md" 2>&1)"
assert_contains "$_out" "ORACLE_GAP_FORMAT: EXTRACTED-1" "blank oracle_gap: value -> ORACLE_GAP_FORMAT"

# ── promoted_as: grammar (OPTIONAL field, CONFIRMED-only) ──────────────────

assert_exit 1 sh "$LINT" "$FX/promoted-as-invalid.md"
_out="$(sh "$LINT" "$FX/promoted-as-invalid.md" 2>&1)"
assert_contains "$_out" "PROMOTED_AS_INVALID: EXTRACTED-1: not-a-journey-id" "promoted_as value not matching JOURNEY-<n> -> PROMOTED_AS_INVALID"

assert_exit 1 sh "$LINT" "$FX/promoted-as-not-confirmed.md"
_out="$(sh "$LINT" "$FX/promoted-as-not-confirmed.md" 2>&1)"
assert_contains "$_out" "PROMOTED_AS_INVALID: EXTRACTED-1: promoted_as present but confirmation_status is PENDING" "promoted_as on a non-CONFIRMED entry -> PROMOTED_AS_INVALID"

assert_exit 0 sh "$LINT" "$FX/promoted-as-ok.md"
_out="$(sh "$LINT" "$FX/promoted-as-ok.md" 2>&1)"
assert_eq "" "$_out" "well-formed promoted_as on a CONFIRMED entry -> zero diagnostics"

assert_exit 1 sh "$LINT" "$FX/prior-e2e-format.md"
_out="$(sh "$LINT" "$FX/prior-e2e-format.md" 2>&1)"
assert_contains "$_out" "PRIOR_E2E_FORMAT: EXTRACTED-1: /etc/passwd" "absolute prior_e2e path -> PRIOR_E2E_FORMAT"

assert_exit 1 sh "$LINT" "$FX/resolved-from-missing.md"
_out="$(sh "$LINT" "$FX/resolved-from-missing.md" 2>&1)"
assert_contains "$_out" "RESOLVED_FROM_MISSING: EXTRACTED-1" "resolution: without resolved_from: -> RESOLVED_FROM_MISSING (locks 2/3)"
# positive: the golden staging file's resolved entry (EXTRACTED-5) carries
# both resolution: and resolved_from: with >=2 sources and must never trip
# this code or SOURCES_MISSING.
assert_not_contains "$_good_out" "RESOLVED_FROM_MISSING" "golden resolved entry (resolution+resolved_from+2 sources) never trips RESOLVED_FROM_MISSING"
assert_not_contains "$_good_out" "SOURCES_MISSING" "golden resolved entry retains >=2 sources, never trips SOURCES_MISSING"
assert_not_contains "$_good_out" "X_ONE_SIDED" "golden [X] entry (EXTRACTED-2) carries 2 sources, never trips X_ONE_SIDED"
assert_not_contains "$_good_out" "ORACLE_EXACTLY_ONE" "golden entries each carry exactly one of oracle:/oracle_gap:, never trip ORACLE_EXACTLY_ONE"

# ── Fail-slow: multiple independent violations in one file all accumulate ──
# (house rule 2 — for/heredoc-while, never `| while read`; this proves the
# accumulator actually survives to the final exit, not just the first hit).
assert_exit 1 sh "$LINT" "$FX/multi-violation.md"
_multi_out="$(sh "$LINT" "$FX/multi-violation.md" 2>&1)"
assert_contains "$_multi_out" "BAD_ORIGIN" "fail-slow: first independent violation present"
assert_contains "$_multi_out" "BAD_AUTHOR_STATUS" "fail-slow: second independent violation present in the SAME run"
