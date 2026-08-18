# shellcheck shell=sh
. "$(dirname "$0")/assert.sh"
. "$(dirname "$0")/../lib/journey-lib.sh"

JOURNEY_MAP="$(dirname "$0")/fixtures/good/JOURNEY_MAP.md"
export JOURNEY_MAP

ids="$(journey_ids | tr '\n' ',')"
assert_eq "JOURNEY-001," "$ids" "journey_ids lists the one example id"

assert_eq "P0" "$(journey_field JOURNEY-001 priority)" "journey_field reads priority"
assert_eq "tests/journeys/journey-001.spec.ts" "$(journey_field JOURNEY-001 test)" "journey_field reads test path"
assert_contains "$(journey_block JOURNEY-001)" "origin:" "journey_block returns the whole block"
assert_exit 1 journey_field JOURNEY-001 nonexistent_key

# ── Multi-block isolation tests ──────────────────────────────────────────────
JOURNEY_MAP="$(dirname "$0")/fixtures/multiblock/JOURNEY_MAP.md"
export JOURNEY_MAP

# JOURNEY-001 block must not bleed into JOURNEY-002
assert_not_contains "$(journey_block JOURNEY-001)" "JOURNEY-002" \
  "journey_block JOURNEY-001 does not contain JOURNEY-002 (no bleed)"

# JOURNEY-002 fields are readable independently
assert_eq "P1" "$(journey_field JOURNEY-002 priority)" \
  "journey_field JOURNEY-002 priority returns P1 (trimmed, proves trailing-ws fix)"
assert_eq "second goal distinct from the first journey" \
  "$(journey_field JOURNEY-002 goal)" \
  "journey_field JOURNEY-002 goal returns JOURNEY-002 value independently"
assert_eq "tests/journeys/journey-002.spec.ts" \
  "$(journey_field JOURNEY-002 test)" \
  "journey_field JOURNEY-002 test path is independent of JOURNEY-001"

# ids from multiblock fixture lists both journeys
mb_ids="$(journey_ids | tr '\n' ',')"
assert_eq "JOURNEY-001,JOURNEY-002," "$mb_ids" \
  "journey_ids lists both blocks in multiblock fixture"

# ── Template contract tests ───────────────────────────────────────────────────
TEMPLATE="$(dirname "$0")/../JOURNEY_MAP.template.md"
JOURNEY_MAP="$TEMPLATE"; export JOURNEY_MAP

assert_eq "JOURNEY-000" "$(journey_ids | head -n1)" \
  "template ships an example JOURNEY-000"
assert_eq "UI+API" "$(journey_field JOURNEY-000 oracle_surface)" \
  "template example has oracle_surface"

# Forbidden runtime-truth fields must NOT appear as keys in the template
assert_exit 1 grep -qE \
  '^(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):' \
  "$TEMPLATE"

# ── norm_covers / norm_oracle — shared dedup normalization helpers, used by
# both journey-inbox-triage.sh and journey-reality-intake.sh. Direct unit
# proofs of the two properties their callers rely on: sort -u dedup (V-T2
# F1 / L15) and whitespace-run collapse. ─────────────────────────────────────
assert_eq "FEAT-001," "$(norm_covers "FEAT-001, FEAT-001")" \
  "norm_covers: a repeated token collapses to the same single-token set (L15)"
assert_eq "FEAT-001,FEAT-002," "$(norm_covers "FEAT-002,  FEAT-001 ")" \
  "norm_covers: sorts and trims distinct tokens"
assert_eq "value=1 AND stuff=2" "$(norm_oracle "value=1   AND  stuff=2")" \
  "norm_oracle: collapses runs of whitespace to a single space"
assert_eq "trimmed" "$(norm_oracle "  trimmed  ")" \
  "norm_oracle: trims leading/trailing whitespace"
