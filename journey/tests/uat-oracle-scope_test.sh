#!/bin/sh
# shellcheck shell=sh
# uat-oracle-scope_test.sh — oracle observability classes (spec G4): the
# false-gap killer. Three coordinated pieces under one test file:
#   1. lint-journey-map.sh Check 9 — optional `oracle_classes:` grammar
#      (ORACLE_CLASS_UNKNOWN / ORACLE_CLASS_COUNT_MISMATCH), committed
#      fixtures under fixtures/lint/.
#   2. lint-uat-report.sh — optional `- oracle_clause:` claim-line FORMAT
#      check (ORACLE_CLAUSE_FORMAT); zero-behavior-change proof on a
#      ref-free report.
#   3. check-uat-oracle-scope.sh — the standalone gate that rejects a
#      browser-UAT `[C-absent]` claim citing a `lower`-classed oracle
#      clause as a gap.
# Model: surface-staleness_test.sh (mktemp-dir fixture-build idiom) +
# uat-preconditions_test.sh (gate arg/exit proof style). Unique prefix: _uos_.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LINT="$TESTS_DIR/../bin/lint-journey-map.sh"
UATLINT="$TESTS_DIR/../bin/lint-uat-report.sh"
GATE="$TESTS_DIR/../bin/check-uat-oracle-scope.sh"
LINT_FX="$TESTS_DIR/fixtures/lint"
UAT_GOLDEN="$TESTS_DIR/fixtures/uat/golden/UAT_REPORT_2026-07-08.md"

_uos_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

# ─────────────────────────────────────────────────────────────────────────
# 1. lint-journey-map.sh Check 9 — committed fixtures
# ─────────────────────────────────────────────────────────────────────────
assert_exit 0 sh "$LINT" "$LINT_FX/oracle-classes-good.md"

assert_exit 1 sh "$LINT" "$LINT_FX/oracle-classes-bad-token.md"
_uos_bt="$(sh "$LINT" "$LINT_FX/oracle-classes-bad-token.md" 2>&1)"
assert_contains "$_uos_bt" "ORACLE_CLASS_UNKNOWN" "Check 9: bad token reports ORACLE_CLASS_UNKNOWN"

assert_exit 1 sh "$LINT" "$LINT_FX/oracle-classes-count.md"
_uos_ct="$(sh "$LINT" "$LINT_FX/oracle-classes-count.md" 2>&1)"
assert_contains "$_uos_ct" "ORACLE_CLASS_COUNT_MISMATCH" "Check 9: count mismatch reports ORACLE_CLASS_COUNT_MISMATCH"

# Regression lock: oracle_classes stays OPTIONAL — a map that never
# mentions it still lints clean.
assert_exit 0 sh "$LINT" "$TESTS_DIR/fixtures/good/JOURNEY_MAP.md"

# ─────────────────────────────────────────────────────────────────────────
# 2. lint-uat-report.sh — optional `- oracle_clause:` claim line
# ─────────────────────────────────────────────────────────────────────────
# A ref-free report behaves EXACTLY as before this field existed.
assert_exit 0 sh "$UATLINT" "$UAT_GOLDEN"

_uos_lt="$(mktemp -d)"
cat > "$_uos_lt/UAT_REPORT_2026-07-08.md" <<'EOF'
# UAT-REPORT
report_date: 2026-07-08
repo_commit: 0123456789012345678901234567890123456789
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: Hash check confirmed present in code
- journey_ids: JOURNEY-101
- grade: [C]
- claim: The app computes and compares the invoice hash to the source manifest.
- evidence: src/invoices/hash.ts:9 — "if (hash !== manifest.hash) throw"
- oracle_clause: JOURNEY-101-BAD
EOF
_uos_lt_out="$(sh "$UATLINT" "$_uos_lt/UAT_REPORT_2026-07-08.md" 2>&1)"; _uos_lt_rc=$?
assert_eq "1" "$_uos_lt_rc" "lint-uat-report: malformed oracle_clause ref exits 1"
assert_contains "$_uos_lt_out" "ORACLE_CLAUSE_FORMAT" "lint-uat-report: malformed oracle_clause ref reports ORACLE_CLAUSE_FORMAT"
assert_contains "$_uos_lt_out" "JOURNEY-101-BAD" "lint-uat-report: ORACLE_CLAUSE_FORMAT names the offending ref"

