#!/bin/sh
# shellcheck shell=sh
# check-uat-citation.sh <report> <repo_root> — gate 4.5, the authority
# check a downstream consumer runs. Green ONLY when: the promotion marker
# exists, BOTH recorded hashes match recomputed reality right now, and
# gates 4.1 + 4.2 + 4.3 (composed as EXECUTABLES via /bin/sh, never
# re-implemented) pass right now. The marker is a claim, not a proof — this
# gate re-verifies every time and never trusts it alone (O2).
#
# Pairing rule: v="${r%.md}.verification.md", p="${r%.md}.promotion".
# No timestamps anywhere.
#
# Codes (own): PROMOTION_MISSING PROMOTION_STALE TOOL_MISSING (emitted
# directly if its own sha256 calls fail; M-T8-1 — this comment was stale,
# the code has thrown it since the report/verification hash recompute was
# added)
# + pass-through of whatever lint-uat-report.sh / check-uat-evidence.sh /
# check-uat-verification.sh emit.
#
# On success: prints exactly "UAT-CITATION: green <report_sha256>" to
# stdout and exits 0.
set -u
_here="$(dirname "$0")"; . "$_here/../lib/uat-lib.sh"

r="${1:?usage: check-uat-citation.sh <report> <repo_root>}"
repo_root="${2:?usage: check-uat-citation.sh <report> <repo_root>}"
v="${r%.md}.verification.md"
p="${r%.md}.promotion"

[ -f "$p" ] || uat_die PROMOTION_MISSING "no promotion marker at $p — a verification is not authority (O2)"

_rsha="$(uat_sha256 "$r")" || uat_die TOOL_MISSING "sha256 of $r failed — cannot verify (fail closed)"
[ -f "$v" ] || uat_die PROMOTION_STALE "verification file $v is missing — the promoted pair no longer exists"
_vsha="$(uat_sha256 "$v")" || uat_die TOOL_MISSING "sha256 of $v failed — cannot verify (fail closed)"

_marker_rsha="$(uat_header_field "$p" report_sha256)"
_marker_vsha="$(uat_header_field "$p" verification_sha256)"

[ "$_marker_rsha" = "$_rsha" ] || uat_die PROMOTION_STALE "marker report_sha256 does not match recomputed $r"
[ "$_marker_vsha" = "$_vsha" ] || uat_die PROMOTION_STALE "marker verification_sha256 does not match recomputed $v"

# The marker's hashes matching is necessary but not sufficient: re-run the
# deterministic gates right now. A byte-identical pair can still have
# drifted out from under a repo_root whose pinned commit's tree changed
# underneath an artifact, etc. — never trust the marker alone.
/bin/sh "$_here/lint-uat-report.sh" "$r" || exit 1
/bin/sh "$_here/check-uat-evidence.sh" "$r" "$repo_root" || exit 1
/bin/sh "$_here/check-uat-verification.sh" "$r" "$v" "$repo_root" || exit 1

printf 'UAT-CITATION: green %s\n' "$_rsha"
exit 0
