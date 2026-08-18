#!/bin/sh
# journey-inbox-triage_test.sh — TDD proofs for journey-inbox-triage.sh (DC-2)
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
GATE="$TESTS_DIR/../bin/journey-inbox-triage.sh"
LINTMAP="$TESTS_DIR/../bin/lint-journey-map.sh"
LINTINBOX="$TESTS_DIR/../bin/lint-journey-inbox.sh"
FX="$TESTS_DIR/fixtures/inbox/triage"

# ── --approve refuses BEFORE any other work (house rule 7) ─────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-base.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-golden.md" "$T/INBOX.md"
_map_before="$(cat "$T/MAP.md")"
_inbox_before="$(cat "$T/INBOX.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "no --approve -> exit 1"
assert_contains "$_out" "APPROVE_REQUIRED" "no --approve -> APPROVE_REQUIRED, refuses before any other work"
assert_eq "$_map_before" "$(cat "$T/MAP.md")" "APPROVE-refusal: MAP byte-unchanged"
assert_eq "$_inbox_before" "$(cat "$T/INBOX.md")" "APPROVE-refusal: INBOX byte-unchanged"
# even with a nonexistent MAP/INBOX, missing --approve refuses first, before
# any file-readability check — nothing is even attempted to be read.
_out="$(sh "$GATE" "$T/does-not-exist.md" "$T/also-missing.md" 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "no --approve, even with missing files -> still exit 1 (not 2) — approve gates before file checks"
assert_contains "$_out" "APPROVE_REQUIRED" "no --approve, missing files -> still APPROVE_REQUIRED, not a file-not-found message"
rm -rf "$T"

# ── usage / missing file: exit 2 (only once --approve is present — without
# it, APPROVE_REQUIRED fires first regardless of arg count; already proven
# above) ─────────────────────────────────────────────────────────────────────
assert_exit 2 sh "$GATE" --approve
assert_exit 2 sh "$GATE" a --approve
assert_exit 2 sh "$GATE" "$FX/does-not-exist.md" "$FX/JOURNEY_INBOX.triage-golden.md" --approve
assert_exit 2 sh "$GATE" "$FX/JOURNEY_MAP.triage-base.md" "$FX/does-not-exist.md" --approve

# ── golden promotion: 2 ACCEPTED + 1 PROPOSED + 1 REJECTED ─────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-base.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-golden.md" "$T/INBOX.md"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "golden promotion: exit 0"
assert_contains "$_out" "PROMOTED: INBOX-1 -> JOURNEY-301" "golden: INBOX-1 promoted to JOURNEY-301"
assert_contains "$_out" "PROMOTED: INBOX-2 -> JOURNEY-302" "golden: INBOX-2 promoted to JOURNEY-302"
assert_eq 2 "$(grep -c '^## JOURNEY-' "$T/MAP.md")" "golden: exactly 2 map blocks written"
assert_eq 1 "$(grep -c '^## JOURNEY-301 ' "$T/MAP.md")" "golden: JOURNEY-301 present"
assert_eq 1 "$(grep -c '^## JOURNEY-302 ' "$T/MAP.md")" "golden: JOURNEY-302 present"
assert_exit 0 sh "$LINTMAP" "$T/MAP.md"
assert_exit 0 sh "$LINTINBOX" "$T/INBOX.md"
# forced fields on the promoted blocks
assert_eq 2 "$(awk '/^## JOURNEY-30[12] /{f=1} f&&/^origin:/{print;f=0}' "$T/MAP.md" | grep -c 'SIMULATOR')" \
  "golden: both promoted blocks forced origin: SIMULATOR"
assert_eq 2 "$(awk '/^## JOURNEY-30[12] /{f=1} f&&/^author_status:/{print;f=0}' "$T/MAP.md" | grep -c 'UNWRITTEN')" \
  "golden: both promoted blocks forced author_status: UNWRITTEN"
# never copied: promotion_status/rejected_reason/simulator_trace never land in the map
assert_eq 0 "$(grep -c 'promotion_status\|rejected_reason\|simulator_trace' "$T/MAP.md")" \
  "golden: promotion_status/rejected_reason/simulator_trace never copied into the map"
# PROPOSED/REJECTED entries untouched; no promoted_as on them
assert_contains "$(cat "$T/INBOX.md")" '## INBOX-3 — "candidate 3"' "golden: PROPOSED entry (INBOX-3) still present"
assert_contains "$(cat "$T/INBOX.md")" '## INBOX-4 — "candidate 4"' "golden: REJECTED entry (INBOX-4) still present"
assert_eq 2 "$(grep -c '^promoted_as:' "$T/INBOX.md")" "golden: promoted_as stamped exactly twice (only the 2 ACCEPTED entries)"
rm -rf "$T"

