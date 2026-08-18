#!/bin/sh
# shellcheck shell=sh
# check-uat-verification.sh <report> <verification> <repo_root> — gate 4.3.
# The verifier's own evidence held to the same discipline as the author's
# (gate 4.2): reads are pinned to the report's repo_commit; working tree
# never read for evidence.
# Codes: STALE_VERIFICATION VERDICT_INCOMPLETE DUPLICATE_VERDICT
#        UNKNOWN_CLAIM VERDICT_UNKNOWN REGRADE_MISSING RESIDUAL_ON_CONFIRM
#        SEARCH_FORMAT ABSENCE_NO_SEARCH COMMIT_UNKNOWN TOOL_MISSING
#        MKTEMP_FAILED ROOT_MISMATCH CITATION_MISSING
#        + reused QUOTE_UNVERIFIED LINE_MISMATCH SEARCH_ERROR SEARCH_DIVERGED
#        (uat_check_quote_line / uat_check_search_line in uat-lib.sh, pinned
#        commit; COMMIT_UNKNOWN/TOOL_MISSING mirror gate 4.2's preconditions
#        so this gate is safe to run standalone, not only after 4.2.
#        MKTEMP_FAILED: the $_fail accumulator itself could not be created —
#        same fail-open as gate 4.2 without this guard; M-T1-4.)
#
# W1 (D2, fix-wave): this gate resolves its OWN <repo_root> argument to an
# absolute PHYSICAL path (cd + pwd -P) and REQUIRES the verification file's
# line 2 to read exactly `repo_root: <that resolved path>` — never trusting
# the raw argument string, and never trusting the verification file's claim
# without recomputing. ROOT_MISMATCH covers both a missing line 2 and a
# mismatched one (message text distinguishes which). Physical resolution
# means a relative arg and a symlinked arg that both point at the same real
# directory compare equal.
#
# W2 (D3-a, fix-wave): a `refute` or `downgrade` verdict — one that asserts
# something IS or IS NOT true of code reality — must carry >= 1
# `- evidence:` line (already independently re-checked against the pinned
# commit by the existing quote checker below). Before this fix a
# refute/downgrade built entirely on unverifiable prose in `- reason:` /
# `- residual:` sailed through this gate clean, with nothing left to
# re-check — the exact reason D2's wrong-repo failure mode was invisible to
# the deterministic layer. `confirm` is unchanged by this law.
set -u
_here="$(dirname "$0")"; . "$_here/../lib/uat-lib.sh"
r="${1:?usage: check-uat-verification.sh <report> <verification> <repo_root>}"
v="${2:?need verification}"
repo="${3:?need repo_root}"
rdir="$(dirname "$r")"

commit="$(uat_header_field "$r" repo_commit)"
git -C "$repo" cat-file -e "$commit^{commit}" 2>/dev/null || uat_die COMMIT_UNKNOWN "repo_commit $commit not in $repo"

rsha="$(uat_sha256 "$r")" || uat_die TOOL_MISSING "sha256 of $r failed — cannot verify (fail closed)"

# First line is the runner-stamped hash of the report; recomputed, not trusted.
_first="$(head -1 "$v")"
[ "$_first" = "reviewed_sha256: $rsha" ] \
  || uat_die STALE_VERIFICATION "first line must be 'reviewed_sha256: $rsha', got '$_first'"

# W1 (D2): line 2 is the runner-stamped repo_root; this gate resolves its
# OWN <repo_root> argument the identical way the runner does (cd + pwd -P)
# and requires an exact match — physical resolution means a relative arg
# and a symlinked arg pointing at the same real directory both compare
# equal to whatever the runner stamped.
_repo_root_abs="$(cd "$repo" 2>/dev/null && pwd -P)" \
  || uat_die ROOT_MISMATCH "repo_root argument '$repo' does not exist or is not a directory"
_second="$(sed -n '2p' "$v")"
# Plain string comparison, never a `case` glob match — $_repo_root_abs is an
# arbitrary filesystem path that could itself contain glob metacharacters
# (*, ?, [), which a `case` pattern would misinterpret.
if [ "$_second" = "repo_root: $_repo_root_abs" ]; then
  : # matches
elif [ "${_second#repo_root: }" != "$_second" ]; then
  uat_die ROOT_MISMATCH "verification repo_root '${_second#repo_root: }' != resolved repo_root '$_repo_root_abs'"
else
  uat_die ROOT_MISMATCH "verification file line 2 must be 'repo_root: $_repo_root_abs' (missing)"
fi

# Every echoed checked_hash: must equal the same recomputed hash.
for _hv in $(grep '^- checked_hash: ' "$v" | sed 's/^- checked_hash: //'); do
  [ "$_hv" = "$rsha" ] || uat_die STALE_VERIFICATION "checked_hash '$_hv' != report sha $rsha"
done

