# check-extracted-provenance_test.sh — gate E2 vs a pinned commit
# (spec §4.3/§7.2). Fixture-git-repo harness idiom mirrors
# journey/tests/uat-evidence_test.sh: a real mktemp git repo committed once,
# staging-file variants built by sed-mutating the golden fixture (so every
# RED case differs from the PASS case by exactly one thing), PATH-shim
# proofs for TOOL_MISSING/MKTEMP_FAILED.
# shellcheck shell=sh
. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
GATE="$TESTS_DIR/../bin/check-extracted-provenance.sh"
GOOD="$TESTS_DIR/fixtures/extracted/good/JOURNEY_EXTRACTED.golden.md"
LINTFX="$TESTS_DIR/fixtures/extracted/lint"

_e2p_tmp="$(mktemp -d)"

# ── fixture git repo: real files backing every citation in the golden
# fixture (journey/tests/fixtures/extracted/good/JOURNEY_EXTRACTED.golden.md)
# ─ EXTRACTED-1: src/routes/invoices.ts:42
# ─ EXTRACTED-2: src/routes/auth.ts:88 + docs/FLW.md#Password reset
# ─ EXTRACTED-3: src/routes/bookings.ts:61
# ─ EXTRACTED-4: src/components/InvoicesToolbar.tsx:19 (REJECTED entry)
# ─ EXTRACTED-5: src/routes/invoices.ts:47 + docs/FLW.md#Invoice resubmission
#                + prior_e2e: tests/e2e/invoice-resubmit.spec.ts
#                (CONFIRMED, promoted_as: JOURNEY-501 — terminal entry)
# ─ EXTRACTED-6: docs/FLW.md#Password reset + search-cite "rateLimit" (DX-1
#                absence-evidence form — 0 hits anywhere in this fixture
#                repo, so it verifies clean)
_e2p_mk_repo() { # $1=dir ; echoes HEAD sha
  ( cd "$1" && git init -q . && git config user.email t@t && git config user.name t
    mkdir -p src/routes src/components docs tests/e2e

    { i=1; while [ "$i" -le 41 ]; do printf '// pad%s\n' "$i"; i=$((i + 1)); done
      printf "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)\n"
      i=43; while [ "$i" -le 46 ]; do printf '// pad%s\n' "$i"; i=$((i + 1)); done
      printf "return res.status(200).json({ status: 'ACCEPTED', row })\n"
    } > src/routes/invoices.ts

    { i=1; while [ "$i" -le 87 ]; do printf '// pad%s\n' "$i"; i=$((i + 1)); done
      printf "router.post('/reset-password', issueOneTimeToken)\n"
    } > src/routes/auth.ts

    { i=1; while [ "$i" -le 60 ]; do printf '// pad%s\n' "$i"; i=$((i + 1)); done
      printf "if (conflict) { warnAfterSave(); }\n"
    } > src/routes/bookings.ts

    { i=1; while [ "$i" -le 18 ]; do printf '// pad%s\n' "$i"; i=$((i + 1)); done
      printf "<button>Export CSV</button>\n"
    } > src/components/InvoicesToolbar.tsx

    printf '# Flows\n\n## Password reset\n\nThe password reset flow.\n\n## Invoice resubmission\n\nInvoice resubmission notes; the response DOES include the row per current code.\n' > docs/FLW.md

    # V-E2 F1 fence-blindness fixtures (both directions):
    # (a) docs/GUIDE.md — "Fenced Pseudo Heading" exists ONLY as a `#` line
    #     INSIDE a ``` fenced code block; a cite to it must be
    #     SECTION_HEADING_MISSING, never verified (the fail-open direction).
    # (b) docs/DEPLOY.md — a REAL unique `# Deploy` heading plus the same
    #     text as a fenced `# Deploy` code line; a cite to it must verify as
    #     exactly 1 match, never a false SECTION_AMBIGUOUS.
    printf '# Guide\n\nProse before the fence.\n\n```\n# Fenced Pseudo Heading\nsome code\n```\n\nProse after the fence.\n' > docs/GUIDE.md
    printf '# Deploy\n\nRun this:\n\n```sh\n# Deploy\nmake deploy\n```\n' > docs/DEPLOY.md

    printf "test('invoice resubmit', () => {});\n" > tests/e2e/invoice-resubmit.spec.ts

    git add -A && git commit -qm fixture && git rev-parse HEAD )
}

