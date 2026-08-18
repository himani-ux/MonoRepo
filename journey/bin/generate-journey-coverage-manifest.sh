#!/bin/sh
# shellcheck shell=sh
# generate-journey-coverage-manifest.sh PRD APP_FLOW JOURNEY_MAP GAPS [--check MANIFEST]
#
# DETERMINISTIC producer for JOURNEY_COVERAGE_MANIFEST.json (owner ruling
# 2026-07-14, item 3).
#
# The manifest is GENERATED EVIDENCE, not a manually authored SSOT. Before this
# script existed the only thing that could write it was an LLM merge backend
# (journey-gen-split.sh materialises whatever the model emitted), which means a
# project with a hand-authored journey map had no way to obtain one except to
# TYPE IT — and a hand-typed coverage manifest is just a claim about coverage
# wearing the costume of evidence. Anything a human can type to make a gate pass
# is not evidence. This script derives the manifest, and only the drift check
# (below) may bless a committed copy.
#
# ── Derivation: canonical machine-readable anchors ONLY ──────────────────────
#   FEAT ids      `## FEAT-<n>` blocks in the PRD, canonical grammar
#                 FEAT-([A-Z]+-)?[0-9]+ — plain (FEAT-001) and prefixed
#                 (FEAT-AUD-101) are both first-class. `priority:` selects the
#                 REQUIRED set (P0/P1).
#   AFJ ids       `### AFJ-<n>` headings under `## User Journeys` in APP_FLOW.
#   coverage      the `covers:` / `flows:` fields of the JOURNEY_MAP's journey
#                 blocks — the journey layer's own declaration of what it covers.
#   gaps          formally recorded coverage-gap records in GAPS.
#
# NOTHING ELSE. In particular the producer does NOT infer a journey<->AFJ
# mapping from any structural coincidence (e.g. matching covers sets, or equal
# ordinals). A journey covers an AFJ when its `flows:` field SAYS SO. Inferring
# the mapping would let the framework manufacture coverage the project never
# declared — a false green dressed up as automation. If `flows:` is empty, the
# AFJs are uncovered, and the gate must say so.
#
# ── Determinism ─────────────────────────────────────────────────────────────
# Identical inputs => BYTE-IDENTICAL output. Stable key order (jq -S), stable
# array order (every array sorted + deduped), fixed 2-space indent, single
# trailing newline. NO timestamps, hostnames, paths, usernames, locale- or
# environment-dependent values are ever emitted.
#
# ── Fail closed ─────────────────────────────────────────────────────────────
# The producer REFUSES to emit rather than emit something a gate would swallow:
#   MISSING_SOURCE          a required input file is unreadable
#   PRD_PRIORITY_UNPARSEABLE  a FEAT block has no / a non-P0-P3 priority
#   APP_FLOW_UNIDDED        a user-journey heading carries no AFJ-id
#   NO_ANCHORS              zero required FEAT anchors and zero AFJ anchors
#   DUPLICATE_JOURNEY_ID    the same JOURNEY-id declared twice
#   INVALID_SOURCE_ID       a journey covers/flows an id absent from the docs
#                           (a feature mapping to an unknown journey, and the
#                           mirror case: a journey mapping to an unknown anchor)
#   MALFORMED_GAP           a gap record missing a required field, or carrying
#                           conflicting expires:/expiry: dates
#   AMBIGUOUS_GAP           one source id in more than one gap record
#   DOC_FORMAT_GAP          a blocking doc-format diagnostic logged as a gap
#   MANIFEST_STALE          (--check) the committed manifest differs from the
#                           regenerated one
#
# ── Modes ───────────────────────────────────────────────────────────────────
#   (default)          write the manifest to stdout
#   --check MANIFEST   DRIFT CHECK: regenerate, compare byte-for-byte against
#                      the committed MANIFEST, exit 1 (MANIFEST_STALE) on any
#                      difference. CI order: generate-or-drift-check FIRST, then
#                      check-journey-coverage.sh against the VERIFIED manifest —
#                      a coverage gate run against a stale manifest proves
#                      nothing about the code that was actually committed.
#
# Gap-record expiry: `expires:` canonical, `expiry:` legacy — identical rule to
# check-journey-coverage.sh (owner ruling 2026-07-14, item 2).
#
# Deps: POSIX sh, awk, jq, sort.

set -u

