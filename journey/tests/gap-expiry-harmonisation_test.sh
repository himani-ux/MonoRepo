# shellcheck shell=sh
# gap-expiry-harmonisation_test.sh — owner ruling, ITEM 2 (2026-07-14).
#
# The two coverage gates disagreed about the shape of the SAME record type:
#
#   check-persona-coverage.sh  parsed ONLY  `expires:`
#   check-journey-coverage.sh  parsed ONLY  `expiry:`
#
# so no single gap record could satisfy both. The rest of the framework had long
# since settled on `expires:` (persona/extraction/surface/mock coverage, quality
# waivers, Step 1.txt, Step 2.txt) — check-journey-coverage.sh was the outlier,
# and VIMS Audit's frozen JOURNEY_COVERAGE_GAPS.md (written to the canonical
# spelling) was rejected by it with MALFORMED_GAP.
#
# The ruling:
#   * BOTH gates accept `expires:` (CANONICAL for new records) and `expiry:`
#     (legacy synonym). Compatibility is ADDITIVE — no project is forced to
#     rewrite a record, and Audit's field is NOT renamed.
#   * neither spelling present  -> still fails (missing required field)
#   * empty / malformed dates   -> still fail under each gate's EXISTING date
#     rules (persona-coverage: YYYY-MM-DD + not-expired; journey-coverage:
#     non-blank — no new strictness is introduced by this ruling)
#   * both spellings, DIFFERENT values -> fails closed. One record cannot expire
#     on two dates, and an ambiguous record must never become a coverage credit.
#   * both spellings, SAME value -> accepted (redundant, not ambiguous).
#
# `journey-gen-check-candidate.sh` validates the same record type, so it accepts
# both spellings too — otherwise the pipeline would refuse the very gap records
# its own prompt (fanout-generator.md, now emitting canonical `expires:`) writes.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
CPC="$TESTS_DIR/../bin/check-persona-coverage.sh"
CJC="$TESTS_DIR/../bin/check-journey-coverage.sh"
CAND="$TESTS_DIR/../bin/journey-gen-check-candidate.sh"
COV="$TESTS_DIR/fixtures/gen/coverage/pass"

_gx=$(mktemp -d)
trap 'rm -rf "$_gx"' EXIT INT TERM

# ══════════════════════════════════════════════════════════════════════════════
# PART A — check-journey-coverage.sh
# The golden `pass` bundle uses the LEGACY `expiry:` spelling. We rewrite ONLY
# the expiry field and assert the verdict does not move.
# ══════════════════════════════════════════════════════════════════════════════
_jc() { # GAPS_FILE -> runs the gate against the golden pass bundle
  sh "$CJC" "$COV/PRD.md" "$COV/APP_FLOW.md" "$COV/JOURNEY_MAP.generated.md" \
            "$COV/JOURNEY_COVERAGE_MANIFEST.json" "$1" 2>&1
}

# A1. legacy `expiry:` — the fixture as it has always been. Must still pass.
_o=$(_jc "$COV/JOURNEY_COVERAGE_GAPS.md"); _e=$?
assert_eq "0" "$_e" "gx-A1: journey-coverage accepts LEGACY expiry: (unchanged fixture)"

# A2. canonical `expires:` — the same records, one field renamed.
sed 's/^expiry:/expires:/' "$COV/JOURNEY_COVERAGE_GAPS.md" > "$_gx/expires.md"
_o=$(_jc "$_gx/expires.md"); _e=$?
assert_eq "0" "$_e" "gx-A2: journey-coverage accepts CANONICAL expires:"
assert_not_contains "$_o" "MALFORMED_GAP" "gx-A2: and raises no MALFORMED_GAP"

# A3. NEITHER spelling -> still a missing required field.
sed '/^expiry:/d' "$COV/JOURNEY_COVERAGE_GAPS.md" > "$_gx/none.md"
_o=$(_jc "$_gx/none.md"); _e=$?
assert_eq "1" "$_e" "gx-A3: a record with NEITHER expires: nor expiry: still fails"
assert_contains "$_o" "MALFORMED_GAP" "gx-A3: and fails as MALFORMED_GAP"
assert_contains "$_o" "expires" "gx-A3: and reports the missing field under the CANONICAL name"

# A4. blank value -> still fails (journey-coverage's existing rule is non-blank).
sed 's/^expiry:.*/expiry:/' "$COV/JOURNEY_COVERAGE_GAPS.md" > "$_gx/blank.md"
_o=$(_jc "$_gx/blank.md"); _e=$?
assert_eq "1" "$_e" "gx-A4: a BLANK expiry: still fails"
assert_contains "$_o" "MALFORMED_GAP" "gx-A4: and fails as MALFORMED_GAP"

sed 's/^expiry:.*/expires:/' "$COV/JOURNEY_COVERAGE_GAPS.md" > "$_gx/blank2.md"
_o=$(_jc "$_gx/blank2.md"); _e=$?
assert_eq "1" "$_e" "gx-A4b: a BLANK expires: fails identically — the canonical spelling is not a loophole"

