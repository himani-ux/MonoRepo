#!/bin/sh
# journey-reality-intake_test.sh — TDD proofs for journey-reality-intake.sh (DC-5)
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
GATE="$TESTS_DIR/../bin/journey-reality-intake.sh"
LINTMAP="$TESTS_DIR/../bin/lint-journey-map.sh"
FX="$TESTS_DIR/fixtures/reality"

_sha() { shasum -a 256 "$1" | awk '{print $1}'; }

# ── --approve refuses BEFORE any other work (house rule 7) ─────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-golden.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_entry_before_sha="$(_sha "$T/ENTRY.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "no --approve -> exit 1"
assert_contains "$_out" "APPROVE_REQUIRED" "no --approve -> APPROVE_REQUIRED, refuses before any other work"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "APPROVE-refusal: MAP byte-unchanged (sha256)"
assert_eq "$_entry_before_sha" "$(_sha "$T/ENTRY.md")" "APPROVE-refusal: ENTRY_FILE byte-unchanged (sha256)"
# even with a nonexistent MAP/ENTRY_FILE, missing --approve refuses first,
# before any file-readability check — nothing is even attempted to be read.
_out="$(sh "$GATE" "$T/does-not-exist.md" "$T/also-missing.md" 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "no --approve, even with missing files -> still exit 1 (not 2) — approve gates before file checks"
assert_contains "$_out" "APPROVE_REQUIRED" "no --approve, missing files -> still APPROVE_REQUIRED, not a file-not-found message"
rm -rf "$T"

# zero args at all -> still APPROVE_REQUIRED (exit 1, not a usage exit 2)
assert_exit 1 sh "$GATE"

# ── usage / missing file: exit 2 (only once --approve is present — without
# it, APPROVE_REQUIRED fires first regardless of arg count; already proven
# above) ─────────────────────────────────────────────────────────────────────
assert_exit 2 sh "$GATE" --approve
assert_exit 2 sh "$GATE" a --approve
assert_exit 2 sh "$GATE" "$FX/does-not-exist.md" "$FX/ENTRY.reality-golden.md" --approve
assert_exit 2 sh "$GATE" "$FX/JOURNEY_MAP.reality-base.md" "$FX/does-not-exist.md" --approve

# ── golden intake: fresh base map + one REALITY entry -> id 401 ────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-golden.md" "$T/ENTRY.md"
_entry_before_sha="$(_sha "$T/ENTRY.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "golden intake: exit 0"
assert_contains "$_out" 'INTAKE: JOURNEY-401 — "Reality regression: checkout total drifts after coupon retry"' \
  "golden: success line names the assigned id and title"
assert_eq 1 "$(grep -c '^## JOURNEY-' "$T/MAP.md")" "golden: exactly one map block written"
assert_eq 1 "$(grep -c '^## JOURNEY-401 ' "$T/MAP.md")" "golden: JOURNEY-401 present"
assert_exit 0 sh "$LINTMAP" "$T/MAP.md"
assert_eq 1 "$(awk '/^## JOURNEY-401 /{f=1} f&&/^origin:/{print;f=0}' "$T/MAP.md" | grep -c 'REALITY')" \
  "golden: promoted block carries origin: REALITY (from the entry, not forced)"
assert_eq "tests/journeys/journey-701.spec.ts" \
  "$(awk '/^## JOURNEY-401 /{f=1} f&&/^test:/{sub(/^test:[ \t]*/,""); print; f=0}' "$T/MAP.md")" \
  "golden: concrete test value with no <n> token copies byte-identical (control)"
assert_eq "$_entry_before_sha" "$(_sha "$T/ENTRY.md")" "golden: ENTRY_FILE itself is never modified"
rm -rf "$T"