# Well-formed ref: lint stays green — this gate only checks FORMAT, not
# journey/index/class adjudication (that's check-uat-oracle-scope.sh's job).
cat > "$_uos_lt/UAT_REPORT_2026-07-08.md" <<'EOF'
# UAT-REPORT
report_date: 2026-07-08
repo_commit: 0123456789012345678901234567890123456789
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: Hash check confirmed present in code
- journey_ids: JOURNEY-101
- grade: [C]
- claim: The app computes and compares the invoice hash to the source manifest.
- evidence: src/invoices/hash.ts:9 — "if (hash !== manifest.hash) throw"
- oracle_clause: JOURNEY-101#1
EOF
assert_exit 0 sh "$UATLINT" "$_uos_lt/UAT_REPORT_2026-07-08.md"

rm -rf "$_uos_lt"

# ─────────────────────────────────────────────────────────────────────────
# 3. check-uat-oracle-scope.sh — the false-gap killer gate
# ─────────────────────────────────────────────────────────────────────────
_uos_t="$(mktemp -d)"

# Archetype map: JOURNEY-101 oracle has 2 clauses — clause 1 (hash
# integrity) is verified BELOW the UI (unit test coverage), clause 2 (row
# visibility) is adjudicable from the browser.
cat > "$_uos_t/JOURNEY_MAP_full.md" <<'EOF'
# JOURNEY_MAP — oracle-scope archetype (with oracle_classes declared)

## JOURNEY-101 — "Invoice hash integrity visible in list"
origin:          PERSONA
persona:         P2 (impatient ops user)
goal:            confirm an uploaded invoice's hash matches the source manifest and the row is visible
priority:        P0
covers:          FEAT-101
flows:           AF-3
oracle_surface:  UI+API
negative_states: schema_error
data_fixtures:
steps:
  1. land on /invoices            (state: AUTHENTICATED, EMPTY list)
  2. upload corrected.csv          → inject schema_error
  3. observe row appear in /invoices
oracle:          invoice hash matches source manifest AND row visible in /invoices
oracle_classes:  lower AND browser
evidence:        []
test:            tests/journeys/journey-101.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
EOF

# Same journey, no oracle_classes declared at all — for ORACLE_CLASS_UNDECLARED.
cat > "$_uos_t/JOURNEY_MAP_noclasses.md" <<'EOF'
# JOURNEY_MAP — oracle-scope archetype (no oracle_classes declared)

## JOURNEY-101 — "Invoice hash integrity visible in list"
origin:          PERSONA
persona:         P2 (impatient ops user)
goal:            confirm an uploaded invoice's hash matches the source manifest and the row is visible
priority:        P0
covers:          FEAT-101
flows:           AF-3
oracle_surface:  UI+API
negative_states: schema_error
data_fixtures:
steps:
  1. land on /invoices            (state: AUTHENTICATED, EMPTY list)
  2. upload corrected.csv          → inject schema_error
  3. observe row appear in /invoices
oracle:          invoice hash matches source manifest AND row visible in /invoices
evidence:        []
test:            tests/journeys/journey-101.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
EOF

# Both archetype maps must themselves be lint-clean (Check 9 grammar-valid) —
# this gate composes lint-journey-map.sh and trusts a lint-clean map.
assert_exit 0 sh "$LINT" "$_uos_t/JOURNEY_MAP_full.md"
assert_exit 0 sh "$LINT" "$_uos_t/JOURNEY_MAP_noclasses.md"

# ── 3.0: wrong arg count → usage, exit 2 ──────────────────────────────────
assert_exit 2 sh "$GATE"
assert_exit 2 sh "$GATE" "$_uos_t/JOURNEY_MAP_full.md"
assert_exit 2 sh "$GATE" a b c

# ── 3.0b: missing input file → exit 2 ─────────────────────────────────────
assert_exit 2 sh "$GATE" "$_uos_t/does-not-exist-report.md" "$_uos_t/JOURNEY_MAP_full.md"
assert_exit 2 sh "$GATE" "$_uos_t/JOURNEY_MAP_full.md" "$_uos_t/does-not-exist-map.md"

# ── 3.1: NO_CLAUSE_REFS — zero oracle_clause lines anywhere ───────────────
cat > "$_uos_t/report_none.md" <<'EOF'
# UAT-REPORT
report_date: 2026-07-10
repo_commit: 0123456789012345678901234567890123456789
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: Invoice hash verification is missing
- journey_ids: JOURNEY-101
- grade: [C-absent]
- claim: The app never confirms an uploaded invoice's hash matches the source manifest.
- search: grep -rFn -- "hash matches source manifest" src/
EOF
_uos_o="$(sh "$GATE" "$_uos_t/report_none.md" "$_uos_t/JOURNEY_MAP_full.md" 2>&1)"; _uos_ec=$?
_uos_nonzero "$_uos_ec" "gate: zero oracle_clause refs fails"
assert_contains "$_uos_o" "NO_CLAUSE_REFS" "gate: zero oracle_clause refs reports NO_CLAUSE_REFS"

