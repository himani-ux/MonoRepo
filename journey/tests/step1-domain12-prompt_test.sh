# shellcheck shell=sh
# step1-domain12-prompt_test.sh — Domain 12 persona contract is STATED in
# Step 1.txt (proves statement, not live-model obedience).
#
# Personas are FACTS ABOUT REAL USERS. The agent has no authority to assert
# them, so persona fields sit on the Proposal Policy's no-default list: the
# agent may DRAFT a candidate from Product/Flow evidence and show its
# derivation, but every field is user-supplied or user-edited (origin: USER).
# A persona field is never banked as an accepted default, and an unanswerable
# one is BLOCKED — a fabricated persona silently poisons every journey, every
# gap record, and the whole behavioral-truth layer downstream.
. "$(dirname "$0")/assert.sh"
TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
S1="$TESTS_DIR/../../Step 1.txt"
P="$(cat "$S1")"

assert_contains "$P" "## Domain 12: Personas & Journeys" "Domain 12 exists"

# ── Drafting is allowed; tagged acceptance is not ────────────────────────────
assert_contains "$P" "DRAFT-AND-CONFIRM" "personas are drafted, then confirmed"
assert_not_contains "$P" "PROPOSE-AND-CONFIRM" \
  "personas no longer use the propose-and-accept shortcut Domains 13/14 get"
assert_contains "$P" "persona facts are on the no-default list" \
  "Domain 12 cites the no-default list explicitly"
assert_contains "$P" "no persona field is ever banked as origin: PROPOSED" \
  "a persona field can never be an accepted default"
assert_contains "$P" "user-supplied or user-edited" \
  "every persona field is authored by the user"

# ── Unanswerable persona fields BLOCK; they are never filled ─────────────────
assert_contains "$P" "BLOCKED, never filled" \
  "an unanswerable persona field blocks rather than defaults"

# ── The captured schema still matches what lint-personas.sh parses ───────────
for _f in "goal:" "context:" "tech_savviness:" "error_tendency:" \
          "patience_budget:" "known_misbehaviors:"; do
  assert_contains "$P" "$_f" "persona schema field survives the change: $_f"
done
assert_contains "$P" "docs/PERSONAS.md" "Domain 12 feeds the canonical persona doc"
