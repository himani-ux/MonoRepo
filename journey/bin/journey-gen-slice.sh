#!/bin/sh
# journey-gen-slice.sh SSOT PRD APP_FLOW OUTDIR
#
# Parses canonical PRD + APP_FLOW + Step-1 SSOT into FEAT<->AFJ source bundles
# and a bundle-manifest.json.  Fails closed on malformed docs.
#
# Exit codes
#   0  success — bundles/ + bundle-manifest.json written to OUTDIR
#   1  error   — diagnostic on stderr:
#                  PRD_PRIORITY_UNPARSEABLE  (missing or invalid priority:)
#                  APP_FLOW_UNIDDED          (### heading without AFJ-<n>)
#                  or missing / unreadable input file
#
# Dependencies: POSIX sh, awk, jq
# shellcheck shell=sh

set -u

_die() { printf '%s\n' "$*" >&2; exit 1; }

[ $# -ne 4 ] && _die "Usage: journey-gen-slice.sh SSOT PRD APP_FLOW OUTDIR"

SSOT="$1"; PRD="$2"; APP_FLOW="$3"; OUTDIR="$4"

[ -r "$SSOT" ]     || _die "journey-gen-slice: file not readable: $SSOT"
[ -r "$PRD" ]      || _die "journey-gen-slice: file not readable: $PRD"
[ -r "$APP_FLOW" ] || _die "journey-gen-slice: file not readable: $APP_FLOW"

# Fix 1: guard OUTDIR and mktemp (fail closed)
mkdir -p "$OUTDIR/bundles" || _die "cannot create output dir: $OUTDIR/bundles"
_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

# ── Generation Context (review C3/I3/I4) ──────────────────────────────────────
# The generator may read ONLY its bundle, so everything it needs is injected
# here deterministically — never left to model judgment.

# Template schema — INLINED into every bundle (a SCHEMA: pointer contradicted
# the read boundary and forced the generator to improvise the block syntax).
_here=$(cd "$(dirname "$0")" && pwd)
_TEMPLATE="$_here/../JOURNEY_MAP.template.md"
[ -r "$_TEMPLATE" ] || _die "journey-gen-slice: template not readable: $_TEMPLATE (fail closed)"

# RUNNER — resolved from $JOURNEY_RUNNER, validated against the same enum as
# journey-runner-resolve.sh. The generator copies it verbatim; when absent it
# must emit 'runner: UNRESOLVED', which the lint enum rejects (fail closed
# downstream, never an invented value).
_RUNNER_VAL=""
if [ -n "${JOURNEY_RUNNER:-}" ]; then
  _RUNNER_VAL=$(printf '%s' "$JOURNEY_RUNNER" | tr '[:upper:]' '[:lower:]')
  case "$_RUNNER_VAL" in
    playwright|maestro|appium|pty|http) : ;;
    stub)
      [ "${ALLOW_STUB_RUNNER:-}" = "1" ] || \
        _die "journey-gen-slice: 'stub' runner requires ALLOW_STUB_RUNNER=1 (local/fixtures only)" ;;
    *)
      _die "journey-gen-slice: unknown JOURNEY_RUNNER '$JOURNEY_RUNNER' (allowed: playwright|maestro|appium|pty|http|stub)" ;;
  esac
fi

# GAP_EXPIRY — run date + 30 days (GNU then BSD date; fail closed if neither).
# Structured gaps cite this instead of inventing a date.
_GAP_EXPIRY=$(date -d "+30 days" +%Y-%m-%d 2>/dev/null) \
  || _GAP_EXPIRY=$(date -v+30d +%Y-%m-%d 2>/dev/null) \
  || _die "journey-gen-slice: cannot compute GAP_EXPIRY (fail closed)"

# Shared bundle tail: persona context + generation context + inlined schema
_emit_bundle_tail() {
  printf '\n## Persona Context\n\n%s\n' "$_persona"
  printf '\n## Generation Context\n\n'
  [ -n "$_RUNNER_VAL" ] && printf 'RUNNER: %s\n' "$_RUNNER_VAL"
  printf 'GAP_EXPIRY: %s\n' "$_GAP_EXPIRY"
  printf '\n## Schema (inlined from journey/JOURNEY_MAP.template.md)\n\n'
  cat "$_TEMPLATE"
}

