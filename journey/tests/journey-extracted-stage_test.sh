#!/bin/sh
# shellcheck shell=sh
# journey-extracted-stage_test.sh — journey-extracted-stage.sh (task E4,
# spec §4.3/§6.1/§14): deterministic CANDIDATES -> JOURNEY_EXTRACTED.md
# staging, incl. the §6.1 re-stage preserve-and-reverify contract. Fixture
# idiom mirrors check-extracted-provenance_test.sh (real mktemp git repo,
# sed-stamped commit) + check-extraction-coverage_test.sh (sed-stamped
# manifest_sha256 golden pair, one-thing-different RED mutations).
. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$TESTS_DIR/../bin"
GATE="$BIN/journey-extracted-stage.sh"
LIB="$TESTS_DIR/../lib/journey-lib.sh"
FX="$TESTS_DIR/fixtures/extracted/stage"
GOLD_CAND="$FX/CANDIDATES.golden.md"
GOLD_MF="$FX/MANIFEST.golden.md"

_jes_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}
_sha_jes() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }
_field_jes() { ( JOURNEY_EXTRACTED="$2"; export JOURNEY_EXTRACTED; # shellcheck disable=SC1090
  . "$LIB"; extracted_field "$1" "$3" ); } # ID FILE KEY
_block_jes() { ( JOURNEY_EXTRACTED="$2"; export JOURNEY_EXTRACTED; # shellcheck disable=SC1090
  . "$LIB"; extracted_block "$1" ); } # ID FILE

_jt="$(mktemp -d)"

# ── fixture git repo: real files backing every citation in CANDIDATES.golden.md
# ─ candidate 1: src/routes/invoices.ts:42, docs/FLW.md#Invoice resubmission,
#                prior_e2e: tests/e2e/invoice-resubmit.spec.ts
# ─ candidate 2: src/routes/auth.ts:12
_jes_mk_repo() { # $1=dir ; echoes HEAD sha
  ( cd "$1" && git init -q . && git config user.email t@t && git config user.name t
    mkdir -p src/routes docs tests/e2e

    { i=1; while [ "$i" -le 41 ]; do printf '// pad%s\n' "$i"; i=$((i + 1)); done
      printf "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)\n"
    } > src/routes/invoices.ts

    { i=1; while [ "$i" -le 11 ]; do printf '// pad%s\n' "$i"; i=$((i + 1)); done
      printf "router.get('/login', renderLogin)\n"
    } > src/routes/auth.ts

    printf '# Flows\n\n## Invoice resubmission\n\nInvoice resubmission notes.\n' > docs/FLW.md
    printf "test('invoice resubmit', () => {});\n" > tests/e2e/invoice-resubmit.spec.ts

    git add -A && git commit -qm fixture && git rev-parse HEAD )
}

repo="$_jt/repo"; mkdir -p "$repo"
commit="$(_jes_mk_repo "$repo")"

# golden CANDIDATES/MANIFEST, commit-stamped (mirrors check-extraction-
# coverage_test.sh's placeholder-then-sed idiom)
gold_cand="$_jt/CANDIDATES.md"
sed "s/^extraction_commit: .*/extraction_commit: $commit/" "$GOLD_CAND" > "$gold_cand"
gold_mf="$_jt/MANIFEST.md"
sed "s/^extraction_commit: .*/extraction_commit: $commit/" "$GOLD_MF" > "$gold_mf"

# manifest_sha256 of the golden manifest's machine block — the SAME
# BEGIN..END-inclusive recipe the runner/check-extraction-coverage.sh use
# — computed ONCE here for every hand-built OUT_EXTRACTED fixture below.
_mf_block_sha() { # MANIFEST_PATH
  awk '/^EXTRACTION-MANIFEST BEGIN$/{f=1} f{print} /^EXTRACTION-MANIFEST END$/{exit}' "$1" \
    | { if command -v sha256sum >/dev/null 2>&1; then sha256sum; else shasum -a 256; fi; } \
    | awk '{print $1}'
}
gold_mf_sha="$(_mf_block_sha "$gold_mf")"

# ═══════════════════════════════════════════════════════════════════════
# Usage / missing-arg (exit 2)
# ═══════════════════════════════════════════════════════════════════════

assert_exit 2 /bin/sh "$GATE"
assert_exit 2 /bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo"
assert_exit 2 /bin/sh "$GATE" "$_jt/does-not-exist.md" "$gold_mf" "$repo" "$_jt/o1/E.md"
assert_exit 2 /bin/sh "$GATE" "$gold_cand" "$gold_mf" "$_jt/does-not-exist-dir" "$_jt/o2/E.md"
assert_exit 2 /bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$_jt/o3/E.md" "$_jt/does-not-exist-gaps.md"
assert_exit 2 /bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$_jt/o4/E.md" extra1 extra2

# ═══════════════════════════════════════════════════════════════════════
# Booby-trap composition order: missing REPO_ROOT fails before ANY gate
# runs — proved with a `git` PATH-shim sentinel (journey-gen-check-
# candidate.sh is not even invoked: git is only ever reached through the
# composed provenance gate, which never runs when REPO_ROOT fails first).
# ═══════════════════════════════════════════════════════════════════════

_shim="$_jt/shim"; mkdir -p "$_shim"
_sentinel="$_jt/SENTINEL"
rm -f "$_sentinel"
cat > "$_shim/git" << SHIMGIT
#!/bin/sh
touch "$_sentinel"
exit 1
SHIMGIT
chmod +x "$_shim/git"
for _b in sh awk sed grep tr head sort uniq cat mktemp dirname basename rm wc printf date find; do
  _real="$(command -v "$_b")" && ln -s "$_real" "$_shim/$_b"
