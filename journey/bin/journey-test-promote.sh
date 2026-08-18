#!/bin/sh
# shellcheck shell=sh
# journey-test-promote.sh [--approve] JOURNEY_ID SPEC_CANDIDATE AUTHOR_BUNDLE REFUTER_RESULT JOURNEY_MAP TESTS_DIR
#
# Human-gated promotion of ONE blind-authored spec (Increment 2). On success:
# installs the spec into TESTS_DIR (at the journey's `test:` basename) and
# flips ONLY the target journey `author_status: UNWRITTEN -> WRITTEN` in the
# map — every other byte of the map is preserved. Promotion is NEVER
# automatic.
#
# Gates (ALL must hold):
#   * --approve present (human);
#   * journey exists, is UNWRITTEN, and its test: path basename matches;
#   * lint-journey-tests.sh SPEC AUTHOR_BUNDLE passes (blindness/discipline);
#   * refuter result contains NO 'REFUTER-BLOCK:' anywhere;
#   * refuter result contains a 'REFUTER-NO-BLOCK:' entry naming THIS journey
#     with checked_hash == sha256(SPEC_CANDIDATE) (STALE_REFUTER otherwise —
#     silence is not a review; a review of another spec is not a review);
#   * no existing spec with different content (EXISTING_SPEC_DIFFERS —
#     no silent overwrite).
# Deps: POSIX sh, awk, grep, sed, sha256sum|shasum.

set -u
_here=$(cd "$(dirname "$0")" && pwd)
_emit() { printf '%s\n' "$*" >&2; }
_die()  { _emit "$*"; exit 1; }

APPROVE=0
if [ "${1:-}" = "--approve" ]; then APPROVE=1; shift; fi
[ $# -eq 6 ] || \
  _die "usage: journey-test-promote.sh [--approve] JOURNEY_ID SPEC_CANDIDATE AUTHOR_BUNDLE REFUTER_RESULT JOURNEY_MAP TESTS_DIR"
JID="$1"; SPEC="$2"; BUNDLE="$3"; REF="$4"; MAP="$5"; TESTS_DIR="$6"

_rejects=0
_reject() { printf 'REJECT: %s\n' "$*" >&2; _rejects=$((_rejects + 1)); }

for _f in "$SPEC" "$BUNDLE" "$REF" "$MAP"; do
  [ -r "$_f" ] || _reject "input not readable: $_f"
done
[ -d "$TESTS_DIR" ] || _reject "TESTS_DIR is not a directory: $TESTS_DIR"
[ "$_rejects" -eq 0 ] || { _emit "spec promotion REFUSED ($_rejects). Nothing written."; exit 1; }

# ── journey state ─────────────────────────────────────────────────────────────
JOURNEY_MAP="$MAP"; export JOURNEY_MAP
# shellcheck disable=SC1090
. "$_here/../lib/journey-lib.sh"

if ! journey_ids | grep -qxF "$JID"; then
  _reject "UNKNOWN_JOURNEY: $JID not present in $MAP"
else
  _astatus=$(journey_field "$JID" author_status 2>/dev/null) || _astatus=""
  [ "$_astatus" = "UNWRITTEN" ] || \
    _reject "ALREADY_WRITTEN: $JID author_status is '${_astatus:-<blank>}' — only UNWRITTEN journeys are promotable"
  _test_path=$(journey_field "$JID" test 2>/dev/null) || _test_path=""
  [ -n "$_test_path" ] || _reject "MAP_PATH_MISSING: $JID has no test: path in the map"
fi

# ── blindness/discipline lint ─────────────────────────────────────────────────
sh "$_here/lint-journey-tests.sh" "$SPEC" "$BUNDLE" >/dev/null 2>&1 || \
  _reject "lint-journey-tests.sh failed on the candidate (blindness / selector / oracle discipline)"

# ── refuter binding ───────────────────────────────────────────────────────────
_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else return 1; fi
}
_spec_sha=$(_sha256 "$SPEC") || _die "no sha256 tool available (fail closed)"

