#!/bin/sh
# shellcheck shell=sh
# check-uat-oracle-scope.sh <report> <journey_map> — the false-gap killer
# (spec G4, oracle observability classes).
#
# Field-run motivation: in a real browser-UAT pass, oracle clauses that are
# only verifiable BELOW the browser (hash computation, exclusion logic —
# covered by unit tests) were reported as false "gaps" because nothing
# classified clauses as browser-observable vs lower-level. A human had to
# hand-verify every one of them. This gate makes that classification
# machine-checkable: a browser-UAT `[C-absent]` claim citing an
# `oracle_classes: lower` clause is not a legitimate browser gap, and this
# gate rejects it deterministically.
#
# Composes lint-journey-map.sh FIRST (as an executable, never
# re-implemented — the same composition style check-uat-preconditions.sh
# uses for itself): the `oracle_classes:` GRAMMAR (Check 9: token
# membership, positional clause-count match against `oracle:`) is that
# gate's job, not this one's — this gate trusts a lint-clean map and
# re-parses the same blocks using journey/lib/journey-lib.sh accessors
# (including `split_and`, the same ` AND `-splitter Check 9 uses), so the
# two can never disagree about a clause count or a positional class. Claim
# blocks are parsed with journey/lib/uat-lib.sh's `uat_claim_ids` /
# `uat_claim_block` — the identical accessors lint-uat-report.sh uses — plus
# the `uat_oc_*` oracle-clause-reference helpers shared with that gate's own
# `- oracle_clause:` FORMAT check.
#
# TRUST STATEMENT: adjudication exists ONLY for claims that carry an
# `- oracle_clause:` ref. A `[C-absent]` claim with no ref at all is
# invisible to the per-claim adjudication below — the anti-vacuous
# NO_CLAUSE_REFS check is the only backstop for a report that should have
# carried refs but doesn't.
#
# Every `- oracle_clause: <ref>` line this gate consumes is fail-closed:
#   - malformed ref (not `JOURNEY-<digits>#<positive-int>`) ->
#     ORACLE_CLAUSE_FORMAT
#   - journey id not present in the (lint-clean) map ->
#     ORACLE_CLAUSE_UNKNOWN_JOURNEY
#   - index k > that journey's ` AND `-split oracle clause count ->
#     ORACLE_CLAUSE_OUT_OF_RANGE
#   - journey has no `oracle_classes:` declared at all -> ORACLE_CLASS_UNDECLARED
#     (fail closed: scope cannot be adjudicated without a declaration)
#   - ADJUDICATION: claim grade is `[C-absent]` AND the referenced clause's
#     class is `lower` -> ORACLE_CLASS_OUT_OF_SCOPE (the false-gap killer:
#     a browser UAT absence claim cannot assert a below-the-UI clause as a
#     gap; route it to lower-level evidence instead).
# Grades other than `[C-absent]` with a valid ref are allowed (positive
# evidence, e.g. `[C]`, citing a `lower` clause is legitimate — the claim
# isn't asserting an absence). `[C-absent]` against a `browser`-classed
# clause is allowed (a genuine browser gap).
#
# Anti-vacuous law (matches NO_PRECONDITIONS / NO_SURFACE_BLOCKS / NO_CLAIMS
# elsewhere in this framework — an invoked gate never passes vacuously):
# zero `- oracle_clause: ` lines anywhere in the whole report ->
# NO_CLAUSE_REFS and exit 1. This is checked over the WHOLE FILE, not just
# recognized claim blocks — a stray ref outside any claim block still
# proves the report intends to use this field.
#
# All violations are accumulated (fail-slow, not fail-fast) via a plain
# `for`/heredoc-fed `while` loop — deliberately NOT a `| while read` pipe
# (a tool-missing/counter-mutation-lost failure inside a pipeline subshell
# is a known fail-open class in this repo; same idiom as
# check-uat-preconditions.sh and lint-journey-map.sh Check 8/9).
#
# Codes (closed enum):
#   LINT_FAILED                     — journey map failed lint-journey-map.sh
#   NO_CLAUSE_REFS                  — zero oracle_clause refs in the report
#                                      (anti-vacuous; nothing to adjudicate)
#   ORACLE_CLAUSE_FORMAT: UAT-CLAIM-<n>: <ref>
#   ORACLE_CLAUSE_UNKNOWN_JOURNEY: UAT-CLAIM-<n>: <id>
#   ORACLE_CLAUSE_OUT_OF_RANGE: UAT-CLAIM-<n>: <ref>
#   ORACLE_CLASS_UNDECLARED: UAT-CLAIM-<n>: <id>
#   ORACLE_CLASS_OUT_OF_SCOPE: UAT-CLAIM-<n>: <ref> is a lower-level clause;
#     a browser UAT absence claim cannot assert it as a gap — route to
#     lower-level evidence
# Usage error / missing input file: exit 2 (matches lint-journey-map.sh /
# check-uat-preconditions.sh's own convention).
#
# shellcheck shell=sh
set -u