# This IS the RED-PROOF false gap (the field-run motivation): the exact
# same claim content, under the filename convention lint-uat-report.sh
# requires, sails through that gate with exit 0 — nothing below the browser
# classifies the claim as out of scope until check-uat-oracle-scope.sh (3.6
# below) is invoked.
cp "$_uos_t/report_none.md" "$_uos_t/UAT_REPORT_2026-07-10.md"
assert_exit 0 sh "$UATLINT" "$_uos_t/UAT_REPORT_2026-07-10.md"

# ── 3.2: ORACLE_CLAUSE_FORMAT — malformed ref ─────────────────────────────
cat > "$_uos_t/report_badformat.md" <<'EOF'
# UAT-REPORT
report_date: 2026-07-10
repo_commit: 0123456789012345678901234567890123456789
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: bad ref
- journey_ids: JOURNEY-101
- grade: [C]
- claim: x
- evidence: src/x.ts:1 — "x"
- oracle_clause: JOURNEY-101-1
EOF
_uos_o="$(sh "$GATE" "$_uos_t/report_badformat.md" "$_uos_t/JOURNEY_MAP_full.md" 2>&1)"; _uos_ec=$?
_uos_nonzero "$_uos_ec" "gate: malformed ref fails"
assert_contains "$_uos_o" "ORACLE_CLAUSE_FORMAT: UAT-CLAIM-1: JOURNEY-101-1" "gate: malformed ref reports ORACLE_CLAUSE_FORMAT with id+ref"

# ── 3.3: ORACLE_CLAUSE_UNKNOWN_JOURNEY — journey id absent from the map ───
cat > "$_uos_t/report_unknown.md" <<'EOF'
# UAT-REPORT
report_date: 2026-07-10
repo_commit: 0123456789012345678901234567890123456789
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: unknown journey
- journey_ids: JOURNEY-999
- grade: [C]
- claim: x
- evidence: src/x.ts:1 — "x"
- oracle_clause: JOURNEY-999#1
EOF
_uos_o="$(sh "$GATE" "$_uos_t/report_unknown.md" "$_uos_t/JOURNEY_MAP_full.md" 2>&1)"; _uos_ec=$?
_uos_nonzero "$_uos_ec" "gate: unknown journey id fails"
assert_contains "$_uos_o" "ORACLE_CLAUSE_UNKNOWN_JOURNEY: UAT-CLAIM-1: JOURNEY-999" "gate: unknown journey id reports ORACLE_CLAUSE_UNKNOWN_JOURNEY"

# ── 3.4: ORACLE_CLAUSE_OUT_OF_RANGE — index beyond the oracle's clause count
cat > "$_uos_t/report_outofrange.md" <<'EOF'
# UAT-REPORT
report_date: 2026-07-10
repo_commit: 0123456789012345678901234567890123456789
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: index too high
- journey_ids: JOURNEY-101
- grade: [C]
- claim: x
- evidence: src/x.ts:1 — "x"
- oracle_clause: JOURNEY-101#3
EOF
_uos_o="$(sh "$GATE" "$_uos_t/report_outofrange.md" "$_uos_t/JOURNEY_MAP_full.md" 2>&1)"; _uos_ec=$?
_uos_nonzero "$_uos_ec" "gate: out-of-range index fails"
assert_contains "$_uos_o" "ORACLE_CLAUSE_OUT_OF_RANGE: UAT-CLAIM-1: JOURNEY-101#3" "gate: out-of-range index reports ORACLE_CLAUSE_OUT_OF_RANGE"

# ── 3.5: ORACLE_CLASS_UNDECLARED — journey has no oracle_classes: at all ──
cat > "$_uos_t/report_undeclared.md" <<'EOF'
# UAT-REPORT
report_date: 2026-07-10
repo_commit: 0123456789012345678901234567890123456789
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: Invoice hash verification is missing
- journey_ids: JOURNEY-101
- grade: [C-absent]
- claim: The app never confirms an uploaded invoice's hash matches the source manifest.
- search: grep -rFn -- "hash matches source manifest" src/
- oracle_clause: JOURNEY-101#1
EOF
_uos_o="$(sh "$GATE" "$_uos_t/report_undeclared.md" "$_uos_t/JOURNEY_MAP_noclasses.md" 2>&1)"; _uos_ec=$?
_uos_nonzero "$_uos_ec" "gate: undeclared oracle_classes fails (fail closed)"
assert_contains "$_uos_o" "ORACLE_CLASS_UNDECLARED: UAT-CLAIM-1: JOURNEY-101" "gate: undeclared oracle_classes reports ORACLE_CLASS_UNDECLARED"

