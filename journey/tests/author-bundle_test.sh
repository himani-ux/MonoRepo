# shellcheck shell=sh
# author-bundle_test.sh — blind author-bundle builder proofs (Increment 2).
# Blindness is BY CONSTRUCTION: the bundle is the author's entire world.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
AB="$TESTS_DIR/../bin/author-bundle.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
SFX="$TESTS_DIR/fixtures/surface"
GMAP="$GENDIR/golden/expected-journey-map.generated.md"

_ab_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

_t=$(mktemp -d)

# ── ab-1: golden bundle for JOURNEY-101 ───────────────────────────────────────
sh "$AB" "$GMAP" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t/out1" >/dev/null 2>&1
assert_eq 0 $? "ab-1: golden author bundle builds"
_b=$(cat "$_t/out1/author-bundle-journey-101.md" 2>/dev/null)
assert_contains "$_b" "## JOURNEY-101" "ab-1: bundle carries the target journey block"
assert_contains "$_b" "## SURFACE: invoices_list" "ab-1: bundle carries the touched SURFACE screen"
assert_contains "$_b" "AFJ-001" "ab-1: bundle carries the journey's AFJ steps"
assert_contains "$_b" "AC-2: the file appears in the invoice list" "ab-1: bundle carries the covered FEAT's ACs"
assert_contains "$_b" "import { test, expect } from '@playwright/test';" "ab-1: bundle carries the frozen spec skeleton"

# ── ab-2: bundle excludes unrelated anchors and src/ ─────────────────────────
assert_not_contains "$_b" "FEAT-002" "ab-2: bundle excludes uncovered FEATs"
assert_not_contains "$_b" "AFJ-002" "ab-2: bundle excludes untouched journeys"
assert_not_contains "$_b" "src/" "ab-2: bundle carries no src/ path (blind by construction)"

# ── ab-3: unknown journey fails ───────────────────────────────────────────────
_o=$(sh "$AB" "$GMAP" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-999 "$_t/out3" 2>&1); _ec=$?
_ab_nonzero "$_ec" "ab-3: unknown journey fails"
assert_contains "$_o" "UNKNOWN_JOURNEY" "ab-3: names UNKNOWN_JOURNEY"

# ── ab-4: already-WRITTEN journey fails ───────────────────────────────────────
sed 's/^author_status:   UNWRITTEN/author_status:   WRITTEN/' "$GMAP" > "$_t/written-map.md"
_o=$(sh "$AB" "$_t/written-map.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t/out4" 2>&1); _ec=$?
_ab_nonzero "$_ec" "ab-4: already-WRITTEN journey fails"
assert_contains "$_o" "ALREADY_WRITTEN" "ab-4: names ALREADY_WRITTEN"

# ── ab-5: touched screen missing from TEST_SURFACE → REQUIRED_SURFACE_GAP ────
_o=$(sh "$AB" "$GMAP" "$SFX/TEST_SURFACE.invented-screen.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t/out5" 2>&1); _ec=$?
_ab_nonzero "$_ec" "ab-5: touched screen absent from surface fails"
assert_contains "$_o" "REQUIRED_SURFACE_GAP" "ab-5: names REQUIRED_SURFACE_GAP"
[ ! -d "$_t/out5" ] || [ -z "$(ls -A "$_t/out5" 2>/dev/null)" ]
assert_eq 0 $? "ab-5: no bundle written on failure (never invents selectors)"

# ── ab-6: journey flows anchor missing from APP_FLOW → MISSING_ANCHOR ─────────
sed '/^### AFJ-001/,/^$/d' "$GENDIR/APP_FLOW.md" > "$_t/noafj.md"
_o=$(sh "$AB" "$GMAP" "$SFX/TEST_SURFACE.golden.md" "$_t/noafj.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t/out6" 2>&1); _ec=$?
_ab_nonzero "$_ec" "ab-6: missing AFJ anchor fails"
assert_contains "$_o" "MISSING_ANCHOR" "ab-6: names MISSING_ANCHOR"

# ── ab-7: flows: [] means NO anchors, not ALL anchors (V1 F1) ────────────────
# `flows: []` is the map's legally-blank list-field sentinel (forced by
# journey-inbox-triage.sh on every promoted SIMULATOR journey). The AFJ
# anchor matcher builds a dynamic ERE from the raw token
# ("(^|[^0-9A-Za-z])" id "([^0-9]|$)") — with id="[]" this parses as a
# bracket-class atom that matches any digit, so it fires on every heading
# that has a digit immediately after punctuation (i.e. every realistic
# "### AFJ-NNN" / "### SCR-NNN" heading) — the whole APP_FLOW leaks into the
# blind bundle instead of contributing zero anchors.
sed 's/^flows:.*/flows:           []/' "$GMAP" > "$_t/flows-empty-map.md"
sh "$AB" "$_t/flows-empty-map.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t/out7" >/dev/null 2>&1
assert_eq 0 $? "ab-7: flows: [] still builds a bundle (covers: FEAT-001 is a valid anchor)"
_b7=$(cat "$_t/out7/author-bundle-journey-101.md" 2>/dev/null)
assert_contains "$_b7" "## FEAT-001" "ab-7: bundle still carries the covered FEAT-001 block"
assert_not_contains "$_b7" "### AFJ-" "ab-7: flows: [] means NO anchors — no ### AFJ- section leaks in"
assert_not_contains "$_b7" "### SCR-" "ab-7: flows: [] means NO anchors — no ### SCR- section leaks in either"

# ── ab-8..ab-12: anchor-token grammar — the ERE-injection CLASS (V-T4b) ──────
# T4b's fix guarded only the literal `[]` token; any OTHER token was still
# spliced verbatim into the AFJ matcher's dynamic ERE. Canonical id grammars
# per journey/bin/check-doc-format.sh: FEAT is prefix-capable
# `FEAT-([A-Z]+-)?[0-9]+` (its PRD block-split regex); AFJ is `AFJ-[0-9]+`
# (its User-Journeys heading regex). A token that does not full-match its
# field's grammar must fail closed as ANCHOR_TOKEN_INVALID (ungrammatical)
# BEFORE reaching any matcher — distinct from MISSING_ANCHOR (grammatical
# but absent from the doc, ab-6 above). `[]` stays a legal no-anchors
# sentinel (ab-7 above), never an error.

# ab-8: flows: [AFJ-001] — the YAML-list typo a human can make during the
# very §6.1 re-anchoring step. Pre-fix: `[AFJ-001]` parses as a bracket
# class, matches BOTH ### AFJ- headings, exit 0 — silent overexposure.
sed 's/^flows:.*/flows:           [AFJ-001]/' "$GMAP" > "$_t/flows-yaml-typo.md"
_o=$(sh "$AB" "$_t/flows-yaml-typo.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t/out8" 2>&1); _ec=$?
_ab_nonzero "$_ec" "ab-8: flows: [AFJ-001] (YAML-list typo) fails closed"
assert_contains "$_o" "ANCHOR_TOKEN_INVALID: JOURNEY-101 flows token '[AFJ-001]'" \
  "ab-8: names ANCHOR_TOKEN_INVALID with journey id, field, and the offending token"
[ ! -d "$_t/out8" ] || [ -z "$(ls -A "$_t/out8" 2>/dev/null)" ]
assert_eq 0 $? "ab-8: no bundle written on an ungrammatical flows token"

# ab-9: bare flows: [ — pre-fix this unclosed bracket ERE matched EVERY
# heading (AFJ-001, AFJ-002, SCR-001 all leaked) at exit 0.
sed 's/^flows:.*/flows:           [/' "$GMAP" > "$_t/flows-bare-bracket.md"
_o=$(sh "$AB" "$_t/flows-bare-bracket.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t/out9" 2>&1); _ec=$?
_ab_nonzero "$_ec" "ab-9: bare flows: [ fails closed"
assert_contains "$_o" "ANCHOR_TOKEN_INVALID: JOURNEY-101 flows token '['" \
  "ab-9: bare [ named as an ungrammatical flows token"