_here="$(cd "$(dirname "$0")" && pwd)"
LIB="$_here/../lib/journey-lib.sh"
UATLIB="$_here/../lib/uat-lib.sh"

usage() { printf 'Usage: check-uat-oracle-scope.sh <report> <journey_map>\n' >&2; exit 2; }
[ $# -eq 2 ] || usage

REPORT="$1"
MAP="$2"

[ -f "$REPORT" ] || {
  printf 'check-uat-oracle-scope: file not found: %s\n' "$REPORT" >&2
  exit 2
}
[ -f "$MAP" ] || {
  printf 'check-uat-oracle-scope: file not found: %s\n' "$MAP" >&2
  exit 2
}

# ── compose lint-journey-map.sh first — oracle_classes GRAMMAR is its job,
#    not ours (Check 9); this gate trusts a lint-clean map ─────────────────
/bin/sh "$_here/lint-journey-map.sh" "$MAP"
_lint_rc=$?
if [ "$_lint_rc" -ne 0 ]; then
  printf 'LINT_FAILED: journey map failed lint-journey-map.sh\n' >&2
  exit 1
fi

JOURNEY_MAP="$MAP"
export JOURNEY_MAP
# shellcheck disable=SC1090
. "$LIB"
# shellcheck disable=SC1090
. "$UATLIB"

errors=0

# ── anti-vacuous law: zero oracle_clause refs ANYWHERE in the report ──────
_total_refs="$(grep -c '^- oracle_clause: ' "$REPORT")"
if [ "$_total_refs" -eq 0 ]; then
  printf 'NO_CLAUSE_REFS: report carries no oracle_clause references; nothing to adjudicate\n' >&2
  exit 1
fi

_map_ids="$(journey_ids | sort -u)"
_claim_ids="$(uat_claim_ids "$REPORT")"

for _id in $_claim_ids; do
  _blk="$(uat_claim_block "$REPORT" "$_id")"
  _grade="$(printf '%s\n' "$_blk" | sed -n 's/^- grade: //p' | head -1)"
  _oclines="$(printf '%s\n' "$_blk" | grep '^- oracle_clause: ')"
  [ -z "$_oclines" ] && continue

  while IFS= read -r _ln; do
    [ -z "$_ln" ] && continue

    if ! uat_oc_wellformed "$_ln"; then
      printf 'ORACLE_CLAUSE_FORMAT: %s: %s\n' "$_id" "$(uat_oc_ref "$_ln")" >&2
      errors=$((errors + 1))
      continue
    fi

    _ref="$(uat_oc_ref "$_ln")"
    _jid="$(uat_oc_journey_id "$_ln")"
    _idx="$(uat_oc_index "$_ln")"

    printf '%s\n' "$_map_ids" | grep -qxF "$_jid" || {
      printf 'ORACLE_CLAUSE_UNKNOWN_JOURNEY: %s: %s\n' "$_id" "$_jid" >&2
      errors=$((errors + 1))
      continue
    }

    # oracle: is a NONEMPTY required field on a lint-clean map, so a journey
    # that exists in the map always has >= 1 clause here.
    _oracle="$(journey_field "$_jid" oracle 2>/dev/null)" || _oracle=""
    _oc_count="$(split_and "$_oracle" | wc -l | tr -d ' ')"

    if [ "$_idx" -gt "$_oc_count" ]; then
      printf 'ORACLE_CLAUSE_OUT_OF_RANGE: %s: %s\n' "$_id" "$_ref" >&2
      errors=$((errors + 1))
      continue
    fi

    _oclasses="$(journey_field "$_jid" oracle_classes 2>/dev/null)" || {
      printf 'ORACLE_CLASS_UNDECLARED: %s: %s\n' "$_id" "$_jid" >&2
      errors=$((errors + 1))
      continue
    }

    _class="$(split_and "$_oclasses" | sed -n "${_idx}p")"

    # ── ADJUDICATION: the false-gap killer ──────────────────────────────
    if [ "$_grade" = "[C-absent]" ] && [ "$_class" = "lower" ]; then
      printf 'ORACLE_CLASS_OUT_OF_SCOPE: %s: %s is a lower-level clause; a browser UAT absence claim cannot assert it as a gap — route to lower-level evidence\n' \
        "$_id" "$_ref" >&2
      errors=$((errors + 1))
    fi
  done << _OC_EOF_
$_oclines
_OC_EOF_
done

[ "$errors" -gt 0 ] && exit 1

printf 'OK: %s oracle_clause reference(s) checked across %s claim(s), zero out-of-scope\n' \
  "$_total_refs" "$(printf '%s\n' "$_claim_ids" | grep -c .)"
exit 0