# ── RED: NO_ACCEPTED_ENTRIES (anti-vacuous) ─────────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-base.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-no-accepted.md" "$T/INBOX.md"
_map_before="$(cat "$T/MAP.md")"; _inbox_before="$(cat "$T/INBOX.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "zero ACCEPTED entries -> exit 1"
assert_contains "$_out" "NO_ACCEPTED_ENTRIES" "zero ACCEPTED entries -> NO_ACCEPTED_ENTRIES"
assert_eq "$_map_before" "$(cat "$T/MAP.md")" "NO_ACCEPTED_ENTRIES: MAP byte-unchanged"
assert_eq "$_inbox_before" "$(cat "$T/INBOX.md")" "NO_ACCEPTED_ENTRIES: INBOX byte-unchanged"
rm -rf "$T"

# ── RED: DUPLICATE_JOURNEY vs an existing map journey ───────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-dupbase.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-dup-vs-map.md" "$T/INBOX.md"
_map_before="$(cat "$T/MAP.md")"; _inbox_before="$(cat "$T/INBOX.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "duplicate vs map -> exit 1"
assert_contains "$_out" "DUPLICATE_JOURNEY: INBOX-1 matches JOURNEY-500" \
  "normalized covers+oracle match against an existing map journey -> DUPLICATE_JOURNEY"
assert_eq "$_map_before" "$(cat "$T/MAP.md")" "DUPLICATE_JOURNEY vs map: MAP byte-unchanged (all-or-nothing)"
assert_eq "$_inbox_before" "$(cat "$T/INBOX.md")" "DUPLICATE_JOURNEY vs map: INBOX byte-unchanged (all-or-nothing)"
rm -rf "$T"

# ── RED: DUPLICATE_JOURNEY when the candidate's covers repeats a token ──────
# V-T2 F1: `sort` without -u kept the repeated token, so "FEAT-001, FEAT-001"
# normalized differently from "FEAT-001" and the true duplicate promoted.
# `sort -u` closes it: a repeated token can only ever collapse to the same
# set, never split two genuinely different sets apart.
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-dupcovers.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-dup-repeated-token.md" "$T/INBOX.md"
_map_before="$(cat "$T/MAP.md")"; _inbox_before="$(cat "$T/INBOX.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "covers with a repeated token vs single-token map journey -> exit 1 (V-T2 F1)"
assert_contains "$_out" "DUPLICATE_JOURNEY: INBOX-1 matches JOURNEY-600" \
  "repeated covers token normalizes to the same SET -> DUPLICATE_JOURNEY (V-T2 F1)"
assert_eq "$_map_before" "$(cat "$T/MAP.md")" "V-T2 F1: MAP byte-unchanged"
assert_eq "$_inbox_before" "$(cat "$T/INBOX.md")" "V-T2 F1: INBOX byte-unchanged"
rm -rf "$T"

# ── RED: DUPLICATE_JOURNEY between two ACCEPTED entries ─────────────────────
# also proves normalization is real, not literal string equality: the two
# entries' covers differ in token order/spacing and their oracle differs in
# whitespace runs, yet both normalize to the same key.
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-base.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-dup-entries.md" "$T/INBOX.md"
_map_before="$(cat "$T/MAP.md")"; _inbox_before="$(cat "$T/INBOX.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "duplicate between accepted entries -> exit 1"
assert_contains "$_out" "DUPLICATE_JOURNEY: INBOX-2 matches INBOX-1" \
  "two ACCEPTED entries with the same normalized covers+oracle key -> DUPLICATE_JOURNEY (i<j reported once)"
assert_eq "$_map_before" "$(cat "$T/MAP.md")" "DUPLICATE_JOURNEY entry-vs-entry: MAP byte-unchanged (all-or-nothing)"
assert_eq "$_inbox_before" "$(cat "$T/INBOX.md")" "DUPLICATE_JOURNEY entry-vs-entry: INBOX byte-unchanged (all-or-nothing)"
rm -rf "$T"

