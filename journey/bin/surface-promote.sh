#!/bin/sh
# shellcheck shell=sh
# surface-promote.sh APP_FLOW CANDIDATE_TEST_SURFACE TARGET_TEST_SURFACE [--approve]
#
# Human-gated promotion of a candidate TEST_SURFACE to canonical (Increment 2).
# Gates: lint-test-surface.sh AND check-surface-coverage.sh must pass, and a
# human must pass --approve. On success the candidate is installed ATOMICALLY
# and byte-identically — this script never repairs, merges, infers, or calls
# a model. Exit 0 promoted; exit 1 refused (no write).
#
# (APP_FLOW is a required input because the coverage gate re-derives the
# required screens from it — coverage is never trusted from generator output.)
#
# PROVENANCE ANCHOR (spec G2): on success this script ALSO writes a SIBLING
# file <TARGET_TEST_SURFACE>.provenance, containing exactly one line:
#   app_flow_sha256: <64-hex sha256 of the APP_FLOW file>
# written ATOMICALLY (guarded mktemp + mv), alongside — but never in place
# of — the existing byte-identical surface write. This is the fix for a
# real field incident: a stale TEST_SURFACE (old routes/test-IDs) coexisted
# silently with the current app because nothing gated staleness, and the
# team improvised an unenforced `.current.md` suffix instead of a real
# anchor. journey/bin/check-surface-staleness.sh re-derives APP_FLOW's
# sha256 later and fails SURFACE_STALE if it no longer matches this anchor
# — an un-anchored surface (no `.provenance` sibling) never passes that
# gate (PROVENANCE_MISSING).
#
# The sha256 tool (sha256sum, falling back to shasum) is located and the
# APP_FLOW hash is computed BEFORE any write happens in this run. If
# neither tool is on PATH, promotion fails LOUD — TOOL_MISSING, exit 1 —
# with NOTHING written: not the surface, not the provenance sibling.
# Promotion must never succeed without stamping a provenance anchor.

set -u
_here=$(cd "$(dirname "$0")" && pwd)
_emit() { printf '%s\n' "$*" >&2; }
_die()  { _emit "$*"; exit 1; }

[ $# -eq 3 ] || [ $# -eq 4 ] || \
  _die "usage: surface-promote.sh APP_FLOW CANDIDATE_TEST_SURFACE TARGET_TEST_SURFACE [--approve]"

APP_FLOW="$1"; CAND="$2"; TARGET="$3"
APPROVE=0
if [ $# -eq 4 ]; then
  [ "$4" = "--approve" ] || _die "unexpected argument: $4"
  APPROVE=1
fi

_rejects=0
_reject() { printf 'REJECT: %s\n' "$*" >&2; _rejects=$((_rejects + 1)); }

for _f in "$APP_FLOW" "$CAND"; do
  [ -r "$_f" ] || _reject "input not readable: $_f"
done
[ "$_rejects" -eq 0 ] || { _emit "surface promotion REFUSED ($_rejects). No write to $TARGET."; exit 1; }

sh "$_here/lint-test-surface.sh" "$CAND" >/dev/null 2>&1 || \
  _reject "lint-test-surface.sh failed on the candidate (format / selector grammar / gap)"

sh "$_here/check-surface-coverage.sh" "$APP_FLOW" "$CAND" >/dev/null 2>&1 || \
  _reject "check-surface-coverage.sh failed (coverage / invented screen / route mismatch)"

if [ "$_rejects" -gt 0 ]; then
  _emit "surface promotion REFUSED: $_rejects gate failure(s) above. No write to $TARGET."
  exit 1
fi

if [ "$APPROVE" -ne 1 ]; then
  _emit "All gates pass, but promotion is NEVER automatic. Human review required:"
  _emit "  [x] lint-test-surface.sh"
  _emit "  [x] check-surface-coverage.sh"
  _emit "  [ ] human --approve   <-- MISSING"
  _emit "Re-run with --approve to install the canonical TEST_SURFACE. No write to $TARGET."
  exit 1
fi

# ── provenance anchor: locate the sha256 tool and hash APP_FLOW BEFORE any
#    write happens below — if no tool is on PATH, fail loud (TOOL_MISSING)
#    with nothing written; promotion must never succeed without stamping ──
_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else return 1; fi
}
_appflow_sha=$(_sha256 "$APP_FLOW") || \
  _die "TOOL_MISSING: no sha256sum or shasum on PATH — refusing to promote without a provenance anchor (fail closed). No write to $TARGET."

_out=$(mktemp "$(dirname "$TARGET")/.surface-XXXXXXXX") || _die "mktemp failed (fail closed)"
trap 'rm -f "$_out"' EXIT INT TERM
cat "$CAND" > "$_out" || _die "failed to stage candidate (fail closed)"
mv "$_out" "$TARGET" || _die "failed to install $TARGET"
trap - EXIT INT TERM

# ── sibling provenance file (atomic: guarded mktemp + mv). mktemp guard
#    checks rc AND non-empty path before installing the trap — see
#    journey/bin/check-uat-evidence.sh's $_fail guard (M-T1-4) as the model.
_prov="$TARGET.provenance"
_ptmp=$(mktemp "$(dirname "$TARGET")/.provenance-XXXXXXXX") || _die "mktemp failed for provenance (fail closed)"
[ -n "$_ptmp" ] || _die "mktemp returned empty path for provenance (fail closed)"
trap 'rm -f "$_ptmp"' EXIT INT TERM
printf 'app_flow_sha256: %s\n' "$_appflow_sha" > "$_ptmp" || _die "failed to stage provenance (fail closed)"
mv "$_ptmp" "$_prov" || _die "failed to install $_prov"
trap - EXIT INT TERM

_emit "PROMOTED: canonical TEST_SURFACE installed at $TARGET (byte-identical to the reviewed candidate); provenance anchor written to $_prov (app_flow_sha256: $_appflow_sha)."
exit 0
