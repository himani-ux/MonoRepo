#!/bin/sh
# shellcheck shell=sh
# check-doc-format.sh PRD APP_FLOW [--allow-unlinked]
#
# Doc-format PREFLIGHT for doc-derived journey generation (review C5).
# The slicer fails closed on the FIRST malformed block; this preflight
# reports EVERY violation as an actionable per-id diagnostic so the operator
# fixes the docs in one pass BEFORE any generation is attempted.
#
# Contract: journey/docs/journey-gen-doc-format.md
#   §1 PRD    — '## FEAT-<n> — "<title>"' blocks; priority: P0..P3;
#               user_story (journey goal source); '- AC-<n>:' labeled
#               acceptance criteria (journey oracle source + AC accounting).
#   §2 APP_FLOW — '## User Journeys' section; '### AFJ-<n> — "<title>"'
#               headings; steps: (journey steps source).
#   §3b Screens — '## Screens' section; '### SCR-<n> — "<name>"' blocks with a
#               REQUIRED route: (TEST_SURFACE + touch-rule source). Unidded /
#               unnamed / no-route / duplicate ids fail closed; a screen whose
#               route is touched by no AFJ step (SCREEN_UNTOUCHED) fails unless
#               deferred by --allow-unlinked.
#   §3 link   — every P0/P1 FEAT and every AFJ must be linked from at least
#               one side (covers_flows / covers_features). Unlinked ids fail
#               by default; --allow-unlinked defers them to the structured
#               coverage-gap workflow (never an invented journey).
#
# Diagnostics go to stdout (lint convention); exit 1 if any. Exit 0 = the
# docs are generation-ready.
# Deps: POSIX sh, awk, grep, sed.

set -u
_die() { printf '%s\n' "$*" >&2; exit 1; }

ALLOW_UNLINKED=0
case "${3:-}" in
  --allow-unlinked) ALLOW_UNLINKED=1 ;;
  "") : ;;
  *) _die "usage: check-doc-format.sh PRD APP_FLOW [--allow-unlinked]" ;;
esac
[ $# -ge 2 ] || _die "usage: check-doc-format.sh PRD APP_FLOW [--allow-unlinked]"
PRD="$1"; APP_FLOW="$2"
[ -r "$PRD" ]      || _die "check-doc-format: file not readable: $PRD"
[ -r "$APP_FLOW" ] || _die "check-doc-format: file not readable: $APP_FLOW"

_tmp=$(mktemp -d) || _die "mktemp failed (fail closed)"
trap 'rm -rf "$_tmp"' EXIT INT TERM

problems=0
_p() { printf '%s\n' "$1"; problems=$((problems + 1)); }

FMT_DOC="journey/docs/journey-gen-doc-format.md"

# ── PRD: split into per-FEAT block files ──────────────────────────────────────
awk -v out="$_tmp" '
  /^## FEAT-([A-Z]+-)?[0-9]/ {
    match($0, /FEAT-([A-Z]+-)?[0-9]+/); id = substr($0, RSTART, RLENGTH)
    print id >> (out "/feat_order.txt")
    file = out "/prd_" id "_" (++n[id]) ".txt"
    print $0 > file
    next
  }
  file != "" { print >> file }
' "$PRD"

if [ ! -s "$_tmp/feat_order.txt" ]; then
  _p "PRD_NO_FEAT_BLOCKS: no '## FEAT-<n> — \"<title>\"' block found in $PRD — the PRD must emit machine-readable FEAT blocks, not only tables/prose (see $FMT_DOC §1)"
else
  # duplicates
  for _dup in $(sort "$_tmp/feat_order.txt" | uniq -d); do
    _p "DUPLICATE_FEAT_ID: $_dup appears more than once in $PRD — ids must be stable and unique"
  done

  # per-FEAT block checks (first block per id)
  for _fid in $(sort -u "$_tmp/feat_order.txt"); do
    _bf="$_tmp/prd_${_fid}_1.txt"
    _pri=$(awk '/^priority:/ { sub(/^priority:[ \t]*/, ""); sub(/[ \t]*#.*$/, ""); sub(/[ \t]+$/, ""); print; exit }' "$_bf")
    if [ -z "$_pri" ]; then
      _p "FEAT_PRIORITY_MISSING: $_fid — add 'priority: P0|P1|P2|P3' (machine-readable; the slicer never guesses)"
    else
      case "$_pri" in
        P0|P1|P2|P3) : ;;
        *) _p "FEAT_PRIORITY_INVALID: $_fid priority '$_pri' — use exactly one of P0|P1|P2|P3 (not must/should/nice; see $FMT_DOC §1)" ;;
      esac
    fi
    grep -qE '^user_story:[[:space:]]*[^[:space:]]' "$_bf" || \
      _p "FEAT_NO_USER_STORY: $_fid — add 'user_story: As <role>, I want <action>, so that <outcome>' (source of the journey goal)"
    if grep -qE '^acceptance_criteria:' "$_bf"; then
      grep -qE '^[[:space:]]*-[[:space:]]*AC-[0-9]+:' "$_bf" || \
        _p "FEAT_AC_UNLABELED: $_fid — acceptance criteria must carry '- AC-<n>:' labels (AC accounting in the coverage/provenance gates needs them)"
    else
      _p "FEAT_NO_ACCEPTANCE_CRITERIA: $_fid — add 'acceptance_criteria:' with '- AC-<n>:' lines (source of the journey oracle)"
    fi
  done