done
_o="$(PATH="$_shim" /bin/sh "$GATE" "$gold_cand" "$gold_mf" "$_jt/no-such-repo" "$_jt/trap-out/E.md" 2>&1)"; _ec=$?
assert_eq "2" "$_ec" "booby-trap: missing REPO_ROOT rc (usage-class exit 2, same as check-extracted-provenance.sh's own REPO_ROOT check)"
assert_contains "$_o" "repo root not found" "booby-trap: names the missing REPO_ROOT"
[ ! -f "$_sentinel" ]; assert_eq 0 $? "booby-trap: git NEVER invoked (composed provenance gate never even started)"
[ ! -f "$_jt/trap-out/E.md" ]; assert_eq 0 $? "booby-trap: nothing created when REPO_ROOT is missing"

# ═══════════════════════════════════════════════════════════════════════
# Golden fresh stage — end to end
# ═══════════════════════════════════════════════════════════════════════

fresh_out="$_jt/fresh/JOURNEY_EXTRACTED.md"
_o="$(/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$fresh_out" 2>&1)"; _ec=$?
assert_eq "0" "$_ec" "golden fresh stage: exit 0"
assert_contains "$_o" "2 new entries staged" "golden fresh stage: summary line names the count"
[ -f "$fresh_out" ]; assert_eq 0 $? "golden fresh stage: OUT_EXTRACTED created"

assert_exit 0 /bin/sh "$BIN/lint-journey-extracted.sh" "$fresh_out"
assert_exit 0 /bin/sh "$BIN/check-extracted-provenance.sh" "$fresh_out" "$repo"
assert_exit 0 /bin/sh "$BIN/check-extraction-coverage.sh" "$gold_mf" "$fresh_out"

_g="$(cat "$fresh_out")"
assert_contains "$_g" '## EXTRACTED-1 — "Invoice resubmission after a schema-error rejection"' "golden fresh stage: ids assigned from 1"
assert_contains "$_g" '## EXTRACTED-2 — "Login screen reachable directly"' "golden fresh stage: second candidate gets EXTRACTED-2"
assert_eq "true" "$(_field_jes EXTRACTED-1 "$fresh_out" needs_human_confirm)" "golden fresh stage: needs_human_confirm forced true"
assert_eq "PENDING" "$(_field_jes EXTRACTED-1 "$fresh_out" confirmation_status)" "golden fresh stage: confirmation_status forced PENDING"
assert_eq "EXTRACTED" "$(_field_jes EXTRACTED-1 "$fresh_out" origin)" "golden fresh stage: origin forced EXTRACTED"
assert_eq "UNWRITTEN" "$(_field_jes EXTRACTED-1 "$fresh_out" author_status)" "golden fresh stage: author_status forced UNWRITTEN"
assert_eq "[C]" "$(_field_jes EXTRACTED-1 "$fresh_out" grade)" "golden fresh stage: grade copied from the candidate"
assert_eq "tests/e2e/invoice-resubmit.spec.ts" "$(_field_jes EXTRACTED-1 "$fresh_out" prior_e2e)" "golden fresh stage: prior_e2e carried over from the candidate's EXTRACTION-SOURCES block"
_b1="$(_block_jes EXTRACTED-1 "$fresh_out")"
assert_contains "$_b1" 'src/routes/invoices.ts:42 — "router.post' "golden fresh stage: extraction_sources citation carried over"
assert_eq "PENDING" "$(_field_jes EXTRACTED-2 "$fresh_out" confirmation_status)" "golden fresh stage: second entry also PENDING"
assert_eq "40" "$(awk '/^extraction_commit:/{print length($2); exit}' "$fresh_out")" "golden fresh stage: header extraction_commit is 40 chars"
assert_eq "64" "$(awk '/^manifest_sha256:/{print length($2); exit}' "$fresh_out")" "golden fresh stage: header manifest_sha256 is 64 chars"

# ═══════════════════════════════════════════════════════════════════════
# Degenerate whole-file tokens
# ═══════════════════════════════════════════════════════════════════════

printf 'EXTRACTION-FAILED: repo has no discoverable routes\n' > "$_jt/failed-cand.md"
_o="$(/bin/sh "$GATE" "$_jt/failed-cand.md" "$gold_mf" "$repo" "$_jt/failed-out/E.md" 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "EXTRACTION-FAILED: exit non-zero"
assert_contains "$_o" "EXTRACTION-FAILED: repo has no discoverable routes" "EXTRACTION-FAILED: model's own token surfaced"
[ ! -f "$_jt/failed-out/E.md" ]; assert_eq 0 $? "EXTRACTION-FAILED: nothing created"

printf 'NO-JOURNEYS-FOUND\n' > "$_jt/none-cand.md"
none_out="$_jt/none-out/JOURNEY_EXTRACTED.md"
_o="$(/bin/sh "$GATE" "$_jt/none-cand.md" "$gold_mf" "$repo" "$none_out" 2>&1)"; _ec=$?
assert_eq "0" "$_ec" "NO-JOURNEYS-FOUND: exit 0 (legitimate outcome, spec §4.1)"
[ ! -f "$none_out" ]; assert_eq 0 $? "NO-JOURNEYS-FOUND: OUT_EXTRACTED never created"
_att="$_jt/none-out/EXTRACTED_ATTEMPTS.md"
[ -f "$_att" ]; assert_eq 0 $? "NO-JOURNEYS-FOUND: EXTRACTED_ATTEMPTS.md written as OUT_EXTRACTED's sibling"
assert_contains "$(cat "$_att")" "NO-JOURNEYS-FOUND" "NO-JOURNEYS-FOUND: attempts log records the token"

