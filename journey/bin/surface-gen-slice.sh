#!/bin/sh
# shellcheck shell=sh
# surface-gen-slice.sh APP_FLOW DESIGN_SYSTEM OUT_DIR
#
# Deterministic per-screen bundle slicer for TEST_SURFACE generation
# (Increment 2). One bundle per '## Screens' entry, containing:
#   * screen id / name / route / states (from APP_FLOW — the oracle side);
#   * the AFJ journey entries whose steps mention the screen's route
#     (what the selectors must support);
#   * the FULL design-system doc (enrichment, not oracle — its absence for a
#     screen never blocks the bundle);
#   * the frozen '## SURFACE:' entry format the generator must emit.
#
# Fail closed: SCREEN_UNIDDED (### heading without SCR-<n>), SCREEN_UNNAMED
# (no quoted name), SCREEN_NO_ROUTE, DUPLICATE_SCREEN_ID, NO_SCREENS,
# unreadable inputs. Never invents screens, routes, selectors, or components.
# Deps: POSIX sh, awk, grep, sed.

set -u
_die() { printf '%s\n' "$*" >&2; exit 1; }

[ $# -eq 3 ] || _die "usage: surface-gen-slice.sh APP_FLOW DESIGN_SYSTEM OUT_DIR"
APP_FLOW="$1"; DESIGN="$2"; OUTDIR="$3"
[ -r "$APP_FLOW" ] || _die "surface-gen-slice: file not readable: $APP_FLOW"
[ -r "$DESIGN" ]   || _die "surface-gen-slice: file not readable: $DESIGN"
mkdir -p "$OUTDIR/bundles" || _die "cannot create output dir: $OUTDIR/bundles"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

# ── parse ## Screens into per-screen files + an index ─────────────────────────
awk -v out="$_tmp" '
  /^## Screens/ { insc = 1; next }
  insc && /^## / { insc = 0; next }
  insc && /^### / {
    line = $0
    if (!match(line, /SCR-([A-Z]+-)?[0-9]+/)) { print line >> (out "/unidded.txt"); cur = ""; next }
    id = substr(line, RSTART, RLENGTH)
    name = ""
    if (match(line, /"[^"]+"/)) name = substr(line, RSTART + 1, RLENGTH - 2)
    print id >> (out "/ids.txt")
    if (name == "") { print id >> (out "/unnamed.txt"); cur = ""; next }
    printf "%s\t%s\n", id, name >> (out "/index.tsv")
    cur = out "/scr_" id ".txt"
    print line > cur
    next
  }
  insc && cur != "" { print >> cur }
' "$APP_FLOW"

[ -f "$_tmp/unidded.txt" ] && \
  _die "SCREEN_UNIDDED: screen heading without SCR-<n> id: $(cat "$_tmp/unidded.txt")"
[ -f "$_tmp/unnamed.txt" ] && \
  _die "SCREEN_UNNAMED: screen without a quoted \"<name>\": $(cat "$_tmp/unnamed.txt")"
[ -s "$_tmp/ids.txt" ] || \
  _die "NO_SCREENS: APP_FLOW has no '## Screens' section with '### SCR-<n> — \"<name>\"' entries (fail closed; see journey/docs/journey-gen-doc-format.md §3b)"
_dups=$(sort "$_tmp/ids.txt" | uniq -d)
[ -z "$_dups" ] || _die "DUPLICATE_SCREEN_ID: $_dups"

# ── journeys text for touch derivation ────────────────────────────────────────
awk '
  /^## User Journeys/ { uj = 1; next }
  uj && /^## /        { uj = 0 }
  uj                  { print }
' "$APP_FLOW" > "$_tmp/journeys.txt"

# ── one bundle per screen ─────────────────────────────────────────────────────
while IFS="$(printf '\t')" read -r _id _name; do
  [ -n "$_id" ] || continue
  _sf="$_tmp/scr_${_id}.txt"
  _route=$(awk '/^route:/ { sub(/^route:[ \t]*/, ""); sub(/[ \t]+$/, ""); print; exit }' "$_sf")
  [ -n "$_route" ] || _die "SCREEN_NO_ROUTE: $_id (\"$_name\") has no route: (fail closed)"

  _brel="bundles/$(printf '%s' "$_id" | tr 'A-Z' 'a-z').md"
  {
    printf '# Surface bundle: %s — "%s"\n\n' "$_id" "$_name"
    printf '## Screen (APP_FLOW)\n\n'
    cat "$_sf"
    printf '\n## Touching journeys (APP_FLOW steps that visit %s)\n\n' "$_route"
    awk -v route="$_route" '
      /^### / { blk = $0 "\n"; keep = 0; next }
      { blk = blk $0 "\n"; if (index($0, route) > 0) keep = 1 }
      /^[[:space:]]*$/ && keep { printf "%s", blk; blk = ""; keep = 0 }
      END { if (keep) printf "%s", blk }
    ' "$_tmp/journeys.txt"
    printf '\n## Design context (enrichment, not oracle)\n\n'
    cat "$DESIGN"
    printf '\n## Output format (frozen — emit EXACTLY this shape)\n\n'
    printf '## SURFACE: %s\n' "$_name"
    printf 'route: %s\n' "$_route"
    printf 'allowed_selectors:\n  - role=<role>[name="<name>"]\n  - testid=<id>\nobservable_states: [<from the screen states>]\npublic_api: [<public endpoints the touching journeys imply>]\n'
  } > "$OUTDIR/$_brel"
done < "$_tmp/index.tsv"

# ── screens manifest ──────────────────────────────────────────────────────────
{
  printf '{"screens":['
  _first=1
  while IFS="$(printf '\t')" read -r _id _name; do
    [ -n "$_id" ] || continue
    [ "$_first" -eq 1 ] || printf ','
    _first=0
    printf '{"id":"%s","name":"%s","bundle":"bundles/%s.md"}' \
      "$_id" "$_name" "$(printf '%s' "$_id" | tr 'A-Z' 'a-z')"
  done < "$_tmp/index.tsv"
  printf ']}\n'
} > "$OUTDIR/screens-manifest.json"

exit 0
