# uat-evidence_test.sh — gate 4.2 vs a pinned commit
# shellcheck shell=sh
. "$(dirname "$0")/../lib/uat-lib.sh"

uat_ev_tmp="$(mktemp -d)"

uat_mk_repo() { # $1=dir ; echoes HEAD sha
  ( cd "$1" && git init -q . && git config user.email t@t && git config user.name t
    mkdir -p src/pda docs src config
    printf 'line1\nline2\n// context\nline4\nline5\nline6\nline7\nline8\nline9\nline10\nline11\nthrow new Error('"'"'portal timeout'"'"')\n' > src/pda/send.ts
    printf '1\n2\n3\n4\n5\n6\n7\ninvoices can be exported as CSV\n' > docs/PRD.md
    { i=1; while [ $i -le 21 ]; do printf 'x%s\n' "$i"; i=$((i+1)); done
      printf "if (fmt === 'csv') reject()\n"; } > src/export.ts
    printf 'no bypass here\n' > config/auth.ts
    git add -A && git commit -qm fixture && git rev-parse HEAD )
}

repo="$uat_ev_tmp/repo"; mkdir -p "$repo"; commit="$(uat_mk_repo "$repo")"
mkdir -p "$uat_ev_tmp/evidence"
printf 'fake-png\n' > "$uat_ev_tmp/evidence/journey-106-send-500.png"
printf 'fake-png-2\n' > "$uat_ev_tmp/evidence/journey-114-save-error.png"
artsha="$(uat_sha256 "$uat_ev_tmp/evidence/journey-106-send-500.png")"
artsha2="$(uat_sha256 "$uat_ev_tmp/evidence/journey-114-save-error.png")"

uat_mk_report() { sed -e "s/@COMMIT@/$3/" -e "s/@ARTSHA@/$4/" -e "s/@ARTSHA2@/$5/" "$1" > "$2"; }
tpl="journey/tests/fixtures/uat/templates/UAT_REPORT_2026-07-08.md.in"
rep="$uat_ev_tmp/UAT_REPORT_2026-07-08.md"
uat_mk_report "$tpl" "$rep" "$commit" "$artsha" "$artsha2"

out="$(/bin/sh journey/bin/check-uat-evidence.sh "$rep" "$repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "evidence: golden verifies against pinned commit"

# report survives HEAD advancing (spec §4.2 step 1: reports do not expire)
( cd "$repo" && printf 'new\n' > NEW.txt && git add NEW.txt && git commit -qm advance )
out="$(/bin/sh journey/bin/check-uat-evidence.sh "$rep" "$repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "evidence: still green after HEAD advances past repo_commit"

# O1 proof: quote planted in WORKING TREE only is not evidence
( cd "$repo" && printf 'PLANTED unique quote\n' >> src/pda/send.ts )
bad="$uat_ev_tmp/planted/UAT_REPORT_2026-07-08.md"; mkdir -p "$uat_ev_tmp/planted"
sed 's|"throw new Error(.portal timeout.)"|"PLANTED unique quote"|; s|send.ts:12|send.ts:13|' "$rep" > "$bad"
cp -R "$uat_ev_tmp/evidence" "$uat_ev_tmp/planted/evidence"
out="$(/bin/sh journey/bin/check-uat-evidence.sh "$bad" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "evidence O1 rc: working-tree plant rejected"
assert_contains "$out" "QUOTE_UNVERIFIED" "evidence O1 code: pinned-commit read"
( cd "$repo" && git checkout -q -- src/pda/send.ts )