[ ! -d "$_t/out9" ] || [ -z "$(ls -A "$_t/out9" 2>/dev/null)" ]
assert_eq 0 $? "ab-9: no bundle written on a bare-bracket flows token"

# ab-10: a covers token carrying brackets is ungrammatical for the FEAT
# field — ANCHOR_TOKEN_INVALID, not MISSING_ANCHOR (it never legitimately
# reaches the PRD matcher at all).
sed 's/^covers:          FEAT-001/covers:          [FEAT-001]/' "$GMAP" > "$_t/covers-bracket.md"
_o=$(sh "$AB" "$_t/covers-bracket.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t/out10" 2>&1); _ec=$?
_ab_nonzero "$_ec" "ab-10: covers: [FEAT-001] fails closed"
assert_contains "$_o" "ANCHOR_TOKEN_INVALID: JOURNEY-101 covers token '[FEAT-001]'" \
  "ab-10: bracketed covers token is ANCHOR_TOKEN_INVALID (ungrammatical), not MISSING_ANCHOR"
assert_not_contains "$_o" "MISSING_ANCHOR" \
  "ab-10: ungrammatical is never reported as merely unanchored"

# ab-11: a screen-name covers (the not-yet-re-anchored promoted SIMULATOR
# journey, §6.1) is ungrammatical for the covers field at authoring time —
# ANCHOR_TOKEN_INVALID, telling the human to re-anchor, not to hunt a
# missing PRD block. (No prior test locked the screen-name failure code;
# this one now does.)
sed 's/^covers:          FEAT-001/covers:          invoices_list/' "$GMAP" > "$_t/covers-screen.md"
_o=$(sh "$AB" "$_t/covers-screen.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t/out11" 2>&1); _ec=$?
_ab_nonzero "$_ec" "ab-11: screen-name covers fails closed"
assert_contains "$_o" "ANCHOR_TOKEN_INVALID: JOURNEY-101 covers token 'invoices_list'" \
  "ab-11: screen-name covers is ANCHOR_TOKEN_INVALID — re-anchor to FEAT-IDs at triage (L18/§6.1)"

# ab-12: prefix-capable FEAT ids are grammatical (check-doc-format.sh's own
# PRD regex allows FEAT-([A-Z]+-)?<n>) — a FEAT-ABC-1 token must reach the
# matcher and fail as MISSING_ANCHOR (absent from this PRD), never as
# ANCHOR_TOKEN_INVALID.
sed 's/^covers:          FEAT-001/covers:          FEAT-ABC-1/' "$GMAP" > "$_t/covers-prefixed.md"
_o=$(sh "$AB" "$_t/covers-prefixed.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$GENDIR/PRD.md" \
  JOURNEY-101 "$_t/out12" 2>&1); _ec=$?
_ab_nonzero "$_ec" "ab-12: grammatical-but-absent prefixed FEAT id fails closed"
assert_contains "$_o" "MISSING_ANCHOR" \
  "ab-12: prefix-capable FEAT id passes the grammar, fails as MISSING_ANCHOR (absent)"
assert_not_contains "$_o" "ANCHOR_TOKEN_INVALID" \
  "ab-12: a grammatical token is never reported as ungrammatical"

# ── ab-13/ab-14/ab-15: covers matcher boundary anchoring (V-T4c P1) ─────────
# Pre-fix: the PRD block matcher used bare `index($0, id)` — a SUBSTRING
# match. covers: FEAT-001 against a PRD that also contains ## FEAT-0011
# pulled BOTH blocks into the blind bundle at exit 0 (silent overexposure —
# the blind author sees acceptance criteria it was never anchored to).
# Fixed with the boundary-anchored heading match ("^## " id "( |$)"),
# mirroring the flows/AFJ matcher's boundary idiom; the id is grammar-
# whitelisted (^FEAT-([A-Z]+-)?[0-9]+$) BEFORE interpolation (L22).
cat "$GENDIR/PRD.md" > "$_t/prd-collide.md"
cat >> "$_t/prd-collide.md" <<'_PRD_COLLIDE_EOF_'

