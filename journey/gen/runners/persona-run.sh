#!/bin/sh
# shellcheck shell=sh
# persona-run.sh SSOT PRD APP_FLOW OUTDIR [PERSONA_GAPS]
#
# Thin runner for persona-journey generation (Increment 3). Deterministic at
# the edges; NO model merge stage — (FEAT × persona) candidates are disjoint,
# so assembly is concatenation with runner-assigned ids (sequential from 201,
# skipping existing-ids). NEVER promotes: a human runs
#   journey-gen-promote.sh --origin PERSONA ... --approve
#
#   RUN_LLM_GEN unset  -> deterministic no-op (exit 0, no model, no network)
#   RUN_LLM_GEN=1 without JOURNEY_GEN_BACKEND -> fail closed
#   JOURNEY_RUNNER required (fail EARLY, before any model call)
#
# Refuter binding: the runner computes the candidate hash, the model echoes
# it per journey (REFUTER-NO-BLOCK), the runner re-verifies name+hash for
# EVERY journey, then deterministically adapts the verified result into the
# promote-compatible FIDELITY shape (reviewed_sha256 + per-journey lines).
# The raw refuter output is kept as an audit artifact.
#
# PERSONA journeys model USER BEHAVIOR, not tested behavior — nothing here
# writes tests, runtime status, or ledger data.

set -u
_here=$(cd "$(dirname "$0")" && pwd)
_prompts="$_here/../prompts"
_bin="$_here/../../bin"

if [ "${RUN_LLM_GEN:-0}" != "1" ]; then
  printf 'persona-run: no-op (RUN_LLM_GEN not set). No model or network invoked.\n'
  printf 'Opt-in: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> JOURNEY_RUNNER=<runner> %s SSOT PRD APP_FLOW OUTDIR [PERSONA_GAPS]\n' "$0"
  exit 0
fi
[ -n "${JOURNEY_GEN_BACKEND:-}" ] || {
  printf 'persona-run: RUN_LLM_GEN=1 but JOURNEY_GEN_BACKEND is unset (fail closed; no network).\n' >&2; exit 1; }
[ $# -eq 4 ] || [ $# -eq 5 ] || {
  printf 'usage: RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND=<cmd> JOURNEY_RUNNER=<runner> persona-run.sh SSOT PRD APP_FLOW OUTDIR [PERSONA_GAPS]\n' >&2; exit 1; }
SSOT="$1"; PRD="$2"; APP_FLOW="$3"; OUTDIR="$4"; PGAPS="${5:-/dev/null}"
[ -n "${JOURNEY_RUNNER:-}" ] || {
  printf 'persona-run: JOURNEY_RUNNER is unset (allowed: playwright|maestro|appium|pty|http|stub) — fail closed before any model call\n' >&2; exit 1; }
mkdir -p "$OUTDIR/candidates" || { printf 'persona-run: cannot create %s\n' "$OUTDIR" >&2; exit 1; }

# 0. preflights — every doc violation reported before any model call
sh "$_bin/lint-personas.sh" "$SSOT" || {
  printf 'persona-run: lint-personas failed (fail closed)\n' >&2; exit 1; }
sh "$_bin/check-doc-format.sh" "$PRD" "$APP_FLOW" \
  ${JOURNEY_GEN_ALLOW_UNLINKED:+--allow-unlinked} || {
  printf 'persona-run: doc-format preflight failed (fail closed)\n' >&2; exit 1; }

# 1. deterministic slice -> (FEAT × persona) bundles
sh "$_bin/persona-gen-slice.sh" "$SSOT" "$PRD" "$APP_FLOW" "$OUTDIR" || {
  printf 'persona-run: slicer failed (fail closed)\n' >&2; exit 1; }

