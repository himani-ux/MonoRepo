#!/bin/sh
# step0-stage4b-coherence_test.sh — byte-locks the Step 0.txt Stage 4b
# amendment (task E6, spec docs/superpowers/specs/2026-07-11-extracted-
# baseline-design.md §4.1 "Step 0.txt amendment" + §14 "§2 tightening").
# Model: journey/tests/step3-wiring-coherence_test.sh /
# journey/tests/step5-wiring-coherence_test.sh (assert_contains
# substring-anchor style — this amendment has no MARKER BEGIN/END pair of
# its own beyond the worked example's own WORKED-EXAMPLE-BEGIN/END
# sentinels, added by this same amendment for exactly this extraction).
#
# Locks five things:
#   (a) the EXTRACTION-MANIFEST machine-block grammar lands in the Stage 4
#       MANIFEST.md bullet verbatim (BEGIN/END fences, manifest_version,
#       extraction_commit 40-hex, feat:/screen:/e2e_test: line shapes, the
#       value charset, the NOT-MACHINE-LISTABLE substitution rule)
#   (b) the new Stage 4b section lands verbatim: the §14 input-lock law
#       ("no ambient repository discovery"), the output grammar, the
#       trust-limits law text (byte-exact, B2/B3/B4), the [C-absent]
#       negative_states rule, oracle honesty, the two degenerate tokens
#       with their semantics, the [C]/[I]/[G]/[X] grading + [X] two-source
#       rule, and the prior_e2e-last-line rule
#   (c) the Stage 5 checklist gains its one new line; the goal sentence
#       gains its 4b clause
#   (d) no phantom gates: every journey/bin path the new text names exists
#   (e) the <mission> output tree (the "only thing you may write" list)
#       gains its Stage 4b line, `journey-candidates.md ← Stage 4b`,
#       positioned after the Stage 4 artifacts — keeping the tree
#       internally consistent with Stage 4b's own existence
#
# Then (f) REAL execution: the worked example is extracted byte-for-byte
# from between the WORKED-EXAMPLE-BEGIN/END sentinels and run through
# journey/bin/journey-gen-check-candidate.sh --origin EXTRACTED AND
# journey/bin/journey-extracted-stage.sh's candidate reader (golden-example
# law) against a scratch git repo whose committed files back every citation
# in the worked example, byte for byte — mirrors journey/tests/
# journey-extracted-stage_test.sh's own fixture idiom (mktemp git repo,
# sed-stamped commit, matching MANIFEST.md).
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$TESTS_DIR/../.."
BIN="$TESTS_DIR/../bin"
S0="$ROOT/Step 0.txt"

if [ ! -f "$S0" ]; then
  printf 'FAIL: Step 0.txt not found at repo root\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
