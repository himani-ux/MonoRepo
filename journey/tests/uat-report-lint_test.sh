# uat-report-lint_test.sh — gate 4.1 schema lint
uat_lint_dir="journey/tests/fixtures/uat"
uat_lint_tmp="$(mktemp -d)"

# golden passes
out="$(/bin/sh journey/bin/lint-uat-report.sh "$uat_lint_dir/golden/UAT_REPORT_2026-07-08.md" 2>&1)"; rc=$?
assert_eq "0" "$rc" "lint: golden report is clean"

# red matrix: each case = sed mutation of golden -> expected CODE
uat_lint_red() { # $1=name $2=sed-script $3=expected-code [$4=dest-name]
  _dst="$uat_lint_tmp/${4:-UAT_REPORT_2026-07-08.md}"
  sed "$2" "$uat_lint_dir/golden/UAT_REPORT_2026-07-08.md" > "$_dst"
  _out="$(/bin/sh journey/bin/lint-uat-report.sh "$_dst" 2>&1)"; _rc=$?
  assert_eq "1" "$_rc" "lint red rc: $1"
  assert_contains "$_out" "$3" "lint red code: $1"
}
uat_lint_red header-missing  '/^repo_commit:/d'                          HEADER_MISSING
uat_lint_red commit-short    's/^repo_commit: .*/repo_commit: abc123/'   HEADER_MISSING
uat_lint_red date-bad        's/^report_date: .*/report_date: 08-07-2026/' DATE_INVALID
uat_lint_red date-filename   's/^report_date: .*/report_date: 2026-07-09/' DATE_INVALID
# F-DATE (bounds check, not full calendar): digit-shape-only regex used to
# accept calendar-impossible month/day. Filename renamed to MATCH the
# mutated date so the failure is isolated to the date-bounds check itself
# (line 27), not the filename-mismatch check (line 29-30) -- pre-fix these
# two cases passed the whole lint (rc 0), reproduced by hand.
uat_lint_red date-month-oob  's/^report_date: .*/report_date: 2026-13-45/' DATE_INVALID UAT_REPORT_2026-13-45.md
uat_lint_red date-zero       's/^report_date: .*/report_date: 2026-00-00/' DATE_INVALID UAT_REPORT_2026-00-00.md
uat_lint_red grade-unknown   's/- grade: \[C\]$/- grade: [Z]/'           GRADE_UNKNOWN
uat_lint_red dup-claim-id    's/^## UAT-CLAIM-2:/## UAT-CLAIM-1:/'       DUPLICATE_CLAIM_ID
uat_lint_red no-evidence     '/^- evidence: src\/pda\/send.ts/d;/^- evidence: artifact evidence\/journey-106-send-500.png/d' CLAIM_NO_EVIDENCE
uat_lint_red x-one-sided     '/^- evidence: docs\/PRD.md/d'               CONTRADICTION_ONE_SIDED
uat_lint_red absent-nosearch '/^- search: /d'                             ABSENCE_NO_SEARCH
uat_lint_red sample-missing  '/^- sample: /d'                             SAMPLE_MISSING
uat_lint_red sample-small    's/^- sample: 4 instances/- sample: 2 instances/' SAMPLE_TOO_SMALL
uat_lint_red evidence-format 's|^- evidence: src/pda/send.ts:12 — |- evidence: src/pda/send.ts;12 — |' EVIDENCE_FORMAT
uat_lint_red empty-quote     's|^- evidence: src/pda/send.ts:12 — .*|- evidence: src/pda/send.ts:12 — ""|' EVIDENCE_FORMAT
uat_lint_red search-regex    's/grep -rFn -- "PORTAL_MAGIC/grep -rEn -- "PORTAL_MAGIC/' SEARCH_FORMAT
uat_lint_red search-dotdot   's|" config/|" ../config/|'                  SEARCH_FORMAT

# NO_CLAIMS: header-only file
printf '# UAT-REPORT\nreport_date: 2026-07-08\nrepo_commit: %s\napp_target: http://x\n' \
  "0123456789012345678901234567890123456789" > "$uat_lint_tmp/UAT_REPORT_2026-07-08.md"
out="$(/bin/sh journey/bin/lint-uat-report.sh "$uat_lint_tmp/UAT_REPORT_2026-07-08.md" 2>&1)"; rc=$?
assert_eq "1" "$rc" "lint red rc: no-claims"
assert_contains "$out" "NO_CLAIMS" "lint red code: no-claims"

rm -rf "$uat_lint_tmp"

# ── Task 8: doc-coherence lock — journey/docs/uat-report-format.md must stay
# coherent with the shipped gates (spec §8 T8; HARD-STOP-A phase review's
# documentation duties). Codes below are read straight from each gate's own
# header-comment enumeration (the authoritative source per gate), not
# transcribed from the plan — deduped across gates where the same code is
# reused (SEARCH_FORMAT/ABSENCE_NO_SEARCH/COMMIT_UNKNOWN/TOOL_MISSING each
# appear in more than one gate's own list).
uat_dc_doc="journey/docs/uat-report-format.md"
if [ ! -f "$uat_dc_doc" ]; then
  printf 'FAIL: uat-report-format.md missing: %s\n' "$uat_dc_doc"
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
  uat_dc_d=""
else
  printf 'ok: uat-report-format.md exists\n'
  uat_dc_d="$(cat "$uat_dc_doc")"
fi

# grammar tokens, verbatim
assert_contains "$uat_dc_d" '## UAT-CLAIM-<n>: <title>'   "doc: claim block header token"
assert_contains "$uat_dc_d" 'UAT-VERDICT: UAT-CLAIM-<n>'  "doc: verdict block header token"
assert_contains "$uat_dc_d" 'reviewed_sha256:'            "doc: verification first-line field"
assert_contains "$uat_dc_d" 'grep -rFn -- "<literal>" <relpath>' "doc: search-line grammar token"

# mandatory verbatim sentences (doc-coherence assertions per the brief)
assert_contains "$uat_dc_d" 'hash-consistent, gate-clean, human-approved' \
  "doc: what green means, verbatim (spec §6)"
assert_contains "$uat_dc_d" 'Browser UAT observations are evidence only' \
  "doc: runtime-truth-untouched sentence, verbatim"
assert_contains "$uat_dc_d" 'pinned commit' "doc: pinned-commit rule present"
assert_contains "$uat_dc_d" 'uat_report: <path> sha256:<hash>' \
  "doc: consumer citation convention line"

# every error code emitted by the five gates + runner (authoritative
# enumeration: each gate's own header-comment code list) — deduped.
for uat_dc_code in \
  HEADER_MISSING DATE_INVALID NO_CLAIMS DUPLICATE_CLAIM_ID GRADE_UNKNOWN \
  CLAIM_NO_EVIDENCE CONTRADICTION_ONE_SIDED ABSENCE_NO_SEARCH SAMPLE_MISSING \
  SAMPLE_TOO_SMALL EVIDENCE_FORMAT SEARCH_FORMAT \
  COMMIT_UNKNOWN QUOTE_UNVERIFIED LINE_MISMATCH ARTIFACT_MISSING \
  ARTIFACT_HASH_MISMATCH SEARCH_ERROR SEARCH_DIVERGED TOOL_MISSING \
  STALE_VERIFICATION VERDICT_INCOMPLETE DUPLICATE_VERDICT UNKNOWN_CLAIM \
  VERDICT_UNKNOWN REGRADE_MISSING RESIDUAL_ON_CONFIRM \
  VERIFICATION_MISSING NON_CONFIRM_VERDICT NO_EVIDENCED_CLAIMS \
  PROMOTION_MISSING PROMOTION_STALE \
  MISSING-REPORT REPO_MISMATCH TREE_DIRTY MKTEMP_FAILED WRITE_FAILED BACKEND_FAILED \
  LINT_FAILED NO_PRECONDITIONS PRECONDITION_ENV_UNSET PROBE_MISSING PRECONDITION_UNMET \
  ORACLE_CLAUSE_FORMAT NO_CLAUSE_REFS ORACLE_CLAUSE_UNKNOWN_JOURNEY \
  ORACLE_CLAUSE_OUT_OF_RANGE ORACLE_CLASS_UNDECLARED ORACLE_CLASS_OUT_OF_SCOPE \
  ROOT_MISMATCH CITATION_MISSING \
; do
  assert_contains "$uat_dc_d" "$uat_dc_code" "doc: error code $uat_dc_code documented"
done

printf 'ok: uat-report-format.md doc-coherence lock complete\n'
