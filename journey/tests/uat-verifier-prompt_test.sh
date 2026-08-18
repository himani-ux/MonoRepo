# uat-verifier-prompt_test.sh — Task 6: deterministic token-lock validation of
# the uat-verifier PROMPT CONTRACT (journey/gen/prompts/uat-verifier.md,
# spec 2026-07-09 §5.1, O8 rename — the code-READING sibling of the blind
# refuter family).
#
# Invokes NO model. Standing honesty note: these assertions prove the
# contract is STATED in the prompt text — they do NOT prove a live model
# OBEYS it. Live verifier behavior is exercised only by the opt-in
# RUN_LLM_GEN=1 harness a later task wires to journey/gen/runners/uat-verify-run.sh.
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

uat_vp_tests_dir="$(cd "$(dirname "$0")" && pwd)"
uat_vp_prompt="$uat_vp_tests_dir/../gen/prompts/uat-verifier.md"

if [ ! -f "$uat_vp_prompt" ]; then
  printf 'FAIL: uat-verifier prompt asset missing: %s\n' "$uat_vp_prompt"
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
  uat_vp_p=""
else
  printf 'ok: uat-verifier prompt asset exists\n'
  uat_vp_p="$(cat "$uat_vp_prompt")"
fi

# ── REQUIRED — role framing + the stated read-only departure from the blind
#    refuter family (Step 0 posture: the repo is ground truth to consult) ──
assert_contains "$uat_vp_p" "REPO_ROOT"    "prompt: verifier reads the project repo at REPO_ROOT"
assert_contains "$uat_vp_p" "read-only"    "prompt: repo access is read-only (stated departure from blind refuters)"
assert_contains "$uat_vp_p" "pinned commit" "prompt: repo reads are pinned to the pinned commit, never the working tree"

# ── REQUIRED — input contract: one file, CHECKED_HASH then report verbatim ─
assert_contains "$uat_vp_p" "CHECKED_HASH" "prompt: input's first line carries CHECKED_HASH: <sha>"

# ── REQUIRED — verdict-block grammar (byte-shape check-uat-verification.sh
#    enforces — §3.2) ──────────────────────────────────────────────────────
assert_contains "$uat_vp_p" "UAT-VERDICT:"    "prompt: verdict block header UAT-VERDICT:"
assert_contains "$uat_vp_p" "- verdict:"      "prompt: verdict field - verdict:"
assert_contains "$uat_vp_p" "confirm"         "prompt: vocabulary includes confirm"
assert_contains "$uat_vp_p" "downgrade"       "prompt: vocabulary includes downgrade"
assert_contains "$uat_vp_p" "refute"          "prompt: vocabulary includes refute"
assert_contains "$uat_vp_p" "- regrade:"      "prompt: regrade field required on downgrade, must differ from author's grade"
assert_contains "$uat_vp_p" "- residual:"     "prompt: residual field, downgrade/refute only, must say unverified"
assert_contains "$uat_vp_p" "- checked_hash:" "prompt: every verdict block echoes - checked_hash:"

# ── REQUIRED — one verdict per claim, every claim, no silent gaps ─────────
assert_contains "$uat_vp_p" "silence is not a review" "prompt: every claim gets a verdict block — silence is not a review"

# ── REQUIRED — doubt resolution rule, verbatim, plus its cost rationale ───
assert_contains "$uat_vp_p" "When in doubt between confirm and downgrade, downgrade" \
  "prompt: doubt-resolution rule verbatim (overstated claims are the expensive failure)"

# ── REQUIRED — citations/searches are actually read and re-verified ───────
assert_contains "$uat_vp_p" "deterministically re-verified" \
  "prompt: every citation/search is deterministically re-verified against the pinned commit (fabrication is a guaranteed catch)"
assert_contains "$uat_vp_p" "at least the author's" \
  "prompt: confirming an absence needs searches >= the author's, plus the verifier's own broader ones"

# ── FORBIDDEN — no promotion authority (mirrors the refuter family) ───────
assert_contains "$uat_vp_p" "never approve, promote, or mark anything citable" \
  "prompt: forbidden sentence present verbatim — only the promote ceremony marks citable"
assert_contains "$uat_vp_p" "never bless" "prompt: forbids blessing"

# ── FORBIDDEN — no runtime-truth fields (name all five) ───────────────────
for uat_vp_rt in ci_status last_run ci_run_id ci_artifact failure_summary; do
  assert_contains "$uat_vp_p" "$uat_vp_rt" "prompt: forbids runtime-truth field $uat_vp_rt"
done

# ── FORBIDDEN — no re-running, no editing, no false test claims ───────────
assert_contains "$uat_vp_p" "never re-run the UAT" "prompt: forbids re-running the UAT or the app"

