# uat-promote-citation_test.sh — gates 4.4/4.5: the human trust elevation
# (uat-report-promote.sh --approve) and the downstream authority check
# (check-uat-citation.sh), spec §4.4/§4.5, O2/O11.
# shellcheck shell=sh
. "$(dirname "$0")/assert.sh"
. "$(dirname "$0")/../lib/uat-lib.sh"

uat_pc_tmp="$(mktemp -d)"

# Own prefixed copy of T2/T3's fixture-repo builder (same shape — the golden
# verification cites the identical paths/lines: send.ts:12, PRD.md:8,
# export.ts:22, config/ search).
uat_pc_mk_repo() { # $1=dir ; echoes HEAD sha
  ( cd "$1" && git init -q . && git config user.email t@t && git config user.name t
    mkdir -p src/pda docs src config src/auth
    printf 'line1\nline2\n// context\nline4\nline5\nline6\nline7\nline8\nline9\nline10\nline11\nthrow new Error('"'"'portal timeout'"'"')\n' > src/pda/send.ts
    printf '1\n2\n3\n4\n5\n6\n7\ninvoices can be exported as CSV\n' > docs/PRD.md
    { i=1; while [ $i -le 21 ]; do printf 'x%s\n' "$i"; i=$((i+1)); done
      printf "if (fmt === 'csv') reject()\n"; } > src/export.ts
    printf 'no bypass here\n' > config/auth.ts
    # flagship (T5) fixture: a real dev-auth bypass, but it lives OUTSIDE
    # config/ — the seam the field-run archetype exploits (a narrow, honest
    # search that re-runs empty against the pinned commit).
    printf "export const ENABLE_DEV_AUTH_BYPASS = readEnv('ENABLE_DEV_AUTH_BYPASS')\n" > src/auth/bypass.ts
    git add -A && git commit -qm fixture && git rev-parse HEAD )
}

repo="$uat_pc_tmp/repo"; mkdir -p "$repo"; commit="$(uat_pc_mk_repo "$repo")"
mkdir -p "$uat_pc_tmp/evidence"
printf 'fake-png\n' > "$uat_pc_tmp/evidence/journey-106-send-500.png"
printf 'fake-png-2\n' > "$uat_pc_tmp/evidence/journey-114-save-error.png"
artsha="$(uat_sha256 "$uat_pc_tmp/evidence/journey-106-send-500.png")"
artsha2="$(uat_sha256 "$uat_pc_tmp/evidence/journey-114-save-error.png")"

uat_pc_mk_report() { sed -e "s/@COMMIT@/$3/" -e "s/@ARTSHA@/$4/" -e "s/@ARTSHA2@/$5/" "$1" > "$2"; }
rtpl="journey/tests/fixtures/uat/templates/UAT_REPORT_2026-07-08.md.in"
vtpl="journey/tests/fixtures/uat/templates/UAT_REPORT_2026-07-08.verification.md.in"

# W1 (D2): the physical resolution of $repo — every verification fixture
# built directly from a template below stamps THIS value as its repo_root
# line (mirrors the runner's own cd + pwd -P resolution, uat-verify-run.sh).
repo_abs="$(cd "$repo" && pwd -P)"
# uat_pc_mk_ver TEMPLATE DEST RSHA -> substitutes @RSHA@ and @REPO_ROOT@
# (always $repo_abs here — every case in this file verifies against the
# one shared fixture repo).
uat_pc_mk_ver() { sed -e "s/@RSHA@/$3/g" -e "s#@REPO_ROOT@#$repo_abs#" "$1" > "$2"; }

rep="$uat_pc_tmp/UAT_REPORT_2026-07-08.md"
uat_pc_mk_report "$rtpl" "$rep" "$commit" "$artsha" "$artsha2"
rsha="$(uat_sha256 "$rep")"

ver="$uat_pc_tmp/UAT_REPORT_2026-07-08.verification.md"
uat_pc_mk_ver "$vtpl" "$ver" "$rsha"

