# shellcheck shell=sh
# persona-thematic-break_test.sh — owner ruling, ITEM 1 (2026-07-14).
#
# lint-personas.sh must IGNORE markdown thematic breaks before applying the
# misbehavior list-item regex.
#
# The defect: a thematic break spelled with dashes (`---`, or the spaced
# `- - -`) starts with a dash, so the list-item regex
#     /^[[:space:]]*-[[:space:]]*/
# matched it, stripped the leading "- ", and reported the REMAINDER as a
# misbehavior token. A document that closed its `## Personas` section with a
# trailing `---` therefore failed the whole lint with
#     MISBEHAVIOR_TOKEN_INVALID: P8 token '--' is not kebab-case
# on a persona whose misbehavior list was perfectly well-formed. Both frozen
# staging bundles (Audit, 8 personas; RightShip, 6) tripped exactly this.
#
# The fix is a SKIP, never a relaxation of the token grammar:
#   * a kebab token must contain [a-z0-9], so a line made only of dashes,
#     stars, underscores and spaces can never be a VALID token — it can only
#     ever be an invalid one. Skipping it removes a false POSITIVE and cannot
#     create a false green (asserted below, `tb-6`/`tb-7`);
#   * a known_misbehaviors list containing nothing but breaks still derives
#     zero tokens and still fails closed with MISBEHAVIORS_BLANK (`tb-8`);
#   * real list items are still parsed and still kebab-validated (`tb-6`),
#     and a malformed token in a real list item still fails (`tb-7`).
#
# The breaks are NOT removed from the bundles as a workaround: the parser is
# what was wrong, so the parser is what changed.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
LP="$TESTS_DIR/../bin/lint-personas.sh"

_tb=$(mktemp -d)
trap 'rm -rf "$_tb"' EXIT INT TERM

