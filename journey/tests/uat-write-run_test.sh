# uat-write-run_test.sh — opt-in report-WRITER runner
# (journey/gen/runners/uat-write-run.sh, journey/gen/prompts/uat-writer.md,
# spec DC-7). Mirrors uat-runner_test.sh's own fixture/harness idioms for
# the verify-run side of this layer. Unique prefix: _uwr_.
# shellcheck shell=sh
. "$(dirname "$0")/assert.sh"
. "$(dirname "$0")/../lib/uat-lib.sh"

_uwr_tmp="$(mktemp -d)"
_uwr_runner="journey/gen/runners/uat-write-run.sh"
_uwr_stub="journey/tests/fixtures/uat/stub-writer-backend.sh"
_uwr_stub_badcommit="journey/tests/fixtures/uat/stub-writer-badcommit.sh"
_uwr_stub_badclaim="journey/tests/fixtures/uat/stub-writer-badclaim.sh"
_uwr_stub_fakehash="journey/tests/fixtures/uat/stub-writer-fakehash.sh"
_uwr_stub_oracle_nomap="journey/tests/fixtures/uat/stub-writer-oracle-nomap.sh"
_uwr_stub_oracle_inscope="journey/tests/fixtures/uat/stub-writer-oracle-inscope.sh"
_uwr_stub_failed="journey/tests/fixtures/uat/stub-writer-failed.sh"

# Own prefixed copy of uat-runner_test.sh's fixture-repo builder (same
# shape — the stub's claim bodies cite the identical paths/lines).
_uwr_mk_repo() { # $1=dir ; echoes HEAD sha
  ( cd "$1" && git init -q . && git config user.email t@t && git config user.name t
    mkdir -p src/pda docs src config src/auth
    printf 'line1\nline2\n// context\nline4\nline5\nline6\nline7\nline8\nline9\nline10\nline11\nthrow new Error('"'"'portal timeout'"'"')\n' > src/pda/send.ts
    printf '1\n2\n3\n4\n5\n6\n7\ninvoices can be exported as CSV\n' > docs/PRD.md
    { i=1; while [ $i -le 21 ]; do printf 'x%s\n' "$i"; i=$((i+1)); done
      printf "if (fmt === 'csv') reject()\n"; } > src/export.ts
    printf 'no bypass here\n' > config/auth.ts
    git add -A && git commit -qm fixture && git rev-parse HEAD )
}

_uwr_repo="$_uwr_tmp/repo"; mkdir -p "$_uwr_repo"
_uwr_commit="$(_uwr_mk_repo "$_uwr_repo")"

# One shared evidence SOURCE dir — the runner only ever reads/copies from
# it, never mutates it, so every subtest below can point EVIDENCE_DIR at
# the same directory safely.
_uwr_evsrc="$_uwr_tmp/evidence-src"; mkdir -p "$_uwr_evsrc"
printf 'fake-png\n' > "$_uwr_evsrc/journey-106-send-500.png"
printf 'fake-png-2\n' > "$_uwr_evsrc/journey-114-save-error.png"

# Shared notes file — stub backends ignore its content (deterministic test
# doubles), so one file suffices everywhere it's needed.
_uwr_notes="$_uwr_tmp/notes.txt"
cat > "$_uwr_notes" <<'EOF'
Session: PDA send flow.
Clicked Send on the PDA screen; the app returned HTTP 500 to the browser.
Captured as evidence/journey-106-send-500.png.
Searched for a dev-auth bypass: grep -rFn -- "PORTAL_MAGIC_BYPASS" config/
found nothing.
Tested against http://127.0.0.1:3002.
EOF

# Oracle-scope archetype map — mirrors uat-oracle-scope_test.sh's own
# JOURNEY_MAP_full fixture exactly (JOURNEY-101, clause 1 = lower/hash
# integrity, clause 2 = browser/row visibility) so the SAME claim content
# is legitimately in-scope against clause #2 and out-of-scope against
# clause #1.
_uwr_map="$_uwr_tmp/JOURNEY_MAP.md"
cat > "$_uwr_map" <<'EOF'
# JOURNEY_MAP — oracle-scope archetype (with oracle_classes declared)