fi

# ── APP_FLOW: User Journeys section + per-AFJ checks ──────────────────────────
awk -v out="$_tmp" '
  /^## User Journeys/ { in_uj = 1; seen = 1; next }
  in_uj && /^## /     { in_uj = 0; next }
  in_uj && /^### / {
    if (match($0, /AFJ-[0-9]+/)) {
      id = substr($0, RSTART, RLENGTH)
      print id >> (out "/afj_order.txt")
      file = out "/afj_" id "_" (++n[id]) ".txt"
      print $0 > file
    } else {
      print $0 >> (out "/afj_unidded.txt")
      file = ""
    }
    next
  }
  in_uj && file != "" { print >> file }
  END { if (seen) print "yes" > (out "/uj_section.txt") }
' "$APP_FLOW"

if [ ! -f "$_tmp/uj_section.txt" ]; then
  _p "APP_FLOW_NO_USER_JOURNEYS: no '## User Journeys' section in $APP_FLOW — document journeys as '### AFJ-<n> — \"<title>\"' entries under it (see $FMT_DOC §2)"
else
  if [ -f "$_tmp/afj_unidded.txt" ]; then
    while IFS= read -r _h; do
      _p "APP_FLOW_UNIDDED: journey heading lacks an AFJ-<n> id: '$_h' — the slicer never invents ids"
    done < "$_tmp/afj_unidded.txt"
  fi
  if [ ! -s "$_tmp/afj_order.txt" ]; then
    _p "APP_FLOW_NO_JOURNEYS: the '## User Journeys' section has no '### ... AFJ-<n>' entries (see $FMT_DOC §2)"
  else
    for _dup in $(sort "$_tmp/afj_order.txt" | uniq -d); do
      _p "DUPLICATE_AFJ_ID: $_dup appears more than once in $APP_FLOW — ids must be stable and unique"
    done
    for _aid in $(sort -u "$_tmp/afj_order.txt"); do
      grep -qE '^steps:' "$_tmp/afj_${_aid}_1.txt" || \
        _p "AFJ_NO_STEPS: $_aid — add 'steps:' with the ordered path (source of the journey steps)"
    done
  fi
fi

# ── §3b Screens: '### SCR-<n> — "<name>"' blocks with route: ─────────────────
awk -v out="$_tmp" '
  /^## Screens/ { in_sc = 1; seen = 1; next }
  in_sc && /^## /  { in_sc = 0; next }
  in_sc && /^### / {
    if (match($0, /SCR-([A-Z]+-)?[0-9]+/)) {
      id = substr($0, RSTART, RLENGTH)
      print id >> (out "/scr_order.txt")
      file = out "/scr_" id "_" (++n[id]) ".txt"
      print $0 > file
      if ($0 !~ /"[^"]+"/) print id >> (out "/scr_unnamed.txt")
    } else {
      print $0 >> (out "/scr_unidded.txt")
      file = ""
    }
    next
  }
  in_sc && file != "" { print >> file }
  END { if (seen) print "yes" > (out "/sc_section.txt") }
' "$APP_FLOW"

if [ ! -f "$_tmp/sc_section.txt" ]; then
  _p "SCREENS_SECTION_MISSING: no '## Screens' section in $APP_FLOW — every screen needs a '### SCR-<n> — \"<name>\"' block with route: (see $FMT_DOC §3b)"