_here=$(dirname "$0")
_emit() { printf '%s\n' "$*" >&2; }
_die()  { _emit "$*"; exit 1; }

MODE=generate
COMMITTED=""
if [ $# -eq 6 ] && [ "$5" = "--check" ]; then
  MODE=check; COMMITTED="$6"
elif [ $# -ne 4 ]; then
  _die "usage: generate-journey-coverage-manifest.sh PRD APP_FLOW JOURNEY_MAP GAPS [--check MANIFEST]"
fi

PRD="$1"; APP_FLOW="$2"; GEN_MAP="$3"; GAPS="$4"

# GAPS may legitimately be absent ONLY if the project records no gaps at all;
# the other three are always required. A missing GAPS file is treated as zero
# gap records (never as "gaps unknown") — the same reading check-persona-
# coverage.sh already takes.
for _f in "$PRD" "$APP_FLOW" "$GEN_MAP"; do
  [ -r "$_f" ] || _die "MISSING_SOURCE: required input not readable: $_f (fail closed)"
done
[ "$MODE" = check ] && { [ -r "$COMMITTED" ] || _die "MISSING_SOURCE: committed manifest not readable: $COMMITTED (fail closed)"; }

command -v jq >/dev/null 2>&1 || _die "generate-journey-coverage-manifest: jq not found (fail closed)"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

# ─────────────────────────────────────────────────────────────────────────────
# 1. FEAT anchors from the PRD — canonical grammar, same block-split + priority
#    rule as check-journey-coverage.sh (reused verbatim, never re-derived).
# ─────────────────────────────────────────────────────────────────────────────
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
      "")    _die "PRD_PRIORITY_UNPARSEABLE: $_fid has no priority: field (fail closed)" ;;
      *)     _die "PRD_PRIORITY_UNPARSEABLE: $_fid priority not P0-P3: $_pri (fail closed)" ;;
    esac
  done < "$_tmp/feat_all.txt"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 2. AFJ anchors from APP_FLOW
# ─────────────────────────────────────────────────────────────────────────────
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
  _die "APP_FLOW_UNIDDED: journey heading without AFJ-ID: $(cat "$_tmp/afj_err.txt") (fail closed)"

# Anti-vacuous: an empty anchor universe makes coverage vacuously satisfied.
if [ ! -s "$_tmp/feat_req.txt" ] && [ ! -s "$_tmp/afj_all.txt" ]; then
  _die "NO_ANCHORS: zero required FEAT anchors and zero AFJ anchors derived from PRD/APP_FLOW — a manifest over an empty universe is not evidence (fail closed)"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 3. Journey coverage relationships from the JOURNEY_MAP (its own declaration).
#    Reuses the shared block parser, so the producer and every gate can never
#    disagree about how a block/field is extracted.
# ─────────────────────────────────────────────────────────────────────────────
JOURNEY_MAP="$GEN_MAP"; export JOURNEY_MAP
# shellcheck disable=SC1090
. "$_here/../lib/journey-lib.sh"

journey_ids > "$_tmp/jids.txt"
_dup=$(sort "$_tmp/jids.txt" | uniq -d)
[ -z "$_dup" ] || _die "DUPLICATE_JOURNEY_ID: $(printf '%s' "$_dup" | tr '\n' ' ')— the same journey id is declared twice; its coverage would be ambiguous (fail closed)"

: > "$_tmp/pairs.tsv"   # JOURNEY-id <TAB> kind(covers|flows) <TAB> source-id
while IFS= read -r _jid; do
  [ -n "$_jid" ] || continue

  _covers=$(journey_field "$_jid" covers 2>/dev/null) || _covers=""
  printf '%s\n' "$_covers" | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | while IFS= read -r _tok; do
        [ -n "$_tok" ] || continue
        printf '%s\tcovers\t%s\n' "$_jid" "$_tok" >> "$_tmp/pairs.tsv"
      done

  _flows=$(journey_field "$_jid" flows 2>/dev/null) || _flows=""
  printf '%s\n' "$_flows" | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | while IFS= read -r _tok; do
        [ -n "$_tok" ] || continue
        printf '%s\tflows\t%s\n' "$_jid" "$_tok" >> "$_tmp/pairs.tsv"
      done
done < "$_tmp/jids.txt"