# ── 3.6: ORACLE_CLASS_OUT_OF_SCOPE — the archetype, the false-gap killer ──
# Same report as 3.5's ref (JOURNEY-101#1, the lower-classed hash clause)
# but against the FULL map (oracle_classes declared) — a [C-absent] claim
# asserting a below-the-UI clause as a browser gap.
_uos_o="$(sh "$GATE" "$_uos_t/report_undeclared.md" "$_uos_t/JOURNEY_MAP_full.md" 2>&1)"; _uos_ec=$?
_uos_nonzero "$_uos_ec" "gate: [C-absent] against a lower clause fails (the false-gap killer)"
assert_contains "$_uos_o" "ORACLE_CLASS_OUT_OF_SCOPE: UAT-CLAIM-1: JOURNEY-101#1" "gate: reports ORACLE_CLASS_OUT_OF_SCOPE"
assert_contains "$_uos_o" "lower-level clause" "gate: ORACLE_CLASS_OUT_OF_SCOPE message explains why"

# ── 3.7: [C-absent] + browser clause → exit 0 (a genuine browser gap) ─────
cat > "$_uos_t/report_browserabsent.md" <<'EOF'
# UAT-REPORT
report_date: 2026-07-10
repo_commit: 0123456789012345678901234567890123456789
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: Row visibility is missing
- journey_ids: JOURNEY-101
- grade: [C-absent]
- claim: The uploaded row never appears in /invoices.
- search: grep -rFn -- "row visible in" src/
- oracle_clause: JOURNEY-101#2
EOF
assert_exit 0 sh "$GATE" "$_uos_t/report_browserabsent.md" "$_uos_t/JOURNEY_MAP_full.md"

# ── 3.8: [C] + lower clause → exit 0 (positive evidence, not an absence) ──
cat > "$_uos_t/report_clower.md" <<'EOF'
# UAT-REPORT
report_date: 2026-07-10
repo_commit: 0123456789012345678901234567890123456789
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: Hash check confirmed present in code
- journey_ids: JOURNEY-101
- grade: [C]
- claim: The app computes and compares the invoice hash to the source manifest.
- evidence: src/invoices/hash.ts:9 — "if (hash !== manifest.hash) throw"
- oracle_clause: JOURNEY-101#1
EOF
assert_exit 0 sh "$GATE" "$_uos_t/report_clower.md" "$_uos_t/JOURNEY_MAP_full.md"

# ── 3.9: LINT_FAILED — composes lint-journey-map.sh first, reuses an ──────
#    existing lint-red fixture (not forked) ────────────────────────────────
_uos_o="$(sh "$GATE" "$_uos_t/report_clower.md" "$LINT_FX/bad-enum.md" 2>&1)"; _uos_ec=$?
_uos_nonzero "$_uos_ec" "gate: lint-failing map fails"
assert_contains "$_uos_o" "LINT_FAILED" "gate: lint-failing map reports LINT_FAILED"

# ── 3.10: fail-slow accumulation — two distinct violations in one report,
#    both reported (not fail-fast on the first) ───────────────────────────
cat > "$_uos_t/report_multi.md" <<'EOF'
# UAT-REPORT
report_date: 2026-07-10
repo_commit: 0123456789012345678901234567890123456789
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: bad ref
- journey_ids: JOURNEY-101
- grade: [C]
- claim: x
- evidence: src/x.ts:1 — "x"
- oracle_clause: JOURNEY-101-1

## UAT-CLAIM-2: unknown journey
- journey_ids: JOURNEY-999
- grade: [C]
- claim: y
- evidence: src/y.ts:1 — "y"
- oracle_clause: JOURNEY-999#1
EOF
_uos_o="$(sh "$GATE" "$_uos_t/report_multi.md" "$_uos_t/JOURNEY_MAP_full.md" 2>&1)"; _uos_ec=$?
_uos_nonzero "$_uos_ec" "gate: multi-violation report fails"
assert_contains "$_uos_o" "ORACLE_CLAUSE_FORMAT: UAT-CLAIM-1" "gate: fail-slow — first violation present"
assert_contains "$_uos_o" "ORACLE_CLAUSE_UNKNOWN_JOURNEY: UAT-CLAIM-2" "gate: fail-slow — second violation ALSO present (not fail-fast)"

rm -rf "$_uos_t"