else
  if [ -f "$_tmp/scr_unidded.txt" ]; then
    while IFS= read -r _h; do
      _p "SCREEN_UNIDDED: screen heading lacks an SCR-<n> id: '$_h' — ids are never invented downstream"
    done < "$_tmp/scr_unidded.txt"
  fi
  if [ -f "$_tmp/scr_unnamed.txt" ]; then
    while IFS= read -r _sid; do
      _p "SCREEN_UNNAMED: $_sid has no quoted \"<name>\" — the name is the TEST_SURFACE key (see $FMT_DOC §3b)"
    done < "$_tmp/scr_unnamed.txt"
  fi
  if [ ! -s "$_tmp/scr_order.txt" ]; then
    _p "SCREENS_SECTION_MISSING: the '## Screens' section has no '### SCR-<n> — \"<name>\"' entries (see $FMT_DOC §3b)"
  else
    for _dup in $(sort "$_tmp/scr_order.txt" | uniq -d); do
      _p "DUPLICATE_SCREEN_ID: $_dup appears more than once in $APP_FLOW — ids must be stable and unique"
    done
    _afj_steps=$(cat "$_tmp"/afj_AFJ-*_1.txt 2>/dev/null || true)
    for _sid in $(sort -u "$_tmp/scr_order.txt"); do
      _sf="$_tmp/scr_${_sid}_1.txt"
      _route=$(awk '/^route:/ { sub(/^route:[ \t]*/, ""); sub(/[ \t]*#.*$/, ""); sub(/[ \t]+$/, ""); print; exit }' "$_sf")
      if [ -z "$_route" ]; then
        _p "SCREEN_NO_ROUTE: $_sid — add 'route: /<path>' (REQUIRED; the touch rule and the mock contract key off it)"
        continue
      fi
      if ! printf '%s\n' "$_afj_steps" | grep -F -- "$_route" >/dev/null 2>&1; then
        if [ "$ALLOW_UNLINKED" -eq 1 ]; then
          printf 'note: SCREEN_UNTOUCHED deferred by --allow-unlinked: %s (%s) — no AFJ step mentions this route; add a journey or log a structured gap\n' "$_sid" "$_route"
        else
          _p "SCREEN_UNTOUCHED: $_sid route '$_route' appears in no AFJ steps — add a journey touching it, or defer with --allow-unlinked (see $FMT_DOC §3b)"
        fi
      fi
    done
  fi
fi

# ── §3 linkage: every P0/P1 FEAT and every AFJ linked from at least one side ──
if [ -s "$_tmp/feat_order.txt" ] && [ -f "$_tmp/uj_section.txt" ]; then
  _all_afj_covers=$(cat "$_tmp"/afj_AFJ-*_1.txt 2>/dev/null | grep -E '^covers_features:' | sed 's/^covers_features:[[:space:]]*//')
  _all_feat_covers=$(cat "$_tmp"/prd_FEAT-*_1.txt 2>/dev/null | grep -E '^covers_flows:' | sed 's/^covers_flows:[[:space:]]*//')

  for _fid in $(sort -u "$_tmp/feat_order.txt"); do
    _bf="$_tmp/prd_${_fid}_1.txt"
    _pri=$(awk '/^priority:/ { sub(/^priority:[ \t]*/, ""); sub(/[ \t]*#.*$/, ""); sub(/[ \t]+$/, ""); print; exit }' "$_bf")
    case "$_pri" in P0|P1) : ;; *) continue ;; esac
    if ! grep -qE '^covers_flows:[[:space:]]*AFJ-[0-9]' "$_bf" \
       && ! printf '%s\n' "$_all_afj_covers" | grep -qE "(^|[^0-9A-Za-z-])${_fid}([^0-9]|\$)"; then
      if [ "$ALLOW_UNLINKED" -eq 1 ]; then
        printf 'note: UNLINKED_FEAT deferred by --allow-unlinked: %s — MUST become a structured coverage gap (owner/expiry/reviewer), never an invented journey\n' "$_fid"
      else
        _p "UNLINKED_FEAT: $_fid ($_pri) has no covers_flows and no AFJ back-link — add a link, or author a structured coverage gap and re-run with --allow-unlinked (see $FMT_DOC §3)"
      fi
    fi
  done

  if [ -s "$_tmp/afj_order.txt" ]; then
    for _aid in $(sort -u "$_tmp/afj_order.txt"); do
      _ba="$_tmp/afj_${_aid}_1.txt"
      if ! grep -qE '^covers_features:[[:space:]]*FEAT-([A-Z]+-)?[0-9]' "$_ba" \
         && ! printf '%s\n' "$_all_feat_covers" | grep -qE "(^|[^0-9A-Za-z-])${_aid}([^0-9]|\$)"; then
        if [ "$ALLOW_UNLINKED" -eq 1 ]; then
          printf 'note: UNLINKED_AFJ deferred by --allow-unlinked: %s — MUST become a structured coverage gap, never an invented journey\n' "$_aid"
        else
          _p "UNLINKED_AFJ: $_aid has no covers_features and no FEAT covers_flows link — add a link, or author a structured coverage gap and re-run with --allow-unlinked (see $FMT_DOC §3)"
        fi
      fi
    done
  fi
fi

if [ "$problems" -gt 0 ]; then
  printf 'check-doc-format: %d problem(s) — the docs are not generation-ready (fail closed)\n' "$problems"
  exit 1
fi
exit 0
