# shellcheck shell=sh
# simulator-run_test.sh — prompt/slicer/runner proofs for the Increment-4
# user-simulator engine (spec DC-3, rulings B/C/D). No model, no network.
# Every OUTDIR/target below lives under mktemp -d (outside journey/) — L14:
# this file never writes a file with the bare basename JOURNEY_INBOX.md
# under journey/.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
GEN="$TESTS_DIR/../gen"
BIN="$TESTS_DIR/../bin"
LIBFILE="$TESTS_DIR/../lib/journey-lib.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
SURFDIR="$TESTS_DIR/fixtures/surface"
SFX="$TESTS_DIR/fixtures/simulator"
SSOT="$GENDIR/SSOT.md"
SURF="$SURFDIR/TEST_SURFACE.golden.md"
SLICE="$BIN/simulator-gen-slice.sh"
SRUN="$GEN/runners/simulator-run.sh"
LINT="$BIN/lint-journey-inbox.sh"
CC="$BIN/journey-gen-check-candidate.sh"

_sr_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}
_sha_sr() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }
_ibfield() { ( JOURNEY_INBOX="$2"; export JOURNEY_INBOX; . "$LIBFILE"; inbox_field "$1" "$3" ); } # ID FILE KEY

# ═══════════════════════════════════════════════════════════════════════════
# Prompt contract (simulator-brain.md)
# ═══════════════════════════════════════════════════════════════════════════
_SB=$(cat "$GEN/prompts/simulator-brain.md")
assert_contains "$_SB" "READ ONLY THIS BUNDLE" "brain prompt: bundle-only read boundary"
assert_contains "$_SB" 'origin:          SIMULATOR' "brain prompt: worked example emits origin SIMULATOR"
assert_contains "$_SB" 'author_status:   UNWRITTEN' "brain prompt: worked example stays UNWRITTEN"
assert_contains "$_SB" "SIM-FAILED: " "brain prompt: loud bundle-failure token defined"
assert_contains "$_SB" "EMPTY-CANDIDATE" "brain prompt: clean-run token defined"
assert_contains "$_SB" "Abandon at the patience budget." "brain prompt: abandonment law stated"
assert_contains "$_SB" 'Never emit a `promotion_status:` line' "brain prompt: promotion authority stays human"
assert_contains "$_SB" "never claim anything is tested, verified, passing, or green" "brain prompt: core invariant stated"
assert_contains "$_SB" "is NOT skipped here" "brain prompt: contrast with the persona engine's skip rule stated"
assert_contains "$_SB" "json field_sources" "brain prompt: shares the frozen field_sources fence with every other generator"

# ═══════════════════════════════════════════════════════════════════════════
# Slicer proofs (simulator-gen-slice.sh)
# ═══════════════════════════════════════════════════════════════════════════
_t=$(mktemp -d)

SIM_APP_TARGET=staging SIM_APP_BUILD=build-2026-07-10 JOURNEY_RUNNER=playwright \
  sh "$SLICE" "$SSOT" "$SURF" "$_t/s1" >/dev/null 2>&1
assert_eq 0 $? "sslice-1: golden docs slice"
[ -f "$_t/s1/bundles/p1.md" ] && [ -f "$_t/s1/bundles/p2.md" ]
assert_eq 0 $? "sslice-1: EVERY persona gets a bundle, including P2's known_misbehaviors: [none: ...] (contrast with persona-gen-slice.sh, which skips it)"
_b1=$(cat "$_t/s1/bundles/p1.md")
assert_contains "$_b1" "uploads-wrong-file-first" "sslice-1: bundle carries the persona's own tokens"
assert_not_contains "$_b1" "Finance Reviewer" "sslice-1: bundle carries THIS persona only"
assert_contains "$_b1" "## SURFACE: invoices_list" "sslice-1: TEST_SURFACE inlined verbatim"
assert_contains "$_b1" "APP_TARGET: staging" "sslice-1: APP_TARGET injected from env"
assert_contains "$_b1" "APP_BUILD:  build-2026-07-10" "sslice-1: APP_BUILD injected from env"
assert_contains "$_b1" "RUNNER:     playwright" "sslice-1: RUNNER injected from env"
assert_contains "$_b1" "## Schema (inlined from journey/JOURNEY_MAP.template.md)" "sslice-1: frozen schema inlined"
assert_eq "2" "$(jq -r '.bundles | length' "$_t/s1/simulator-manifest.json")" "sslice-1: manifest records both bundles"

sh "$SLICE" "$SSOT" "$SURF" "$_t/s2" >/dev/null 2>&1
assert_eq 1 $? "sslice-2: SIM_APP_TARGET/SIM_APP_BUILD unset fails closed (runner-declared, never inferred)"