## JOURNEY-101 — "Invoice hash integrity visible in list"
origin:          PERSONA
persona:         P2 (impatient ops user)
goal:            confirm an uploaded invoice's hash matches the source manifest and the row is visible
priority:        P0
covers:          FEAT-101
flows:           AF-3
oracle_surface:  UI+API
negative_states: schema_error
data_fixtures:
steps:
  1. land on /invoices            (state: AUTHENTICATED, EMPTY list)
  2. upload corrected.csv          → inject schema_error
  3. observe row appear in /invoices
oracle:          invoice hash matches source manifest AND row visible in /invoices
oracle_classes:  lower AND browser
evidence:        []
test:            tests/journeys/journey-101.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
EOF
assert_exit 0 sh journey/bin/lint-journey-map.sh "$_uwr_map"

_uwr_run() { # env-prefixed helper: $1..$4 are the positional args
  RUN_LLM_GEN=1 /bin/sh "$_uwr_runner" "$1" "$2" "$3" "$4"
}

# ── (a) RUN_LLM_GEN unset -> exit 0, SKIP message, nothing written ────────
_d="$_uwr_tmp/skip"; mkdir -p "$_d"
unset RUN_LLM_GEN JOURNEY_GEN_BACKEND REPORT_DATE JOURNEY_MAP
out="$(/bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "0" "$rc" "runner: RUN_LLM_GEN unset -> exit 0"
assert_contains "$out" "SKIP" "runner: SKIP message present"
[ ! -f "$_d/UAT_REPORT_2026-07-08.md" ]; assert_eq "0" "$?" "runner: no report when skipped"

# ── (b) RUN_LLM_GEN=1 without JOURNEY_GEN_BACKEND -> fail closed ─────────
out="$(RUN_LLM_GEN=1 /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: RUN_LLM_GEN=1 without backend -> exit 1"
[ ! -f "$_d/UAT_REPORT_2026-07-08.md" ]; assert_eq "0" "$?" "runner: no report (backend unset)"

