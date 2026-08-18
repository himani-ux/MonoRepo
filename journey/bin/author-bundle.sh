#!/bin/sh
# shellcheck shell=sh
# author-bundle.sh JOURNEY_MAP TEST_SURFACE APP_FLOW PRD JOURNEY_ID OUT_DIR
#
# Builds ONE blind author bundle for an author_status: UNWRITTEN journey
# (Increment 2). The bundle is the test author's ENTIRE world — blindness is
# by construction, not by trust. It contains ONLY:
#   * the target journey block (intent: steps, oracle, negative_states, ...);
#   * the TEST_SURFACE screens the journey touches (route token in steps);
#   * the journey's AFJ entries (its flows: anchors) from APP_FLOW;
#   * the covered FEAT blocks' acceptance criteria from the PRD;
#   * the frozen Playwright spec skeleton.
#
# FAIL CLOSED (no bundle written):
#   UNKNOWN_JOURNEY       — id not in the map
#   ALREADY_WRITTEN       — author_status is not UNWRITTEN
#   REQUIRED_SURFACE_GAP  — a touched screen has no SURFACE entry (this script
#                           NEVER creates the gap and NEVER invents selectors)
#   MISSING_ANCHOR        — a flows:/covers: anchor absent from APP_FLOW/PRD
# Deps: POSIX sh, awk, grep, sed.

set -u
_die() { printf '%s\n' "$*" >&2; exit 1; }
_here=$(cd "$(dirname "$0")" && pwd)

