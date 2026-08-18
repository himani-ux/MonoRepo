#!/bin/sh
# journey-reality-intake.sh MAP ENTRY_FILE [--approve]
#
# Human-approved reality->map intake gate (spec DC-5). A confirmed real
# workflow failure (a bug report, an incident, a telemetry drop-off) skips
# the inbox entirely — it is already confirmed real, not a stochastic
# candidate — and becomes a new `## JOURNEY-<n>` block straight in MAP.
# Never automatic — see --approve below. Promotion is all-or-nothing: MAP
# is updated, or it is not touched at all (spec §5.3, journey-validation
# design doc).
#
# ── Argument parsing ────────────────────────────────────────────────────────
# --approve may appear in any argument position (mirrors
# journey/bin/journey-inbox-triage.sh / uat-report-promote.sh). The
# remaining two args are positional (MAP, ENTRY_FILE), original relative
# order preserved.
#
# ── --approve refuses BEFORE any other work (house rule 7) ─────────────────
# Without --approve: refuse immediately. Nothing is read (not even a file
# readability check), nothing is written. This happens before usage
# validation too — a malformed invocation without --approve still refuses
# on APPROVE_REQUIRED, never on a USAGE error, because "did a human approve
# this" is checked first.
#
# ── ENTRY_FILE format ────────────────────────────────────────────────────────
# ENTRY_FILE is NOT the JOURNEY_INBOX candidate format and NOT the
# JOURNEY-CANDIDATE generator format (journey-gen-check-candidate.sh) — it
# is exactly ONE journey block in the FULL JOURNEY_MAP.md grammar: a heading
# `## JOURNEY-<any-digits> — "<title>"` (the digits are a placeholder — this
# gate reassigns the id from the 401 block upward) followed by the same
# field set lint-journey-map.sh validates. A human (or a UAT/incident
# write-up process) authors this file directly; there is no separate
# generator here to compose against.
#
# ── With --approve, in order ────────────────────────────────────────────────
#   1. usage validation (exactly 2 positional args) -> exit 2
#   2. both files exist and are readable                -> exit 2
#   3. exactly one `## JOURNEY-<digits>` block in ENTRY_FILE, found via the
#      SAME journey_ids/journey_block accessors journey-lib.sh uses for
#      MAP (JOURNEY_MAP is pointed at ENTRY_FILE for this read) — zero
#      blocks -> NO_ENTRY_BLOCK, more than one -> MULTIPLE_BLOCKS. Neither
#      code accumulates with anything else: without exactly one block there
#      is nothing to run the field checks below against.
#   4. intake-specific field checks on that one block, FIRST and fail-slow
#      (all of them run; every violation accumulates before refusing):
#        - heading matches the canonical map grammar exactly:
#          `## JOURNEY-<digits> — "<title>"` (spaced em-dash, double-quoted
#          non-empty title)                              -> ENTRY_HEADING_INVALID
#          (V-T5 F1: the lib READS blocks permissively but the rewrite in
#          step 7 substitutes on the spaced form — a glued heading would
#          no-op the rewrite and land under the placeholder id; fail
#          closed here instead)
#        - origin: must be EXACTLY REALITY               -> ORIGIN_NOT_REALITY
#        - author_status: must be EXACTLY UNWRITTEN       -> AUTHOR_STATUS_NOT_UNWRITTEN
#        - evidence: non-empty AND not the literal `[]`   -> EVIDENCE_EMPTY
#      (a REALITY journey exists BECAUSE of a confirmed real failure —
#      evidence carries the bug/incident/report refs; that is the field's
#      whole point here, unlike PERSONA/SIMULATOR journeys where it may be
#      legitimately blank). Any violation here refuses before dedup or
#      promotion is even attempted — MAP is never touched.
#   5. deterministic dedup: normalize the entry's `covers:` and `oracle:`
#      via the SAME shared journey-lib.sh `norm_covers`/`norm_oracle`
#      journey-inbox-triage.sh uses (never forked — see the lib for the
#      sort -u rationale, V-T2 F1 / L15). A match on BOTH keys against an
#      existing MAP journey is DUPLICATE_JOURNEY: the operator is directed
#      to attach the regression to the existing journey instead of minting
#      a new one. All matches accumulate (fail-slow); any match refuses the
#      whole run.
#   6. id assignment: 401 upward, skipping ids already in MAP (persona-run.sh
#      / journey-inbox-triage.sh's next-free idiom, base 401 not 301).
#   7. build a TEMP copy of MAP with the entry block appended verbatim,
#      EXCEPT: the heading's id is rewritten to the assigned `JOURNEY-<id>`,
#      and — mirrors commit 4b08dcb — a `test:` value containing the
#      literal placeholder token `<n>` has ONLY that token substituted with
#      the assigned numeric id (a concrete test value with no `<n>` token
#      copies through byte-identical). Nothing else in the block is
#      rewritten or forced: the intake-specific checks in step 4 already
#      proved origin/author_status/evidence are exactly what this gate
#      requires, so the entry's own field values (persona, goal, priority,
#      covers, steps, oracle, ...) land unchanged.
#   8. `lint-journey-map.sh` runs on the TEMP map as an executable (never
#      re-implemented) — non-zero exit is LINT_FAILED, temp cleaned, MAP
#      untouched. This is also where a runtime-truth field smuggled into
#      the entry gets caught (lint-journey-map.sh Check 3 runs over every
#      block in the temp map, including the newly appended one) — see the
#      "runtime-truth fields" note below for why this gate does not ALSO
#      duplicate that check itself.
#   9. self-check clean -> assert the ASSIGNED id's block is non-empty in
#      the temp map (V-T5 F1 layer 2, defense in depth: the grammar check
#      in step 4 guarantees the rewrite matched, but an SSOT write never
#      trusts a single layer — an unreadable assigned block dies with the
#      temp cleaned, MAP untouched) -> mv temp map over MAP (temp+trap+mv;
#      house rule 8: on ANY failure path before this rename, MAP is
#      byte-unchanged).
#  10. success: `INTAKE: JOURNEY-<id> — "<title>"` on stderr (this gate's
#      own diagnostics/success line, same channel as journey-inbox-
#      triage.sh's `PROMOTED:` line; non-empty by construction — the
#      heading is read back from the asserted block). Exit 0.
#
# Any failure at any point before step 9's rename -> the temp+trap cleans
# the temp; MAP is never touched (house rule 8).
#
# ── runtime-truth fields: composition, not a duplicated direct check ───────
# DC-1/DC-2 precedent (lint-journey-inbox.sh's RUNTIME_FIELD, lint-journey-
# map.sh's Check 3, check-journey-authority.sh's _RT_PAT) each carry their
# OWN inline copy of the same five-field regex. Rather than adding a FOURTH
# inline copy here, this gate relies on COMPOSITION: the entry block is
# appended to the temp map in step 7 and then lint-journey-map.sh runs over
# the WHOLE temp map (including that block) in step 8. Check 3 there
# already rejects any of {ci_status, last_run, ci_run_id, ci_artifact,
# failure_summary} appearing as a key in ANY block, including the one this
# gate just added — so a smuggled runtime-truth field is rejected via
# LINT_FAILED, with lint-journey-map.sh's own diagnostic passing through.
# This is sound because step 8 unconditionally runs whenever steps 4-6 pass
# (there is no path to a write that skips the self-check) — see the
# journey-reality-intake_test.sh RED case that proves it independently of
# the origin/author_status/evidence checks (an entry that PASSES all three
# of those but smuggles a runtime-truth key still gets refused, via
# LINT_FAILED, not a bespoke code).
#
# ── Codes (own; closed enum, this gate) ─────────────────────────────────────
#   APPROVE_REQUIRED                 — --approve absent (refuses before any
#                                       other work)
#   NO_ENTRY_BLOCK                   — ENTRY_FILE has zero `## JOURNEY-<n>`
#                                       blocks (anti-vacuous)
#   MULTIPLE_BLOCKS                  — ENTRY_FILE has more than one
#                                       `## JOURNEY-<n>` block
#   ENTRY_HEADING_INVALID            — entry heading is not the canonical
#                                       `## JOURNEY-<digits> — "<title>"`
#                                       form (V-T5 F1: a glued/malformed
#                                       heading must never reach the
#                                       rewrite)
#   ORIGIN_NOT_REALITY               — entry's origin: is not exactly REALITY
#   AUTHOR_STATUS_NOT_UNWRITTEN      — entry's author_status: is not exactly
#                                       UNWRITTEN
#   EVIDENCE_EMPTY                   — entry's evidence: is blank or the
#                                       literal `[]`
#   DUPLICATE_JOURNEY: entry matches <journey-id> — normalized covers+oracle
#                                       collide with an existing MAP journey
#   LINT_FAILED                      — the temp map (existing MAP + the new
#                                       entry) failed lint-journey-map.sh's
#                                       self-check — message states this;
#                                       the composed lint's own diagnostics
#                                       (e.g. a bad enum value, or a
#                                       runtime-truth field, see above)
#                                       print first
#
# Usage error / missing MAP or ENTRY_FILE: exit 2 (house convention). Gate
# violation (APPROVE_REQUIRED, NO_ENTRY_BLOCK, MULTIPLE_BLOCKS,
# ENTRY_HEADING_INVALID, ORIGIN_NOT_REALITY, AUTHOR_STATUS_NOT_UNWRITTEN,
# EVIDENCE_EMPTY, DUPLICATE_JOURNEY, LINT_FAILED): exit 1. Success: exit 0.
#
# This gate never touches runtime fields, the CI-owned ledger, or
# JOURNEY_INBOX.md — it reads and writes MAP only.
#
# Deps: POSIX sh, awk, grep, sed, mktemp. shellcheck shell=sh

