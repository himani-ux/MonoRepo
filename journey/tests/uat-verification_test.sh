# uat-verification_test.sh — gate 4.3: verifier evidence held to the same
# discipline as the author's (4.2), plus hash-bound verdict coverage.
# shellcheck shell=sh
. "$(dirname "$0")/../lib/uat-lib.sh"

uat_ver_tmp="$(mktemp -d)"
_fw_root="$(pwd)"

# Own prefixed copy of T2's fixture-repo builder (same shape — the golden
# verification cites the identical paths/lines: send.ts:12, PRD.md:8,
# export.ts:22, config/ search) so it can be reused without coupling to
# uat-evidence_test.sh's function of the same purpose.
uat_ver_mk_repo() { # $1=dir ; echoes HEAD sha
  ( cd "$1" && git init -q . && git config user.email t@t && git config user.name t
    mkdir -p src/pda docs src config
    printf 'line1\nline2\n// context\nline4\nline5\nline6\nline7\nline8\nline9\nline10\nline11\nthrow new Error('"'"'portal timeout'"'"')\n' > src/pda/send.ts
    printf '1\n2\n3\n4\n5\n6\n7\ninvoices can be exported as CSV\n' > docs/PRD.md
    { i=1; while [ $i -le 21 ]; do printf 'x%s\n' "$i"; i=$((i+1)); done
      printf "if (fmt === 'csv') reject()\n"; } > src/export.ts
    printf 'no bypass here\n' > config/auth.ts
    git add -A && git commit -qm fixture && git rev-parse HEAD )
}

repo="$uat_ver_tmp/repo"; mkdir -p "$repo"; commit="$(uat_ver_mk_repo "$repo")"
# W1 (D2): the physical resolution of $repo — every verification fixture
# below stamps THIS value as its repo_root line, and every gate-4.3 call
# below independently re-resolves whatever repo_root arg it was given the
# identical way (cd + pwd -P), so the two must agree exactly on a golden run.
repo_abs="$(cd "$repo" && pwd -P)"
mkdir -p "$uat_ver_tmp/evidence"
printf 'fake-png\n' > "$uat_ver_tmp/evidence/journey-106-send-500.png"
printf 'fake-png-2\n' > "$uat_ver_tmp/evidence/journey-114-save-error.png"
artsha="$(uat_sha256 "$uat_ver_tmp/evidence/journey-106-send-500.png")"
artsha2="$(uat_sha256 "$uat_ver_tmp/evidence/journey-114-save-error.png")"

uat_ver_mk_report() { sed -e "s/@COMMIT@/$3/" -e "s/@ARTSHA@/$4/" -e "s/@ARTSHA2@/$5/" "$1" > "$2"; }
rtpl="journey/tests/fixtures/uat/templates/UAT_REPORT_2026-07-08.md.in"
rep="$uat_ver_tmp/UAT_REPORT_2026-07-08.md"
uat_ver_mk_report "$rtpl" "$rep" "$commit" "$artsha" "$artsha2"
rsha="$(uat_sha256 "$rep")"

# uat_ver_mk_ver TEMPLATE DEST REPO_ROOT_ABS -> substitutes @RSHA@ (this
# report's hash) and @REPO_ROOT@ (W1/D2 — the runner-stamped physical repo
# root) into a verification template.
uat_ver_mk_ver() { sed -e "s/@RSHA@/$rsha/g" -e "s#@REPO_ROOT@#$3#" "$1" > "$2"; }

vtpl="journey/tests/fixtures/uat/templates/UAT_REPORT_2026-07-08.verification.md.in"
ver="$uat_ver_tmp/UAT_REPORT_2026-07-08.verification.md"
uat_ver_mk_ver "$vtpl" "$ver" "$repo_abs"

