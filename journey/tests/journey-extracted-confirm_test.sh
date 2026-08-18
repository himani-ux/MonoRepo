#!/bin/sh
# shellcheck shell=sh
# journey-extracted-confirm_test.sh — journey-extracted-confirm.sh (task E5,
# spec §4.3/§14): the human confirmation gate promoting CONFIRMED EXTRACTED
# entries into JOURNEY-5xx map blocks. Fixture idiom mirrors
# journey-extracted-stage_test.sh (golden fixtures, sed-stamped
# manifest_sha256, one-thing-different RED mutations) — no git repo is
# needed here (unlike E4's own suite) because this gate composes
# check-extraction-coverage.sh, never check-extracted-provenance.sh.
. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$TESTS_DIR/../bin"
GATE="$BIN/journey-extracted-confirm.sh"
LIB="$TESTS_DIR/../lib/journey-lib.sh"
FX="$TESTS_DIR/fixtures/extracted/confirm"
GOLD_MAP="$FX/MAP.golden.md"
GOLD_EXT="$FX/EXTRACTED.golden.md"
GOLD_MF="$FX/MANIFEST.golden.md"

_jec_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}
_sha_jec() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }
_field_jec() { ( JOURNEY_EXTRACTED="$2"; export JOURNEY_EXTRACTED; # shellcheck disable=SC1090
  . "$LIB"; extracted_field "$1" "$3" ); } # ID FILE KEY
_block_jec() { ( JOURNEY_EXTRACTED="$2"; export JOURNEY_EXTRACTED; # shellcheck disable=SC1090
  . "$LIB"; extracted_block "$1" ); } # ID FILE
_mfield_jec() { ( JOURNEY_MAP="$2"; export JOURNEY_MAP; # shellcheck disable=SC1090
  . "$LIB"; journey_field "$1" "$3" ); } # ID FILE KEY
_mblock_jec() { ( JOURNEY_MAP="$2"; export JOURNEY_MAP; # shellcheck disable=SC1090
  . "$LIB"; journey_block "$1" ); } # ID FILE

_jt="$(mktemp -d)"

_mf_block_sha() { # MANIFEST_PATH -- IDENTICAL BEGIN..END-inclusive recipe
  awk '/^EXTRACTION-MANIFEST BEGIN$/{f=1} f{print} /^EXTRACTION-MANIFEST END$/{exit}' "$1" \
    | { if command -v sha256sum >/dev/null 2>&1; then sha256sum; else shasum -a 256; fi; } \
    | awk '{print $1}'
}
_MF_SHA="$(_mf_block_sha "$GOLD_MF")"

# _jec_setup DIR -- populates DIR/MAP.md, DIR/EXTRACTED.md, DIR/MANIFEST.md
# from the golden fixtures, EXTRACTED's manifest_sha256 correctly stamped.
_jec_setup() {
  mkdir -p "$1"
  cp "$GOLD_MAP" "$1/MAP.md"
  cp "$GOLD_MF" "$1/MANIFEST.md"
  sed "s/^manifest_sha256:.*/manifest_sha256:   $_MF_SHA/" "$GOLD_EXT" > "$1/EXTRACTED.md"
}

# _jec_setup_with_mf DIR MF_CONTENT_FILE -- like _jec_setup, but MANIFEST.md
# is MF_CONTENT_FILE's content, with EXTRACTED's manifest_sha256 correctly
# (re-)stamped against IT (never the golden manifest's stale hash).
_jec_setup_with_mf() {
  mkdir -p "$1"
  cp "$GOLD_MAP" "$1/MAP.md"
  cp "$2" "$1/MANIFEST.md"
  _sha="$(_mf_block_sha "$1/MANIFEST.md")"
  sed "s/^manifest_sha256:.*/manifest_sha256:   $_sha/" "$GOLD_EXT" > "$1/EXTRACTED.md"
}

# a manifest variant declaring ONLY FEAT-100 (no FEAT-200) -- for isolated
# scenarios whose EXTRACTED file deliberately carries just ONE promotable
# candidate and must not trip MISSING_EXTRACTION for FEAT-200.
MF_SINGLE_FEAT="$_jt/MANIFEST-single-feat.md"
mkdir -p "$_jt"
cat > "$MF_SINGLE_FEAT" << SFEOF
# MANIFEST — single-feat variant (isolated confirm test scenarios)

EXTRACTION-MANIFEST BEGIN
manifest_version: 1
extraction_commit: 1234567890123456789012345678901234567890
feat: FEAT-100 | behaviors=2 | states_filled=4 | grade_counts=C:2,I:0,G:0,X:0
EXTRACTION-MANIFEST END
SFEOF

