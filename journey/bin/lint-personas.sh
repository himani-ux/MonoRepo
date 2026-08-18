#!/bin/sh
# shellcheck shell=sh
# lint-personas.sh SSOT
#
# Persona-schema lint (Increment 3, spec §3). The SSOT '## Personas' section
# must contain AT LEAST 2 machine-readable blocks:
#
#   ### P<n> — "<name>"
#   goal:             <non-blank>
#   context:          <non-blank>
#   tech_savviness:   low | medium | high
#   error_tendency:   low | medium | high
#   patience_budget:  <non-negative integer>   (captured for Increment 4; NOT consumed here)
#   known_misbehaviors:
#     - kebab-case-token            (or:  known_misbehaviors: [none: <reason>])
#
# Markdown THEMATIC BREAKS (--- / *** / ___, with any surrounding whitespace,
# and the spaced `- - -` variant) are prose punctuation, not list items: they
# are SKIPPED before the misbehavior list-item regex is applied. A document may
# close its persona section with one. See the parser note below for why this
# cannot mask a real token error.
#
# Persona COUNT policy (owner ruling, 2026-07-14):
#   < 2   -> NO_PERSONAS         (BLOCKING failure — a 0/1-persona set is vacuous)
#   2–5   -> pass, silent        (the advisory sweet spot)
#   > 5   -> TOO_MANY_PERSONAS   (NON-BLOCKING warning — never a failure)
# The 2–5 range is ADVISORY, not a canonical contract: it is a heuristic about
# simulator dilution, not a property the docs must satisfy. Real RBAC role
# models legitimately exceed it (an 8-role audit module, a 6-role RS module),
# their persona counts are cited by number in frozen journey maps, and pruning
# a real approved role to satisfy a lint heuristic would corrupt the journey
# layer to flatter the gate. A warning informs; it must not block. TOO_MANY_
# PERSONAS is therefore a WARNING DIAGNOSTIC, not a state — it never changes
# the verdict and is never project debt.
#
# Diagnostics (blocking): NO_PERSONAS, DUPLICATE_PERSONA_ID,
# PERSONA_FIELD_MISSING, PERSONA_ENUM_INVALID, MISBEHAVIOR_TOKEN_INVALID,
# MISBEHAVIORS_BLANK.
# Warnings (non-blocking): TOO_MANY_PERSONAS.
# Diagnostics to stdout (lint convention); exit 1 on any BLOCKING diagnostic.
# Deps: POSIX sh, awk, grep, sed.

set -u
_die() { printf '%s\n' "$*" >&2; exit 1; }

[ $# -eq 1 ] || _die "usage: lint-personas.sh SSOT"
SSOT="$1"
[ -r "$SSOT" ] || _die "lint-personas: file not readable: $SSOT"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

problems=0
warnings=0
_p() { printf '%s\n' "$1"; problems=$((problems + 1)); }
# _w: non-blocking warning. Prints, counts, and NEVER touches `problems` — a
# warning informs the author, it does not change the verdict (WARN: is the
# framework's existing non-blocking prefix, cf. check-journeys.sh).
_w() { printf 'WARN: %s\n' "$1"; warnings=$((warnings + 1)); }

# ── split ## Personas into per-block files ────────────────────────────────────
awk -v out="$_tmp" '
  /^## Personas/ { inp = 1; next }
  inp && /^## /  { inp = 0; next }
  inp && /^### / {
    line = $0
    if (!match(line, /P[0-9]+/)) { cur = ""; next }
    id = substr(line, RSTART, RLENGTH)
    print id >> (out "/ids.txt")
    cur = out "/persona_" id "_" (++n[id]) ".txt"
    print line > cur
    next
  }
  inp && cur != "" { print >> cur }
' "$SSOT"

if [ ! -s "$_tmp/ids.txt" ]; then
  _p "NO_PERSONAS: no '### P<n> — \"<name>\"' block under '## Personas' (at least 2 required; see spec §3)"
else
  _count=$(wc -l < "$_tmp/ids.txt" | tr -d ' ')
  # > 5 personas: WARN only. The ceiling is advisory (simulator dilution), not a
  # contract — an approved RBAC role model may legitimately exceed it, and the
  # journey map cites the personas by number. Never a failure, never debt.
  [ "$_count" -le 5 ] || \
    _w "TOO_MANY_PERSONAS: $_count personas (2-5 is the advisory range — beyond 5 dilutes the simulator and the coverage rule; non-blocking, the verdict is unchanged)"
  # < 2 personas: still a hard failure. A 0- or 1-persona set makes the whole
  # persona layer vacuous, so this floor is a real contract, not advice.
  [ "$_count" -ge 2 ] || \
    _p "NO_PERSONAS: only $_count persona block(s) (at least 2 required)"
  for _dup in $(sort "$_tmp/ids.txt" | uniq -d); do
    _p "DUPLICATE_PERSONA_ID: $_dup appears more than once"
  done
fi

