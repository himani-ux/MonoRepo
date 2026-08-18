#!/bin/sh
# check-journey-coverage.sh PRD APP_FLOW GEN_MAP MANIFEST GAPS
#
# Deterministic coverage gate for doc-derived journey generation.
#
# Proves COMPLETENESS ONLY — coverage is accounting, not fidelity. It does NOT
# judge whether a generated journey is semantically faithful (that is the
# refuter's job). It proves that every required source anchor is either
# represented by a JOURNEY-ID or explicitly accounted for by a well-formed
# structured gap, and that the accounting cannot silently lie.
#
# Required source anchors (re-derived here directly from PRD/APP_FLOW using the
# SAME fail-closed rules as the slicer — the gate never trusts the slicer's
# bundle-manifest.json, so a "dangling"/"unlinked" record can never become a
# coverage credit):
#   * every P0/P1 FEAT-ID in the PRD               (P2/P3 are excluded)
#   * every AFJ-ID under `## User Journeys` in APP_FLOW
#
# Inputs
#   PRD        canonical PRD (FEAT blocks with `priority:` + optional links)
#   APP_FLOW   canonical APP_FLOW (`## User Journeys` with `### AFJ-<n>` headings)
#   GEN_MAP    JOURNEY_MAP.generated.md (the promotable artifact)
#   MANIFEST   JOURNEY_COVERAGE_MANIFEST.json (§5.2: per-journey covers/flows + _index)
#   GAPS       JOURNEY_COVERAGE_GAPS.md (§5.1: machine-parseable gap records)
#
# Gap-record expiry field (owner ruling 2026-07-14, item 2): `expires:` is the
# CANONICAL spelling; `expiry:` is accepted as a legacy synonym. Additive — no
# existing project is forced to rewrite a record. Neither present -> MALFORMED_GAP
# (reported as a missing `expires`). Both present with DIFFERENT values ->
# MALFORMED_GAP (ambiguous; no coverage credit). Both with the same value ->
# accepted (redundant, not ambiguous).
#
# Exit codes
#   0  every required FEAT-ID and AFJ-ID is journeyed or well-formed-gapped
#   1  fail closed — one or more diagnostics on stderr, each prefixed with a
#      stable token:
#        PRD_PRIORITY_UNPARSEABLE   FEAT priority missing / not P0-P3
#        APP_FLOW_UNIDDED           user-journey heading without an AFJ-id
#        MALFORMED_MANIFEST         MANIFEST is not evaluable JSON
#        COVERAGE_GAP               required id neither journeyed nor gapped
#        INVALID_SOURCE_ID          journey covers/flows an id absent from the docs
#        ORPHAN_JOURNEY             journey traces to no valid source id
#        MALFORMED_GAP              gap record missing a required §5.1 field
#        DOC_FORMAT_GAP             a DOC_FORMAT diagnostic logged as a gap
#        AMBIGUOUS_GAP              one source id in more than one gap record
#        JOURNEYED_AND_GAPPED       id both covered by a journey and gapped
#        INDEX_INCONSISTENT         _index disagrees with the forward mapping
#        MAP_MANIFEST_MISMATCH      GEN_MAP and MANIFEST disagree on which journeys exist
#
# Dependencies: POSIX sh, awk, jq
# shellcheck shell=sh

set -u

_here=$(dirname "$0")

_emit() { printf '%s\n' "$*" >&2; }
_die()  { _emit "$*"; exit 1; }

[ $# -eq 5 ] || _die "Usage: check-journey-coverage.sh PRD APP_FLOW GEN_MAP MANIFEST GAPS"
PRD="$1"; APP_FLOW="$2"; GEN_MAP="$3"; MANIFEST="$4"; GAPS="$5"

for _f in "$PRD" "$APP_FLOW" "$GEN_MAP" "$MANIFEST" "$GAPS"; do
  [ -r "$_f" ] || _die "check-journey-coverage: file not readable: $_f"
done

command -v jq >/dev/null 2>&1 || _die "check-journey-coverage: jq not found (fail closed)"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

# ──────────────────────────────────────────────────────────────────────────────
# 1. Authoritative FEAT anchors from the PRD (fail closed on unparseable priority)
#    Same block-split + priority rule as journey-gen-slice.sh.
#
#    The anchor regex is the framework's CANONICAL feature-id grammar,
#    FEAT-([A-Z]+-)?[0-9]+ (check-doc-format.sh §1). A narrower ^## FEAT-[0-9]
#    anchor derived ZERO anchors from a PRD of PREFIXED ids (FEAT-AUD-101):
#    $FA came back empty, so every real journey's covers turned into
#    INVALID_SOURCE_ID "not a FEAT-ID in PRD" — the gate accusing the PRD of
#    the gate's own blindness.
# ──────────────────────────────────────────────────────────────────────────────
awk -v out="$_tmp" '
  /^## FEAT-([A-Z]+-)?[0-9]/ {
    if (id != "") close(out "/prd_" id ".txt")
    match($0, /FEAT-([A-Z]+-)?[0-9]+/); id = substr($0, RSTART, RLENGTH)
    print id >> (out "/feat_all.txt")
    print $0 > (out "/prd_" id ".txt")
    next
  }
  id != "" { print >> (out "/prd_" id ".txt") }