# ── all-or-nothing: ONE bad entry AMONG otherwise-clean ACCEPTED entries
# refuses the WHOLE batch — the clean sibling does NOT partially promote. ──
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-dupbase.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-mixed-allornothing.md" "$T/INBOX.md"
_map_before="$(cat "$T/MAP.md")"; _inbox_before="$(cat "$T/INBOX.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "mixed batch (1 clean + 1 duplicate) -> exit 1"
assert_contains "$_out" "DUPLICATE_JOURNEY: INBOX-2 matches JOURNEY-500" "the duplicate entry is named"
assert_not_contains "$_out" "PROMOTED:" "all-or-nothing: the CLEAN sibling entry is NOT partially promoted"
assert_eq "$_map_before" "$(cat "$T/MAP.md")" "all-or-nothing: MAP byte-unchanged (not even the clean entry landed)"
assert_eq "$_inbox_before" "$(cat "$T/INBOX.md")" "all-or-nothing: INBOX byte-unchanged (no promoted_as anywhere)"
rm -rf "$T"

# ── RED: PROMOTED_AS_INVALID (pass-through from the composed inbox lint) ───
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-base.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-promoted-as-invalid.md" "$T/INBOX.md"
_map_before="$(cat "$T/MAP.md")"; _inbox_before="$(cat "$T/INBOX.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "pre-existing malformed promoted_as -> exit 1"
assert_contains "$_out" "PROMOTED_AS_INVALID" "malformed promoted_as caught by the composed pre-flight lint (its own diagnostic passes through)"
assert_contains "$_out" "LINT_FAILED" "malformed promoted_as -> LINT_FAILED wrapper (inbox pre-flight)"
assert_eq "$_map_before" "$(cat "$T/MAP.md")" "PROMOTED_AS_INVALID: MAP byte-unchanged"
assert_eq "$_inbox_before" "$(cat "$T/INBOX.md")" "PROMOTED_AS_INVALID: INBOX byte-unchanged"
rm -rf "$T"

# ── RED: lint-failure pass-through (inbox side) ─────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-base.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-badheader.md" "$T/INBOX.md"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "broken inbox -> exit 1"
assert_contains "$_out" "BAD_HEADER" "broken inbox: underlying lint diagnostic passes through"
assert_contains "$_out" "LINT_FAILED: inbox failed lint-journey-inbox.sh" "broken inbox -> LINT_FAILED wrapper"
rm -rf "$T"

# ── RED: lint-failure pass-through (map side) ────────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-badmap.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-golden.md" "$T/INBOX.md"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "broken map -> exit 1"
assert_contains "$_out" "missing required field: priority" "broken map: underlying lint diagnostic passes through"
assert_contains "$_out" "LINT_FAILED: map failed lint-journey-map.sh" "broken map -> LINT_FAILED wrapper"
rm -rf "$T"

# ── RED: id collision skip — MAP already has JOURNEY-301 -> next gets 302 ──
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-collision.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-collision.md" "$T/INBOX.md"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "id collision skip: exit 0"
assert_contains "$_out" "PROMOTED: INBOX-1 -> JOURNEY-302" "id collision: 301 already taken, next promotion assigned 302"
assert_eq 1 "$(grep -c '^## JOURNEY-301 ' "$T/MAP.md")" "id collision: pre-existing JOURNEY-301 untouched (still exactly one)"
assert_eq 1 "$(grep -c '^## JOURNEY-302 ' "$T/MAP.md")" "id collision: new JOURNEY-302 present"
assert_exit 0 sh "$LINTMAP" "$T/MAP.md"
rm -rf "$T"

# ── RED: test: placeholder <n> substituted with the assigned numeric id (V1
# F4). A promoted SIMULATOR journey may carry `test: .../journey-<n>.spec.ts`
# as a placeholder (the simulator cannot know its future JOURNEY-<n> id at
# generation time) — the triage gate must substitute the literal token `<n>`
# with the id it assigns (e.g. 301), and ONLY that exact token; a concrete
# test value with no `<n>` token copies verbatim (control). ─────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-base.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-test-placeholder.md" "$T/INBOX.md"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "test placeholder: exit 0"
assert_contains "$_out" "PROMOTED: INBOX-1 -> JOURNEY-301" "test placeholder: INBOX-1 promoted to JOURNEY-301"
assert_contains "$_out" "PROMOTED: INBOX-2 -> JOURNEY-302" "test placeholder: INBOX-2 promoted to JOURNEY-302"
assert_eq "tests/journeys/journey-301.spec.ts" \
  "$(awk '/^## JOURNEY-301 /{f=1} f&&/^test:/{sub(/^test:[ \t]*/,""); print; f=0}' "$T/MAP.md")" \
  "V1 F4: <n> placeholder substituted with the assigned id (301)"