# ── (c) bad REPORT_DATE fails EARLY — booby-trap backend proves no call ──
_d="$_uwr_tmp/baddate"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub" REPORT_DATE="08-07-2026" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: malformed REPORT_DATE -> exit 1"
assert_contains "$out" "DATE_INVALID" "runner: names DATE_INVALID"
[ ! -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked on malformed REPORT_DATE"
[ ! -f "$_d/UAT_REPORT_08-07-2026.md" ]; assert_eq "0" "$?" "runner: nothing written on malformed REPORT_DATE"

_d="$_uwr_tmp/nodate"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: unset REPORT_DATE -> exit 1"
assert_contains "$out" "DATE_INVALID" "runner: unset REPORT_DATE names DATE_INVALID"
[ ! -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked on unset REPORT_DATE"

# F-DATE (bounds check, not full calendar): a digit-shape-only regex used to
# accept calendar-impossible month/day (e.g. 2026-13-45); the runner never
# derives dates itself, so this must fail closed here, before any backend
# call, same as (c) above.
_d="$_uwr_tmp/dateoob"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub" REPORT_DATE="2026-13-45" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: calendar-out-of-bounds REPORT_DATE (month 13) -> exit 1"
assert_contains "$out" "DATE_INVALID" "runner: month-13 REPORT_DATE names DATE_INVALID"
[ ! -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked on month-13 REPORT_DATE"

_d="$_uwr_tmp/datezero"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub" REPORT_DATE="2026-00-00" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: calendar-out-of-bounds REPORT_DATE (00-00) -> exit 1"
assert_contains "$out" "DATE_INVALID" "runner: 00-00 REPORT_DATE names DATE_INVALID"
[ ! -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked on 00-00 REPORT_DATE"

# ── (d) dirty tree fails before backend ───────────────────────────────────
_d="$_uwr_tmp/dirty"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
_dirtyrepo="$_d/repo-dirty"; cp -R "$_uwr_repo" "$_dirtyrepo"
printf 'uncommitted\n' >> "$_dirtyrepo/src/pda/send.ts"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub" REPORT_DATE="2026-07-08" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_dirtyrepo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: dirty tree -> exit 1"
assert_contains "$out" "TREE_DIRTY" "runner: names TREE_DIRTY"
[ ! -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked on TREE_DIRTY"
[ ! -f "$_d/UAT_REPORT_2026-07-08.md" ]; assert_eq "0" "$?" "runner: nothing written on TREE_DIRTY"

# ── (d2) REPO_ROOT not a usable git repo -> REPO_MISMATCH, no backend call
_d="$_uwr_tmp/notrepo"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
_notrepo="$_d/plain-dir"; mkdir -p "$_notrepo"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub" REPORT_DATE="2026-07-08" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_notrepo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: REPO_ROOT not a git repo -> exit 1"
assert_contains "$out" "REPO_MISMATCH" "runner: names REPO_MISMATCH (not a git repo)"
[ ! -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked when REPO_ROOT is not a git repo"

# ── (e) golden happy path -> exit 0, both final files written, evidence
#    installed, lint+evidence gates green STANDALONE afterwards ──────────
_d="$_uwr_tmp/happy"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub" REPORT_DATE="2026-07-08" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "0" "$rc" "runner: happy path exit 0"
[ -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend was invoked on the happy path"
_rep="$_d/UAT_REPORT_2026-07-08.md"
[ -f "$_rep" ]; assert_eq "0" "$?" "runner: report file written"
[ -f "$_d/UAT_REPORT_2026-07-08.writer-raw.md" ]; assert_eq "0" "$?" "runner: writer-raw audit file written"
_first="$(head -1 "$_rep")"
assert_eq "# UAT-REPORT" "$_first" "runner: installed report's first line is the header token"
_hdate="$(uat_header_field "$_rep" report_date)"
assert_eq "2026-07-08" "$_hdate" "runner: installed report echoes runner's REPORT_DATE"
_hcommit="$(uat_header_field "$_rep" repo_commit)"
assert_eq "$_uwr_commit" "$_hcommit" "runner: installed report echoes runner's own repo_commit (HEAD)"
[ -f "$_d/evidence/journey-106-send-500.png" ]; assert_eq "0" "$?" "runner: evidence file installed alongside report"
[ -f "$_d/evidence/journey-114-save-error.png" ]; assert_eq "0" "$?" "runner: second evidence file installed alongside report"

out2="$(/bin/sh journey/bin/lint-uat-report.sh "$_rep" 2>&1)"; rc2=$?
assert_eq "0" "$rc2" "runner: installed report passes lint-uat-report.sh standalone"
out3="$(/bin/sh journey/bin/check-uat-evidence.sh "$_rep" "$_uwr_repo" 2>&1)"; rc3=$?
assert_eq "0" "$rc3" "runner: installed report passes check-uat-evidence.sh standalone"

# no leftover scratch dotfiles/dirs
_scratchleft="$(find "$_d" -maxdepth 1 -name '.uat-write-*')"
assert_eq "" "$_scratchleft" "runner: no leftover scratch temp/dir after success"

# ── (f) header echo mismatch (model invents repo_commit) -> no final
#    files, sentinel present (the runner only detects this AFTER the
#    backend already ran) ─────────────────────────────────────────────────
_d="$_uwr_tmp/echo-mismatch"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub_badcommit" REPORT_DATE="2026-07-08" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: echoed repo_commit mismatch -> exit 1"
assert_contains "$out" "REPO_MISMATCH" "runner: names REPO_MISMATCH (echo mismatch)"
[ -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend WAS invoked (echo-mismatch reaches the backend)"
[ ! -f "$_d/UAT_REPORT_2026-07-08.md" ]; assert_eq "0" "$?" "runner: nothing written on echo mismatch"
[ ! -f "$_d/UAT_REPORT_2026-07-08.writer-raw.md" ]; assert_eq "0" "$?" "runner: no writer-raw on echo mismatch"

# ── (g) lint-invalid model output (missing claim line) -> no final files ─
_d="$_uwr_tmp/lint-invalid"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub_badclaim" REPORT_DATE="2026-07-08" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: lint-invalid model output -> exit 1"
assert_contains "$out" "HEADER_MISSING" "runner: pass-through of lint-uat-report.sh's own code (missing claim line)"
[ -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend WAS invoked (lint-invalid reaches the backend)"
[ ! -f "$_d/UAT_REPORT_2026-07-08.md" ]; assert_eq "0" "$?" "runner: nothing written on lint failure"

# ── (h) artifact evidence hash NOT in the manifest -> evidence gate fails,
#    no final files ────────────────────────────────────────────────────────
_d="$_uwr_tmp/fakehash"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub_fakehash" REPORT_DATE="2026-07-08" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: invented artifact hash -> exit 1"
assert_contains "$out" "ARTIFACT_HASH_MISMATCH" "runner: pass-through of check-uat-evidence.sh's own code"
[ -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend WAS invoked (fakehash reaches the backend)"
[ ! -f "$_d/UAT_REPORT_2026-07-08.md" ]; assert_eq "0" "$?" "runner: nothing written on evidence failure"

# ── (i) oracle_clause ref present but JOURNEY_MAP unset -> fail closed ───
_d="$_uwr_tmp/oracle-nomap"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub_oracle_nomap" REPORT_DATE="2026-07-08" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: oracle_clause ref without JOURNEY_MAP -> exit 1"
assert_contains "$out" "JOURNEY_MAP" "runner: message names the missing JOURNEY_MAP precondition"
assert_contains "$out" "fail closed" "runner: message states fail-closed posture"
[ -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend WAS invoked (oracle-nomap reaches the backend)"
[ ! -f "$_d/UAT_REPORT_2026-07-08.md" ]; assert_eq "0" "$?" "runner: nothing written when oracle_clause ref has no map"

# ── (j) oracle_clause ref WITH JOURNEY_MAP set, browser-classed clause ──
#    -> exit 0, positive composition proof (check-uat-oracle-scope.sh
#    actually runs and passes, not merely "not invoked") ─────────────────
_d="$_uwr_tmp/oracle-inscope"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub_oracle_inscope" REPORT_DATE="2026-07-08" JOURNEY_MAP="$_uwr_map" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "0" "$rc" "runner: oracle_clause ref with JOURNEY_MAP + browser clause -> exit 0"
[ -f "$_d/UAT_REPORT_2026-07-08.md" ]; assert_eq "0" "$?" "runner: report written (oracle in-scope)"
_ocgate="$(/bin/sh journey/bin/check-uat-oracle-scope.sh "$_d/UAT_REPORT_2026-07-08.md" "$_uwr_map" 2>&1)"; _ocrc=$?
assert_eq "0" "$_ocrc" "runner: installed report passes check-uat-oracle-scope.sh standalone"

# lower-classed clause, same map, must still be rejected — proves the
# runner's composition doesn't just check "a map was given" but really
# gates on adjudicated scope.
_d="$_uwr_tmp/oracle-outscope"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub_oracle_nomap" REPORT_DATE="2026-07-08" JOURNEY_MAP="$_uwr_map" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: oracle_clause ref against a lower clause, map set -> exit 1 (false-gap killer)"
assert_contains "$out" "ORACLE_CLASS_OUT_OF_SCOPE" "runner: pass-through of check-uat-oracle-scope.sh's own code"
[ ! -f "$_d/UAT_REPORT_2026-07-08.md" ]; assert_eq "0" "$?" "runner: nothing written on out-of-scope oracle claim"

# ── (k) WRITER-FAILED -> loud exit 1, nothing written ─────────────────────
_d="$_uwr_tmp/writer-failed"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub_failed" REPORT_DATE="2026-07-08" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: WRITER-FAILED -> exit 1"
assert_contains "$out" "WRITER-FAILED" "runner: names WRITER-FAILED"
[ -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend WAS invoked (WRITER-FAILED reaches the backend)"
[ ! -f "$_d/UAT_REPORT_2026-07-08.md" ]; assert_eq "0" "$?" "runner: nothing written on WRITER-FAILED"

# ── (l) TOOL_MISSING — no sha256 tool on PATH fails closed during
#    manifest-building, BEFORE the backend is ever invoked (same PATH-shim
#    idiom as journey/tests/uat-evidence_test.sh's own TOOL_MISSING proof:
#    symlink every non-sha binary needed, deliberately omit
#    sha256sum/shasum) ──────────────────────────────────────────────────
_d="$_uwr_tmp/tool-missing"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
_uwr_shim="$_uwr_tmp/shim"; mkdir -p "$_uwr_shim"
for _b in git awk sed grep tr head sort uniq cat mktemp dirname basename rm wc find cp mkdir; do
  _real="$(command -v "$_b")" && ln -s "$_real" "$_uwr_shim/$_b"
done
out="$(PATH="$_uwr_shim" RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub" REPORT_DATE="2026-07-08" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: no sha256 tool on PATH -> exit 1"
assert_contains "$out" "TOOL_MISSING" "runner: names TOOL_MISSING"
[ ! -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked when sha256 tool is missing"
[ ! -f "$_d/UAT_REPORT_2026-07-08.md" ]; assert_eq "0" "$?" "runner: nothing written when sha256 tool is missing"

# ── (m) missing NOTES_FILE / EVIDENCE_DIR -> plain usage-style failure,
#    before any backend call ──────────────────────────────────────────────
_d="$_uwr_tmp/missing-notes"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub" REPORT_DATE="2026-07-08" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_d/no-such-notes.txt" "$_uwr_evsrc" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: missing notes file -> exit 1"
[ ! -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked when notes file is missing"

_d="$_uwr_tmp/missing-evdir"; mkdir -p "$_d"; _sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_uwr_stub" REPORT_DATE="2026-07-08" UAT_STUB_SENTINEL="$_sentinel" \
  /bin/sh "$_uwr_runner" "$_uwr_notes" "$_d/no-such-evidence" "$_uwr_repo" "$_d" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: missing evidence dir -> exit 1"
[ ! -f "$_sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked when evidence dir is missing"

# ── Task-mirrored doc-coherence spot check: the §8 amendment names the
#    prompt + runner paths and states the writer's authority boundary
#    (mirrors the style of the existing uat-report-format.md lock in
#    journey/tests/uat-report-lint_test.sh — this is a light-touch,
#    same-commit companion check for the T7-specific prose, not a
#    duplicate of that lock). No new gate codes are asserted here because
#    this runner mints none (see uat-write-run.sh's own header comment).
_uwr_doc="journey/docs/uat-report-format.md"
if [ ! -f "$_uwr_doc" ]; then
  printf 'FAIL: uat-report-format.md missing: %s\n' "$_uwr_doc"
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
else
  _uwr_docd="$(cat "$_uwr_doc")"
  assert_contains "$_uwr_docd" "uat-writer.md" "doc §8: names the writer prompt"
  assert_contains "$_uwr_docd" "uat-write-run.sh" "doc §8: names the writer runner"
  assert_contains "$_uwr_docd" "WRITER-FAILED" "doc: documents the writer's own degenerate token"
  assert_contains "$_uwr_docd" "the writer never verifies" "doc §8: states the writer's authority boundary, verbatim"
fi

rm -rf "$_uwr_tmp"
