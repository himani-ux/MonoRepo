# shellcheck shell=sh
# journey-gen-split_test.sh — sentinel splitter + runner fail-closed proofs.
#
# Post-merge review C1/C2: the merge backend's stdout is the ONLY channel for
# the three §5.1/§5.2 artifacts. The splitter materializes them
# deterministically; the runner must NEVER silently skip the coverage gate
# when the artifacts are missing.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$TESTS_DIR/../bin"
SPLIT="$BIN/journey-gen-split.sh"
RUNNER="$TESTS_DIR/../gen/runners/fanout-run.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
G="$GENDIR/golden"

GMAP="$G/expected-journey-map.generated.md"
GMAN="$G/expected-coverage-manifest.json"
GGAP="$G/expected-gaps.md"

assert_nonzero() { # ACTUAL_CODE MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

_SP_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/journey-split-test-XXXXXXXX") || {
  printf 'FAIL: split-test mktemp -d failed\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1)); }

if [ -n "${_SP_ROOT:-}" ] && [ -d "$_SP_ROOT" ]; then

# Helper: wrap a file in FILE sentinels onto stdout
_wrap() { # NAME FILE
  printf '=== FILE: %s ===\n' "$1"
  cat "$2"
  printf '=== END FILE ===\n'
}

# Golden three-artifact merge.out
_mk_good_merge_out() { # DEST
  { _wrap "JOURNEY_MAP.generated.md" "$GMAP"
    _wrap "JOURNEY_COVERAGE_MANIFEST.json" "$GMAN"
    _wrap "JOURNEY_COVERAGE_GAPS.md" "$GGAP"; } > "$1"
}

# ── split-1: golden sentinel stream → three byte-identical artifacts ──────────
_d1="$_SP_ROOT/s1"; mkdir -p "$_d1"
_mk_good_merge_out "$_d1/merge.out"
sh "$SPLIT" "$_d1/merge.out" "$_d1" >/dev/null 2>&1
assert_eq 0 $? "split-1: golden sentinel stream splits with exit 0"
for _f in JOURNEY_MAP.generated.md JOURNEY_COVERAGE_MANIFEST.json JOURNEY_COVERAGE_GAPS.md; do
  [ -f "$_d1/$_f" ] || { printf 'FAIL: split-1 missing %s\n' "$_f"; ASSERT_FAILS=$((ASSERT_FAILS + 1)); }
done
if cmp -s "$_d1/JOURNEY_MAP.generated.md" "$GMAP" \
   && cmp -s "$_d1/JOURNEY_COVERAGE_MANIFEST.json" "$GMAN" \
   && cmp -s "$_d1/JOURNEY_COVERAGE_GAPS.md" "$GGAP"; then
  printf 'ok: split-1: artifacts byte-identical to the wrapped inputs\n'
else
  printf 'FAIL: split-1: split artifacts differ from wrapped inputs\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi

# ── split-2: a missing artifact section fails closed, writes nothing ─────────
_d2="$_SP_ROOT/s2"; mkdir -p "$_d2"
{ _wrap "JOURNEY_MAP.generated.md" "$GMAP"
  _wrap "JOURNEY_COVERAGE_MANIFEST.json" "$GMAN"; } > "$_d2/merge.out"
sh "$SPLIT" "$_d2/merge.out" "$_d2" >/dev/null 2>&1
assert_nonzero $? "split-2: 2-of-3 sections rejected (fail closed)"
assert_eq "" "$(ls "$_d2" | grep -v '^merge.out$')" \
  "split-2: no partial artifacts written on failure"

# ── split-3: duplicate section fails closed ───────────────────────────────────
_d3="$_SP_ROOT/s3"; mkdir -p "$_d3"
{ _mk_good_merge_out /dev/stdout
  _wrap "JOURNEY_MAP.generated.md" "$GMAP"; } > "$_d3/merge.out"
sh "$SPLIT" "$_d3/merge.out" "$_d3" >/dev/null 2>&1
assert_nonzero $? "split-3: duplicate FILE section rejected"

# ── split-4: unknown / traversal filename fails closed ────────────────────────
_d4="$_SP_ROOT/s4"; mkdir -p "$_d4"
{ _mk_good_merge_out /dev/stdout
  _wrap "../evil.md" "$GGAP"; } > "$_d4/merge.out"
sh "$SPLIT" "$_d4/merge.out" "$_d4" >/dev/null 2>&1
assert_nonzero $? "split-4: unknown artifact name (../evil.md) rejected"
[ ! -f "$_SP_ROOT/evil.md" ]
assert_eq 0 $? "split-4: no traversal write occurred"

# ── split-5: prose outside sections (backend apology/preamble) fails closed ──
_d5="$_SP_ROOT/s5"; mkdir -p "$_d5"
{ printf 'Sure! Here are your artifacts:\n'
  _mk_good_merge_out /dev/stdout; } > "$_d5/merge.out"
sh "$SPLIT" "$_d5/merge.out" "$_d5" >/dev/null 2>&1
assert_nonzero $? "split-5: prose outside FILE sections rejected (fail closed)"

# ── split-6: unterminated section fails closed ────────────────────────────────
_d6="$_SP_ROOT/s6"; mkdir -p "$_d6"
{ _wrap "JOURNEY_MAP.generated.md" "$GMAP"
  _wrap "JOURNEY_COVERAGE_MANIFEST.json" "$GMAN"
  printf '=== FILE: JOURNEY_COVERAGE_GAPS.md ===\n'
  cat "$GGAP"; } > "$_d6/merge.out"
sh "$SPLIT" "$_d6/merge.out" "$_d6" >/dev/null 2>&1
assert_nonzero $? "split-6: unterminated FILE section rejected"

# ── split-7: empty merge.out fails closed ─────────────────────────────────────
_d7="$_SP_ROOT/s7"; mkdir -p "$_d7"
: > "$_d7/merge.out"
sh "$SPLIT" "$_d7/merge.out" "$_d7" >/dev/null 2>&1
assert_nonzero $? "split-7: empty merge output rejected (fail closed)"

# ── Runner proofs (deterministic — stub backend, no model, no network) ────────
# Stub: fanout-generator → the frozen golden candidate; merge-dedup → replay
# $STUB_MERGE; refuter-fidelity → one non-blocking line.
_STUB="$_SP_ROOT/stub-backend.sh"
GOLDEN_CAND="$G/expected-candidate-feat-001.md"
cat > "$_STUB" << 'STUB'
#!/bin/sh
case "$1" in
  *fanout-generator.md) cat "$GOLDEN_CAND" ;;
  *merge-dedup.md)      cat "$STUB_MERGE" ;;
  *refuter-fidelity.md) printf 'correct: stub review — no findings\n' ;;
  *) printf 'stub: unknown prompt %s\n' "$1" >&2; exit 1 ;;
