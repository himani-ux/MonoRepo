#!/bin/sh
# step5-wiring-coherence_test.sh — byte-locks the DC-6 Step 5 wiring
# amendment into Step 5.txt (spec 2026-07-10-simulator-reality-engines-goal.md
# DC-6; design 2026-06-22-journey-validation-layer-design.md §5.3 "Reality
# feedback" + §8 "Step 5" line). Model: journey/tests/step3-wiring-coherence_test.sh
# (assert_contains substring-anchor style — this amendment has no MARKER
# BEGIN/END pair of its own).
#
# Locks four things:
#   (a) Part B: the WORKFLOW BUG journey-granularity law (the five-condition
#       list) lands in Step 5.txt's <change_intake> block, verbatim
#   (b) Part B: the <goal> "Definition of done" text names the workflow-bug
#       journey requirement
#   (c) Part D: the Gate 2 extension — exact grep idioms + the teaching
#       rejection message — lands verbatim, and the PRE-EXISTING Gate 1 /
#       Gate 2 blocks are untouched (byte-lock on their literal lines)
#   (d) Part C: the drift-auditor JOURNEY DRIFT step composes the three
#       named executables, verbatim
#   (e) no phantom gates: every path the new text names actually exists
#
# Then (f) REAL execution of the extracted Part D hook script in a scratch
# git repo, proving the five hook-correctness scenarios from the T6 brief:
#   (a) JOURNEY-<n> ref + staged tests/journeys/ change -> accepted
#   (b) same ref, no journey-test staged -> rejected, teaching message shown
#   (c) rejected case + JOURNEY-EXEMPT: reason -> accepted
#   (d) WORKFLOW-BUG tag behaves identically (reject + accept sub-cases)
#   (e) an ordinary non-workflow fix: commit is untouched by the new gate
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$TESTS_DIR/../.."
S5="$ROOT/Step 5.txt"