# ── per-persona checks (first block per id) ───────────────────────────────────
for _pid in $(sort -u "$_tmp/ids.txt" 2>/dev/null); do
  _bf="$_tmp/persona_${_pid}_1.txt"
  [ -f "$_bf" ] || continue

  grep -qE '^### P[0-9]+ [—-] "[^"]+"' "$_bf" || \
    _p "PERSONA_FIELD_MISSING: $_pid heading lacks a quoted \"<name>\" (### P<n> — \"<name>\")"

  for _k in goal context tech_savviness error_tendency patience_budget known_misbehaviors; do
    grep -qE "^${_k}:" "$_bf" || \
      _p "PERSONA_FIELD_MISSING: $_pid has no '${_k}:' field"
  done
  for _k in goal context; do
    if grep -qE "^${_k}:" "$_bf" && ! grep -qE "^${_k}:[[:space:]]*[^[:space:]]" "$_bf"; then
      _p "PERSONA_FIELD_MISSING: $_pid '${_k}:' is blank"
    fi
  done

  for _k in tech_savviness error_tendency; do
    _v=$(grep -m1 -E "^${_k}:" "$_bf" | sed "s/^${_k}:[[:space:]]*//;s/[[:space:]]*#.*$//;s/[[:space:]]*$//")
    if grep -qE "^${_k}:" "$_bf"; then
      case "$_v" in
        low|medium|high) : ;;
        *) _p "PERSONA_ENUM_INVALID: $_pid ${_k} '$_v' (must be low|medium|high)" ;;
      esac
    fi
  done

  _pb=$(grep -m1 -E '^patience_budget:' "$_bf" | sed 's/^patience_budget:[[:space:]]*//;s/[[:space:]]*#.*$//;s/[[:space:]]*$//')
  if grep -qE '^patience_budget:' "$_bf"; then
    case "$_pb" in
      ''|*[!0-9]*) _p "PERSONA_ENUM_INVALID: $_pid patience_budget '$_pb' (must be a non-negative integer)" ;;
    esac
  fi

  # misbehaviors: inline [none: <reason>] OR >=1 '  - token' line
  if grep -qE '^known_misbehaviors:' "$_bf"; then
    _inline=$(grep -m1 -E '^known_misbehaviors:' "$_bf" | sed 's/^known_misbehaviors:[[:space:]]*//;s/[[:space:]]*$//')
    if [ -n "$_inline" ]; then
      case "$_inline" in
        "[none: "*"]"|"[none:"*"]") : ;;  # explicit none-with-reason
        *) _p "MISBEHAVIOR_TOKEN_INVALID: $_pid inline known_misbehaviors must be '[none: <reason>]', got: [$_inline]" ;;
      esac
    else
      awk '
           # A markdown THEMATIC BREAK is not a list item. CommonMark spells it
           # with three or more -, * or _ (all the same char), optionally spaced
           # apart and surrounded by whitespace: --- *** ___ "  ---  " "- - -".
           # The `- - -` and `---` forms both start with a dash, so the
           # list-item regex below used to eat them: it stripped the leading
           # "- " and reported the REMAINDER as a token — a trailing `---` after
           # the final persona became the token "--" and failed the whole lint
           # with MISBEHAVIOR_TOKEN_INVALID. The break is prose punctuation; a
           # document is allowed to close a section with one.
           #
           # Skipping these lines cannot manufacture a false green. A kebab-case
           # token must contain [a-z0-9], so a line made only of dashes, stars,
           # underscores and spaces can NEVER be a valid token — today it can
           # only produce an INVALID one. Removing it removes a false POSITIVE,
           # never a real failure. And a known_misbehaviors list that holds
           # nothing BUT thematic breaks still yields zero tokens, so it still
           # fails closed with MISBEHAVIORS_BLANK below.
           #
           # Written without ERE interval braces {3,} — not every stock awk
           # supports them. "(x[ \t]*)(x[ \t]*)(x[ \t]*)+" is three-or-more.
           function is_tbreak(s) {
             return (s ~ /^[ \t]*(-[ \t]*)(-[ \t]*)(-[ \t]*)+$/)  ||
                    (s ~ /^[ \t]*(\*[ \t]*)(\*[ \t]*)(\*[ \t]*)+$/) ||
                    (s ~ /^[ \t]*(_[ \t]*)(_[ \t]*)(_[ \t]*)+$/)
           }
           /^known_misbehaviors:/ { inm = 1; next }
           /^[a-z_]+:/ && inm    { inm = 0 }
           /^### / && inm        { inm = 0 }
           inm && is_tbreak($0) { next }
           inm && /^[[:space:]]*-[[:space:]]*/ {
             sub(/^[[:space:]]*-[[:space:]]*/, ""); sub(/[[:space:]]+$/, ""); print }
      ' "$_bf" > "$_tmp/tokens.txt"
      if [ ! -s "$_tmp/tokens.txt" ]; then
        _p "MISBEHAVIORS_BLANK: $_pid known_misbehaviors is empty — list kebab-case tokens or declare '[none: <reason>]' explicitly"
      else
        while IFS= read -r _tok; do
          [ -n "$_tok" ] || continue
          printf '%s\n' "$_tok" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*$' || \
            _p "MISBEHAVIOR_TOKEN_INVALID: $_pid token '$_tok' is not kebab-case"
        done < "$_tmp/tokens.txt"
      fi
    fi
  fi
done

if [ "$problems" -gt 0 ]; then
  printf 'lint-personas: %d problem(s) in %s (fail closed)\n' "$problems" "$SSOT"
  exit 1
fi
# Warnings never fail the lint. Summarised only when there are any, so a clean
# 2–5-persona run stays byte-identical (silent, exit 0) to its pre-ruling output.
if [ "$warnings" -gt 0 ]; then
  printf 'lint-personas: 0 problem(s), %d warning(s) in %s (warnings are non-blocking — the lint PASSES)\n' \
    "$warnings" "$SSOT"
fi
exit 0