# Verdict-id set vs the report's claim-id set: membership BEFORE coverage —
# an id that doesn't exist in the report is a more specific diagnosis than
# "some claim is uncovered" (it explains why the claim looks uncovered too).
_rids="$(uat_claim_ids "$r")"
_vids="$(uat_verdict_ids "$v")"

for _vid in $_vids; do
  printf '%s\n' "$_rids" | grep -qxF "$_vid" || uat_die UNKNOWN_CLAIM "verdict for unknown claim id: $_vid"
done

_dup="$(printf '%s\n' "$_vids" | sort | uniq -d | head -1)"
[ -z "$_dup" ] || uat_die DUPLICATE_VERDICT "$_dup has more than one verdict block"

for _rid in $_rids; do
  printf '%s\n' "$_vids" | grep -qxF "$_rid" || uat_die VERDICT_INCOMPLETE "no verdict for claim $_rid"
done

_fail="$(mktemp)" || uat_die MKTEMP_FAILED "cannot create scratch file (fail closed)"
[ -n "$_fail" ] || uat_die MKTEMP_FAILED "mktemp returned empty path (fail closed)"
trap 'rm -f "$_fail"' EXIT

# uat_check_quote_line / uat_check_search_line (uat-lib.sh) read
# $repo/$commit/$rdir/$_fail from this scope.

for _id in $_rids; do
  _rblk="$(uat_claim_block "$r" "$_id")"
  _grade="$(printf '%s\n' "$_rblk" | sed -n 's/^- grade: //p' | head -1)"
  _vblk="$(uat_verdict_block "$v" "$_id")"
  _verdict="$(printf '%s\n' "$_vblk" | sed -n 's/^- verdict: //p' | head -1)"

  case "$_verdict" in
    confirm|downgrade|refute) : ;;
    *)
      printf 'VERDICT_UNKNOWN: %s: verdict must be confirm|downgrade|refute, got "%s"\n' "$_id" "$_verdict" >&2
      echo x >>"$_fail"
      continue ;;
  esac

  if [ "$_verdict" = downgrade ]; then
    _regrade="$(printf '%s\n' "$_vblk" | sed -n 's/^- regrade: //p' | head -1)"
    _regrade_ok=1
    case "$_regrade" in
      "[C]"|"[C-absent]"|"[I]"|"[G]"|"[X]") : ;;
      *) _regrade_ok=0 ;;
    esac
    if [ "$_regrade_ok" -eq 0 ] || [ "$_regrade" = "$_grade" ]; then
      printf 'REGRADE_MISSING: %s: downgrade needs a - regrade: differing from author grade %s (got "%s")\n' \
        "$_id" "$_grade" "$_regrade" >&2
      echo x >>"$_fail"
    fi
  fi

  if [ "$_verdict" = confirm ] && printf '%s\n' "$_vblk" | grep -q '^- residual: '; then
    printf 'RESIDUAL_ON_CONFIRM: %s: residual not allowed on a confirm verdict\n' "$_id" >&2
    echo x >>"$_fail"
  fi

  # W2 (D3-a): a refute/downgrade asserts something about code reality (or
  # its absence) and must carry >= 1 re-checkable `- evidence:` line — never
  # a verdict resting solely on unverifiable `- reason:`/`- residual:`
  # prose. confirm is unchanged (its own evidence-count laws live elsewhere:
  # ABSENCE_NO_SEARCH below for a [C-absent] confirm).
  if [ "$_verdict" = refute ] || [ "$_verdict" = downgrade ]; then
    _ncit="$(printf '%s\n' "$_vblk" | grep -c '^- evidence: ')"
    if [ "$_ncit" -eq 0 ]; then
      printf 'CITATION_MISSING: %s: %s verdict needs >= 1 - evidence: line\n' "$_id" "$_verdict" >&2
      echo x >>"$_fail"
    fi
  fi

  printf '%s\n' "$_vblk" | grep '^- evidence: ' | while IFS= read -r _ln; do
    uat_check_quote_line "$_id" "$_ln"
  done

  _nsr="$(printf '%s\n' "$_vblk" | grep -c '^- search: ')"
  if [ "$_verdict" = confirm ] && [ "$_grade" = "[C-absent]" ]; then
    if [ "$_nsr" -eq 0 ]; then
      printf 'ABSENCE_NO_SEARCH: %s: confirm of a [C-absent] claim needs >=1 search line\n' "$_id" >&2
      echo x >>"$_fail"
    fi
    printf '%s\n' "$_vblk" | grep '^- search: ' | while IFS= read -r _ln; do
      uat_check_search_line "$_id" "$_ln" zero
    done
  elif [ "$_nsr" -gt 0 ]; then
    printf 'SEARCH_FORMAT: %s: search: lines only allowed on a confirm of a [C-absent] claim\n' "$_id" >&2
    echo x >>"$_fail"
  fi
done

[ -s "$_fail" ] && exit 1
exit 0