sed '/^patience_budget:/d' "$SSOT" > "$_t/bad-ssot.md"
SIM_APP_TARGET=t SIM_APP_BUILD=b sh "$SLICE" "$_t/bad-ssot.md" "$SURF" "$_t/s3" >/dev/null 2>&1
assert_eq 1 $? "sslice-3: SSOT failing lint-personas fails closed"

SIM_APP_TARGET=t SIM_APP_BUILD=b sh "$SLICE" "$SSOT" "$SURFDIR/TEST_SURFACE.missing-key.md" "$_t/s4" >/dev/null 2>&1
assert_eq 1 $? "sslice-4: TEST_SURFACE failing lint-test-surface fails closed"

rm -rf "$_t"

# ═══════════════════════════════════════════════════════════════════════════
# Runner proofs (simulator-run.sh)
# ═══════════════════════════════════════════════════════════════════════════
_t=$(mktemp -d)

# ── no-op default / backend-missing fail-closed ───────────────────────────
assert_exit 0 env -u RUN_LLM_GEN sh "$SRUN"
_noop_out=$(env -u RUN_LLM_GEN sh "$SRUN" 2>&1)
assert_contains "$_noop_out" "no-op" "sr-noop: no-op message printed"
RUN_LLM_GEN=1 sh "$SRUN" >/dev/null 2>&1; _sr_nonzero $? "sr-nobackend: RUN_LLM_GEN=1 without backend fails closed"

# ── booby-trap: JOURNEY_RUNNER / SIM_APP_TARGET / SIM_APP_BUILD each fail
# EARLY — proved by a backend that would leave a sentinel file if invoked ──
_TRAP="$_t/trap.sh"
cat > "$_TRAP" << TRAP
#!/bin/sh
touch "$_t/SENTINEL"
exit 1
TRAP
chmod +x "$_TRAP"

rm -f "$_t/SENTINEL"
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_TRAP" SIM_APP_TARGET=t SIM_APP_BUILD=b \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/tr1" >/dev/null 2>&1
_sr_nonzero $? "sr-trap: missing JOURNEY_RUNNER fails closed"
[ ! -f "$_t/SENTINEL" ]; assert_eq 0 $? "sr-trap: missing JOURNEY_RUNNER — backend NEVER invoked (booby trap unsprung)"

rm -f "$_t/SENTINEL"
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_TRAP" JOURNEY_RUNNER=playwright SIM_APP_BUILD=b \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/tr2" >/dev/null 2>&1
_sr_nonzero $? "sr-trap: missing SIM_APP_TARGET fails closed"
[ ! -f "$_t/SENTINEL" ]; assert_eq 0 $? "sr-trap: missing SIM_APP_TARGET — backend NEVER invoked"

rm -f "$_t/SENTINEL"
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_TRAP" JOURNEY_RUNNER=playwright SIM_APP_TARGET=t \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/tr3" >/dev/null 2>&1
_sr_nonzero $? "sr-trap: missing SIM_APP_BUILD fails closed"
[ ! -f "$_t/SENTINEL" ]; assert_eq 0 $? "sr-trap: missing SIM_APP_BUILD — backend NEVER invoked"

# ── stub backend: house idiom (mirrors persona-run_test.sh's STUB_PGEN_MODE) ─
_STUB="$_t/stub.sh"
cat > "$_STUB" << 'STUB'
#!/bin/sh
case "$1" in
  *simulator-brain.md)
    case "${STUB_SIM_MODE:-golden}" in
      golden)
        case "$2" in
          *bundles/p1.md) cat "$SCAND1" ;;
          *bundles/p2.md) cat "$SCAND2" ;;
          *) exit 1 ;;
        esac ;;
      prose) printf 'Here is a lovely simulator narrative...\n' ;;
      wrongpatience)
        case "$2" in
          *bundles/p1.md) sed 's/patience_budget: 2/patience_budget: 99/' "$SCAND1" ;;
          *bundles/p2.md) cat "$SCAND2" ;;
          *) exit 1 ;;
        esac ;;
      withstatus)
        case "$2" in
          *bundles/p1.md) sed 's/^origin:          SIMULATOR/promotion_status: ACCEPTED\n&/' "$SCAND1" ;;
          *bundles/p2.md) cat "$SCAND2" ;;
          *) exit 1 ;;
        esac ;;
      simfailed) printf 'SIM-FAILED: bundle persona missing a usable goal\n' ;;
      empty)     printf 'EMPTY-CANDIDATE\n' ;;
    esac ;;
  *) exit 1 ;;
esac
STUB
chmod +x "$_STUB"
export SCAND1="$SFX/expected-candidate-p1.md" SCAND2="$SFX/expected-candidate-p2.md"

# ── sr-1: golden replay end-to-end (assembly, ids, PROPOSED, evidence) ──────
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright \
  SIM_APP_TARGET=staging SIM_APP_BUILD=build-2026-07-10 \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/r1" >/dev/null 2>&1