# _jec_red_case DIR CODE LABEL -- runs the gate on DIR's three files,
# asserts non-zero exit, the code name present, and MAP+EXTRACTED
# byte-unchanged (all-or-nothing, sha256).
_jec_red_case() {
  _d="$1"; _code="$2"; _label="$3"
  _msha="$(_sha_jec "$_d/MAP.md")"
  _esha="$(_sha_jec "$_d/EXTRACTED.md")"
  _out="$(sh "$GATE" "$_d/MAP.md" "$_d/EXTRACTED.md" "$_d/MANIFEST.md" --approve 2>&1)"; _rc=$?
  _jec_nonzero "$_rc" "$_label: exit non-zero"
  assert_contains "$_out" "$_code" "$_label: names $_code"
  assert_eq "$_msha" "$(_sha_jec "$_d/MAP.md")" "$_label: MAP byte-unchanged"
  assert_eq "$_esha" "$(_sha_jec "$_d/EXTRACTED.md")" "$_label: EXTRACTED byte-unchanged"
}

# ═══════════════════════════════════════════════════════════════════════
# Usage / missing-arg (exit 2) -- only once --approve is present (without
# it, APPROVE_REQUIRED fires first regardless of arg count; proven below).
# ═══════════════════════════════════════════════════════════════════════

assert_exit 2 sh "$GATE" --approve
assert_exit 2 sh "$GATE" a b --approve
assert_exit 2 sh "$GATE" a b c d e --approve
d="$_jt/usage1"; _jec_setup "$d"
assert_exit 2 sh "$GATE" "$_jt/does-not-exist.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve
assert_exit 2 sh "$GATE" "$d/MAP.md" "$_jt/does-not-exist.md" "$d/MANIFEST.md" --approve
assert_exit 2 sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" "$_jt/does-not-exist-gaps.md" --approve

# ═══════════════════════════════════════════════════════════════════════
# Approve-refusal: --approve absent refuses BEFORE any other work — nothing
# is read, not even a file-existence check (house rule 7). Proven with
# THREE nonexistent paths: if any file check ran first, it would report a
# "not found" message instead of / before APPROVE_REQUIRED.
# ═══════════════════════════════════════════════════════════════════════

_out="$(sh "$GATE" 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "no --approve, no args at all -> exit 1"
assert_contains "$_out" "APPROVE_REQUIRED" "no --approve, no args -> APPROVE_REQUIRED"

_out="$(sh "$GATE" "$_jt/nope1.md" "$_jt/nope2.md" "$_jt/nope3.md" 2>&1)"; _rc=$?
assert_eq 1 "$_rc" "no --approve, three nonexistent paths -> still exit 1 (not 2)"
assert_contains "$_out" "APPROVE_REQUIRED" "no --approve, nonexistent paths -> still APPROVE_REQUIRED"
assert_not_contains "$_out" "not found" "no --approve -> no file-not-found message leaks (nothing was even checked)"
[ ! -d "$_jt/nope1.md" ]; assert_eq 0 $? "no --approve -> nothing created either"

# ═══════════════════════════════════════════════════════════════════════
# Golden promote: 2 CONFIRMED [C] entries + 1 PENDING + 1 REJECTED ->
# JOURNEY-501/502
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/golden"; _jec_setup "$d"
_before_e12="$(_block_jec EXTRACTED-12 "$d/EXTRACTED.md")"
_before_e13="$(_block_jec EXTRACTED-13 "$d/EXTRACTED.md")"

_out="$(sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "golden promote: exit 0"
assert_contains "$_out" "PROMOTED: EXTRACTED-10 -> JOURNEY-501" "golden promote: EXTRACTED-10 -> JOURNEY-501"
assert_contains "$_out" "PROMOTED: EXTRACTED-11 -> JOURNEY-502" "golden promote: EXTRACTED-11 -> JOURNEY-502"

assert_exit 0 sh "$BIN/lint-journey-map.sh" "$d/MAP.md"
assert_exit 0 sh "$BIN/lint-journey-extracted.sh" "$d/EXTRACTED.md"