uat_ev_red() { # $1=name $2=sed $3=code
  _d="$uat_ev_tmp/$1"; mkdir -p "$_d"; cp -R "$uat_ev_tmp/evidence" "$_d/evidence"
  sed "$2" "$rep" > "$_d/UAT_REPORT_2026-07-08.md"
  _o="$(/bin/sh journey/bin/check-uat-evidence.sh "$_d/UAT_REPORT_2026-07-08.md" "$repo" 2>&1)"; _rc=$?
  assert_eq "1" "$_rc" "evidence red rc: $1"
  assert_contains "$_o" "$3" "evidence red code: $1"
}
uat_ev_red commit-unknown "s/$commit/1111111111111111111111111111111111111111/" COMMIT_UNKNOWN
uat_ev_red fabricated-quote 's/portal timeout/portal timeout NEVER/' QUOTE_UNVERIFIED
uat_ev_red wrong-line 's|send.ts:12|send.ts:3|' LINE_MISMATCH
uat_ev_red search-relpath-gone 's|" config/|" nonexistent/|' SEARCH_ERROR
uat_ev_red art-hash 's/sha256:'"$artsha"'/sha256:0000000000000000000000000000000000000000000000000000000000000000/' ARTIFACT_HASH_MISMATCH

# W3 (D3-b): search relpath "." (repo root) must not spuriously fail via
# git's own rev:path quirk on `cat-file -e <commit>:.` — the verifier
# prompt explicitly encourages a broadened, whole-tree search on a
# [C-absent] confirm ("a wider pattern, a different directory"), and "."
# is the natural literal expression of "search everywhere". Before the
# uat_check_search_line fix this reproducibly returned SEARCH_ERROR even
# though `git grep -- .` against the same commit works fine and the
# literal is genuinely absent from the whole tree — confirmed independent
# of any model, live with plain git (characterization report D3-b).
_d="$uat_ev_tmp/root-relpath"; mkdir -p "$_d"; cp -R "$uat_ev_tmp/evidence" "$_d/evidence"
sed 's|" config/|" .|' "$rep" > "$_d/UAT_REPORT_2026-07-08.md"
_o="$(/bin/sh journey/bin/check-uat-evidence.sh "$_d/UAT_REPORT_2026-07-08.md" "$repo" 2>&1)"; _rc=$?
assert_eq "0" "$_rc" "evidence: search relpath '.' (repo root) succeeds, not SEARCH_ERROR (W3/D3-b)"

# ARTIFACT_MISSING: remove the artifact file
mkdir -p "$uat_ev_tmp/noart"; cp "$rep" "$uat_ev_tmp/noart/"
out="$(/bin/sh journey/bin/check-uat-evidence.sh "$uat_ev_tmp/noart/UAT_REPORT_2026-07-08.md" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "evidence red rc: artifact-missing"
assert_contains "$out" "ARTIFACT_MISSING" "evidence red code: artifact-missing"

# SEARCH_DIVERGED: plant the searched literal in the pinned commit
repo2="$uat_ev_tmp/repo2"; mkdir -p "$repo2"; commit2="$(uat_mk_repo "$repo2")"
( cd "$repo2" && printf 'export PORTAL_MAGIC_BYPASS=1\n' > config/bypass.ts && git add -A && git commit -qm plant && git rev-parse HEAD ) > "$uat_ev_tmp/c2"
commit2="$(cat "$uat_ev_tmp/c2")"
mkdir -p "$uat_ev_tmp/div"; cp -R "$uat_ev_tmp/evidence" "$uat_ev_tmp/div/evidence"
uat_mk_report "$tpl" "$uat_ev_tmp/div/UAT_REPORT_2026-07-08.md" "$commit2" "$artsha" "$artsha2"
out="$(/bin/sh journey/bin/check-uat-evidence.sh "$uat_ev_tmp/div/UAT_REPORT_2026-07-08.md" "$repo2" 2>&1)"; rc=$?
assert_eq "1" "$rc" "evidence red rc: search-diverged"
assert_contains "$out" "SEARCH_DIVERGED" "evidence red code: search-diverged"