assert_eq 0 $? "sr-1: golden replay passes end-to-end"
_inbox="$_t/r1/JOURNEY_INBOX.md"
sh "$LINT" "$_inbox" >/dev/null 2>&1
assert_eq 0 $? "sr-1: assembled inbox is lint-clean"
_g=$(cat "$_inbox")
assert_contains "$_g" '## INBOX-1 —' "sr-1: ids assigned from 1"
assert_contains "$_g" '## INBOX-2 —' "sr-1: second candidate gets INBOX-2"
assert_eq "PROPOSED" "$(_ibfield INBOX-1 "$_inbox" promotion_status)" "sr-1: promotion_status forced to PROPOSED regardless of model content"
assert_eq "SIMULATOR" "$(_ibfield INBOX-1 "$_inbox" origin)" "sr-1: origin forced to SIMULATOR"
assert_eq "UNWRITTEN" "$(_ibfield INBOX-1 "$_inbox" author_status)" "sr-1: author_status forced to UNWRITTEN"

[ -f "$_t/r1/transcripts/INBOX-1.transcript.md" ]
assert_eq 0 $? "sr-1: transcript artifact for INBOX-1 exists"
[ -f "$_t/r1/transcripts/INBOX-2.transcript.md" ]
assert_eq 0 $? "sr-1: transcript artifact for INBOX-2 exists"
assert_eq "transcripts/INBOX-1.transcript.md" "$(_ibfield INBOX-1 "$_inbox" evidence)" \
  "sr-1: top-level evidence field is the runner-owned transcript relpath"
