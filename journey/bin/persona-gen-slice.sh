#!/bin/sh
# shellcheck shell=sh
# persona-gen-slice.sh SSOT PRD APP_FLOW OUT_DIR
#
# Deterministic (P0/P1 FEAT × persona) bundle slicer for persona-journey
# generation (Increment 3). One bundle per pair, containing ONLY:
#   * the FEAT block (oracle side) + its linked AFJ blocks (steps side);
#   * THAT persona's block — never another persona's;
#   * Generation Context (RUNNER, GAP_EXPIRY) + the inlined map schema;
#   * the frozen JOURNEY-CANDIDATE output shape.
#
# Relevance (spec §7): all personas are relevant to all P0/P1 FEATs unless a
# future field narrows it — the human prunes at promotion. Personas that
# declare '[none: <reason>]' misbehaviors are SKIPPED deterministically (a
# persona journey without owned misbehaviors cannot pass
# check-persona-journeys) and recorded in the manifest.
#
# Fail closed: zero personas / zero P0/P1 FEATs / zero AFJs / malformed docs
# (same rules as journey-gen-slice.sh). Unlinked FEATs get NO bundle and are
# recorded — never an invented journey. No source code ever enters a bundle.
# Deps: POSIX sh, awk, grep, sed, jq.

set -u
_die() { printf '%s\n' "$*" >&2; exit 1; }
_here=$(cd "$(dirname "$0")" && pwd)

[ $# -eq 4 ] || _die "usage: persona-gen-slice.sh SSOT PRD APP_FLOW OUT_DIR"
SSOT="$1"; PRD="$2"; APP_FLOW="$3"; OUTDIR="$4"
for _f in "$SSOT" "$PRD" "$APP_FLOW"; do
  [ -r "$_f" ] || _die "persona-gen-slice: file not readable: $_f"
done
mkdir -p "$OUTDIR/bundles" || _die "cannot create output dir: $OUTDIR/bundles"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

# personas must lint before slicing (schema is the contract)
sh "$_here/lint-personas.sh" "$SSOT" >/dev/null 2>&1 || \
  _die "persona-gen-slice: SSOT personas fail lint-personas.sh (fix the schema first; fail closed)"

_TEMPLATE="$_here/../JOURNEY_MAP.template.md"
[ -r "$_TEMPLATE" ] || _die "persona-gen-slice: template not readable: $_TEMPLATE (fail closed)"

_RUNNER_VAL=""
if [ -n "${JOURNEY_RUNNER:-}" ]; then
  _RUNNER_VAL=$(printf '%s' "$JOURNEY_RUNNER" | tr '[:upper:]' '[:lower:]')
  case "$_RUNNER_VAL" in
    playwright|maestro|appium|pty|http) : ;;
    stub) [ "${ALLOW_STUB_RUNNER:-}" = "1" ] || _die "persona-gen-slice: 'stub' runner requires ALLOW_STUB_RUNNER=1" ;;
    *) _die "persona-gen-slice: unknown JOURNEY_RUNNER '$JOURNEY_RUNNER' (allowed: playwright|maestro|appium|pty|http|stub)" ;;
  esac
fi
_GAP_EXPIRY=$(date -d "+30 days" +%Y-%m-%d 2>/dev/null) \
  || _GAP_EXPIRY=$(date -v+30d +%Y-%m-%d 2>/dev/null) \
  || _die "persona-gen-slice: cannot compute GAP_EXPIRY (fail closed)"

# ── personas: id, name, misbehavior-bearing blocks ────────────────────────────
awk -v out="$_tmp" '
  /^## Personas/ { inp = 1; next }
  inp && /^## /  { inp = 0; next }
  inp && /^### / {
    if (!match($0, /P[0-9]+/)) { cur = ""; next }
    id = substr($0, RSTART, RLENGTH)
    name = ""
    if (match($0, /"[^"]+"/)) name = substr($0, RSTART + 1, RLENGTH - 2)
    printf "%s\t%s\n", id, name >> (out "/personas.tsv")
    cur = out "/pblock_" id ".txt"
    print $0 > cur
    next
  }
  inp && cur != "" { print >> cur }
' "$SSOT"
[ -s "$_tmp/personas.tsv" ] || _die "NO_PERSONAS: no personas in the SSOT (fail closed)"

# ── FEAT blocks + link map (same fail-closed rules as journey-gen-slice) ──────
# Canonical feature-id grammar FEAT-([A-Z]+-)?[0-9]+ (check-doc-format.sh §1) —
# identical split to journey-gen-slice.sh, so plain and prefixed ids slice alike.
awk -v outdir="$_tmp" '
  /^## FEAT-([A-Z]+-)?[0-9]/ {
    if (id != "") close(outdir "/prd_" id ".txt")
    match($0, /FEAT-([A-Z]+-)?[0-9]+/); id = substr($0, RSTART, RLENGTH)
    print > (outdir "/prd_" id ".txt"); next
  }
  id != "" { print >> (outdir "/prd_" id ".txt") }
' "$PRD"

_p01=""
for _ff in "$_tmp"/prd_FEAT-*.txt; do
  [ -f "$_ff" ] || continue
  _fid=$(basename "$_ff" .txt | sed 's/^prd_//')
  _pri=$(awk '/^priority:/ { sub(/^priority:[ \t]+/, ""); sub(/[ \t]*#.*$/, ""); sub(/[ \t]+$/, ""); print; exit }' "$_ff")
  case "$_pri" in
    P0|P1) _p01="$_p01 $_fid" ;;
    P2|P3) : ;;
    "")    _die "PRD_PRIORITY_UNPARSEABLE: $_fid has no priority: field" ;;
    *)     _die "PRD_PRIORITY_UNPARSEABLE: $_fid priority not P0-P3: $_pri" ;;
  esac
