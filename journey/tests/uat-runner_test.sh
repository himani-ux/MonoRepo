# uat-runner_test.sh — opt-in verify runner (journey/gen/runners/uat-verify-run.sh),
# spec §5.2 + phase-review guardrail M-T1-2 (existence check before uat_sha256).
# shellcheck shell=sh
. "$(dirname "$0")/assert.sh"
. "$(dirname "$0")/../lib/uat-lib.sh"

uat_rn_tmp="$(mktemp -d)"
uat_rn_fw_root="$(pwd)"
uat_rn_runner="journey/gen/runners/uat-verify-run.sh"
uat_rn_stub="journey/tests/fixtures/uat/stub-backend.sh"
uat_rn_badstub="journey/tests/fixtures/uat/stub-backend-badhash.sh"
uat_rn_missingrootstub="journey/tests/fixtures/uat/stub-backend-missingroot.sh"
uat_rn_rtpl="journey/tests/fixtures/uat/templates/UAT_REPORT_2026-07-08.md.in"

# Own prefixed copy of the citation test's fixture-repo builder (same
# shape — the golden verification cites the identical paths/lines).
uat_rn_mk_repo() { # $1=dir ; echoes HEAD sha
  ( cd "$1" && git init -q . && git config user.email t@t && git config user.name t
    mkdir -p src/pda docs src config src/auth
    printf 'line1\nline2\n// context\nline4\nline5\nline6\nline7\nline8\nline9\nline10\nline11\nthrow new Error('"'"'portal timeout'"'"')\n' > src/pda/send.ts
    printf '1\n2\n3\n4\n5\n6\n7\ninvoices can be exported as CSV\n' > docs/PRD.md
    { i=1; while [ $i -le 21 ]; do printf 'x%s\n' "$i"; i=$((i+1)); done
      printf "if (fmt === 'csv') reject()\n"; } > src/export.ts
    printf 'no bypass here\n' > config/auth.ts
    git add -A && git commit -qm fixture && git rev-parse HEAD )
}

uat_rn_repo="$uat_rn_tmp/repo"; mkdir -p "$uat_rn_repo"
uat_rn_commit="$(uat_rn_mk_repo "$uat_rn_repo")"

mkdir -p "$uat_rn_tmp/evidence"
printf 'fake-png\n' > "$uat_rn_tmp/evidence/journey-106-send-500.png"
printf 'fake-png-2\n' > "$uat_rn_tmp/evidence/journey-114-save-error.png"
uat_rn_artsha="$(uat_sha256 "$uat_rn_tmp/evidence/journey-106-send-500.png")"
uat_rn_artsha2="$(uat_sha256 "$uat_rn_tmp/evidence/journey-114-save-error.png")"

uat_rn_mk_report() { sed -e "s/@COMMIT@/$3/" -e "s/@ARTSHA@/$4/" -e "s/@ARTSHA2@/$5/" "$1" > "$2"; }

# ── (a) RUN_LLM_GEN unset -> exit 0, SKIP message, nothing written ────────
_d="$uat_rn_tmp/skip"; mkdir -p "$_d"; cp -R "$uat_rn_tmp/evidence" "$_d/evidence"
rep="$_d/UAT_REPORT_2026-07-08.md"
uat_rn_mk_report "$uat_rn_rtpl" "$rep" "$uat_rn_commit" "$uat_rn_artsha" "$uat_rn_artsha2"
unset RUN_LLM_GEN JOURNEY_GEN_BACKEND
out="$(/bin/sh "$uat_rn_runner" "$rep" "$uat_rn_repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "runner: RUN_LLM_GEN unset -> exit 0"
assert_contains "$out" "SKIP" "runner: SKIP message present"
[ ! -f "${rep%.md}.verification.md" ]; assert_eq "0" "$?" "runner: no verification file when skipped"
[ ! -f "${rep%.md}.verifier-raw.md" ]; assert_eq "0" "$?" "runner: no raw file when skipped"

