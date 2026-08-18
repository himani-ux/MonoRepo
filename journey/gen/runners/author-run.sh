#!/bin/sh
# shellcheck shell=sh
# author-run.sh JOURNEY_MAP TEST_SURFACE APP_FLOW PRD JOURNEY_ID OUTDIR
#
# Thin runner for blind test authoring (Increment 2). Deterministic at the
# edges: author-bundle → model author → deterministic lint → model refuter
# (hash supplied BY THE RUNNER, echoed back, re-verified deterministically).
# NEVER promotes — a human runs journey-test-promote.sh --approve.
#
#   RUN_LLM_GEN unset  -> deterministic no-op (exit 0, no model, no network)
#   RUN_LLM_GEN=1 without JOURNEY_GEN_BACKEND -> fail closed

set -u
_here=$(cd "$(dirname "$0")" && pwd)
_prompts="$_here/../prompts"
_bin="$_here/../../bin"

if [ "${RUN_LLM_GEN:-0}" != "1" ]; then
  printf 'author-run: no-op (RUN_LLM_GEN not set). No model or network invoked.\n'
  printf 'Opt-in: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> %s JOURNEY_MAP TEST_SURFACE APP_FLOW PRD JOURNEY_ID OUTDIR\n' "$0"
  exit 0
fi
[ -n "${JOURNEY_GEN_BACKEND:-}" ] || {
  printf 'author-run: RUN_LLM_GEN=1 but JOURNEY_GEN_BACKEND is unset (fail closed; no network).\n' >&2; exit 1; }
[ $# -eq 6 ] || { printf 'usage: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> author-run.sh JOURNEY_MAP TEST_SURFACE APP_FLOW PRD JOURNEY_ID OUTDIR\n' >&2; exit 1; }
MAP="$1"; TS="$2"; APP_FLOW="$3"; PRD="$4"; JID="$5"; OUTDIR="$6"
mkdir -p "$OUTDIR" || { printf 'author-run: cannot create %s\n' "$OUTDIR" >&2; exit 1; }

_low=$(printf '%s' "$JID" | tr 'A-Z' 'a-z')

# 1. deterministic blind bundle (fails closed on gaps/anchors/status)
sh "$_bin/author-bundle.sh" "$MAP" "$TS" "$APP_FLOW" "$PRD" "$JID" "$OUTDIR" || {
  printf 'author-run: author-bundle failed (fail closed)\n' >&2; exit 1; }
_BUNDLE="$OUTDIR/author-bundle-$_low.md"

# 2. blind author (model) -> candidate spec
_SPEC="$OUTDIR/$_low.spec.candidate.ts"
"$JOURNEY_GEN_BACKEND" "$_prompts/test-author.md" "$_BUNDLE" > "$_SPEC" || {
  printf 'author-run: backend failed on the author step\n' >&2; exit 1; }
if grep -qE '^SPEC-FAILED:' "$_SPEC"; then
  printf 'author-run: author declared failure: %s (fail closed)\n' \
    "$(grep -m1 '^SPEC-FAILED:' "$_SPEC")" >&2; exit 1
fi
_first=$(awk 'NF { print; exit }' "$_SPEC")
[ "$_first" = "import { test, expect } from '@playwright/test';" ] || {
  printf 'author-run: candidate does not open with the @playwright/test import (prose or drift — fail closed)\n' >&2; exit 1; }

# 3. deterministic blindness/discipline lint BEFORE the refuter sees it
sh "$_bin/lint-journey-tests.sh" "$_SPEC" "$_BUNDLE" || {
  printf 'author-run: candidate failed lint-journey-tests (fail closed before refuter)\n' >&2; exit 1; }

# 4. refuter (model), hash supplied by the RUNNER and re-verified after
if command -v sha256sum >/dev/null 2>&1; then
  _sha=$(sha256sum "$_SPEC" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
  _sha=$(shasum -a 256 "$_SPEC" | awk '{print $1}')
else
  printf 'author-run: no sha256 tool available (fail closed)\n' >&2; exit 1
fi
_RIN="$OUTDIR/refuter-input-$_low.md"
{
  printf '# Refuter input — %s\n\n' "$JID"
  printf 'CHECKED_HASH: %s\n\n' "$_sha"
  printf '## AUTHOR BUNDLE (fidelity ground truth)\n\n'
  cat "$_BUNDLE"
  printf '\n## CANDIDATE SPEC (verbatim)\n\n'
  cat "$_SPEC"
} > "$_RIN"
_ROUT="$OUTDIR/refuter-result-$_low.md"
"$JOURNEY_GEN_BACKEND" "$_prompts/refuter-test-fidelity.md" "$_RIN" > "$_ROUT" || {
  printf 'author-run: backend failed on the refuter step\n' >&2; exit 1; }

# deterministic shape check: exactly one of the two frozen shapes
if grep -qE '^REFUTER-BLOCK:' "$_ROUT"; then
  printf 'author-run: refuter BLOCKED %s — see %s (fail closed; fix and re-run)\n' "$JID" "$_ROUT" >&2
  exit 1
fi
grep -qE '^REFUTER-NO-BLOCK:' "$_ROUT" || {
  printf 'author-run: refuter emitted neither REFUTER-BLOCK nor REFUTER-NO-BLOCK (prose is not a review — fail closed)\n' >&2; exit 1; }
grep -qE "^- journey_id:[[:space:]]*$JID([^0-9]|\$)" "$_ROUT" || {
  printf 'author-run: refuter NO-BLOCK does not name %s (fail closed)\n' "$JID" >&2; exit 1; }
_echoed=$(grep -m1 -E '^- checked_hash:' "$_ROUT" | sed 's/^- checked_hash:[[:space:]]*//;s/[[:space:]]*$//')
[ "$_echoed" = "$_sha" ] || {
  printf 'author-run: refuter checked_hash [%s] does not match the candidate [%s] (fail closed)\n' "$_echoed" "$_sha" >&2; exit 1; }

printf 'author-run: candidate spec + hash-bound refuter result written to %s. NOT promoted — run:\n' "$OUTDIR"
printf '  sh %s --approve %s %s %s %s <JOURNEY_MAP> <TESTS_DIR>\n' \
  "$_bin/journey-test-promote.sh" "$JID" "$_SPEC" "$_BUNDLE" "$_ROUT"
exit 0