# A second, additive commit on the same repo: docs/FLW.md gains a SECOND
# heading whose stripped text is also exactly "Password reset" (at a
# different level) — the SECTION_AMBIGUOUS fixture. Everything else the
# golden fixture cites is unaffected (additive-only commit).
_e2p_mk_ambiguous_commit() { # $1=dir (already committed base) ; echoes new HEAD sha
  ( cd "$1" &&
    printf '\n### Password reset\n\nDuplicate heading text (different level), for SECTION_AMBIGUOUS.\n' >> docs/FLW.md &&
    git add -A && git commit -qm "add dup heading" && git rev-parse HEAD )
}

repo="$_e2p_tmp/repo"; mkdir -p "$repo"
commit="$(_e2p_mk_repo "$repo")"
ambig_commit="$(_e2p_mk_ambiguous_commit "$repo")"

base="$_e2p_tmp/base/JOURNEY_EXTRACTED.md"; mkdir -p "$_e2p_tmp/base"
sed "s/^extraction_commit: .*/extraction_commit: $commit/" "$GOOD" > "$base"

# ── Positive: golden verifies against the pinned commit, one-line summary ──
out="$(/bin/sh "$GATE" "$base" "$repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "provenance: golden verifies against pinned commit"
assert_contains "$out" "OK: 6 entries, 5 code-cite(s), 3 section-cite(s), 1 search-cite(s), 1 prior_e2e checked" \
  "provenance: success summary line counts entries/code-cites/section-cites/search-cites/prior_e2e"

# ── Usage / missing-file / missing-dir: exit 2 ─────────────────────────────
assert_exit 2 /bin/sh "$GATE"
assert_exit 2 /bin/sh "$GATE" "$base"
assert_exit 2 /bin/sh "$GATE" "$base" "$repo" extra-arg
assert_exit 2 /bin/sh "$GATE" "$_e2p_tmp/does-not-exist.md" "$repo"
assert_exit 2 /bin/sh "$GATE" "$base" "$_e2p_tmp/does-not-exist-dir"

# ── LINT_FAILED — composition pass-through (not a §7.2 schema code) ───────
out="$(/bin/sh "$GATE" "$LINTFX/bad-header.md" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "provenance: LINT_FAILED rc"
assert_contains "$out" "LINT_FAILED" "provenance: LINT_FAILED pass-through when lint-journey-extracted.sh fails"

# ── generic RED helper: same commit, one sed mutation vs the golden ───────
_e2p_case() { # $1=name $2=sed-script $3=expected-code-substring
  _d="$_e2p_tmp/$1"; mkdir -p "$_d"
  sed "s/^extraction_commit: .*/extraction_commit: $commit/" "$GOOD" | sed "$2" > "$_d/JOURNEY_EXTRACTED.md"
  _o="$(/bin/sh "$GATE" "$_d/JOURNEY_EXTRACTED.md" "$repo" 2>&1)"; _rc=$?
  assert_eq "1" "$_rc" "provenance red rc: $1"
  assert_contains "$_o" "$3" "provenance red code: $1"
}

_e2p_case commit-unknown \
  's/^extraction_commit: .*/extraction_commit: 1111111111111111111111111111111111111111/' \
  COMMIT_UNKNOWN

_e2p_case quote-unverified 's/resubmitHandler/resubmitHandlerNEVER/' QUOTE_UNVERIFIED

_e2p_case line-mismatch 's/invoices.ts:42/invoices.ts:1/' LINE_MISMATCH

_e2p_case section-file-missing 's#docs/FLW.md#docs/NOPE.md#' SECTION_FILE_MISSING

_e2p_case section-heading-missing 's/#Password reset/#Nonexistent Heading/' SECTION_HEADING_MISSING

_e2p_case prior-e2e-missing \
  's#tests/e2e/invoice-resubmit.spec.ts#tests/e2e/nope.spec.ts#' \
  PRIOR_E2E_MISSING

# ── DX-1 search-cite (absence-evidence form): reuses uat-lib.sh's search
# checker unchanged. EXTRACTED-6's "rateLimit" literal has zero hits
# anywhere in the fixture repo (golden PASS case, proven above by the
# summary-line count). A literal that DOES exist (resubmitHandler, in
# src/routes/invoices.ts) turns the same absence-cite into a genuine
# divergence; a relpath absent at the pinned commit is SEARCH_ERROR.
_e2p_case search-diverged \
  's/"rateLimit" src/"resubmitHandler" src/' \
  'SEARCH_DIVERGED: EXTRACTED-6: "resubmitHandler" found in src'

_e2p_case search-error \
  's#"rateLimit" src#"rateLimit" nope#' \
  'SEARCH_ERROR: EXTRACTED-6: nope not in pinned commit'

