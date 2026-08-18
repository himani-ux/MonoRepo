# shellcheck shell=sh
# doc-coherence_test.sh — framework-coherence locks (review C5).
#
# journey-gen's doc-format contract is only real if the Step 1 / Step 2
# prompts actually tell the user to produce conforming docs. These checks
# lock the contract tokens into the root prompts so a future edit cannot
# silently reintroduce the drift (must/should/nice tables, no AFJ section).

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$TESTS_DIR/../.."
S1="$ROOT/Step 1.txt"
S2="$ROOT/Step 2.txt"

if [ ! -f "$S1" ] || [ ! -f "$S2" ]; then
  printf 'FAIL: Step 1.txt / Step 2.txt not found at repo root\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
else
  _s1=$(cat "$S1"); _s2=$(cat "$S2")

  # Step 1: P0..P3 vocabulary + AC labels in the summary table
  assert_contains "$_s1" "P0 / P1 / P2 / P3" "Step 1: summary table records priority as P0..P3"
  assert_not_contains "$_s1" "| must / should / nice |" "Step 1: must/should/nice no longer a table value"
  assert_contains "$_s1" "AC-1:" "Step 1: acceptance criteria carry AC-<n> labels"

  # Step 2: PRD FEAT-block + APP_FLOW User Journeys contracts present
  assert_contains "$_s2" "journey-gen-doc-format.md" "Step 2: names the doc-format contract"
  assert_contains "$_s2" '## FEAT-001' "Step 2: shows the machine-readable FEAT block"
  assert_contains "$_s2" "P0 | P1 | P2 | P3" "Step 2: FEAT priority enum stated exactly"
  assert_contains "$_s2" "## User Journeys" "Step 2: requires the APP_FLOW User Journeys section"
  assert_contains "$_s2" "AFJ-001" "Step 2: shows the AFJ heading format"
  assert_contains "$_s2" "covers_features" "Step 2: states the AFJ→FEAT link key"
  assert_contains "$_s2" "check-doc-format.sh" "Step 2: points at the preflight verifier"
fi

  # Step 1: Domain 12 persona contract (Increment 3)
  assert_contains "$_s1" "## Domain 12: Personas & Journeys" "Step 1: Domain 12 exists"
  assert_contains "$_s1" "patience_budget" "Step 1: captures patience_budget (simulator-bound, not consumed)"
  assert_contains "$_s1" "known_misbehaviors" "Step 1: captures known_misbehaviors"
  assert_contains "$_s1" "(misbehavior: " "Step 1: journeys annotate misbehavior steps"
  assert_contains "$_s1" "origin: PERSONA" "Step 1: persona journeys carry origin PERSONA"
  assert_contains "$_s1" "PERSONA_COVERAGE_GAPS.md" "Step 1: uncovered features get persona gaps"
  assert_not_contains "$_s1" "persona-selfcheck" "Step 1: Domain 12 no longer runs the self-check (capture-only; B-02)"
  assert_contains "$_s2" "persona-selfcheck.sh docs/PERSONAS.md docs/PRD.md JOURNEY_MAP.md docs/PERSONA_COVERAGE_GAPS.md" "Step 2: Domain 12 handoff closes with the self-check over generated docs/ paths (B-02)"
  assert_contains "$_s1" "not tested behavior" "Step 1: core invariant stated"