esac
STUB
chmod +x "$_STUB"

# ── run-1: merge emits garbage (no sentinels) → runner FAILS CLOSED ──────────
# Regression lock for review C1: pre-fix, the runner silently skipped the
# coverage gate and exited 0 when the artifacts were never materialized.
_r1="$_SP_ROOT/r1"; mkdir -p "$_r1"
printf 'I could not produce the artifacts, sorry.\n' > "$_SP_ROOT/garbage.out"
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright GOLDEN_CAND="$GOLDEN_CAND" STUB_MERGE="$_SP_ROOT/garbage.out" \
  sh "$RUNNER" "$GENDIR/SSOT.md" "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$_r1" >/dev/null 2>&1
assert_nonzero $? "run-1: merge without sentinel artifacts → runner exits non-zero (no silent gate skip)"
[ ! -f "$_r1/JOURNEY_FIDELITY_REVIEW.md" ]
assert_eq 0 $? "run-1: refuter never ran on unmaterialized artifacts"

# ── run-1b: generator emits free prose → runner dies BEFORE the merge ────────
_r1b="$_SP_ROOT/r1b"; mkdir -p "$_r1b"
_PROSE_STUB="$_SP_ROOT/prose-stub.sh"
cat > "$_PROSE_STUB" << 'STUB'
#!/bin/sh
case "$1" in
  *fanout-generator.md) printf 'Here is a journey I designed...\n' ;;
  *) printf 'should never reach the merge\n' >&2; exit 1 ;;