_s5_nonzero() { # ACTUAL_CODE MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"
  else printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

if [ ! -f "$S5" ]; then
  printf 'FAIL: Step 5.txt not found at repo root\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
else
  _s5="$(cat "$S5")"

  # ── (a) Part B — WORKFLOW BUG journey-granularity law (Tier 1 ceremony) ──
  assert_contains "$_s5" "WORKFLOW BUG" "workflow-bug law is named"
  assert_contains "$_s5" "journey-granularity lift" "journey-granularity lift named (spec §5.3)"
  assert_contains "$_s5" "user-facing multi-step flow" "workflow-bug definition: user-facing multi-step flow"
  assert_contains "$_s5" "pure internal defect" "workflow-bug definition: contrast with pure internal defect"
  assert_contains "$_s5" "a JOURNEY-ID covering the failing workflow exists" \
    "condition 1: JOURNEY-ID must exist"
  assert_contains "$_s5" "sh journey/bin/journey-reality-intake.sh JOURNEY_MAP.md <entry-file> --approve" \
    "condition 1: exact reality-intake invocation named"
  assert_contains "$_s5" "origin REALITY, evidence carries the bug/incident refs" \
    "condition 1: origin + evidence law stated"
  assert_contains "$_s5" "JOURNEY-EXEMPT: <reason>" "condition 1: exemption tag grammar named"
  assert_contains "$_s5" "logged as debt" "condition 1: exemption logged as debt"
  assert_contains "$_s5" "owner + expiry" "condition 1: exemption carries owner + expiry"
  assert_contains "$_s5" "a deterministic journey test reproduces the bug or encodes the missing workflow" \
    "condition 2: deterministic journey test stated"
  assert_contains "$_s5" "the test fails before the fix" "condition 3: RED-first stated"
  assert_contains "$_s5" "technically impossible" "condition 3: technically-impossible escape hatch named"
  assert_contains "$_s5" "the test passes after the fix" "condition 4: GREEN-after stated"
  assert_contains "$_s5" "runtime truth for that journey lands only via the CI ledger" \
    "condition 5: CI ledger is the only runtime-truth path"
  assert_contains "$_s5" "the report/citation layer never marks anything green" \
    "condition 5: report layer cannot forge green"
  assert_contains "$_s5" "Test + fix commit together" "workflow-bug law: test + fix commit together"

  # ── (b) Part B — <goal> Definition of done names the journey requirement ─
  assert_contains "$_s5" "for a WORKFLOW BUG, a JOURNEY-ID exists (via reality-intake) or JOURNEY-EXEMPT is logged" \
    "goal: workflow-bug journey requirement stated"
  assert_contains "$_s5" "its journey regression test lands in the same commit" \
    "goal: journey regression test required in the same commit"

  # ── (c) Part D — Gate 2 extension ────────────────────────────────────────
  assert_contains "$_s5" "Gate 2 extension" "hook: Gate 2 extension is named"
  assert_contains "$_s5" "if echo \"\$MSG\" | grep -qE 'JOURNEY-[0-9]+' || echo \"\$MSG\" | grep -q 'WORKFLOW-BUG'; then" \
    "hook: exact detection idiom (JOURNEY-<n> ref OR WORKFLOW-BUG tag)"
  assert_contains "$_s5" "if ! echo \"\$STAGED\" | grep -q 'tests/journeys/'; then" \
    "hook: exact staged-path check idiom"
  assert_contains "$_s5" "if ! echo \"\$MSG\" | grep -q 'JOURNEY-EXEMPT:'; then" \
    "hook: exact exemption-tag check idiom"
  assert_contains "$_s5" "KLOSS GATE: commit references a JOURNEY-<n> workflow or is tagged WORKFLOW-BUG, but no tests/journeys/ change is staged." \
    "hook: exact rejection diagnostic"
  assert_contains "$_s5" "Stage the journey regression test, or add 'JOURNEY-EXEMPT: <reason>' (logged as debt)." \
    "hook: exact teaching message (mirrors TEST-EXEMPT message style)"

  # ── (c-ext) pre-existing Gate 1 / Gate 2 blocks byte-locked unmodified ───
  assert_contains "$_s5" '# Gate 1: code change must carry a progress.txt entry or an exemption tag
if ! echo "$STAGED" | grep -q '"'"'^progress.txt$'"'"'; then
  if ! echo "$MSG" | grep -q '"'"'DOCS-EXEMPT:'"'"'; then
    echo "KLOSS GATE: code changed but progress.txt is not in this commit."
    echo "Append the progress entry (schema in CLAUDE.md MAINTAIN MODE) and stage it,"
    echo "or add '"'"'DOCS-EXEMPT: <reason>'"'"' to this commit message (logged as debt)."
    exit 1
  fi
fi' "hook: Gate 1 block byte-identical to pre-T6"
  assert_contains "$_s5" '# Gate 2: bugfix commits carry a test change or an exemption tag
if echo "$MSG" | grep -qiE '"'"'\bfix(es|ed)?\b|\bbug\b'"'"'; then
  if ! echo "$STAGED" | grep -qiE '"'"'(test|spec)'"'"'; then
    if ! echo "$MSG" | grep -q '"'"'TEST-EXEMPT:'"'"'; then
      echo "KLOSS GATE: commit message says fix/bug but no test file is staged."
      echo "Stage the regression test, or add '"'"'TEST-EXEMPT: <reason>'"'"' (logged as debt)."
      exit 1
    fi
  fi
fi' "hook: Gate 2 block byte-identical to pre-T6"

  # ── (d) Part C — JOURNEY DRIFT step (composition, not re-implementation) ─
  assert_contains "$_s5" "JOURNEY_MAP ↔ tests ↔ TEST_SURFACE" "auditor: names the three-way coherence check (spec §8)"
  assert_contains "$_s5" "sh journey/bin/check-journeys.sh <conf> JOURNEY_MAP.md tests/journeys/" \
    "auditor: re-runs check-journeys.sh with its real CONF MAP TESTS_DIR positional args (V-T6 F1/P3)"
  assert_contains "$_s5" "three-source join" "auditor: names check-journeys.sh's three-source join"
  assert_contains "$_s5" "sh journey/bin/lint-journey-map.sh JOURNEY_MAP.md" "auditor: re-runs lint-journey-map.sh"
  assert_contains "$_s5" "where a TEST_SURFACE exists" "auditor: surface-staleness re-check is conditional"
  assert_contains "$_s5" "sh journey/bin/check-surface-staleness.sh TEST_SURFACE.md docs/APP_FLOW.md" \
    "auditor: re-runs check-surface-staleness.sh with its real TEST_SURFACE APP_FLOW positional args (V-T6 F1/P3)"
  assert_contains "$_s5" "Composing existing gates, never re-implementing" "auditor: composition-not-reimplementation stated"
  assert_contains "$_s5" "DRIFT finding" "auditor: journey drift files as a DRIFT finding"
  assert_contains "$_s5" "DRIFT_REPORT.md" "auditor: findings land in DRIFT_REPORT.md"
  assert_contains "$_s5" "same as the auditor's other findings" "auditor: journey drift treated like other findings"

  # ── numbering stayed internally consistent after the step-8 insertion ───
  assert_contains "$_s5" "step 9's waiver cleanup" "auditor preamble: waiver-cleanup step ref renumbered to 9"
fi

# ── (e) no phantom gates: every path the new text names must exist ────────
for _p in \
  "journey/bin/journey-reality-intake.sh" \
  "journey/bin/check-journeys.sh" \
  "journey/bin/lint-journey-map.sh" \
  "journey/bin/check-surface-staleness.sh" \
; do
  assert_exit 0 test -f "$ROOT/$_p"
done

# ═══════════════════════════════════════════════════════════════════════════
# (f) REAL hook execution — extract Part D's literal script and run it as an
# actual git commit-msg hook in a scratch repo (mktemp; temp+trap+cleanup).
# ═══════════════════════════════════════════════════════════════════════════

if [ -f "$S5" ] && command -v git >/dev/null 2>&1; then
  _s5_repo=$(mktemp -d "${TMPDIR:-/tmp}/s5-hook-XXXXXXXX")
  _s5_msgfile=$(mktemp "${TMPDIR:-/tmp}/s5-msg-XXXXXXXX")
  _s5_cleanup() { rm -rf "$_s5_repo" "$_s5_msgfile"; }
  trap '_s5_cleanup' EXIT INT TERM

  # Extract the literal Part D script: from its #!/bin/sh line through the
  # final "drift auditor is the final net" comment line, inclusive. Both
  # anchors are unique in Step 5.txt (verified: grep -c each == 1).
  awk '
    /^#!\/bin\/sh$/ { grab=1 }
    grab { print }
    /^# The drift auditor \(Part C\) is the final net behind both\.$/ { exit }
  ' "$S5" > "$_s5_repo/.extracted-hook"

  assert_exit 0 test -s "$_s5_repo/.extracted-hook"

  (
    cd "$_s5_repo" || exit 1
    git init -q .
    git config user.email "s5-hook-test@example.com"
    git config user.name "S5 Hook Test"
    git config commit.gpgsign false
    git config tag.gpgsign false
    mkdir -p .git/hooks
    cp .extracted-hook .git/hooks/commit-msg
    chmod +x .git/hooks/commit-msg

    # Baseline commit that neither gate touches (no CODE_PATHS file staged,
    # no fix/bug wording, no JOURNEY-<n>/WORKFLOW-BUG) — establishes a repo
    # history to commit against.
    mkdir -p docs
    printf 'init\n' > docs/README.md
    git add docs/README.md
    git commit -q -m "chore: scratch repo init" >/dev/null 2>&1
  )
  _s5_setup_rc=$?
  assert_eq "0" "$_s5_setup_rc" "hook harness: scratch repo + hook install succeeded"

  _s5_reset() { ( cd "$_s5_repo" && git reset -q >/dev/null 2>&1; git clean -qfd >/dev/null 2>&1 ); }

  # ── (a) JOURNEY-101 ref + staged tests/journeys/ change -> accepted ──────
  _s5_reset
  ( cd "$_s5_repo" && mkdir -p tests/journeys && printf 'spec a\n' > tests/journeys/journey-101.spec.ts && git add tests/journeys/journey-101.spec.ts )
  printf 'fix(app): JOURNEY-101 retry no longer double-submits\n' > "$_s5_msgfile"
  _s5_out=$( ( cd "$_s5_repo" && git commit -q -F "$_s5_msgfile" ) 2>&1 ); _s5_rc=$?
  assert_eq "0" "$_s5_rc" "(a) JOURNEY-101 ref + staged tests/journeys/ change -> accepted"

  # ── (b) same ref, no journey-test staged -> rejected, teaching message ──
  _s5_reset
  ( cd "$_s5_repo" && printf 'notes\n' > docs/notes-b.md && git add docs/notes-b.md )
  printf 'fix(app): JOURNEY-101 retry no longer double-submits\n' > "$_s5_msgfile"
  _s5_out=$( ( cd "$_s5_repo" && git commit -q -F "$_s5_msgfile" ) 2>&1 ); _s5_rc=$?
  _s5_nonzero "$_s5_rc" "(b) JOURNEY-101 ref, no journey-test staged -> rejected"
  assert_contains "$_s5_out" "Stage the journey regression test, or add 'JOURNEY-EXEMPT: <reason>'" \
    "(b) teaching message shown on rejection"

  # ── (c) rejected case + JOURNEY-EXEMPT: reason -> accepted ──────────────
  _s5_reset
  ( cd "$_s5_repo" && printf 'notes\n' > docs/notes-c.md && git add docs/notes-c.md )
  printf 'fix(app): JOURNEY-101 retry no longer double-submits\n\nJOURNEY-EXEMPT: manual QA only, unautomatable OTP step\n' > "$_s5_msgfile"
  _s5_out=$( ( cd "$_s5_repo" && git commit -q -F "$_s5_msgfile" ) 2>&1 ); _s5_rc=$?
  assert_eq "0" "$_s5_rc" "(c) JOURNEY-EXEMPT logged -> accepted"

  # ── (d) WORKFLOW-BUG tag behaves identically ─────────────────────────────
  _s5_reset
  ( cd "$_s5_repo" && printf 'notes\n' > docs/notes-d1.md && git add docs/notes-d1.md )
  printf 'fix(app): retry no longer double-submits\nWORKFLOW-BUG\n' > "$_s5_msgfile"
  _s5_out=$( ( cd "$_s5_repo" && git commit -q -F "$_s5_msgfile" ) 2>&1 ); _s5_rc=$?
  _s5_nonzero "$_s5_rc" "(d1) WORKFLOW-BUG tag, no journey test -> rejected"

  _s5_reset
  ( cd "$_s5_repo" && mkdir -p tests/journeys && printf 'spec d\n' > tests/journeys/journey-999.spec.ts && git add tests/journeys/journey-999.spec.ts )
  printf 'fix(app): retry no longer double-submits\nWORKFLOW-BUG\n' > "$_s5_msgfile"
  _s5_out=$( ( cd "$_s5_repo" && git commit -q -F "$_s5_msgfile" ) 2>&1 ); _s5_rc=$?
  assert_eq "0" "$_s5_rc" "(d2) WORKFLOW-BUG tag + journey test staged -> accepted"

  # ── (e) ordinary non-workflow commit: existing Gate 2 behavior untouched ─
  # e1: fix: + CODE_PATHS file + generic test file + progress.txt -> accepted
  #     (Gate 1 satisfied, Gate 2 satisfied via generic test/spec match; new
  #     gate never fires — no JOURNEY-<n>/WORKFLOW-BUG in the message).
  _s5_reset
  ( cd "$_s5_repo" && mkdir -p src tests/unit && printf 'x\n' > src/app.js && printf 'y\n' > tests/unit/app_test.js && printf 'progress\n' > progress.txt && git add src/app.js tests/unit/app_test.js progress.txt )
  printf 'fix: app no longer crashes on empty input\n' > "$_s5_msgfile"
  _s5_out=$( ( cd "$_s5_repo" && git commit -q -F "$_s5_msgfile" ) 2>&1 ); _s5_rc=$?
  assert_eq "0" "$_s5_rc" "(e1) plain fix: with generic test + progress.txt -> accepted (pre-existing Gate 1+2 behavior)"

  # e2: fix: + CODE_PATHS file, progress.txt, but NO test/spec anywhere ->
  #     rejected by the pre-existing Gate 2 (unchanged by this amendment).
  _s5_reset
  ( cd "$_s5_repo" && mkdir -p src && printf 'z\n' > src/app2.js && printf 'progress2\n' > progress.txt && git add src/app2.js progress.txt )
  printf 'fix: app no longer crashes on null input\n' > "$_s5_msgfile"
  _s5_out=$( ( cd "$_s5_repo" && git commit -q -F "$_s5_msgfile" ) 2>&1 ); _s5_rc=$?
  _s5_nonzero "$_s5_rc" "(e2) plain fix: with no test staged -> rejected (pre-existing Gate 2 behavior, unchanged)"
  assert_contains "$_s5_out" "Stage the regression test, or add 'TEST-EXEMPT: <reason>'" \
    "(e2) pre-existing Gate 2 teaching message unchanged"

  _s5_cleanup
  trap - EXIT INT TERM
else
  printf 'FAIL: hook-execution harness skipped (Step 5.txt or git missing)\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi
