#!/bin/sh
# fanout-run.sh [SSOT PRD APP_FLOW OUTDIR] — thin runner for doc-derived journey
# generation. It wires the three prompt contracts (fanout-generator, merge-dedup,
# refuter-fidelity) to the deterministic gates, but performs NO model or network
# call unless RUN_LLM_GEN=1 AND an operator-supplied backend command is provided.
#
# Guarantees:
#   * RUN_LLM_GEN unset (or != 1)  -> DETERMINISTIC NO-OP: exit 0, no model, no
#     network. Safe to call from default CI.
#   * RUN_LLM_GEN=1 without JOURNEY_GEN_BACKEND -> fail closed (exit 1), no network.
#   * RUN_LLM_GEN=1 with JOURNEY_GEN_BACKEND=<cmd> -> the opt-in live path. Each
#     generative step shells out to `<cmd> <prompt-file> <input>`; no vendor SDK
#     is embedded here (Claude Workflow JS or `codex exec` sh supply the backend —
#     see fanout.workflow.md). Promotion is NOT run here: it is a separate,
#     human-gated step (journey-gen-promote.sh --approve).
#
# This runner NEVER writes runtime truth and NEVER promotes. Output is a CANDIDATE.
# shellcheck shell=sh

set -u
_here=$(cd "$(dirname "$0")" && pwd)
_prompts="$_here/../prompts"
_bin="$_here/../../bin"

# ── Default: deterministic no-op. No model, no network. ───────────────────────
if [ "${RUN_LLM_GEN:-0}" != "1" ]; then
  printf 'fanout-run: no-op (RUN_LLM_GEN not set). No model or network invoked.\n'
  printf 'Opt-in live run: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> %s SSOT PRD APP_FLOW OUTDIR\n' "$0"
  exit 0
fi

# ── Opt-in live path (RUN_LLM_GEN=1) ──────────────────────────────────────────
if [ -z "${JOURNEY_GEN_BACKEND:-}" ]; then
  printf 'fanout-run: RUN_LLM_GEN=1 but JOURNEY_GEN_BACKEND is unset (fail closed; no network).\n' >&2
  exit 1
fi

