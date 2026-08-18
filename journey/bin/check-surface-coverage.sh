#!/bin/sh
# shellcheck shell=sh
# check-surface-coverage.sh APP_FLOW TEST_SURFACE_FILE
#
# Deterministic surface-coverage gate (Increment 2). Re-derives the required
# screens DIRECTLY from APP_FLOW — the generator's output is never trusted
# for coverage:
#   * a screen is REQUIRED iff its route token appears in the steps of any
#     '## User Journeys' AFJ entry;
#   * every required screen must have a '## SURFACE: <name>' entry or a
#     VALID, unexpired '## SURFACE-GAP: <name>' (SURFACE_COVERAGE_GAP);
#   * every SURFACE entry must name a screen that exists in APP_FLOW
#     (INVENTED_SCREEN) and carry its exact APP_FLOW route (ROUTE_MISMATCH).
# Anti-vacuous: zero screens in APP_FLOW fails (NO_SCREENS).
# Deps: POSIX sh, awk, grep, sed, date.

set -u
_die() { printf '%s\n' "$*" >&2; exit 1; }

[ $# -eq 2 ] || _die "usage: check-surface-coverage.sh APP_FLOW TEST_SURFACE_FILE"
APP_FLOW="$1"; TS="$2"
[ -r "$APP_FLOW" ] || _die "check-surface-coverage: file not readable: $APP_FLOW"
[ -r "$TS" ]       || _die "check-surface-coverage: file not readable: $TS"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

problems=0
_p() { printf '%s\n' "$1"; problems=$((problems + 1)); }

# ── screens from APP_FLOW: "name<TAB>route" lines ─────────────────────────────
awk '
  /^## Screens/ { insc = 1; next }
  insc && /^## / { insc = 0; next }
  insc && /^### / {
    name = ""; if (match($0, /"[^"]+"/)) name = substr($0, RSTART + 1, RLENGTH - 2)
    cur = name; next
  }
  insc && cur != "" && /^route:/ {
    r = $0; sub(/^route:[ \t]*/, "", r); sub(/[ \t]+$/, "", r)
    printf "%s\t%s\n", cur, r; cur = ""
  }
' "$APP_FLOW" > "$_tmp/screens.tsv"

[ -s "$_tmp/screens.tsv" ] || \
  _die "NO_SCREENS: APP_FLOW has no '## Screens' section with routed '### SCR-<n> — \"<name>\"' entries (fail closed; see journey/docs/journey-gen-doc-format.md §3b)"

# ── journey steps text (all AFJ entries) ──────────────────────────────────────
awk '
  /^## User Journeys/ { uj = 1; next }
  uj && /^## /        { uj = 0 }
  uj                  { print }
' "$APP_FLOW" > "$_tmp/journeys.txt"

# required screens: route token appears in journey steps
: > "$_tmp/required.txt"
while IFS="$(printf '\t')" read -r _name _route; do
  [ -n "$_name" ] || continue
  if grep -qF "$_route" "$_tmp/journeys.txt"; then
    printf '%s\t%s\n' "$_name" "$_route" >> "$_tmp/required.txt"
  fi
done < "$_tmp/screens.tsv"

# ── surface entries: name + route; gap names with validity ────────────────────
awk '
  /^## SURFACE: /     { name = $0; sub(/^## SURFACE: */, "", name); sub(/[ \t]+$/, "", name); cur = name; print "S\t" name; next }
  /^## SURFACE-GAP: / { g = $0; sub(/^## SURFACE-GAP: */, "", g); sub(/[ \t]+$/, "", g); cur = ""; gap = g; print "G\t" g; next }
  /^## /              { cur = ""; gap = "" ; next }
  cur != "" && /^route:/ { r = $0; sub(/^route:[ \t]*/, "", r); sub(/[ \t]+$/, "", r); print "R\t" cur "\t" r }
  gap != "" && /^[[:space:]]+expires:/ { e = $0; sub(/^[[:space:]]*expires:[ \t]*"?/, "", e); sub(/"?[ \t]*$/, "", e); print "E\t" gap "\t" e }
' "$TS" > "$_tmp/surface.tsv"

_today=$(date +%Y-%m-%d) || _die "cannot get today's date (fail closed)"

# INVENTED_SCREEN + ROUTE_MISMATCH
grep '^S' "$_tmp/surface.tsv" | cut -f2 | while IFS= read -r _sname; do
  if ! cut -f1 "$_tmp/screens.tsv" | grep -qxF "$_sname"; then
    printf 'INVENTED_SCREEN: SURFACE %s does not exist in APP_FLOW ## Screens (the contract must describe design intent, not invention)\n' "$_sname" >> "$_tmp/viol.txt"
  fi
done
grep '^R' "$_tmp/surface.tsv" | while IFS="$(printf '\t')" read -r _tag _sname _sroute; do
  _want=$(awk -F'\t' -v n="$_sname" '$1 == n { print $2; exit }' "$_tmp/screens.tsv")
  if [ -n "$_want" ] && [ "$_sroute" != "$_want" ]; then
    printf 'ROUTE_MISMATCH: SURFACE %s route %s contradicts APP_FLOW route %s\n' "$_sname" "$_sroute" "$_want" >> "$_tmp/viol.txt"
  fi
done

# SURFACE_COVERAGE_GAP: every required screen has an entry or a valid gap
while IFS="$(printf '\t')" read -r _name _route; do
  [ -n "$_name" ] || continue
  if awk -F'\t' -v n="$_name" '$1 == "S" && $2 == n { found = 1 } END { exit !found }' "$_tmp/surface.tsv"; then
    continue
  fi
  _gexp=$(awk -F'\t' -v n="$_name" '$1 == "E" && $2 == n { print $3; exit }' "$_tmp/surface.tsv")
  if awk -F'\t' -v n="$_name" '$1 == "G" && $2 == n { found = 1 } END { exit !found }' "$_tmp/surface.tsv"; then
    case "$_gexp" in
      [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9])
        if [ "$_gexp" \< "$_today" ]; then
          printf 'SURFACE_COVERAGE_GAP: screen %s gap expired %s — an expired gap is not a coverage credit\n' "$_name" "$_gexp" >> "$_tmp/viol.txt"
        fi ;;
      *)
        printf 'SURFACE_COVERAGE_GAP: screen %s gap has no valid expires date\n' "$_name" >> "$_tmp/viol.txt" ;;
    esac
    continue
  fi
  printf 'SURFACE_COVERAGE_GAP: journey-touched screen %s (route %s) has no SURFACE entry and no structured gap\n' "$_name" "$_route" >> "$_tmp/viol.txt"
done < "$_tmp/required.txt"

if [ -s "$_tmp/viol.txt" ]; then
  cat "$_tmp/viol.txt"
  problems=$(wc -l < "$_tmp/viol.txt" | tr -d ' ')
fi

if [ "${problems:-0}" -gt 0 ]; then
  printf 'check-surface-coverage: %d problem(s) (fail closed)\n' "$problems"
  exit 1
fi
exit 0
