#!/bin/sh
# shellcheck shell=sh
# journey-gen-check-candidate.sh CANDIDATE_FILE
#
# Deterministic pre-merge validation of ONE fan-out generator candidate
# (review C3 — the generator→merge hop was a model↔model seam with zero
# bracketing). Frozen candidate format:
#
#   ## JOURNEY-CANDIDATE — "<title>"        (NEVER a final JOURNEY-ID)
#   <template-schema fields, column-0 keys>
#   ```json field_sources
#   { ...one JSON object... }
#   ```
#
# A candidate may instead be a structured §5.1 gap record (source_id/
# source_type/reason/owner/expiry/reviewer) when the bundle lacks a side, or
# a single `CANDIDATE-FAILED: <reason>` line when the generator could not
# proceed — that is a LOUD failure, never silence.
#
# --origin also accepts SIMULATOR (Increment 4, spec DC-3 ruling A): the
# simulator-run.sh runner validates its own JOURNEY-CANDIDATE slices with
# `--origin SIMULATOR` before assembling them into JOURNEY_INBOX.md — same
# frozen block grammar, `origin: SIMULATOR` instead of DERIVED/PERSONA.
# DERIVED/PERSONA behavior is unchanged: SIMULATOR only widens the accepted
# --origin enum, never alters how a DERIVED/PERSONA candidate is checked.
#
# --origin also accepts EXTRACTED (Step 0 EXTRACTED baseline increment,
# task E4): journey-extracted-stage.sh validates each candidate's
# JOURNEY-CANDIDATE slice with `--origin EXTRACTED` before staging it into
# JOURNEY_EXTRACTED.md — same frozen block grammar, `origin: EXTRACTED`
# instead of DERIVED/PERSONA/SIMULATOR. Restrict-never-broaden, same as the
# SIMULATOR addition: DERIVED/PERSONA/SIMULATOR behavior of this script is
# byte-unchanged; EXTRACTED just becomes a fourth legal value of the same
# variable. An EXTRACTED candidate's own `## EXTRACTION-SOURCES` provenance
# block (spec §4.1) is NOT this script's concern — journey-extracted-
# stage.sh parses that separately; this checker validates the
# JOURNEY-CANDIDATE block's own grammar exactly as it always has (still
# requiring a `json field_sources` fence, same as every other origin).
#
# FAIL CLOSED (exit 1, reasons to stderr) on anything else.
# Deps: POSIX sh, awk, grep, sed, jq.

set -u
_SELF="$0"
_die() { printf '%s: %s\n' "$_SELF" "$1" >&2; exit 1; }

# --origin (A4, extended Increment 4 ruling A): the EXPECTED origin is
# runner-declared, never inferred from candidate content. Default DERIVED
# preserves pre-Increment-3 behavior. SIMULATOR (Increment 4) is an
# ADDITION to the enum only — restrict-never-broaden: every check below is
# driven off $EXPECT_ORIGIN exactly as before, so DERIVED/PERSONA behavior
# is byte-identical; SIMULATOR just becomes a third legal value of the same
# variable.
[ $# -ge 1 ] || _die "usage: journey-gen-check-candidate.sh CANDIDATE_FILE [--origin DERIVED|PERSONA|SIMULATOR|EXTRACTED]"
CAND="$1"; shift
EXPECT_ORIGIN="DERIVED"
if [ "${1:-}" = "--origin" ]; then
  EXPECT_ORIGIN="${2:-}"
  case "$EXPECT_ORIGIN" in
    DERIVED|PERSONA|SIMULATOR|EXTRACTED) : ;;
    *) _die "unknown --origin '$EXPECT_ORIGIN' (DERIVED|PERSONA|SIMULATOR|EXTRACTED)" ;;
  esac
  shift 2