[ $# -eq 6 ] || _die "usage: author-bundle.sh JOURNEY_MAP TEST_SURFACE APP_FLOW PRD JOURNEY_ID OUT_DIR"
MAP="$1"; TS="$2"; APP_FLOW="$3"; PRD="$4"; JID="$5"; OUTDIR="$6"
for _f in "$MAP" "$TS" "$APP_FLOW" "$PRD"; do
  [ -r "$_f" ] || _die "author-bundle: file not readable: $_f (fail closed)"
done

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

# ── target journey ────────────────────────────────────────────────────────────
JOURNEY_MAP="$MAP"; export JOURNEY_MAP
# shellcheck disable=SC1090
. "$_here/../lib/journey-lib.sh"

journey_ids | grep -qxF "$JID" || \
  _die "UNKNOWN_JOURNEY: $JID not present in $MAP (fail closed)"
_astatus=$(journey_field "$JID" author_status 2>/dev/null) || _astatus=""
[ "$_astatus" = "UNWRITTEN" ] || \
  _die "ALREADY_WRITTEN: $JID author_status is '${_astatus:-<blank>}' — only UNWRITTEN journeys are authored (fail closed)"

journey_block "$JID" > "$_tmp/journey.txt"
_flows=$(journey_field "$JID" flows 2>/dev/null) || _flows=""
_covers=$(journey_field "$JID" covers 2>/dev/null) || _covers=""
_test_path=$(journey_field "$JID" test 2>/dev/null) || _test_path=""

# ── touched screens: APP_FLOW screens whose route appears in the steps ───────
awk '
  /^## Screens/ { insc = 1; next }
  insc && /^## / { insc = 0; next }
  insc && /^### / {
    name = ""; if (match($0, /"[^"]+"/)) name = substr($0, RSTART + 1, RLENGTH - 2)
    cur = name; next
  }
  insc && cur != "" && /^route:/ {
    r = $0; sub(/^route:[ \t]*/, "", r); sub(/[ \t]+$/, "", r)
    printf "%s\t%s\n", cur, r; cur = ""
  }
' "$APP_FLOW" > "$_tmp/screens.tsv"

_steps=$(awk '/^steps:/ { s = 1; next } s && /^[a-z_]+:/ { s = 0 } s { print }' "$_tmp/journey.txt")
: > "$_tmp/touched.txt"
while IFS="$(printf '\t')" read -r _name _route; do
  [ -n "$_name" ] || continue
  printf '%s\n' "$_steps" | grep -qF "$_route" && printf '%s\n' "$_name" >> "$_tmp/touched.txt"
done < "$_tmp/screens.tsv"
[ -s "$_tmp/touched.txt" ] || \
  _die "MISSING_ANCHOR: no APP_FLOW screen route appears in $JID's steps — cannot determine the touched surface (fail closed)"

# ── touched SURFACE blocks (verbatim; a missing one is a hard failure) ────────
: > "$_tmp/surface.txt"
while IFS= read -r _name; do
  [ -n "$_name" ] || continue
  awk -v n="$_name" '
    $0 == "## SURFACE: " n { insb = 1; print; next }
    insb && /^## /         { insb = 0 }
    insb                   { print }
  ' "$TS" > "$_tmp/one-surface.txt"
  if [ ! -s "$_tmp/one-surface.txt" ]; then
    _die "REQUIRED_SURFACE_GAP: touched screen '$_name' has no '## SURFACE:' entry in $TS — author the surface (or fix the docs); this script never invents selectors (fail closed)"
  fi
  cat "$_tmp/one-surface.txt" >> "$_tmp/surface.txt"
  printf '\n' >> "$_tmp/surface.txt"
done < "$_tmp/touched.txt"

# ── the journey's AFJ entries + covered FEAT blocks ───────────────────────────
# ANCHOR-TOKEN GRAMMAR (V-T4b — the ERE-injection CLASS, superseding the V1
# F1 literal-"[]"-only guard):
#   * "[]" alone is the map's required-present, legally-blank list-field
#     sentinel (journey-inbox-triage.sh forces flows: [] on every promoted
#     SIMULATOR journey — journey-inbox-format.md §6). It means "no
#     anchors" and is skipped, never an error.
#   * EVERY other token must full-match the canonical id grammar for its
#     field BEFORE it reaches any matcher — the flows matcher below splices
#     its token into a dynamic awk ERE, so an unvalidated token is regex
#     INJECTION, not just a bad lookup: "[AFJ-001]" (a plausible YAML-list
#     typo during the §6.1 re-anchoring) parses as a bracket class and
#     matched BOTH ### AFJ- headings at exit 0; a bare "[" matched every
#     heading in the file. Canonical grammars are taken from
#     journey/bin/check-doc-format.sh (never invented here): FEAT is
#     prefix-capable FEAT-([A-Z]+-)?[0-9]+ (its PRD block-split regex);
#     AFJ is AFJ-[0-9]+ (its User-Journeys heading regex).
#   * An ungrammatical token is ANCHOR_TOKEN_INVALID — distinct from
#     MISSING_ANCHOR, which stays reserved for a GRAMMATICAL token absent
#     from the doc. A screen-name covers (the not-yet-re-anchored promoted
#     SIMULATOR journey) is therefore ANCHOR_TOKEN_INVALID: the human's fix
#     is re-anchoring to FEAT ids at triage (§6.1), not hunting a missing
#     PRD block. Both list fields are guarded identically — the class must
#     not survive on a sibling field. Since V-T4c P1 the covers matcher
#     ALSO splices its token into a dynamic ERE (the boundary-anchored
#     heading match below), so the grammar whitelist doubles as the L22
#     injection guard for both fields.
: > "$_tmp/afj.txt"
for _aid in $(printf '%s\n' "$_flows" | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'); do
  [ -n "$_aid" ] || continue
  [ "$_aid" = "[]" ] && continue
  printf '%s\n' "$_aid" | grep -qE '^AFJ-[0-9]+$' || \
    _die "ANCHOR_TOKEN_INVALID: $JID flows token '$_aid' does not match the canonical AFJ id grammar AFJ-<n> (per check-doc-format.sh; [] alone means no anchors) — never fed to the matcher (fail closed)"
  awk -v id="$_aid" '
    /^### / { inb = ($0 ~ ("(^|[^0-9A-Za-z])" id "([^0-9]|$)")) }
    /^## / && !/^### / { inb = 0 }
    inb { print }
  ' "$APP_FLOW" > "$_tmp/one-afj.txt"
  [ -s "$_tmp/one-afj.txt" ] || \
    _die "MISSING_ANCHOR: $JID flows anchor $_aid has no entry in $APP_FLOW (fail closed)"
  cat "$_tmp/one-afj.txt" >> "$_tmp/afj.txt"; printf '\n' >> "$_tmp/afj.txt"
done

: > "$_tmp/feat.txt"
for _fid in $(printf '%s\n' "$_covers" | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'); do
  [ -n "$_fid" ] || continue
  [ "$_fid" = "[]" ] && continue
  printf '%s\n' "$_fid" | grep -qE '^FEAT-([A-Z]+-)?[0-9]+$' || \
    _die "ANCHOR_TOKEN_INVALID: $JID covers token '$_fid' does not match the canonical FEAT id grammar FEAT-([A-Z]+-)?<n> (per check-doc-format.sh) — a promoted SIMULATOR journey's screen-name covers must be re-anchored to FEAT ids at triage (journey-inbox-format.md §6.1; fail closed)"
  # V-T4c P1: boundary-anchored heading match, NOT bare index() substring.
  # index($0, id) matched FEAT-001 inside a "## FEAT-0011 ..." heading and
  # pulled the prefix-colliding sibling block into the blind bundle at
  # exit 0. The anchored ERE ("^## " id "( |$)") requires the heading to be
  # exactly this id followed by a space (the canonical "## FEAT-<id> — ..."
  # form) or end-of-line — same boundary idiom as the flows/AFJ matcher
  # above. The block-start/reset conditions use the prefix-capable
  # ^## FEAT- (not ^## FEAT-[0-9]) so a grammatical prefixed id
  # (FEAT-ABC-1, admitted by the whitelist above) can actually find its
  # own "## FEAT-ABC-1 ..." block instead of dying MISSING_ANCHOR. id is
  # grammar-whitelisted before interpolation (L22) — [A-Z0-9-] only, no
  # ERE metacharacters can reach this pattern.
  awk -v id="$_fid" '
    /^## FEAT-/ { inb = ($0 ~ ("^## " id "( |$)")) }
    /^## / && !/^## FEAT-/ { inb = 0 }
    inb { print }
  ' "$PRD" > "$_tmp/one-feat.txt"
  [ -s "$_tmp/one-feat.txt" ] || \
    _die "MISSING_ANCHOR: $JID covers anchor $_fid has no block in $PRD (fail closed)"
  cat "$_tmp/one-feat.txt" >> "$_tmp/feat.txt"; printf '\n' >> "$_tmp/feat.txt"
done

_SKELETON="$_here/../tests/fixtures/author/spec-skeleton.ts"
[ -r "$_SKELETON" ] || _die "author-bundle: spec skeleton not readable: $_SKELETON (fail closed)"

# ── emit (only after every check passed) ──────────────────────────────────────
mkdir -p "$OUTDIR" || _die "cannot create output dir: $OUTDIR"
_low=$(printf '%s' "$JID" | tr 'A-Z' 'a-z')
{
  printf '# Author bundle: %s (BLIND — this file is the author'\''s entire world)\n\n' "$JID"
  printf '## Journey intent (JOURNEY_MAP)\n\n'
  cat "$_tmp/journey.txt"
  printf '\n## Allowed surface (TEST_SURFACE — selectors/routes/APIs beyond this are FORBIDDEN)\n\n'
  cat "$_tmp/surface.txt"
  printf '## APP_FLOW anchors\n\n'
  cat "$_tmp/afj.txt"
  printf '## PRD acceptance criteria\n\n'
  cat "$_tmp/feat.txt"
  printf '## Spec file\n\nEmit exactly one file named: %s\n' "${_test_path:-tests/journeys/$_low.spec.ts}"
  printf '\n## Frozen skeleton (your output follows this shape EXACTLY)\n\n'
  cat "$_SKELETON"
} > "$OUTDIR/author-bundle-$_low.md"

exit 0
