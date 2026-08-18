#!/bin/sh
# shellcheck shell=sh
# surface-run.sh APP_FLOW DESIGN_SYSTEM OUTDIR — thin runner for TEST_SURFACE
# generation (Increment 2). Deterministic at the edges: slicer → per-screen
# model call → per-entry validation → deterministic concatenate + sort (NO
# model merge stage) → lint + coverage gates. NEVER promotes — a human runs
# surface-promote.sh --approve on the candidate.
#
#   RUN_LLM_GEN unset  -> deterministic no-op (exit 0, no model, no network)
#   RUN_LLM_GEN=1 without JOURNEY_GEN_BACKEND -> fail closed
#   RUN_LLM_GEN=1 + backend -> `$JOURNEY_GEN_BACKEND <prompt> <bundle>` per screen

set -u
_here=$(cd "$(dirname "$0")" && pwd)
_prompts="$_here/../prompts"
_bin="$_here/../../bin"

if [ "${RUN_LLM_GEN:-0}" != "1" ]; then
  printf 'surface-run: no-op (RUN_LLM_GEN not set). No model or network invoked.\n'
  printf 'Opt-in: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> %s APP_FLOW DESIGN_SYSTEM OUTDIR\n' "$0"
  exit 0
fi
[ -n "${JOURNEY_GEN_BACKEND:-}" ] || {
  printf 'surface-run: RUN_LLM_GEN=1 but JOURNEY_GEN_BACKEND is unset (fail closed; no network).\n' >&2; exit 1; }
[ $# -eq 3 ] || { printf 'usage: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> surface-run.sh APP_FLOW DESIGN_SYSTEM OUTDIR\n' >&2; exit 1; }
APP_FLOW="$1"; DESIGN="$2"; OUTDIR="$3"

# 1. deterministic slice -> per-screen bundles + screens-manifest.json
sh "$_bin/surface-gen-slice.sh" "$APP_FLOW" "$DESIGN" "$OUTDIR" || {
  printf 'surface-run: slicer failed (fail closed)\n' >&2; exit 1; }

mkdir -p "$OUTDIR/entries" || { printf 'surface-run: cannot create %s/entries\n' "$OUTDIR" >&2; exit 1; }

# 2. per-screen generation, each entry validated BEFORE assembly
for _b in "$OUTDIR"/bundles/*.md; do
  [ -f "$_b" ] || continue
  _name=$(basename "$_b" .md)
  "$JOURNEY_GEN_BACKEND" "$_prompts/surface-generator.md" "$_b" > "$OUTDIR/entries/$_name.entry" || {
    printf 'surface-run: backend failed on screen %s\n' "$_name" >&2; exit 1; }

  if grep -qE '^SURFACE-FAILED:' "$OUTDIR/entries/$_name.entry"; then
    printf 'surface-run: generator declared failure on %s: %s (fail closed)\n' \
      "$_name" "$(grep -m1 '^SURFACE-FAILED:' "$OUTDIR/entries/$_name.entry")" >&2; exit 1
  fi
  # the screen's expected name + route come from the bundle, deterministically
  _want_name=$(grep -m1 -oE '"[^"]+"' "$_b" | sed 's/"//g')
  _want_route=$(grep -m1 '^route:' "$_b" | sed 's/^route:[[:space:]]*//;s/[[:space:]]*$//')
  _first=$(awk 'NF { print; exit }' "$OUTDIR/entries/$_name.entry")
  if [ "$_first" != "## SURFACE: $_want_name" ]; then
    printf 'surface-run: entry for %s does not open with "## SURFACE: %s" (prose or drift — fail closed)\n' \
      "$_name" "$_want_name" >&2; exit 1
  fi
  grep -qxF "route: $_want_route" "$OUTDIR/entries/$_name.entry" || {
    printf 'surface-run: entry for %s does not carry "route: %s" (fail closed)\n' \
      "$_name" "$_want_route" >&2; exit 1; }
done

# 3. deterministic assembly: header + entries sorted by file name (no model)
{
  printf '# TEST_SURFACE — public black-box contract (CANDIDATE)\n'
  printf '# Generated from APP_FLOW + DESIGN_SYSTEM; NOT canonical until surface-promote.sh --approve.\n'
  for _e in $(ls "$OUTDIR/entries"/*.entry | sort); do
    printf '\n'
    cat "$_e"
  done
} > "$OUTDIR/TEST_SURFACE.candidate.md"

# 4. deterministic gates on the assembled candidate
sh "$_bin/lint-test-surface.sh" "$OUTDIR/TEST_SURFACE.candidate.md" || {
  printf 'surface-run: candidate failed lint-test-surface (fail closed)\n' >&2; exit 1; }
sh "$_bin/check-surface-coverage.sh" "$APP_FLOW" "$OUTDIR/TEST_SURFACE.candidate.md" || {
  printf 'surface-run: candidate failed check-surface-coverage (fail closed)\n' >&2; exit 1; }

printf 'surface-run: candidate written to %s/TEST_SURFACE.candidate.md. NOT promoted — run surface-promote.sh --approve after human review.\n' "$OUTDIR"
exit 0