esac
STUB
chmod +x "$_PROSE_STUB"
_r1berr=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_PROSE_STUB" JOURNEY_RUNNER=playwright \
  sh "$RUNNER" "$GENDIR/SSOT.md" "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$_r1b" 2>&1 >/dev/null); _r1bec=$?
assert_nonzero "$_r1bec" "run-1b: free-prose candidate stops the run pre-merge"
assert_contains "$_r1berr" "format check" "run-1b: failure attributed to the candidate format check"

# ── run-2: golden replay end-to-end → exit 0, artifacts + gate + review ──────
_r2="$_SP_ROOT/r2"; mkdir -p "$_r2"
_mk_good_merge_out "$_SP_ROOT/golden-merge.out"
RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB" JOURNEY_RUNNER=playwright GOLDEN_CAND="$GOLDEN_CAND" STUB_MERGE="$_SP_ROOT/golden-merge.out" \
  sh "$RUNNER" "$GENDIR/SSOT.md" "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$_r2" >/dev/null 2>&1
assert_eq 0 $? "run-2: golden replay through stub backend passes end-to-end"
for _f in JOURNEY_MAP.generated.md JOURNEY_COVERAGE_MANIFEST.json JOURNEY_COVERAGE_GAPS.md JOURNEY_FIDELITY_REVIEW.md; do
  [ -f "$_r2/$_f" ] || { printf 'FAIL: run-2 missing %s\n' "$_f"; ASSERT_FAILS=$((ASSERT_FAILS + 1)); }
done
printf 'ok: run-2: all four artifacts materialized deterministically\n'

rm -rf "$_SP_ROOT"
fi

# ── run-3: diluted-oracle replay → runner dies at the PROVENANCE gate ─────────
# Coverage passes on the diluted candidate by design; the runner must still
# fail closed before the refuter ever sees it.
_R3=$(mktemp -d "${TMPDIR:-/tmp}/journey-run3-XXXXXXXX")
_ADV="$GENDIR/adversarial/diluted-oracle"
_STUB3="$_R3/stub.sh"
cat > "$_STUB3" << 'STUB'
#!/bin/sh
case "$1" in
  *fanout-generator.md) cat "$GOLDEN_CAND3" ;;
  *merge-dedup.md)      cat "$STUB_MERGE" ;;
  *refuter-fidelity.md) printf 'correct: stub review\n' ;;
  *) exit 1 ;;
esac
STUB
chmod +x "$_STUB3"
{ printf '=== FILE: JOURNEY_MAP.generated.md ===\n'; cat "$_ADV/JOURNEY_MAP.generated.md"
  printf '=== END FILE ===\n=== FILE: JOURNEY_COVERAGE_MANIFEST.json ===\n'; cat "$_ADV/JOURNEY_COVERAGE_MANIFEST.json"
  printf '=== END FILE ===\n=== FILE: JOURNEY_COVERAGE_GAPS.md ===\n'; cat "$_ADV/JOURNEY_COVERAGE_GAPS.md"
  printf '=== END FILE ===\n'; } > "$_R3/diluted-merge.out"
_r3out="$_R3/out"; mkdir -p "$_r3out"
_r3err=$(RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$_STUB3" JOURNEY_RUNNER=playwright \
  GOLDEN_CAND3="$GENDIR/golden/expected-candidate-feat-001.md" STUB_MERGE="$_R3/diluted-merge.out" \
  sh "$RUNNER" "$GENDIR/SSOT.md" "$GENDIR/PRD.md" "$GENDIR/APP_FLOW.md" "$_r3out" 2>&1 >/dev/null); _r3ec=$?
if [ "$_r3ec" -ne 0 ]; then printf 'ok: run-3: diluted-oracle replay fails closed at the runner\n'; else
  printf 'FAIL: run-3: diluted-oracle replay passed the runner\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
assert_contains "$_r3err" "provenance" "run-3: failure attributed to the provenance gate"
[ ! -f "$_r3out/JOURNEY_FIDELITY_REVIEW.md" ]
assert_eq 0 $? "run-3: refuter never ran on a provenance-failing candidate"
rm -rf "$_R3"