# forced fields
assert_eq "EXTRACTED" "$(_mfield_jec JOURNEY-501 "$d/MAP.md" origin)" "golden promote: origin forced EXTRACTED"
assert_eq "UNWRITTEN" "$(_mfield_jec JOURNEY-501 "$d/MAP.md" author_status)" "golden promote: author_status forced UNWRITTEN"
assert_eq "[]" "$(_mfield_jec JOURNEY-501 "$d/MAP.md" evidence)" "golden promote: evidence forced [] (Lock 4)"
# injected fields (L25) -- staging never carries these
assert_eq "[]" "$(_mfield_jec JOURNEY-501 "$d/MAP.md" data_fixtures)" "golden promote: data_fixtures injected []"
assert_eq "[]" "$(_mfield_jec JOURNEY-501 "$d/MAP.md" exemptions)" "golden promote: exemptions injected []"
assert_eq "[]" "$(_mfield_jec JOURNEY-502 "$d/MAP.md" data_fixtures)" "golden promote: data_fixtures injected [] (2nd entry)"
assert_eq "[]" "$(_mfield_jec JOURNEY-502 "$d/MAP.md" exemptions)" "golden promote: exemptions injected [] (2nd entry)"
# <n> substitution
assert_eq "tests/journeys/journey-501.spec.ts" "$(_mfield_jec JOURNEY-501 "$d/MAP.md" test)" "golden promote: <n> substituted with 501"
assert_eq "tests/journeys/journey-502.spec.ts" "$(_mfield_jec JOURNEY-502 "$d/MAP.md" test)" "golden promote: <n> substituted with 502"
# copied-unchanged fields
assert_eq "FEAT-100" "$(_mfield_jec JOURNEY-501 "$d/MAP.md" covers)" "golden promote: covers copied unchanged"
assert_eq "the first-candidate success signal is observed" "$(_mfield_jec JOURNEY-501 "$d/MAP.md" oracle)" "golden promote: oracle copied unchanged"
# extraction_provenance stamp (Q1)
_ep501="$(_mfield_jec JOURNEY-501 "$d/MAP.md" extraction_provenance)"
assert_contains "$_ep501" "EXTRACTED-10 commit:1234567890123456789012345678901234567890 confirmed:" "golden promote: extraction_provenance names id+commit"
printf '%s\n' "$_ep501" | grep -qE 'confirmed:[0-9a-f]{12}$'
assert_eq 0 $? "golden promote: extraction_provenance confirmed: is exactly 12 hex chars"

# promoted_as stamped on staging
assert_eq "JOURNEY-501" "$(_field_jec EXTRACTED-10 "$d/EXTRACTED.md" promoted_as)" "golden promote: EXTRACTED-10 stamped promoted_as JOURNEY-501"
assert_eq "JOURNEY-502" "$(_field_jec EXTRACTED-11 "$d/EXTRACTED.md" promoted_as)" "golden promote: EXTRACTED-11 stamped promoted_as JOURNEY-502"

# PENDING/REJECTED entries byte-unchanged
assert_eq "$_before_e12" "$(_block_jec EXTRACTED-12 "$d/EXTRACTED.md")" "golden promote: PENDING entry EXTRACTED-12 byte-unchanged"
assert_eq "$_before_e13" "$(_block_jec EXTRACTED-13 "$d/EXTRACTED.md")" "golden promote: REJECTED entry EXTRACTED-13 byte-unchanged"

# ═══════════════════════════════════════════════════════════════════════
# L25 injection proof: the STAGING file carries neither data_fixtures nor
# exemptions at all -- the map lint passing above is proof the confirm
# gate injects them, not that they were merely copied through.
# ═══════════════════════════════════════════════════════════════════════

assert_not_contains "$(cat "$GOLD_EXT")" "data_fixtures" "L25: staging fixture carries no data_fixtures field at all"
assert_not_contains "$(cat "$GOLD_EXT")" "exemptions" "L25: staging fixture carries no exemptions field at all"

# ═══════════════════════════════════════════════════════════════════════
# <n> substitution vs concrete-path control: a CONFIRMED entry whose test:
# has NO <n> token copies through byte-identical.
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/concrete-path"; mkdir -p "$d"
cp "$GOLD_MAP" "$d/MAP.md"
cp "$MF_SINGLE_FEAT" "$d/MANIFEST.md"
_cp_sha="$(_mf_block_sha "$d/MANIFEST.md")"
cat > "$d/EXTRACTED.md" << CPEOF
# JOURNEY-EXTRACTED
extraction_commit: 1234567890123456789012345678901234567890
manifest_sha256:   $_cp_sha

## EXTRACTED-30 — "A concrete test-path candidate"
needs_human_confirm: true
confirmation_status: CONFIRMED
grade:               [C]
origin:              EXTRACTED
persona:             ops user
goal:                do the concrete-path thing
priority:            P2
covers:              FEAT-100
flows:               []
oracle_surface:      UI
negative_states:     concrete_error
steps:
  1. do the concrete-path thing
  2. trigger concrete_error
