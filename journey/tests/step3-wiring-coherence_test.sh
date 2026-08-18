#!/bin/sh
# step3-wiring-coherence_test.sh — byte-locks the DC-4 Step 3 wiring amendment
# into Step 2.txt (spec 2026-07-10-simulator-reality-engines-goal.md DC-4;
# design 2026-06-22-journey-validation-layer-design.md §7 "Wired gates" + §8
# "Step 3" line). Model: journey/tests/doc-coherence_test.sh (assert_contains
# substring-anchor style, not full-fragment extraction — this amendment has
# no MARKER BEGIN/END pair of its own).
#
# Locks four things:
#   (a) the journey phase-exit law lines land in Step 2.txt verbatim
#   (b) the Step 3 simulator/triage sequence line lands verbatim
#   (c) the L18 SIMULATOR-covers re-anchor sentence lands verbatim
#   (d) every gate path the new text names actually exists on disk — a
#       phantom gate can never be cited (path-existence, house style per
#       journey-gen-acceptance_test.sh / refuter-fidelity-prompt_test.sh)
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$TESTS_DIR/../.."
S2="$ROOT/Step 2.txt"

if [ ! -f "$S2" ]; then
  printf 'FAIL: Step 2.txt not found at repo root\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
else
  _s2="$(cat "$S2")"

  # ── (b) Step 3 sequence: blind-author -> CI -> simulator pass -> triage ──
  assert_contains "$_s2" "blind test-author writes the phase's UNWRITTEN" \
    "Step 3 sequence: blind-author stage stated"
  assert_contains "$_s2" "journey/gen/runners/simulator-run.sh, RUN_LLM_GEN=1" \
    "Step 3 sequence: simulator pass names its runner + opt-in env"
  assert_contains "$_s2" "never a CI gate" \
    "Step 3 sequence: stochastic discovery is never a CI gate"
  assert_contains "$_s2" "inbox triage (human)" \
    "Step 3 sequence: triage is human, not automatic"

  # ── (c) L18 — SIMULATOR covers re-anchor is a triage-time human duty ────
  assert_contains "$_s2" "carries a screen-name" \
    "L18: promoted SIMULATOR journey carries screen-name covers"
  assert_contains "$_s2" "a human must re-anchor" \
    "L18: re-anchor is a stated human responsibility"
  assert_contains "$_s2" "covers: to FEAT-IDs at triage" \
    "L18: re-anchor target is FEAT-IDs, at triage"
  assert_contains "$_s2" "journey/bin/author-bundle.sh fails closed on the non-FEAT anchor" \
    "L18: author-bundle.sh fail-closed consequence stated"
  # ── (c-ext) V1 F3 — L18 names flows: [] and the test: <n> placeholder
  # alongside covers, the full re-anchor law's three placeholders ─────────
  assert_contains "$_s2" "carries THREE placeholders" \
    "L18: all three triage-time placeholders are named as a set (V1 F3)"
  assert_contains "$_s2" "a flows: [] empty-list" \
    "L18: flows: [] placeholder named (V1 F3)"
  assert_contains "$_s2" "flows: may optionally be re-anchored to real AFJ-IDs" \
    "L18: flows: re-anchor is optional, at triage (V1 F3)"
  assert_contains "$_s2" "a test: path that may carry the literal <n> token" \
    "L18: test: <n> placeholder named (V1 F3)"
  assert_contains "$_s2" "substituted with the assigned JOURNEY-<n> id at promotion" \
    "L18: test: <n> substitution law stated (V1 F3/F4)"

  # ── (a) phase-exit journey law ───────────────────────────────────────────
  assert_contains "$_s2" "phase exit (Step 3 build) extends to journeys" \
    "phase-exit: journey extension announced in the same block as QUALITY citation"
  assert_contains "$_s2" "sh journey/bin/check-journeys.sh passes for the" \
    "phase-exit: check-journeys.sh named as a condition"
  assert_contains "$_s2" "GREEN in the CI ledger or a logged" \
    "phase-exit: GREEN-or-exemption condition stated"
  assert_contains "$_s2" "JOURNEY_INBOX.md exists at the project root, zero" \
    "phase-exit: inbox condition is conditional on the file's existence"
  assert_contains "$_s2" "promotion_status: PROPOSED entries remain" \
    "phase-exit: zero-PROPOSED condition stated"
  assert_contains "$_s2" "sh journey/bin/check-inbox-triaged.sh JOURNEY_INBOX.md" \
    "phase-exit: zero-PROPOSED leg names its executable check (V1 F2)"
  assert_contains "$_s2" "journey/bin/journey-inbox-triage.sh JOURNEY_MAP.md JOURNEY_INBOX.md" \
    "phase-exit: triage invocation named"
  assert_contains "$_s2" "rejected entries carry rejected_reason" \
    "phase-exit: rejects require rejected_reason"
  assert_contains "$_s2" "the inbox is created by the first" \
    "phase-exit: no-inbox-file means no-inbox-condition, rationale stated"
  assert_contains "$_s2" "never generated at Step 2" \
    "phase-exit: inbox is never a Step 2 generation artifact"
  assert_contains "$_s2" "journey/bin/check-test-surface.sh against the running" \
    "phase-exit: surface check named"
  assert_contains "$_s2" "journey/bin/check-surface-staleness.sh" \
    "phase-exit: surface staleness check named"

  # ── placement law: JOURNEY_INBOX.md sits beside JOURNEY_MAP.md at root ──
  assert_contains "$_s2" "JOURNEY_MAP.md, JOURNEY_INBOX.md" \
    "placement: JOURNEY_INBOX.md enumerated beside JOURNEY_MAP.md at root"
fi

# ── (d) no phantom gates: every path the new text names must exist ────────
for _p in \
  "journey/bin/check-journeys.sh" \
  "journey/bin/journey-inbox-triage.sh" \
  "journey/bin/check-inbox-triaged.sh" \
  "journey/bin/check-test-surface.sh" \
  "journey/bin/check-surface-staleness.sh" \
  "journey/gen/runners/simulator-run.sh" \
  "journey/bin/author-bundle.sh" \
; do
  assert_exit 0 test -f "$ROOT/$_p"
done
