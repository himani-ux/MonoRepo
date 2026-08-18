# shellcheck shell=sh
# persona-gates_test.sh — Increment-3 deterministic gate proofs.
# Core invariant: PERSONA journeys model USER BEHAVIOR, not tested behavior.
# Misbehavior ownership is what separates a persona journey from a happy path
# in costume.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$TESTS_DIR/../bin"
LP="$BIN/lint-personas.sh"
CPJ="$BIN/check-persona-journeys.sh"
CPC="$BIN/check-persona-coverage.sh"
PSC="$BIN/persona-selfcheck.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
PFX="$TESTS_DIR/fixtures/persona"
SSOT="$GENDIR/SSOT.md"
PMAP="$PFX/JOURNEY_MAP.persona.md"
PGAPS="$PFX/PERSONA_COVERAGE_GAPS.md"

_pg_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

_t=$(mktemp -d)

# ═══ lint-personas.sh ══════════════════════════════════════════════════════════

# ── lp-1: golden SSOT personas pass ───────────────────────────────────────────
sh "$LP" "$SSOT" >/dev/null 2>&1
assert_eq 0 $? "lp-1: golden SSOT personas pass lint"

# ── lp-2: zero personas fails ─────────────────────────────────────────────────
printf '# SSOT\n\n## System Context\nprose only\n' > "$_t/none.md"
_o=$(sh "$LP" "$_t/none.md" 2>&1); _ec=$?
_pg_nonzero "$_ec" "lp-2: SSOT without personas fails"
assert_contains "$_o" "NO_PERSONAS" "lp-2: names NO_PERSONAS"

# ── lp-3: too many personas WARNS but PASSES (owner ruling B, 2026-07-14) ─────
# The 2-5 range is advisory, not a contract: an approved RBAC role model may
# legitimately exceed it (Audit runs 8, RightShip 6) and the frozen journey maps
# cite those personas by number. The ceiling therefore informs; it does not
# block. The FLOOR (< 2) is still a hard failure — see lp-2 and
# persona-count-policy_test.sh for the full 1/2/5/6/8 matrix.
# extra personas must land INSIDE the ## Personas section (before System Context)
awk '
  /^## System Context/ {
    for (n = 3; n <= 6; n++) {
      printf "### P%d — \"Extra %d\"\ngoal:             g\ncontext:          c\ntech_savviness:   low\nerror_tendency:   low\npatience_budget:  1\nknown_misbehaviors: [none: careful]\n\n", n, n
    }
  }
  { print }
' "$SSOT" > "$_t/many.md"
_o=$(sh "$LP" "$_t/many.md" 2>&1); _ec=$?
assert_eq 0 "$_ec" "lp-3: six personas PASSES (the ceiling warns, it no longer fails)"
assert_contains "$_o" "TOO_MANY_PERSONAS" "lp-3: still names TOO_MANY_PERSONAS"
assert_contains "$_o" "WARN:" "lp-3: TOO_MANY_PERSONAS is emitted as a non-blocking warning"

# ── lp-4: duplicate persona id fails ──────────────────────────────────────────
sed 's/^### P2 — "Finance Reviewer"$/### P1 — "Finance Reviewer"/' "$SSOT" > "$_t/dup.md"
_o=$(sh "$LP" "$_t/dup.md" 2>&1); _ec=$?
_pg_nonzero "$_ec" "lp-4: duplicate persona id fails"
assert_contains "$_o" "DUPLICATE_PERSONA_ID" "lp-4: names DUPLICATE_PERSONA_ID"

# ── lp-5: missing required field fails ────────────────────────────────────────
grep -v '^context:' "$SSOT" > "$_t/nofield.md"
_o=$(sh "$LP" "$_t/nofield.md" 2>&1); _ec=$?
_pg_nonzero "$_ec" "lp-5: missing context field fails"
assert_contains "$_o" "PERSONA_FIELD_MISSING" "lp-5: names PERSONA_FIELD_MISSING"

# ── lp-6: bad enum fails ──────────────────────────────────────────────────────
sed 's/^error_tendency:   high$/error_tendency:   extreme/' "$SSOT" > "$_t/badenum.md"
_o=$(sh "$LP" "$_t/badenum.md" 2>&1); _ec=$?
_pg_nonzero "$_ec" "lp-6: invalid enum value fails"
assert_contains "$_o" "PERSONA_ENUM_INVALID" "lp-6: names PERSONA_ENUM_INVALID"

