#!/bin/sh
# shellcheck shell=sh
# uat-write-run.sh NOTES_FILE EVIDENCE_DIR REPO_ROOT OUTDIR — opt-in LLM
# report-WRITER runner (spec DC-7). Mirrors uat-verify-run.sh's discipline
# exactly: SKIP default, fail-closed preconditions BEFORE any hashing or
# backend call, runner-computed facts the model must echo verbatim,
# stamp-into-scratch + gate-before-rename, trap cleans every temp on any
# failure path.
#
#   RUN_LLM_GEN unset  -> deterministic no-op (exit 0, no model, no network)
#   RUN_LLM_GEN=1 without JOURNEY_GEN_BACKEND -> fail closed
#
# Env:
#   REPORT_DATE (required) -- YYYY-MM-DD. The runner never derives dates
#     itself (no wall-clock in this layer); malformed/unset fails closed
#     BEFORE any hashing or backend call.
#   JOURNEY_MAP (optional) -- path to a JOURNEY_MAP.md. When set, its
#     content is appended to the bundle as a JOURNEY MAP EXCERPT and
#     check-uat-oracle-scope.sh gates any `- oracle_clause:` ref the model
#     emits. A ref present with JOURNEY_MAP unset is a fail-closed
#     precondition, never a silent skip -- a claim the runner cannot
#     adjudicate must not reach disk.
#
# Bundle handed to the backend: REPORT_DATE:/REPO_COMMIT: lines
# (runner-owned -- the model must echo these verbatim into the report
# header, it never derives or invents either), an ARTIFACT MANIFEST (every
# file under EVIDENCE_DIR, runner-hashed -- the ONLY artifact evidence
# lines the model may emit), the session notes verbatim, and the optional
# JOURNEY MAP EXCERPT.
#
# Deterministic validation BEFORE any final-named file exists, in order:
#   1. header echo check (report_date/repo_commit == runner's own values)
#   2. lint-uat-report.sh (schema)          -- composed, never reimplemented
#   3. check-uat-evidence.sh (re-verification against the pinned commit)
#   4. check-uat-oracle-scope.sh, composed ONLY when the output carries any
#      `- oracle_clause:` ref (JOURNEY_MAP required in that case)
# Only after ALL pass: scratch -> OUTDIR/UAT_REPORT_<date>.md (+ evidence/
# merged alongside) and OUTDIR/UAT_REPORT_<date>.writer-raw.md (mirrors
# verifier-raw). A trap cleans the whole scratch dir on any exit; nothing
# with a final OUTDIR name exists on any failure path.
#
# Relpath-resolution choice (ruling B: "solve honestly, document the
# choice"): EVIDENCE_DIR's files are COPIED -- not referenced in place --
# into an `evidence/` directory that lives alongside the report at every
# stage: inside the scratch dir during validation, and inside OUTDIR after
# install. check-uat-evidence.sh resolves artifact relpaths as
# `dirname(report)/<relpath>`; keeping the report and its evidence
# co-located (same directory, same relative structure) throughout means
# the gate resolves identically during our own pre-rename check AND on any
# later standalone re-run against the installed report. It also makes
# OUTDIR self-contained and portable: it does not depend on EVIDENCE_DIR
# continuing to exist at its original path.
#
# Codes: this runner mints NO new gate codes (rule 4, append-only unions;
# ruling C). Own failures reuse the existing closed-enum codes wherever the
# semantics genuinely match: DATE_INVALID (malformed/echo-mismatched
# REPORT_DATE), REPO_MISMATCH / TREE_DIRTY (mirrors uat-verify-run.sh's own
# precondition posture -- REPO_ROOT must be a usable, clean git repo, and
# an echoed repo_commit must match reality), TOOL_MISSING (uat_sha256,
# uat-lib.sh), MKTEMP_FAILED, WRITE_FAILED, BACKEND_FAILED. All other
# runner-level preconditions (usage, missing NOTES_FILE/EVIDENCE_DIR,
# oracle_clause refs with no JOURNEY_MAP set) fail with a plain
# "uat-write-run: <reason>" message and no dedicated code token -- the same
# uncoded-message idiom uat-verify-run.sh itself uses for its own
# backend-unset precondition. Plus pass-through of whatever
# lint-uat-report.sh / check-uat-evidence.sh / check-uat-oracle-scope.sh
# emit, and the prompt's own degenerate-input token `WRITER-FAILED`
# (uat-writer.md) -- mirrors MISSING-REPORT/MISSING-HASH in
# uat-verifier.md: a prompt-declared token documented in prose, not added
# to the doc's closed-enum code-union list.
set -u
_here="$(cd "$(dirname "$0")" && pwd)"
_prompts="$_here/../prompts"
_bin="$_here/../../bin"
# shellcheck disable=SC1091
. "$_here/../../lib/uat-lib.sh"