done
[ -n "$_p01" ] || _die "NO_P01_FEATURES: zero P0/P1 FEATs — persona generation would be vacuous (fail closed)"

awk -v outdir="$_tmp" '
  /^## User Journeys/ { in_uj=1; next }
  in_uj && /^## /     { in_uj=0; id=""; next }
  in_uj && /^### / {
    if (id != "") close(outdir "/afj_" id ".txt")
    if (match($0, /AFJ-[0-9]+/)) { id = substr($0, RSTART, RLENGTH); print > (outdir "/afj_" id ".txt") }
    else { id = "" }
    next
  }
  in_uj && id != "" { print >> (outdir "/afj_" id ".txt") }
' "$APP_FLOW"
ls "$_tmp"/afj_AFJ-*.txt >/dev/null 2>&1 || \
  _die "APP_FLOW_NO_JOURNEYS: zero AFJ journeys — persona steps have no grounding (fail closed)"

# FEAT -> linked AFJs (covers_flows + covers_features back-links; blocks must exist)
_links_for() { # FEAT_ID -> newline AFJ ids
  _lf="$1"
  { awk '/^covers_flows:/ { sub(/^covers_flows:[ \t]+/, ""); sub(/[ \t]*#.*$/, ""); print; exit }' "$_tmp/prd_${_lf}.txt" \
      | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
    for _af in "$_tmp"/afj_AFJ-*.txt; do
      [ -f "$_af" ] || continue
      if grep -E '^covers_features:' "$_af" | grep -qE "(^|[^0-9A-Za-z-])${_lf}([^0-9]|\$)"; then
        basename "$_af" .txt | sed 's/^afj_//'
      fi
    done; } | awk 'NF' | sort -u
}

# ── emit (FEAT × misbehavior-bearing persona) bundles ─────────────────────────
_bundles_json="[]"; _skipped_json="[]"; _unlinked_json="[]"

while IFS="$(printf '\t')" read -r _pid _pname; do
  [ -n "$_pid" ] || continue
  # skip [none: ...] personas deterministically
  if grep -m1 -E '^known_misbehaviors:' "$_tmp/pblock_${_pid}.txt" | grep -q '\[none:'; then
    _skipped_json=$(printf '%s' "$_skipped_json" | jq --arg id "$_pid" \
      '. + [{persona:$id,reason:"declares no misbehaviors — cannot own a misbehavior step"}]')
    continue
  fi
  for _fid in $_p01; do
    _afjs=$(_links_for "$_fid")
    _valid=""
    for _aid in $_afjs; do
      [ -f "$_tmp/afj_${_aid}.txt" ] && _valid="$_valid $_aid"
    done
    if [ -z "$(printf '%s' "$_valid" | tr -d ' ')" ]; then
      _unlinked_json=$(printf '%s' "$_unlinked_json" | jq --arg id "$_fid" \
        '. + [{id:$id,reason:"no linked AFJ block — no faithful steps side; author a persona gap, never an invented journey"}] | unique')
      continue
    fi
    _low_f=$(printf '%s' "$_fid" | tr 'A-Z' 'a-z')
    _low_p=$(printf '%s' "$_pid" | tr 'A-Z' 'a-z')
    _brel="bundles/${_low_f}-${_low_p}.md"
    {
      printf '# Persona bundle: %s × %s — "%s"\n\n' "$_fid" "$_pid" "$_pname"
      printf '## PRD Source\n\n'
      cat "$_tmp/prd_${_fid}.txt"
      printf '\n## APP_FLOW Source\n\n'
      for _aid in $_valid; do cat "$_tmp/afj_${_aid}.txt"; printf '\n'; done
      printf '## Persona (THIS bundle persona ONLY — its misbehavior tokens are your entire allowance)\n\n'
      cat "$_tmp/pblock_${_pid}.txt"
      printf '\n## Generation Context\n\n'
      [ -n "$_RUNNER_VAL" ] && printf 'RUNNER: %s\n' "$_RUNNER_VAL"
      printf 'GAP_EXPIRY: %s\n' "$_GAP_EXPIRY"
      printf '\n## Schema (inlined from journey/JOURNEY_MAP.template.md)\n\n'
      cat "$_TEMPLATE"
    } > "$OUTDIR/$_brel"
    _bundles_json=$(printf '%s' "$_bundles_json" | jq \
      --arg f "$_fid" --arg p "$_pid" --arg path "$_brel" \
      '. + [{feat:$f,persona:$p,bundle_path:$path}]')
  done
done < "$_tmp/personas.tsv"

_count=$(printf '%s' "$_bundles_json" | jq 'length')
[ "$_count" -gt 0 ] || \
  _die "NO_BUNDLES: zero (FEAT × persona) bundles emitted (all personas skipped or all FEATs unlinked) — persona coverage must come from gaps or doc fixes (fail closed)"

jq -n --argjson bundles "$_bundles_json" --argjson skipped "$_skipped_json" \
      --argjson unlinked "$_unlinked_json" \
  '{bundles:$bundles,skipped_personas:$skipped,unlinked_features:$unlinked}' \
  > "$OUTDIR/persona-manifest.json"

exit 0