# ── brief's flagship sequence (Step 1 code block, transcribed) ────────────
# Deviation note: the brief's assert_contains call for the refusal message
# reads `assert_contains "$out" -- "--approve" "..."` — a stray "--" that
# would (per assert_contains's HAYSTACK/NEEDLE/MSG signature) make "--" the
# needle and "--approve" the discarded message, not actually asserting the
# message names the flag. The binding contract text is explicit ("message
# must contain --approve"), so this call is written correctly below instead
# of literally replaying the apparent typo.

# no --approve -> refusal, nothing written
out="$(/bin/sh journey/bin/uat-report-promote.sh "$rep" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "promote: refuses without --approve"
assert_contains "$out" "--approve" "promote: names the missing flag"
[ ! -f "${rep%.md}.promotion" ]; assert_eq "0" "$?" "promote: no marker without approval"

# full green path
out="$(/bin/sh journey/bin/uat-report-promote.sh "$rep" "$repo" --approve 2>&1)"; rc=$?
assert_eq "0" "$rc" "promote: golden + all-confirm promotes"
out="$(/bin/sh journey/bin/check-uat-citation.sh "$rep" "$repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "citation: green after promotion"
assert_contains "$out" "UAT-CITATION: green" "citation: greppable green line"

# O2 proof: hand-written all-confirm verification WITHOUT promotion
rm "${rep%.md}.promotion"
out="$(/bin/sh journey/bin/check-uat-citation.sh "$rep" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "citation O2 rc: verification alone is not authority"
assert_contains "$out" "PROMOTION_MISSING" "citation O2 code"

# edit-after-promotion -> PROMOTION_STALE
/bin/sh journey/bin/uat-report-promote.sh "$rep" "$repo" --approve >/dev/null 2>&1
printf '\nEdited narrative line.\n' >> "$rep"
out="$(/bin/sh journey/bin/check-uat-citation.sh "$rep" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "citation rc: post-promotion edit"
assert_contains "$out" "PROMOTION_STALE" "citation code: post-promotion edit"

# --approve may appear in any position, not just trailing
_d="$uat_pc_tmp/flag-position"; mkdir -p "$_d"; cp -R "$uat_pc_tmp/evidence" "$_d/evidence"
uat_pc_mk_report "$rtpl" "$_d/UAT_REPORT_2026-07-08.md" "$commit" "$artsha" "$artsha2"
uat_pc_mk_ver "$vtpl" "$_d/UAT_REPORT_2026-07-08.verification.md" "$(uat_sha256 "$_d/UAT_REPORT_2026-07-08.md")"
out="$(/bin/sh journey/bin/uat-report-promote.sh --approve "$_d/UAT_REPORT_2026-07-08.md" "$repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "promote: --approve accepted in leading position"
[ -f "$_d/UAT_REPORT_2026-07-08.promotion" ]; assert_eq "0" "$?" "promote: marker written (leading --approve)"

# ── downgrade -> NON_CONFIRM_VERDICT. Also the suite's first positive-path
# valid downgrade through check-uat-verification.sh (closes T3 coverage
# note M-T3-1): asserted green on that gate alone BEFORE asserting promote
# rejects it — a valid downgrade is gate-legal but promote-blocking.
_d="$uat_pc_tmp/downgrade"; mkdir -p "$_d"; cp -R "$uat_pc_tmp/evidence" "$_d/evidence"
_drep="$_d/UAT_REPORT_2026-07-08.md"
uat_pc_mk_report "$rtpl" "$_drep" "$commit" "$artsha" "$artsha2"
_drsha="$(uat_sha256 "$_drep")"
_dver="$_d/UAT_REPORT_2026-07-08.verification.md"
uat_pc_mk_ver "$vtpl" "$_dver" "$_drsha"
# claim-4's verdict (line 25, post-W1 repo_root-line shift) -> downgrade,
# with a regrade differing from its author grade ([I] in the template; [G]
# is a legal, differing regrade), plus an - evidence: line (W2/D3-a: every
# downgrade/refute needs >= 1 re-checkable citation — real text, genuinely
# at config/auth.ts:1 in the fixture repo).
sed '25s/^- verdict: confirm$/- verdict: downgrade/' "$_dver" \
  | awk -v r='- regrade: [G]' -v e='- evidence: config/auth.ts:1 — "no bypass here"' \
      'NR==25{print; print r; print e; next}{print}' > "$_dver.next"