[ $# -eq 4 ] || { printf 'usage: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> JOURNEY_RUNNER=<runner> fanout-run.sh SSOT PRD APP_FLOW OUTDIR\n' >&2; exit 1; }
SSOT="$1"; PRD="$2"; APP_FLOW="$3"; OUTDIR="$4"
for _f in "$SSOT" "$PRD" "$APP_FLOW"; do
  [ -r "$_f" ] || { printf 'fanout-run: input not readable: %s\n' "$_f" >&2; exit 1; }
done
# Fail EARLY on a missing runner declaration: without it the slicer emits no
# RUNNER, the generator emits 'runner: UNRESOLVED', and the run only dies at
# lint — surface the requirement before any model call instead.
[ -n "${JOURNEY_RUNNER:-}" ] || {
  printf 'fanout-run: JOURNEY_RUNNER is unset (allowed: playwright|maestro|appium|pty|http|stub) — fail closed before any model call\n' >&2; exit 1; }
mkdir -p "$OUTDIR/candidates" || { printf 'fanout-run: cannot create %s\n' "$OUTDIR" >&2; exit 1; }

# 0. doc-format preflight — every violation reported at once, actionable,
#    BEFORE any model call. JOURNEY_GEN_ALLOW_UNLINKED=1 defers unlinked ids
#    to the structured coverage-gap workflow.
sh "$_bin/check-doc-format.sh" "$PRD" "$APP_FLOW" \
  ${JOURNEY_GEN_ALLOW_UNLINKED:+--allow-unlinked} || {
  printf 'fanout-run: doc-format preflight failed — fix the docs above (fail closed)\n' >&2; exit 1; }

# 1. deterministic slice -> bundles + bundle-manifest.json
sh "$_bin/journey-gen-slice.sh" "$SSOT" "$PRD" "$APP_FLOW" "$OUTDIR" || {
  printf 'fanout-run: slicer failed (fail closed)\n' >&2; exit 1; }

# 2. per-bundle generation (fanout-generator prompt) via the operator backend,
#    each candidate validated deterministically BEFORE the merge model sees it
#    (review C3 — the generator→merge hop gets the same bracketing as the rest)
for _b in "$OUTDIR"/bundles/*.md; do
  [ -f "$_b" ] || continue
  _name=$(basename "$_b" .md)
  "$JOURNEY_GEN_BACKEND" "$_prompts/fanout-generator.md" "$_b" > "$OUTDIR/candidates/$_name.candidate" || {
    printf 'fanout-run: backend failed on bundle %s\n' "$_name" >&2; exit 1; }
  sh "$_bin/journey-gen-check-candidate.sh" "$OUTDIR/candidates/$_name.candidate" || {
    printf 'fanout-run: candidate %s failed the format check (fail closed before merge)\n' "$_name" >&2; exit 1; }
done

# 2b. existing JOURNEY-IDs for the merge's collision rule. When the target map
#     is known (JOURNEY_TARGET_MAP env or ./JOURNEY_MAP.md), its ids are
#     emitted deterministically — the merge model never reads the map itself.
_target="${JOURNEY_TARGET_MAP:-JOURNEY_MAP.md}"
if [ -f "$_target" ]; then
  JOURNEY_MAP="$_target"; export JOURNEY_MAP
  # shellcheck disable=SC1090
  . "$_here/../../lib/journey-lib.sh"
  journey_ids > "$OUTDIR/candidates/existing-ids.txt"
else
  : > "$OUTDIR/candidates/existing-ids.txt"
fi

# 3. merge + dedup (merge-dedup prompt) -> sentinel-delimited stdout, captured
#    verbatim as an audit artifact (merge.out)
"$JOURNEY_GEN_BACKEND" "$_prompts/merge-dedup.md" "$OUTDIR/candidates" > "$OUTDIR/merge.out" || {
  printf 'fanout-run: backend failed on merge/dedup\n' >&2; exit 1; }

# 3b. deterministic split: merge.out -> the three §5.1/§5.2 artifacts.
#     Artifact materialization NEVER depends on model initiative (review C2).
sh "$_bin/journey-gen-split.sh" "$OUTDIR/merge.out" "$OUTDIR" || {
  printf 'fanout-run: merge output failed the sentinel split (fail closed)\n' >&2; exit 1; }

# 4. deterministic coverage gate over the merged candidate (completeness proof).
#    HARD requirement — a missing artifact is a failure, never a skip (review C1).
for _a in JOURNEY_MAP.generated.md JOURNEY_COVERAGE_MANIFEST.json JOURNEY_COVERAGE_GAPS.md; do
  [ -f "$OUTDIR/$_a" ] || {
    printf 'fanout-run: merge did not materialize %s (fail closed)\n' "$_a" >&2; exit 1; }
done
sh "$_bin/check-journey-coverage.sh" "$PRD" "$APP_FLOW" \
  "$OUTDIR/JOURNEY_MAP.generated.md" "$OUTDIR/JOURNEY_COVERAGE_MANIFEST.json" "$OUTDIR/JOURNEY_COVERAGE_GAPS.md" || {
  printf 'fanout-run: coverage gate failed on the merged candidate (fail closed)\n' >&2; exit 1; }

# 4b. deterministic provenance gate: quotes verbatim-grounded in the docs,
#     no covered FEAT's AC dropped from an oracle (oracle-dilution catch)
sh "$_bin/check-journey-provenance.sh" "$PRD" "$APP_FLOW" \
  "$OUTDIR/JOURNEY_MAP.generated.md" "$OUTDIR/JOURNEY_COVERAGE_MANIFEST.json" "$SSOT" || {
  printf 'fanout-run: provenance gate failed on the merged candidate (fail closed)\n' >&2; exit 1; }

# 5. refuter fidelity review (refuter-fidelity prompt) -> review-only findings
"$JOURNEY_GEN_BACKEND" "$_prompts/refuter-fidelity.md" "$OUTDIR" > "$OUTDIR/JOURNEY_FIDELITY_REVIEW.md" || {
  printf 'fanout-run: backend failed on refuter\n' >&2; exit 1; }

# 5b. hash-bind the review to THIS candidate (runner-attested, deterministic).
#     journey-gen-promote.sh Gate 3b recomputes and compares — a stale review
#     from a previous candidate can never bless this one.
if command -v sha256sum >/dev/null 2>&1; then
  _fsha=$(sha256sum "$OUTDIR/JOURNEY_MAP.generated.md" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
  _fsha=$(shasum -a 256 "$OUTDIR/JOURNEY_MAP.generated.md" | awk '{print $1}')
else
  printf 'fanout-run: no sha256 tool available (fail closed)\n' >&2; exit 1
fi
_ftmp=$(mktemp "${TMPDIR:-/tmp}/journey-fid-XXXXXXXX") || {
  printf 'fanout-run: mktemp failed (fail closed)\n' >&2; exit 1; }
{ printf 'reviewed_sha256: %s\n' "$_fsha"; cat "$OUTDIR/JOURNEY_FIDELITY_REVIEW.md"; } > "$_ftmp" \
  && mv "$_ftmp" "$OUTDIR/JOURNEY_FIDELITY_REVIEW.md" || {
  rm -f "$_ftmp"; printf 'fanout-run: could not stamp the fidelity review (fail closed)\n' >&2; exit 1; }

printf 'fanout-run: candidate written to %s. NOT promoted — run journey-gen-promote.sh --approve after human review.\n' "$OUTDIR"
exit 0
