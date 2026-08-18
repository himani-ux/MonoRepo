#!/bin/sh
# shellcheck shell=sh
# lint-uat-report.sh <report> — gate 4.1, schema only (no repo access).
# Codes: HEADER_MISSING DATE_INVALID NO_CLAIMS DUPLICATE_CLAIM_ID GRADE_UNKNOWN
#        CLAIM_NO_EVIDENCE CONTRADICTION_ONE_SIDED ABSENCE_NO_SEARCH
#        SAMPLE_MISSING SAMPLE_TOO_SMALL EVIDENCE_FORMAT SEARCH_FORMAT
#        ORACLE_CLAUSE_FORMAT
#
# `- oracle_clause: <ref>` is an OPTIONAL claim line (spec G4, oracle
# observability classes). When present, <ref> must match
# JOURNEY-<digits>#<positive-int>; malformed -> ORACLE_CLAUSE_FORMAT and
# fail-closed, same emission style as SEARCH_FORMAT/EVIDENCE_FORMAT above.
# This gate checks FORMAT ONLY (no journey-map lookup, no class
# adjudication — that is check-uat-oracle-scope.sh's job). A report with no
# `- oracle_clause:` lines at all behaves EXACTLY as before this field
# existed.
set -u
_here="$(dirname "$0")"; . "$_here/../lib/uat-lib.sh"
r="${1:?usage: lint-uat-report.sh <report>}"
[ -f "$r" ] || uat_die HEADER_MISSING "no such report: $r"

head -1 "$r" | grep -q '^# UAT-REPORT$' || uat_die HEADER_MISSING "first line must be '# UAT-REPORT'"
_date="$(uat_header_field "$r" report_date)"; _commit="$(uat_header_field "$r" repo_commit)"
_target="$(uat_header_field "$r" app_target)"
[ -n "$_date" ] && [ -n "$_commit" ] && [ -n "$_target" ] || uat_die HEADER_MISSING "need report_date, repo_commit, app_target"
printf '%s\n' "$_commit" | grep -q '^[0-9a-f]\{40\}$' || uat_die HEADER_MISSING "repo_commit must be 40-hex"
# Bounds check only (F-DATE), NOT a full calendar (e.g. 2026-02-31 still
# passes — no days-in-month/leap-year logic). month 01-12, day 01-31.
printf '%s\n' "$_date" | grep -Eq '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$' \
  || uat_die DATE_INVALID "report_date must be YYYY-MM-DD with month 01-12 and day 01-31"
_base="$(basename "$r")"
printf '%s\n' "$_base" | grep -q "^UAT_REPORT_${_date}\(-[0-9][0-9]*\)\{0,1\}\.md$" \
  || uat_die DATE_INVALID "filename must be UAT_REPORT_${_date}[-<n>].md, got $_base"

_ids="$(uat_claim_ids "$r")"
[ -n "$_ids" ] || uat_die NO_CLAIMS "no '## UAT-CLAIM-<n>:' blocks"
_dup="$(printf '%s\n' "$_ids" | sort | uniq -d | head -1)"
[ -z "$_dup" ] || uat_die DUPLICATE_CLAIM_ID "$_dup appears more than once"

for _id in $_ids; do
  _blk="$(uat_claim_block "$r" "$_id")"
  _grade="$(printf '%s\n' "$_blk" | sed -n 's/^- grade: //p' | head -1)"
  case "$_grade" in
    "[C]"|"[C-absent]"|"[I]"|"[G]"|"[X]") : ;;
    *) uat_die GRADE_UNKNOWN "$_id grade '$_grade'";;
  esac
  printf '%s\n' "$_blk" | grep -q '^- claim: .' || uat_die HEADER_MISSING "$_id missing claim line"
  _nev="$(printf '%s\n' "$_blk" | grep -c '^- evidence: ')"
  # every evidence line must be well-formed
  printf '%s\n' "$_blk" | grep '^- evidence: ' | while IFS= read -r _ln; do
    if uat_ev_is_artifact "$_ln"; then
      printf '%s\n' "$_ln" | grep -q '^- evidence: artifact [A-Za-z0-9._/-]\{1,\} sha256:[0-9a-f]\{64\}$' \
        || { printf 'EVIDENCE_FORMAT: %s: bad artifact line\n' "$_id" >&2; exit 9; }
    else
      printf '%s\n' "$_ln" | grep -q '^- evidence: [^ ][^—]*:[0-9][0-9]* — ".\{1,\}"$' \
        || { printf 'EVIDENCE_FORMAT: %s: bad quote line\n' "$_id" >&2; exit 9; }
      _p="$(uat_ev_path "$_ln")"
      case "$_p" in /*|*..*) printf 'EVIDENCE_FORMAT: %s: path not repo-relative\n' "$_id" >&2; exit 9;; esac
    fi
  done || exit 1
  # search lines must be well-formed everywhere they appear
  printf '%s\n' "$_blk" | grep '^- search: ' | while IFS= read -r _ln; do
    uat_srch_wellformed "$_ln" || { printf 'SEARCH_FORMAT: %s: %s\n' "$_id" "$_ln" >&2; exit 9; }
  done || exit 1
  # oracle_clause lines are OPTIONAL (spec G4) — format only, wherever they
  # appear; a report with none is unaffected (loop body never runs).
  printf '%s\n' "$_blk" | grep '^- oracle_clause: ' | while IFS= read -r _ln; do
    uat_oc_wellformed "$_ln" \
      || { printf 'ORACLE_CLAUSE_FORMAT: %s: %s\n' "$_id" "$(uat_oc_ref "$_ln")" >&2; exit 9; }
  done || exit 1
  _nsr="$(printf '%s\n' "$_blk" | grep -c '^- search: ')"
  case "$_grade" in
    "[C]") [ "$_nev" -ge 1 ] || uat_die CLAIM_NO_EVIDENCE "$_id is [C] with no evidence line";;
    "[X]") [ "$_nev" -ge 2 ] || uat_die CONTRADICTION_ONE_SIDED "$_id is [X] with <2 evidence lines";;
    "[C-absent]") [ "$_nsr" -ge 1 ] || uat_die ABSENCE_NO_SEARCH "$_id is [C-absent] with no search line";;
    "[I]")
      _smp="$(printf '%s\n' "$_blk" | sed -n 's/^- sample: \([0-9][0-9]*\) instances$/\1/p' | head -1)"
      [ -n "$_smp" ] || uat_die SAMPLE_MISSING "$_id is [I] with no sample line"
      [ "$_smp" -ge 3 ] || uat_die SAMPLE_TOO_SMALL "$_id sample $_smp < 3";;
  esac
done
exit 0
