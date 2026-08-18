# shellcheck shell=sh
# persona-count-policy_test.sh — owner ruling B (2026-07-14).
#
# The persona-count ceiling is ADVISORY, not a contract:
#
#     < 2   -> NO_PERSONAS        BLOCKING failure
#     2-5   -> pass, silent
#     > 5   -> TOO_MANY_PERSONAS  NON-BLOCKING warning (exit 0)
#
# Why the ceiling had to stop failing: it is a heuristic about simulator
# dilution, not a property of the world. Real RBAC role models exceed it — the
# Audit module has 8 approved roles, the RightShip module 6 — and those persona
# numbers are cited in FROZEN journey maps. The old lint offered exactly two
# ways out, and both were corruption: prune a real approved role to flatter a
# gate, or bank TOO_MANY_PERSONAS as permanent "project debt" and teach the team
# that a red gate is normal. A warning informs; only a contract may block.
#
# The FLOOR is different and stays hard: a 0- or 1-persona set makes the whole
# persona layer vacuous, so < 2 is still a failure.
#
# TOO_MANY_PERSONAS is a WARNING DIAGNOSTIC, never a state — it does not enter
# the RESOLVED / DEFERRED / BLOCKED / NOT_APPLICABLE_YET vocabulary and never
# changes a verdict.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LP="$TESTS_DIR/../bin/lint-personas.sh"

_pc=$(mktemp -d)
trap 'rm -rf "$_pc"' EXIT INT TERM

# ── Build an SSOT with exactly N personas, all structurally valid ─────────────
# P1 always carries a real misbehavior list; the rest declare none-with-reason.
_mk_ssot() { # N FILE
  _n="$1"; _f="$2"
  {
    printf '# SSOT\n\n## Personas\n\n'
    _i=1
    while [ "$_i" -le "$_n" ]; do
      printf '### P%d — "Role %d"\n' "$_i" "$_i"
      printf 'goal:             do job %d\n' "$_i"
      printf 'context:          office, daily\n'
      printf 'tech_savviness:   medium\n'
      printf 'error_tendency:   low\n'
      printf 'patience_budget:  2\n'
      if [ "$_i" -eq 1 ]; then
        printf 'known_misbehaviors:\n  - double-clicks-submit\n  - uploads-wrong-file-first\n\n'
      else
        printf 'known_misbehaviors: [none: methodical; follows the documented flow]\n\n'
      fi
      _i=$((_i + 1))
    done
    printf '## System Context\n\nprose\n'
  } > "$_f"
}

# ── The five ruled-on counts ──────────────────────────────────────────────────

# N=1 — below the floor: still a hard failure.
_mk_ssot 1 "$_pc/n1.md"
_o=$(sh "$LP" "$_pc/n1.md" 2>&1); _ec=$?
assert_eq 1 "$_ec" "pcp-1a: 1 persona FAILS (below the floor of 2)"
assert_contains "$_o" "NO_PERSONAS" "pcp-1b: 1 persona names NO_PERSONAS"
assert_not_contains "$_o" "TOO_MANY_PERSONAS" "pcp-1c: 1 persona is not a ceiling problem"

# N=2 — the floor exactly: passes, silently.
_mk_ssot 2 "$_pc/n2.md"
_o=$(sh "$LP" "$_pc/n2.md" 2>&1); _ec=$?
assert_eq 0 "$_ec" "pcp-2a: 2 personas PASS (floor is inclusive)"
assert_not_contains "$_o" "NO_PERSONAS" "pcp-2b: 2 personas emit no NO_PERSONAS"
assert_not_contains "$_o" "TOO_MANY_PERSONAS" "pcp-2c: 2 personas emit no warning"
assert_eq "" "$_o" "pcp-2d: 2 personas produce NO output at all (byte-identical to the pre-ruling pass)"

# N=5 — the top of the advisory range: passes, silently, no warning.
_mk_ssot 5 "$_pc/n5.md"
_o=$(sh "$LP" "$_pc/n5.md" 2>&1); _ec=$?
assert_eq 0 "$_ec" "pcp-3a: 5 personas PASS (ceiling is inclusive)"
assert_not_contains "$_o" "TOO_MANY_PERSONAS" "pcp-3b: 5 personas emit NO warning"
assert_eq "" "$_o" "pcp-3c: 5 personas produce NO output (the 2-5 pass is unchanged by this ruling)"