fi
[ $# -eq 0 ] || _die "unexpected argument: $1"
[ -r "$CAND" ] || _die "candidate not readable: $CAND (fail closed)"
[ -s "$CAND" ] || _die "candidate is empty: $CAND (fail closed)"
command -v jq >/dev/null 2>&1 || _die "jq not found (fail closed)"

problems=0
_p() { printf '%s\n' "$1" >&2; problems=$((problems + 1)); }

# ── explicit generator failure is a loud, attributable failure ────────────────
if grep -qE '^CANDIDATE-FAILED:' "$CAND"; then
  _die "generator declared failure: $(grep -m1 '^CANDIDATE-FAILED:' "$CAND")"
fi

# ── a final JOURNEY-ID is the merge's to assign, never the generator's ────────
if grep -qE '^## JOURNEY-[0-9]' "$CAND"; then
  _p "FORBIDDEN_JOURNEY_ID: candidate carries a final '## JOURNEY-<n>' heading — ids are assigned by the merge, never the generator"
fi

# ── runtime truth never appears in generated intent ───────────────────────────
if grep -qE '^[[:space:]]*(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):' "$CAND"; then
  _p "RUNTIME_FIELD: candidate carries a runtime-truth field key (runtime truth lives only in the CI-owned ledger)"
fi

_blocks=$(grep -cE '^## JOURNEY-CANDIDATE — ' "$CAND") || _blocks=0
_gaps=$(grep -cE '^source_id:[[:space:]]*(FEAT|AFJ)-[0-9]+' "$CAND") || _gaps=0

if [ "$_blocks" -eq 0 ] && [ "$_gaps" -eq 0 ]; then
  _p "NO_CANDIDATE_BLOCK: no '## JOURNEY-CANDIDATE — \"<title>\"' block and no structured gap record — a candidate must contain one or the other (free prose is not a candidate)"
fi

# ── per-block checks ──────────────────────────────────────────────────────────
if [ "$_blocks" -gt 0 ]; then
  # every block must pair with exactly one field_sources fence
  _fences=$(grep -cE '^```json field_sources$' "$CAND") || _fences=0
  if [ "$_fences" -lt "$_blocks" ]; then
    _p "MISSING_FIELD_SOURCES: $_blocks candidate block(s) but only $_fences 'json field_sources' fence(s) — every journey needs its provenance object"
  fi

  # each fence must parse as one JSON object
  _tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
  trap 'rm -rf "$_tmp"' EXIT INT TERM
  awk -v out="$_tmp" '
    /^```json field_sources$/ { n++; f = out "/fs_" n ".json"; infs = 1; next }
    /^```$/ && infs { infs = 0; next }
    infs { print >> f }
  ' "$CAND"
  for _f in "$_tmp"/fs_*.json; do
    [ -f "$_f" ] || continue
    jq -e 'type == "object"' "$_f" >/dev/null 2>&1 || \
      _p "BAD_FIELD_SOURCES_JSON: a field_sources fence is not a valid JSON object ($_f)"
  done

  # candidate blocks carry EXACTLY the runner-declared origin (A4)
  grep -qE "^origin:[[:space:]]+${EXPECT_ORIGIN}[[:space:]]*\$" "$CAND" || \
    _p "BAD_ORIGIN: every candidate block must carry 'origin: ${EXPECT_ORIGIN}' (runner-declared; never inferred)"
  if grep -E '^origin:' "$CAND" | grep -vqE "${EXPECT_ORIGIN}[[:space:]]*\$"; then
    _p "BAD_ORIGIN: a candidate block carries an origin other than ${EXPECT_ORIGIN}"
  fi
  grep -qE '^author_status:[[:space:]]+UNWRITTEN[[:space:]]*$' "$CAND" || \
    _p "BAD_AUTHOR_STATUS: every candidate block must carry 'author_status: UNWRITTEN' (generation writes no test)"
  if grep -E '^author_status:' "$CAND" | grep -vqE 'UNWRITTEN[[:space:]]*$'; then
    _p "BAD_AUTHOR_STATUS: a candidate block carries an author_status other than UNWRITTEN"
  fi
fi

# ── per-gap checks: all six fields, non-blank ─────────────────────────────────
if [ "$_gaps" -gt 0 ]; then
  for _k in source_id source_type reason owner reviewer; do
    _n=$(grep -cE "^${_k}:[[:space:]]*[^[:space:]]" "$CAND") || _n=0
    [ "$_n" -ge "$_gaps" ] || \
      _p "MALFORMED_GAP: $_gaps gap record(s) but only $_n non-blank '${_k}:' line(s) — every §5.1 field is required"
  done
  # The expiry field: `expires:` is CANONICAL, `expiry:` is the accepted legacy
  # spelling (owner ruling 2026-07-14, item 2). Either satisfies the requirement,
  # so the two are counted TOGETHER — this gate must not reject a canonical
  # `expires:` record that check-journey-coverage.sh accepts, or the generation
  # pipeline would refuse the very gap records its own prompt now emits.
  _ne=$(grep -cE "^(expires|expiry):[[:space:]]*[^[:space:]]" "$CAND") || _ne=0
  [ "$_ne" -ge "$_gaps" ] || \
    _p "MALFORMED_GAP: $_gaps gap record(s) but only $_ne non-blank 'expires:' (or legacy 'expiry:') line(s) — every §5.1 field is required"
fi

if [ "$problems" -gt 0 ]; then
  printf '%s: %d problem(s) — candidate rejected before merge (fail closed)\n' "$_SELF" "$problems" >&2
  exit 1
fi
exit 0
