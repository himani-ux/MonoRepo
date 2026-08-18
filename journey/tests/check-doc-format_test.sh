# shellcheck shell=sh
# check-doc-format_test.sh — doc-format PREFLIGHT proofs (review C5).
#
# The slicer dies on the FIRST malformed block; the preflight reports EVERY
# violation with an actionable per-id diagnostic BEFORE generation is
# attempted, so an operator fixes the docs in one pass instead of ten runs.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
CDF="$TESTS_DIR/../bin/check-doc-format.sh"
FX="$TESTS_DIR/fixtures/gen"

_df_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

# ── df-1: golden docs pass the preflight ──────────────────────────────────────
sh "$CDF" "$FX/PRD.md" "$FX/APP_FLOW.md" >/dev/null 2>&1
assert_eq 0 $? "df-1: golden PRD/APP_FLOW pass the preflight"

# ── df-2: Step-1-style PRD (must/should/nice, no FEAT blocks) → actionable ───
_t=$(mktemp -d)
cat > "$_t/PRD-step1.md" << 'DOC'
# PRD

| FEAT-ID | Name | Priority |
|---------|------|----------|
| FEAT-001 | Upload | must |
DOC
_o=$(sh "$CDF" "$_t/PRD-step1.md" "$FX/APP_FLOW.md" 2>&1); _ec=$?
_df_nonzero "$_ec" "df-2: table-style PRD (no FEAT blocks) fails preflight"
assert_contains "$_o" "PRD_NO_FEAT_BLOCKS" "df-2: names PRD_NO_FEAT_BLOCKS"
assert_contains "$_o" "journey-gen-doc-format.md" "df-2: points at the format doc"

# ── df-3: multi-diagnostic — ALL violations reported in ONE run ──────────────
cat > "$_t/PRD-multi.md" << 'DOC'
# PRD

## FEAT-001 — "No priority"
user_story: As a user, I do a thing.
acceptance_criteria:
  - AC-1: the thing happens

## FEAT-002 — "Bad priority, no story, no ACs"
priority: must
DOC
_o=$(sh "$CDF" "$_t/PRD-multi.md" "$FX/APP_FLOW.md" 2>&1); _ec=$?
_df_nonzero "$_ec" "df-3: malformed PRD fails preflight"
assert_contains "$_o" "FEAT_PRIORITY_MISSING: FEAT-001" "df-3: reports missing priority on FEAT-001"
assert_contains "$_o" "FEAT_PRIORITY_INVALID: FEAT-002" "df-3: reports invalid priority 'must' on FEAT-002"
assert_contains "$_o" "FEAT_NO_USER_STORY: FEAT-002" "df-3: reports missing user_story on FEAT-002"
assert_contains "$_o" "FEAT_NO_ACCEPTANCE_CRITERIA: FEAT-002" "df-3: reports missing ACs on FEAT-002"

# ── df-4: APP_FLOW without a User Journeys section ────────────────────────────
printf '# APP_FLOW\n\nScreens only, no journeys section.\n' > "$_t/APP-none.md"
_o=$(sh "$CDF" "$FX/PRD.md" "$_t/APP-none.md" 2>&1); _ec=$?
_df_nonzero "$_ec" "df-4: APP_FLOW without '## User Journeys' fails"
assert_contains "$_o" "APP_FLOW_NO_USER_JOURNEYS" "df-4: names APP_FLOW_NO_USER_JOURNEYS"

# ── df-5: un-id'd journey heading + journey without steps ─────────────────────
cat > "$_t/APP-bad.md" << 'DOC'
# APP_FLOW

## User Journeys

### Corrected invoice upload
steps:
  1. do the thing

### AFJ-002 — "No steps"
covers_features: FEAT-001
states: [EMPTY]
DOC
_o=$(sh "$CDF" "$FX/PRD.md" "$_t/APP-bad.md" 2>&1); _ec=$?
_df_nonzero "$_ec" "df-5: un-id'd heading + stepless journey fail"
assert_contains "$_o" "APP_FLOW_UNIDDED" "df-5: names APP_FLOW_UNIDDED"
assert_contains "$_o" "AFJ_NO_STEPS: AFJ-002" "df-5: names AFJ_NO_STEPS for AFJ-002"

# ── df-6: duplicate FEAT / AFJ ids ────────────────────────────────────────────
cat > "$_t/PRD-dup.md" << 'DOC'
# PRD

## FEAT-001 — "One"
priority: P0
covers_flows: AFJ-001
user_story: As a user, I do one.
acceptance_criteria:
  - AC-1: one happens

## FEAT-001 — "One again"
priority: P1
covers_flows: AFJ-002
user_story: As a user, I do one again.
acceptance_criteria:
  - AC-1: one happens again
DOC
_o=$(sh "$CDF" "$_t/PRD-dup.md" "$FX/APP_FLOW.md" 2>&1); _ec=$?
_df_nonzero "$_ec" "df-6: duplicate FEAT id fails"
assert_contains "$_o" "DUPLICATE_FEAT_ID: FEAT-001" "df-6: names DUPLICATE_FEAT_ID"

# ── df-7: unlinked P0 FEAT fails by default, passes with --allow-unlinked ────
_o=$(sh "$CDF" "$FX/unlinked/PRD.md" "$FX/unlinked/APP_FLOW.md" 2>&1); _ec=$?
_df_nonzero "$_ec" "df-7: unlinked P0 FEAT-004 fails preflight by default"
assert_contains "$_o" "UNLINKED_FEAT: FEAT-004" "df-7: names the unlinked id"
assert_contains "$_o" "coverage gap" "df-7: remedy mentions the structured-gap path"
sh "$CDF" "$FX/unlinked/PRD.md" "$FX/unlinked/APP_FLOW.md" --allow-unlinked >/dev/null 2>&1
assert_eq 0 $? "df-7: --allow-unlinked defers the unlinked ids to the gap workflow"