oracle:              a wholly distinct concrete-path oracle signal never used elsewhere
evidence:            []
test:                tests/journeys/custom-fixed-path.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/concrete.ts:1 — "export function concrete() {}"
CPEOF
_out="$(sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "concrete-path control: exit 0"
assert_contains "$_out" "PROMOTED: EXTRACTED-30 -> JOURNEY-501" "concrete-path control: promotes to JOURNEY-501 (fresh map)"
assert_eq "tests/journeys/custom-fixed-path.spec.ts" "$(_mfield_jec JOURNEY-501 "$d/MAP.md" test)" \
  "concrete-path control: test: with no <n> token copies through byte-identical"

# ═══════════════════════════════════════════════════════════════════════
# NO_CONFIRMED_ENTRIES (anti-vacuous): zero CONFIRMED, zero terminal
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/none-confirmed"; _jec_setup "$d"
sed 's/^confirmation_status: CONFIRMED$/confirmation_status: PENDING/' "$d/EXTRACTED.md" > "$d/EXTRACTED.md.new"
mv "$d/EXTRACTED.md.new" "$d/EXTRACTED.md"
_jec_red_case "$d" "NO_CONFIRMED_ENTRIES" "NO_CONFIRMED_ENTRIES"

# ═══════════════════════════════════════════════════════════════════════
# Terminal skip: promoted_as entries are skipped, printed as inventory;
# an all-promoted file is a legitimate no-op (exit 0); a MIXED run
# (terminal + one new promotable) still promotes the new one, continuing
# id assignment past what's already in MAP.
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/terminal1"; _jec_setup "$d"
sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve > /dev/null 2>&1
# re-run: both EXTRACTED-10/11 are now terminal (promoted_as-stamped); no
# new CONFIRMED-without-promoted_as entries remain -> legitimate no-op.
_msha="$(_sha_jec "$d/MAP.md")"
_esha="$(_sha_jec "$d/EXTRACTED.md")"
_out="$(sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "terminal skip: all-promoted file -> exit 0 no-op"
assert_contains "$_out" "ALREADY PROMOTED: EXTRACTED-10 -> JOURNEY-501" "terminal skip: EXTRACTED-10 inventory printed"
assert_contains "$_out" "ALREADY PROMOTED: EXTRACTED-11 -> JOURNEY-502" "terminal skip: EXTRACTED-11 inventory printed"
assert_contains "$_out" "CONFIRM COMPLETE: 0 promoted" "terminal skip: zero NEW promotions (no re-promotion of terminal entries)"
assert_eq "$_msha" "$(_sha_jec "$d/MAP.md")" "terminal skip (no-op): MAP byte-unchanged"
assert_eq "$_esha" "$(_sha_jec "$d/EXTRACTED.md")" "terminal skip (no-op): EXTRACTED byte-unchanged"

# mixed run: add a fresh CONFIRMED candidate to the already-promoted file
cat >> "$d/EXTRACTED.md" << MIXEOF

## EXTRACTED-14 — "A third, freshly confirmed candidate"
needs_human_confirm: true
confirmation_status: CONFIRMED
grade:               [C]
origin:              EXTRACTED
persona:             ops user
goal:                do the third confirmed thing
priority:            P2
covers:              FEAT-100
flows:               []
oracle_surface:      UI
negative_states:     third_error
steps:
  1. do the third thing
  2. trigger third_error
oracle:              a wholly distinct third-candidate oracle signal
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/third.ts:1 — "export function third() {}"
MIXEOF
_out="$(sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve 2>&1)"; _rc=$?
assert_eq 0 "$_rc" "terminal skip (mixed run): exit 0"
assert_contains "$_out" "ALREADY PROMOTED: EXTRACTED-10 -> JOURNEY-501" "terminal skip (mixed): EXTRACTED-10 still inventoried"
assert_contains "$_out" "ALREADY PROMOTED: EXTRACTED-11 -> JOURNEY-502" "terminal skip (mixed): EXTRACTED-11 still inventoried"
assert_contains "$_out" "PROMOTED: EXTRACTED-14 -> JOURNEY-503" "terminal skip (mixed): new entry continues id assignment past 502"
assert_exit 0 sh "$BIN/lint-journey-map.sh" "$d/MAP.md"

# ═══════════════════════════════════════════════════════════════════════
# GRADE_NOT_C
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/grade-not-c"; _jec_setup "$d"
sed '/^## EXTRACTED-10/,/^## EXTRACTED-11/ s/^grade:               \[C\]$/grade:               [I]/' "$d/EXTRACTED.md" > "$d/EXTRACTED.md.new"
mv "$d/EXTRACTED.md.new" "$d/EXTRACTED.md"
_jec_red_case "$d" "GRADE_NOT_C" "GRADE_NOT_C"