# 2. per-bundle generation, each candidate validated with the DECLARED origin
for _b in "$OUTDIR"/bundles/*.md; do
  [ -f "$_b" ] || continue
  _name=$(basename "$_b" .md)
  "$JOURNEY_GEN_BACKEND" "$_prompts/persona-journey-generator.md" "$_b" \
    > "$OUTDIR/candidates/$_name.candidate" || {
    printf 'persona-run: backend failed on bundle %s\n' "$_name" >&2; exit 1; }
  sh "$_bin/journey-gen-check-candidate.sh" "$OUTDIR/candidates/$_name.candidate" --origin PERSONA || {
    printf 'persona-run: candidate %s failed the format check (fail closed before assembly)\n' "$_name" >&2; exit 1; }
done

# 3. deterministic assembly — ids from 201, skipping the target map's ids
_target="${JOURNEY_TARGET_MAP:-JOURNEY_MAP.md}"
: > "$OUTDIR/existing-ids.txt"
if [ -f "$_target" ]; then
  JOURNEY_MAP="$_target"; export JOURNEY_MAP
  # shellcheck disable=SC1090
  . "$_here/../../lib/journey-lib.sh"
  journey_ids > "$OUTDIR/existing-ids.txt"
fi

_next=201
_next_free() {
  while grep -qxF "JOURNEY-$_next" "$OUTDIR/existing-ids.txt"; do
    _next=$((_next + 1))
  done
}

_GEN="$OUTDIR/JOURNEY_MAP.generated.md"
_MAN="$OUTDIR/JOURNEY_COVERAGE_MANIFEST.json"
printf '# JOURNEY_MAP (generated) — PERSONA candidates (NOT canonical until --origin PERSONA promotion)\n' > "$_GEN"
printf '{}' > "$_MAN"

for _c in $(ls "$OUTDIR"/candidates/*.candidate 2>/dev/null | sort); do
  _next_free
  _jid="JOURNEY-$_next"; _next=$((_next + 1))

  # block: candidate heading -> assigned id; strip the field_sources fence
  awk -v jid="$_jid" '
    /^## JOURNEY-CANDIDATE — / { sub(/^## JOURNEY-CANDIDATE/, "## " jid); inb = 1 }
    /^```json field_sources$/ { infs = 1; next }
    /^```$/ && infs           { infs = 0; next }
    inb && !infs { print }
  ' "$_c" >> "$_GEN"
  printf '\n' >> "$_GEN"

  # manifest entry: covers/flows from the block + the candidate fence verbatim
  awk '/^```json field_sources$/ { infs = 1; next } /^```$/ && infs { infs = 0; next } infs { print }' \
    "$_c" > "$OUTDIR/.fs.json"
  _covers=$(awk '/^covers:/ { sub(/^covers:[ \t]*/, ""); sub(/[ \t]+$/, ""); print; exit }' "$_c")
  _flows=$(awk '/^flows:/ { sub(/^flows:[ \t]*/, ""); sub(/[ \t]+$/, ""); print; exit }' "$_c")
  jq --arg j "$_jid" --arg c "$_covers" --arg f "$_flows" --slurpfile fs "$OUTDIR/.fs.json" \
    '.[$j] = { covers: ($c | split(",") | map(gsub("^\\s+|\\s+$"; "")) | map(select(. != ""))),
               flows:  ($f | split(",") | map(gsub("^\\s+|\\s+$"; "")) | map(select(. != ""))),
               field_sources: $fs[0] }' "$_MAN" > "$_MAN.tmp" && mv "$_MAN.tmp" "$_MAN" || {
    printf 'persona-run: manifest assembly failed for %s (fail closed)\n' "$_jid" >&2; exit 1; }
  rm -f "$OUTDIR/.fs.json"
done

# 4. deterministic gates on the assembled candidate
sh "$_bin/lint-journey-map.sh" "$_GEN" || {
  printf 'persona-run: assembled candidate failed lint-journey-map (fail closed)\n' >&2; exit 1; }
sh "$_bin/check-journey-provenance.sh" "$PRD" "$APP_FLOW" "$_GEN" "$_MAN" "$SSOT" || {
  printf 'persona-run: assembled candidate failed check-journey-provenance (fail closed)\n' >&2; exit 1; }
sh "$_bin/check-persona-journeys.sh" "$_GEN" "$SSOT" || {
  printf 'persona-run: assembled candidate failed check-persona-journeys (fail closed)\n' >&2; exit 1; }