mv "$_dver.next" "$_dver"
out="$(/bin/sh journey/bin/check-uat-verification.sh "$_drep" "$_dver" "$repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "downgrade: valid downgrade alone passes check-uat-verification"
out="$(/bin/sh journey/bin/uat-report-promote.sh "$_drep" "$repo" --approve 2>&1)"; rc=$?
assert_eq "1" "$rc" "promote: downgrade verdict refused"
assert_contains "$out" "NON_CONFIRM_VERDICT" "promote: names NON_CONFIRM_VERDICT"
[ ! -f "${_drep%.md}.promotion" ]; assert_eq "0" "$?" "promote: no marker on downgrade refusal"

# ── all-[G] report (no [C]/[C-absent]/[X] claims) -> NO_EVIDENCED_CLAIMS ──
_d="$uat_pc_tmp/all-gaps"; mkdir -p "$_d"
gtpl="journey/tests/fixtures/uat/templates/UAT_REPORT_2026-07-09.md.in"
gvtpl="journey/tests/fixtures/uat/templates/UAT_REPORT_2026-07-09.verification.md.in"
_grep="$_d/UAT_REPORT_2026-07-09.md"
sed "s/@COMMIT@/$commit/" "$gtpl" > "$_grep"
_grsha="$(uat_sha256 "$_grep")"
_gver="$_d/UAT_REPORT_2026-07-09.verification.md"
uat_pc_mk_ver "$gvtpl" "$_gver" "$_grsha"
out="$(/bin/sh journey/bin/lint-uat-report.sh "$_grep" 2>&1)"; rc=$?
assert_eq "0" "$rc" "all-gaps: lint alone is clean (isolates the NO_EVIDENCED_CLAIMS cause)"
out="$(/bin/sh journey/bin/check-uat-verification.sh "$_grep" "$_gver" "$repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "all-gaps: verification alone is clean (isolates the NO_EVIDENCED_CLAIMS cause)"
out="$(/bin/sh journey/bin/uat-report-promote.sh "$_grep" "$repo" --approve 2>&1)"; rc=$?
assert_eq "1" "$rc" "promote: all-[G] report refused"
assert_contains "$out" "NO_EVIDENCED_CLAIMS" "promote: names NO_EVIDENCED_CLAIMS"
[ ! -f "${_grep%.md}.promotion" ]; assert_eq "0" "$?" "promote: no marker on all-[G] refusal"

# ── missing verification file -> VERIFICATION_MISSING ─────────────────────
_d="$uat_pc_tmp/no-verification"; mkdir -p "$_d"; cp -R "$uat_pc_tmp/evidence" "$_d/evidence"
_nvrep="$_d/UAT_REPORT_2026-07-08.md"
uat_pc_mk_report "$rtpl" "$_nvrep" "$commit" "$artsha" "$artsha2"
out="$(/bin/sh journey/bin/uat-report-promote.sh "$_nvrep" "$repo" --approve 2>&1)"; rc=$?
assert_eq "1" "$rc" "promote: missing verification refused"
assert_contains "$out" "VERIFICATION_MISSING" "promote: names VERIFICATION_MISSING"
[ ! -f "${_nvrep%.md}.promotion" ]; assert_eq "0" "$?" "promote: no marker without verification"

# ── citation re-verifies, never trusts the marker alone: delete the
# verification file AFTER a valid promotion -> citation must still fail
# (brief lacks this case; added per self-review instruction) ──────────────
_d="$uat_pc_tmp/verification-deleted-post-promotion"; mkdir -p "$_d"; cp -R "$uat_pc_tmp/evidence" "$_d/evidence"
_vdrep="$_d/UAT_REPORT_2026-07-08.md"
uat_pc_mk_report "$rtpl" "$_vdrep" "$commit" "$artsha" "$artsha2"
_vdver="$_d/UAT_REPORT_2026-07-08.verification.md"
uat_pc_mk_ver "$vtpl" "$_vdver" "$(uat_sha256 "$_vdrep")"
out="$(/bin/sh journey/bin/uat-report-promote.sh "$_vdrep" "$repo" --approve 2>&1)"; rc=$?
assert_eq "0" "$rc" "verification-deleted: setup promotes cleanly"
rm "$_vdver"
out="$(/bin/sh journey/bin/check-uat-citation.sh "$_vdrep" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "citation: verification deleted post-promotion must fail"
assert_contains "$out" "PROMOTION_STALE" "citation: names PROMOTION_STALE when verification vanishes"