# ── golden id 401, then a SECOND intake run on the just-mutated map gets 402
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-golden.md" "$T/E1.md"
cp "$FX/ENTRY.reality-second.md" "$T/E2.md"
_out1="$(sh "$GATE" "$T/MAP.md" "$T/E1.md" --approve 2>&1)"; _rc1=$?
assert_eq 0 "$_rc1" "first of two sequential runs: exit 0"
assert_contains "$_out1" "INTAKE: JOURNEY-401" "first sequential run assigns 401"
_out2="$(sh "$GATE" "$T/MAP.md" "$T/E2.md" --approve 2>&1)"; _rc2=$?
assert_eq 0 "$_rc2" "second of two sequential runs: exit 0"
assert_contains "$_out2" 'INTAKE: JOURNEY-402 — "Reality regression: export CSV truncates rows over 10k"' \
  "second sequential run (on the already-mutated map) assigns 402"
assert_eq 2 "$(grep -c '^## JOURNEY-' "$T/MAP.md")" "both blocks present after two sequential runs"
assert_eq 1 "$(grep -c '^## JOURNEY-401 ' "$T/MAP.md")" "401 still present after the second run"
assert_eq 1 "$(grep -c '^## JOURNEY-402 ' "$T/MAP.md")" "402 present after the second run"
assert_exit 0 sh "$LINTMAP" "$T/MAP.md"
rm -rf "$T"

# ── id collision skip: MAP already HAS JOURNEY-401 (dedicated fixture,
# unrelated content) -> a new entry's id assignment skips it and lands 402 ──
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-with401.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-golden.md" "$T/ENTRY.md"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "id collision skip: exit 0"
assert_contains "$_out" "INTAKE: JOURNEY-402" "id collision: 401 already taken, next intake assigned 402"
assert_eq 1 "$(grep -c '^## JOURNEY-401 ' "$T/MAP.md")" "id collision: pre-existing JOURNEY-401 untouched (still exactly one)"
assert_eq 1 "$(grep -c '^## JOURNEY-402 ' "$T/MAP.md")" "id collision: new JOURNEY-402 present"
assert_exit 0 sh "$LINTMAP" "$T/MAP.md"
rm -rf "$T"

# ── RED: NO_ENTRY_BLOCK (anti-vacuous) ──────────────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-noblock.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "zero blocks -> exit 1"
assert_contains "$_out" "NO_ENTRY_BLOCK" "zero blocks -> NO_ENTRY_BLOCK"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "NO_ENTRY_BLOCK: MAP byte-unchanged (sha256)"
rm -rf "$T"

# ── RED: MULTIPLE_BLOCKS ────────────────────────────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-multiblock.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "two blocks -> exit 1"
assert_contains "$_out" "MULTIPLE_BLOCKS" "two blocks -> MULTIPLE_BLOCKS"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "MULTIPLE_BLOCKS: MAP byte-unchanged (sha256)"
rm -rf "$T"

# ── RED: ORIGIN_NOT_REALITY ─────────────────────────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-origin-wrong.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "origin != REALITY -> exit 1"
assert_contains "$_out" "ORIGIN_NOT_REALITY" "origin != REALITY -> ORIGIN_NOT_REALITY"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "ORIGIN_NOT_REALITY: MAP byte-unchanged (sha256)"
rm -rf "$T"

# ── RED: AUTHOR_STATUS_NOT_UNWRITTEN ────────────────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-authorstatus-wrong.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "author_status != UNWRITTEN -> exit 1"
assert_contains "$_out" "AUTHOR_STATUS_NOT_UNWRITTEN" "author_status != UNWRITTEN -> AUTHOR_STATUS_NOT_UNWRITTEN"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "AUTHOR_STATUS_NOT_UNWRITTEN: MAP byte-unchanged (sha256)"
rm -rf "$T"

# ── RED: EVIDENCE_EMPTY — blank value ───────────────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-evidence-blank.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "blank evidence -> exit 1"
assert_contains "$_out" "EVIDENCE_EMPTY" "blank evidence -> EVIDENCE_EMPTY"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "EVIDENCE_EMPTY (blank): MAP byte-unchanged (sha256)"
rm -rf "$T"

