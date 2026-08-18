#!/bin/sh
# shellcheck shell=sh
# check-journey-provenance.sh PRD APP_FLOW GEN_MAP MANIFEST [SSOT]
#
# Deterministic PROVENANCE gate (post-merge review, highest-leverage rec).
# The coverage gate proves accounting; this gate proves the manifest's own
# provenance claims are VERBATIM TRUE. Where transfer is verbatim,
# verification is string equality — no model involved.
#
# Checks (all violations accumulated; exit 1 if any):
#   QUOTE_UNGROUNDED   — a field_sources quote does not appear verbatim in the
#                        doc its `from` names. Quotes may elide with " ... "
#                        and join criteria with "; "; every fragment must be a
#                        byte-substring (whitespace-normalized) of the doc.
#   AC_DROPPED         — an AC-<n> declared by a covered FEAT in the PRD is
#                        absent from that journey's oracle manifest entry
#                        (ref + quote). This catches oracle dilution
#                        deterministically — previously refuter-only.
#   MISSING_PROVENANCE — a GEN_MAP journey with no manifest field_sources, or
#                        an oracle/goal/steps entry without a quote (a
#                        negative_states entry may omit its quote ONLY when
#                        generated_minimal is true).
#   BAD_SOURCE         — `from` names an unknown doc.
#   UNVERIFIABLE_SOURCE— `from: SSOT` quote present but no SSOT was provided
#                        (cannot verify ⇒ fail closed).
#
# Prints NOTHING on success. Violations go to stderr.
# Deps: POSIX sh, awk, sed, tr, grep, jq (1.5+).

set -u
_SELF="$0"
_die() { printf '%s: %s\n' "$_SELF" "$1" >&2; exit 1; }

[ $# -eq 4 ] || [ $# -eq 5 ] || \
  _die "usage: check-journey-provenance.sh PRD APP_FLOW GEN_MAP MANIFEST [SSOT]"

PRD="$1"; APP_FLOW="$2"; GEN_MAP="$3"; MANIFEST="$4"; SSOT="${5:-}"

for _f in "$PRD" "$APP_FLOW" "$GEN_MAP" "$MANIFEST"; do
  [ -r "$_f" ] || _die "input not readable: $_f (fail closed)"
done
[ -z "$SSOT" ] || [ -r "$SSOT" ] || _die "SSOT not readable: $SSOT (fail closed)"
command -v jq >/dev/null 2>&1 || _die "jq not found (fail closed)"
jq -e . "$MANIFEST" >/dev/null 2>&1 || _die "manifest is not valid JSON: $MANIFEST (fail closed)"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

_violations=0
_viol() { printf '%s\n' "$1" >&2; _violations=$((_violations + 1)); }

# ── whitespace-normalized doc contents ────────────────────────────────────────
_norm() { tr '\n' ' ' < "$1" | tr -s '[:space:]' ' '; }
_PRD_N=$(_norm "$PRD")
_AFW_N=$(_norm "$APP_FLOW")
_SSOT_N=""; [ -n "$SSOT" ] && _SSOT_N=$(_norm "$SSOT")

# ── declared ACs per FEAT block from the PRD ──────────────────────────────────
# Canonical feature-id grammar FEAT-([A-Z]+-)?[0-9]+ (check-doc-format.sh §1):
# a prefixed id (FEAT-AUD-101) must find its own AC block, not fall through and
# silently attribute its ACs to the previous plain-id FEAT.
awk -v out="$_tmp" '
  /^## FEAT-([A-Z]+-)?[0-9]/ {
    match($0, /FEAT-([A-Z]+-)?[0-9]+/); id = substr($0, RSTART, RLENGTH); next
  }
  id != "" && /^[[:space:]]*-[[:space:]]*AC-[0-9]+:/ {
    match($0, /AC-[0-9]+/); print substr($0, RSTART, RLENGTH) >> (out "/ac_" id ".txt")
  }
' "$PRD"

# ── journey ids in the candidate map ──────────────────────────────────────────
JOURNEY_MAP="$GEN_MAP"; export JOURNEY_MAP
_here=$(cd "$(dirname "$0")" && pwd)
# shellcheck disable=SC1090
. "$_here/../lib/journey-lib.sh"
journey_ids | sort -u > "$_tmp/map_ids.txt"