# ═══════════════════════════════════════════════════════════════════════
# CANDIDATES_HEADER_INVALID (DX-2, live-characterization fix wave) — the
# CANDIDATES file's FIRST NON-BLANK line must be EXACTLY
# "extraction_commit: <40-hex>", checked before any candidate-block
# parsing. Two RED shapes reproduce the live characterization exactly:
# a prose preamble before the real header (an agentic backend narrating
# "I'll generate..." before its fenced content — attempt1-raw.md), and a
# DECOY extraction_commit line embedded in narration ahead of the real
# one (the old header-scan was position-agnostic and let the decoy win —
# cross-checked downstream by MANIFEST_COMMIT_MISMATCH before this fix).
# ═══════════════════════════════════════════════════════════════════════

_d="$_jt/header-preamble"; mkdir -p "$_d"
cat > "$_d/CANDIDATES.md" << PREEOF
I'll generate \`step0-out/journey-candidates.md\` using only the declared inputs.

extraction_commit: $commit

## JOURNEY-CANDIDATE — "Invoice resubmission after a schema-error rejection"
origin:          EXTRACTED
persona:         ops user (inferred from the route's auth middleware)
goal:            resubmit a corrected invoice after a schema-error rejection
priority:        P2
covers:          FEAT-014
flows:           []
oracle_surface:  UI+API
negative_states: schema_error
grade:           [C]
steps:
  1. land on /invoices
oracle:          row status=ACCEPTED
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

\`\`\`json field_sources
{}
\`\`\`

## EXTRACTION-SOURCES
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)"
PREEOF
_o="$(/bin/sh "$GATE" "$_d/CANDIDATES.md" "$gold_mf" "$repo" "$_d/out/E.md" 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "CANDIDATES_HEADER_INVALID (prose preamble): exit non-zero"
assert_contains "$_o" "CANDIDATES_HEADER_INVALID" "CANDIDATES_HEADER_INVALID (prose preamble): names the code"
assert_not_contains "$_o" "SOURCE_FORMAT" "CANDIDATES_HEADER_INVALID (prose preamble): dies HERE, not at a downstream lint code"
[ ! -f "$_d/out/E.md" ]; assert_eq 0 $? "CANDIDATES_HEADER_INVALID (prose preamble): nothing created"

_d="$_jt/header-decoy-commit"; mkdir -p "$_d"
cat > "$_d/CANDIDATES.md" << DECOYEOF
Note: per my analysis the audited repo is pinned like this:
extraction_commit: 1111111111111111111111111111111111111111

extraction_commit: $commit

## JOURNEY-CANDIDATE — "Invoice resubmission after a schema-error rejection"
origin:          EXTRACTED
persona:         ops user
goal:            resubmit a corrected invoice
priority:        P2
covers:          FEAT-014
flows:           []
oracle_surface:  UI+API
negative_states: schema_error
grade:           [C]
steps:
  1. land on /invoices
oracle:          row status=ACCEPTED
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

\`\`\`json field_sources
{}
\`\`\`

## EXTRACTION-SOURCES
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)"
DECOYEOF
_o="$(/bin/sh "$GATE" "$_d/CANDIDATES.md" "$gold_mf" "$repo" "$_d/out/E.md" 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "CANDIDATES_HEADER_INVALID (decoy commit ahead of the real one): exit non-zero"
assert_contains "$_o" "CANDIDATES_HEADER_INVALID" "CANDIDATES_HEADER_INVALID (decoy commit): names the code — the decoy never silently wins the parse"
assert_not_contains "$_o" "EXTRACTION_COMMIT_INVALID" "CANDIDATES_HEADER_INVALID (decoy commit): dies at the structural check, not the value-format check"
[ ! -f "$_d/out/E.md" ]; assert_eq 0 $? "CANDIDATES_HEADER_INVALID (decoy commit): nothing created"

# Positive: a leading BLANK line before the real header is still legal —
# only the FIRST NON-BLANK line is load-bearing.
_d="$_jt/header-leading-blank"; mkdir -p "$_d"
{ printf '\n'; cat "$gold_cand"; } > "$_d/CANDIDATES.md"
_o="$(/bin/sh "$GATE" "$_d/CANDIDATES.md" "$gold_mf" "$repo" "$_d/out/E.md" 2>&1)"; _ec=$?
assert_eq "0" "$_ec" "CANDIDATES_HEADER_INVALID: a leading blank line before the real header is still legal"
[ -f "$_d/out/E.md" ]; assert_eq 0 $? "CANDIDATES_HEADER_INVALID: leading-blank-line case still stages"

# ═══════════════════════════════════════════════════════════════════════
# CANDIDATE_WORKFLOW_FIELD — one per forbidden field (spec: the model
# never sets workflow state)
# ═══════════════════════════════════════════════════════════════════════

_jes_workflow_case() { # $1=field $2=insertion-line
  _d="$_jt/wf-$1"; mkdir -p "$_d"
  awk -v ins="$2" '{print} /^## JOURNEY-CANDIDATE — "Invoice/{print ins}' "$gold_cand" > "$_d/CANDIDATES.md"
  _o="$(/bin/sh "$GATE" "$_d/CANDIDATES.md" "$gold_mf" "$repo" "$_d/out/E.md" 2>&1)"; _ec=$?
  _jes_nonzero "$_ec" "CANDIDATE_WORKFLOW_FIELD ($1): exit non-zero"
  assert_contains "$_o" "CANDIDATE_WORKFLOW_FIELD" "CANDIDATE_WORKFLOW_FIELD ($1): names the code"
  assert_contains "$_o" "$1" "CANDIDATE_WORKFLOW_FIELD ($1): names the specific field"
  [ ! -f "$_d/out/E.md" ]; assert_eq 0 $? "CANDIDATE_WORKFLOW_FIELD ($1): nothing created"
}
_jes_workflow_case needs_human_confirm "needs_human_confirm: true"
_jes_workflow_case confirmation_status "confirmation_status: CONFIRMED"
_jes_workflow_case promoted_as "promoted_as: JOURNEY-501"
_jes_workflow_case resolution "resolution: the model resolved its own disagreement"
_jes_workflow_case resolved_from "resolved_from: [X]"

# a workflow field smuggled INSIDE the EXTRACTION-SOURCES span (after the
# citation lines) is caught identically — "anywhere" in the slice, spec text
_d="$_jt/wf-in-sources"; mkdir -p "$_d"
sed '/^prior_e2e:/a\
resolution: smuggled after the sources block
' "$gold_cand" > "$_d/CANDIDATES.md"
_o="$(/bin/sh "$GATE" "$_d/CANDIDATES.md" "$gold_mf" "$repo" "$_d/out/E.md" 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "CANDIDATE_WORKFLOW_FIELD (in EXTRACTION-SOURCES span): exit non-zero"
assert_contains "$_o" "CANDIDATE_WORKFLOW_FIELD" "CANDIDATE_WORKFLOW_FIELD (in EXTRACTION-SOURCES span): still caught"

# ═══════════════════════════════════════════════════════════════════════
# checker-rejection pass-through — a candidate missing its field_sources
# fence fails journey-gen-check-candidate.sh's own MISSING_FIELD_SOURCES
# ═══════════════════════════════════════════════════════════════════════

_d="$_jt/checker-reject"; mkdir -p "$_d"
awk '/^```json field_sources$/{c++; if (c==1) {skip=1; next}} /^```$/ && skip {skip=0; next} skip{next} {print}' "$gold_cand" > "$_d/CANDIDATES.md"
_o="$(/bin/sh "$GATE" "$_d/CANDIDATES.md" "$gold_mf" "$repo" "$_d/out/E.md" 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "checker-rejection pass-through: exit non-zero"
assert_contains "$_o" "MISSING_FIELD_SOURCES" "checker-rejection pass-through: names the underlying checker code"
assert_contains "$_o" "format check" "checker-rejection pass-through: attributed to the format check"
[ ! -f "$_d/out/E.md" ]; assert_eq 0 $? "checker-rejection pass-through: nothing created"

# ═══════════════════════════════════════════════════════════════════════
# provenance-failure pass-through (bad cite), OUT byte-unchanged (seeded
# via a prior successful stage, then a re-stage attempt with a broken new
# candidate — proves the promise even in restage mode, not just fresh)
# ═══════════════════════════════════════════════════════════════════════

prov_out="$_jt/prov/JOURNEY_EXTRACTED.md"
/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$prov_out" >/dev/null 2>&1
_sha_before="$(_sha_jes "$prov_out")"

# a GENUINELY NEW third candidate (distinct covers, so it is not
# idempotent-skipped against the two already-preserved entries) whose
# citation quote does not exist at the pinned commit.
_d="$_jt/prov-bad"; mkdir -p "$_d"
cat > "$_d/CANDIDATES.md" << PROVEOF
extraction_commit: $commit

## JOURNEY-CANDIDATE — "Third candidate with a broken citation"
origin:          EXTRACTED
persona:         ops user
goal:            a goal distinct from the first two candidates
priority:        P2
covers:          FEAT-014
flows:           []
oracle_surface:  UI
negative_states: none
grade:           [C]
steps:
  1. do something else entirely
oracle:          a completely different oracle text
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

\`\`\`json field_sources
{}
\`\`\`

## EXTRACTION-SOURCES
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandlerNEVER)"
PROVEOF
_o="$(/bin/sh "$GATE" "$_d/CANDIDATES.md" "$gold_mf" "$repo" "$prov_out" 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "provenance-failure pass-through: exit non-zero"
assert_contains "$_o" "QUOTE_UNVERIFIED" "provenance-failure pass-through: names the underlying provenance code"
_sha_after="$(_sha_jes "$prov_out")"
assert_eq "$_sha_before" "$_sha_after" "provenance-failure pass-through: pre-existing OUT_EXTRACTED byte-unchanged (sha256)"

# ═══════════════════════════════════════════════════════════════════════
# coverage-failure pass-through (unknown covers anchor), OUT byte-unchanged
# ═══════════════════════════════════════════════════════════════════════

cov_out="$_jt/cov/JOURNEY_EXTRACTED.md"
/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$cov_out" >/dev/null 2>&1
_sha_before="$(_sha_jes "$cov_out")"

_d="$_jt/cov-bad"; mkdir -p "$_d"
sed 's/covers:          FEAT-014/covers:          FEAT-999/' "$gold_cand" > "$_d/CANDIDATES.md"
_o="$(/bin/sh "$GATE" "$_d/CANDIDATES.md" "$gold_mf" "$repo" "$cov_out" 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "coverage-failure pass-through: exit non-zero"
assert_contains "$_o" "UNKNOWN_ANCHOR" "coverage-failure pass-through: names the underlying coverage code"
_sha_after="$(_sha_jes "$cov_out")"
assert_eq "$_sha_before" "$_sha_after" "coverage-failure pass-through: pre-existing OUT_EXTRACTED byte-unchanged (sha256)"

# ═══════════════════════════════════════════════════════════════════════
# STAGED_DUP_KEY — two NEW candidates in the same run share a normalized
# covers+oracle key
# ═══════════════════════════════════════════════════════════════════════

_d="$_jt/dupkey"; mkdir -p "$_d"
cat > "$_d/CANDIDATES.md" << DUPEOF
extraction_commit: $commit

## JOURNEY-CANDIDATE — "Dup A"
origin:          EXTRACTED
persona:         ops user
goal:            resubmit a corrected invoice
priority:        P2
covers:          FEAT-014
flows:           []
oracle_surface:  UI+API
negative_states: schema_error
grade:           [C]
steps:
  1. land on /invoices
oracle:          row status=ACCEPTED
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

\`\`\`json field_sources
{}
\`\`\`

## EXTRACTION-SOURCES
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)"

## JOURNEY-CANDIDATE — "Dup B (same covers+oracle as Dup A)"
origin:          EXTRACTED
persona:         ops user
goal:            resubmit a corrected invoice via a different path
priority:        P2
covers:          FEAT-014
flows:           []
oracle_surface:  UI+API
negative_states: schema_error
grade:           [C]
steps:
  1. land on /invoices
oracle:          row status=ACCEPTED
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

\`\`\`json field_sources
{}
\`\`\`

## EXTRACTION-SOURCES
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)"
DUPEOF
_o="$(/bin/sh "$GATE" "$_d/CANDIDATES.md" "$gold_mf" "$repo" "$_d/out/E.md" 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "STAGED_DUP_KEY: exit non-zero"
assert_contains "$_o" "STAGED_DUP_KEY" "STAGED_DUP_KEY: names the code"
[ ! -f "$_d/out/E.md" ]; assert_eq 0 $? "STAGED_DUP_KEY: nothing created"

# ═══════════════════════════════════════════════════════════════════════
# Re-stage: golden append — old entries survive byte-for-byte, new
# candidate gains the next id
# ═══════════════════════════════════════════════════════════════════════

restage_out="$_jt/restage/JOURNEY_EXTRACTED.md"
/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$restage_out" >/dev/null 2>&1
_before_e1="$(_block_jes EXTRACTED-1 "$restage_out")"
_before_e2="$(_block_jes EXTRACTED-2 "$restage_out")"

_d="$_jt/restage-append"; mkdir -p "$_d"
cat > "$_d/CANDIDATES.md" << APPEOF
extraction_commit: $commit

## JOURNEY-CANDIDATE — "A brand new third candidate"
origin:          EXTRACTED
persona:         shopper
goal:            complete checkout
priority:        P2
covers:          FEAT-014
flows:           []
oracle_surface:  UI+API
negative_states: payment_declined
grade:           [C]
steps:
  1. land on /checkout
oracle:          order status=CONFIRMED
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

\`\`\`json field_sources
{}
\`\`\`

## EXTRACTION-SOURCES
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)"
APPEOF
_o="$(/bin/sh "$GATE" "$_d/CANDIDATES.md" "$gold_mf" "$repo" "$restage_out" 2>&1)"; _ec=$?
assert_eq "0" "$_ec" "re-stage append: exit 0"
assert_contains "$_o" "1 new entry staged" "re-stage append: summary names one new entry"
_g="$(cat "$restage_out")"
assert_contains "$_g" '## EXTRACTED-3 — "A brand new third candidate"' "re-stage append: new candidate gains next-free id EXTRACTED-3"
_after_e1="$(_block_jes EXTRACTED-1 "$restage_out")"
_after_e2="$(_block_jes EXTRACTED-2 "$restage_out")"
assert_eq "$_before_e1" "$_after_e1" "re-stage append: EXTRACTED-1 byte-identical (per-entry compare)"
assert_eq "$_before_e2" "$_after_e2" "re-stage append: EXTRACTED-2 byte-identical (per-entry compare)"

assert_exit 0 /bin/sh "$BIN/lint-journey-extracted.sh" "$restage_out"
assert_exit 0 /bin/sh "$BIN/check-extracted-provenance.sh" "$restage_out" "$repo"
assert_exit 0 /bin/sh "$BIN/check-extraction-coverage.sh" "$gold_mf" "$restage_out"

# ═══════════════════════════════════════════════════════════════════════
# Idempotent skip — re-presenting the SAME candidate on a later pass
# ═══════════════════════════════════════════════════════════════════════

_o="$(/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$restage_out" 2>&1)"; _ec=$?
assert_eq "0" "$_ec" "idempotent re-run: exit 0"
assert_contains "$_o" "SKIPPED:" "idempotent re-run: SKIPPED line printed"
assert_contains "$_o" "already staged as EXTRACTED-1" "idempotent re-run: names the matching preserved id"
assert_contains "$_o" "already staged as EXTRACTED-2" "idempotent re-run: names the second matching preserved id"
assert_contains "$_o" "0 new entries staged" "idempotent re-run: zero new entries (both candidates already present)"
_g2="$(cat "$restage_out")"
_n_e1=$(printf '%s\n' "$_g2" | grep -c '^## EXTRACTED-1 —')
assert_eq "1" "$_n_e1" "idempotent re-run: no duplicate EXTRACTED-1 block created"

# ═══════════════════════════════════════════════════════════════════════
# REJECTED_KEY_COLLISION (V-E4 F1) — a new candidate whose normalized key
# matches a REJECTED preserved entry must surface LOUD, never be silently
# SKIPPED as "idempotent": spec §6's owner-approved text says a wrongly
# rejected entry is recovered by re-staging its still-present candidate,
# and the key-match against the REJECTED sibling "surfaces, forcing the
# human to delete the REJECTED entry first: deliberate friction". A silent
# skip (the pre-fix behavior, reproduced RED: SKIPPED + exit 0) blocks
# that documented recovery path with a mislabeled message.
# ═══════════════════════════════════════════════════════════════════════

rej_out="$_jt/rejected-collision/JOURNEY_EXTRACTED.md"; mkdir -p "$_jt/rejected-collision"
cat > "$rej_out" << REJEOF
# JOURNEY-EXTRACTED
extraction_commit: $commit
manifest_sha256:   $gold_mf_sha

## EXTRACTED-1 — "Invoice resubmission after a schema-error rejection"
needs_human_confirm: true
confirmation_status: REJECTED
rejected_reason:     rejected in error — the route is real; a human will want this candidate back
grade:               [C]
origin:              EXTRACTED
persona:             ops user (inferred from the route's auth middleware)
goal:                resubmit a corrected invoice after a schema-error rejection
priority:            P2
covers:              FEAT-014
flows:               []
oracle_surface:      UI+API
negative_states:     schema_error
steps:
  1. land on /invoices
  2. upload malformed.csv -> inject schema_error
  3. re-upload corrected.csv
  4. observe the row transition to ACCEPTED
oracle:              row status=ACCEPTED AND GET /invoices returns the row
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)"
REJEOF
assert_exit 0 /bin/sh "$BIN/lint-journey-extracted.sh" "$rej_out"
_rej_sha_before="$(_sha_jes "$rej_out")"

# gold_cand's candidate 1 carries the IDENTICAL normalized covers+oracle
# key as the REJECTED EXTRACTED-1 above (the recovery re-presentation).
_o="$(/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$rej_out" 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "REJECTED_KEY_COLLISION: exit non-zero (never a silent idempotent skip against a REJECTED sibling)"
assert_contains "$_o" "REJECTED_KEY_COLLISION" "REJECTED_KEY_COLLISION: names the code"
assert_contains "$_o" "EXTRACTED-1" "REJECTED_KEY_COLLISION: names the REJECTED sibling entry"
assert_contains "$_o" "delete the REJECTED entry first" "REJECTED_KEY_COLLISION: states the delete-first recovery path (deliberate friction, spec §6)"
assert_not_contains "$_o" "SKIPPED:" "REJECTED_KEY_COLLISION: no mislabeled idempotent-skip line for a REJECTED-sibling match"
_rej_sha_after="$(_sha_jes "$rej_out")"
assert_eq "$_rej_sha_before" "$_rej_sha_after" "REJECTED_KEY_COLLISION: pre-existing OUT_EXTRACTED byte-unchanged"

# the documented recovery path itself: the human deletes the REJECTED
# entry by hand (here it is the file's ONLY entry, and a zero-entry
# staging file is itself lint-rejected — NO_EXTRACTED_ENTRIES — so the
# hand-delete is the whole file), then re-stages the same candidates ->
# the candidate returns as a NEW entry.
rm -f "$rej_out"
_o="$(/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$rej_out" 2>&1)"; _ec=$?
assert_eq "0" "$_ec" "REJECTED_KEY_COLLISION recovery: after deleting the REJECTED entry, re-staging succeeds"
assert_contains "$(cat "$rej_out")" '## EXTRACTED-1 — "Invoice resubmission after a schema-error rejection"' \
  "REJECTED_KEY_COLLISION recovery: the wrongly-rejected candidate returns as a NEW entry"

# a CONFIRMED (non-REJECTED) sibling match stays the idempotent SKIPPED
# path — the fix is scoped to REJECTED only (spec §6.1's skip is correct
# for every other status; anti-overreach guard on this fix).
conf_out="$_jt/confirmed-skip/JOURNEY_EXTRACTED.md"; mkdir -p "$_jt/confirmed-skip"
sed 's/^confirmation_status: PENDING$/confirmation_status: CONFIRMED/' "$_jt/fresh/JOURNEY_EXTRACTED.md" > "$conf_out"
assert_exit 0 /bin/sh "$BIN/lint-journey-extracted.sh" "$conf_out"
_o="$(/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$conf_out" 2>&1)"; _ec=$?
assert_eq "0" "$_ec" "REJECTED-scope guard: a CONFIRMED-sibling key match still skips idempotently (exit 0)"
assert_contains "$_o" "SKIPPED:" "REJECTED-scope guard: CONFIRMED-sibling match prints the SKIPPED line"
assert_not_contains "$_o" "REJECTED_KEY_COLLISION" "REJECTED-scope guard: no false collision against a CONFIRMED sibling"

# ═══════════════════════════════════════════════════════════════════════
# HUMAN-EDIT SURVIVAL — a hand-edited [X]->[C]+CONFIRMED resolution
# entry, byte-for-byte, through a re-stage that adds one new candidate
# ═══════════════════════════════════════════════════════════════════════

he_out="$_jt/human-edit/JOURNEY_EXTRACTED.md"; mkdir -p "$_jt/human-edit"
cat > "$he_out" << HEEOF
# JOURNEY-EXTRACTED
extraction_commit: $commit
manifest_sha256:   $gold_mf_sha

## EXTRACTED-1 — "Invoice resubmission — resolved doc/code conflict"
needs_human_confirm: true
confirmation_status: CONFIRMED
grade:               [C]
origin:              EXTRACTED
persona:             ops user
goal:                resubmit a corrected invoice and see it accepted
priority:            P1
covers:              FEAT-014
flows:               []
oracle_surface:      UI+API
negative_states:     schema_error
steps:
  1. land on /invoices
  2. resubmit
oracle:              row status=ACCEPTED AND GET /invoices returns the row
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)"
  - docs/FLW.md#Invoice resubmission
prior_e2e:           tests/e2e/invoice-resubmit.spec.ts
resolution:          docs/FLW.md#Invoice resubmission and the code cited above were reconciled by a human; code wins.
resolved_from:       [X]
HEEOF
_before_edit_block="$(_block_jes EXTRACTED-1 "$he_out")"

assert_exit 0 /bin/sh "$BIN/lint-journey-extracted.sh" "$he_out"

_d="$_jt/human-edit-restage"; mkdir -p "$_d"
cat > "$_d/CANDIDATES.md" << APP2EOF
extraction_commit: $commit

## JOURNEY-CANDIDATE — "Login screen reachable directly"
origin:          EXTRACTED
persona:         any user
goal:            reach the login screen
priority:        P2
covers:          SCR-login
flows:           []
oracle_surface:  UI
negative_states: bad_credentials
grade:           [C]
steps:
  1. land on /login
oracle:          a session cookie is set
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

\`\`\`json field_sources
{}
\`\`\`

## EXTRACTION-SOURCES
  - src/routes/auth.ts:12 — "router.get('/login', renderLogin)"
APP2EOF
_o="$(/bin/sh "$GATE" "$_d/CANDIDATES.md" "$gold_mf" "$repo" "$he_out" 2>&1)"; _ec=$?
assert_eq "0" "$_ec" "human-edit survival: re-stage with a new candidate succeeds"
_after_edit_block="$(_block_jes EXTRACTED-1 "$he_out")"
assert_eq "$_before_edit_block" "$_after_edit_block" "human-edit survival: CONFIRMED + resolution + resolved_from + oracle all survive byte-for-byte"
assert_eq "CONFIRMED" "$(_field_jes EXTRACTED-1 "$he_out" confirmation_status)" "human-edit survival: confirmation_status still CONFIRMED after re-stage"
assert_contains "$(cat "$he_out")" '## EXTRACTED-2 — "Login screen reachable directly"' "human-edit survival: new candidate appended as EXTRACTED-2"

# ═══════════════════════════════════════════════════════════════════════
# ORPHANED_AFTER_RESTAGE — MANIFEST drops an anchor a preserved entry
# depends on; incl. a promoted_as-stamped terminal entry variant (Q7)
# ═══════════════════════════════════════════════════════════════════════

orph_out="$_jt/orphan/JOURNEY_EXTRACTED.md"
/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$orph_out" >/dev/null 2>&1
_orph_sha_before="$(_sha_jes "$orph_out")"

drift_mf="$_jt/manifest-drift.md"
sed 's/^feat: FEAT-014.*/feat: FEAT-999 | behaviors=1 | states_filled=1 | grade_counts=C:1,I:0,G:0,X:0/' "$gold_mf" > "$drift_mf"

# empty candidates file variant is not legal (must have >=1 block or a
# degenerate token) — re-present the SAME two candidates (idempotent
# skip) against the DRIFTED manifest, so the failure is purely about
# preserved-entry re-verification, not new content.
_o="$(/bin/sh "$GATE" "$gold_cand" "$drift_mf" "$repo" "$orph_out" 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "ORPHANED_AFTER_RESTAGE: exit non-zero"
assert_contains "$_o" "UNKNOWN_ANCHOR: EXTRACTED-1: FEAT-014" "ORPHANED_AFTER_RESTAGE: underlying coverage diagnostic passed through"
assert_contains "$_o" "ORPHANED_AFTER_RESTAGE: EXTRACTED-1" "ORPHANED_AFTER_RESTAGE: names the orphaned preserved id"
_orph_sha_after="$(_sha_jes "$orph_out")"
assert_eq "$_orph_sha_before" "$_orph_sha_after" "ORPHANED_AFTER_RESTAGE: pre-existing OUT_EXTRACTED byte-unchanged"

# ── Q7 variant: a promoted_as-stamped TERMINAL entry is still re-verified
# and still orphans loud (never a silent skip) ──────────────────────────
term_out="$_jt/terminal/JOURNEY_EXTRACTED.md"; mkdir -p "$_jt/terminal"
cat > "$term_out" << TERMEOF
# JOURNEY-EXTRACTED
extraction_commit: $commit
manifest_sha256:   $gold_mf_sha

## EXTRACTED-1 — "Invoice resubmission after a schema-error rejection"
needs_human_confirm: true
confirmation_status: CONFIRMED
grade:               [C]
origin:              EXTRACTED
persona:             ops user
goal:                resubmit a corrected invoice after a schema-error rejection
priority:            P2
covers:              FEAT-014
flows:               []
oracle_surface:      UI+API
negative_states:     schema_error
steps:
  1. land on /invoices
oracle:              row status=ACCEPTED
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)"
promoted_as:         JOURNEY-501
TERMEOF
assert_exit 0 /bin/sh "$BIN/lint-journey-extracted.sh" "$term_out"
_term_sha_before="$(_sha_jes "$term_out")"
# A real (idempotent) re-presentation of the golden candidates against the
# DRIFTED manifest — NOT a NO-JOURNEYS-FOUND file, whose degenerate-token
# short-circuit fires before MANIFEST is ever consulted (spec-documented
# limitation, journey-extracted-format.md §10.4) and would exit 0 without
# ever re-verifying EXTRACTED-1 at all.
_o="$(/bin/sh "$GATE" "$gold_cand" "$drift_mf" "$repo" "$term_out" 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "ORPHANED_AFTER_RESTAGE (terminal, promoted_as-stamped): exit non-zero"
assert_contains "$_o" "ORPHANED_AFTER_RESTAGE: EXTRACTED-1" "ORPHANED_AFTER_RESTAGE: a promoted_as-stamped terminal entry still orphans loud (Q7 — never a silent skip)"
_term_sha_after="$(_sha_jes "$term_out")"
assert_eq "$_term_sha_before" "$_term_sha_after" "ORPHANED_AFTER_RESTAGE (terminal): pre-existing OUT_EXTRACTED byte-unchanged"

# ═══════════════════════════════════════════════════════════════════════
# REGENERATE_REFUSED / --regenerate succeeds on all-PENDING
# ═══════════════════════════════════════════════════════════════════════

regen_out="$_jt/regen/JOURNEY_EXTRACTED.md"
/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$regen_out" >/dev/null 2>&1
sed 's/confirmation_status: PENDING/confirmation_status: CONFIRMED/' "$regen_out" > "$regen_out.new"
mv "$regen_out.new" "$regen_out"
_regen_sha_before="$(_sha_jes "$regen_out")"
_o="$(/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$regen_out" --regenerate 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "REGENERATE_REFUSED: exit non-zero (a CONFIRMED entry is present)"
assert_contains "$_o" "REGENERATE_REFUSED" "REGENERATE_REFUSED: names the code"
_regen_sha_after="$(_sha_jes "$regen_out")"
assert_eq "$_regen_sha_before" "$_regen_sha_after" "REGENERATE_REFUSED: OUT_EXTRACTED byte-unchanged"

# all-PENDING file: --regenerate succeeds, rebuilding from candidates alone
allpending_out="$_jt/allpending/JOURNEY_EXTRACTED.md"
/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$allpending_out" >/dev/null 2>&1
_o="$(/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$allpending_out" --regenerate 2>&1)"; _ec=$?
assert_eq "0" "$_ec" "regenerate-succeeds: all-PENDING file, --regenerate rebuilds cleanly"
_g="$(cat "$allpending_out")"
assert_contains "$_g" '## EXTRACTED-1 —' "regenerate-succeeds: ids restart from 1"
_n_blocks=$(printf '%s\n' "$_g" | grep -c '^## EXTRACTED-')
assert_eq "2" "$_n_blocks" "regenerate-succeeds: exactly 2 entries (rebuilt from candidates, not doubled)"

# --regenerate on a file that does not exist yet is an inert no-op
noexist_out="$_jt/noexist-regen/JOURNEY_EXTRACTED.md"
_o="$(/bin/sh "$GATE" "$gold_cand" "$gold_mf" "$repo" "$noexist_out" --regenerate 2>&1)"; _ec=$?
assert_eq "0" "$_ec" "regenerate: no-op on a missing OUT_EXTRACTED (identical to fresh stage)"
[ -f "$noexist_out" ]; assert_eq 0 $? "regenerate: no-op still stages fresh (file created)"

# ═══════════════════════════════════════════════════════════════════════
# Existing DERIVED/PERSONA/SIMULATOR checker tests byte-unchanged — run
# them directly here as a belt-and-suspenders local re-check (the
# suite-wide proof is run.sh executing journey-gen-candidate_test.sh /
# persona-origin_test.sh / simulator-run_test.sh alongside this file).
# ═══════════════════════════════════════════════════════════════════════

CC="$BIN/journey-gen-check-candidate.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
assert_exit 0 /bin/sh "$CC" "$GENDIR/golden/expected-candidate-feat-001.md"
assert_exit 0 /bin/sh "$CC" "$GENDIR/golden/expected-candidate-feat-001.md" --origin DERIVED
_pcand="$_jt/persona-check.candidate"
sed 's/^origin:          DERIVED$/origin:          PERSONA/' "$GENDIR/golden/expected-candidate-feat-001.md" > "$_pcand"
assert_exit 0 /bin/sh "$CC" "$_pcand" --origin PERSONA
_o="$(/bin/sh "$CC" "$_pcand" --origin SIMULATOR 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "restrict-never-broaden: PERSONA candidate still rejected under --origin SIMULATOR"
_o="$(/bin/sh "$CC" "$_pcand" --origin EXTRACTED 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "restrict-never-broaden: PERSONA candidate still rejected under --origin EXTRACTED"
_o="$(/bin/sh "$CC" "$_pcand" --origin BOGUS 2>&1)"; _ec=$?
_jes_nonzero "$_ec" "usage: unknown --origin value still rejected"
assert_contains "$_o" "EXTRACTED" "usage: unknown --origin error message lists EXTRACTED among the legal values"

rm -rf "$_jt"