# A5. DUPLICATE CONFLICTING fields -> fails closed, and grants NO credit.
#     (Both spellings on the same record, different dates.)
awk '{ print } /^expiry:/ { print "expires:      2027-01-01" }' \
  "$COV/JOURNEY_COVERAGE_GAPS.md" > "$_gx/conflict.md"
_o=$(_jc "$_gx/conflict.md"); _e=$?
assert_eq "1" "$_e" "gx-A5: conflicting expires:/expiry: on one record FAILS CLOSED"
assert_contains "$_o" "MALFORMED_GAP" "gx-A5: and fails as MALFORMED_GAP"
assert_contains "$_o" "conflicting"   "gx-A5: and names the conflict"
# The anti-false-green half: a conflicting record must not silently still count
# as a coverage credit. FEAT-003/AFJ-003 are ONLY covered by their gap records,
# so if the conflict were tolerated the run would be green; it must instead
# surface the now-uncovered anchors.
assert_contains "$_o" "COVERAGE_GAP" "gx-A5: a conflicting record grants NO coverage credit"

# A6. duplicate but AGREEING fields -> redundant, not ambiguous. Accepted.
awk '{ print } /^expiry:/ { print "expires:      2026-09-01" }' \
  "$COV/JOURNEY_COVERAGE_GAPS.md" > "$_gx/agree.md"
_o=$(_jc "$_gx/agree.md"); _e=$?
assert_eq "0" "$_e" "gx-A6: both spellings with the SAME date is redundant, not ambiguous — accepted"

# A7. the harmonisation must not disarm the gate: a MISSING owner is still
#     MALFORMED_GAP even when the expiry field is perfectly canonical.
#     (awk, not `sed 0,/re/` — that address form is a GNU extension and is
#     silently a no-op on the BSD sed this framework must run under.)
sed 's/^expiry:/expires:/' "$COV/JOURNEY_COVERAGE_GAPS.md" \
  | awk '/^owner:/ && !done { done = 1; next } { print }' > "$_gx/noowner.md"
_o=$(_jc "$_gx/noowner.md"); _e=$?
assert_eq "1" "$_e" "gx-A7: a missing owner: still fails under the canonical spelling"
assert_contains "$_o" "MALFORMED_GAP" "gx-A7: and still names MALFORMED_GAP"

# ══════════════════════════════════════════════════════════════════════════════
# PART B — check-persona-coverage.sh
# Its fixture uses the CANONICAL `expires:`. We rewrite to the legacy spelling
# and assert the verdict does not move.
# ══════════════════════════════════════════════════════════════════════════════
# Same fixture wiring as persona-gates_test.sh — the PRD and SSOT live under
# fixtures/gen, the persona map and gaps under fixtures/persona.
PFX="$TESTS_DIR/fixtures/persona"
GENDIR="$TESTS_DIR/fixtures/gen"
_pc() { # GAPS_FILE
  sh "$CPC" "$GENDIR/PRD.md" "$GENDIR/SSOT.md" "$PFX/JOURNEY_MAP.persona.md" "$1" 2>&1
}

# B1. canonical `expires:` — the fixture as it has always been.
_o=$(_pc "$PFX/PERSONA_COVERAGE_GAPS.md"); _e=$?
assert_eq "0" "$_e" "gx-B1: persona-coverage accepts CANONICAL expires: (unchanged fixture)"

# B2. legacy `expiry:` — the same record, one field renamed. Previously this
#     was rejected outright (the gate could not see the field at all).
sed 's/^expires:/expiry:/' "$PFX/PERSONA_COVERAGE_GAPS.md" > "$_gx/p-legacy.md"
_o=$(_pc "$_gx/p-legacy.md"); _e=$?
assert_eq "0" "$_e" "gx-B2: persona-coverage accepts LEGACY expiry:"
assert_not_contains "$_o" "GAP_MALFORMED" "gx-B2: and raises no GAP_MALFORMED"

# B3. NEITHER spelling -> still fails.
sed '/^expires:/d' "$PFX/PERSONA_COVERAGE_GAPS.md" > "$_gx/p-none.md"
_o=$(_pc "$_gx/p-none.md"); _e=$?
assert_eq "1" "$_e" "gx-B3: a record with NEITHER expires: nor expiry: still fails"
assert_contains "$_o" "GAP_MALFORMED" "gx-B3: and fails as GAP_MALFORMED"

# B4. MALFORMED date -> still fails the existing YYYY-MM-DD rule, under BOTH
#     spellings. The synonym must not become a way to smuggle a bad date in.
sed 's|^expires:.*|expires: 2026-1-2|' "$PFX/PERSONA_COVERAGE_GAPS.md" > "$_gx/p-bad1.md"
_o=$(_pc "$_gx/p-bad1.md"); _e=$?
assert_eq "1" "$_e" "gx-B4a: malformed date under expires: still fails"
assert_contains "$_o" "not YYYY-MM-DD" "gx-B4a: and names the format rule"