else
  _s0="$(cat "$S0")"

  # ── (a) Stage 4 MANIFEST.md bullet — EXTRACTION-MANIFEST machine block ──
  assert_contains "$_s0" "EXTRACTION-MANIFEST machine block that Stage 4b and the journey layer's gates parse directly" \
    "MANIFEST bullet: machine-block introduced, prose stays for humans"
  assert_contains "$_s0" "EXTRACTION-MANIFEST BEGIN" \
    "machine block: BEGIN fence"
  assert_contains "$_s0" "manifest_version: 1" \
    "machine block: manifest_version line"
  assert_contains "$_s0" "extraction_commit: <full 40-hex sha of the audited repo>" \
    "machine block: extraction_commit 40-hex placeholder line"
  assert_contains "$_s0" "feat: FEAT-001 | behaviors=3 | states_filled=8 | grade_counts=C:5,I:1,G:2,X:0" \
    "machine block: feat: line shape"
  assert_contains "$_s0" "screen: SCR-login | route=/login | flows=AFJ-...   (one line per screen from FLW)" \
    "machine block: screen: line shape"
  assert_contains "$_s0" "e2e_test: tests/e2e/booking.spec.ts | framework=playwright" \
    "machine block: e2e_test: line shape"
  assert_contains "$_s0" "EXTRACTION-MANIFEST END" \
    "machine block: END fence"
  assert_contains "$_s0" '^[A-Za-z0-9._/:=,-]+$' \
    "machine block: value charset regex stated verbatim"
  assert_contains "$_s0" "no whitespace, no \`|\`, no quoting/escaping mechanism exists" \
    "machine block: charset consequence stated"
  assert_contains "$_s0" "NOT-MACHINE-LISTABLE" \
    "machine block: NOT-MACHINE-LISTABLE substitution token named"
  assert_contains "$_s0" "is NEVER silently dropped: list it with its cite in the prose MANIFEST and mark it" \
    "machine block: nonconforming values surface in prose, never silently dropped"
  assert_contains "$_s0" "rejected by the consumer as \`MANIFEST_FORMAT\`" \
    "machine block: nonconforming line rejected as MANIFEST_FORMAT"
  assert_contains "$_s0" "Duplicate ids within the block are a consumer-side failure" \
    "machine block: duplicate ids are a consumer-side failure"

  # ── (b) Stage 4b heading + purpose + inputs (§14 input-lock law) ────────
  assert_contains "$_s0" "## Stage 4b: JOURNEY BASELINE — seed journey intent from AS-IS evidence" \
    "Stage 4b: heading lands"
  assert_contains "$_s0" "routes prove screens, tests prove intended multi-step behavior, state matrices prove non-happy handling or its confirmed absence" \
    "Stage 4b: purpose names routes/tests/state-matrices as AS-IS evidence"
  assert_contains "$_s0" "Stage 4b consumes ONLY MANIFEST-declared, commit-pinned inputs — no ambient repository discovery, no undeclared source expansion" \
    "Stage 4b: §14 input-lock law, verbatim"
  assert_contains "$_s0" "\`claims/FLW.verified.md\`, \`claims/PRD.verified.md\`, \`doc-audit.md\`, and the E2E test files named in MANIFEST.md's machine block \`e2e_test:\` lines — nothing else" \
    "Stage 4b: the exact locked input set, nothing else"
  assert_contains "$_s0" "an \`UNKNOWN_ANCHOR\`-class failure (journey/bin/check-extraction-coverage.sh)" \
    "Stage 4b: out-of-contract anchors fail downstream as UNKNOWN_ANCHOR"

  # ── (b) output grammar ───────────────────────────────────────────────────
  assert_contains "$_s0" "Stage 4b WRITES \`step0-out/journey-candidates.md\`" \
    "Stage 4b: output path named, WRITE mode stated (DX-3)"
  assert_contains "$_s0" "consistent with the mission block's \"All output goes to a \`step0-out/\` directory\" law above" \
    "Stage 4b: output-mode law cross-references the mission block (DX-3)"
  assert_contains "$_s0" "the printed stream must BE the file's content, verbatim: first non-blank line the header, nothing before it, no prose framing the content" \
    "Stage 4b: print-fallback law — printed stream IS the file, header first (DX-3)"
  assert_contains "$_s0" 'a shared header `extraction_commit: <full 40-hex sha of the audited repo>`' \
    "Stage 4b: shared extraction_commit header stated"
  assert_contains "$_s0" '## JOURNEY-CANDIDATE — "<title>"' \
    "Stage 4b: frozen JOURNEY-CANDIDATE heading grammar"
  assert_contains "$_s0" "## EXTRACTION-SOURCES" \
    "Stage 4b: EXTRACTION-SOURCES block named"
  assert_contains "$_s0" "requires this fence UNCONDITIONALLY, exactly as it does for every other origin (restrict-never-broaden)" \
    "Stage 4b: field_sources fence requirement is unconditional (E4 binding disclosure)"
  assert_contains "$_s0" "an empty object \`{}\` satisfies it and is the expected shape here" \
    "Stage 4b: {} fence is the expected EXTRACTED shape"
  assert_contains "$_s0" 'a code-cite `  - <path>:<line> — "<verbatim quote>"` or a section-cite `  - <path>#<heading>`' \
    "Stage 4b: citation line grammars named"
  assert_contains "$_s0" 'a search-cite `  - search: grep -rFn -- "<literal>" <relpath>`' \
    "Stage 4b: search-cite (absence-evidence) grammar named (DX-1)"
  assert_contains "$_s0" "Absence evidence uses the deterministic search form, never freeform prose" \
    "Stage 4b: absence-evidence law sentence, verbatim (DX-1)"
  assert_contains "$_s0" "ANY hit means the absence claim was wrong, and the citation diverges, failing closed" \
    "Stage 4b: hits-mean-divergence note (DX-1)"
  assert_contains "$_s0" "A section-cite's heading is never followed by a quote — that shape is a hybrid line-cite/section-cite paste, rejected at staging" \
    "Stage 4b: hybrid section-cite guard named (DX-5)"
  assert_contains "$_s0" "Citation targets are COMMITTED repo files at the pinned \`extraction_commit\` only" \
    "Stage 4b: citation-target law, verbatim (DX-4)"
  assert_contains "$_s0" "\`step0-out/\` artifacts (\`MANIFEST.md\`, every \`claims/*.verified.md\`, \`doc-audit.md\`) are Stage 4b's OWN INPUTS, never legal citation targets" \
    "Stage 4b: step0-out/ artifacts named as inputs, never citation targets (DX-4)"
  assert_contains "$_s0" "When evidence lives only inside a step0-out/ artifact" \
    "Stage 4b: derive-from-underlying-file rule stated (DX-4)"
  assert_contains "$_s0" "cite the UNDERLYING repo file or doc THAT artifact itself cites — never the artifact" \
    "Stage 4b: cite-the-underlying-file law, verbatim (DX-4)"
  assert_contains "$_s0" "it MUST ride as the LAST line of the \`## EXTRACTION-SOURCES\` block — after every citation line, never before, never inside the JOURNEY-CANDIDATE field block itself" \
    "Stage 4b: prior_e2e LAST-line rule, verbatim (E4 binding disclosure)"
  assert_contains "$_s0" "it never reaches the map's \`evidence:\`, which stays \`[]\` — the blind author never reads it" \
    "Stage 4b: prior_e2e is staging-only, never laundered into evidence:"

  # ── (b) priority enum / flows example (DX-6) ─────────────────────────────
  assert_contains "$_s0" "\`priority:\` is one of the map's own enum \`P0 | P1 | P2 | P3\`" \
    "Stage 4b: priority enum stated, verbatim (DX-6)"
  assert_contains "$_s0" "default \`P2\` when the evidence gives no signal; priority is INTENT, not a fact code can prove, so a human adjusts it at confirmation" \
    "Stage 4b: priority default + human-adjusts-at-confirmation guidance (DX-6)"
  assert_contains "$_s0" "\`flows:\` is either the empty-list sentinel \`[]\` (no AFJ anchor discovered) or one or more bare, non-empty AFJ ids, e.g. \`flows: AFJ-booking-flow\`" \
    "Stage 4b: flows [] sentinel + bare non-empty example, verbatim (DX-6)"

  # ── (b) search-literal discipline (DX-7, D6 law ported from
  # journey/gen/prompts/uat-verifier.md — live run 2: 2/2 attempts died
  # SEARCH_DIVERGED on feature-noun literals ("waitlist", "notesStore"),
  # and a range-scoped FLW absence claim was transcribed into a
  # file-scoped search where its literal turns false) ───────────────────────
  assert_contains "$_s0" "MUST have been re-executed by the extractor, at the pinned commit, BEFORE emission" \
    "Stage 4b: search-literal discipline — re-execute before emit (DX-7)"
  assert_contains "$_s0" 'git grep -Fn -e "<literal>" <commit> -- "<relpath>"' \
    "Stage 4b: search-literal discipline — exact re-execution command form (DX-7)"
  assert_contains "$_s0" "and it must have returned ZERO matches" \
    "Stage 4b: search-literal discipline — zero-matches requirement (DX-7)"
  assert_contains "$_s0" "including the feature's own identifiers, comments, or docs that merely name the absent behavior" \
    "Stage 4b: search-literal discipline — any match means not citable, incl. feature identifiers (DX-7)"
  assert_contains "$_s0" "The feature's key noun is the WRONG literal by construction — the implementing file necessarily contains it" \
    "Stage 4b: search-literal discipline — feature-noun warning, verbatim (DX-7)"
  assert_contains "$_s0" "prefer implementation-shaped literals of the ABSENT behavior — function-call forms like \`promote(\`, \`notifyMember(\`" \
    "Stage 4b: search-literal discipline — implementation-shaped literal guidance (DX-7)"
  assert_contains "$_s0" "NEVER transcribe such a claim's literal into a file-scope search line; RE-ANCHOR the claim to a literal that is absent at the citable scope" \
    "Stage 4b: search-literal discipline — range-claim re-anchoring law, verbatim (DX-7)"
  assert_contains "$_s0" "never satisfy zero-hit by narrowing so far the search becomes vacuous" \
    "Stage 4b: search-literal discipline — vacuous-narrowing warning (DX-7, D6 mirror)"
  assert_contains "$_s0" 'grep -rFn -- "promoteFromWaitlist(" src' \
    "Stage 4b: search-literal discipline — worked micro-example re-anchored literal (DX-7)"
  assert_contains "$_s0" "true at its own range scope" \
    "Stage 4b: search-literal discipline — micro-example names the range-scope truth (DX-7)"

  # ── (b) trust limits — verbatim law text ─────────────────────────────────
  assert_contains "$_s0" "an extracted journey is a hypothesis about intent reverse-engineered from mechanism; it proves what the code does, never that it should, that it runs correctly, or that any user validated it; every candidate is born needs_human_confirm: true and no automated step may confirm it" \
    "Stage 4b: trust-limits law text, byte-exact (B2/B3/B4)"

  # ── (b) non-happy states / oracle honesty / degenerate tokens / grading ──
  assert_contains "$_s0" "Where handling is \`[C-absent]\`, the candidate's \`negative_states\` note the absence directly" \
    "Stage 4b: [C-absent] surfaces in negative_states"
  assert_contains "$_s0" "the candidate carries \`oracle_gap: <the question a human must answer>\` in place of a real \`oracle:\` line" \
    "Stage 4b: oracle_gap: honest-gap rule"
  assert_contains "$_s0" "Never guess an oracle to fill the field" \
    "Stage 4b: never guess an oracle"
  assert_contains "$_s0" "\`EXTRACTION-FAILED: <reason>\` line is a loud, attributable failure" \
    "Stage 4b: EXTRACTION-FAILED degenerate token semantics"
  assert_contains "$_s0" "\`NO-JOURNEYS-FOUND\` line is a legitimate, recorded outcome (e.g. a BACKEND_ONLY project with no user-facing flows) — never invented candidates to avoid it" \
    "Stage 4b: NO-JOURNEYS-FOUND degenerate token semantics"
  assert_contains "$_s0" "[C] direct code evidence at file:line, [I] a stated recurring pattern (sample" \
    "Stage 4b: grading reuses evidence_rules vocabulary"
  assert_contains "$_s0" "An [X] candidate MUST carry at least two \`## EXTRACTION-SOURCES\` lines, both sides of the disagreement — a one-sided [X] is malformed" \
    "Stage 4b: [X] two-source rule"

  # ── (c) Stage 5 checklist + goal sentence ────────────────────────────────
  assert_contains "$_s0" "step0-out/journey-candidates.md exists and every candidate carries extraction sources and a grade, or NO-JOURNEYS-FOUND is recorded" \
    "Stage 5 checklist: new line names the 4b closure condition"
  assert_contains "$_s0" "and step0-out/journey-candidates.md exists with every candidate carrying extraction sources and a grade, or NO-JOURNEYS-FOUND is recorded." \
    "goal sentence: extended with 4b outputs"

  # ── (b) worked-example sentinels present (extracted for real execution below) ──
  assert_contains "$_s0" "WORKED-EXAMPLE-BEGIN" "worked example: begin sentinel present"
  assert_contains "$_s0" "WORKED-EXAMPLE-END" "worked example: end sentinel present"
fi

# ── (d) no phantom gates: every journey/bin path the new text names ───────
for _p in \
  "journey/bin/journey-gen-check-candidate.sh" \
  "journey/bin/journey-extracted-stage.sh" \
  "journey/bin/check-extraction-coverage.sh" \
  "journey/bin/check-extracted-provenance.sh" \
  "journey/bin/lint-journey-extracted.sh" \
  "journey/docs/journey-extracted-format.md" \
; do
  assert_exit 0 test -f "$ROOT/$_p"
done

# ── (e) mission tree: journey-candidates.md ← Stage 4b ────────────────────
# The <mission> block's output tree (line ~25: "it is the only thing you
# may write") must list every step0-out/ artifact with its producing
# stage — including Stage 4b's journey-candidates.md, added after the
# Stage 4 artifacts, matching the tree's existing two-space-indent /
# arrow-column-31 alignment.
if [ -f "$S0" ]; then
  assert_contains "$_s0" "  journey-candidates.md       ← Stage 4b" \
    "mission tree: journey-candidates.md lands after the Stage 4 artifacts"
fi

# ═══════════════════════════════════════════════════════════════════════════
# (f) REAL execution — extract the worked example, byte for byte, and run it
# through the candidate checker AND the stage runner's candidate reader.
# ═══════════════════════════════════════════════════════════════════════════