# ── golden layout (post-W1, line numbers used by every sed/awk mutation
# below): 1 reviewed_sha256, 2 repo_root, 3 blank, then per claim a blank +
# UAT-VERDICT + verdict + reason [+ evidence/search lines] + checked_hash —
# claim-1 body at 4-8, claim-2 at 10-15, claim-3 at 17-22, claim-4 at 24-27,
# claim-5 at 29-32. ──────────────────────────────────────────────────────
out="$(/bin/sh journey/bin/check-uat-verification.sh "$rep" "$ver" "$repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "verification: golden all-confirm verifies against pinned commit + report hash + repo_root"

zeros="$(awk 'BEGIN{for(i=0;i<64;i++)printf "0"}')"

# $1=name $2=code $3=mutated-verification-file — NOT fed via a trailing pipe:
# a pipe's last stage runs in a subshell, so assert_eq/assert_contains would
# increment ASSERT_FAILS in a subshell the parent never sees (same class of
# bug as the a21f319 lesson). Each case below writes its mutation to a real
# file with `>` first, then calls this as a plain function.
uat_ver_run() {
  _o="$(/bin/sh journey/bin/check-uat-verification.sh "$rep" "$3" "$repo" 2>&1)"; _rc=$?
  assert_eq "1" "$_rc" "verification red rc: $1"
  assert_contains "$_o" "$2" "verification red code: $1"
}

# stale: header hash overwritten with 64 zeros; every checked_hash: still
# matches the real report sha, so this isolates the first-line check.
_d="$uat_ver_tmp/stale"; mkdir -p "$_d"
sed "1s/$rsha/$zeros/" "$ver" > "$_d/ver.md"
uat_ver_run stale STALE_VERIFICATION "$_d/ver.md"

# incomplete: drop claim-5's entire verdict block (lines 28-32: the blank
# separator plus the four body lines).
_d="$uat_ver_tmp/incomplete"; mkdir -p "$_d"
sed '28,32d' "$ver" > "$_d/ver.md"
uat_ver_run incomplete VERDICT_INCOMPLETE "$_d/ver.md"

# duplicate: append a second copy of claim-1's block (lines 4-9, including
# the blank separator right after it) right after the first — awk reads the
# source a second time via getline (portable under BSD awk, which errors on
# embedded newlines in a -v string).
_d="$uat_ver_tmp/duplicate"; mkdir -p "$_d"
awk -v src="$ver" 'NR==9{print; while ((getline line < src) > 0) {c++; if (c>=4 && c<=9) print line}; next}{print}' "$ver" > "$_d/ver.md"
uat_ver_run duplicate DUPLICATE_VERDICT "$_d/ver.md"

# unknown-claim: claim-5's verdict id becomes CLAIM-9 (unique text, single
# occurrence) — membership is checked BEFORE coverage, so this must surface
# UNKNOWN_CLAIM specifically, not VERDICT_INCOMPLETE (claim-5 is also now
# uncovered, but membership fires first).
_d="$uat_ver_tmp/unknown-claim"; mkdir -p "$_d"
sed 's/UAT-VERDICT: UAT-CLAIM-5/UAT-VERDICT: UAT-CLAIM-9/' "$ver" > "$_d/ver.md"
uat_ver_run unknown-claim UNKNOWN_CLAIM "$_d/ver.md"

# vocab: claim-1's verdict (line 5, the first "- verdict: confirm") becomes
# an out-of-vocabulary value.
_d="$uat_ver_tmp/vocab"; mkdir -p "$_d"
sed '5s/^- verdict: confirm$/- verdict: maybe/' "$ver" > "$_d/ver.md"
uat_ver_run vocab VERDICT_UNKNOWN "$_d/ver.md"

# regrade-missing: claim-4 (line 25) downgraded with no - regrade: line.
_d="$uat_ver_tmp/regrade-missing"; mkdir -p "$_d"
sed '25s/^- verdict: confirm$/- verdict: downgrade/' "$ver" > "$_d/ver.md"
uat_ver_run regrade-missing REGRADE_MISSING "$_d/ver.md"

