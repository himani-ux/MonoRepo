#!/bin/sh
# journey-gen-promote.sh PRD APP_FLOW GEN_MAP MANIFEST GAPS FIDELITY TARGET_MAP [--approve]
#
# Human-bounded promotion gate for doc-derived journeys. Promotes the DERIVED
# journeys from a generated candidate map INTO a canonical JOURNEY_MAP.md ONLY
# when EVERY gate holds AND a human passes --approve. Promotion is NEVER automatic
# from generation. Fail closed on any gate; no write unless all gates pass and the
# human approves.
#
# Gates (all must pass):
#   1. lint-journey-map.sh on GEN_MAP  — schema; rejects runtime-truth field keys,
#      validates enums (origin/priority/oracle_surface/author_status).
#   2. check-journey-coverage.sh PRD APP_FLOW GEN_MAP MANIFEST GAPS — completeness;
#      rejects a malformed/missing manifest, malformed gaps, a DOC_FORMAT record
#      used as a credit, and any coverage failure.
#   3. no BLOCKING refuter finding — FIDELITY must contain zero `block:` lines.
#   4. defense-in-depth — GEN_MAP carries no runtime-truth field key; every DERIVED
#      journey is author_status=UNWRITTEN (no tested/written claim); no TEST_SURFACE
#      reference; no DERIVED JOURNEY-ID already present in TARGET_MAP (idempotence —
#      re-promoting the same candidate is refused, never silently duplicated).
#   5. human --approve marker present.
#
# On success: APPENDS GEN_MAP's DERIVED journey blocks to TARGET_MAP (creating it
# if absent), preserving any existing non-DERIVED (e.g. PERSONA) blocks
# byte-for-byte. Runtime truth is never written here — it lives only in the
# CI-owned ledger, which this gate does not touch.
#
# Exit codes: 0 promoted; 1 refused (gate failure OR missing --approve; no write).
#
# Deps: POSIX sh, awk, grep, jq (via the sub-gates). shellcheck shell=sh

set -u

_here=$(cd "$(dirname "$0")" && pwd)
_emit()  { printf '%s\n' "$*" >&2; }
_die()   { _emit "$*"; exit 1; }

# --origin (A3): restricts WHICH candidates may promote — never broadens
# trust. Default DERIVED is byte-compatible with pre-Increment-3 behavior.
# A PERSONA promotion rejects DERIVED candidates and vice versa; mixed-origin
# candidate files fail (ORIGIN_MISMATCH). PERSONA promotion is INTENT-ONLY:
# it writes no tests, no runtime status, no ledger data.
_ORIGIN="DERIVED"
if [ "${1:-}" = "--origin" ]; then
  _ORIGIN="${2:-}"
  case "$_ORIGIN" in
    DERIVED|PERSONA) : ;;
    *) _die "unknown --origin '$_ORIGIN' (DERIVED|PERSONA)" ;;
  esac
  shift 2
fi

