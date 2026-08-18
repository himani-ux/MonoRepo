#!/bin/sh
# journey-inbox-triage.sh MAP INBOX [--approve]
#
# Human-approved inbox->map promotion gate (spec DC-2). Promotes ONLY
# promotion_status: ACCEPTED entries from INBOX into MAP as real
# JOURNEY-<n> blocks. Never automatic — see --approve below. Promotion is a
# transaction: MAP and INBOX are both updated, or neither is.
#
# ── Argument parsing ────────────────────────────────────────────────────────
# --approve may appear in any argument position (mirrors
# journey/bin/uat-report-promote.sh). The remaining two args are positional
# (MAP, INBOX), original relative order preserved.
#
# ── --approve refuses BEFORE any other work (house rule 7) ─────────────────
# Without --approve: refuse immediately. Nothing is read (not even a file
# readability check), nothing is written. This happens before usage
# validation too — a malformed invocation without --approve still refuses
# on APPROVE_REQUIRED, never on a USAGE error, because "did a human approve
# this" is checked first.
#
# ── With --approve, in order ────────────────────────────────────────────────
#   1. usage validation (exactly 2 positional args) -> exit 2
#   2. both files exist and are readable                -> exit 2
#   3. compose lint-journey-inbox.sh INBOX, then lint-journey-map.sh MAP, as
#      EXECUTABLES (never re-implemented), fail-closed on non-zero
#      (LINT_FAILED pass-through style, mirrors
#      journey/bin/check-uat-preconditions.sh's composition idiom: the
#      composed lint's own diagnostics print, THEN this gate's own
#      LINT_FAILED wrapper line).
#   4. backlog warning (spec 13.2) — computed and printed here, unconditional
#      on everything that follows: a lint-clean inbox always gets its
#      PROPOSED count reported, whether or not this run goes on to promote
#      anything.
#   5. select entries whose promotion_status is EXACTLY ACCEPTED — read via
#      the SAME first-match `inbox_field` accessor lint-journey-inbox.sh
#      uses (L11 discipline, see below). Zero ACCEPTED entries ->
#      NO_ACCEPTED_ENTRIES (an invoked promotion with nothing to promote
#      never passes vacuously).
#   6. deterministic dedup: for each ACCEPTED entry, normalize its `covers:`
#      (split on commas, trim each token, sort) and its `oracle:`
#      (whitespace-normalized: collapse runs of spaces/tabs, trim). A match
#      on BOTH keys against an existing MAP journey, or against ANOTHER
#      ACCEPTED entry, is DUPLICATE_JOURNEY. All duplicates accumulate
#      (fail-slow); any duplicate at all refuses the WHOLE run (no partial
#      promotion of the non-duplicate entries).
#   7. build a TEMP copy of MAP with one `## JOURNEY-<id>` block appended per
#      ACCEPTED entry (ids from 301 upward, skipping ids already in MAP or
#      already assigned this run — the persona-run.sh next-free idiom).
#      Forced fields regardless of entry content: origin: SIMULATOR,
#      author_status: UNWRITTEN. promotion_status, rejected_reason, and
#      every simulator_trace line are NEVER copied. flows/data_fixtures/
#      exemptions (not carried by a pre-promotion candidate) are added as
#      `[]` — required-present, legally-blank fields per
#      lint-journey-map.sh. Then lint-journey-map.sh runs on the TEMP map
#      (L12 self-check) — non-zero refuses, temp cleaned, MAP untouched.
#   8. build a TEMP copy of INBOX: each promoted entry's promotion_status
#      line is left as `promotion_status: ACCEPTED` and a NEW line is
#      inserted directly after it: `promoted_as: JOURNEY-<id>`. Then
#      lint-journey-inbox.sh runs on the TEMP inbox — non-zero refuses, both
#      temps cleaned, MAP and INBOX untouched.
#   9. both temps lint-clean -> mv temp map over MAP, THEN mv temp inbox over
#      INBOX (map first, inbox second: the map is the SSOT mutation; the
#      inbox update is only the audit-trail annotation of a fact the map
#      write already established, so this ordering makes the map, not the
#      inbox, the single source of truth for "did this promote" if the
#      process is ever interrupted between the two renames).
#  10. success: one `PROMOTED: INBOX-<n> -> JOURNEY-<id>` line per promotion,
#      plus final counts. Exit 0.
#
# Any failure at any point before step 9's renames -> the temp+trap cleans
# both temps; neither MAP nor INBOX is touched (house rule 8).
#
# ── L11 (binding) ───────────────────────────────────────────────────────────
# lint-journey-inbox.sh validates promotion_status by reading it with
# inbox_field, which returns the FIRST matching line in a block — and does
# NOT flag a block that carries the key twice (e.g. `promotion_status:
# PROPOSED` followed later by `promotion_status: ACCEPTED`) as a duplicate.
# This gate reads promotion_status the IDENTICAL way, via the shared
# inbox_field accessor (journey/lib/journey-lib.sh), for the exact same
# entries, everywhere this gate needs to know an entry's status: ACCEPTED
# selection (step 5), dedup normalization inputs are read from ACCEPTED
# entries only so no separate read is needed there, and the promoted_as
# stamping awk pass (step 8) fires on the FIRST `promotion_status:` line
# under a heading, matching the accessor's own first-match semantics. A
# PROPOSED-then-ACCEPTED duplicate-scalar entry is therefore classified
# PROPOSED end-to-end by this gate, never promoted, exactly as
# lint-journey-inbox.sh itself reads it — the two can never disagree.
#
# ── L12 (binding) ───────────────────────────────────────────────────────────
# lint-journey-inbox.sh deliberately defers map-enum validity to
# lint-journey-map.sh, composed at promotion (journey-inbox-format.md §4.2).
# This gate IS that composition point: after writing the candidate map to a
# temp file, lint-journey-map.sh runs on the temp as an executable, and a
# non-zero exit refuses the whole run before any rename.
#
# ── Codes (own; closed enum, this gate) ─────────────────────────────────────
#   APPROVE_REQUIRED       — --approve absent (refuses before any other work)
#   LINT_FAILED             — INBOX failed lint-journey-inbox.sh, OR MAP
#                              failed lint-journey-map.sh (pre-flight), OR
#                              the temp map/inbox this gate built failed its
#                              own self-check lint (L12) — message states
#                              which
#   NO_ACCEPTED_ENTRIES     — zero promotion_status: ACCEPTED entries
#                              (anti-vacuous)
#   DUPLICATE_JOURNEY: <inbox-id> matches <journey-or-inbox-id> — normalized
#                              covers+oracle collide with an existing MAP
#                              journey or with another ACCEPTED entry
#   ENTRY_HEADING_INVALID: <inbox-id>: ... — an ACCEPTED entry's heading is
#                              not the canonical `## INBOX-<digits> —
#                              "<title>"` form (V-T5 F1, appended: a
#                              glued/malformed heading must never reach the
#                              promotion rewrite — see the check below for
#                              the fail-open it closes)
# + pass-through of whatever lint-journey-inbox.sh / lint-journey-map.sh
# emit on the LINT_FAILED paths (their own diagnostics print first).
#
# Usage error / missing MAP or INBOX file: exit 2 (house convention). Gate
# violation (APPROVE_REQUIRED, LINT_FAILED, NO_ACCEPTED_ENTRIES,
# DUPLICATE_JOURNEY, ENTRY_HEADING_INVALID): exit 1. Success: exit 0.
#
# Deps: POSIX sh, awk, grep, sed, mktemp. shellcheck shell=sh