# ── per-journey checks ────────────────────────────────────────────────────────
while IFS= read -r _jid; do
  [ -n "$_jid" ] || continue

  if ! jq -e --arg j "$_jid" '.[$j].field_sources' "$MANIFEST" >/dev/null 2>&1; then
    _viol "MISSING_PROVENANCE: $_jid has no field_sources entry in the manifest"
    continue
  fi

  # quote grounding for every field_sources entry
  for _fld in $(jq -r --arg j "$_jid" '.[$j].field_sources | keys[]' "$MANIFEST"); do
    _from=$(jq -r --arg j "$_jid" --arg f "$_fld" '.[$j].field_sources[$f].from // empty' "$MANIFEST")
    _quote=$(jq -r --arg j "$_jid" --arg f "$_fld" '.[$j].field_sources[$f].quote // empty' "$MANIFEST")
    _genmin=$(jq -r --arg j "$_jid" --arg f "$_fld" '.[$j].field_sources[$f].generated_minimal // false' "$MANIFEST")

    if [ -z "$_quote" ]; then
      case "$_fld" in
        oracle|goal|steps)
          _viol "MISSING_PROVENANCE: $_jid field '$_fld' has no verbatim quote" ;;
        negative_states)
          [ "$_genmin" = "true" ] || \
            _viol "MISSING_PROVENANCE: $_jid negative_states has no quote and is not generated_minimal" ;;
        *) : ;;  # ref-only entries (e.g. persona) are allowed
      esac
      continue
    fi

    case "$_from" in
      PRD)      _doc="$_PRD_N" ;;
      APP_FLOW) _doc="$_AFW_N" ;;
      SSOT)
        if [ -z "$SSOT" ]; then
          _viol "UNVERIFIABLE_SOURCE: $_jid field '$_fld' quotes SSOT but no SSOT was provided (fail closed)"
          continue
        fi
        _doc="$_SSOT_N" ;;
      "")
        _viol "BAD_SOURCE: $_jid field '$_fld' has a quote but no 'from' doc"
        continue ;;
      *)
        _viol "BAD_SOURCE: $_jid field '$_fld' names unknown source doc '$_from'"
        continue ;;
    esac

    # fragment-wise verbatim check: " ... " elision and "; " joins split the
    # quote; every fragment must appear (whitespace-normalized) in the doc.
    printf '%s\n' "$_quote" | sed 's/ \.\.\. /\
/g; s/; /\
/g' | while IFS= read -r _frag; do
      _frag=$(printf '%s' "$_frag" | tr -s '[:space:]' ' ' | sed 's/^ //;s/ $//')
      [ -n "$_frag" ] || continue
      case "$_doc" in
        *"$_frag"*) : ;;
        *) printf 'QUOTE_UNGROUNDED: %s field %s — fragment not verbatim in %s: [%s]\n' \
             "$_jid" "$_fld" "$_from" "$_frag" >> "$_tmp/frag_viol.txt" ;;
      esac
    done
  done

  # AC accounting: every AC declared by a covered FEAT must appear in this
  # journey's oracle manifest entry (ref or quote)
  _oracle_entry=$(jq -r --arg j "$_jid" \
    '(.[$j].field_sources.oracle.ref // "") + " " + (.[$j].field_sources.oracle.quote // "")' "$MANIFEST")
  for _feat in $(jq -r --arg j "$_jid" '.[$j].covers[]? // empty' "$MANIFEST"); do
    [ -f "$_tmp/ac_${_feat}.txt" ] || continue  # unknown FEAT ids are the coverage gate's job
    while IFS= read -r _ac; do
      [ -n "$_ac" ] || continue
      printf '%s' "$_oracle_entry" | grep -qE "${_ac}([^0-9]|\$)" || \
        _viol "AC_DROPPED: $_jid oracle entry does not represent $_feat $_ac (oracle dilution — declared in the PRD, absent from ref+quote)"
    done < "$_tmp/ac_${_feat}.txt"
  done
done < "$_tmp/map_ids.txt"

# fragment violations were collected in a subshell; fold them in here
if [ -s "$_tmp/frag_viol.txt" ]; then
  while IFS= read -r _v; do _viol "$_v"; done < "$_tmp/frag_viol.txt"
fi

if [ "$_violations" -gt 0 ]; then
  printf 'check-journey-provenance: %d violation(s) — provenance is NOT verbatim-true (fail closed)\n' \
    "$_violations" >&2
  exit 1
fi
exit 0
