#!/bin/sh
# shellcheck shell=sh
# uat-verify-run.sh <report> <repo_root> — opt-in LLM verifier runner
# (spec §5.2). Composes: preconditions (report exists, repo working tree
# is exactly the report's pinned repo_commit and is clean) -> hash the
# report deterministically -> hand the model CHECKED_HASH + the report
# verbatim -> gate 4.3 (check-uat-verification.sh) re-verifies the model's
# own evidence/search citations against the pinned commit -> only on gate
# PASS does anything land on disk.
#
#   RUN_LLM_GEN unset  -> deterministic no-op (exit 0, no model, no network)
#   RUN_LLM_GEN=1 without JOURNEY_GEN_BACKEND -> fail closed
#
# Write-then-rename: every temp file is built via mktemp in the report's
# own directory; a trap removes them on any exit. On any failure path
# (including gate 4.3 rejecting the model's output) NOTHING new exists on
# disk. Only after check-uat-verification.sh passes are the verification
# and raw-audit temp files renamed into their final names.
#
# Codes (own): MISSING-REPORT REPO_MISMATCH TREE_DIRTY BACKEND_FAILED
#              MKTEMP_FAILED WRITE_FAILED
#              + MISSING-REPORT / MISSING-HASH / MISSING-ROOT pass-through of
#              the prompt's own degenerate-input tokens (uat-verifier.md)
#              + pass-through of whatever check-uat-verification.sh emits
#              + TOOL_MISSING (uat_sha256, uat-lib.sh)
#
# W1 (D2, fix-wave): REPO_ROOT is resolved to an ABSOLUTE PHYSICAL path (cd +
# pwd -P — never the raw, possibly-relative or symlinked argument) and
# carried IN-BAND from here on: the backend input file gains a
# `REPO_ROOT: <abs path>` line directly after `CHECKED_HASH: <sha>`, and the
# verification file gains a runner-stamped line 2 `repo_root: <abs path>`
# (line 1 stays `reviewed_sha256: <sha>`; both lines are runner-owned, never
# model-written). Before this fix REPO_ROOT was purely an ambient
# convention (the backend process's own cwd) — nothing in the data handed to
# the backend named it, so a live agentic backend launched from the wrong
# cwd could confidently reason about the wrong repository and gate 4.3 had
# no way to notice (the live characterization pass's single highest-signal
# finding).
set -u
_here="$(cd "$(dirname "$0")" && pwd)"
_prompts="$_here/../prompts"
_bin="$_here/../../bin"
# shellcheck disable=SC1091
. "$_here/../../lib/uat-lib.sh"

if [ "${RUN_LLM_GEN:-0}" != "1" ]; then
  printf 'uat-verify-run: SKIP no-op (RUN_LLM_GEN not set). No model or network invoked.\n'
  printf 'Opt-in: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> %s REPORT REPO_ROOT\n' "$0"
  exit 0
fi
[ -n "${JOURNEY_GEN_BACKEND:-}" ] || {
  printf 'uat-verify-run: RUN_LLM_GEN=1 but JOURNEY_GEN_BACKEND is unset (fail closed; no network).\n' >&2; exit 1; }
[ $# -eq 2 ] || {
  printf 'usage: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> uat-verify-run.sh <report> <repo_root>\n' >&2; exit 1; }

r="$1"; repo="$2"

# M-T1-2 guardrail (phase-review, mandatory): existence check BEFORE any
# read of $r. uat_sha256 on a missing file returns empty output + exit 0
# (the underlying sha tool's own error is swallowed by the awk pipeline),
# and uat_header_field on a missing file just prints nothing — either one
# would silently degrade into a wrong downstream code (an empty repo_commit
# masquerading as REPO_MISMATCH, or a poisoned empty hash flowing into
# reviewed_sha256/checked_hash). Check existence first and die on its own
# unambiguous code instead.
[ -f "$r" ] || uat_die MISSING-REPORT "no report file at $r"

# ── preconditions, BEFORE any backend call ─────────────────────────────
commit="$(uat_header_field "$r" repo_commit)"
# M-T7-2 guardrail (final review): an empty $commit (missing/blank
# repo_commit header) must not reach the HEAD comparison below — HEAD is
# never empty for a real repo, so `[ "$HEAD" = "$commit" ]` would already
# fail correctly in the common case, but that's incidental, not a
# guarantee (an unborn/detached-HEAD edge could make `git rev-parse HEAD`
# itself fail closed to empty too, and two empties would compare equal).
# Diagnose the actually-missing precondition on its own unambiguous code.
[ -n "$commit" ] || uat_die REPO_MISMATCH "report has no repo_commit (fail closed)"