_trace1_first_evi=$(awk '
  $0 ~ "^## INBOX-1 " { inblk = 1 }
  inblk && /^## / && $0 !~ "^## INBOX-1 " { exit }
  inblk && /^simulator_trace:/ { intr = 1; next }
  intr && /^  - evidence: / { sub(/^  - evidence: /, ""); print; exit }
' "$_inbox")
assert_eq "transcripts/INBOX-1.transcript.md" "$_trace1_first_evi" "sr-1: transcript relpath is the FIRST simulator_trace evidence entry"
assert_eq "transcripts/INBOX-2.transcript.md, traces/p2-audit-retry.png" "$(_ibfield INBOX-2 "$_inbox" evidence)" \
  "sr-1: model-supplied extra evidence passes through AFTER the injected transcript"

# ── sr-2: append run — SAME outdir/target continues past the prior ids ─────
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright \
  SIM_APP_TARGET=staging SIM_APP_BUILD=build-2026-07-10 \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/r1" >/dev/null 2>&1
assert_eq 0 $? "sr-2: second pass over the same outdir/target succeeds"
_g2=$(cat "$_inbox")
assert_contains "$_g2" '## INBOX-1 —' "sr-2: original INBOX-1 entry preserved (append, never overwrite)"
assert_contains "$_g2" '## INBOX-3 —' "sr-2: third candidate continues at INBOX-3"
assert_contains "$_g2" '## INBOX-4 —' "sr-2: fourth candidate continues at INBOX-4"

# ── sr-3: a model-declared promotion_status is REJECTED, never rewritten ───
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright \
  SIM_APP_TARGET=staging SIM_APP_BUILD=build-2026-07-10 STUB_SIM_MODE=withstatus \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/r3" 2>&1 >/dev/null); _ec=$?
_sr_nonzero "$_ec" "sr-3: model-declared promotion_status fails closed"
assert_contains "$_o" "PROMOTION_STATUS_FORBIDDEN" "sr-3: names PROMOTION_STATUS_FORBIDDEN"
[ ! -f "$_t/r3/JOURNEY_INBOX.md" ]; assert_eq 0 $? "sr-3: nothing renamed when promotion_status is forbidden-rejected"

# ── sr-4: candidate failing the shared format check -> nothing renamed ─────
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright \
  SIM_APP_TARGET=staging SIM_APP_BUILD=build-2026-07-10 STUB_SIM_MODE=prose \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/r4" 2>&1 >/dev/null); _ec=$?
_sr_nonzero "$_ec" "sr-4: free-prose candidate fails closed"
assert_contains "$_o" "format check" "sr-4: attributed to the candidate format check"
[ ! -f "$_t/r4/JOURNEY_INBOX.md" ]; assert_eq 0 $? "sr-4: nothing renamed on a format-check failure"

# ── sr-5: trace echo mismatch (wrong patience_budget) -> fail closed ───────
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright \
  SIM_APP_TARGET=staging SIM_APP_BUILD=build-2026-07-10 STUB_SIM_MODE=wrongpatience \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/r5" 2>&1 >/dev/null); _ec=$?
_sr_nonzero "$_ec" "sr-5: mismatched patience_budget echo fails closed"
assert_contains "$_o" "PATIENCE_BUDGET_MISMATCH" "sr-5: names PATIENCE_BUDGET_MISMATCH"

# ── sr-6: SIM-FAILED is a loud failure ──────────────────────────────────────
_o=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright \
  SIM_APP_TARGET=staging SIM_APP_BUILD=build-2026-07-10 STUB_SIM_MODE=simfailed \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/r6" 2>&1 >/dev/null); _ec=$?
_sr_nonzero "$_ec" "sr-6: SIM-FAILED exits non-zero"
assert_contains "$_o" "SIM-FAILED:" "sr-6: the model's own SIM-FAILED token is surfaced"

# ── sr-7: EMPTY-CANDIDATE (every bundle) -> attempts log, no inbox, exit 0 ──
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright \
  SIM_APP_TARGET=staging SIM_APP_BUILD=build-2026-07-10 STUB_SIM_MODE=empty \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/r7" >/dev/null 2>&1
assert_eq 0 $? "sr-7: an all-EMPTY-CANDIDATE pass succeeds (spec 10.5: a clean run is positive evidence)"
[ -f "$_t/r7/SIMULATOR_ATTEMPTS.md" ]; assert_eq 0 $? "sr-7: attempts log written"
_att=$(cat "$_t/r7/SIMULATOR_ATTEMPTS.md")
assert_contains "$_att" "ATTEMPTED: P1" "sr-7: attempts log records P1's attempt"
assert_contains "$_att" "ATTEMPTED: P2" "sr-7: attempts log records P2's attempt"
[ ! -f "$_t/r7/JOURNEY_INBOX.md" ]; assert_eq 0 $? "sr-7: no inbox entry created for an EMPTY-CANDIDATE pass"

# ── sr-8: pre-existing target inbox is byte-unchanged on failure ───────────
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright \
  SIM_APP_TARGET=staging SIM_APP_BUILD=build-2026-07-10 \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/r8-seed" >/dev/null 2>&1
_pre="$_t/r8-seed/JOURNEY_INBOX.md"
_sha_before=$(_sha_sr "$_pre")
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright \
  SIM_APP_TARGET=staging SIM_APP_BUILD=build-2026-07-10 STUB_SIM_MODE=prose \
  JOURNEY_TARGET_INBOX="$_pre" \
  sh "$SRUN" "$SSOT" "$SURF" "$_t/r8-fail" >/dev/null 2>&1
_ec=$?
_sr_nonzero "$_ec" "sr-8: attack pass against a pre-existing target fails closed"
_sha_after=$(_sha_sr "$_pre")
assert_eq "$_sha_before" "$_sha_after" "sr-8: pre-existing target inbox is byte-unchanged on failure (sha256)"

unset SCAND1 SCAND2

# ═══════════════════════════════════════════════════════════════════════════
# sr-9: --origin SIMULATOR is a restrict-never-broaden ADDITION — DERIVED and
# PERSONA behavior of journey-gen-check-candidate.sh is byte-unchanged. The
# suite-wide proof is journey-gen-candidate_test.sh / persona-origin_test.sh
# (run.sh runs every *_test.sh, so both execute alongside this file); this
# is an explicit, local belt-and-suspenders re-check.
# ═══════════════════════════════════════════════════════════════════════════
sh "$CC" "$GENDIR/golden/expected-candidate-feat-001.md" >/dev/null 2>&1
assert_eq 0 $? "sr-9: DERIVED candidate still passes with no --origin flag (back-compat unchanged)"
sh "$CC" "$GENDIR/golden/expected-candidate-feat-001.md" --origin DERIVED >/dev/null 2>&1
assert_eq 0 $? "sr-9: DERIVED candidate still passes --origin DERIVED explicitly"
_pcand="$_t/persona-check.candidate"
sed 's/^origin:          DERIVED$/origin:          PERSONA/' "$GENDIR/golden/expected-candidate-feat-001.md" > "$_pcand"
sh "$CC" "$_pcand" --origin PERSONA >/dev/null 2>&1
assert_eq 0 $? "sr-9: PERSONA candidate still passes --origin PERSONA"
sh "$CC" "$_pcand" --origin SIMULATOR >/dev/null 2>&1; _ec=$?
_sr_nonzero "$_ec" "sr-9: a PERSONA-origin candidate is still rejected under --origin SIMULATOR (restrict-never-broaden)"

# ── L14 sanity: every path above lives under mktemp -d, never journey/ ─────
case "$_t" in
  "$TESTS_DIR"*) printf 'FAIL: L14: temp dir %s is under journey/tests (bare-basename risk)\n' "$_t"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)) ;;
  *) printf 'ok: L14: all runner output stays under mktemp -d (%s), outside journey/\n' "$_t" ;;
esac

rm -rf "$_t"