if [ -f "$S0" ] && command -v git >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  _jt="$(mktemp -d "${TMPDIR:-/tmp}/s0-s4b-XXXXXXXX")"
  _s0_cleanup() { rm -rf "$_jt"; }
  trap '_s0_cleanup' EXIT INT TERM

  # Extract strictly BETWEEN the WORKED-EXAMPLE-BEGIN/END sentinel lines
  # (exclusive) — both are unique in Step 0.txt (verified: grep -c each == 1
  # by construction of the amendment).
  awk '
    /^WORKED-EXAMPLE-BEGIN$/ { grab=1; next }
    /^WORKED-EXAMPLE-END$/   { grab=0; next }
    grab { print }
  ' "$S0" > "$_jt/candidate-raw.md"

  assert_exit 0 test -s "$_jt/candidate-raw.md"

  # strip a single leading/trailing blank line the sentinel spacing leaves
  awk 'NF || seen { print; seen=1 }' "$_jt/candidate-raw.md" > "$_jt/candidate.md"

  # ── scratch git repo backing every citation in the worked example ───────
  _s0_mk_repo() { # $1=dir ; echoes HEAD sha
    ( cd "$1" && git init -q . && git config user.email s0@t.example && git config user.name S0Test
      git config commit.gpgsign false
      mkdir -p src/routes docs tests/e2e

      { i=1; while [ "$i" -le 41 ]; do printf '// pad%s\n' "$i"; i=$((i + 1)); done
        printf "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)\n"
      } > src/routes/invoices.ts

      printf '# Flows\n\n## Invoice resubmission\n\nInvoice resubmission notes.\n' > docs/FLW.md
      printf "test('invoice resubmit', () => {});\n" > tests/e2e/invoice-resubmit.spec.ts

      git add -A && git commit -qm fixture >/dev/null && git rev-parse HEAD )
  }
  repo="$_jt/repo"; mkdir -p "$repo"
  commit="$(_s0_mk_repo "$repo")"
  assert_eq "40" "$(printf '%s' "$commit" | wc -c | tr -d ' ')" \
    "worked-example harness: scratch repo HEAD is a 40-char sha"

  cand="$_jt/CANDIDATES.md"
  sed "s/^extraction_commit: .*/extraction_commit: $commit/" "$_jt/candidate.md" > "$cand"

  # ── (f-1) journey-gen-check-candidate.sh --origin EXTRACTED ─────────────
  _o="$(/bin/sh "$BIN/journey-gen-check-candidate.sh" "$cand" --origin EXTRACTED 2>&1)"; _ec=$?
  assert_eq "0" "$_ec" "worked example: passes journey-gen-check-candidate.sh --origin EXTRACTED"
  [ "$_ec" -eq 0 ] || printf 'diagnostic: %s\n' "$_o"

  # ── (f-2) journey-extracted-stage.sh's candidate reader ─────────────────
  # minimal matching MANIFEST.md: declares exactly the one anchor the worked
  # example's candidate covers (FEAT-014) — no screen/flows anchor, so the
  # single-candidate file satisfies coverage completeness end to end.
  mf="$_jt/MANIFEST.md"
  cat > "$mf" << MFEOF