if grep -qE '^REFUTER-BLOCK:' "$REF"; then
  _reject "refuter BLOCKED: $(grep -A2 -m1 '^REFUTER-BLOCK:' "$REF" | tr '\n' ' ')"
fi
# the NO-BLOCK entry must name THIS journey and THIS spec's hash
_ref_hash=$(awk -v jid="$JID" '
  /^REFUTER-NO-BLOCK:/ { inb = 1; seen = 0; next }
  inb && /^- journey_id:/ { seen = (index($0, jid) > 0); next }
  inb && /^- checked_hash:/ { if (seen) { sub(/^- checked_hash:[ \t]*/, ""); print; exit } next }
  /^[A-Z]/ { inb = 0 }
' "$REF")
if [ -z "$_ref_hash" ]; then
  _reject "REFUTER_SILENT: no REFUTER-NO-BLOCK entry names $JID — silence is not a review"
elif [ "$_ref_hash" != "$_spec_sha" ]; then
  _reject "STALE_REFUTER: checked_hash $_ref_hash does not match this candidate ($_spec_sha) — a review of another spec is not a review"
fi

# ── no silent overwrite ───────────────────────────────────────────────────────
_dest=""
if [ -n "${_test_path:-}" ]; then
  _dest="$TESTS_DIR/$(basename "$_test_path")"
  if [ -f "$_dest" ] && ! cmp -s "$_dest" "$SPEC"; then
    _reject "EXISTING_SPEC_DIFFERS: $_dest exists with different content — refusing to overwrite (remove it deliberately first)"
  fi
fi

if [ "$_rejects" -gt 0 ]; then
  _emit "spec promotion REFUSED: $_rejects gate failure(s) above. Nothing written."
  exit 1
fi

if [ "$APPROVE" -ne 1 ]; then
  _emit "All gates pass, but promotion is NEVER automatic. Human review required:"
  _emit "  [x] lint-journey-tests.sh (blindness / selector / oracle discipline)"
  _emit "  [x] refuter: NO-BLOCK, hash-bound to this candidate"
  _emit "  [ ] human --approve   <-- MISSING"
  _emit "Re-run with --approve to install the spec and mark $JID WRITTEN. Nothing written."
  exit 1
fi

# ── install spec (atomic) ─────────────────────────────────────────────────────
_stmp=$(mktemp "$TESTS_DIR/.spec-XXXXXXXX") || _die "mktemp failed (fail closed)"
trap 'rm -f "$_stmp"' EXIT INT TERM
cat "$SPEC" > "$_stmp" && mv "$_stmp" "$_dest" || _die "failed to install $_dest"
trap - EXIT INT TERM

# ── flip author_status for THIS journey only (byte-preserving, atomic) ────────
_mtmp=$(mktemp "$(dirname "$MAP")/.map-XXXXXXXX") || _die "mktemp failed (fail closed)"
trap 'rm -f "$_mtmp"' EXIT INT TERM
awk -v jid="$JID" '
  $0 ~ ("^## " jid "([^0-9]|$)") { inb = 1; print; next }
  /^## / && inb { inb = 0 }
  inb && /^author_status:/ { sub(/UNWRITTEN/, "WRITTEN"); print; next }
  { print }
' "$MAP" > "$_mtmp" || _die "failed to rewrite the map (fail closed)"
# self-check before publishing: exactly the one intended change
_changed=$(diff "$MAP" "$_mtmp" | grep -c '^[<>]')
[ "$_changed" -eq 2 ] || { rm -f "$_mtmp"; _die "map flip self-check failed (expected exactly one changed line, got $_changed/2) — map untouched"; }
mv "$_mtmp" "$MAP" || _die "failed to write $MAP"
trap - EXIT INT TERM

_emit "PROMOTED: $_dest installed; $JID author_status UNWRITTEN -> WRITTEN (map otherwise byte-identical)."
_emit "The journey is WRITTEN, not GREEN: only a trusted CI run of this spec stamps runtime truth in the ledger."
exit 0