if [ "${RUN_LLM_GEN:-0}" != "1" ]; then
  printf 'uat-write-run: SKIP no-op (RUN_LLM_GEN not set). No model or network invoked.\n'
  printf 'Opt-in: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> REPORT_DATE=<YYYY-MM-DD> [JOURNEY_MAP=<path>] %s NOTES_FILE EVIDENCE_DIR REPO_ROOT OUTDIR\n' "$0"
  exit 0
fi
[ -n "${JOURNEY_GEN_BACKEND:-}" ] || {
  printf 'uat-write-run: RUN_LLM_GEN=1 but JOURNEY_GEN_BACKEND is unset (fail closed; no network).\n' >&2; exit 1; }

# REPORT_DATE: fail early, before any hashing or backend call -- this layer
# never derives dates itself (no wall-clock).
_report_date="${REPORT_DATE:-}"
# Bounds check only (F-DATE, mirrors lint-uat-report.sh), NOT a full
# calendar (e.g. 2026-02-31 still passes — no days-in-month/leap-year
# logic). month 01-12, day 01-31.
printf '%s\n' "$_report_date" | grep -Eq '^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$' \
  || uat_die DATE_INVALID "REPORT_DATE must be YYYY-MM-DD with month 01-12 and day 01-31, got '$_report_date'"

[ $# -eq 4 ] || {
  printf 'usage: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> REPORT_DATE=<YYYY-MM-DD> [JOURNEY_MAP=<path>] %s NOTES_FILE EVIDENCE_DIR REPO_ROOT OUTDIR\n' "$0" >&2
  exit 1; }

notes="$1"; evdir="$2"; repo="$3"; outdir="$4"

[ -f "$notes" ] || { printf 'uat-write-run: no notes file at %s\n' "$notes" >&2; exit 1; }
[ -d "$evdir" ] || { printf 'uat-write-run: no evidence directory at %s\n' "$evdir" >&2; exit 1; }

# ── preconditions, BEFORE any backend call ─────────────────────────────
commit="$(git -C "$repo" rev-parse HEAD 2>/dev/null)"
[ -n "$commit" ] || uat_die REPO_MISMATCH "$repo is not a usable git repo (cannot derive HEAD)"
[ -z "$(git -C "$repo" status --porcelain 2>&1)" ] || uat_die TREE_DIRTY "$repo working tree is not clean"

mkdir -p "$outdir" || { printf 'uat-write-run: could not create OUTDIR %s\n' "$outdir" >&2; exit 1; }

scratch="$(mktemp -d "$outdir/.uat-write-XXXXXXXX")" || uat_die MKTEMP_FAILED "fail closed"
trap 'rm -rf "$scratch"' EXIT INT TERM
mkdir -p "$scratch/evidence" || uat_die MKTEMP_FAILED "could not stage evidence directory"

# ── artifact manifest: runner-computed hashes are the ONLY artifact
# evidence the model may emit. Files are copied into the scratch dir now
# so relpaths resolve identically here (pre-rename validation) and after
# install (see the header note on the relpath-resolution choice). Built
# with a heredoc-fed while (never `| while read` -- rule 2: a
# pipeline-subshell mutation of $manifest would be silently lost). ────────
manifest=""
_filelist="$(cd "$evdir" && find . -type f | sed 's|^\./||' | sort)"
while IFS= read -r _rel; do
  [ -z "$_rel" ] && continue
  _destdir="$scratch/evidence/$(dirname "$_rel")"
  mkdir -p "$_destdir" || uat_die MKTEMP_FAILED "could not stage evidence file $_rel"
  cp "$evdir/$_rel" "$scratch/evidence/$_rel" || uat_die MKTEMP_FAILED "could not copy evidence file $_rel"
  _h="$(uat_sha256 "$scratch/evidence/$_rel")" || exit 1
  manifest="$manifest
evidence/$_rel sha256:$_h"
done <<EOF
$_filelist
EOF
manifest="$(printf '%s\n' "$manifest" | sed '/^$/d')"

# ── build the bundle ────────────────────────────────────────────────────
in_tmp="$(mktemp "$scratch/.uat-write-in-XXXXXXXX")" || uat_die MKTEMP_FAILED "fail closed"
raw_tmp="$(mktemp "$scratch/.uat-write-raw-XXXXXXXX")" || uat_die MKTEMP_FAILED "fail closed"