[ $# -eq 7 ] || [ $# -eq 8 ] || \
  _die "usage: journey-gen-promote.sh [--origin DERIVED|PERSONA] PRD APP_FLOW GEN_MAP MANIFEST GAPS FIDELITY TARGET_MAP [--approve]"

PRD="$1"; APP_FLOW="$2"; GEN_MAP="$3"; MANIFEST="$4"; GAPS="$5"; FIDELITY="$6"; TARGET_MAP="$7"
APPROVE=0
if [ $# -eq 8 ]; then
  shift 7
  [ "$1" = "--approve" ] || _die "unexpected argument: $1"
  APPROVE=1
fi

_rejects=0
_reject() { printf 'REJECT: %s\n' "$*" >&2; _rejects=$((_rejects + 1)); }

# ── input readability (TARGET_MAP may not exist yet) ──────────────────────────
for _f in "$PRD" "$APP_FLOW" "$GEN_MAP" "$MANIFEST" "$GAPS" "$FIDELITY"; do
  [ -r "$_f" ] || _reject "input not readable: $_f"
done
[ "$_rejects" -eq 0 ] || { _emit "promotion REFUSED ($_rejects). No write to $TARGET_MAP."; exit 1; }

# ── Gate 1: schema (lint) ─────────────────────────────────────────────────────
sh "$_here/lint-journey-map.sh" "$GEN_MAP" >/dev/null 2>&1 || \
  _reject "lint-journey-map.sh failed on the candidate (schema / runtime-field / enum)"

# ── Gate 2: completeness (coverage) ───────────────────────────────────────────
sh "$_here/check-journey-coverage.sh" "$PRD" "$APP_FLOW" "$GEN_MAP" "$MANIFEST" "$GAPS" >/dev/null 2>&1 || \
  _reject "check-journey-coverage.sh failed (coverage / manifest / gap / DOC_FORMAT)"

# ── Gate 2b: provenance (verbatim quotes + AC accounting) ─────────────────────
# Deterministic oracle-dilution catch: every manifest quote must ground
# verbatim in PRD/APP_FLOW and every covered FEAT's AC-<n> must appear in the
# journey's oracle entry. The refuter is a second opinion, not the only line.
sh "$_here/check-journey-provenance.sh" "$PRD" "$APP_FLOW" "$GEN_MAP" "$MANIFEST" >/dev/null 2>&1 || \
  _reject "check-journey-provenance.sh failed (ungrounded quote / dropped AC / missing provenance)"

# ── Gate 3: refuter has no blocking finding ───────────────────────────────────
# Case-insensitive and tolerant of a leading markdown list/bold marker so a
# `block:` finding still vetoes even when the refuter formats it as `- block:`,
# `**block:**`, or `BLOCK:`. (No new fidelity schema — same `block:` convention.)
if grep -qiE '^[[:space:]]*[-*]?[[:space:]]*\**block:' "$FIDELITY" 2>/dev/null; then
  _reject "refuter fidelity review has BLOCKING finding(s): $FIDELITY"
fi

# ── Gate 3b: fidelity review is hash-bound to THIS candidate (review I6) ──────
# The runner stamps `reviewed_sha256: <sha256 of the candidate>` as the first
# line of the review. A review of a previous candidate, an empty file, or a
# backend apology carries no matching stamp — all refused. "Checked and clean"
# must be distinguishable from "didn't check".
_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else return 1; fi
}
_gen_sha=$(_sha256 "$GEN_MAP") || _die "no sha256 tool available (fail closed)"
_fid_sha=$(grep -m1 '^reviewed_sha256:' "$FIDELITY" 2>/dev/null | awk '{print $2}')
if [ -z "$_fid_sha" ]; then
  _reject "fidelity review carries no reviewed_sha256: line — cannot bind it to this candidate (stale-review guard)"
elif [ "$_fid_sha" != "$_gen_sha" ]; then
  _reject "fidelity reviewed_sha256 does not match this candidate (stale or mismatched review): $_fid_sha != $_gen_sha"
fi

# ── Gate 4a: no runtime-truth field key in the candidate ──────────────────────
if grep -qE '^[[:space:]]*(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):' "$GEN_MAP" 2>/dev/null; then
  _reject "candidate carries a runtime-truth field key (runtime truth lives only in the CI-owned ledger)"
fi

# ── Gate 4b: no TEST_SURFACE reference / executable-test implication ───────────
if grep -q 'TEST_SURFACE' "$GEN_MAP" 2>/dev/null; then
  _reject "candidate references TEST_SURFACE.md (out of scope — journey intent only)"
fi

# ── Gate 4c: DERIVED journeys must be UNWRITTEN; no duplicate JOURNEY-ID ───────
JOURNEY_MAP="$GEN_MAP"; export JOURNEY_MAP
# shellcheck disable=SC1090
. "$_here/../lib/journey-lib.sh"
_existing_ids=""
if [ -f "$TARGET_MAP" ]; then
  JOURNEY_MAP="$TARGET_MAP"; _existing_ids=$(journey_ids); JOURNEY_MAP="$GEN_MAP"
fi

# ── Gate 3c: fidelity review covers EVERY candidate journey (review I6) ───────
# A refuter that stayed silent on a journey did not check it. Every journey id
# must carry at least one correct:/warn:/block: finding line.
for _jid in $(journey_ids | sort -u); do
  grep -qiE '^[[:space:]]*[-*]?[[:space:]]*\**(correct|warn|block):.*'"$_jid"'([^0-9]|$)' "$FIDELITY" 2>/dev/null || \
    _reject "FIDELITY_INCOMPLETE: no correct/warn/block finding for $_jid in $FIDELITY — silence is not a review"
done

_target_count=0
_mismatch_count=0
for _jid in $(journey_ids); do
  _org=$(journey_field "$_jid" origin 2>/dev/null) || _org=""
  if [ "$_org" != "$_ORIGIN" ]; then
    # A3/clarification 6: the flag restricts, never broadens — a candidate
    # carrying ANY other origin (incl. mixed-origin files) is refused.
    _reject "ORIGIN_MISMATCH: $_jid has origin '${_org:-<blank>}' but this promotion is --origin $_ORIGIN (the flag restricts, never broadens; mixed-origin candidates are refused)"
    _mismatch_count=$((_mismatch_count + 1))
    continue
  fi
  _target_count=$((_target_count + 1))
  _as=$(journey_field "$_jid" author_status 2>/dev/null) || _as=""
  [ "$_as" = "UNWRITTEN" ] || \
    _reject "$_ORIGIN journey $_jid has author_status=${_as:-<blank>} (must be UNWRITTEN — generation is not a tested claim)"
  for _eid in $_existing_ids; do
    [ "$_jid" = "$_eid" ] && \
      _reject "duplicate JOURNEY-ID $_jid already present in $TARGET_MAP (idempotence guard — refusing to append a colliding id)"
  done
done

# ── Gate 4d: anti-vacuous (review C4) — an empty candidate is a refusal ───────
# (suppressed only when ORIGIN_MISMATCH already explains the zero count)
[ "$_target_count" -gt 0 ] || [ "$_mismatch_count" -gt 0 ] || \
  _reject "EMPTY_CANDIDATE: candidate contains zero $_ORIGIN journeys — nothing to promote; a vacuous generation run is a failure, not a success"

# ── verdict ───────────────────────────────────────────────────────────────────
if [ "$_rejects" -gt 0 ]; then
  _emit "promotion REFUSED: $_rejects gate failure(s) above. No write to $TARGET_MAP."
  exit 1
fi

if [ "$APPROVE" -ne 1 ]; then
  _emit "All gates pass, but promotion is NEVER automatic. Human review required:"
  _emit "  [x] lint-journey-map.sh (schema, no runtime truth)"
  _emit "  [x] check-journey-coverage.sh (completeness)"
  _emit "  [x] refuter: no BLOCKING findings"
  _emit "  [ ] human --approve   <-- MISSING"
  _emit "Re-run with --approve to append the DERIVED journeys. No write to $TARGET_MAP."
  exit 1
fi

# ── promote: append DERIVED blocks, preserving existing content byte-for-byte ──
_out=$(mktemp) || _die "mktemp failed (fail closed)"
# Clean up the temp on any early exit/signal (incl. the mv-failure _die below).
trap 'rm -f "$_out"' EXIT INT TERM
if [ -f "$TARGET_MAP" ]; then
  cat "$TARGET_MAP" > "$_out"
else
  printf '# JOURNEY_MAP — canonical intent SSOT\n' > "$_out"
fi
for _jid in $(journey_ids); do
  _org=$(journey_field "$_jid" origin 2>/dev/null) || _org=""
  [ "$_org" = "$_ORIGIN" ] || continue
  printf '\n' >> "$_out"
  journey_block "$_jid" >> "$_out"
done
mv "$_out" "$TARGET_MAP" || _die "failed to write $TARGET_MAP"
# Success: the temp has been renamed onto the target. Clear the trap so the
# EXIT handler never runs against the (now-written) target path.
trap - EXIT INT TERM

_emit "PROMOTED: appended DERIVED journeys to $TARGET_MAP (non-DERIVED blocks preserved; runtime truth untouched)."
exit 0
