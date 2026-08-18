#!/bin/sh
# check-inbox-triaged_test.sh — TDD proofs for check-inbox-triaged.sh (V1 F2):
# the zero-PROPOSED phase-exit leg (Step 2.txt journey phase-exit law) made
# into a single executable gate a phase-exit citation can name.
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
GATE="$TESTS_DIR/../bin/check-inbox-triaged.sh"
FX="$TESTS_DIR/fixtures/inbox/triage"
LINTFX="$TESTS_DIR/fixtures/inbox/lint"

# ── usage: wrong argc -> exit 2 ─────────────────────────────────────────────
assert_exit 2 sh "$GATE"
assert_exit 2 sh "$GATE" a b

# ── SKIP: no inbox file — documented N/A, not a vacuous pass (Step 2 law:
# "no inbox file means no inbox condition — the inbox is created by the
# first simulator pass, never generated at Step 2"). ────────────────────────
_out="$(sh "$GATE" "$FX/does-not-exist.md" 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "no inbox file -> exit 0"
assert_contains "$_out" "SKIP: no inbox file — condition not applicable (inbox is created by the first simulator pass)" \
  "no inbox file -> explicit SKIP line, not a silent pass"

# ── lint composition: a schema-broken inbox fails via LINT_FAILED
# pass-through — the composed lint-journey-inbox.sh diagnostic prints first,
# then this gate's own wrapper line (never re-implemented). ────────────────
_out="$(sh "$GATE" "$LINTFX/bad-header.md" 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "broken inbox -> exit 1"
assert_contains "$_out" "BAD_HEADER" "broken inbox: underlying lint diagnostic passes through"
assert_contains "$_out" "LINT_FAILED: inbox failed lint-journey-inbox.sh" "broken inbox -> LINT_FAILED wrapper"

# ── zero PROPOSED entries -> exit 0, one-line summary ───────────────────────
_out="$(sh "$GATE" "$FX/JOURNEY_INBOX.check-triaged-clean.md" 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "zero PROPOSED entries -> exit 0"
assert_contains "$_out" "OK: zero PROPOSED entries" "zero PROPOSED entries -> one-line summary"
assert_not_contains "$_out" "INBOX_UNTRIAGED" "zero PROPOSED entries -> no INBOX_UNTRIAGED lines"

# ── any PROPOSED entries -> INBOX_UNTRIAGED per entry (fail-slow accumulate,
# house rule 2 — never `| while read`), exit 1. Fixture has PROPOSED at
# INBOX-1 AND INBOX-3 either side of an ACCEPTED INBOX-2, so both must be
# named — proving the loop doesn't stop at the first. ──────────────────────
_out="$(sh "$GATE" "$FX/JOURNEY_INBOX.check-triaged-untriaged.md" 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "PROPOSED entries remain -> exit 1"
assert_contains "$_out" "INBOX_UNTRIAGED: INBOX-1" "PROPOSED entry INBOX-1 named"
assert_contains "$_out" "INBOX_UNTRIAGED: INBOX-3" "PROPOSED entry INBOX-3 named (fail-slow: both accumulate, not fail-fast on the first)"
assert_not_contains "$_out" "INBOX_UNTRIAGED: INBOX-2" "ACCEPTED entry INBOX-2 is NOT flagged"