set -u

_here="$(cd "$(dirname "$0")" && pwd)"
LIB="$_here/../lib/journey-lib.sh"

_emit() { printf '%s\n' "$*" >&2; }
_die()  { _emit "$*"; exit 1; }

# ── parse: --approve may appear anywhere; MAP/ENTRY_FILE stay positional in
# their original relative order (mirrors journey-inbox-triage.sh; no
# arrays, bash 3.2 compatible). ─────────────────────────────────────────────
APPROVE=0
_first=1
for _a in "$@"; do
  if [ "$_a" = "--approve" ]; then
    APPROVE=1
  else
    if [ "$_first" -eq 1 ]; then set -- "$_a"; _first=0
    else set -- "$@" "$_a"; fi
  fi
done

# --approve gates EVERYTHING: absent -> refuse before any other work, before
# even usage validation. Nothing read, nothing written (house rule 7).
if [ "$APPROVE" -ne 1 ]; then
  _emit "APPROVE_REQUIRED: reality intake requires human --approve (never automatic). Nothing read, nothing written."
  exit 1
fi

[ $# -eq 2 ] || {
  _emit "Usage: journey-reality-intake.sh MAP ENTRY_FILE [--approve]"
  exit 2
}
MAP="$1"; ENTRY_FILE="$2"