# ── RED: EVIDENCE_EMPTY — literal [] value ──────────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-evidence-brackets.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "literal [] evidence -> exit 1"
assert_contains "$_out" "EVIDENCE_EMPTY" "literal [] evidence -> EVIDENCE_EMPTY (a non-empty-looking but vacuous value is still refused)"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "EVIDENCE_EMPTY (literal []): MAP byte-unchanged (sha256)"
rm -rf "$T"

# ── fail-slow accumulation: an entry violating BOTH origin and evidence
# rules reports BOTH codes in one run (never short-circuits on the first). ──
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-failslow.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "origin+evidence both wrong -> exit 1"
assert_contains "$_out" "ORIGIN_NOT_REALITY" "fail-slow: ORIGIN_NOT_REALITY present"
assert_contains "$_out" "EVIDENCE_EMPTY" "fail-slow: EVIDENCE_EMPTY ALSO present in the SAME run"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "fail-slow: MAP byte-unchanged (sha256)"
rm -rf "$T"

# ── RED: DUPLICATE_JOURNEY vs an existing map journey (normalized
# covers+oracle collide, despite differing whitespace) ─────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-dupbase.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-dup.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "duplicate vs map -> exit 1"
assert_contains "$_out" "DUPLICATE_JOURNEY: entry matches JOURNEY-500" \
  "normalized covers+oracle match against an existing map journey -> DUPLICATE_JOURNEY"
assert_contains "$_out" "attach this regression to the existing journey instead of minting a new one" \
  "DUPLICATE_JOURNEY message directs the operator to the existing journey"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "DUPLICATE_JOURNEY: MAP byte-unchanged (sha256, all-or-nothing)"
rm -rf "$T"

# ── RED: LINT_FAILED — entry passes ALL intake-specific checks (origin,
# author_status, evidence) but violates map lint via a bad priority enum. ──
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-badpriority.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "bad priority enum -> exit 1"
assert_contains "$_out" "invalid priority value: SUPER" "bad priority: underlying lint-journey-map.sh diagnostic passes through"
assert_contains "$_out" "LINT_FAILED: promoted map failed lint-journey-map.sh self-check" "bad priority -> LINT_FAILED wrapper"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "bad priority: MAP byte-unchanged (sha256)"
rm -rf "$T"

# ── RED: LINT_FAILED — entry passes ALL intake-specific checks but smuggles
# a runtime-truth field (ci_status). This gate does NOT run its own direct
# regex for runtime-truth fields (see the header comment "composition, not
# a duplicated direct check") — it relies entirely on lint-journey-map.sh's
# Check 3 firing over the temp map's newly appended block. This test proves
# that composition actually catches it, independent of the intake-specific
# checks. ────────────────────────────────────────────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-runtimesmuggle.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "runtime-key smuggle -> exit 1"
assert_not_contains "$_out" "ORIGIN_NOT_REALITY" "runtime-key smuggle: intake-specific checks all pass (origin is REALITY)"
assert_not_contains "$_out" "EVIDENCE_EMPTY" "runtime-key smuggle: intake-specific checks all pass (evidence is non-empty)"
assert_contains "$_out" "runtime-truth field found in block" "runtime-key smuggle: underlying lint-journey-map.sh Check 3 diagnostic passes through"
assert_contains "$_out" "LINT_FAILED: promoted map failed lint-journey-map.sh self-check" "runtime-key smuggle -> LINT_FAILED wrapper (composition, not a bespoke code)"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "runtime-key smuggle: MAP byte-unchanged (sha256)"
rm -rf "$T"

# ── RED: test: <n> placeholder substituted with the assigned numeric id
# (mirrors journey-inbox-triage.sh's V1 F4, commit 4b08dcb). ONLY the
# literal token `<n>` is substituted — everything else in the entry copies
# through unchanged. ──────────────────────────────────────────────────────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-testplaceholder.md" "$T/ENTRY.md"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "test placeholder: exit 0"
assert_contains "$_out" "INTAKE: JOURNEY-401" "test placeholder: assigned JOURNEY-401"
assert_eq "tests/journeys/journey-401.spec.ts" \
  "$(awk '/^## JOURNEY-401 /{f=1} f&&/^test:/{sub(/^test:[ \t]*/,""); print; f=0}' "$T/MAP.md")" \
  "<n> placeholder substituted with the assigned id (401)"
