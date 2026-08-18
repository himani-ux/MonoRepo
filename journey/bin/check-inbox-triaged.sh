#!/bin/sh
# check-inbox-triaged.sh INBOX_PATH — the zero-PROPOSED phase-exit leg made
# executable (V1 F2; Step 2.txt journey phase-exit law; design spec
# journey-validation-layer-design.md §7 "Wired gates").
#
# The Step 3 phase-exit law reads: "IF a JOURNEY_INBOX.md exists at the
# project root, zero promotion_status: PROPOSED entries remain" — that leg
# named no single executable a phase-exit citation (or CI) could run. This
# gate is that check.
#
# The "no inbox file" case is a DOCUMENTED N/A, not a vacuous pass: per the
# same Step 2 law, "no inbox file means no inbox condition — the inbox is
# created by the first simulator pass, never generated at Step 2." A
# project that has never run a simulator pass has nothing to triage, so
# this gate prints an explicit SKIP line (never a silent, unexplained exit
# 0) and exits 0 — the condition is inapplicable, not satisfied.
#
# Composes lint-journey-inbox.sh FIRST, as an executable (never
# re-implemented) — the same LINT_FAILED pass-through composition idiom
# journey/bin/check-uat-preconditions.sh and journey/bin/journey-inbox-triage.sh
# use: the composed lint's own diagnostics print, THEN this gate's own
# LINT_FAILED wrapper line.
#
# promotion_status is read via the SAME first-match inbox_field accessor
# journey-inbox-triage.sh and lint-journey-inbox.sh use (L11 discipline —
# see journey-inbox-triage.sh's header comment): an entry carrying a
# duplicate promotion_status scalar line is classified by its FIRST line
# here too, so this gate can never disagree with the triage gate or the
# inbox lint about which entries are still PROPOSED.
#
# All violations accumulate fail-slow via a plain `for` loop — never
# `| while read` (pipeline-subshell counter loss is a known fail-open class
# in this framework, house rule 2).
#
# Codes (closed enum):
#   LINT_FAILED             — inbox failed lint-journey-inbox.sh (its own
#                              diagnostics print first, then this wrapper)
#   INBOX_UNTRIAGED: <id>    — a promotion_status: PROPOSED entry remains
#                              (one line per entry, fail-slow)
# Usage error (argc != 1): exit 2. No inbox file: SKIP line, exit 0. Any
# INBOX_UNTRIAGED: exit 1. Zero PROPOSED (lint-clean inbox): exit 0.
#
# Deps: POSIX sh, awk, grep, sed.
# shellcheck shell=sh

set -u

_here="$(cd "$(dirname "$0")" && pwd)"
LIB="$_here/../lib/journey-lib.sh"

usage() { printf 'Usage: check-inbox-triaged.sh INBOX_PATH\n' >&2; exit 2; }
[ $# -eq 1 ] || usage

INBOX="$1"

# ── no inbox file: documented N/A, not a vacuous pass (Step 2 law) ────────
if [ ! -f "$INBOX" ]; then
  printf 'SKIP: no inbox file — condition not applicable (inbox is created by the first simulator pass)\n'
  exit 0
fi

# ── compose lint-journey-inbox.sh FIRST, as an executable — never
# re-implemented. LINT_FAILED pass-through style (mirrors
# check-uat-preconditions.sh / journey-inbox-triage.sh): the composed
# lint's own diagnostics print, then this gate's own wrapper line. ────────
/bin/sh "$_here/lint-journey-inbox.sh" "$INBOX"
_rc=$?
if [ "$_rc" -ne 0 ]; then
  printf 'LINT_FAILED: inbox failed lint-journey-inbox.sh: %s\n' "$INBOX" >&2
  exit 1
fi

JOURNEY_INBOX="$INBOX"
export JOURNEY_INBOX
# shellcheck disable=SC1090
. "$LIB"

_untriaged=0
for _id in $(inbox_ids | sort -u); do
  _ps="$(inbox_field "$_id" promotion_status 2>/dev/null)" || _ps=""
  if [ "$_ps" = "PROPOSED" ]; then
    printf 'INBOX_UNTRIAGED: %s\n' "$_id" >&2
    _untriaged=$((_untriaged + 1))
  fi
done

if [ "$_untriaged" -gt 0 ]; then
  printf 'TRIAGE INCOMPLETE: %s PROPOSED entry(ies) remain in %s\n' "$_untriaged" "$INBOX" >&2
  exit 1
fi

printf 'OK: zero PROPOSED entries in %s\n' "$INBOX"
exit 0