# ──────────────────────────────────────────────────────────────────────────────
# 1. Extract ## Personas block from SSOT
# ──────────────────────────────────────────────────────────────────────────────
_persona=$(awk '
  /^## Personas/ { p=1; print; next }
  p && /^## /    { p=0 }
  p              { print }
' "$SSOT")

# ──────────────────────────────────────────────────────────────────────────────
# 2. Parse PRD into one file per FEAT-ID
#    Canonical feature-id grammar FEAT-([A-Z]+-)?[0-9]+ (check-doc-format.sh §1):
#    the slicer and the coverage gates must split the PRD identically, or a
#    prefixed-id PRD slices into nothing and journey generation silently
#    derives no journeys at all.
# ──────────────────────────────────────────────────────────────────────────────
awk -v outdir="$_tmp" '
  /^## FEAT-([A-Z]+-)?[0-9]/ {
    if (id != "") close(outdir "/prd_" id ".txt")
    line = $0
    match(line, /FEAT-([A-Z]+-)?[0-9]+/)
    id = substr(line, RSTART, RLENGTH)
    print > (outdir "/prd_" id ".txt")
    next
  }
  id != "" { print >> (outdir "/prd_" id ".txt") }
' "$PRD"

# ──────────────────────────────────────────────────────────────────────────────
# 3. Validate each FEAT block; classify P0/P1 (keep) or P2/P3 (exclude)
# ──────────────────────────────────────────────────────────────────────────────
_p01_feats=""
_excluded_json="[]"
_feat_count=0

for _feat_file in "$_tmp"/prd_FEAT-*.txt; do
  [ -f "$_feat_file" ] || continue
  _feat_count=$((_feat_count + 1))
  _fid=$(basename "$_feat_file" .txt | sed 's/^prd_//')

  _pri=$(awk '/^priority:/ {
    sub(/^priority:[ \t]+/, "")
    sub(/[ \t]*#.*$/, "")
    sub(/[ \t]+$/, "")
    print; exit
  }' "$_feat_file")

  case "$_pri" in
    P0|P1)
      _p01_feats="$_p01_feats $_fid"
      ;;
    P2|P3)
      _excluded_json=$(printf '%s' "$_excluded_json" | jq \
        --arg id "$_fid" --arg p "$_pri" \
        '. + [{id:$id,priority:$p}]')
      ;;
    "")
      _die "PRD_PRIORITY_UNPARSEABLE: $_fid has no priority: field"
      ;;
    *)
      _die "PRD_PRIORITY_UNPARSEABLE: $_fid priority not P0-P3: $_pri"
      ;;
  esac
done

# Anti-vacuous (review C4): ABSENT blocks fail closed exactly like malformed
# ones. Zero bundles would let every downstream gate pass vacuously.
[ "$_feat_count" -gt 0 ] || \
  _die "PRD_NO_FEAT_BLOCKS: PRD has no '## FEAT-<n>' block — nothing to derive journeys from (fail closed; see journey/docs/journey-gen-doc-format.md)"
[ -n "$_p01_feats" ] || \
  _die "NO_P01_FEATURES: PRD has FEAT blocks but none with priority P0/P1 — a generation run would be vacuous (fail closed)"

# ──────────────────────────────────────────────────────────────────────────────
# 4. Parse APP_FLOW into one file per AFJ-ID (under ## User Journeys)
#    Any ### heading without an AFJ-<n> id is a hard error (APP_FLOW_UNIDDED)
# ──────────────────────────────────────────────────────────────────────────────
awk -v outdir="$_tmp" -v errfile="$_tmp/app_flow_error.txt" '
  /^## User Journeys/ { in_uj=1; next }
  in_uj && /^## /     { in_uj=0; id=""; next }
  in_uj && /^### / {
    if (id != "") close(outdir "/afj_" id ".txt")
    line = $0
    if (match(line, /AFJ-[0-9]+/)) {
      id = substr(line, RSTART, RLENGTH)
      print > (outdir "/afj_" id ".txt")
    } else {
      print line > errfile
      id = ""
    }
    next
  }
  in_uj && id != "" { print >> (outdir "/afj_" id ".txt") }