# ═══════════════════════════════════════════════════════════════════════
# ORACLE_GAP_UNRESOLVED
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/oracle-gap"; _jec_setup "$d"
sed '/^## EXTRACTED-10/,/^## EXTRACTED-11/ s/^oracle:              the first-candidate success signal is observed$/oracle_gap:          what is the real success signal here?/' "$d/EXTRACTED.md" > "$d/EXTRACTED.md.new"
mv "$d/EXTRACTED.md.new" "$d/EXTRACTED.md"
_jec_red_case "$d" "ORACLE_GAP_UNRESOLVED" "ORACLE_GAP_UNRESOLVED"

# ═══════════════════════════════════════════════════════════════════════
# COVERS_NOT_FEAT — a grammatically non-FEAT covers token. It must be a
# token check-extraction-coverage.sh's OWN anchor pool already recognizes
# (else composition's UNKNOWN_ANCHOR fires first, pre-empting this gate's
# own check entirely) -- a legitimate SCREEN-anchored covers token (spec
# §9.5: staging entries may anchor to screens pre-confirmation) declared
# in the manifest is exactly that: composition passes it through cleanly,
# and THIS gate's own Q6 enforcement (FEAT-grammar only) is what refuses
# it at promotion time.
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/covers-not-feat"; mkdir -p "$d"
awk -v extra='screen: SCR-login | route=/login' '/^EXTRACTION-MANIFEST END$/{print extra} {print}' "$GOLD_MF" > "$_jt/mf-with-screen.md"
_jec_setup_with_mf "$d" "$_jt/mf-with-screen.md"
sed '/^## EXTRACTED-10/,/^## EXTRACTED-11/ s/^covers:              FEAT-100$/covers:              SCR-login/' "$d/EXTRACTED.md" > "$d/EXTRACTED.md.new"
mv "$d/EXTRACTED.md.new" "$d/EXTRACTED.md"
_jec_red_case "$d" "COVERS_NOT_FEAT" "COVERS_NOT_FEAT"
_out="$(sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve 2>&1)"
assert_contains "$_out" "COVERS_NOT_FEAT: EXTRACTED-10: SCR-login" "COVERS_NOT_FEAT: names the offending token"

# ═══════════════════════════════════════════════════════════════════════
# COVERS_UNKNOWN_FEAT — a FEAT-grammatical token that exists in the
# manifest's anchor pool (so composition's own UNKNOWN_ANCHOR does not
# pre-empt this gate) but NOT among its `feat:` lines specifically — a
# manifest `screen:` entry whose id happens to be FEAT-shaped syntax
# proves this gate checks existence against `feat:` lines exactly, never
# the broader covers/flows anchor pool composition itself uses.
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/covers-unknown-feat"; mkdir -p "$d"
awk -v extra='screen: FEAT-777 | route=/somewhere' '/^EXTRACTION-MANIFEST END$/{print extra} {print}' "$GOLD_MF" > "$_jt/mf-with-feat-screen.md"
_jec_setup_with_mf "$d" "$_jt/mf-with-feat-screen.md"
sed '/^## EXTRACTED-10/,/^## EXTRACTED-11/ s/^covers:              FEAT-100$/covers:              FEAT-777/' "$d/EXTRACTED.md" > "$d/EXTRACTED.md.new"
mv "$d/EXTRACTED.md.new" "$d/EXTRACTED.md"
_jec_red_case "$d" "COVERS_UNKNOWN_FEAT" "COVERS_UNKNOWN_FEAT"
_out="$(sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve 2>&1)"
assert_contains "$_out" "COVERS_UNKNOWN_FEAT: EXTRACTED-10: FEAT-777" "COVERS_UNKNOWN_FEAT: names the offending token"
assert_not_contains "$_out" "COVERS_NOT_FEAT: EXTRACTED-10: FEAT-777" "COVERS_UNKNOWN_FEAT: a grammatically-valid but unknown token never ALSO gets COVERS_NOT_FEAT (whitelist-first, one primary code)"

# ═══════════════════════════════════════════════════════════════════════
# COVERS_DUPLICATE — a repeated covers token
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/covers-dup"; _jec_setup "$d"
sed '/^## EXTRACTED-10/,/^## EXTRACTED-11/ s/^covers:              FEAT-100$/covers:              FEAT-100, FEAT-100/' "$d/EXTRACTED.md" > "$d/EXTRACTED.md.new"
mv "$d/EXTRACTED.md.new" "$d/EXTRACTED.md"
_jec_red_case "$d" "COVERS_DUPLICATE" "COVERS_DUPLICATE"
_out="$(sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve 2>&1)"
assert_contains "$_out" "COVERS_DUPLICATE: EXTRACTED-10: FEAT-100" "COVERS_DUPLICATE: names the offending token"