assert_exit 0 sh "$LINTMAP" "$T/MAP.md"
rm -rf "$T"

# ── RED: ENTRY_HEADING_INVALID — glued em-dash heading (V-T5 F1) ────────────
# Pre-fix fail-open: journey-lib reads blocks with '^## <id>([^0-9]|$)' but
# the promotion rewrite substitutes on '^## <id> ' (trailing space). A glued
# heading '## JOURNEY-999—"title"' passed every read/field/lint check, the
# rewrite silently no-opped, the block landed in the map UNDER THE
# PLACEHOLDER ID 999 (JOURNEY-401 never appeared), and the gate printed an
# EMPTY 'INTAKE: ' at exit 0 — a fail-open SSOT write. The heading grammar
# must now fail closed BEFORE any write.
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-glued-emdash.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "glued em-dash heading -> exit 1 (V-T5 F1)"
assert_contains "$_out" "ENTRY_HEADING_INVALID" "glued em-dash heading -> ENTRY_HEADING_INVALID"
assert_not_contains "$_out" "INTAKE:" "glued em-dash heading: no success line, empty or otherwise"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "glued em-dash heading: MAP byte-unchanged (sha256 — the placeholder-id block never lands)"
assert_eq 0 "$(grep -c '^## JOURNEY-999' "$T/MAP.md")" "glued em-dash heading: JOURNEY-999 never appears in the map"
rm -rf "$T"

# ── RED: ENTRY_HEADING_INVALID — glued plain hyphen heading (V-T5 F1) ──────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-glued-hyphen.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "glued plain-hyphen heading -> exit 1 (V-T5 F1)"
assert_contains "$_out" "ENTRY_HEADING_INVALID" "glued plain-hyphen heading -> ENTRY_HEADING_INVALID (an ASCII hyphen is not the canonical spaced em-dash either)"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "glued plain-hyphen heading: MAP byte-unchanged (sha256)"
rm -rf "$T"

# ── fail-slow: glued heading + wrong origin -> BOTH codes in one run ────────
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-glued-failslow.md" "$T/ENTRY.md"
_map_before_sha="$(_sha "$T/MAP.md")"
_out="$(sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "glued heading + wrong origin -> exit 1"
assert_contains "$_out" "ENTRY_HEADING_INVALID" "fail-slow: ENTRY_HEADING_INVALID present"
assert_contains "$_out" "ORIGIN_NOT_REALITY" "fail-slow: ORIGIN_NOT_REALITY ALSO present in the SAME run (heading check accumulates, never short-circuits)"
assert_eq "$_map_before_sha" "$(_sha "$T/MAP.md")" "fail-slow (heading+origin): MAP byte-unchanged (sha256)"
rm -rf "$T"

# ── never touches JOURNEY_INBOX.md or any other file: sanity check that a
# stray JOURNEY_INBOX.md sitting next to MAP is untouched by a golden run. ──
T=$(mktemp -d)
cp "$FX/JOURNEY_MAP.reality-base.md" "$T/MAP.md"
cp "$FX/ENTRY.reality-golden.md" "$T/ENTRY.md"
printf '# JOURNEY-INBOX (sentinel, must survive untouched)\n' > "$T/JOURNEY_INBOX.md"
_inbox_before_sha="$(_sha "$T/JOURNEY_INBOX.md")"
assert_exit 0 sh "$GATE" "$T/MAP.md" "$T/ENTRY.md" --approve
assert_eq "$_inbox_before_sha" "$(_sha "$T/JOURNEY_INBOX.md")" "golden run never touches a sibling JOURNEY_INBOX.md"
rm -rf "$T"