# Every declared token must be a real anchor. An unknown id is refused, never
# silently dropped: dropping it would quietly shrink the coverage claim until it
# happened to be true.
sort -u "$_tmp/feat_all.txt" 2>/dev/null > "$_tmp/feat_all_s.txt" || : > "$_tmp/feat_all_s.txt"
sort -u "$_tmp/afj_all.txt"  2>/dev/null > "$_tmp/afj_all_s.txt"  || : > "$_tmp/afj_all_s.txt"
[ -f "$_tmp/feat_all_s.txt" ] || : > "$_tmp/feat_all_s.txt"
[ -f "$_tmp/afj_all_s.txt" ]  || : > "$_tmp/afj_all_s.txt"

if [ -s "$_tmp/pairs.tsv" ]; then
  while IFS="$(printf '\t')" read -r _jid _kind _sid; do
    [ -n "$_sid" ] || continue
    case "$_kind" in
      covers)
        grep -qxF "$_sid" "$_tmp/feat_all_s.txt" || \
          _die "INVALID_SOURCE_ID: $_jid covers $_sid (not a FEAT-ID in the PRD) — refusing to emit a manifest that maps a journey to an unknown feature (fail closed)"
        ;;
      flows)
        grep -qxF "$_sid" "$_tmp/afj_all_s.txt" || \
          _die "INVALID_SOURCE_ID: $_jid flows $_sid (not an AFJ-ID in APP_FLOW) — refusing to emit a manifest that maps a journey to an unknown app-flow journey (fail closed)"
        ;;
    esac
  done < "$_tmp/pairs.tsv"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 4. Formally recorded coverage gaps. Identical well-formedness law to