set -u

_here="$(cd "$(dirname "$0")" && pwd)"
LIB="$_here/../lib/journey-lib.sh"

_emit() { printf '%s\n' "$*" >&2; }
_die()  { _emit "$*"; exit 1; }

# ── parse: --approve may appear anywhere; MAP/INBOX stay positional in their
# original relative order (mirrors uat-report-promote.sh; no arrays, bash
# 3.2 compatible). ──────────────────────────────────────────────────────────
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
  _emit "APPROVE_REQUIRED: promotion requires human --approve (never automatic). Nothing read, nothing written."
  exit 1
fi

[ $# -eq 2 ] || {
  _emit "Usage: journey-inbox-triage.sh MAP INBOX [--approve]"
  exit 2
}
MAP="$1"; INBOX="$2"

[ -f "$MAP" ] || {
  _emit "journey-inbox-triage: file not found: $MAP"
  exit 2
}
[ -f "$INBOX" ] || {
  _emit "journey-inbox-triage: file not found: $INBOX"
  exit 2
}

# ── compose lint-journey-inbox.sh INBOX, then lint-journey-map.sh MAP,
# FIRST, as executables — never re-implemented. LINT_FAILED pass-through
# style (mirrors check-uat-preconditions.sh): the composed lint's own
# diagnostics print, then this gate's own wrapper line. ────────────────────
/bin/sh "$_here/lint-journey-inbox.sh" "$INBOX"
_rc=$?
if [ "$_rc" -ne 0 ]; then
  _emit "LINT_FAILED: inbox failed lint-journey-inbox.sh: $INBOX"
  exit 1
