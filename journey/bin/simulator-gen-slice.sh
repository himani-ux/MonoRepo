#!/bin/sh
# shellcheck shell=sh
# simulator-gen-slice.sh SSOT TEST_SURFACE OUT_DIR
#
# Deterministic PER-PERSONA bundle slicer for the Increment-4 simulator
# engine (spec DC-3, ruling C). One bundle per persona, containing ONLY:
#   * THAT persona's block, verbatim — never another persona's;
#   * the FULL TEST_SURFACE, verbatim (the ONLY interface knowledge the
#     brain is allowed — no PRD, no APP_FLOW, no src/);
#   * Generation Context (APP_TARGET, APP_BUILD, RUNNER, injected from env)
#     + the inlined JOURNEY_MAP schema (frozen candidate field shape).
#
# Contrast with persona-gen-slice.sh (Increment 3): THAT slicer skips
# personas whose `known_misbehaviors:` is `[none: ...]`, because its whole
# candidate is built around one misbehavior annotation. This slicer does
# NOT skip them — the simulator's core mechanic is goal-pursuit under a
# patience budget, not misbehavior injection. A careful, low-error-tendency
# persona with no declared misbehaviors still has a real goal and a real
# patience budget, and can still surface real friction with zero
# characteristic mistakes of its own. Every persona in the SSOT gets a
# bundle here.
#
# v1 scope (documented, not a bug): one bundle per PERSONA, using that
# persona's own `goal:` field — NOT a (FEAT x persona) fan-out like
# persona-gen-slice.sh. The simulator explores; the map already has
# per-FEAT coverage from the DERIVED and PERSONA engines. A future
# increment MAY fan a persona out across multiple goals; v1 does not.
#
# Fail closed: SSOT/TEST_SURFACE unreadable, SSOT fails lint-personas.sh,
# TEST_SURFACE fails lint-test-surface.sh, or SIM_APP_TARGET/SIM_APP_BUILD
# are unset (runner-declared facts the bundle injects — never inferred, per
# house rule 6). No source code ever enters a bundle.
# Deps: POSIX sh, awk, grep, sed.

set -u
_die() { printf '%s\n' "$*" >&2; exit 1; }
_here=$(cd "$(dirname "$0")" && pwd)

[ $# -eq 3 ] || _die "usage: simulator-gen-slice.sh SSOT TEST_SURFACE OUT_DIR"
SSOT="$1"; TEST_SURFACE="$2"; OUTDIR="$3"
for _f in "$SSOT" "$TEST_SURFACE"; do
  [ -r "$_f" ] || _die "simulator-gen-slice: file not readable: $_f"
done
mkdir -p "$OUTDIR/bundles" || _die "cannot create output dir: $OUTDIR/bundles"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

# personas must lint before slicing (schema is the contract)
sh "$_here/lint-personas.sh" "$SSOT" >/dev/null 2>&1 || \
  _die "simulator-gen-slice: SSOT personas fail lint-personas.sh (fix the schema first; fail closed)"

# TEST_SURFACE must lint before it is trusted as the brain's entire
# interface knowledge — a stale/malformed contract must never reach a
# model as if it were ground truth.
sh "$_here/lint-test-surface.sh" "$TEST_SURFACE" >/dev/null 2>&1 || \
  _die "simulator-gen-slice: TEST_SURFACE fails lint-test-surface.sh (fix the contract first; fail closed)"

_TEMPLATE="$_here/../JOURNEY_MAP.template.md"
[ -r "$_TEMPLATE" ] || _die "simulator-gen-slice: template not readable: $_TEMPLATE (fail closed)"

# runner-declared facts (house rule 6): never inferred, never defaulted.
_APP_TARGET="${SIM_APP_TARGET:-}"
_APP_BUILD="${SIM_APP_BUILD:-}"
[ -n "$_APP_TARGET" ] || _die "simulator-gen-slice: SIM_APP_TARGET is unset (fail closed; runner-declared, never inferred)"
[ -n "$_APP_BUILD" ] || _die "simulator-gen-slice: SIM_APP_BUILD is unset (fail closed; runner-declared, never inferred)"

# JOURNEY_RUNNER: same idiom as persona-gen-slice.sh — optional here (the
# simulator-run.sh runner itself requires it BEFORE calling this slicer),
# format-validated when present so a bogus value never reaches a bundle.
_RUNNER_VAL=""
if [ -n "${JOURNEY_RUNNER:-}" ]; then
  _RUNNER_VAL=$(printf '%s' "$JOURNEY_RUNNER" | tr '[:upper:]' '[:lower:]')
  case "$_RUNNER_VAL" in
    playwright|maestro|appium|pty|http) : ;;
    stub) [ "${ALLOW_STUB_RUNNER:-}" = "1" ] || _die "simulator-gen-slice: 'stub' runner requires ALLOW_STUB_RUNNER=1" ;;
    *) _die "simulator-gen-slice: unknown JOURNEY_RUNNER '$JOURNEY_RUNNER' (allowed: playwright|maestro|appium|pty|http|stub)" ;;
  esac