#    check-journey-coverage.sh: all fields non-blank; `expires:` canonical with
#    `expiry:` accepted; conflicting dates are ambiguous. A malformed or
#    ambiguous gap is a malformed ANCHOR — the producer refuses rather than
#    emit a manifest whose _index encodes a credit the gate will reject.
# ─────────────────────────────────────────────────────────────────────────────
: > "$_tmp/gaps.tsv"
if [ -r "$GAPS" ]; then
  awk '
    /^[ \t]*source_id:/ { idx++ }
    /^[ \t]*(source_id|source_type|reason|owner|expiry|expires|reviewer):/ {
      match($0, /[a-z_]+:/)
      key = substr($0, RSTART, RLENGTH - 1)
      val = substr($0, RSTART + RLENGTH)
      sub(/^[ \t]+/, "", val); sub(/[ \t]+$/, "", val)
      printf "%d\t%s\t%s\n", idx, key, val
    }
  ' "$GAPS" > "$_tmp/graw.tsv"

  # fold (idx,key,val) into one record per idx, then validate
  _gaps_json=$(jq -Rn '
    [ inputs | split("\t") | { idx: .[0], key: .[1], val: (.[2] // "") } ]
    | group_by(.idx)
    | map( reduce .[] as $f ({}; .[$f.key] = $f.val) )
  ' < "$_tmp/graw.tsv")

  _bad=$(printf '%s' "$_gaps_json" | jq -r '
    ["source_id","source_type","reason","owner","reviewer"] as $REQ
    | [ .[]
        | ( (.expires // "") | tostring | gsub("^[ \t]+|[ \t]+$"; "") ) as $exs
        | ( (.expiry  // "") | tostring | gsub("^[ \t]+|[ \t]+$"; "") ) as $exy
        | { sid: (.source_id // ""), stype: (.source_type // ""),
            missing: ( [ $REQ[] as $k
                         | select( ((.[$k] // "") | tostring | gsub("^[ \t]+|[ \t]+$"; "")) == "" ) | $k ]
                       + (if ($exs == "" and $exy == "") then ["expires"] else [] end) ),
            conflict: ($exs != "" and $exy != "" and $exs != $exy) }
        | if (.missing | length) > 0 then
            "MALFORMED_GAP: \(if .sid == "" then "<no source_id>" else .sid end) missing field(s): \(.missing | join(", "))"
          elif .conflict then
            "MALFORMED_GAP: \(.sid) carries conflicting expires:/expiry: dates — one record cannot expire on two dates"
          elif .stype == "DOC_FORMAT" then
            "DOC_FORMAT_GAP: \(.sid) is a blocking document-format diagnostic, not a coverage credit"
          elif (.stype != "FEAT" and .stype != "AFJ") then
            "MALFORMED_GAP: \(.sid) source_type \"\(.stype)\" (must be FEAT or AFJ)"
          else empty end ]
    | .[]')
  if [ -n "$_bad" ]; then
    printf '%s\n' "$_bad" >&2
    _die "generate-journey-coverage-manifest: refusing to emit a manifest over malformed gap records (fail closed)"
  fi

  printf '%s' "$_gaps_json" | jq -r '.[] | .source_id // ""' \
    | sed '/^$/d' > "$_tmp/gapids.txt"

  _dupg=$(sort "$_tmp/gapids.txt" | uniq -d)
  [ -z "$_dupg" ] || _die "AMBIGUOUS_GAP: $(printf '%s' "$_dupg" | tr '\n' ' ')— appears in more than one gap record (fail closed)"

  # A gap for an id that is not an anchor at all is meaningless accounting.
  while IFS= read -r _gid; do
    [ -n "$_gid" ] || continue
    if ! grep -qxF "$_gid" "$_tmp/feat_all_s.txt" && ! grep -qxF "$_gid" "$_tmp/afj_all_s.txt"; then
      _die "INVALID_SOURCE_ID: gap record names $_gid, which is neither a FEAT-ID in the PRD nor an AFJ-ID in APP_FLOW (fail closed)"
    fi
  done < "$_tmp/gapids.txt"
else
  : > "$_tmp/gapids.txt"
fi

# ─────────────────────────────────────────────────────────────────────────────
# 5. Emit. jq -S sorts object keys; every array is sorted + deduped. No
#    timestamp, no path, no environment value is ever written.
# ─────────────────────────────────────────────────────────────────────────────
_j_array() { if [ -f "$1" ]; then jq -Rn '[inputs | select(length > 0)]' < "$1"; else printf '[]'; fi; }

_pairs=$(if [ -f "$_tmp/pairs.tsv" ]; then
  jq -Rn '[ inputs | select(length > 0) | split("\t")
            | { j: .[0], kind: .[1], sid: .[2] } ]' < "$_tmp/pairs.tsv"
else printf '[]'; fi)

_generate() {
  jq -S -n \
    --argjson pairs  "$_pairs" \
    --argjson jids   "$(_j_array "$_tmp/jids.txt")" \
    --argjson featReq "$(_j_array "$_tmp/feat_req.txt")" \
    --argjson afjAll  "$(_j_array "$_tmp/afj_all.txt")" \
    --argjson gapIds  "$(_j_array "$_tmp/gapids.txt")" '
    ($jids | unique) as $J
    | ($gapIds | unique) as $G

    # per-journey coverage: covers (FEAT) and flows (AFJ), sorted + deduped
    | ( reduce $J[] as $j ({};
          .[$j] = {
            covers: [ $pairs[] | select(.j == $j and .kind == "covers") | .sid ] | unique,
            flows:  [ $pairs[] | select(.j == $j and .kind == "flows")  | .sid ] | unique
          }) ) as $journeys

    # reverse index: source id -> the journeys that cover it
    | ( reduce $pairs[] as $p ({};
          .[$p.sid] = ((.[$p.sid] // []) + [$p.j]) ) ) as $covBy

    # every id the accounting must speak about: required FEATs, all AFJs,
    # everything gapped, and everything some journey claims to cover.
    | ( [ $featReq[], $afjAll[], $G[], ($covBy | keys[]) ] | unique ) as $ALL

    | ( reduce $ALL[] as $id ({};
          .[$id] = {
            journeys: (($covBy[$id] // []) | unique),
            gap: (if ($G | index($id)) != null then $id else null end)
          }) ) as $index

    | $journeys + { "_index": $index }
  '
}

if [ "$MODE" = check ]; then
  _generate > "$_tmp/regenerated.json" || _die "generate-journey-coverage-manifest: generation failed (fail closed)"
  if cmp -s "$_tmp/regenerated.json" "$COMMITTED"; then
    exit 0
  fi
  _emit "MANIFEST_STALE: $COMMITTED does not match the manifest regenerated from PRD/APP_FLOW/JOURNEY_MAP/GAPS."
  _emit "The manifest is generated evidence, not an authored document — regenerate it, do not hand-edit it:"
  _emit "  sh journey/bin/generate-journey-coverage-manifest.sh PRD APP_FLOW JOURNEY_MAP GAPS > JOURNEY_COVERAGE_MANIFEST.json"
  _emit "--- diff (committed vs regenerated) ---"
  diff "$COMMITTED" "$_tmp/regenerated.json" >&2 || true
  exit 1
fi

_generate