# N=6 — RightShip's real count: PASSES, with a non-blocking warning.
_mk_ssot 6 "$_pc/n6.md"
_o=$(sh "$LP" "$_pc/n6.md" 2>&1); _ec=$?
assert_eq 0 "$_ec" "pcp-4a: 6 personas PASS (was a hard failure before the ruling)"
assert_contains "$_o" "TOO_MANY_PERSONAS" "pcp-4b: 6 personas emit TOO_MANY_PERSONAS"
assert_contains "$_o" "WARN:" "pcp-4c: 6 personas — the diagnostic is a WARNING, not a problem"
assert_contains "$_o" "non-blocking" "pcp-4d: 6 personas — the warning says so in words"
assert_not_contains "$_o" "fail closed" "pcp-4e: 6 personas — no fail-closed summary line"

# N=8 — Audit's real count: PASSES, same warning.
_mk_ssot 8 "$_pc/n8.md"
_o=$(sh "$LP" "$_pc/n8.md" 2>&1); _ec=$?
assert_eq 0 "$_ec" "pcp-5a: 8 personas PASS (Audit's approved RBAC role model)"
assert_contains "$_o" "TOO_MANY_PERSONAS" "pcp-5b: 8 personas emit TOO_MANY_PERSONAS"
assert_contains "$_o" "WARN:" "pcp-5c: 8 personas — warning, not failure"
assert_contains "$_o" "8 personas" "pcp-5d: the warning reports the actual count"

# The warning is a DIAGNOSTIC, not a state: none of the four canonical state
# tokens may leak into a lint that merely wants to raise an eyebrow.
for _state in RESOLVED DEFERRED BLOCKED NOT_APPLICABLE_YET; do
  assert_not_contains "$_o" "$_state" "pcp-5e: the warning introduces no '$_state' state token"
done

# ═══════════════════════════════════════════════════════════════════════════════
# Ruling B condition 6 — EVERY structural check stays enforced above 5 personas.
#
# The danger of "more than five is fine" is that >5 becomes an unpoliced zone.
# It does not: the 6th, 7th and 8th personas are linted exactly like the first.
# ═══════════════════════════════════════════════════════════════════════════════

# Duplicate id among 8 personas still fails.
sed 's/^### P7 — "Role 7"$/### P3 — "Role 7"/' "$_pc/n8.md" > "$_pc/n8-dup.md"
_o=$(sh "$LP" "$_pc/n8-dup.md" 2>&1); _ec=$?
assert_eq 1 "$_ec" "pcp-6a: duplicate persona id at N=8 still FAILS"
assert_contains "$_o" "DUPLICATE_PERSONA_ID" "pcp-6b: names DUPLICATE_PERSONA_ID above the ceiling"
assert_contains "$_o" "TOO_MANY_PERSONAS" "pcp-6c: the warning still rides along with the failure"

# Missing required field on the 8th persona still fails.
awk '/^### P8 /{p=1} p && /^context:/ {next} {print}' "$_pc/n8.md" > "$_pc/n8-nofield.md"
_o=$(sh "$LP" "$_pc/n8-nofield.md" 2>&1); _ec=$?
assert_eq 1 "$_ec" "pcp-7a: a missing required field on persona 8 still FAILS"
assert_contains "$_o" "PERSONA_FIELD_MISSING" "pcp-7b: names PERSONA_FIELD_MISSING above the ceiling"

# Bad enum on the 6th persona still fails.
awk '/^### P6 /{p=1} p && /^error_tendency:/ {sub(/low/, "extreme")} {print}' "$_pc/n6.md" > "$_pc/n6-badenum.md"
_o=$(sh "$LP" "$_pc/n6-badenum.md" 2>&1); _ec=$?
assert_eq 1 "$_ec" "pcp-8a: an invalid enum on persona 6 still FAILS"
assert_contains "$_o" "PERSONA_ENUM_INVALID" "pcp-8b: names PERSONA_ENUM_INVALID above the ceiling"

# Non-kebab misbehavior token on persona 1 still fails even in an 8-persona set.
sed 's/^  - double-clicks-submit$/  - Double Clicks Submit/' "$_pc/n8.md" > "$_pc/n8-badtoken.md"
_o=$(sh "$LP" "$_pc/n8-badtoken.md" 2>&1); _ec=$?
assert_eq 1 "$_ec" "pcp-9a: a non-kebab misbehavior token at N=8 still FAILS"
assert_contains "$_o" "MISBEHAVIOR_TOKEN_INVALID" "pcp-9b: names MISBEHAVIOR_TOKEN_INVALID above the ceiling"

# A warning alone never flips the verdict: the summary must report the pass.
_o=$(sh "$LP" "$_pc/n8.md" 2>&1)
assert_contains "$_o" "0 problem(s)" "pcp-10a: an 8-persona SSOT reports ZERO problems"
assert_contains "$_o" "the lint PASSES" "pcp-10b: the summary states the verdict explicitly"