EXTRACTION-MANIFEST BEGIN
manifest_version: 1
extraction_commit: $commit
feat: FEAT-014 | behaviors=1 | states_filled=1 | grade_counts=C:1,I:0,G:0,X:0
e2e_test: tests/e2e/invoice-resubmit.spec.ts | framework=playwright
EXTRACTION-MANIFEST END
MFEOF

  out="$_jt/out/JOURNEY_EXTRACTED.md"
  _o="$(/bin/sh "$BIN/journey-extracted-stage.sh" "$cand" "$mf" "$repo" "$out" 2>&1)"; _ec=$?
  assert_eq "0" "$_ec" "worked example: journey-extracted-stage.sh stages it cleanly"
  [ "$_ec" -eq 0 ] || printf 'diagnostic: %s\n' "$_o"
  assert_exit 0 test -f "$out"

  # staged output independently re-passes the full composed gate chain
  # (mirrors journey-extracted-stage_test.sh's own golden-fresh-stage checks)
  assert_exit 0 /bin/sh "$BIN/lint-journey-extracted.sh" "$out"
  assert_exit 0 /bin/sh "$BIN/check-extracted-provenance.sh" "$out" "$repo"
  assert_exit 0 /bin/sh "$BIN/check-extraction-coverage.sh" "$mf" "$out"

  _g="$(cat "$out" 2>/dev/null)"
  assert_contains "$_g" '## EXTRACTED-1 — "Invoice resubmission after a schema-error rejection"' \
    "worked example: staged as EXTRACTED-1 with its title preserved"
  _s0_prior_e2e="$( ( JOURNEY_EXTRACTED="$out"; export JOURNEY_EXTRACTED
    # shellcheck disable=SC1090
    . "$TESTS_DIR/../lib/journey-lib.sh"; extracted_field EXTRACTED-1 prior_e2e ) )"
  assert_eq "tests/e2e/invoice-resubmit.spec.ts" "$_s0_prior_e2e" \
    "worked example: prior_e2e carried into the staged entry"

  _s0_cleanup
  trap - EXIT INT TERM
else
  printf 'FAIL: worked-example execution harness skipped (Step 0.txt, git, or jq missing)\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi
