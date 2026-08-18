#!/bin/sh
# shellcheck shell=sh
# lint-test-surface.sh TEST_SURFACE_FILE
#
# Format lint for the frozen TEST_SURFACE contract (Increment 2, spec
# 2026-07-03). Blocks are `## SURFACE: <screen>` entries and
# `## SURFACE-GAP: <screen>` structured gaps.
#
# Per SURFACE block (all REQUIRED): route:, allowed_selectors: (>=1 entry),
# observable_states:, public_api:. Selector grammar is ONLY
#   role=<role>[name="<name>"]     (the [name=...] part optional)
#   testid=<id>
# CSS, XPath, and arbitrary locators are rejected (SELECTOR_GRAMMAR).
#
# Per SURFACE-GAP block: gap: with indented reason/owner/reviewer/expires/
# evidence, all non-blank; reason in the frozen enum; expires YYYY-MM-DD and
# not in the past (GAP_EXPIRED).
#
# Anti-vacuous: a surface with zero SURFACE blocks fails.
# Diagnostics to stdout (lint convention); exit 1 on any problem.
# Deps: POSIX sh, awk, grep, sed, date.

set -u
_die() { printf '%s\n' "$*" >&2; exit 1; }

[ $# -eq 1 ] || _die "usage: lint-test-surface.sh TEST_SURFACE_FILE"
TS="$1"
[ -r "$TS" ] || _die "lint-test-surface: file not readable: $TS"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

problems=0
_p() { printf '%s\n' "$1"; problems=$((problems + 1)); }

# ── split into per-block files ────────────────────────────────────────────────
awk -v out="$_tmp" '
  /^## SURFACE: /     { n++; name = $0; sub(/^## SURFACE: */, "", name); sub(/[ \t]+$/, "", name)
                        print name >> (out "/screens.txt")
                        f = out "/surface_" n ".txt"; print $0 > f; next }
  /^## SURFACE-GAP: / { g++; gname = $0; sub(/^## SURFACE-GAP: */, "", gname); sub(/[ \t]+$/, "", gname)
                        print gname >> (out "/gapnames.txt")
                        f = out "/gap_" g ".txt"; print $0 > f; next }
  /^## /              { f = "" ; next }
  f != ""             { print >> f }
' "$TS"

if [ ! -s "$_tmp/screens.txt" ]; then
  _p "NO_SURFACE_BLOCKS: no '## SURFACE: <screen>' block found — an empty surface is vacuous (fail closed)"
fi

# duplicate screens
if [ -s "$_tmp/screens.txt" ]; then
  for _dup in $(sort "$_tmp/screens.txt" | uniq -d); do
    _p "DUPLICATE_SCREEN: SURFACE '$_dup' appears more than once"
  done
fi

# ── per-SURFACE checks ────────────────────────────────────────────────────────
for _sf in "$_tmp"/surface_*.txt; do
  [ -f "$_sf" ] || continue
  _name=$(head -1 "$_sf" | sed 's/^## SURFACE: *//')

  for _k in route allowed_selectors observable_states public_api; do
    grep -qE "^${_k}:" "$_sf" || \
      _p "MISSING_KEY: SURFACE '$_name' has no '${_k}:' key"
  done

  _rt=$(grep -m1 '^route:' "$_sf" | sed 's/^route:[[:space:]]*//;s/[[:space:]]*$//')
  if grep -qE '^route:' "$_sf" && [ -z "$_rt" ]; then
    _p "MISSING_KEY: SURFACE '$_name' route: is blank"
  fi

  # selectors: the '  - ' lines after allowed_selectors: until next column-0 key
  awk '/^allowed_selectors:/ { insel = 1; next }
       /^[a-z_]+:/ && insel  { insel = 0 }
       insel && /^[[:space:]]*-[[:space:]]*/ {
         sub(/^[[:space:]]*-[[:space:]]*/, ""); sub(/[[:space:]]+$/, ""); print }
  ' "$_sf" > "$_tmp/sel.txt"

  if grep -qE '^allowed_selectors:' "$_sf" && [ ! -s "$_tmp/sel.txt" ]; then
    _p "MISSING_KEY: SURFACE '$_name' allowed_selectors has no entries"
  fi

  while IFS= read -r _sel; do
    [ -n "$_sel" ] || continue
    if ! printf '%s\n' "$_sel" | grep -qE '^(role=[a-z]+(\[name="[^"]+"\])?|testid=[A-Za-z0-9_-]+)$'; then
      _p "SELECTOR_GRAMMAR: SURFACE '$_name' selector not role=/testid= grammar: [$_sel] (CSS/XPath/arbitrary locators are rejected)"
    fi
  done < "$_tmp/sel.txt"
done

# ── per-GAP checks ────────────────────────────────────────────────────────────
_today=$(date +%Y-%m-%d) || _die "cannot get today's date (fail closed)"
for _gf in "$_tmp"/gap_*.txt; do
  [ -f "$_gf" ] || continue
  _gname=$(head -1 "$_gf" | sed 's/^## SURFACE-GAP: *//')

  grep -qE '^gap:' "$_gf" || _p "MALFORMED_GAP: SURFACE-GAP '$_gname' has no 'gap:' block"

  for _k in reason owner reviewer expires evidence; do
    _v=$(grep -m1 -E "^[[:space:]]+${_k}:" "$_gf" | sed "s/^[[:space:]]*${_k}:[[:space:]]*//;s/^\"//;s/\"[[:space:]]*$//;s/[[:space:]]*$//")
    if [ -z "$_v" ]; then
      _p "MALFORMED_GAP: SURFACE-GAP '$_gname' field '${_k}' missing or blank"
      continue
    fi
    case "$_k" in
      reason)
        case "$_v" in
          NOT_IMPLEMENTED|NON_UI_FLOW|EXTERNAL_SYSTEM|DOC_AMBIGUOUS) : ;;
          *) _p "MALFORMED_GAP: SURFACE-GAP '$_gname' reason '$_v' not in NOT_IMPLEMENTED|NON_UI_FLOW|EXTERNAL_SYSTEM|DOC_AMBIGUOUS" ;;
        esac ;;
      expires)
        case "$_v" in
          [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9])
            if [ "$_v" \< "$_today" ]; then
              _p "GAP_EXPIRED: SURFACE-GAP '$_gname' expired $_v (today: $_today) — an expired gap is not a coverage credit"
            fi ;;
          *) _p "MALFORMED_GAP: SURFACE-GAP '$_gname' expires '$_v' not YYYY-MM-DD" ;;
        esac ;;
    esac
  done
done

if [ "$problems" -gt 0 ]; then
  printf 'lint-test-surface: %d problem(s) in %s (fail closed)\n' "$problems" "$TS"
  exit 1
fi
exit 0