# W1 (D2): resolve REPO_ROOT to an absolute PHYSICAL path early — `cd` into
# it and `pwd -P` (resolves symlinks) rather than trusting the raw argument
# string, which may be relative or pass through a symlink. Everything
# downstream (HEAD/tree checks, the backend bundle, the verification
# stamp, and the arg handed to gate 4.3) uses this resolved value, never
# the raw $repo argument directly.
repo_root_abs="$(cd "$repo" 2>/dev/null && pwd -P)" || uat_die REPO_MISMATCH "repo_root $repo does not exist or is not a directory"

HEAD="$(git -C "$repo_root_abs" rev-parse HEAD 2>/dev/null)"
[ "$HEAD" = "$commit" ] || uat_die REPO_MISMATCH "repo HEAD $HEAD != report repo_commit $commit"
[ -z "$(git -C "$repo_root_abs" status --porcelain)" ] || uat_die TREE_DIRTY "$repo_root_abs working tree is not clean"

rsha=$(uat_sha256 "$r") || exit 1

rdir="$(dirname "$r")"
in_tmp="$(mktemp "$rdir/.uat-verify-in-XXXXXXXX")" || uat_die MKTEMP_FAILED "fail closed"
raw_tmp="$(mktemp "$rdir/.uat-verify-raw-XXXXXXXX")" || { rm -f "$in_tmp"; uat_die MKTEMP_FAILED "fail closed"; }
ver_tmp="$(mktemp "$rdir/.uat-verify-ver-XXXXXXXX")" || { rm -f "$in_tmp" "$raw_tmp"; uat_die MKTEMP_FAILED "fail closed"; }
trap 'rm -f "$in_tmp" "$raw_tmp" "$ver_tmp"' EXIT INT TERM

# input handed to the backend: CHECKED_HASH (runner-computed, never the
# model's to derive), REPO_ROOT (runner-resolved, absolute physical path —
# W1/D2, never the model's to derive or infer from its own ambient cwd), a
# blank line, then the report verbatim.
{ printf 'CHECKED_HASH: %s\n' "$rsha"; printf 'REPO_ROOT: %s\n\n' "$repo_root_abs"; cat "$r"; } > "$in_tmp"

"$JOURNEY_GEN_BACKEND" "$_prompts/uat-verifier.md" "$in_tmp" > "$raw_tmp" || {
  printf 'BACKEND_FAILED: backend exited non-zero on the verify step\n' >&2; exit 1; }

# degenerate shapes are the prompt's own bare-token contract
# (uat-verifier.md): never partial output, never both, never prose around
# them. Either one means the model saw a report/hash/root it couldn't
# use — die on that exact token, nothing gets written.
if grep -qE '^(MISSING-REPORT|MISSING-HASH|MISSING-ROOT)$' "$raw_tmp"; then
  _tok="$(grep -oE '^(MISSING-REPORT|MISSING-HASH|MISSING-ROOT)$' "$raw_tmp" | head -1)"
  uat_die "$_tok" "backend declared a degenerate input for $r"
fi

# stamp reviewed_sha256 (line 1) and repo_root (line 2) ourselves — never
# trust the model to echo either as the file's own header lines;
# check-uat-verification.sh recomputes/re-resolves and compares both anyway,
# but the runner is the one making the claim here (W1/D2: both runner-owned,
# never model-written).
{ printf 'reviewed_sha256: %s\n' "$rsha"; printf 'repo_root: %s\n\n' "$repo_root_abs"; cat "$raw_tmp"; } > "$ver_tmp"

/bin/sh "$_bin/check-uat-verification.sh" "$r" "$ver_tmp" "$repo_root_abs" || exit 1

# only past this point does the gate consider the model's evidence sound
# against the pinned commit — stamp-after-validate, never before.
mv "$ver_tmp" "${r%.md}.verification.md" || uat_die WRITE_FAILED "could not install verification file"
mv "$raw_tmp" "${r%.md}.verifier-raw.md" || uat_die WRITE_FAILED "could not install verifier-raw file"
rm -f "$in_tmp"
trap - EXIT INT TERM

printf 'uat-verify-run: wrote %s and %s\n' "${r%.md}.verification.md" "${r%.md}.verifier-raw.md"
exit 0