fi

/bin/sh "$_here/lint-journey-map.sh" "$MAP"
_rc=$?
if [ "$_rc" -ne 0 ]; then
  _emit "LINT_FAILED: map failed lint-journey-map.sh: $MAP"
  exit 1
fi

JOURNEY_MAP="$MAP"
JOURNEY_INBOX="$INBOX"
export JOURNEY_MAP JOURNEY_INBOX
# shellcheck disable=SC1090
. "$LIB"

# ── backlog warning (spec 13.2) — unconditional once both inputs are known
# lint-clean; fires whether or not this run goes on to promote anything
# ("always, even on success"). ──────────────────────────────────────────────
_proposed_count=0
for _id in $(inbox_ids | sort -u); do
  _ps="$(inbox_field "$_id" promotion_status 2>/dev/null)" || _ps=""
  [ "$_ps" = "PROPOSED" ] && _proposed_count=$((_proposed_count + 1))
done
if [ "$_proposed_count" -gt 10 ]; then
  _emit "WARNING: inbox backlog $_proposed_count PROPOSED entries exceeds threshold 10 (spec 13.2)"
fi

# ── select ACCEPTED entries — first-match inbox_field (L11) ────────────────
_accepted=""
for _id in $(inbox_ids | sort -u); do
  _ps="$(inbox_field "$_id" promotion_status 2>/dev/null)" || _ps=""
  [ "$_ps" = "ACCEPTED" ] || continue
  _accepted="$_accepted $_id"
done
_accepted="${_accepted# }"

if [ -z "$_accepted" ]; then
  _emit "NO_ACCEPTED_ENTRIES: no promotion_status: ACCEPTED entries found in $INBOX"
  exit 1
fi

# ── heading grammar on ACCEPTED entries (V-T5 F1, same class as
# journey-reality-intake.sh's ENTRY_HEADING_INVALID): lint-journey-inbox.sh
# does NOT validate entry-heading grammar (RED-proven: a glued
# '## INBOX-1—"title"' heading lints clean at exit 0), and the promotion
# rewrite in _write_promoted_block substitutes on '^## <id> ' — trailing
# space. A glued ACCEPTED heading would silently no-op that rewrite and
# land a literal '## INBOX-<n>—...' heading in the MAP — invisible to
# journey_ids AND to lint-journey-map's per-journey checks (a smuggled
# section in the SSOT) — while still printing 'PROMOTED:' at exit 0. Fail
# closed here, fail-slow across entries, refusing the WHOLE run
# (all-or-nothing, same as dedup). The pattern is STATIC (no operator data
# interpolated — L22 does not arise). Canonical grammar:
# '## INBOX-<digits> — "<title>"' (spaced em-dash, double-quoted non-empty
# title — the form every inbox fixture and journey-inbox-format.md use). ──
_heading_errors=0
for _aid in $_accepted; do
  _h="$(inbox_block "$_aid" | head -n1)"
  if ! printf '%s\n' "$_h" | grep -qE '^## INBOX-[0-9]+ — ".+"$'; then
    printf 'ENTRY_HEADING_INVALID: %s: heading must match %s (spaced em-dash, double-quoted title; found: %s)\n' \
      "$_aid" '## INBOX-<digits> — "<title>"' "$_h" >&2
    _heading_errors=$((_heading_errors + 1))
  fi