' "$PRD"

: > "$_tmp/feat_req.txt"
if [ -f "$_tmp/feat_all.txt" ]; then
  while IFS= read -r _fid; do
    [ -z "$_fid" ] && continue
    _pri=$(awk '/^priority:/ {
      sub(/^priority:[ \t]+/, ""); sub(/[ \t]*#.*$/, ""); sub(/[ \t]+$/, "")
      print; exit
    }' "$_tmp/prd_${_fid}.txt")
    case "$_pri" in
      P0|P1) printf '%s\n' "$_fid" >> "$_tmp/feat_req.txt" ;;
      P2|P3) : ;;
      "")    _die "PRD_PRIORITY_UNPARSEABLE: $_fid has no priority: field" ;;
      *)     _die "PRD_PRIORITY_UNPARSEABLE: $_fid priority not P0-P3: $_pri" ;;
    esac
  done < "$_tmp/feat_all.txt"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 2. Authoritative AFJ anchors from APP_FLOW (fail closed on un-id'd heading)
# ──────────────────────────────────────────────────────────────────────────────
awk -v out="$_tmp" '
  /^## User Journeys/ { in_uj=1; next }
  in_uj && /^## /     { in_uj=0; next }
  in_uj && /^### / {
    if (match($0, /AFJ-[0-9]+/)) print substr($0, RSTART, RLENGTH) >> (out "/afj_all.txt")
    else print $0 >> (out "/afj_err.txt")
    next
  }
' "$APP_FLOW"

[ -f "$_tmp/afj_err.txt" ] && \
  _die "APP_FLOW_UNIDDED: journey heading without AFJ-ID: $(cat "$_tmp/afj_err.txt")"

# Anti-vacuous (review C4): an empty anchor universe makes every requirement
# vacuously satisfied (nothing required → nothing violated → exit 0). That is
# a doc-format failure, not a coverage pass.
if [ ! -s "$_tmp/feat_req.txt" ] && [ ! -s "$_tmp/afj_all.txt" ]; then
  _die "NO_ANCHORS: zero required FEAT anchors and zero AFJ anchors derived from PRD/APP_FLOW — coverage would be vacuous (fail closed; see journey/docs/journey-gen-doc-format.md)"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 3. GEN_MAP journey-id set (reuse the Increment-1 block parser)
# ──────────────────────────────────────────────────────────────────────────────
JOURNEY_MAP="$GEN_MAP"
# shellcheck disable=SC1090
. "$_here/../lib/journey-lib.sh"
journey_ids > "$_tmp/map_journeys.txt"

# ──────────────────────────────────────────────────────────────────────────────
# 4. Marshal inputs into JSON for the reconciliation pass
# ──────────────────────────────────────────────────────────────────────────────
_json_array() { # FILE -> JSON array of non-blank lines
  if [ -f "$1" ]; then jq -Rn '[inputs | select(length > 0)]' < "$1"; else printf '[]'; fi
}
_feat_all=$(_json_array "$_tmp/feat_all.txt")
_feat_req=$(_json_array "$_tmp/feat_req.txt")
_afj_all=$(_json_array "$_tmp/afj_all.txt")
_map_j=$(_json_array "$_tmp/map_journeys.txt")

# Gap records: emit (idx, key, value) TSV, then fold into JSON objects. Building
# JSON via jq -R sidesteps escaping. A new record begins at each `source_id:`.
# `expires:` is CANONICAL; `expiry:` is the accepted LEGACY spelling (owner
# ruling 2026-07-14, item 2). This gate used to read ONLY `expiry:` while
# check-persona-coverage.sh read ONLY `expires:` — the two gates disagreed about
# the shape of the same record type, and the rest of the framework (persona,
# extraction, surface and mock coverage; quality waivers; Step 1/Step 2) had
# long since settled on `expires:`. Both are captured here; the resolution, the
# conflict rule and the missing-field report are in the jq pass below.
awk '
  /^[ \t]*source_id:/ { idx++ }
  /^[ \t]*(source_id|source_type|reason|owner|expiry|expires|reviewer):/ {
    match($0, /[a-z_]+:/)
    key = substr($0, RSTART, RLENGTH - 1)
    val = substr($0, RSTART + RLENGTH)
    sub(/^[ \t]+/, "", val); sub(/[ \t]+$/, "", val)
    printf "%d\t%s\t%s\n", idx, key, val
  }