# ── FORBIDDEN — no reference to other framework artifacts, named or not ───
# (the prompt must express "consult only REPO_ROOT + the input file" WITHOUT
# ever naming TEST_SURFACE.md — the assert_not_contains below is the proof)
assert_not_contains "$uat_vp_p" "TEST_SURFACE.md" "prompt: never names TEST_SURFACE.md"

# ══════════════════════════════════════════════════════════════════════
# Fix-wave (W1/D2, W2/D3-a, W4/D3-d) — verifier trust-boundary locks.
# ══════════════════════════════════════════════════════════════════════

# ── W1 (D2): REPO_ROOT is named IN-BAND, quoted git -C law, MISSING-ROOT ──
assert_contains "$uat_vp_p" "REPO_ROOT: <abs path>" "prompt: REPO_ROOT is named in-band on its own input line"
assert_contains "$uat_vp_p" "never an" "prompt: REPO_ROOT is a hard law, not an ambient assumption"
assert_contains "$uat_vp_p" 'git -C "$REPO_ROOT"' "prompt: git -C law, quoted"
assert_contains "$uat_vp_p" "always quoted" "prompt: states paths must always be quoted (this repo's own path has a space)"
assert_contains "$uat_vp_p" "contain spaces" "prompt: names the space-in-path hazard explicitly"
assert_contains "$uat_vp_p" "MISSING-ROOT" "prompt: MISSING-ROOT degenerate token"

# ── W2 (D3-a): citations gate-enforced on refute/downgrade, lint's turf ───
assert_contains "$uat_vp_p" "CITATION_MISSING" "prompt: names the CITATION_MISSING gate code"
assert_contains "$uat_vp_p" "gate-enforced, not just prose" "prompt: states the refute/downgrade citation law is gate-enforced"
assert_contains "$uat_vp_p" "LINT's jurisdiction" "prompt: report-internal deficiencies are lint's jurisdiction, never a downgrade/refute reason"

# ── W4 (D3-d): the artifact-evidence seam law, verbatim from the format doc §3, plus a worked example ──
assert_contains "$uat_vp_p" "binds an artifact's BYTES, not its MEANING" "prompt: artifact-seam law verbatim (sha256 binds bytes, not meaning)"
assert_contains "$uat_vp_p" "NEVER" "prompt: states the artifact-seam prohibition in caps"
assert_contains "$uat_vp_p" "solely because the artifact is not in the git tree" "prompt: forbids downgrading/refuting an artifact claim solely for tree-absence"
assert_contains "$uat_vp_p" "relative to the REPORT's own directory" "prompt: artifact relpaths resolve relative to the report, not REPO_ROOT's git tree"
assert_contains "$uat_vp_p" "Worked micro-example" "prompt: carries the artifact-seam worked micro-example"

# ── D6 (live re-characterization): SEARCH-LITERAL DISCIPLINE — the
# comment-collision law. A live verifier, correctly broadening beyond the
# author's search, emitted a bare-word literal ("throttle") that matched a
# COMMENT asserting the very absence under confirmation — gate 4.3
# re-executed it, SEARCH_DIVERGED, whole verification failed closed. The
# gate is correct and unchanged; the prompt must carry the citation
# discipline, because real codebases routinely contain comments naming
# absent features. ────────────────────────────────────────────────────────
assert_contains "$uat_vp_p" "SEARCH-LITERAL DISCIPLINE" "prompt: search-literal discipline law heading (D6)"
assert_contains "$uat_vp_p" 'git -C "$REPO_ROOT" grep -Fn' "prompt: re-execute-before-emit command shape, quoted -C form (D6)"
assert_contains "$uat_vp_p" "ZERO matches" "prompt: every emitted search must have re-executed to zero matches (D6)"
assert_contains "$uat_vp_p" "including comments or docs that merely mention" "prompt: comments/docs count as matches — a mention is a hit (D6)"
assert_contains "$uat_vp_p" "A comment naming an absent feature does not make it present" "prompt: comment-collision principle stated verbatim (D6)"
assert_contains "$uat_vp_p" "implementation-shaped" "prompt: refine toward implementation-shaped literals, not bare English words (D6)"
assert_contains "$uat_vp_p" "rateLimit(" "prompt: names a call-syntax literal example (D6)"
assert_contains "$uat_vp_p" "throttle(" "prompt: worked micro-example refines the exact live failure (bare 'throttle' -> call syntax) (D6)"
assert_contains "$uat_vp_p" "vacuous" "prompt: mirror-image warning — zero-hit must never be bought by vacuous narrowing (D6, cross-refs the lazy-narrow-confirm seam)"

printf 'ok: uat-verifier prompt contract token-lock complete (STATED, not model-obedience-tested)\n'