sed 's|^expires:.*|expiry: 2026-1-2|' "$PFX/PERSONA_COVERAGE_GAPS.md" > "$_gx/p-bad2.md"
_o=$(_pc "$_gx/p-bad2.md"); _e=$?
assert_eq "1" "$_e" "gx-B4b: malformed date under LEGACY expiry: fails identically"
assert_contains "$_o" "not YYYY-MM-DD" "gx-B4b: and names the format rule"

# B5. EXPIRED date -> still not a coverage credit, under BOTH spellings.
sed 's|^expires:.*|expires: 2020-01-01|' "$PFX/PERSONA_COVERAGE_GAPS.md" > "$_gx/p-exp1.md"
_o=$(_pc "$_gx/p-exp1.md"); _e=$?
assert_eq "1" "$_e" "gx-B5a: an EXPIRED gap under expires: is still no credit"
assert_contains "$_o" "GAP_EXPIRED" "gx-B5a: and fails as GAP_EXPIRED"

sed 's|^expires:.*|expiry: 2020-01-01|' "$PFX/PERSONA_COVERAGE_GAPS.md" > "$_gx/p-exp2.md"
_o=$(_pc "$_gx/p-exp2.md"); _e=$?
assert_eq "1" "$_e" "gx-B5b: an EXPIRED gap under LEGACY expiry: fails identically"
assert_contains "$_o" "GAP_EXPIRED" "gx-B5b: and fails as GAP_EXPIRED"

# B6. DUPLICATE CONFLICTING fields -> fails closed, no credit.
awk '{ print } /^expires:/ { print "expiry: 2027-01-01" }' \
  "$PFX/PERSONA_COVERAGE_GAPS.md" > "$_gx/p-conflict.md"
_o=$(_pc "$_gx/p-conflict.md"); _e=$?
assert_eq "1" "$_e" "gx-B6: conflicting expires:/expiry: on one record FAILS CLOSED"
assert_contains "$_o" "conflicting" "gx-B6: and names the conflict"
assert_contains "$_o" "PERSONA_COVERAGE_GAP" "gx-B6: a conflicting record grants NO coverage credit"

# B7. duplicate but AGREEING fields -> accepted.
_agree=$(grep -m1 '^expires:' "$PFX/PERSONA_COVERAGE_GAPS.md" | sed 's/^expires:[[:space:]]*//')
awk -v d="$_agree" '{ print } /^expires:/ { print "expiry: " d }' \
  "$PFX/PERSONA_COVERAGE_GAPS.md" > "$_gx/p-agree.md"
_o=$(_pc "$_gx/p-agree.md"); _e=$?
assert_eq "0" "$_e" "gx-B7: both spellings with the SAME date is accepted"

# ══════════════════════════════════════════════════════════════════════════════
# PART C — journey-gen-check-candidate.sh reads the same record type.
# If it still demanded `expiry:`, a canonical `expires:` gap record would pass
# the coverage gate and be REJECTED by the candidate check — the pipeline would
# refuse the gap records its own prompt now emits.
# ══════════════════════════════════════════════════════════════════════════════
# A pure structured-gap candidate (no journey block) — the shape the candidate
# check already blesses (cc-9). A candidate must NOT carry a '## JOURNEY-<n>'
# heading: ids are assigned by the merge, never by the generator.
_mk_cand() { # FILE EXPIRY_LINE
  {
    printf 'source_id:    FEAT-004\n'
    printf 'source_type:  FEAT\n'
    printf 'reason:       bundle has no acceptance_criteria side; no faithful oracle derivable\n'
    printf 'owner:        UNASSIGNED — human triage required\n'
    printf '%s\n' "$2"
    printf 'reviewer:     PENDING-HUMAN\n'
  } > "$1"
}
_mk_cand "$_gx/cand-legacy.md"  'expiry:       2026-12-01'
_mk_cand "$_gx/cand-canon.md"   'expires:      2026-12-01'
_mk_cand "$_gx/cand-missing.md" 'note:         no expiry field at all'

_o=$(sh "$CAND" "$_gx/cand-legacy.md" 2>&1); _e=$?
assert_eq "0" "$_e" "gx-C1: candidate check accepts LEGACY expiry:"
_o=$(sh "$CAND" "$_gx/cand-canon.md" 2>&1); _e=$?
assert_eq "0" "$_e" "gx-C2: candidate check accepts CANONICAL expires: (the spelling its prompt now emits)"
_o=$(sh "$CAND" "$_gx/cand-missing.md" 2>&1); _e=$?
assert_eq "1" "$_e" "gx-C3: candidate check still fails a gap record with NO expiry field"
assert_contains "$_o" "MALFORMED_GAP" "gx-C3: and names MALFORMED_GAP"

# ══════════════════════════════════════════════════════════════════════════════
# PART D — the shipped template emits the CANONICAL spelling (condition 8).
# ══════════════════════════════════════════════════════════════════════════════
_fg="$TESTS_DIR/../gen/prompts/fanout-generator.md"
assert_contains "$(cat "$_fg")" "expires:" "gx-D1: fanout-generator template emits canonical expires:"
_n=$(grep -c '^expiry:' "$_fg" 2>/dev/null || true)
assert_eq "0" "${_n:-0}" "gx-D2: and no longer emits a bare 'expiry:' gap field"