# ── citation re-runs the gates: a promoted report/verification pair that
# later fails 4.2 (evidence tampered post-promotion) must fail citation
# even though the marker's hashes still match byte-for-byte ────────────────
_d="$uat_pc_tmp/evidence-tampered-post-promotion"; mkdir -p "$_d"; cp -R "$uat_pc_tmp/evidence" "$_d/evidence"
_etrep="$_d/UAT_REPORT_2026-07-08.md"
uat_pc_mk_report "$rtpl" "$_etrep" "$commit" "$artsha" "$artsha2"
_etver="$_d/UAT_REPORT_2026-07-08.verification.md"
uat_pc_mk_ver "$vtpl" "$_etver" "$(uat_sha256 "$_etrep")"
out="$(/bin/sh journey/bin/uat-report-promote.sh "$_etrep" "$repo" --approve 2>&1)"; rc=$?
assert_eq "0" "$rc" "evidence-tampered: setup promotes cleanly"
# corrupt the artifact bytes in place (same path, same marker hashes) so the
# marker is still byte-fresh but gate 4.2's re-run must now fail
printf 'tampered bytes\n' > "$_d/evidence/journey-106-send-500.png"
out="$(/bin/sh journey/bin/check-uat-citation.sh "$_etrep" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "citation: post-promotion evidence tamper must fail"
assert_contains "$out" "ARTIFACT_HASH_MISMATCH" "citation: pass-through of gate 4.2's failure code"

# ── flagship: the GAPS.txt archetype in miniature (spec's field-run failure
# mode). An overstated-absence claim whose author search is honest but
# narrow (config/ only) — the code it should have found lives in src/auth/.
# Deterministic gates 4.1/4.2 PASS it on purpose: the cited search really
# does reproduce zero hits against the pinned commit, so lint/evidence have
# no basis to object. Only the verifier layer (a human or reviewer with
# broader knowledge of the tree) catches the overstatement and refutes it —
# and that refutation is itself gate-legal (also the suite's first
# positive-path refute-with-residual, closing T3 coverage note), yet
# promotion — and therefore citation authority — is still blocked. ────────
_d="$uat_pc_tmp/flagship"; mkdir -p "$_d"
r10tpl="journey/tests/fixtures/uat/templates/UAT_REPORT_2026-07-10.md.in"
v10tpl="journey/tests/fixtures/uat/templates/UAT_REPORT_2026-07-10.verification.md.in"
rep10="$_d/UAT_REPORT_2026-07-10.md"
sed "s/@COMMIT@/$commit/" "$r10tpl" > "$rep10"
rsha10="$(uat_sha256 "$rep10")"
ver10="$_d/UAT_REPORT_2026-07-10.verification.md"
uat_pc_mk_ver "$v10tpl" "$ver10" "$rsha10"

# deterministic gates PASS the overstated claim — the seam, asserted on purpose
out="$(/bin/sh journey/bin/lint-uat-report.sh "$rep10" 2>&1)"; rc=$?
assert_eq "0" "$rc" "flagship: lint passes overstated absence"
out="$(/bin/sh journey/bin/check-uat-evidence.sh "$rep10" "$repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "flagship: evidence gate passes it (seam is real)"
# the verifier layer catches it and citation goes red
out="$(/bin/sh journey/bin/check-uat-verification.sh "$rep10" "$ver10" "$repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "flagship: refuting verification is itself valid"
out="$(/bin/sh journey/bin/uat-report-promote.sh "$rep10" "$repo" --approve 2>&1)"; rc=$?
assert_eq "1" "$rc" "flagship rc: refuted claim cannot promote"
assert_contains "$out" "NON_CONFIRM_VERDICT" "flagship code"

rm -rf "$uat_pc_tmp"