# ═══════════════════════════════════════════════════════════════════════
# EXTRACTED_COLLIDES — one case each vs DERIVED-101/PERSONA-201/
# SIMULATOR-301/REALITY-401 (all four share covers: FEAT-100 in the golden
# MAP, distinct oracle text; matching EXTRACTED-10's oracle to each target
# in turn produces an isolated, single-code collision).
# ═══════════════════════════════════════════════════════════════════════

_jec_collide_case() { # TARGET_ORACLE TARGET_JID LABEL
  d="$_jt/collide-$3"; _jec_setup "$d"
  sed "/^## EXTRACTED-10/,/^## EXTRACTED-11/ s|^oracle:              the first-candidate success signal is observed\$|oracle:              $1|" "$d/EXTRACTED.md" > "$d/EXTRACTED.md.new"
  mv "$d/EXTRACTED.md.new" "$d/EXTRACTED.md"
  _jec_red_case "$d" "EXTRACTED_COLLIDES" "EXTRACTED_COLLIDES vs $3"
  _out="$(sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve 2>&1)"
  assert_contains "$_out" "EXTRACTED_COLLIDES: EXTRACTED-10 vs $2" "EXTRACTED_COLLIDES vs $3: names the exact pair"
}
_jec_collide_case "the derived-journey success signal" "JOURNEY-101" "DERIVED-101"
_jec_collide_case "the persona-journey success signal" "JOURNEY-201" "PERSONA-201"
_jec_collide_case "the simulator-journey success signal" "JOURNEY-301" "SIMULATOR-301"
_jec_collide_case "the reality-journey success signal" "JOURNEY-401" "REALITY-401"

# sibling collision: two CONFIRMED entries in the SAME staging file share
# a normalized covers+oracle key -- no existing map journey involved.
d="$_jt/sibling-collide"; mkdir -p "$d"
cp "$GOLD_MAP" "$d/MAP.md"
cp "$MF_SINGLE_FEAT" "$d/MANIFEST.md"
_sib_sha="$(_mf_block_sha "$d/MANIFEST.md")"
cat > "$d/EXTRACTED.md" << SIBEOF
# JOURNEY-EXTRACTED
extraction_commit: 1234567890123456789012345678901234567890
manifest_sha256:   $_sib_sha

## EXTRACTED-20 — "Sibling A"
needs_human_confirm: true
confirmation_status: CONFIRMED
grade:               [C]
origin:              EXTRACTED
persona:             ops user
goal:                do the sibling thing, path A
priority:            P2
covers:              FEAT-100
flows:               []
oracle_surface:      UI
negative_states:     sibling_error
steps:
  1. do the sibling thing (A)
  2. trigger sibling_error
oracle:              a shared sibling oracle signal never used elsewhere
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/sibling-a.ts:1 — "export function siblingA() {}"

## EXTRACTED-21 — "Sibling B (same covers+oracle as A)"
needs_human_confirm: true
confirmation_status: CONFIRMED
grade:               [C]
origin:              EXTRACTED
persona:             ops user
goal:                do the sibling thing, path B
priority:            P2
covers:              FEAT-100
flows:               []
oracle_surface:      UI
negative_states:     sibling_error
steps:
  1. do the sibling thing (B)
  2. trigger sibling_error
oracle:              a shared sibling oracle signal never used elsewhere
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/sibling-b.ts:1 — "export function siblingB() {}"
SIBEOF
_jec_red_case "$d" "EXTRACTED_COLLIDES" "EXTRACTED_COLLIDES (sibling)"
_out="$(sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve 2>&1)"
assert_contains "$_out" "EXTRACTED-20" "EXTRACTED_COLLIDES (sibling): names EXTRACTED-20"
assert_contains "$_out" "EXTRACTED-21" "EXTRACTED_COLLIDES (sibling): names EXTRACTED-21"

# ═══════════════════════════════════════════════════════════════════════
# RANGE_EXHAUSTED — a map pre-seeded with JOURNEY-501..599 (99 blocks,
# generated here, never committed as a fixture)
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/range-exhausted"; mkdir -p "$d"
: > "$d/MAP.md"
i=501
while [ "$i" -le 599 ]; do
  cat >> "$d/MAP.md" << RBEOF

## JOURNEY-$i — "Range filler $i"
origin:          DERIVED
persona:         any user
goal:            filler goal $i
priority:        P2
covers:          FEAT-8$i
flows:           []
oracle_surface:  UI
negative_states: filler_error
data_fixtures:   []
steps:
  1. filler step
  2. trigger filler_error
oracle:          filler oracle $i
evidence:        []
test:            tests/journeys/journey-$i.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
RBEOF
  i=$((i + 1))