# RUN_LLM_GEN=1 without JOURNEY_GEN_BACKEND -> fail closed, nothing written
out="$(RUN_LLM_GEN=1 /bin/sh "$uat_rn_runner" "$rep" "$uat_rn_repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: RUN_LLM_GEN=1 without backend -> exit 1"
[ ! -f "${rep%.md}.verification.md" ]; assert_eq "0" "$?" "runner: no verification file (backend unset)"

# ── (b) RUN_LLM_GEN=1 + stub on clean repo at pinned HEAD -> exit 0 ───────
_d="$uat_rn_tmp/happy"; mkdir -p "$_d"; cp -R "$uat_rn_tmp/evidence" "$_d/evidence"
rep="$_d/UAT_REPORT_2026-07-08.md"
uat_rn_mk_report "$uat_rn_rtpl" "$rep" "$uat_rn_commit" "$uat_rn_artsha" "$uat_rn_artsha2"
rsha="$(uat_sha256 "$rep")"
sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$uat_rn_stub" UAT_STUB_SENTINEL="$sentinel" /bin/sh "$uat_rn_runner" "$rep" "$uat_rn_repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "runner: happy path exit 0"
[ -f "$sentinel" ]; assert_eq "0" "$?" "runner: backend was invoked on the happy path"
[ -f "${rep%.md}.verification.md" ]; assert_eq "0" "$?" "runner: verification file written"
_first="$(head -1 "${rep%.md}.verification.md")"
assert_eq "reviewed_sha256: $rsha" "$_first" "runner: stamped first line matches report sha"
# W1 (D2): line 2 is the runner-stamped, absolute PHYSICAL repo_root —
# never model-written, never the raw (possibly relative/symlinked) arg.
_second="$(sed -n '2p' "${rep%.md}.verification.md")"
_uat_rn_repo_abs="$(cd "$uat_rn_repo" && pwd -P)"
assert_eq "repo_root: $_uat_rn_repo_abs" "$_second" "runner: stamped line 2 is the physically-resolved repo_root (W1)"
[ -f "${rep%.md}.verifier-raw.md" ]; assert_eq "0" "$?" "runner: raw audit file written"
out2="$(/bin/sh journey/bin/check-uat-verification.sh "$rep" "${rep%.md}.verification.md" "$uat_rn_repo" 2>&1)"; rc2=$?
assert_eq "0" "$rc2" "runner: written verification passes check-uat-verification.sh"