' "$APP_FLOW"

[ -f "$_tmp/app_flow_error.txt" ] && \
  _die "APP_FLOW_UNIDDED: journey heading without AFJ-ID: $(cat "$_tmp/app_flow_error.txt")"

# Anti-vacuous (review C4): an APP_FLOW with no '## User Journeys' section or
# zero '### ... AFJ-<n>' headings yields zero journey anchors — fail closed.
_afj_found=0
for _af in "$_tmp"/afj_AFJ-*.txt; do
  [ -f "$_af" ] && { _afj_found=1; break; }
done
[ "$_afj_found" -eq 1 ] || \
  _die "APP_FLOW_NO_JOURNEYS: APP_FLOW has no '## User Journeys' section with '### ... AFJ-<n>' headings (fail closed; see journey/docs/journey-gen-doc-format.md)"

# ──────────────────────────────────────────────────────────────────────────────
# 5. Build FEAT<->AFJ link map
#    feat_links_FEAT-NNN.txt  — AFJ-IDs linked to this FEAT (from either side)
#    afj_links_AFJ-NNN.txt   — FEAT-IDs linked to this AFJ  (from either side)
# ──────────────────────────────────────────────────────────────────────────────

# Helper: split a comma-separated value and print one trimmed token per line
_split_csv() {
  printf '%s\n' "$1" | awk '{
    n = split($0, a, /,/)
    for (i = 1; i <= n; i++) {
      gsub(/^[ \t]+|[ \t]+$/, "", a[i])
      if (a[i] != "") print a[i]
    }
  }'
}