done
assert_exit 0 sh "$BIN/lint-journey-map.sh" "$d/MAP.md"
cp "$GOLD_MF" "$d/MANIFEST.md"
sed "s/^manifest_sha256:.*/manifest_sha256:   $_MF_SHA/" "$GOLD_EXT" > "$d/EXTRACTED.md"
_jec_red_case "$d" "RANGE_EXHAUSTED" "RANGE_EXHAUSTED"

# ═══════════════════════════════════════════════════════════════════════
# LINT_FAILED pass-through -- EXTRACTED fails lint-journey-extracted.sh
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/lint-failed-extracted"; _jec_setup "$d"
printf '\nSTRAY: ## JOURNEY-999 pasted directly (paste-promotion bypass attempt)\n' >> "$d/EXTRACTED.md"
_jec_red_case "$d" "LINT_FAILED" "LINT_FAILED (staging)"

d="$_jt/lint-failed-map"; _jec_setup "$d"
sed 's/^priority:        P2$/priority:        P9/' "$d/MAP.md" > "$d/MAP.md.new"
mv "$d/MAP.md.new" "$d/MAP.md"
_jec_red_case "$d" "LINT_FAILED" "LINT_FAILED (map)"

# ═══════════════════════════════════════════════════════════════════════
# check-extraction-coverage.sh pass-through -- a staleness drift
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/stale-manifest"; _jec_setup "$d"
sed 's/^feat: FEAT-200.*/feat: FEAT-200 | behaviors=9 | states_filled=9 | grade_counts=C:1,I:0,G:0,X:0/' "$d/MANIFEST.md" > "$d/MANIFEST.md.new"
mv "$d/MANIFEST.md.new" "$d/MANIFEST.md"
_jec_red_case "$d" "EXTRACTION_STALE" "EXTRACTION_STALE (coverage pass-through)"

# ═══════════════════════════════════════════════════════════════════════
# TOOL_MISSING -- PATH shim excluding sha256sum AND shasum (E2/E3
# precedent). Reached via the COMPOSED check-extraction-coverage.sh's own
# stage-3 freshness requirement (it runs, and needs a sha tool, BEFORE
# this gate's own extraction_provenance-stamp sha computation is ever
# reached) -- documented latent note, not a bug: both share the identical
# "cannot compute a sha256, fail closed" meaning.
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/tool-missing"; _jec_setup "$d"
_shim_nosha="$_jt/shim-nosha"; mkdir -p "$_shim_nosha"
for _b in sh awk sed grep tr head sort uniq cat mktemp dirname basename rm wc printf date cut; do
  _real="$(command -v "$_b")" && ln -s "$_real" "$_shim_nosha/$_b"
done
_msha="$(_sha_jec "$d/MAP.md")"
_esha="$(_sha_jec "$d/EXTRACTED.md")"
_out="$(PATH="$_shim_nosha" /bin/sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve 2>&1)"; _rc=$?
_jec_nonzero "$_rc" "TOOL_MISSING: exit non-zero"
assert_contains "$_out" "TOOL_MISSING" "TOOL_MISSING: names the code"
assert_eq "$_msha" "$(_sha_jec "$d/MAP.md")" "TOOL_MISSING: MAP byte-unchanged"
assert_eq "$_esha" "$(_sha_jec "$d/EXTRACTED.md")" "TOOL_MISSING: EXTRACTED byte-unchanged"

# ═══════════════════════════════════════════════════════════════════════
# MKTEMP_FAILED -- PATH shim with a fake mktemp that always fails (reached
# via THIS gate's own first mktemp call, step 11 -- check-extraction-
# coverage.sh itself uses no temp files at all).
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/mktemp-failed"; _jec_setup "$d"
_shim_nomktemp="$_jt/shim-nomktemp"; mkdir -p "$_shim_nomktemp"
for _b in sh awk sed grep tr head sort uniq cat dirname basename rm wc printf date cut sha256sum shasum; do
  _real="$(command -v "$_b")" && ln -s "$_real" "$_shim_nomktemp/$_b"
done
cat > "$_shim_nomktemp/mktemp" << 'MKSHIM'
#!/bin/sh
printf 'mktemp: simulated failure (fail-closed proof)\n' >&2
exit 1
MKSHIM
chmod +x "$_shim_nomktemp/mktemp"
_msha="$(_sha_jec "$d/MAP.md")"
_esha="$(_sha_jec "$d/EXTRACTED.md")"
_out="$(PATH="$_shim_nomktemp" /bin/sh "$GATE" "$d/MAP.md" "$d/EXTRACTED.md" "$d/MANIFEST.md" --approve 2>&1)"; _rc=$?
_jec_nonzero "$_rc" "MKTEMP_FAILED: exit non-zero"
assert_contains "$_out" "MKTEMP_FAILED" "MKTEMP_FAILED: names the code"
assert_eq "$_msha" "$(_sha_jec "$d/MAP.md")" "MKTEMP_FAILED: MAP byte-unchanged"
assert_eq "$_esha" "$(_sha_jec "$d/EXTRACTED.md")" "MKTEMP_FAILED: EXTRACTED byte-unchanged"