## FEAT-0011 — "Invoice bulk archive"
priority: P2
user_story: As an ops user, I can archive many invoices at once.
acceptance_criteria:
  - AC-1: selected invoices move to the archive
  - AC-2: archived invoices disappear from the active list
_PRD_COLLIDE_EOF_

# ab-13: covers FEAT-001 must pull ONLY FEAT-001's block, never FEAT-0011's.
sh "$AB" "$GMAP" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$_t/prd-collide.md" \
  JOURNEY-101 "$_t/out13" >/dev/null 2>&1
assert_eq 0 $? "ab-13: bundle builds against the prefix-colliding PRD"
_b13="$_t/out13/author-bundle-journey-101.md"
assert_eq 1 "$(grep -c '^## FEAT-001 ' "$_b13")" \
  "ab-13: bundle carries exactly the covered FEAT-001 block"
assert_eq 0 "$(grep -c '^## FEAT-0011' "$_b13")" \
  "ab-13: prefix-colliding FEAT-0011 block does NOT leak into the blind bundle (V-T4c P1)"

# ab-14 (control): covers FEAT-0011 pulls ONLY FEAT-0011's block — the
# boundary anchor must not break the longer id's own lookup.
sed 's/^covers:          FEAT-001$/covers:          FEAT-0011/' "$GMAP" > "$_t/covers-0011-map.md"
sh "$AB" "$_t/covers-0011-map.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$_t/prd-collide.md" \
  JOURNEY-101 "$_t/out14" >/dev/null 2>&1
assert_eq 0 $? "ab-14: covers FEAT-0011 builds against the same PRD (control)"
_b14="$_t/out14/author-bundle-journey-101.md"
assert_eq 1 "$(grep -c '^## FEAT-0011 ' "$_b14")" \
  "ab-14: bundle carries exactly the covered FEAT-0011 block"
assert_eq 0 "$(grep -c '^## FEAT-001 ' "$_b14")" \
  "ab-14: the shorter FEAT-001 block does not ride along either direction"

# ab-15: a prefix-capable covers id (FEAT-ABC-1, grammatical per
# check-doc-format.sh) whose block IS in the PRD must be found — the
# heading matcher honors the same prefix-capable grammar the token
# whitelist admits (ab-12 proved the absent case; this proves the present
# one).
cat "$_t/prd-collide.md" > "$_t/prd-prefixed.md"
cat >> "$_t/prd-prefixed.md" <<'_PRD_PREFIXED_EOF_'

## FEAT-ABC-1 — "Invoice audit trail"
priority: P2
user_story: As an auditor, I can see who changed an invoice and when.
acceptance_criteria:
  - AC-1: every status change lists actor and timestamp
_PRD_PREFIXED_EOF_
sed 's/^covers:          FEAT-001$/covers:          FEAT-ABC-1/' "$GMAP" > "$_t/covers-abc-map.md"
sh "$AB" "$_t/covers-abc-map.md" "$SFX/TEST_SURFACE.golden.md" "$GENDIR/APP_FLOW.md" "$_t/prd-prefixed.md" \
  JOURNEY-101 "$_t/out15" >/dev/null 2>&1
assert_eq 0 $? "ab-15: prefix-capable covers id with a present PRD block builds"
_b15="$_t/out15/author-bundle-journey-101.md"
assert_eq 1 "$(grep -c '^## FEAT-ABC-1 ' "$_b15")" \
  "ab-15: bundle carries the prefix-capable FEAT-ABC-1 block (grammar and matcher agree)"
assert_eq 0 "$(grep -c '^## FEAT-001 ' "$_b15")" \
  "ab-15: unrelated FEAT-001 block does not leak in"

rm -rf "$_t"