# ── lp-7: non-integer patience budget fails ───────────────────────────────────
sed 's/^patience_budget:  2$/patience_budget:  plenty/' "$SSOT" > "$_t/badbudget.md"
_o=$(sh "$LP" "$_t/badbudget.md" 2>&1); _ec=$?
_pg_nonzero "$_ec" "lp-7: non-integer patience_budget fails"
assert_contains "$_o" "PERSONA_ENUM_INVALID" "lp-7: budget failure uses PERSONA_ENUM_INVALID"

# ── lp-8: non-kebab misbehavior token fails ───────────────────────────────────
sed 's/  - double-clicks-submit/  - Double Clicks Submit/' "$SSOT" > "$_t/badtoken.md"
_o=$(sh "$LP" "$_t/badtoken.md" 2>&1); _ec=$?
_pg_nonzero "$_ec" "lp-8: non-kebab misbehavior token fails"
assert_contains "$_o" "MISBEHAVIOR_TOKEN_INVALID" "lp-8: names MISBEHAVIOR_TOKEN_INVALID"

# ── lp-9: blank misbehavior list fails; explicit none-with-reason passes ──────
sed 's/^known_misbehaviors: \[none: methodical reviewer; follows the documented flow\]$/known_misbehaviors:/' "$SSOT" > "$_t/blank.md"
_o=$(sh "$LP" "$_t/blank.md" 2>&1); _ec=$?
_pg_nonzero "$_ec" "lp-9: blank misbehavior list fails"
assert_contains "$_o" "MISBEHAVIORS_BLANK" "lp-9: names MISBEHAVIORS_BLANK"
# (golden P2 already proves the none-with-reason form passes via lp-1)

# ═══ check-persona-journeys.sh ═════════════════════════════════════════════════

# ── pj-1: golden PERSONA journey passes ───────────────────────────────────────
sh "$CPJ" "$PMAP" "$SSOT" >/dev/null 2>&1
assert_eq 0 $? "pj-1: golden PERSONA journey passes"

# ── pj-2: undefined persona fails ─────────────────────────────────────────────
sed 's/^persona:         P1 (Operations User)$/persona:         P9 (Ghost User)/' "$PMAP" > "$_t/ghost.md"
_o=$(sh "$CPJ" "$_t/ghost.md" "$SSOT" 2>&1); _ec=$?
_pg_nonzero "$_ec" "pj-2: undefined persona fails"
assert_contains "$_o" "UNDEFINED_PERSONA" "pj-2: names UNDEFINED_PERSONA"

# ── pj-3: happy path in costume (no misbehavior step) fails ───────────────────
sed 's/ (misbehavior: uploads-wrong-file-first)//; s/ (misbehavior: double-clicks-submit)//' "$PMAP" > "$_t/costume.md"
_o=$(sh "$CPJ" "$_t/costume.md" "$SSOT" 2>&1); _ec=$?
_pg_nonzero "$_ec" "pj-3: PERSONA journey with zero misbehavior steps fails"
assert_contains "$_o" "NO_MISBEHAVIOR_STEP" "pj-3: names NO_MISBEHAVIOR_STEP"

# ── pj-4: foreign misbehavior token fails ─────────────────────────────────────
sed 's/(misbehavior: double-clicks-submit)/(misbehavior: ignores-audit-trail)/' "$PMAP" > "$_t/foreign.md"
_o=$(sh "$CPJ" "$_t/foreign.md" "$SSOT" 2>&1); _ec=$?
_pg_nonzero "$_ec" "pj-4: misbehavior token not owned by the persona fails"
assert_contains "$_o" "FOREIGN_MISBEHAVIOR" "pj-4: names FOREIGN_MISBEHAVIOR"

# ── pj-5: DERIVED journeys are ignored by this gate ───────────────────────────
sh "$CPJ" "$GENDIR/golden/expected-journey-map.generated.md" "$SSOT" >/dev/null 2>&1
assert_eq 0 $? "pj-5: a map with only DERIVED journeys passes untouched"

# ═══ check-persona-coverage.sh ═════════════════════════════════════════════════

# ── pc-1: golden map + gap covers both P0/P1 FEATs ────────────────────────────
sh "$CPC" "$GENDIR/PRD.md" "$SSOT" "$PMAP" "$PGAPS" >/dev/null 2>&1
assert_eq 0 $? "pc-1: FEAT-001 journey + FEAT-002 gap = covered"