# regrade-same: claim-4 downgraded AND regraded to [I] — claim-4's own
# author grade (see the report template) is already [I], so this must still
# be REGRADE_MISSING (regrade must differ from the author's grade).
_d="$uat_ver_tmp/regrade-same"; mkdir -p "$_d"
sed '25s/^- verdict: confirm$/- verdict: downgrade/' "$ver" \
  | awk -v ins='- regrade: [I]' 'NR==25{print; print ins; next}{print}' > "$_d/ver.md"
uat_ver_run regrade-same REGRADE_MISSING "$_d/ver.md"

# residual-on-confirm: claim-1 stays confirm but gains a residual: line.
_d="$uat_ver_tmp/residual-on-confirm"; mkdir -p "$_d"
awk -v ins='- residual: probably config' 'NR==7{print; print ins; next}{print}' "$ver" > "$_d/ver.md"
uat_ver_run residual-on-confirm RESIDUAL_ON_CONFIRM "$_d/ver.md"

# verifier-fabricates: claim-1's evidence quote (line 7) is rewritten to text
# that appears nowhere in the pinned commit.
_d="$uat_ver_tmp/verifier-fabricates"; mkdir -p "$_d"
sed "7s/throw new Error('portal timeout')/throw new Error('NEVER PRESENT TEXT XYZ')/" "$ver" > "$_d/ver.md"
uat_ver_run verifier-fabricates QUOTE_UNVERIFIED "$_d/ver.md"

# empty-quote: claim-1's evidence quote (line 7) is emptied to "" — a naive
# substring check (grep -qF -- "" matches every line) would verify vacuously
# with zero bytes checked; must fail closed instead.
_d="$uat_ver_tmp/empty-quote"; mkdir -p "$_d"
sed '7s/ — ".*"$/ — ""/' "$ver" > "$_d/ver.md"
uat_ver_run empty-quote QUOTE_UNVERIFIED "$_d/ver.md"

# search-on-refute: claim-2's verdict (line 11) becomes refute while its two
# search: lines stay in the block — search: is only legal on a confirm of a
# [C-absent] claim.
_d="$uat_ver_tmp/search-on-refute"; mkdir -p "$_d"
sed '11s/^- verdict: confirm$/- verdict: refute/' "$ver" > "$_d/ver.md"
uat_ver_run search-on-refute SEARCH_FORMAT "$_d/ver.md"

# hash-echo: claim-1's checked_hash (line 8, the first occurrence) diverges
# from the recomputed report sha — every checked_hash: must match.
_d="$uat_ver_tmp/hash-echo"; mkdir -p "$_d"
sed '8s/^- checked_hash: .*/- checked_hash: beef/' "$ver" > "$_d/ver.md"
uat_ver_run hash-echo STALE_VERIFICATION "$_d/ver.md"

# absence-no-search: claim-2 stays confirm of a [C-absent] claim but both of
# its search: lines (13-14) are removed — a confirmed absence needs proof.
_d="$uat_ver_tmp/absence-no-search"; mkdir -p "$_d"
sed '13,14d' "$ver" > "$_d/ver.md"
uat_ver_run absence-no-search ABSENCE_NO_SEARCH "$_d/ver.md"

# ══════════════════════════════════════════════════════════════════════
# W3 (D3-b): a confirm-verdict search line whose relpath is "." (repo
# root — the verifier prompt's own "a wider pattern, a different
# directory" instruction taken literally) must pass through gate 4.3
# exactly like a scoped relpath does. Claim-2's first search line
# (config/, line 13) is widened to the whole tree.
# ══════════════════════════════════════════════════════════════════════
_d="$uat_ver_tmp/search-root-relpath"; mkdir -p "$_d"
sed '13s|" config/|" .|' "$ver" > "$_d/ver.md"
_o="$(/bin/sh journey/bin/check-uat-verification.sh "$rep" "$_d/ver.md" "$repo" 2>&1)"; _rc=$?
assert_eq "0" "$_rc" "verification: confirm-verdict search relpath '.' succeeds through gate 4.3 (W3/D3-b)"

