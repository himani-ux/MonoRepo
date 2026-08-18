#!/bin/sh
# shellcheck shell=sh
# check-persona-journeys.sh JOURNEY_MAP SSOT
#
# Misbehavior-ownership gate (Increment 3 — the core invariant). For every
# `origin: PERSONA` journey in the map:
#   * the named persona must exist in the SSOT (UNDEFINED_PERSONA), with the
#     exact 'P<n> (<name>)' form matching the SSOT block;
#   * at least one step must carry '(misbehavior: <token>)'
#     (NO_MISBEHAVIOR_STEP — a persona journey without its persona's mistakes
#     is a happy path in costume);
#   * every annotated token must belong to THAT persona's known_misbehaviors
#     (FOREIGN_MISBEHAVIOR).
# Non-PERSONA journeys are ignored. PERSONA journeys model USER BEHAVIOR, not
# tested behavior — nothing here reads or writes runtime truth.
# Deps: POSIX sh, awk, grep, sed.

set -u
_die() { printf '%s\n' "$*" >&2; exit 1; }
_here=$(cd "$(dirname "$0")" && pwd)

[ $# -eq 2 ] || _die "usage: check-persona-journeys.sh JOURNEY_MAP SSOT"
MAP="$1"; SSOT="$2"
[ -r "$MAP" ]  || _die "check-persona-journeys: file not readable: $MAP"
[ -r "$SSOT" ] || _die "check-persona-journeys: file not readable: $SSOT"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

problems=0
_p() { printf '%s\n' "$1"; problems=$((problems + 1)); }

# ── persona index from the SSOT: "P<n>\t<name>" + per-persona token files ─────
awk -v out="$_tmp" '
  /^## Personas/ { inp = 1; next }
  inp && /^## /  { inp = 0; next }
  inp && /^### / {
    line = $0
    if (!match(line, /P[0-9]+/)) { cur = ""; next }
    id = substr(line, RSTART, RLENGTH)
    name = ""
    if (match(line, /"[^"]+"/)) name = substr(line, RSTART + 1, RLENGTH - 2)
    printf "%s\t%s\n", id, name >> (out "/personas.tsv")
    cur = id; inm = 0; next
  }
  inp && cur != "" && /^known_misbehaviors:/ { inm = 1; next }
  inp && cur != "" && /^[a-z_]+:/            { inm = 0 }
  inp && cur != "" && inm && /^[[:space:]]*-[[:space:]]*/ {
    t = $0; sub(/^[[:space:]]*-[[:space:]]*/, "", t); sub(/[[:space:]]+$/, "", t)
    print t >> (out "/tokens_" cur ".txt")
  }
' "$SSOT"

# ── per-journey checks ────────────────────────────────────────────────────────
JOURNEY_MAP="$MAP"; export JOURNEY_MAP
# shellcheck disable=SC1090
. "$_here/../lib/journey-lib.sh"

for _jid in $(journey_ids | sort -u); do
  _org=$(journey_field "$_jid" origin 2>/dev/null) || _org=""
  [ "$_org" = "PERSONA" ] || continue

  _pfield=$(journey_field "$_jid" persona 2>/dev/null) || _pfield=""
  _pid=$(printf '%s' "$_pfield" | grep -oE '^P[0-9]+') || _pid=""
  _pname=$(printf '%s' "$_pfield" | sed -n 's/^P[0-9]*[[:space:]]*(\(.*\))$/\1/p')

  _want_name=$(awk -F'\t' -v id="$_pid" '$1 == id { print $2; exit }' "$_tmp/personas.tsv" 2>/dev/null)
  if [ -z "$_pid" ] || [ -z "$_want_name" ]; then
    _p "UNDEFINED_PERSONA: $_jid persona '$_pfield' does not name a defined SSOT persona (P<n> (<name>))"
    continue
  fi
  if [ "$_pname" != "$_want_name" ]; then
    _p "UNDEFINED_PERSONA: $_jid persona name '($_pname)' does not match SSOT $_pid (\"$_want_name\") — transfer verbatim"
    continue
  fi

  journey_block "$_jid" | awk '/^steps:/ { s = 1; next } s && /^[a-z_]+:/ { s = 0 } s { print }' \
    > "$_tmp/steps.txt"
  grep -oE '\(misbehavior: [a-z0-9-]+\)' "$_tmp/steps.txt" \
    | sed 's/(misbehavior: //;s/)//' > "$_tmp/used.txt" || true

  if [ ! -s "$_tmp/used.txt" ]; then
    _p "NO_MISBEHAVIOR_STEP: $_jid has no step annotated '(misbehavior: <token>)' — a persona journey without its persona's mistakes is a happy path in costume (fail closed)"
    continue
  fi
  while IFS= read -r _tok; do
    [ -n "$_tok" ] || continue
    grep -qxF "$_tok" "$_tmp/tokens_${_pid}.txt" 2>/dev/null || \
      _p "FOREIGN_MISBEHAVIOR: $_jid step uses '(misbehavior: $_tok)' but $_pid (\"$_want_name\") does not own that token"
  done < "$_tmp/used.txt"
done

if [ "$problems" -gt 0 ]; then
  printf 'check-persona-journeys: %d problem(s) (fail closed)\n' "$problems"
  exit 1
fi
exit 0
