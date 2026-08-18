#!/bin/sh
# shellcheck shell=sh
# check-uat-evidence.sh <report> <repo_root> — gate 4.2.
# All reads pinned to the report's repo_commit; working tree NEVER read.
# Codes: COMMIT_UNKNOWN QUOTE_UNVERIFIED LINE_MISMATCH ARTIFACT_MISSING
#        ARTIFACT_HASH_MISMATCH SEARCH_ERROR SEARCH_DIVERGED TOOL_MISSING
#        MKTEMP_FAILED
#        (TOOL_MISSING: no sha256sum/shasum on PATH — fails closed via the
#        $_fail accumulator, never a bare `exit` inside a pipe subshell;
#        see uat_check_artifact_line in uat-lib.sh and commit a21f319.
#        MKTEMP_FAILED: the $_fail accumulator itself could not be created —
#        an unguarded `_fail="$(mktemp)"` on mktemp failure leaves $_fail
#        empty, every violation append silently no-ops against `>>""`, and
#        `[ -s "$_fail" ]` reads false — a real-violations fail-open. Guarded
#        immediately after mktemp, before the trap is installed; M-T1-4.)
set -u
_here="$(dirname "$0")"; . "$_here/../lib/uat-lib.sh"
r="${1:?usage: check-uat-evidence.sh <report> <repo_root>}"; repo="${2:?need repo_root}"
rdir="$(dirname "$r")"
commit="$(uat_header_field "$r" repo_commit)"
git -C "$repo" cat-file -e "$commit^{commit}" 2>/dev/null || uat_die COMMIT_UNKNOWN "repo_commit $commit not in $repo"

_fail="$(mktemp)" || uat_die MKTEMP_FAILED "cannot create scratch file (fail closed)"
[ -n "$_fail" ] || uat_die MKTEMP_FAILED "mktemp returned empty path (fail closed)"
trap 'rm -f "$_fail"' EXIT

# uat_check_quote_line / uat_check_artifact_line / uat_check_search_line live
# in uat-lib.sh; they read $repo/$commit/$rdir/$_fail from this scope.

for _id in $(uat_claim_ids "$r"); do
  _blk="$(uat_claim_block "$r" "$_id")"
  printf '%s\n' "$_blk" | grep '^- evidence: ' | while IFS= read -r _ln; do
    if uat_ev_is_artifact "$_ln"; then uat_check_artifact_line "$_id" "$_ln"
    else uat_check_quote_line "$_id" "$_ln"; fi
  done
  printf '%s\n' "$_blk" | grep '^- search: ' | while IFS= read -r _ln; do
    uat_check_search_line "$_id" "$_ln" zero
  done
done
[ -s "$_fail" ] && exit 1
exit 0