assert_eq "tests/journeys/journey-inbox-2.spec.ts" \
  "$(awk '/^## JOURNEY-302 /{f=1} f&&/^test:/{sub(/^test:[ \t]*/,""); print; f=0}' "$T/MAP.md")" \
  "V1 F4: concrete test value with no <n> token copies byte-identical (control)"
assert_exit 0 sh "$LINTMAP" "$T/MAP.md"
rm -rf "$T"

# ── L11 attack: promotion_status PROPOSED then a duplicate ACCEPTED line ───
# lint-journey-inbox.sh does NOT flag this duplication (it reads
# promotion_status via first-match too) — this gate must classify the
# attack entry as PROPOSED (its first-match value) and refuse to promote it,
# while an ordinary ACCEPTED entry in the SAME file still promotes normally.
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-base.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-l11.md" "$T/INBOX.md"
assert_exit 0 sh "$LINTINBOX" "$T/INBOX.md"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "L11 attack: exit 0 (the clean sibling entry still promotes)"
assert_contains "$_out" "PROMOTED: INBOX-1 -> JOURNEY-301" "L11: the clean entry (INBOX-1) promotes normally"
assert_not_contains "$_out" "INBOX-2 -> JOURNEY" "L11: the attack entry (INBOX-2) is NEVER promoted"
assert_eq 1 "$(grep -c '^## JOURNEY-' "$T/MAP.md")" "L11: exactly one map block written (only the clean entry)"
assert_eq 0 "$(grep -A2 '^## INBOX-2 ' "$T/INBOX.md" | grep -c 'promoted_as')" \
  "L11: the attack entry never gets a promoted_as stamp"
rm -rf "$T"

# ── backlog warning fires at 11 PROPOSED (spec 13.2), even on a successful
# run that also promotes something ("always, even on success"). ────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-base.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-backlog.md" "$T/INBOX.md"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "backlog warning: run still succeeds (warning only, not a failure)"
assert_contains "$_out" "WARNING: inbox backlog 11 PROPOSED entries exceeds threshold 10 (spec 13.2)" \
  "11 PROPOSED entries -> loud backlog WARNING"
rm -rf "$T"

# boundary: exactly 10 PROPOSED entries does NOT warn (threshold is > 10).
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-base.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-backlog10.md" "$T/INBOX.md"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "10 PROPOSED entries: run succeeds"
assert_not_contains "$_out" "WARNING: inbox backlog" "exactly 10 PROPOSED entries -> below threshold, no warning"
rm -rf "$T"

# ── RED: ENTRY_HEADING_INVALID — glued ACCEPTED heading (V-T5 F1, same
# class as journey-reality-intake.sh). Pre-fix fail-open, RED-proven live:
# a glued '## INBOX-1—"candidate 1"' heading (a) lints CLEAN through
# lint-journey-inbox.sh — proven by the assert_exit 0 below, which is the
# evidence that the lint is NOT the guard and the check must live in this
# gate — and (b) no-opped the promotion rewrite ('^## <id> ' needs the
# trailing space), landing a literal '## INBOX-1—...' heading in the MAP
# (invisible to journey_ids AND to lint-journey-map — a smuggled section in
# the SSOT) while still printing 'PROMOTED: INBOX-1 -> JOURNEY-301' at
# exit 0. ────────────────────────────────────────────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.triage-base.md" "$T/MAP.md"
cp "$FX/JOURNEY_INBOX.triage-glued-heading.md" "$T/INBOX.md"
assert_exit 0 sh "$LINTINBOX" "$T/INBOX.md"
_map_before="$(cat "$T/MAP.md")"; _inbox_before="$(cat "$T/INBOX.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/INBOX.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "glued ACCEPTED heading -> exit 1 (V-T5 F1)"
assert_contains "$_out" "ENTRY_HEADING_INVALID: INBOX-1" "glued ACCEPTED heading -> ENTRY_HEADING_INVALID naming the entry"
assert_not_contains "$_out" "PROMOTED:" "glued heading: all-or-nothing — the CLEAN ACCEPTED sibling (INBOX-2) is NOT partially promoted"
assert_eq "$_map_before" "$(cat "$T/MAP.md")" "glued heading: MAP byte-unchanged (no smuggled '## INBOX-' section)"
assert_eq "$_inbox_before" "$(cat "$T/INBOX.md")" "glued heading: INBOX byte-unchanged (no promoted_as stamp)"
assert_eq 0 "$(grep -c '^## INBOX-' "$T/MAP.md")" "glued heading: no literal '## INBOX-' heading ever lands in the map"
rm -rf "$T"