# ── (c) HEAD advanced past repo_commit -> REPO_MISMATCH, no backend call ──
_d="$uat_rn_tmp/mismatch"; mkdir -p "$_d"; cp -R "$uat_rn_tmp/evidence" "$_d/evidence"
rep="$_d/UAT_REPORT_2026-07-08.md"
uat_rn_mk_report "$uat_rn_rtpl" "$rep" "$uat_rn_commit" "$uat_rn_artsha" "$uat_rn_artsha2"
_advrepo="$_d/repo-advanced"; cp -R "$uat_rn_repo" "$_advrepo"
( cd "$_advrepo" && printf 'more\n' >> extra.txt && git add -A && git commit -qm advance )
sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$uat_rn_stub" UAT_STUB_SENTINEL="$sentinel" /bin/sh "$uat_rn_runner" "$rep" "$_advrepo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: HEAD advanced -> exit 1"
assert_contains "$out" "REPO_MISMATCH" "runner: names REPO_MISMATCH"
[ ! -f "$sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked on REPO_MISMATCH"
[ ! -f "${rep%.md}.verification.md" ]; assert_eq "0" "$?" "runner: nothing written on REPO_MISMATCH"
[ ! -f "${rep%.md}.verifier-raw.md" ]; assert_eq "0" "$?" "runner: no raw file on REPO_MISMATCH"

# ── (d) dirty tree -> TREE_DIRTY, no backend call ─────────────────────────
_d="$uat_rn_tmp/dirty"; mkdir -p "$_d"; cp -R "$uat_rn_tmp/evidence" "$_d/evidence"
rep="$_d/UAT_REPORT_2026-07-08.md"
uat_rn_mk_report "$uat_rn_rtpl" "$rep" "$uat_rn_commit" "$uat_rn_artsha" "$uat_rn_artsha2"
_dirtyrepo="$_d/repo-dirty"; cp -R "$uat_rn_repo" "$_dirtyrepo"
printf 'uncommitted\n' >> "$_dirtyrepo/src/pda/send.ts"
sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$uat_rn_stub" UAT_STUB_SENTINEL="$sentinel" /bin/sh "$uat_rn_runner" "$rep" "$_dirtyrepo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: dirty tree -> exit 1"
assert_contains "$out" "TREE_DIRTY" "runner: names TREE_DIRTY"
[ ! -f "$sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked on TREE_DIRTY"
[ ! -f "${rep%.md}.verification.md" ]; assert_eq "0" "$?" "runner: nothing written on TREE_DIRTY"
[ ! -f "${rep%.md}.verifier-raw.md" ]; assert_eq "0" "$?" "runner: no raw file on TREE_DIRTY"

# ── (e) badhash stub -> exit 1, NO .verification.md (temp+trap proof) ─────
_d="$uat_rn_tmp/badhash"; mkdir -p "$_d"; cp -R "$uat_rn_tmp/evidence" "$_d/evidence"
rep="$_d/UAT_REPORT_2026-07-08.md"
uat_rn_mk_report "$uat_rn_rtpl" "$rep" "$uat_rn_commit" "$uat_rn_artsha" "$uat_rn_artsha2"
sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$uat_rn_badstub" UAT_STUB_SENTINEL="$sentinel" /bin/sh "$uat_rn_runner" "$rep" "$uat_rn_repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: badhash stub -> exit 1"
[ -f "$sentinel" ]; assert_eq "0" "$?" "runner: backend WAS invoked (badhash case reaches the backend)"
[ ! -f "${rep%.md}.verification.md" ]; assert_eq "0" "$?" "runner: no verification file (badhash, temp+trap proof)"
[ ! -f "${rep%.md}.verifier-raw.md" ]; assert_eq "0" "$?" "runner: raw not persisted (badhash)"

# ── (f) missing report path -> MISSING-REPORT, nothing written ────────────
# M-T1-2 guardrail proof: existence check fires before uat_sha256 AND
# before the backend is ever invoked.
_d="$uat_rn_tmp/missing-report"; mkdir -p "$_d"
_missing="$_d/UAT_REPORT_2026-07-08.md"
sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$uat_rn_stub" UAT_STUB_SENTINEL="$sentinel" /bin/sh "$uat_rn_runner" "$_missing" "$uat_rn_repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: missing report -> exit 1"
assert_contains "$out" "MISSING-REPORT" "runner: names MISSING-REPORT"
[ ! -f "$sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked on MISSING-REPORT"
[ ! -f "${_missing%.md}.verification.md" ]; assert_eq "0" "$?" "runner: nothing written on missing report"

# ── (g) repo_commit header line REMOVED -> REPO_MISMATCH, no backend call ─
# M-T7-2 guardrail (final review): before this fix, an empty $commit (from
# a missing/blank repo_commit header) fell straight into the HEAD
# comparison with no dedicated precondition check. Hand-written report:
# same fixture, but the `repo_commit: <sha>` header line is deleted
# entirely (not just blanked) — a plausible hand-authoring slip.
_d="$uat_rn_tmp/no-repo-commit"; mkdir -p "$_d"; cp -R "$uat_rn_tmp/evidence" "$_d/evidence"
rep="$_d/UAT_REPORT_2026-07-08.md"
uat_rn_mk_report "$uat_rn_rtpl" "$rep" "$uat_rn_commit" "$uat_rn_artsha" "$uat_rn_artsha2"
_norc="$_d/UAT_REPORT_NOCOMMIT.md"
sed '/^repo_commit: /d' "$rep" > "$_norc"
sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$uat_rn_stub" UAT_STUB_SENTINEL="$sentinel" /bin/sh "$uat_rn_runner" "$_norc" "$uat_rn_repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: repo_commit header removed -> exit 1"
assert_contains "$out" "REPO_MISMATCH" "runner: names REPO_MISMATCH"
[ ! -f "$sentinel" ]; assert_eq "0" "$?" "runner: backend NOT invoked when repo_commit is missing"
[ ! -f "${_norc%.md}.verification.md" ]; assert_eq "0" "$?" "runner: nothing written when repo_commit is missing"
[ ! -f "${_norc%.md}.verifier-raw.md" ]; assert_eq "0" "$?" "runner: no raw file when repo_commit is missing"

# ── (h) backend declares MISSING-ROOT (W1/D2 degenerate token) -> pass
# through, exit 1, nothing written — same shape as MISSING-REPORT/
# MISSING-HASH pass-through. ────────────────────────────────────────────
_d="$uat_rn_tmp/missing-root"; mkdir -p "$_d"; cp -R "$uat_rn_tmp/evidence" "$_d/evidence"
rep="$_d/UAT_REPORT_2026-07-08.md"
uat_rn_mk_report "$uat_rn_rtpl" "$rep" "$uat_rn_commit" "$uat_rn_artsha" "$uat_rn_artsha2"
sentinel="$_d/.sentinel"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$uat_rn_missingrootstub" UAT_STUB_SENTINEL="$sentinel" /bin/sh "$uat_rn_runner" "$rep" "$uat_rn_repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "runner: backend declares MISSING-ROOT -> exit 1"
assert_contains "$out" "MISSING-ROOT" "runner: names MISSING-ROOT"
[ -f "$sentinel" ]; assert_eq "0" "$?" "runner: backend WAS invoked (MISSING-ROOT reaches the backend)"
[ ! -f "${rep%.md}.verification.md" ]; assert_eq "0" "$?" "runner: no verification file (MISSING-ROOT, temp+trap proof)"
[ ! -f "${rep%.md}.verifier-raw.md" ]; assert_eq "0" "$?" "runner: raw not persisted (MISSING-ROOT)"

# ── (i) W1: RELATIVE and SYMLINKED repo_root args are resolved physically
# by the runner itself — the bundle handed to the backend and the stamped
# verification line 2 both carry the same absolute physical path either
# way. ──────────────────────────────────────────────────────────────────
_d="$uat_rn_tmp/root-relative"; mkdir -p "$_d"; cp -R "$uat_rn_tmp/evidence" "$_d/evidence"
rep="$_d/UAT_REPORT_2026-07-08.md"
uat_rn_mk_report "$uat_rn_rtpl" "$rep" "$uat_rn_commit" "$uat_rn_artsha" "$uat_rn_artsha2"
_uat_rn_repo_abs="$(cd "$uat_rn_repo" && pwd -P)"
_uat_rn_repo_parent="$(dirname "$uat_rn_repo")"
_uat_rn_repo_base="$(basename "$uat_rn_repo")"
out="$(cd "$_uat_rn_repo_parent" && RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$uat_rn_fw_root/$uat_rn_stub" /bin/sh "$uat_rn_fw_root/$uat_rn_runner" "$rep" "$_uat_rn_repo_base" 2>&1)"; rc=$?
assert_eq "0" "$rc" "runner: relative repo_root arg resolves physically -> exit 0"
_second="$(sed -n '2p' "${rep%.md}.verification.md")"
assert_eq "repo_root: $_uat_rn_repo_abs" "$_second" "runner: relative repo_root arg stamps the SAME physical path as the absolute one (W1)"

_d="$uat_rn_tmp/root-symlink"; mkdir -p "$_d"; cp -R "$uat_rn_tmp/evidence" "$_d/evidence"
rep="$_d/UAT_REPORT_2026-07-08.md"
uat_rn_mk_report "$uat_rn_rtpl" "$rep" "$uat_rn_commit" "$uat_rn_artsha" "$uat_rn_artsha2"
_link="$_d/repo-link"; ln -s "$_uat_rn_repo_abs" "$_link"
out="$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$uat_rn_stub" /bin/sh "$uat_rn_runner" "$rep" "$_link" 2>&1)"; rc=$?
assert_eq "0" "$rc" "runner: symlinked repo_root arg resolves physically -> exit 0"
_second="$(sed -n '2p' "${rep%.md}.verification.md")"
assert_eq "repo_root: $_uat_rn_repo_abs" "$_second" "runner: symlinked repo_root arg stamps the SAME physical path as the real dir (W1)"

rm -rf "$uat_rn_tmp"