# ═══════════════════════════════════════════════════════════════════════
# map-lint additive check (Check 10): EXTRACTION_PROVENANCE_FORMAT, RED
# ═══════════════════════════════════════════════════════════════════════

d="$_jt/eprov-lint"; mkdir -p "$d"
cat > "$d/MAP-good.md" << EPGOOD
## JOURNEY-501 — "Good extraction_provenance"
origin:          EXTRACTED
persona:         ops user
goal:            do the thing
priority:        P2
covers:          FEAT-100
flows:           []
oracle_surface:  UI
negative_states: some_error
data_fixtures:   []
steps:
  1. do the thing
  2. trigger some_error
oracle:          the success signal
evidence:        []
test:            tests/journeys/journey-501.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
extraction_provenance: EXTRACTED-10 commit:1234567890123456789012345678901234567890 confirmed:aabbccddeeff
EPGOOD
assert_exit 0 sh "$BIN/lint-journey-map.sh" "$d/MAP-good.md"

sed 's/^extraction_provenance:.*/extraction_provenance: not-well-formed-at-all/' "$d/MAP-good.md" > "$d/MAP-bad.md"
_epout="$(sh "$BIN/lint-journey-map.sh" "$d/MAP-bad.md" 2>&1)"; _eprc=$?
assert_eq 1 "$_eprc" "EXTRACTION_PROVENANCE_FORMAT: exit 1 on malformed value"
assert_contains "$_epout" "EXTRACTION_PROVENANCE_FORMAT" "EXTRACTION_PROVENANCE_FORMAT: names the code"

# each of the three sub-grammars, mutated in isolation
sed 's/^extraction_provenance:.*/extraction_provenance: NOTANID-10 commit:1234567890123456789012345678901234567890 confirmed:aabbccddeeff/' "$d/MAP-good.md" > "$d/MAP-bad-id.md"
_o="$(sh "$BIN/lint-journey-map.sh" "$d/MAP-bad-id.md" 2>&1)"; _jec_nonzero "$?" "EXTRACTION_PROVENANCE_FORMAT (bad id shape): exit non-zero"
assert_contains "$_o" "EXTRACTION_PROVENANCE_FORMAT" "EXTRACTION_PROVENANCE_FORMAT (bad id shape): names the code"

sed 's/^extraction_provenance:.*/extraction_provenance: EXTRACTED-10 commit:short confirmed:aabbccddeeff/' "$d/MAP-good.md" > "$d/MAP-bad-commit.md"
_o="$(sh "$BIN/lint-journey-map.sh" "$d/MAP-bad-commit.md" 2>&1)"; _jec_nonzero "$?" "EXTRACTION_PROVENANCE_FORMAT (short commit): exit non-zero"
assert_contains "$_o" "EXTRACTION_PROVENANCE_FORMAT" "EXTRACTION_PROVENANCE_FORMAT (short commit): names the code"

sed 's/^extraction_provenance:.*/extraction_provenance: EXTRACTED-10 commit:1234567890123456789012345678901234567890 confirmed:tooLong123456/' "$d/MAP-good.md" > "$d/MAP-bad-confirmed.md"
_o="$(sh "$BIN/lint-journey-map.sh" "$d/MAP-bad-confirmed.md" 2>&1)"; _jec_nonzero "$?" "EXTRACTION_PROVENANCE_FORMAT (bad confirmed hex length): exit non-zero"
assert_contains "$_o" "EXTRACTION_PROVENANCE_FORMAT" "EXTRACTION_PROVENANCE_FORMAT (bad confirmed hex length): names the code"

# ── regression lock: extraction_provenance stays OPTIONAL — existing map
# lint tests are byte-unchanged (spot-check the shared good fixtures the
# rest of the suite relies on; the full lint-journey-map_test.sh /
# journey-preconditions_test.sh / uat-oracle-scope_test.sh files also run
# unmodified as their own suite members, run.sh-wide). ──────────────────
assert_exit 0 sh "$BIN/lint-journey-map.sh" "$TESTS_DIR/fixtures/good/JOURNEY_MAP.md"
assert_exit 0 sh "$BIN/lint-journey-map.sh" "$TESTS_DIR/fixtures/lint/preconditions-good.md"
assert_exit 1 sh "$BIN/lint-journey-map.sh" "$TESTS_DIR/fixtures/lint/bad-enum.md"

rm -rf "$_jt"