# ══════════════════════════════════════════════════════════════════════
# W1 (D2): ROOT_MISMATCH — the runner-stamped repo_root line (line 2) is
# now gate-enforced, physically resolved on both sides.
# ══════════════════════════════════════════════════════════════════════

# missing line 2 entirely (an old-shaped verification, pre-W1) -> ROOT_MISMATCH
_d="$uat_ver_tmp/root-missing"; mkdir -p "$_d"
sed '2d' "$ver" > "$_d/ver.md"
uat_ver_run root-missing ROOT_MISMATCH "$_d/ver.md"

# wrong root (a real, different directory) -> ROOT_MISMATCH
_d="$uat_ver_tmp/root-wrong"; mkdir -p "$_d"
sed "2s#^repo_root: .*#repo_root: $uat_ver_tmp#" "$ver" > "$_d/ver.md"
uat_ver_run root-wrong ROOT_MISMATCH "$_d/ver.md"

# right root via a RELATIVE arg -> physical resolution equalizes it against
# the stamped absolute path (run from a cwd where "repo" resolves to $repo).
_o="$(cd "$uat_ver_tmp" && /bin/sh "$_fw_root/journey/bin/check-uat-verification.sh" "$rep" "$ver" "repo" 2>&1)"; _rc=$?
assert_eq "0" "$_rc" "verification: relative repo_root arg resolves physically, matches stamped root (W1)"

# right root via a SYMLINKED path -> physical resolution (pwd -P) resolves
# the symlink to the same real directory the stamped line names.
ln -s "$repo_abs" "$uat_ver_tmp/repo-link"
_o="$(/bin/sh journey/bin/check-uat-verification.sh "$rep" "$ver" "$uat_ver_tmp/repo-link" 2>&1)"; _rc=$?
assert_eq "0" "$_rc" "verification: symlinked repo_root arg resolves physically, matches stamped root (W1)"

# a spaced-path repo fixture — this repo's own path has a space
# ("KLOSS FRAMEWORK"); a standalone trio under a deliberately spaced
# directory proves every `git -C "$repo"` / `cd "$repo"` in the W1 path is
# properly quoted end to end, not just incidentally working on this host.
_spd="$uat_ver_tmp/space dir"; mkdir -p "$_spd"
_srepo="$_spd/repo"; mkdir -p "$_srepo"
_scommit="$(uat_ver_mk_repo "$_srepo")"
_srepo_abs="$(cd "$_srepo" && pwd -P)"
_srep="$_spd/UAT_REPORT_2026-07-08.md"
uat_ver_mk_report "$rtpl" "$_srep" "$_scommit" "$artsha" "$artsha2"
_srsha="$(uat_sha256 "$_srep")"
_sver="$_spd/UAT_REPORT_2026-07-08.verification.md"
sed -e "s/@RSHA@/$_srsha/g" -e "s#@REPO_ROOT@#$_srepo_abs#" "$vtpl" > "$_sver"
_o="$(/bin/sh journey/bin/check-uat-verification.sh "$_srep" "$_sver" "$_srepo" 2>&1)"; _rc=$?
assert_eq "0" "$_rc" "verification: spaced-path repo fixture verifies clean (W1 quoting proof)"

# ══════════════════════════════════════════════════════════════════════
# W2 (D3-a): CITATION_MISSING — a refute/downgrade verdict with zero
# - evidence: lines. Claim-4 and claim-5 carry no evidence in the golden
# verification (their confirm needs none), so mutating only their verdict
# token isolates this code from REGRADE_MISSING/RESIDUAL_ON_CONFIRM.
# ══════════════════════════════════════════════════════════════════════