[ -f "$MAP" ] || {
  _emit "journey-reality-intake: file not found: $MAP"
  exit 2
}
[ -f "$ENTRY_FILE" ] || {
  _emit "journey-reality-intake: file not found: $ENTRY_FILE"
  exit 2
}

# shellcheck disable=SC1090
. "$LIB"

# ── step 3: exactly one `## JOURNEY-<digits>` block in ENTRY_FILE ──────────
JOURNEY_MAP="$ENTRY_FILE"
export JOURNEY_MAP
_entry_ids="$(journey_ids | sort -u)"
_entry_count=0
for _eid in $_entry_ids; do _entry_count=$((_entry_count + 1)); done

if [ "$_entry_count" -eq 0 ]; then
  _emit "NO_ENTRY_BLOCK: no '## JOURNEY-<n>' block found in $ENTRY_FILE (exactly one required)"
  exit 1
fi
if [ "$_entry_count" -gt 1 ]; then
  _emit "MULTIPLE_BLOCKS: $ENTRY_FILE contains $_entry_count '## JOURNEY-<n>' blocks (exactly one required): $(printf '%s' "$_entry_ids" | tr '\n' ' ')"
  exit 1
fi
_entry_id="$_entry_ids"

# ── step 4: intake-specific field checks, FIRST and fail-slow ──────────────
_errors=0