# ── SECTION_AMBIGUOUS: same staging file, pinned to the AMBIGUOUS commit
# (docs/FLW.md now has two headings whose stripped text is "Password reset")
_d="$_e2p_tmp/section-ambiguous"; mkdir -p "$_d"
sed "s/^extraction_commit: .*/extraction_commit: $ambig_commit/" "$GOOD" > "$_d/JOURNEY_EXTRACTED.md"
_o="$(/bin/sh "$GATE" "$_d/JOURNEY_EXTRACTED.md" "$repo" 2>&1)"; _rc=$?
assert_eq "1" "$_rc" "provenance red rc: section-ambiguous"
assert_contains "$_o" "SECTION_AMBIGUOUS: EXTRACTED-2: docs/FLW.md#Password reset" \
  "provenance red code: section-ambiguous (2 matches, fail closed)"

# ── V-E2 F1, direction (a) — the fail-OPEN direction: the cited heading
# text exists ONLY as a `#` line INSIDE a ``` fenced code block
# (docs/GUIDE.md). Pre-fix, the bare `grep '^#'` heading extraction counted
# it as a heading and VERIFIED the cite (rc=0, captured verbatim in the
# verifier's repro) — which would let a stale cite survive a real heading
# rename whenever the old text lives on in any fence. Must be
# SECTION_HEADING_MISSING.
_e2p_case fenced-pseudo-heading \
  's|docs/FLW.md#Password reset|docs/GUIDE.md#Fenced Pseudo Heading|' \
  "SECTION_HEADING_MISSING: EXTRACTED-2: docs/GUIDE.md#Fenced Pseudo Heading"

# ── V-E2 F1, direction (b) — the false-ambiguous nuisance direction: a
# REAL, unique `# Deploy` heading whose text also appears as a fenced
# `# Deploy` code line (docs/DEPLOY.md). Pre-fix this was a false
# SECTION_AMBIGUOUS (2 matches); fence-aware extraction sees exactly 1
# heading and the cite verifies.
_d="$_e2p_tmp/real-heading-fenced-dup"; mkdir -p "$_d"
sed "s/^extraction_commit: .*/extraction_commit: $commit/" "$GOOD" \
  | sed 's|docs/FLW.md#Password reset|docs/DEPLOY.md#Deploy|' > "$_d/JOURNEY_EXTRACTED.md"
_o="$(/bin/sh "$GATE" "$_d/JOURNEY_EXTRACTED.md" "$repo" 2>&1)"; _rc=$?
assert_eq "0" "$_rc" "provenance: real heading verifies despite an identical fenced # line (no false SECTION_AMBIGUOUS, V-E2 F1)"
assert_not_contains "$_o" "SECTION_AMBIGUOUS" "provenance: fenced # duplicate of a real heading is not counted as a second match"

# ── Terminal-entry integrity (§14 Q7): EXTRACTED-5 carries promoted_as:
# JOURNEY-501 + confirmation_status: CONFIRMED — a broken cite on it must
# still fail. Its code-cite quote (invoices.ts:47) is unique in the file, so
# mutating it cannot collide with any other entry's citation.
_e2p_case terminal-entry-broken-cite \
  "s/status: 'ACCEPTED', row })/status: 'ACCEPTED', row, NEVER })/" \
  "QUOTE_UNVERIFIED: EXTRACTED-5"

# ── REJECTED-entry integrity: EXTRACTED-4 (confirmation_status: REJECTED)
# is a terminal-in-a-different-sense entry — still gets its citation
# byte-verified. Its quote is unique in the file.
_e2p_case rejected-entry-broken-cite \
  's/<button>Export CSV<\/button>/<button>Export CSV NEVER<\/button>/' \
  "QUOTE_UNVERIFIED: EXTRACTED-4"

# ── Working-tree independence (D2-class proof): editing a cited file in the
# WORKING TREE only (no new commit) must never affect a citation already
# pinned to the existing commit — every read in this gate is `git show`/
# `git cat-file` against $commit, never the filesystem.
( cd "$repo" && printf 'WORKING TREE ONLY EDIT — never committed\n' >> src/routes/invoices.ts )
out="$(/bin/sh "$GATE" "$base" "$repo" 2>&1)"; rc=$?
assert_eq "0" "$rc" "provenance: working-tree edit after commit does not affect pinned-commit citations (D2-class)"
( cd "$repo" && git checkout -q -- src/routes/invoices.ts )

# ── Fail-slow (house rule 2): two entries, two INDEPENDENT violations,
# both reported in the SAME run — proves the accumulator (never
# `| while read`) actually survives to the final exit.
_d="$_e2p_tmp/multi-violation"; mkdir -p "$_d"
sed "s/^extraction_commit: .*/extraction_commit: $commit/" "$GOOD" \
  | sed 's/resubmitHandler/resubmitHandlerNEVER/' \
  | sed 's/#Password reset/#Nonexistent Heading/' \
  > "$_d/JOURNEY_EXTRACTED.md"