' "$GAPS" > "$_tmp/gaps.tsv"

_gaps=$(jq -Rn '
  [ inputs | split("\t") | { idx: .[0], key: .[1], val: (.[2] // "") } ]
  | group_by(.idx)
  | map( reduce .[] as $f ({}; .[$f.key] = $f.val) )
' < "$_tmp/gaps.tsv")

# ──────────────────────────────────────────────────────────────────────────────
# 5. Reconcile — one jq pass emits every violation as a token-prefixed line.
#    Coverage is derived from the per-journey forward mapping (covers/flows), so
#    a mendacious _index cannot fabricate coverage; _index is then cross-checked
#    against the derived truth (INDEX_INCONSISTENT) to keep the accounting honest.
# ──────────────────────────────────────────────────────────────────────────────
jq -r \
  --argjson gaps    "$_gaps" \
  --argjson featReq "$_feat_req" \
  --argjson featAll "$_feat_all" \
  --argjson afjAll  "$_afj_all" \
  --argjson mapJ    "$_map_j" '
  # membership of the current element in $set (bind first — a bare `index(.)`
  # after a pipe would rebind `.` to $set and match the array against itself).
  def inset($set): . as $x | ($set | index($x)) != null;
  . as $m
  | ($m._index // {}) as $index
  # The expiry field is validated separately (canonical `expires:`, legacy
  # `expiry:`), so it is not in this always-required list.
  | ["source_id","source_type","reason","owner","reviewer"] as $REQ
  | ($featAll | unique) as $FA
  | ($featReq | unique) as $FR
  | ($afjAll  | unique) as $AA

  # journeys accounted for in the coverage manifest
  | [ $m | to_entries[] | select(.key | test("^JOURNEY-[0-9]+$"))
      | { name: .key, covers: (.value.covers // []), flows: (.value.flows // []) } ] as $J
  | [ $J[].name ] as $Jnames

  # gap records, classified for well-formedness and duplicates.
  #
  # Expiry: `expires:` is canonical, `expiry:` is the accepted legacy spelling.
  # Compatibility is ADDITIVE — an existing project is never forced to rewrite a
  # record. A record with NEITHER spelling is still missing a required field
  # (reported under the canonical name). A record carrying BOTH with DIFFERENT
  # values is ambiguous — one record cannot expire on two dates — so it fails
  # closed and grants NO coverage credit. Both with the SAME value is merely
  # redundant, not ambiguous, and is accepted.
  | [ $gaps[]
      | ( (.expires // "") | tostring | gsub("^[ \t]+|[ \t]+$"; "") ) as $exs
      | ( (.expiry  // "") | tostring | gsub("^[ \t]+|[ \t]+$"; "") ) as $exy
      | {
          sid:   (.source_id // ""),
          stype: (.source_type // ""),
          exs:   $exs,
          exy:   $exy,
          missing: ( [ $REQ[] as $k
                       | select( ((.[$k] // "") | tostring | gsub("^[ \t]+|[ \t]+$"; "")) == "" ) | $k ]
                     + (if ($exs == "" and $exy == "") then ["expires"] else [] end) ),
          conflict: ($exs != "" and $exy != "" and $exs != $exy)
        } ] as $Graw
  # A conflicting record is NOT well-formed: it cannot become a coverage credit.
  | [ $Graw[] | select((.missing | length == 0) and (.conflict | not)) ] as $Gwell
  | [ $Gwell[] | select(.stype == "FEAT" or .stype == "AFJ") | .sid ] as $GapIds
  | ( $Graw | group_by(.sid) | map(select(length > 1) | .[0].sid) ) as $DupGapIds

  # derived reverse index: valid source id -> [journey names]
  | ( reduce $J[] as $j ({};
        reduce ($j.covers[] | select( inset($FA) )) as $c (.; .[$c] = ((.[$c] // []) + [$j.name]))
        | reduce ($j.flows[] | select( inset($AA) )) as $f (.; .[$f] = ((.[$f] // []) + [$j.name]))
      ) ) as $covBy

  | [
      # ---- per-journey: invalid source ids + orphan ----
      ( $J[] | . as $j
        | ( $j.covers[] | select( inset($FA) | not )
            | "INVALID_SOURCE_ID: \($j.name) covers \(.) (not a FEAT-ID in PRD)" ),
          ( $j.flows[] | select( inset($AA) | not )
            | "INVALID_SOURCE_ID: \($j.name) flows \(.) (not an AFJ-ID in APP_FLOW)" ),
          ( select( ( [ $j.covers[] | select(inset($FA)) ]
                     + [ $j.flows[]  | select(inset($AA)) ] | length ) == 0 )
            | "ORPHAN_JOURNEY: \($j.name) references no valid source id" )
      ),

      # ---- GEN_MAP <-> MANIFEST journey-id set reconciliation ----
      ( $mapJ[]   | select( inset($Jnames) | not )
        | "MAP_MANIFEST_MISMATCH: \(.) is in JOURNEY_MAP but absent from the coverage manifest" ),
      ( $Jnames[] | select( inset($mapJ) | not )
        | "MAP_MANIFEST_MISMATCH: \(.) is in the coverage manifest but absent from JOURNEY_MAP" ),

      # ---- gap integrity ----
      ( $Graw[] | select(.missing | length > 0)
        | "MALFORMED_GAP: \(if .sid == "" then "<no source_id>" else .sid end) missing field(s): \(.missing | join(", "))" ),
      ( $Graw[] | select(.conflict)
        | "MALFORMED_GAP: \(if .sid == "" then "<no source_id>" else .sid end) carries conflicting expires: \"\(.exs)\" and expiry: \"\(.exy)\" — one record cannot expire on two dates (expires: is the canonical spelling)" ),
      ( $Graw[] | select(.stype == "DOC_FORMAT")
        | "DOC_FORMAT_GAP: \(.sid) is a blocking document-format diagnostic, not a coverage credit" ),
      ( $DupGapIds[] | "AMBIGUOUS_GAP: \(.) appears in more than one gap record" ),

      # ---- required coverage (both axes) + journeyed-and-gapped contradiction ----
      ( $FR[] | . as $id
        | ( select( (($covBy[$id] // []) | length == 0) and (($GapIds | index($id)) == null) )
            | "COVERAGE_GAP: FEAT \($id) (P0/P1) has neither a JOURNEY-ID nor a well-formed structured gap" ),
          ( select( (($covBy[$id] // []) | length > 0) and (($GapIds | index($id)) != null) )
            | "JOURNEYED_AND_GAPPED: FEAT \($id) is both covered by a journey and logged as a gap" )
      ),
      ( $AA[] | . as $id
        | ( select( (($covBy[$id] // []) | length == 0) and (($GapIds | index($id)) == null) )
            | "COVERAGE_GAP: AFJ \($id) has neither a JOURNEY-ID nor a well-formed structured gap" ),
          ( select( (($covBy[$id] // []) | length > 0) and (($GapIds | index($id)) != null) )
            | "JOURNEYED_AND_GAPPED: AFJ \($id) is both covered by a journey and logged as a gap" )
      ),

      # ---- _index reconciliation (accounting integrity / determinism) ----
      ( ( [ $FR[], $AA[], $GapIds[], ($covBy | keys[]), ($index | keys[]) ] | unique )[] | . as $id
        | ( ($covBy[$id] // []) | unique | sort ) as $dj
        | ( ($index[$id].journeys // []) | unique | sort ) as $pj
        | ( ($GapIds | index($id)) != null ) as $dg
        | ( ($index[$id].gap // null) != null ) as $pg
        | ( select($dj != $pj)
            | "INDEX_INCONSISTENT: _index[\($id)].journeys \($pj) disagrees with the journeys that cover it \($dj)" ),
          ( select($dg != $pg)
            | "INDEX_INCONSISTENT: _index[\($id)].gap presence (\($pg)) disagrees with the well-formed gap set (\($dg))" )
      )
    ][]
' "$MANIFEST" > "$_tmp/viol.txt" 2>"$_tmp/jqerr.txt"

if [ $? -ne 0 ]; then
  _die "MALFORMED_MANIFEST: cannot evaluate coverage over $MANIFEST: $(cat "$_tmp/jqerr.txt")"
fi

if [ -s "$_tmp/viol.txt" ]; then
  while IFS= read -r _line; do _emit "$_line"; done < "$_tmp/viol.txt"
  exit 1
fi

exit 0
