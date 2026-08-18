#!/bin/sh
# shellcheck shell=sh
# uat-report-promote.sh <report> <repo_root> --approve — gate 4.4, the
# human trust elevation (O2), matching the journey-gen-promote.sh /
# journey-test-promote.sh --approve ceremony. The flag may appear in any
# argument position. Refuses BEFORE any other work when --approve is
# absent: nothing is written, nothing is read, no gate runs.
#
# With --approve: composes gates 4.1/4.2/4.3 as EXECUTABLES via /bin/sh
# (never re-implemented) — lint-uat-report.sh, check-uat-evidence.sh,
# check-uat-verification.sh, each `|| exit 1` with stderr passing through
# unchanged — then requires zero non-confirm verdicts and >=1 evidenced
# claim before writing the promotion marker (mktemp + trap + mv; on any
# failure nothing new exists on disk).
#
# Pairing rule: v="${r%.md}.verification.md", p="${r%.md}.promotion".
#
# Codes (own): VERIFICATION_MISSING NON_CONFIRM_VERDICT NO_EVIDENCED_CLAIMS
# TOOL_MISSING (emitted directly if its own sha256 calls fail; M-T8-1 —
# this comment was stale, the code has thrown it since the mktemp+trap
# marker-write path was added)
# + pass-through of whatever lint-uat-report.sh / check-uat-evidence.sh /
# check-uat-verification.sh emit. No timestamps anywhere in the marker.
set -u
_here="$(dirname "$0")"; . "$_here/../lib/uat-lib.sh"
_emit() { printf '%s\n' "$*" >&2; }
_die()  { _emit "$*"; exit 1; }

# ── parse: --approve may be anywhere; the remaining two args are
# positional (report, repo_root), order preserved. No arrays (bash 3.2). ──
APPROVE=0
_first=1
for _a in "$@"; do
  if [ "$_a" = "--approve" ]; then
    APPROVE=1
  else
    if [ "$_first" -eq 1 ]; then set -- "$_a"; _first=0
    else set -- "$@" "$_a"; fi
  fi
done

# --approve gates EVERYTHING: absent -> refuse before any other work,
# nothing written. Promotion is a human act, never inferred from gate
# success (O2).
if [ "$APPROVE" -ne 1 ]; then
  _emit "REFUSED: promotion requires human --approve (never automatic). Nothing written."
  exit 1
fi

r="${1:?usage: uat-report-promote.sh <report> <repo_root> --approve}"
repo_root="${2:?usage: uat-report-promote.sh <report> <repo_root> --approve}"
v="${r%.md}.verification.md"
p="${r%.md}.promotion"

/bin/sh "$_here/lint-uat-report.sh" "$r" || exit 1
/bin/sh "$_here/check-uat-evidence.sh" "$r" "$repo_root" || exit 1

[ -f "$v" ] || uat_die VERIFICATION_MISSING "no verification file at $v — run the verifier first"
/bin/sh "$_here/check-uat-verification.sh" "$r" "$v" "$repo_root" || exit 1

# Zero refute/downgrade verdicts required (every verdict must be confirm).
# Vocabulary is already guaranteed confirm|downgrade|refute by the gate
# just run, so a plain fixed-string exclusion suffices.
_bad="$(grep '^- verdict: ' "$v" | grep -v '^- verdict: confirm$' | head -1)"
[ -z "$_bad" ] || uat_die NON_CONFIRM_VERDICT "$_bad — promotion requires every verdict to be confirm"

# >=1 claim graded [C]/[C-absent]/[X] required (O11 — nothing evidenced,
# nothing to promote; a report of only [G]/[I] claims is not promotable).
_nev="$(grep -c -e '^- grade: \[C\]$' -e '^- grade: \[C-absent\]$' -e '^- grade: \[X\]$' "$r")"
[ "$_nev" -ge 1 ] || uat_die NO_EVIDENCED_CLAIMS "no claim graded [C]/[C-absent]/[X] in $r — nothing evidenced to promote"

_rsha="$(uat_sha256 "$r")" || uat_die TOOL_MISSING "sha256 of $r failed — cannot promote (fail closed)"
_vsha="$(uat_sha256 "$v")" || uat_die TOOL_MISSING "sha256 of $v failed — cannot promote (fail closed)"

# ── write the marker atomically: temp file in the same dir + trap + mv ───
_tmp="$(mktemp "$(dirname "$p")/.uat-promotion-XXXXXXXX")" || _die "mktemp failed (fail closed)"
trap 'rm -f "$_tmp"' EXIT INT TERM
{
  printf 'report_sha256: %s\n' "$_rsha"
  printf 'verification_sha256: %s\n' "$_vsha"
  printf 'approved: yes\n'
} > "$_tmp" || _die "failed to write promotion marker (fail closed)"
mv "$_tmp" "$p" || _die "failed to install $p (fail closed)"
trap - EXIT INT TERM

_emit "PROMOTED: $p written (report + verification hash-bound, approved: yes)."
exit 0
