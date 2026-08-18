#!/bin/sh
# shellcheck shell=sh
# check-surface-staleness.sh TEST_SURFACE APP_FLOW — TEST_SURFACE provenance
# staleness gate (spec G2).
#
# Field-run motivation: on a real project a stale TEST_SURFACE (old
# routes/test-IDs) coexisted silently with the current app because nothing
# gated staleness — the team improvised an unenforced `.current.md` suffix
# instead of a real fix. check-surface-coverage.sh re-derives screens/
# routes from APP_FLOW and so catches ROUTE drift IF it is re-run, but it
# does not re-derive allowed_selectors / observable_states, and nothing
# forces anyone to re-run anything when APP_FLOW changes. This gate closes
# that gap by re-checking the machine-readable provenance anchor that
# journey/bin/surface-promote.sh stamps at promote time: a SIBLING file
# <TEST_SURFACE>.provenance, exactly one line:
#   app_flow_sha256: <64-hex sha256 of the APP_FLOW file>
#
# An unanchored TEST_SURFACE — no `.provenance` sibling at all, e.g. a
# hand-rolled `.current.md` copy that never went through surface-promote.sh
# — NEVER passes: PROVENANCE_MISSING is unconditional. This is the
# `.current.md` killer the field incident needed.
#
# COARSE BY DESIGN: the entire APP_FLOW file is hashed, not just its
# `## Screens` section. Rationale: coverage re-derives screens from
# APP_FLOW anyway; a changed APP_FLOW always warrants re-running surface
# gates and re-promoting — a reworded journey step, or a renamed UI element
# the surface's allowed_selectors were derived from, never touches
# `## Screens` yet must still invalidate the anchor. ANY APP_FLOW change
# invalidates it; there is no "safe" subset of APP_FLOW that can drift
# without re-validating the surface.
#
# Codes (closed enum):
#   PROVENANCE_MISSING — <TEST_SURFACE>.provenance does not exist
#   PROVENANCE_FORMAT   — first line of the provenance file is not exactly
#                         "app_flow_sha256: " + 64 lowercase hex
#   TOOL_MISSING        — no sha256sum/shasum on PATH (fail closed)
#   SURFACE_STALE       — the recomputed APP_FLOW sha256 does not match the
#                         recorded anchor; re-run surface gates + re-promote
# Usage error / missing input file: exit 2.
#
# Deps: POSIX sh, grep, head, cut, awk, sha256sum|shasum.

set -u

usage() { printf 'Usage: check-surface-staleness.sh TEST_SURFACE APP_FLOW\n' >&2; exit 2; }
[ $# -eq 2 ] || usage

TS="$1"; APP_FLOW="$2"

[ -f "$TS" ] || {
  printf 'check-surface-staleness: file not found: %s\n' "$TS" >&2
  exit 2
}
[ -f "$APP_FLOW" ] || {
  printf 'check-surface-staleness: file not found: %s\n' "$APP_FLOW" >&2
  exit 2
}

PROV="$TS.provenance"
[ -f "$PROV" ] || {
  printf 'PROVENANCE_MISSING: %s has no provenance anchor; re-promote via surface-promote.sh\n' "$TS" >&2
  exit 1
}

_first=$(head -n 1 "$PROV")
printf '%s\n' "$_first" | grep -q '^app_flow_sha256: [0-9a-f]\{64\}$' || {
  printf 'PROVENANCE_FORMAT: %s first line is not exactly "app_flow_sha256: " + 64 lowercase hex: [%s]\n' "$PROV" "$_first" >&2
  exit 1
}
_recorded=${_first#app_flow_sha256: }

# ── sha256 helper (parent-shell tool-missing guard, NOT inside a pipeline —
#    a tool-missing failure inside a pipeline subshell is a known fail-open
#    class in this repo; same idiom as journey/bin/journey-test-promote.sh
#    _sha256 and journey/bin/surface-promote.sh) ──────────────────────────
_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else return 1; fi
}
_current=$(_sha256 "$APP_FLOW") || {
  printf 'TOOL_MISSING: no sha256sum or shasum on PATH — cannot verify the provenance anchor (fail closed)\n' >&2
  exit 1
}

if [ "$_current" != "$_recorded" ]; then
  _rec12=$(printf '%s' "$_recorded" | cut -c1-12)
  _cur12=$(printf '%s' "$_current" | cut -c1-12)
  printf 'SURFACE_STALE: surface anchored to %s but APP_FLOW is %s; re-run surface gates and re-promote\n' "$_rec12" "$_cur12" >&2
  exit 1
fi

printf 'OK: %s provenance matches current APP_FLOW (app_flow_sha256: %s)\n' "$TS" "$_current"
exit 0