# (a) Seed FEAT link files from covers_flows (FEAT -> AFJ)
for _fid in $_p01_feats; do
  : > "$_tmp/feat_links_${_fid}.txt"
  _cflows=$(awk '/^covers_flows:/ {
    sub(/^covers_flows:[ \t]+/, "")
    sub(/[ \t]*#.*$/, "")
    sub(/[ \t]+$/, "")
    print; exit
  }' "$_tmp/prd_${_fid}.txt")
  [ -n "$_cflows" ] && _split_csv "$_cflows" >> "$_tmp/feat_links_${_fid}.txt"
done

# (b) Seed AFJ link files from covers_features (AFJ -> FEAT)
for _afj_file in "$_tmp"/afj_AFJ-*.txt; do
  [ -f "$_afj_file" ] || continue
  _aid=$(basename "$_afj_file" .txt | sed 's/^afj_//')
  : > "$_tmp/afj_links_${_aid}.txt"
  _cfeats=$(awk '/^covers_features:/ {
    sub(/^covers_features:[ \t]+/, "")
    sub(/[ \t]*#.*$/, "")
    sub(/[ \t]+$/, "")
    print; exit
  }' "$_afj_file")
  [ -n "$_cfeats" ] && _split_csv "$_cfeats" >> "$_tmp/afj_links_${_aid}.txt"
done

# (c) Cross-link: for each AFJ's covers_features FEAT-IDs, add the AFJ back
#     to that FEAT's link list (handles the case where only AFJ side declares
#     the link)
for _afj_file in "$_tmp"/afj_AFJ-*.txt; do
  [ -f "$_afj_file" ] || continue
  _aid=$(basename "$_afj_file" .txt | sed 's/^afj_//')
  while IFS= read -r _fid_ref; do
    [ -z "$_fid_ref" ] && continue
    # Only cross-link to P0/P1 FEATs (their link files exist)
    if [ -f "$_tmp/feat_links_${_fid_ref}.txt" ]; then
      if ! grep -qF "$_aid" "$_tmp/feat_links_${_fid_ref}.txt" 2>/dev/null; then
        printf '%s\n' "$_aid" >> "$_tmp/feat_links_${_fid_ref}.txt"
      fi
    fi
  done < "$_tmp/afj_links_${_aid}.txt"
done

# (d) Cross-link: for each P0/P1 FEAT's covers_flows AFJ-IDs, add the FEAT
#     back to that AFJ's link list (handles the case where only FEAT side
#     declares the link)
for _fid in $_p01_feats; do
  [ -f "$_tmp/feat_links_${_fid}.txt" ] || continue
  while IFS= read -r _aid_ref; do
    [ -z "$_aid_ref" ] && continue
    if [ -f "$_tmp/afj_links_${_aid_ref}.txt" ]; then
      if ! grep -qF "$_fid" "$_tmp/afj_links_${_aid_ref}.txt" 2>/dev/null; then
        printf '%s\n' "$_fid" >> "$_tmp/afj_links_${_aid_ref}.txt"
      fi
    fi
  done < "$_tmp/feat_links_${_fid}.txt"
done

# ──────────────────────────────────────────────────────────────────────────────
# 6. Emit bundles and accumulate manifest arrays
# ──────────────────────────────────────────────────────────────────────────────
_bundles_json="[]"
_unlinked_json="[]"

# FEAT bundles — P0/P1 only
for _fid in $_p01_feats; do
  [ -f "$_tmp/feat_links_${_fid}.txt" ] || continue
  _flinks=$(grep -v '^[[:space:]]*$' "$_tmp/feat_links_${_fid}.txt" 2>/dev/null || true)

  if [ -z "$_flinks" ]; then
    # No link in either direction — record as unlinked, emit NO bundle
    _unlinked_json=$(printf '%s' "$_unlinked_json" | jq \
      --arg id "$_fid" \
      '. + [{id:$id,source_type:"FEAT",reason:"no FEAT<->AFJ link"}]')
    continue
  fi

  # Fix 2: filter to only AFJ-IDs that actually have a source block.
  # A dangling cross-reference (covers_flows: AFJ-NNN where AFJ-NNN has no
  # block in APP_FLOW) must never produce a bundle with a blank APP_FLOW side.
  : > "$_tmp/_fv.txt"
  : > "$_tmp/_fm.txt"
  printf '%s\n' "$_flinks" | while IFS= read -r _al; do
    [ -z "$_al" ] && continue
    if [ -f "$_tmp/afj_${_al}.txt" ]; then
      printf '%s\n' "$_al" >> "$_tmp/_fv.txt"
    else
      printf '%s\n' "$_al" >> "$_tmp/_fm.txt"
    fi
  done
  _flinks_valid=$(grep -v '^[[:space:]]*$' "$_tmp/_fv.txt" 2>/dev/null || true)

  if [ -z "$_flinks_valid" ]; then
    # All referenced AFJ counterparts are missing — dangling cross-reference,
    # emit NO bundle (would have blank APP_FLOW side)
    _miss=$(awk 'NF {printf "%s%s", (NR>1 ? ", " : ""), $0}' "$_tmp/_fm.txt")
    _unlinked_json=$(printf '%s' "$_unlinked_json" | jq \
      --arg id "$_fid" --arg r "linked counterpart not found: $_miss" \
      '. + [{id:$id,source_type:"FEAT",reason:$r}]')
    continue
  fi

  _brel="bundles/$(printf '%s' "$_fid" | awk '{print tolower($0)}').md"
  _bfile="$OUTDIR/$_brel"

  {
    printf '# Bundle: %s\n\n' "$_fid"
    printf '## PRD Source\n\n'
    cat "$_tmp/prd_${_fid}.txt"
    printf '\n\n## APP_FLOW Source\n\n'
    printf '%s\n' "$_flinks_valid" | while IFS= read -r _al; do
      [ -z "$_al" ] && continue
      cat "$_tmp/afj_${_al}.txt"
      printf '\n'
    done
    _emit_bundle_tail
  } > "$_bfile"

  _lj=$(printf '%s\n' "$_flinks_valid" | jq -Rs 'split("\n") | map(select(. != ""))')
  _bundles_json=$(printf '%s' "$_bundles_json" | jq \
    --arg id "$_fid" --arg path "$_brel" --argjson links "$_lj" \
    '. + [{id:$id,source_type:"FEAT",bundle_path:$path,links:$links}]')
done

# AFJ bundles — all AFJ-IDs with >=1 link
for _afj_file in "$_tmp"/afj_AFJ-*.txt; do
  [ -f "$_afj_file" ] || continue
  _aid=$(basename "$_afj_file" .txt | sed 's/^afj_//')
  [ -f "$_tmp/afj_links_${_aid}.txt" ] || continue
  _alinks=$(grep -v '^[[:space:]]*$' "$_tmp/afj_links_${_aid}.txt" 2>/dev/null || true)

  if [ -z "$_alinks" ]; then
    _unlinked_json=$(printf '%s' "$_unlinked_json" | jq \
      --arg id "$_aid" \
      '. + [{id:$id,source_type:"AFJ",reason:"no FEAT<->AFJ link"}]')
    continue
  fi

  # Fix 2: filter to only FEAT-IDs that actually have a source block.
  # A dangling cross-reference (covers_features: FEAT-NNN where FEAT-NNN has
  # no block in PRD) must never produce a bundle with a blank PRD side.
  : > "$_tmp/_av.txt"
  : > "$_tmp/_am.txt"
  printf '%s\n' "$_alinks" | while IFS= read -r _fl; do
    [ -z "$_fl" ] && continue
    if [ -f "$_tmp/prd_${_fl}.txt" ]; then
      printf '%s\n' "$_fl" >> "$_tmp/_av.txt"
    else
      printf '%s\n' "$_fl" >> "$_tmp/_am.txt"
    fi
  done
  _alinks_valid=$(grep -v '^[[:space:]]*$' "$_tmp/_av.txt" 2>/dev/null || true)

  if [ -z "$_alinks_valid" ]; then
    # All referenced FEAT counterparts are missing — dangling cross-reference,
    # emit NO bundle (would have blank PRD side)
    _miss=$(awk 'NF {printf "%s%s", (NR>1 ? ", " : ""), $0}' "$_tmp/_am.txt")
    _unlinked_json=$(printf '%s' "$_unlinked_json" | jq \
      --arg id "$_aid" --arg r "linked counterpart not found: $_miss" \
      '. + [{id:$id,source_type:"AFJ",reason:$r}]')
    continue
  fi

  _brel="bundles/$(printf '%s' "$_aid" | awk '{print tolower($0)}').md"
  _bfile="$OUTDIR/$_brel"

  {
    printf '# Bundle: %s\n\n' "$_aid"
    printf '## APP_FLOW Source\n\n'
    cat "$_afj_file"
    printf '\n\n## PRD Source\n\n'
    printf '%s\n' "$_alinks_valid" | while IFS= read -r _fl; do
      [ -z "$_fl" ] && continue
      cat "$_tmp/prd_${_fl}.txt"
      printf '\n'
    done
    _emit_bundle_tail
  } > "$_bfile"

  _lj=$(printf '%s\n' "$_alinks_valid" | jq -Rs 'split("\n") | map(select(. != ""))')
  _bundles_json=$(printf '%s' "$_bundles_json" | jq \
    --arg id "$_aid" --arg path "$_brel" --argjson links "$_lj" \
    '. + [{id:$id,source_type:"AFJ",bundle_path:$path,links:$links}]')
done

# ──────────────────────────────────────────────────────────────────────────────
# 7. Emit bundle-manifest.json
# ──────────────────────────────────────────────────────────────────────────────
jq -n \
  --argjson bundles  "$_bundles_json" \
  --argjson excluded "$_excluded_json" \
  --argjson unlinked "$_unlinked_json" \
  '{bundles:$bundles,excluded_features:$excluded,unlinked:$unlinked}' \
  > "$OUTDIR/bundle-manifest.json"