sh "$_bin/check-persona-coverage.sh" "$PRD" "$SSOT" "$_GEN" "$PGAPS" || {
  printf 'persona-run: assembled candidate failed check-persona-coverage (fail closed)\n' >&2; exit 1; }

# 5. refuter — hash supplied by the runner, echoed per journey, re-verified
if command -v sha256sum >/dev/null 2>&1; then
  _sha=$(sha256sum "$_GEN" | awk '{print $1}')
elif command -v shasum >/dev/null 2>&1; then
  _sha=$(shasum -a 256 "$_GEN" | awk '{print $1}')
else
  printf 'persona-run: no sha256 tool available (fail closed)\n' >&2; exit 1
fi
_RIN="$OUTDIR/refuter-input.md"
{
  printf '# Refuter input — PERSONA candidates\n\nCHECKED_HASH: %s\n\n' "$_sha"
  printf '## SSOT Personas (ground truth)\n\n'
  awk '/^## Personas/, /^## System Context/' "$SSOT" | sed '$d'
  printf '\n## Source bundles (ground truth)\n\n'
  for _b in "$OUTDIR"/bundles/*.md; do [ -f "$_b" ] && { cat "$_b"; printf '\n'; }; done
  printf '\n## CANDIDATE MAP (verbatim)\n\n'
  cat "$_GEN"
} > "$_RIN"
_ROUT="$OUTDIR/refuter-result.md"
"$JOURNEY_GEN_BACKEND" "$_prompts/refuter-persona-fidelity.md" "$_RIN" > "$_ROUT" || {
  printf 'persona-run: backend failed on the refuter step\n' >&2; exit 1; }

if grep -qE '^REFUTER-BLOCK:' "$_ROUT"; then
  printf 'persona-run: refuter BLOCKED — see %s (fail closed; fix and re-run)\n' "$_ROUT" >&2
  exit 1
fi
grep -qE '^REFUTER-NO-BLOCK:' "$_ROUT" || {
  printf 'persona-run: refuter emitted neither shape (prose is not a review — fail closed)\n' >&2; exit 1; }

# every assembled journey must be NO-BLOCKed with the exact hash
JOURNEY_MAP="$_GEN"; export JOURNEY_MAP
# shellcheck disable=SC1090
. "$_here/../../lib/journey-lib.sh"
_FID="$OUTDIR/JOURNEY_FIDELITY_REVIEW.md"
printf 'reviewed_sha256: %s\n' "$_sha" > "$_FID"
for _jid in $(journey_ids | sort -u); do
  _jhash=$(awk -v jid="$_jid" '
    /^REFUTER-NO-BLOCK:/ { inb = 1; seen = 0; next }
    inb && /^- journey_id:/ { seen = (index($0, jid) > 0); next }
    inb && /^- checked_hash:/ { if (seen) { sub(/^- checked_hash:[ \t]*/, ""); print; exit } next }
    /^[A-Z]/ { inb = 0 }
  ' "$_ROUT")
  if [ -z "$_jhash" ]; then
    printf 'persona-run: refuter silent on %s (silence is not a review — fail closed)\n' "$_jid" >&2; exit 1
  fi
  if [ "$_jhash" != "$_sha" ]; then
    printf 'persona-run: refuter checked_hash for %s [%s] does not match the candidate [%s] (fail closed)\n' \
      "$_jid" "$_jhash" "$_sha" >&2; exit 1
  fi
  printf 'correct: %s — refuter REFUTER-NO-BLOCK (hash-bound, runner-verified) — evidence: refuter-result.md\n' "$_jid" >> "$_FID"
done

printf 'persona-run: PERSONA candidate + hash-bound fidelity written to %s. NOT promoted — run:\n' "$OUTDIR"
printf '  sh %s --origin PERSONA %s %s %s %s <JOURNEY_COVERAGE_GAPS> %s <TARGET_MAP> --approve\n' \
  "$_bin/journey-gen-promote.sh" "$PRD" "$APP_FLOW" "$_GEN" "$_MAN" "$_FID"
exit 0
