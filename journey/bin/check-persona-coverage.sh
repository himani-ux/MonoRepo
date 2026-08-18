#!/bin/sh
# shellcheck shell=sh
# check-persona-coverage.sh PRD SSOT JOURNEY_MAP PERSONA_COVERAGE_GAPS
#
# Persona-coverage gate (Increment 3, A2: per-FEAT rule). Anchors are
# RE-DERIVED directly from the PRD (P0/P1 FEAT set) and the SSOT (persona
# set) — generated manifests and the map's own claims are never trusted.
#
#   * every P0/P1 FEAT needs >=1 `origin: PERSONA` journey covering it, OR
#     exactly one valid, unexpired gap record in PERSONA_COVERAGE_GAPS
#     (its OWN artifact — never the doc-derived gaps file);
#   * a FEAT cannot be both covered and gapped (COVERED_AND_GAPPED);
#   * expired gaps are not credits (GAP_EXPIRED); malformed gaps fail
#     (GAP_MALFORMED);
#   * zero P0/P1 FEATs or zero personas fails (NO_ANCHORS — anti-vacuous).
#
# Gap record shape (all fields required, non-blank):
#   source_id: FEAT-<n> / source_type: FEAT / reason / owner / reviewer /
#   expires: YYYY-MM-DD
#
# `expires:` is the CANONICAL spelling for new records. `expiry:` is accepted as
# a legacy synonym (owner ruling 2026-07-14, item 2): this gate demanded
# `expires:` while check-journey-coverage.sh demanded `expiry:`, so the two
# disagreed about the shape of the same record type and a project could not
# satisfy both. Compatibility is ADDITIVE — no existing project is forced to
# rewrite a record. A record carrying BOTH spellings with DIFFERENT dates is
# ambiguous and fails closed (GAP_MALFORMED); with the same date it is merely
# redundant and is accepted. A record with NEITHER still fails, and the
# YYYY-MM-DD format + expiry-date rules below are unchanged.
#
# FEAT ids follow the framework's canonical grammar FEAT-([A-Z]+-)?[0-9]+ —
# plain (FEAT-001) and prefixed (FEAT-AUD-101) forms are both first-class.
#
# A missing gaps file means zero gaps (coverage must then be journey-borne).
# Deps: POSIX sh, awk, grep, sed, date.

set -u
_die() { printf '%s\n' "$*" >&2; exit 1; }
_here=$(cd "$(dirname "$0")" && pwd)