# QUOTE_UNVERIFIED: citation missing ":NN" must not fall back to whole-file
# sed (which would let the quote "verify" anywhere in the file). This gate is
# intentionally standalone — the mutated report below would also fail lint,
# but that must not matter: this case proves the evidence gate fails closed
# on its own, without relying on lint having run first.
uat_ev_red no-line-number 's|src/pda/send.ts:12 — |src/pda/send.ts — |' QUOTE_UNVERIFIED

# TOOL_MISSING: with no sha256 tool on PATH, the gate must fail closed
# (rc 1 + TOOL_MISSING) rather than pass vacuously. Shim PATH with symlinks
# to every non-sha binary the gate needs, deliberately omitting
# sha256sum/shasum.
uat_ev_shim="$uat_ev_tmp/shim"; mkdir -p "$uat_ev_shim"
for _b in git awk sed grep tr head sort uniq cat mktemp dirname basename rm wc; do
  _real="$(command -v "$_b")" && ln -s "$_real" "$uat_ev_shim/$_b"
done
out="$(PATH="$uat_ev_shim" /bin/sh journey/bin/check-uat-evidence.sh "$rep" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "evidence: sha-tool absence fails closed (rc)"
assert_contains "$out" "TOOL_MISSING" "evidence: sha-tool absence fails closed (code)"

# MKTEMP_FAILED (M-T1-4, final review): the $_fail accumulator itself is
# built via an unguarded `_fail="$(mktemp)"`. If mktemp fails, $_fail is
# empty; every violation append below is `echo x >>""` (a silent no-op on
# this shell), and `[ -s "$_fail" ]` reads false — the gate exits 0 WITH A
# REAL VIOLATION PRESENT. Reproduced by hand pre-fix: PATH-shimmed with a
# `mktemp` that always fails, against the fabricated-quote fixture below
# (a real QUOTE_UNVERIFIED), the unfixed gate returned rc 0 with the
# QUOTE_UNVERIFIED line printed to stderr and swallowed — the fail-open in
# the wild (see uat-task-8-report.md for the transcript).
#
# Note: TMPDIR alone does not reproduce mktemp failure on macOS — bare
# `mktemp` prefers _CS_DARWIN_USER_TEMP_DIR over $TMPDIR and silently falls
# back to it even under a nonexistent or chmod-000-unwritable TMPDIR
# (probed empirically). A PATH-shimmed fake `mktemp` that always fails is
# used instead — the same idiom as the TOOL_MISSING shim above, generalized
# to the one binary this gate cannot do without.
uat_ev_mktemp_shim="$uat_ev_tmp/mktemp-shim"; mkdir -p "$uat_ev_mktemp_shim"
for _b in git awk sed grep tr head sort uniq cat dirname basename rm wc sha256sum shasum; do
  _real="$(command -v "$_b")" && ln -s "$_real" "$uat_ev_mktemp_shim/$_b"
done
cat > "$uat_ev_mktemp_shim/mktemp" <<'SHIM'
#!/bin/sh
printf 'mktemp: simulated failure (fail-closed proof)\n' >&2
exit 1
SHIM
chmod +x "$uat_ev_mktemp_shim/mktemp"

uat_ev_mktemp_dir="$uat_ev_tmp/mktemp-fail"; mkdir -p "$uat_ev_mktemp_dir"
cp -R "$uat_ev_tmp/evidence" "$uat_ev_mktemp_dir/evidence"
sed 's/portal timeout/portal timeout NEVER/' "$rep" > "$uat_ev_mktemp_dir/UAT_REPORT_2026-07-08.md"
out="$(PATH="$uat_ev_mktemp_shim" /bin/sh journey/bin/check-uat-evidence.sh "$uat_ev_mktemp_dir/UAT_REPORT_2026-07-08.md" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "evidence: mktemp failure on \$_fail fails closed, not fail-open (rc)"
assert_contains "$out" "MKTEMP_FAILED" "evidence: mktemp failure on \$_fail fails closed, not fail-open (code)"

rm -rf "$uat_ev_tmp"