# uncited refute
_d="$uat_ver_tmp/citation-missing-refute"; mkdir -p "$_d"
sed '25s/^- verdict: confirm$/- verdict: refute/' "$ver" > "$_d/ver.md"
uat_ver_run citation-missing-refute CITATION_MISSING "$_d/ver.md"

# uncited downgrade (regrade supplied, so REGRADE_MISSING must NOT also fire)
_d="$uat_ver_tmp/citation-missing-downgrade"; mkdir -p "$_d"
sed '30s/^- verdict: confirm$/- verdict: downgrade/' "$ver" \
  | awk -v ins='- regrade: [I]' 'NR==30{print; print ins; next}{print}' > "$_d/ver.md"
uat_ver_run citation-missing-downgrade CITATION_MISSING "$_d/ver.md"
assert_not_contains "$_o" "REGRADE_MISSING" "citation-missing-downgrade: a real regrade is present, so REGRADE_MISSING must not co-fire"

# cited refute whose citation fails QUOTE_UNVERIFIED — the D2 failure mode
# now failing closed TWICE over: even a refute that carries an evidence
# line (satisfying W2) is still worthless if that citation doesn't
# actually resolve against the pinned commit (a verifier grounded in the
# wrong repo would produce exactly this shape).
_d="$uat_ver_tmp/cited-refute-fabricated"; mkdir -p "$_d"
sed -e '5s/^- verdict: confirm$/- verdict: refute/' \
    -e "7s/throw new Error('portal timeout')/throw new Error('NEVER PRESENT TEXT XYZ')/" \
    "$ver" > "$_d/ver.md"
uat_ver_run cited-refute-fabricated QUOTE_UNVERIFIED "$_d/ver.md"

# MKTEMP_FAILED (M-T1-4, final review): same accumulator fail-open as gate
# 4.2, reused here since gate 4.3 builds its own $_fail via an unguarded
# `_fail="$(mktemp)"` too. Reproduced by hand pre-fix: PATH-shimmed with a
# `mktemp` that always fails, against the verifier-fabricates fixture below
# (a real QUOTE_UNVERIFIED in the verifier's own evidence), the unfixed
# gate returned rc 0 with the QUOTE_UNVERIFIED line printed to stderr and
# swallowed — see uat-task-8-report.md for the transcript.
#
# TMPDIR alone does not reproduce mktemp failure on macOS (probed
# empirically — bare `mktemp` prefers _CS_DARWIN_USER_TEMP_DIR over
# $TMPDIR and falls back even under a chmod-000-unwritable TMPDIR), so a
# PATH-shimmed fake `mktemp` that always fails is used instead.
uat_ver_mktemp_shim="$uat_ver_tmp/mktemp-shim"; mkdir -p "$uat_ver_mktemp_shim"
for _b in git awk sed grep tr head sort uniq cat dirname basename rm wc sha256sum shasum; do
  _real="$(command -v "$_b")" && ln -s "$_real" "$uat_ver_mktemp_shim/$_b"
done
cat > "$uat_ver_mktemp_shim/mktemp" <<'SHIM'
#!/bin/sh
printf 'mktemp: simulated failure (fail-closed proof)\n' >&2
exit 1
SHIM
chmod +x "$uat_ver_mktemp_shim/mktemp"

_d="$uat_ver_tmp/mktemp-fail"; mkdir -p "$_d"
sed "7s/throw new Error('portal timeout')/throw new Error('NEVER PRESENT TEXT XYZ')/" "$ver" > "$_d/ver.md"
out="$(PATH="$uat_ver_mktemp_shim" /bin/sh journey/bin/check-uat-verification.sh "$rep" "$_d/ver.md" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "verification: mktemp failure on \$_fail fails closed, not fail-open (rc)"
assert_contains "$out" "MKTEMP_FAILED" "verification: mktemp failure on \$_fail fails closed, not fail-open (code)"

rm -rf "$uat_ver_tmp"