[ $# -eq 4 ] || _die "usage: check-persona-coverage.sh PRD SSOT JOURNEY_MAP PERSONA_COVERAGE_GAPS"
PRD="$1"; SSOT="$2"; MAP="$3"; GAPS="$4"
for _f in "$PRD" "$SSOT" "$MAP"; do
  [ -r "$_f" ] || _die "check-persona-coverage: file not readable: $_f"
done

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

problems=0
_p() { printf '%s\n' "$1"; problems=$((problems + 1)); }

# ── anchors: P0/P1 FEATs from the PRD (re-derived; same rules as the slicer) ──
# The anchor regex is the framework's CANONICAL feature-id grammar,
# FEAT-([A-Z]+-)?[0-9]+ — the same one check-doc-format.sh enforces on the PRD
# and journey-extracted-confirm.sh enforces on covers tokens. A narrower
# ^## FEAT-[0-9] anchor silently skipped every PREFIXED id (FEAT-AUD-101), so a
# whole PRD of prefixed features derived ZERO anchors and the gate died
# NO_ANCHORS while claiming the PRD was empty — the gate was blind, not the PRD.
awk -v out="$_tmp" '
  /^## FEAT-([A-Z]+-)?[0-9]/ {
    match($0, /FEAT-([A-Z]+-)?[0-9]+/); id = substr($0, RSTART, RLENGTH)
    cur = id; next
  }
  cur != "" && /^priority:/ {
    p = $0; sub(/^priority:[ \t]*/, "", p); sub(/[ \t]*#.*$/, "", p); sub(/[ \t]+$/, "", p)
    if (p == "P0" || p == "P1") print cur >> (out "/req.txt")
    cur = ""
  }
' "$PRD"

# personas from the SSOT (re-derived)
awk '
  /^## Personas/ { inp = 1; next }
  inp && /^## /  { inp = 0; next }
  inp && /^### / { if (match($0, /P[0-9]+/)) print substr($0, RSTART, RLENGTH) }
' "$SSOT" > "$_tmp/personas.txt"

if [ ! -s "$_tmp/req.txt" ] || [ ! -s "$_tmp/personas.txt" ]; then
  _die "NO_ANCHORS: zero P0/P1 FEATs in the PRD or zero personas in the SSOT — persona coverage would be vacuous (fail closed)"
fi

# ── covered FEATs: covers of origin=PERSONA journeys (from the map directly) ──
JOURNEY_MAP="$MAP"; export JOURNEY_MAP
# shellcheck disable=SC1090
. "$_here/../lib/journey-lib.sh"
: > "$_tmp/covered.txt"
for _jid in $(journey_ids | sort -u); do
  _org=$(journey_field "$_jid" origin 2>/dev/null) || _org=""
  [ "$_org" = "PERSONA" ] || continue
  _covers=$(journey_field "$_jid" covers 2>/dev/null) || _covers=""
  printf '%s\n' "$_covers" | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
    | grep -E '^FEAT-([A-Z]+-)?[0-9]+$' >> "$_tmp/covered.txt" || true
done

# ── gap records (own artifact; missing file = zero gaps) ─────────────────────
: > "$_tmp/gaps.tsv"
if [ -r "$GAPS" ]; then
  awk -v out="$_tmp" '
    /^source_id:/ {
      if (id != "") printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", id, ty, rs, ow, rv, exs, exy >> (out "/gaps.tsv")
      id = $0; sub(/^source_id:[ \t]*/, "", id); sub(/[ \t]+$/, "", id)
      ty = ""; rs = ""; ow = ""; rv = ""; exs = ""; exy = ""; next
    }
    /^source_type:/ { ty = $0; sub(/^source_type:[ \t]*/, "", ty); sub(/[ \t]+$/, "", ty) }
    /^reason:/      { rs = $0; sub(/^reason:[ \t]*/, "", rs); sub(/[ \t]+$/, "", rs) }
    /^owner:/       { ow = $0; sub(/^owner:[ \t]*/, "", ow); sub(/[ \t]+$/, "", ow) }
    /^reviewer:/    { rv = $0; sub(/^reviewer:[ \t]*/, "", rv); sub(/[ \t]+$/, "", rv) }
    # `expires:` is CANONICAL. `expiry:` is the accepted LEGACY spelling — the
    # journey-layer gate used to demand it while this one demanded `expires:`,
    # so the two gates disagreed about the shape of the same record type. Both
    # are read here; the resolution (and the conflict rule) is in the shell
    # below, where a diagnostic can be emitted.
    /^expires:/     { exs = $0; sub(/^expires:[ \t]*/, "", exs); sub(/[ \t]+$/, "", exs) }
    /^expiry:/      { exy = $0; sub(/^expiry:[ \t]*/,  "", exy); sub(/[ \t]+$/, "", exy) }
    END { if (id != "") printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n", id, ty, rs, ow, rv, exs, exy >> (out "/gaps.tsv") }
  ' "$GAPS"
fi

_today=$(date +%Y-%m-%d) || _die "cannot get today's date (fail closed)"
: > "$_tmp/valid_gaps.txt"
while IFS="$(printf '\t')" read -r _gid _gty _grs _gow _grv _gexs _gexy; do
  [ -n "$_gid" ] || continue
  _bad=0
  [ "$_gty" = "FEAT" ] || { _p "GAP_MALFORMED: gap $_gid source_type '$_gty' (must be FEAT)"; _bad=1; }
  for _v in "$_grs" "$_gow" "$_grv"; do
    [ -n "$_v" ] || { _p "GAP_MALFORMED: gap $_gid has a blank reason/owner/reviewer field"; _bad=1; break; }
  done

  # ── expiry field: `expires:` canonical, `expiry:` accepted (owner ruling,
  #    2026-07-14, item 2) ────────────────────────────────────────────────────
  # Compatibility is ADDITIVE: an existing project is never forced to rewrite a
  # record. Carrying BOTH spellings with DIFFERENT dates is ambiguous, though —
  # one record cannot expire on two days — so that fails closed and grants NO
  # credit. Both spellings with the SAME date is merely redundant, not
  # ambiguous, and is accepted. When neither is present the record is treated
  # exactly as before (blank date -> GAP_MALFORMED), so a record with no expiry
  # field at all still fails.
  _conflict=0
  if [ -n "$_gexs" ] && [ -n "$_gexy" ] && [ "$_gexs" != "$_gexy" ]; then
    _p "GAP_MALFORMED: gap $_gid carries conflicting expires: '$_gexs' and expiry: '$_gexy' — one record cannot expire on two dates (fail closed; 'expires:' is canonical)"
    _bad=1; _conflict=1
  fi
  if [ -n "$_gexs" ]; then _gex="$_gexs"; else _gex="$_gexy"; fi

  # A conflicting record is already condemned above; running the date rules on
  # an arbitrarily-picked winner would only add a second, misleading diagnostic.
  if [ "$_conflict" -eq 0 ]; then
    case "$_gex" in
      [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9])
        if [ "$_gex" \< "$_today" ]; then
          _p "GAP_EXPIRED: gap $_gid expired $_gex (today: $_today) — an expired gap is not a coverage credit"
          _bad=1
        fi ;;
      *) _p "GAP_MALFORMED: gap $_gid expires '$_gex' not YYYY-MM-DD"; _bad=1 ;;
    esac
  fi

  [ "$_bad" -eq 0 ] && printf '%s\n' "$_gid" >> "$_tmp/valid_gaps.txt"
  printf '%s\n' "$_gid" >> "$_tmp/all_gaps.txt"
done < "$_tmp/gaps.tsv"

# ── the per-FEAT rule ─────────────────────────────────────────────────────────
sort -u "$_tmp/req.txt" > "$_tmp/req_sorted.txt"
while IFS= read -r _fid; do
  [ -n "$_fid" ] || continue
  _cov=0; _gap=0
  grep -qxF "$_fid" "$_tmp/covered.txt" && _cov=1
  grep -qxF "$_fid" "$_tmp/all_gaps.txt" 2>/dev/null && _gap=1
  if [ "$_cov" -eq 1 ] && [ "$_gap" -eq 1 ]; then
    _p "COVERED_AND_GAPPED: $_fid has a PERSONA journey AND a persona gap — a gap for a covered FEAT hides accounting drift"
    continue
  fi
  if [ "$_cov" -eq 0 ]; then
    if ! grep -qxF "$_fid" "$_tmp/valid_gaps.txt" 2>/dev/null; then
      _p "PERSONA_COVERAGE_GAP: P0/P1 $_fid has no PERSONA journey and no valid persona gap (see PERSONA_COVERAGE_GAPS.md)"
    fi
  fi
done < "$_tmp/req_sorted.txt"

if [ "$problems" -gt 0 ]; then
  printf 'check-persona-coverage: %d problem(s) (fail closed)\n' "$problems"
  exit 1
fi
exit 0