# ── pc-2: uncovered P0/P1 FEAT fails ──────────────────────────────────────────
printf '# empty gaps\n' > "$_t/nogaps.md"
_o=$(sh "$CPC" "$GENDIR/PRD.md" "$SSOT" "$PMAP" "$_t/nogaps.md" 2>&1); _ec=$?
_pg_nonzero "$_ec" "pc-2: uncovered P0/P1 FEAT fails"
assert_contains "$_o" "PERSONA_COVERAGE_GAP" "pc-2: names PERSONA_COVERAGE_GAP"
assert_contains "$_o" "FEAT-002" "pc-2: names the uncovered FEAT"

# ── pc-3: expired gap is not a credit ─────────────────────────────────────────
sed 's/^expires: 2099-12-31$/expires: 2020-01-01/' "$PGAPS" > "$_t/expired.md"
_o=$(sh "$CPC" "$GENDIR/PRD.md" "$SSOT" "$PMAP" "$_t/expired.md" 2>&1); _ec=$?
_pg_nonzero "$_ec" "pc-3: expired gap fails"
assert_contains "$_o" "GAP_EXPIRED" "pc-3: names GAP_EXPIRED"

# ── pc-4: malformed gap fails ─────────────────────────────────────────────────
grep -v '^owner:' "$PGAPS" > "$_t/malformed.md"
_o=$(sh "$CPC" "$GENDIR/PRD.md" "$SSOT" "$PMAP" "$_t/malformed.md" 2>&1); _ec=$?
_pg_nonzero "$_ec" "pc-4: gap without owner fails"
assert_contains "$_o" "GAP_MALFORMED" "pc-4: names GAP_MALFORMED"

# ── pc-5: covered AND gapped fails ────────────────────────────────────────────
sed 's/^source_id: FEAT-002$/source_id: FEAT-001/' "$PGAPS" > "$_t/both.md"
_o=$(sh "$CPC" "$GENDIR/PRD.md" "$SSOT" "$PMAP" "$_t/both.md" 2>&1); _ec=$?
_pg_nonzero "$_ec" "pc-5: FEAT both covered and gapped fails"
assert_contains "$_o" "COVERED_AND_GAPPED" "pc-5: names COVERED_AND_GAPPED"

# ── pc-6: zero anchors fails (anti-vacuous) ───────────────────────────────────
printf '# PRD\n\n## FEAT-001 — "Later"\npriority: P2\nuser_story: later\nacceptance_criteria:\n  - AC-1: later\n' > "$_t/p2only.md"
_o=$(sh "$CPC" "$_t/p2only.md" "$SSOT" "$PMAP" "$PGAPS" 2>&1); _ec=$?
_pg_nonzero "$_ec" "pc-6: zero P0/P1 FEATs fails"
assert_contains "$_o" "NO_ANCHORS" "pc-6: names NO_ANCHORS"
printf '# SSOT\n\n## System Context\nno personas\n' > "$_t/nopersona-ssot.md"
_o=$(sh "$CPC" "$GENDIR/PRD.md" "$_t/nopersona-ssot.md" "$PMAP" "$PGAPS" 2>&1); _ec=$?
_pg_nonzero "$_ec" "pc-6b: zero personas fails"

# ═══ persona-selfcheck.sh ══════════════════════════════════════════════════════

# ── sc-1: golden chain passes ─────────────────────────────────────────────────
sh "$PSC" "$SSOT" "$GENDIR/PRD.md" "$PMAP" "$PGAPS" >/dev/null 2>&1
assert_eq 0 $? "psc-1: golden selfcheck chain passes"

# ── sc-2: failures are attributed to the failing gate ─────────────────────────
_o=$(sh "$PSC" "$_t/none.md" "$GENDIR/PRD.md" "$PMAP" "$PGAPS" 2>&1); _ec=$?
_pg_nonzero "$_ec" "psc-2: selfcheck fails when a gate fails"
assert_contains "$_o" "lint-personas" "psc-2: failure attributed to lint-personas"
_o=$(sh "$PSC" "$SSOT" "$GENDIR/PRD.md" "$_t/costume.md" "$PGAPS" 2>&1); _ec=$?
_pg_nonzero "$_ec" "psc-3: selfcheck fails on the costume map"
assert_contains "$_o" "check-persona-journeys" "psc-3: failure attributed to check-persona-journeys"

rm -rf "$_t"