# ── an SSOT with two valid personas; $1 is spliced in after the LAST persona ──
_mk() { # FILE TRAILER
  _f="$1"; _trailer="$2"
  {
    printf '# SSOT\n\n## Personas\n\n'
    printf '### P1 — "Auditor"\n'
    printf 'goal:             close a finding\n'
    printf 'context:          at sea\n'
    printf 'tech_savviness:   medium\n'
    printf 'error_tendency:   medium\n'
    printf 'patience_budget:  3\n'
    printf 'known_misbehaviors:\n'
    printf '  - skips-the-evidence-field\n'
    printf '  - closes-car-without-verification\n\n'
    printf '### P2 — "Master"\n'
    printf 'goal:             acknowledge the report\n'
    printf 'context:          on the bridge\n'
    printf 'tech_savviness:   low\n'
    printf 'error_tendency:   high\n'
    printf 'patience_budget:  1\n'
    printf 'known_misbehaviors:\n'
    printf '  - acknowledges-without-reading\n'
    printf '%s' "$_trailer"
    printf '\n## Next Section\n'
  } > "$_f"
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. The three canonical thematic-break forms, each trailing the last persona.
#    Every one of these used to be (or, for * and _, could become) a token.
# ─────────────────────────────────────────────────────────────────────────────
for _form in '---' '***' '___'; do
  _f="$_tb/form.md"
  _mk "$_f" "
$_form
"
  _out=$(sh "$LP" "$_f" 2>&1); _ec=$?
  assert_eq "0" "$_ec" "tb-1[$_form]: trailing thematic break does not fail the lint"
  assert_not_contains "$_out" "MISBEHAVIOR_TOKEN_INVALID" \
    "tb-1[$_form]: no MISBEHAVIOR_TOKEN_INVALID from a thematic break"
done

# ─────────────────────────────────────────────────────────────────────────────
# 2. Surrounding whitespace + the spaced variants. `- - -` is a CommonMark
#    thematic break AND looks exactly like a list item — the hardest case.
# ─────────────────────────────────────────────────────────────────────────────
for _form in '  ---  ' '   ---' '---   ' '- - -' '* * *' '_ _ _' '-----' '  * * *  '; do
  _f="$_tb/ws.md"
  _mk "$_f" "
$_form
"
  _out=$(sh "$LP" "$_f" 2>&1); _ec=$?
  assert_eq "0" "$_ec" "tb-2[$_form]: whitespace/spaced break variant is ignored"
  assert_not_contains "$_out" "MISBEHAVIOR_TOKEN_INVALID" \
    "tb-2[$_form]: no token derived from [$_form]"
done

# ─────────────────────────────────────────────────────────────────────────────
# 3. A break BETWEEN personas (not just trailing) is also ignored.
# ─────────────────────────────────────────────────────────────────────────────
_f="$_tb/between.md"
{
  printf '# SSOT\n\n## Personas\n\n'
  printf '### P1 — "Auditor"\n'
  printf 'goal:             g\ncontext:          c\n'
  printf 'tech_savviness:   low\nerror_tendency:   low\npatience_budget:  2\n'
  printf 'known_misbehaviors:\n  - skips-the-evidence-field\n\n'
  printf -- '---\n\n'
  printf '### P2 — "Master"\n'
  printf 'goal:             g\ncontext:          c\n'
  printf 'tech_savviness:   low\nerror_tendency:   low\npatience_budget:  2\n'
  printf 'known_misbehaviors:\n  - acknowledges-without-reading\n'
} > "$_f"
_out=$(sh "$LP" "$_f" 2>&1); _ec=$?
assert_eq "0" "$_ec" "tb-3: a break BETWEEN two personas is ignored"
assert_not_contains "$_out" "MISBEHAVIOR_TOKEN_INVALID" "tb-3: no token from the interior break"

# ─────────────────────────────────────────────────────────────────────────────
# 4. THE REGRESSION, exactly as the bundles hit it: the old parser turned a
#    trailing `---` into the token '--'. Assert that specific string is gone.
# ─────────────────────────────────────────────────────────────────────────────
_f="$_tb/regress.md"
_mk "$_f" "
---
"
_out=$(sh "$LP" "$_f" 2>&1)
assert_not_contains "$_out" "token '--'" "tb-4: the '--' phantom token is gone"

# ─────────────────────────────────────────────────────────────────────────────
# 5. Bundle-shaped: 8 personas (Audit) and 6 (RightShip), each closing with a
#    trailing `---`. Expect exit 0 with ONLY the approved non-blocking
#    persona-count warning — a warning is not a state and never a verdict.
# ─────────────────────────────────────────────────────────────────────────────
_mk_n() { # N FILE
  _n="$1"; _f="$2"
  {
    printf '# SSOT\n\n## Personas\n\n'
    _i=1
    while [ "$_i" -le "$_n" ]; do
      printf '### P%s — "Role %s"\n' "$_i" "$_i"
      printf 'goal:             g%s\ncontext:          c%s\n' "$_i" "$_i"
      printf 'tech_savviness:   medium\nerror_tendency:   medium\npatience_budget:  3\n'
      printf 'known_misbehaviors:\n  - skips-the-evidence-field\n\n'
      _i=$((_i + 1))
    done
    printf -- '---\n'
  } > "$_f"
}
for _n in 8 6; do
  _f="$_tb/n$_n.md"
  _mk_n "$_n" "$_f"
  _out=$(sh "$LP" "$_f" 2>&1); _ec=$?
  assert_eq "0" "$_ec" "tb-5[$_n personas]: passes with a trailing break"
  assert_contains "$_out" "TOO_MANY_PERSONAS" "tb-5[$_n]: the count warning is still emitted"
  assert_contains "$_out" "WARN:" "tb-5[$_n]: and it is emitted as a WARNING, not a problem"
  assert_not_contains "$_out" "MISBEHAVIOR_TOKEN_INVALID" "tb-5[$_n]: and nothing else fires"
  assert_not_contains "$_out" "problem(s) in" "tb-5[$_n]: zero problems reported"
done

# ─────────────────────────────────────────────────────────────────────────────
# 6. ANTI-FALSE-GREEN — real list items are still parsed and still validated.
#    A skip that also swallowed real tokens would silently disarm the lint.
# ─────────────────────────────────────────────────────────────────────────────
_f="$_tb/valid.md"
_mk "$_f" ""
_out=$(sh "$LP" "$_f" 2>&1); _ec=$?
assert_eq "0" "$_ec" "tb-6a: a well-formed kebab list still passes"

# ...and the tokens are genuinely being READ, not skipped: break the grammar of
# a token that sits in a REAL list item and the lint must still catch it.
_f="$_tb/badtok.md"
{
  printf '# SSOT\n\n## Personas\n\n'
  printf '### P1 — "Auditor"\n'
  printf 'goal:             g\ncontext:          c\n'
  printf 'tech_savviness:   low\nerror_tendency:   low\npatience_budget:  2\n'
  printf 'known_misbehaviors:\n'
  printf '  - Skips_The_Evidence\n'
  printf '\n### P2 — "Master"\n'
  printf 'goal:             g\ncontext:          c\n'
  printf 'tech_savviness:   low\nerror_tendency:   low\npatience_budget:  2\n'
  printf 'known_misbehaviors:\n  - acknowledges-without-reading\n\n'
  printf -- '---\n'
} > "$_f"
_out=$(sh "$LP" "$_f" 2>&1); _ec=$?
assert_eq "1" "$_ec" "tb-6b: a malformed token in a REAL list item still fails"
assert_contains "$_out" "MISBEHAVIOR_TOKEN_INVALID" "tb-6b: and names MISBEHAVIOR_TOKEN_INVALID"
assert_contains "$_out" "Skips_The_Evidence" "tb-6b: and names the offending token"

# ─────────────────────────────────────────────────────────────────────────────
# 7. ANTI-FALSE-GREEN — the break skip must not become a token-laundering
#    channel. A token that merely CONTAINS dashes/stars is not a break.
# ─────────────────────────────────────────────────────────────────────────────
_f="$_tb/notbreak.md"
{
  printf '# SSOT\n\n## Personas\n\n'
  printf '### P1 — "Auditor"\n'
  printf 'goal:             g\ncontext:          c\n'
  printf 'tech_savviness:   low\nerror_tendency:   low\npatience_budget:  2\n'
  printf 'known_misbehaviors:\n'
  printf '  - not*kebab*token\n'
  printf '\n### P2 — "Master"\n'
  printf 'goal:             g\ncontext:          c\n'
  printf 'tech_savviness:   low\nerror_tendency:   low\npatience_budget:  2\n'
  printf 'known_misbehaviors:\n  - acknowledges-without-reading\n'
} > "$_f"
_out=$(sh "$LP" "$_f" 2>&1); _ec=$?
assert_eq "1" "$_ec" "tb-7: a token containing '*' is NOT treated as a break — it still fails"
assert_contains "$_out" "not*kebab*token" "tb-7: and the token is named"

# ─────────────────────────────────────────────────────────────────────────────
# 8. FAIL-CLOSED — a misbehavior list holding ONLY a thematic break derives
#    zero tokens, and an empty list is still MISBEHAVIORS_BLANK. The skip
#    must not turn "no tokens" into "no problem".
# ─────────────────────────────────────────────────────────────────────────────
_f="$_tb/blank.md"
{
  printf '# SSOT\n\n## Personas\n\n'
  printf '### P1 — "Auditor"\n'
  printf 'goal:             g\ncontext:          c\n'
  printf 'tech_savviness:   low\nerror_tendency:   low\npatience_budget:  2\n'
  printf 'known_misbehaviors:\n'
  printf -- '  ---\n'
  printf '\n### P2 — "Master"\n'
  printf 'goal:             g\ncontext:          c\n'
  printf 'tech_savviness:   low\nerror_tendency:   low\npatience_budget:  2\n'
  printf 'known_misbehaviors:\n  - acknowledges-without-reading\n'
} > "$_f"
_out=$(sh "$LP" "$_f" 2>&1); _ec=$?
assert_eq "1" "$_ec" "tb-8: a misbehavior list of ONLY a break still fails closed"
assert_contains "$_out" "MISBEHAVIORS_BLANK" "tb-8: and it fails as MISBEHAVIORS_BLANK, not silently"