fi

# ── personas: id, name, FULL block (never skipped, contrast above) ────────────
awk -v out="$_tmp" '
  /^## Personas/ { inp = 1; next }
  inp && /^## /  { inp = 0; next }
  inp && /^### / {
    if (!match($0, /P[0-9]+/)) { cur = ""; next }
    id = substr($0, RSTART, RLENGTH)
    name = ""
    if (match($0, /"[^"]+"/)) name = substr($0, RSTART + 1, RLENGTH - 2)
    printf "%s\t%s\n", id, name >> (out "/personas.tsv")
    cur = out "/pblock_" id ".txt"
    print $0 > cur
    next
  }
  inp && cur != "" { print >> cur }
' "$SSOT"
[ -s "$_tmp/personas.tsv" ] || _die "NO_PERSONAS: no personas in the SSOT (fail closed)"

# ── emit one bundle per persona ────────────────────────────────────────────
_bundles_json="[]"
while IFS="$(printf '\t')" read -r _pid _pname; do
  [ -n "$_pid" ] || continue
  _low_p=$(printf '%s' "$_pid" | tr 'A-Z' 'a-z')
  _brel="bundles/${_low_p}.md"
  _goal=$(grep -m1 -E '^goal:' "$_tmp/pblock_${_pid}.txt" | sed 's/^goal:[[:space:]]*//;s/[[:space:]]*$//')
  {
    printf '# Simulator bundle: %s — "%s"\n\n' "$_pid" "$_pname"
    printf '## Persona (THIS bundle persona ONLY — its full definition, alongside the TEST_SURFACE below, is your entire world)\n\n'
    cat "$_tmp/pblock_${_pid}.txt"
    printf '\n## TEST_SURFACE (verbatim — the ONLY interface knowledge you are allowed)\n\n'
    cat "$TEST_SURFACE"
    printf '\n## Generation Context\n\n'
    printf 'APP_TARGET: %s\n' "$_APP_TARGET"
    printf 'APP_BUILD:  %s\n' "$_APP_BUILD"
    [ -n "$_RUNNER_VAL" ] && printf 'RUNNER:     %s\n' "$_RUNNER_VAL"
    printf '\n## Schema (inlined from journey/JOURNEY_MAP.template.md)\n\n'
    cat "$_TEMPLATE"
  } > "$OUTDIR/$_brel"
  _bundles_json=$(printf '%s' "$_bundles_json" | jq \
    --arg p "$_pid" --arg n "$_pname" --arg path "$_brel" --arg g "$_goal" \
    '. + [{persona:$p,name:$n,bundle_path:$path,goal:$g}]')
done < "$_tmp/personas.tsv"

_count=$(printf '%s' "$_bundles_json" | jq 'length')
[ "$_count" -gt 0 ] || \
  _die "NO_BUNDLES: zero persona bundles emitted (fail closed)"

jq -n --argjson bundles "$_bundles_json" '{bundles:$bundles}' > "$OUTDIR/simulator-manifest.json"

exit 0