# V-T5 F1: the heading must match the canonical map grammar EXACTLY —
# '## JOURNEY-<digits> — "<title>"' (spaced em-dash U+2014, double-quoted
# non-empty title; the form every existing map heading and the template's
# JOURNEY-000 example use). journey-lib READS blocks with the permissive
# '^## <id>([^0-9]|$)' pattern but the promotion rewrite below substitutes
# on '^## <id> ' (trailing space) — a glued heading ('## JOURNEY-999—"t"',
# em-dash or hyphen glued to the digits) passed every read/field/lint
# check, silently no-opped the rewrite, and landed in the map under the
# PLACEHOLDER id with an empty 'INTAKE: ' success line at exit 0. Fail
# closed here, accumulated fail-slow with the other intake checks. The
# pattern is STATIC (no operator data interpolated — L22 does not arise).
_entry_heading="$(journey_block "$_entry_id" | head -n1)"
if ! printf '%s\n' "$_entry_heading" | grep -qE '^## JOURNEY-[0-9]+ — ".+"$'; then
  _emit "ENTRY_HEADING_INVALID: entry heading must match '## JOURNEY-<digits> — \"<title>\"' (spaced em-dash, double-quoted title; found: $_entry_heading)"
  _errors=$((_errors + 1))
fi

_origin="$(journey_field "$_entry_id" origin 2>/dev/null)" || _origin=""
if [ "$_origin" != "REALITY" ]; then
  _emit "ORIGIN_NOT_REALITY: origin must be exactly REALITY (found: '$_origin')"
  _errors=$((_errors + 1))
fi

_astatus="$(journey_field "$_entry_id" author_status 2>/dev/null)" || _astatus=""
if [ "$_astatus" != "UNWRITTEN" ]; then
  _emit "AUTHOR_STATUS_NOT_UNWRITTEN: author_status must be exactly UNWRITTEN (found: '$_astatus')"
  _errors=$((_errors + 1))
fi

_evidence="$(journey_field "$_entry_id" evidence 2>/dev/null)" || _evidence=""
if [ -z "$_evidence" ] || [ "$_evidence" = "[]" ]; then
  _emit "EVIDENCE_EMPTY: evidence must be non-empty and not the literal [] — a REALITY journey exists because of a confirmed real failure; evidence carries the bug/incident/report refs"
  _errors=$((_errors + 1))
fi

if [ "$_errors" -gt 0 ]; then
  _emit "INTAKE REFUSED: $_errors problem(s) found above. No write to $MAP."
  exit 1
fi

# ── step 5: dedup against the existing map (norm_covers/norm_oracle,
# shared with journey-inbox-triage.sh via journey-lib.sh) ──────────────────
_e_covers="$(norm_covers "$(journey_field "$_entry_id" covers 2>/dev/null)")"
_e_oracle="$(norm_oracle "$(journey_field "$_entry_id" oracle 2>/dev/null)")"
_entry_block="$(journey_block "$_entry_id")"

JOURNEY_MAP="$MAP"
export JOURNEY_MAP
_dupe_errors=0
for _mid in $(journey_ids | sort -u); do
  _m_covers="$(norm_covers "$(journey_field "$_mid" covers 2>/dev/null)")"
  _m_oracle="$(norm_oracle "$(journey_field "$_mid" oracle 2>/dev/null)")"
  if [ "$_e_covers" = "$_m_covers" ] && [ "$_e_oracle" = "$_m_oracle" ]; then
    printf 'DUPLICATE_JOURNEY: entry matches %s — attach this regression to the existing journey instead of minting a new one\n' "$_mid" >&2
    _dupe_errors=$((_dupe_errors + 1))
  fi