_o="$(/bin/sh "$GATE" "$_d/JOURNEY_EXTRACTED.md" "$repo" 2>&1)"; _rc=$?
assert_eq "1" "$_rc" "provenance: fail-slow multi-violation rc"
assert_contains "$_o" "QUOTE_UNVERIFIED: EXTRACTED-1" "provenance: fail-slow first independent violation present"
assert_contains "$_o" "SECTION_HEADING_MISSING: EXTRACTED-2" "provenance: fail-slow second independent violation present in the SAME run"

# ── NO_SOURCE_LINES — anti-vacuous backstop. Unreachable through the real
# lint composition: lint-journey-extracted.sh's own SOURCES_MISSING (>=1
# per entry) and NO_EXTRACTED_ENTRIES (>=1 entry) already guarantee this
# gate never sees a lint-clean file with zero total extraction_sources
# lines. Proven here by an HONEST, DOCUMENTED BYPASS of the lint
# composition step (not a production escape hatch — the real gate has no
# such flag): copy the gate script into an isolated bin/ dir alongside a
# stub lint-journey-extracted.sh that always exits 0, with the real lib/
# files symlinked in unchanged, then feed it a hand-built staging file that
# is structurally readable (valid header + one entry) but carries zero
# extraction_sources lines — a shape lint would normally reject.
_stub="$_e2p_tmp/stub"; mkdir -p "$_stub/bin" "$_stub/lib"
cp "$GATE" "$_stub/bin/check-extracted-provenance.sh"
chmod +x "$_stub/bin/check-extracted-provenance.sh"
ln -s "$TESTS_DIR/../lib/journey-lib.sh" "$_stub/lib/journey-lib.sh"
ln -s "$TESTS_DIR/../lib/uat-lib.sh" "$_stub/lib/uat-lib.sh"
cat > "$_stub/bin/lint-journey-extracted.sh" <<'STUBLINT'
#!/bin/sh
# Stub used ONLY by check-extracted-provenance_test.sh to prove the
# NO_SOURCE_LINES anti-vacuous backstop is reachable when lint composition
# is bypassed. Always passes.
exit 0
STUBLINT
chmod +x "$_stub/bin/lint-journey-extracted.sh"

cat > "$_e2p_tmp/no-sources.md" <<NOSRC
# JOURNEY-EXTRACTED
extraction_commit: $commit
manifest_sha256:   0000000000000000000000000000000000000000000000000000000000000000

## EXTRACTED-1 — "no sources anywhere"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [C]
origin:              EXTRACTED
extraction_sources:
NOSRC

out="$(/bin/sh "$_stub/bin/check-extracted-provenance.sh" "$_e2p_tmp/no-sources.md" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "provenance: NO_SOURCE_LINES rc (lint composition bypassed via stub, documented above)"
assert_contains "$out" "NO_SOURCE_LINES" "provenance: NO_SOURCE_LINES code"

# ── TOOL_MISSING: PATH shim excluding git (uat-evidence_test.sh precedent)─
_shim_nogit="$_e2p_tmp/shim-nogit"; mkdir -p "$_shim_nogit"
for _b in sh awk sed grep tr head sort uniq cat mktemp dirname basename rm wc printf; do
  _real="$(command -v "$_b")" && ln -s "$_real" "$_shim_nogit/$_b"
done
out="$(PATH="$_shim_nogit" /bin/sh "$GATE" "$base" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "provenance: git absence fails closed (rc)"
assert_contains "$out" "TOOL_MISSING" "provenance: git absence fails closed (code)"

# ── MKTEMP_FAILED: PATH shim with a fake mktemp that always fails ─────────
_shim_nomktemp="$_e2p_tmp/shim-nomktemp"; mkdir -p "$_shim_nomktemp"
for _b in git sh awk sed grep tr head sort uniq cat dirname basename rm wc printf; do
  _real="$(command -v "$_b")" && ln -s "$_real" "$_shim_nomktemp/$_b"
done
cat > "$_shim_nomktemp/mktemp" <<'MKSHIM'
#!/bin/sh
printf 'mktemp: simulated failure (fail-closed proof)\n' >&2
exit 1
MKSHIM
chmod +x "$_shim_nomktemp/mktemp"
out="$(PATH="$_shim_nomktemp" /bin/sh "$GATE" "$base" "$repo" 2>&1)"; rc=$?
assert_eq "1" "$rc" "provenance: mktemp failure fails closed, not fail-open (rc)"
assert_contains "$out" "MKTEMP_FAILED" "provenance: mktemp failure fails closed, not fail-open (code)"

rm -rf "$_e2p_tmp"