# ── df-8: unlabeled acceptance criteria (no AC-<n>) → actionable ─────────────
cat > "$_t/PRD-unlabeled.md" << 'DOC'
# PRD

## FEAT-001 — "Unlabeled ACs"
priority: P0
covers_flows: AFJ-001
user_story: As a user, I upload.
acceptance_criteria:
  - a valid CSV is accepted
  - the row shows ACCEPTED
DOC
_o=$(sh "$CDF" "$_t/PRD-unlabeled.md" "$FX/APP_FLOW.md" 2>&1); _ec=$?
_df_nonzero "$_ec" "df-8: acceptance criteria without AC-<n> labels fail"
assert_contains "$_o" "FEAT_AC_UNLABELED: FEAT-001" "df-8: names FEAT_AC_UNLABELED (AC accounting needs labels)"

# ── df-9: prefixed FEAT ids (FEAT-SMS-001) are first-class ───────────────────
_pfx="$_t/prefixed"; mkdir -p "$_pfx"
cat > "$_pfx/PRD.md" << 'DOC'
## FEAT-SMS-001 — "Register upload"
priority: P0
covers_flows: AFJ-001
user_story: As an operator, I upload a register and see it accepted.
acceptance_criteria:
  - AC-1: a valid file is accepted
DOC
cat > "$_pfx/APP_FLOW.md" << 'DOC'
## User Journeys

### AFJ-001 — "Register upload"
covers_features: FEAT-SMS-001
steps:
  1. land on /register
  2. upload file -> ACCEPTED

## Screens

### SCR-1 — "register"
route: /register
DOC
_o=$(sh "$CDF" "$_pfx/PRD.md" "$_pfx/APP_FLOW.md" 2>&1); _ec=$?
assert_eq "0" "$_ec" "df-9: prefixed FEAT-SMS ids pass the preflight"
assert_not_contains "$_o" "PRD_NO_FEAT_BLOCKS" "df-9: prefixed FEAT block is recognized"

# ── §3b Screens section is preflight law ─────────────────────────────────────
_scr="$_t/screens"; mkdir -p "$_scr"
cp "$_pfx/PRD.md" "$_scr/PRD.md"
# (a) no ## Screens at all
sed '/## Screens/,$d' "$_pfx/APP_FLOW.md" > "$_scr/AF_none.md"
out=$(sh "$CDF" "$_scr/PRD.md" "$_scr/AF_none.md" 2>&1); ec=$?
assert_eq "1" "$ec" "df-10a: missing ## Screens fails closed"
assert_contains "$out" "SCREENS_SECTION_MISSING" "df-10a: names the missing-section diagnostic"
# (b) unidded / unnamed / no-route / duplicate
cat > "$_scr/AF_bad.md" <<'EOF'
## User Journeys

### AFJ-001 — "Register upload"
covers_features: FEAT-SMS-001
steps:
  1. land on /register

## Screens

### register detail
route: /register

### SCR-2 — no quoted name
route: /two

### SCR-3 — "no_route_screen"
states: [EMPTY]

### SCR-4 — "dup"
route: /four

### SCR-4 — "dup2"
route: /four-b
EOF
out=$(sh "$CDF" "$_scr/PRD.md" "$_scr/AF_bad.md" 2>&1) || true
assert_contains "$out" "SCREEN_UNIDDED"       "df-10b: unidded heading caught"
assert_contains "$out" "SCREEN_UNNAMED"       "df-10b: unquoted name caught"
assert_contains "$out" "SCREEN_NO_ROUTE"      "df-10b: missing route caught"
assert_contains "$out" "DUPLICATE_SCREEN_ID"  "df-10b: duplicate SCR id caught"
# (c) untouched screen: route in no AFJ steps
cat > "$_scr/AF_untouched.md" <<'EOF'
## User Journeys

### AFJ-001 — "Register upload"
covers_features: FEAT-SMS-001
steps:
  1. land on /register

## Screens

### SCR-1 — "register"
route: /register

### SCR-9 — "lonely"
route: /lonely
EOF
out=$(sh "$CDF" "$_scr/PRD.md" "$_scr/AF_untouched.md" 2>&1); ec=$?
assert_eq "1" "$ec" "df-10c: untouched screen fails without --allow-unlinked"
assert_contains "$out" "SCREEN_UNTOUCHED" "df-10c: names the untouched screen"
out=$(sh "$CDF" "$_scr/PRD.md" "$_scr/AF_untouched.md" --allow-unlinked 2>&1); ec=$?
assert_eq "0" "$ec" "df-10c: untouched screen deferred by --allow-unlinked"
assert_contains "$out" "note: SCREEN_UNTOUCHED deferred" "df-10c: deferral is loud"
# (d) prefixed SCR ids pass
sed 's/SCR-1 /SCR-SMS-1 /' "$_pfx/APP_FLOW.md" > "$_scr/AF_pfx.md"
out=$(sh "$CDF" "$_scr/PRD.md" "$_scr/AF_pfx.md" 2>&1); ec=$?
assert_eq "0" "$ec" "df-10d: prefixed SCR-SMS ids pass"

rm -rf "$_t"