done
if [ "$_heading_errors" -gt 0 ]; then
  _emit "TRIAGE REFUSED: $_heading_errors malformed ACCEPTED heading(s) (ENTRY_HEADING_INVALID above). No write to $MAP or $INBOX."
  exit 1
fi

# ── norm_covers / norm_oracle: shared with journey-reality-intake.sh, now
# extracted to journey/lib/journey-lib.sh (sourced above) so both dedup
# passes in the framework normalize identically — see the lib for the
# sort -u rationale (V-T2 F1 / L15). ────────────────────────────────────────

# ── dedup: ACCEPTED entries vs existing MAP journeys ────────────────────────
_dupe_errors=0
_map_ids="$(journey_ids | sort -u)"

for _aid in $_accepted; do
  _a_covers="$(norm_covers "$(inbox_field "$_aid" covers 2>/dev/null)")"
  _a_oracle="$(norm_oracle "$(inbox_field "$_aid" oracle 2>/dev/null)")"

  for _mid in $_map_ids; do
    _m_covers="$(norm_covers "$(journey_field "$_mid" covers 2>/dev/null)")"
    _m_oracle="$(norm_oracle "$(journey_field "$_mid" oracle 2>/dev/null)")"
    if [ "$_a_covers" = "$_m_covers" ] && [ "$_a_oracle" = "$_m_oracle" ]; then
      printf 'DUPLICATE_JOURNEY: %s matches %s\n' "$_aid" "$_mid" >&2
      _dupe_errors=$((_dupe_errors + 1))
    fi
  done
done

# ── dedup: ACCEPTED entries vs EACH OTHER (i < j only, one report per pair) ─
_prev_accepted=""
for _aid in $_accepted; do
  _a_covers="$(norm_covers "$(inbox_field "$_aid" covers 2>/dev/null)")"
  _a_oracle="$(norm_oracle "$(inbox_field "$_aid" oracle 2>/dev/null)")"
  for _bid in $_prev_accepted; do
    _b_covers="$(norm_covers "$(inbox_field "$_bid" covers 2>/dev/null)")"
    _b_oracle="$(norm_oracle "$(inbox_field "$_bid" oracle 2>/dev/null)")"
    if [ "$_a_covers" = "$_b_covers" ] && [ "$_a_oracle" = "$_b_oracle" ]; then
      printf 'DUPLICATE_JOURNEY: %s matches %s\n' "$_aid" "$_bid" >&2
      _dupe_errors=$((_dupe_errors + 1))
    fi
  done
  _prev_accepted="$_prev_accepted $_aid"
done

if [ "$_dupe_errors" -gt 0 ]; then
  _emit "TRIAGE REFUSED: $_dupe_errors duplicate(s) found (DUPLICATE_JOURNEY above). No write to $MAP or $INBOX."
  exit 1
fi