{
  printf 'REPORT_DATE: %s\n' "$_report_date"
  printf 'REPO_COMMIT: %s\n\n' "$commit"
  printf 'ARTIFACT MANIFEST:\n'
  if [ -n "$manifest" ]; then printf '%s\n' "$manifest"; else printf '(none)\n'; fi
  printf '\nSESSION NOTES:\n'
  cat "$notes"
  if [ -n "${JOURNEY_MAP:-}" ]; then
    printf '\nJOURNEY MAP EXCERPT:\n'
    cat "$JOURNEY_MAP"
  fi
} > "$in_tmp"

"$JOURNEY_GEN_BACKEND" "$_prompts/uat-writer.md" "$in_tmp" > "$raw_tmp" || {
  printf 'BACKEND_FAILED: backend exited non-zero on the write step\n' >&2; exit 1; }

# degenerate shape is the prompt's own bare-token contract (uat-writer.md):
# never partial output, never prose around it. It means the notes could not
# honestly be turned into a report -- die on it, nothing gets written.
if grep -q '^WRITER-FAILED:' "$raw_tmp"; then
  grep '^WRITER-FAILED:' "$raw_tmp" | head -1 >&2
  exit 1
fi

# ── stamp into a scratch file whose BASENAME already satisfies lint's
# filename<->date grammar. lint checks basename only, never the parent
# directory, so this is still a temp: its FULL PATH under $scratch is not
# the final OUTDIR path until the mv below (rule 8). ────────────────────
rep_tmp="$scratch/UAT_REPORT_${_report_date}.md"
cp "$raw_tmp" "$rep_tmp" || uat_die WRITE_FAILED "could not stage report"

# ── (1) header echo check -- the model never gets authority over pinned
# facts; a wrong echo dies here, before lint even runs ──────────────────
_out_date="$(uat_header_field "$rep_tmp" report_date)"
[ "$_out_date" = "$_report_date" ] \
  || uat_die DATE_INVALID "model echoed report_date '$_out_date' != runner's REPORT_DATE '$_report_date'"
_out_commit="$(uat_header_field "$rep_tmp" repo_commit)"
[ "$_out_commit" = "$commit" ] \
  || uat_die REPO_MISMATCH "model echoed repo_commit '$_out_commit' != runner's HEAD '$commit'"

# ── (2) schema lint, composed as an executable ──────────────────────────
/bin/sh "$_bin/lint-uat-report.sh" "$rep_tmp" || exit 1

# ── (3) evidence re-verification -- artifact relpaths resolve from
# $scratch, where evidence/ was staged above ────────────────────────────
/bin/sh "$_bin/check-uat-evidence.sh" "$rep_tmp" "$repo" || exit 1

# ── (4) oracle scope, gated -- refs present but no map is a fail-closed
# precondition, never a silent skip ──────────────────────────────────────
if grep -q '^- oracle_clause: ' "$rep_tmp"; then
  [ -n "${JOURNEY_MAP:-}" ] || {
    printf 'uat-write-run: report carries oracle_clause ref(s) but JOURNEY_MAP is not set (fail closed; cannot adjudicate)\n' >&2
    exit 1; }
  [ -f "$JOURNEY_MAP" ] || {
    printf 'uat-write-run: JOURNEY_MAP=%s does not exist\n' "$JOURNEY_MAP" >&2
    exit 1; }
  /bin/sh "$_bin/check-uat-oracle-scope.sh" "$rep_tmp" "$JOURNEY_MAP" || exit 1
fi

# ── install: only past this point does anything land at its final name ──
mv "$rep_tmp" "$outdir/UAT_REPORT_${_report_date}.md" || uat_die WRITE_FAILED "could not install report"
cp "$raw_tmp" "$outdir/UAT_REPORT_${_report_date}.writer-raw.md" || uat_die WRITE_FAILED "could not install writer-raw audit file"
mkdir -p "$outdir/evidence" || uat_die WRITE_FAILED "could not install evidence directory"
cp -R "$scratch/evidence/." "$outdir/evidence/" || uat_die WRITE_FAILED "could not install evidence files"

trap - EXIT INT TERM
rm -rf "$scratch"

printf 'uat-write-run: wrote %s and %s\n' "$outdir/UAT_REPORT_${_report_date}.md" "$outdir/UAT_REPORT_${_report_date}.writer-raw.md"
exit 0