done

if [ "$_dupe_errors" -gt 0 ]; then
  _emit "INTAKE REFUSED: $_dupe_errors duplicate(s) found (DUPLICATE_JOURNEY above). No write to $MAP."
  exit 1
fi

# ---------------------------------------------------------------------------
# _write_promoted_entry OLD_ID NEW_ID -> the entry block (read from stdin)
# with ONLY two rewrites applied: the heading id, and a `test:` value's
# literal `<n>` placeholder token (mirrors commit 4b08dcb — journey-inbox-
# triage.sh's test-placeholder substitution). Every other line — including
# origin/author_status/evidence, already proven correct in step 4 — copies
# through byte-identical; this gate never forces fields the way the
# simulator-triage promotion does, because the intake-specific checks
# already required the entry to carry the exact values a REALITY journey
# must have.
# The heading substitution below matches on '^## <oldid> ' (trailing
# space) — guaranteed to match by the ENTRY_HEADING_INVALID grammar check
# in step 4 (V-T5 F1), and re-asserted before the rename (layer 2, below).
# ---------------------------------------------------------------------------
_write_promoted_entry() {
  _oid="$1"; _nid="$2"
  awk -v oldid="$_oid" -v newid="JOURNEY-$_nid" -v nid="$_nid" '
    NR == 1 {
      pat = "^## " oldid " "
      if ($0 ~ pat) { sub(pat, "## " newid " ") }
      print
      next
    }
    /^test:/ {
      line = $0
      gsub(/<n>/, nid, line)
      print line
      next
    }
    { print }
  '
}

# ── step 6: id assignment, 401 upward, skipping ids already in MAP ─────────
_used_ids="$(journey_ids)"
_next=401
while printf '%s\n' "$_used_ids" | grep -qxF "JOURNEY-$_next"; do
  _next=$((_next + 1))
done
_nid="$_next"

# ── step 7/8/9: temp + trap + mv (house rule 8) ─────────────────────────────
_map_tmp="$(mktemp "$(dirname "$MAP")/.map-XXXXXXXX")" || _die "mktemp failed (fail closed)"
trap 'rm -f "$_map_tmp"' EXIT INT TERM

cat "$MAP" > "$_map_tmp" || _die "failed to stage map temp (fail closed)"
{
  printf '\n'
  printf '%s\n' "$_entry_block" | _write_promoted_entry "$_entry_id" "$_nid"
} >> "$_map_tmp"

/bin/sh "$_here/lint-journey-map.sh" "$_map_tmp"
_rc=$?
if [ "$_rc" -ne 0 ]; then
  _emit "LINT_FAILED: promoted map failed lint-journey-map.sh self-check (temp cleaned; $MAP untouched)"
  exit 1
fi

# ── V-T5 F1 layer 2 (defense in depth): the ASSIGNED id's block must be
# non-empty in the temp map BEFORE any rename. The heading grammar check in
# step 4 already guarantees the rewrite matched, but never trust a single
# layer for an SSOT write: if the assigned block cannot be read back, die
# with the temp cleaned and MAP untouched — an unrewritten placeholder id
# can never again produce an empty 'INTAKE: ' success line at exit 0. ──────
JOURNEY_MAP="$_map_tmp"
export JOURNEY_MAP
_new_block="$(journey_block "JOURNEY-$_nid")"
[ -n "$_new_block" ] || _die "reality-intake: assigned block JOURNEY-$_nid missing from temp map after rewrite (fail closed; temp cleaned; $MAP untouched)"
_new_heading="$(printf '%s\n' "$_new_block" | head -n1)"

mv "$_map_tmp" "$MAP" || _die "failed to write $MAP (fail closed)"
trap - EXIT INT TERM

_emit "INTAKE: ${_new_heading#\#\# }"
exit 0