# ---------------------------------------------------------------------------
# _write_promoted_block ENTRY_ID NEW_ID -> a "## JOURNEY-<NEW_ID> ..." block
# on stdout, built field-by-field from the inbox entry. Never copies
# promotion_status, rejected_reason, promoted_as, or any simulator_trace
# line — those simply aren't read here. origin/author_status are forced;
# flows/data_fixtures/exemptions (not carried by a pre-promotion candidate)
# are added as the map's own blank-list convention, "[]".
# The heading sed below substitutes on '^## <id> ' (trailing space) —
# guaranteed to match by the ENTRY_HEADING_INVALID grammar check above
# (V-T5 F1), and re-asserted after the temp-map write (layer 2, below).
# ---------------------------------------------------------------------------
_write_promoted_block() {
  _eid="$1"; _nid="$2"
  _heading="$(inbox_block "$_eid" | head -n1 | sed "s/^## ${_eid} /## JOURNEY-${_nid} /")"
  printf '\n%s\n' "$_heading"
  printf '%-17s%s\n' "origin:" "SIMULATOR"
  printf '%-17s%s\n' "persona:" "$(inbox_field "$_eid" persona 2>/dev/null)"
  printf '%-17s%s\n' "goal:" "$(inbox_field "$_eid" goal 2>/dev/null)"
  printf '%-17s%s\n' "priority:" "$(inbox_field "$_eid" priority 2>/dev/null)"
  printf '%-17s%s\n' "covers:" "$(inbox_field "$_eid" covers 2>/dev/null)"
  printf '%-17s%s\n' "flows:" "[]"
  printf '%-17s%s\n' "oracle_surface:" "$(inbox_field "$_eid" oracle_surface 2>/dev/null)"
  printf '%-17s%s\n' "negative_states:" "$(inbox_field "$_eid" negative_states 2>/dev/null)"
  printf '%-17s%s\n' "data_fixtures:" "[]"
  inbox_block "$_eid" | awk '
    /^steps:/ { print; ins = 1; next }
    ins && /^[a-zA-Z_][a-zA-Z0-9_]*:/ { exit }
    ins { print }
  '
  printf '%-17s%s\n' "oracle:" "$(inbox_field "$_eid" oracle 2>/dev/null)"
  printf '%-17s%s\n' "evidence:" "$(inbox_field "$_eid" evidence 2>/dev/null)"
  # V1 F4: a candidate's test: value may carry the literal placeholder token
  # `<n>` (the simulator cannot know its future JOURNEY-<n> id at generation
  # time — journey-inbox-format.md §6). Substitute ONLY that exact token
  # with the id just assigned to this promotion; a test value carrying no
  # `<n>` token (the normal case) copies through byte-identical.
  _test_val="$(inbox_field "$_eid" test 2>/dev/null)"
  case "$_test_val" in
    *'<n>'*) _test_val="$(printf '%s' "$_test_val" | sed "s/<n>/${_nid}/g")" ;;
  esac
  printf '%-17s%s\n' "test:" "$_test_val"
  printf '%-17s%s\n' "runner:" "$(inbox_field "$_eid" runner 2>/dev/null)"
  printf '%-17s%s\n' "author_status:" "UNWRITTEN"
  printf '%-17s%s\n' "exemptions:" "[]"
}

# ── temp + trap + mv (house rule 8): nothing with a final name exists on
# disk on any failure path from here on. ────────────────────────────────────
_map_tmp="$(mktemp "$(dirname "$MAP")/.map-XXXXXXXX")" || _die "mktemp failed (fail closed)"
_inbox_tmp="$(mktemp "$(dirname "$INBOX")/.inbox-XXXXXXXX")" || {
  rm -f "$_map_tmp"
  _die "mktemp failed (fail closed)"
}
trap 'rm -f "$_map_tmp" "$_inbox_tmp"' EXIT INT TERM

cat "$MAP" > "$_map_tmp" || _die "failed to stage map temp (fail closed)"

# ── id assignment: 301 upward, skipping ids already in MAP or already
# assigned this run (persona-run.sh's next-free idiom, base 301 not 201). ──
_used_ids="$(journey_ids)"
_next=301
_assignments=""
for _aid in $_accepted; do
  while printf '%s\n' "$_used_ids" | grep -qxF "JOURNEY-$_next"; do
    _next=$((_next + 1))
  done
  _nid="$_next"
  _write_promoted_block "$_aid" "$_nid" >> "$_map_tmp"
  _used_ids="$_used_ids
JOURNEY-$_nid"
  _assignments="$_assignments
$_aid JOURNEY-$_nid"
  _next=$((_next + 1))
done
_assignments="$(printf '%s\n' "$_assignments" | sed '/^$/d')"

# ── L12 self-check: the temp map must itself be lint-clean before anything
# is renamed onto MAP. ───────────────────────────────────────────────────────
/bin/sh "$_here/lint-journey-map.sh" "$_map_tmp"
_rc=$?
if [ "$_rc" -ne 0 ]; then
  _emit "LINT_FAILED: promoted map failed lint-journey-map.sh self-check (temp cleaned; $MAP untouched)"
  exit 1
fi

# ── V-T5 F1 layer 2 (defense in depth): every ASSIGNED JOURNEY-<id> block
# must be non-empty in the temp map BEFORE any rename. The ACCEPTED-heading
# grammar check above guarantees _write_promoted_block's heading rewrite
# matched, but an SSOT write never trusts a single layer: an unreadable
# assigned block dies here with both temps cleaned, MAP and INBOX
# untouched — a no-opped rewrite can never again print 'PROMOTED:' at
# exit 0. heredoc-fed while, never `| while read` (house rule 2). ──────────
_prev_journey_map="$JOURNEY_MAP"
JOURNEY_MAP="$_map_tmp"
export JOURNEY_MAP
while IFS= read -r _line; do
  [ -z "$_line" ] && continue
  _jid="${_line#* }"
  [ -n "$(journey_block "$_jid")" ] || \
    _die "triage: assigned block $_jid missing from temp map after rewrite (fail closed; temps cleaned; $MAP and $INBOX untouched)"
done << _ASSERT_EOF_
$_assignments
_ASSERT_EOF_
JOURNEY_MAP="$_prev_journey_map"
export JOURNEY_MAP

# ── build the temp inbox: stamp promoted_as: JOURNEY-<id> directly after
# each promoted entry's promotion_status line. Fires on the FIRST
# promotion_status: line under a heading (L11 — matches inbox_field's own
# first-match semantics), and only for ids in the assignment map. ──────────
_assign_str=""
while IFS= read -r _line; do
  [ -z "$_line" ] && continue
  _aid="${_line%% *}"
  _jid="${_line#* }"
  _assign_str="$_assign_str $_aid=$_jid"
done << _ASSIGN_EOF_
$_assignments
_ASSIGN_EOF_

awk -v assign="$_assign_str" '
  BEGIN {
    n = split(assign, pairs, " ")
    for (i = 1; i <= n; i++) {
      if (pairs[i] == "") continue
      split(pairs[i], kv, "=")
      map[kv[1]] = kv[2]
    }
  }
  /^## INBOX-[0-9]+/ {
    match($0, /INBOX-[0-9]+/)
    cur = substr($0, RSTART, RLENGTH)
    seen = 0
    print
    next
  }
  {
    if (cur != "" && !seen && (cur in map) && $0 ~ /^promotion_status:/) {
      print
      printf "%-17s%s\n", "promoted_as:", map[cur]
      seen = 1
      next
    }
    print
  }
' "$INBOX" > "$_inbox_tmp"

/bin/sh "$_here/lint-journey-inbox.sh" "$_inbox_tmp"
_rc=$?
if [ "$_rc" -ne 0 ]; then
  _emit "LINT_FAILED: updated inbox failed lint-journey-inbox.sh self-check (temp cleaned; $MAP and $INBOX untouched)"
  exit 1
fi

# ── both temps lint-clean: mv map first, inbox second (see header comment
# for the ordering rationale). ──────────────────────────────────────────────
mv "$_map_tmp" "$MAP" || _die "failed to write $MAP (fail closed)"
mv "$_inbox_tmp" "$INBOX" || _die "failed to write $INBOX (fail closed) -- $MAP was already updated; reconcile manually"
trap - EXIT INT TERM

for _line in $(printf '%s\n' "$_assignments" | tr ' ' '@'); do
  _aid="${_line%%@*}"
  _jid="${_line#*@}"
  _emit "PROMOTED: $_aid -> $_jid"
done

_n_promoted=$(printf '%s\n' "$_assignments" | grep -c .)
_emit "TRIAGE COMPLETE: $_n_promoted promoted; $_proposed_count PROPOSED remaining in $INBOX"
exit 0
