#!/bin/sh
# journey-gen-acceptance_test.sh — Task 9: promotion-gate + thin-runner guards.
#
# DETERMINISTIC ONLY. No LLM, no RUN_LLM_GEN live path, no golden/adversarial
# live-regression lock (those are Task 10). This proves:
#   * the thin runner is a no-op unless RUN_LLM_GEN=1 (no model/network by default);
#   * promotion happens ONLY when lint + coverage + a clean refuter + a human
#     --approve marker all hold, and NEVER automatically from generation;
#   * promotion rejects runtime-truth fields, tested-status claims, coverage
#     failures, blocking refuter findings, TEST_SURFACE references;
#   * promoted journeys stay origin=DERIVED / author_status=UNWRITTEN and existing
#     non-DERIVED journeys are preserved byte-for-byte.
# shellcheck shell=sh

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$TESTS_DIR/../bin"
LIB="$TESTS_DIR/../lib/journey-lib.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
G="$GENDIR/golden"

PROMOTE="$BIN/journey-gen-promote.sh"
LINT="$BIN/lint-journey-map.sh"
RUNNER="$TESTS_DIR/../gen/runners/fanout-run.sh"

PRD="$GENDIR/PRD.md"; APP="$GENDIR/APP_FLOW.md"
GMAP="$G/expected-journey-map.generated.md"
GMAN="$G/expected-coverage-manifest.json"
GGAP="$G/expected-gaps.md"
RAW_CLEAN="$G/fidelity-clean.md"
RAW_BLOCK="$G/fidelity-blocking.md"

# Promote Gate 3b requires the fidelity review to be hash-bound to the
# candidate (the runner stamps reviewed_sha256 in live runs). Stamp the golden
# fixtures against the golden candidate once; all promote calls below use the
# stamped copies. Raw fixtures stay available for the binding proofs.
_sha256_fx() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }
_FIDT=$(mktemp -d)
{ printf 'reviewed_sha256: %s\n' "$(_sha256_fx "$GMAP")"; cat "$RAW_CLEAN"; } > "$_FIDT/clean.md"
{ printf 'reviewed_sha256: %s\n' "$(_sha256_fx "$GMAP")"; cat "$RAW_BLOCK"; } > "$_FIDT/block.md"
CLEAN="$_FIDT/clean.md"
BLOCK="$_FIDT/block.md"

_field() { ( JOURNEY_MAP="$1"; export JOURNEY_MAP; . "$LIB"; journey_field "$2" "$3" ); }

# ── Thin runner — deterministic no-op unless RUN_LLM_GEN=1 ─────────────────────
# Force-unset RUN_LLM_GEN so the no-op property holds regardless of the ambient
# env (a suite run under RUN_LLM_GEN=1 must not break this invariant).
assert_exit 0 env -u RUN_LLM_GEN sh "$RUNNER"
assert_contains "$(env -u RUN_LLM_GEN sh "$RUNNER" 2>&1)" "no-op" "runner is a no-op when RUN_LLM_GEN is unset (no model/network)"
RUN_LLM_GEN=1 sh "$RUNNER" >/dev/null 2>&1; _rec=$?
assert_eq 1 "$_rec" "runner fails closed under RUN_LLM_GEN=1 with no backend (still no network)"

# ── Promotion is NEVER automatic: all gates pass but no --approve → refuse ─────
T=$(mktemp -d)
sh "$PROMOTE" "$PRD" "$APP" "$GMAP" "$GMAN" "$GGAP" "$CLEAN" "$T/JOURNEY_MAP.md" >/dev/null 2>&1
assert_eq 1 $? "promote refuses without --approve even when all gates pass"
[ -f "$T/JOURNEY_MAP.md" ] && _w=wrote || _w=nowrite
assert_eq nowrite "$_w" "promote makes NO write to the target without --approve"
rm -rf "$T"

# ── Refuter veto: a BLOCKING finding refuses even with --approve ───────────────
T=$(mktemp -d)
sh "$PROMOTE" "$PRD" "$APP" "$GMAP" "$GMAN" "$GGAP" "$BLOCK" "$T/JOURNEY_MAP.md" --approve >/dev/null 2>&1
assert_eq 1 $? "promote refuses on a BLOCKING refuter finding (even with --approve)"
rm -rf "$T"

# ── Refuter veto (M2): a markdown/upper-case block finding also vetoes ─────────
T=$(mktemp -d)
printf '# fidelity\n- **BLOCK:** JOURNEY-101 dropped AC-2 — evidence: "..." (bundle FEAT-001 AC-2)\ncorrect: JOURNEY-102 faithful\n' > "$T/fidelity.md"
sh "$PROMOTE" "$PRD" "$APP" "$GMAP" "$GMAN" "$GGAP" "$T/fidelity.md" "$T/JOURNEY_MAP.md" --approve >/dev/null 2>&1
assert_eq 1 $? "promote refuses a markdown/upper-case block finding (- **BLOCK:**)"
[ -f "$T/JOURNEY_MAP.md" ] && _w=wrote || _w=nowrite
assert_eq nowrite "$_w" "promote makes NO write when a markdown/upper-case block finding is present"
rm -rf "$T"

# ── Coverage veto: a malformed §5.1 gap fails coverage → refuse ────────────────
T=$(mktemp -d)
printf 'source_id:    FEAT-001\nsource_type:  FEAT\nreason:       missing owner field\nexpiry:       2026-12-01\nreviewer:     bob\n' > "$T/gaps.md"
sh "$PROMOTE" "$PRD" "$APP" "$GMAP" "$GMAN" "$T/gaps.md" "$CLEAN" "$T/JOURNEY_MAP.md" --approve >/dev/null 2>&1
assert_eq 1 $? "promote refuses on coverage-gate failure (malformed gap)"
rm -rf "$T"

# ── Runtime-truth veto: a ci_status key in the candidate → refuse ─────────────
T=$(mktemp -d)
awk '{print} /^## JOURNEY-101/{print "ci_status: GREEN"}' "$GMAP" > "$T/map.md"
sh "$PROMOTE" "$PRD" "$APP" "$T/map.md" "$GMAN" "$GGAP" "$CLEAN" "$T/JOURNEY_MAP.md" --approve >/dev/null 2>&1
assert_eq 1 $? "promote refuses a candidate carrying a runtime-truth field (ci_status: GREEN)"
rm -rf "$T"

# ── Tested-status veto: a DERIVED journey claiming author_status != UNWRITTEN ──
T=$(mktemp -d)
sed 's/author_status:   UNWRITTEN/author_status:   WRITTEN/' "$GMAP" > "$T/map.md"
sh "$PROMOTE" "$PRD" "$APP" "$T/map.md" "$GMAN" "$GGAP" "$CLEAN" "$T/JOURNEY_MAP.md" --approve >/dev/null 2>&1
assert_eq 1 $? "promote refuses a DERIVED journey with author_status != UNWRITTEN (tested/written claim)"
rm -rf "$T"

# ── TEST_SURFACE veto ─────────────────────────────────────────────────────────
T=$(mktemp -d)
{ cat "$GMAP"; printf '\n<!-- generated from TEST_SURFACE.md -->\n'; } > "$T/map.md"
sh "$PROMOTE" "$PRD" "$APP" "$T/map.md" "$GMAN" "$GGAP" "$CLEAN" "$T/JOURNEY_MAP.md" --approve >/dev/null 2>&1
assert_eq 1 $? "promote refuses a candidate that references TEST_SURFACE.md"
rm -rf "$T"

# ── SUCCESS: all gates pass + --approve → append DERIVED, preserve PERSONA ─────
T=$(mktemp -d); TGT="$T/JOURNEY_MAP.md"
cat > "$TGT" <<'SEED'
# JOURNEY_MAP — canonical intent SSOT (pre-seeded)

## JOURNEY-001 — "hand-seeded persona journey"
origin:          PERSONA
persona:         P1
goal:            a pre-existing hand-authored journey
priority:        P0
covers:          FEAT-000
flows:           AF-0
oracle_surface:  UI
negative_states: seed_error
data_fixtures:
steps:
  1. do the seeded thing -> seed_error
oracle:          seeded oracle holds
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
SEED

sh "$PROMOTE" "$PRD" "$APP" "$GMAP" "$GMAN" "$GGAP" "$CLEAN" "$TGT" --approve >/dev/null 2>&1
assert_eq 0 $? "promote SUCCEEDS when lint + coverage + clean refuter + --approve all hold"
assert_contains "$(cat "$TGT")" "hand-seeded persona journey" "promote preserves the pre-seeded PERSONA journey"
assert_contains "$(cat "$TGT")" "origin:          PERSONA"     "promote does not clobber the non-DERIVED origin"
assert_contains "$(cat "$TGT")" "JOURNEY-101" "promote appended DERIVED JOURNEY-101"
assert_contains "$(cat "$TGT")" "JOURNEY-102" "promote appended DERIVED JOURNEY-102"
assert_eq DERIVED   "$(_field "$TGT" JOURNEY-101 origin)"        "promoted JOURNEY-101 origin=DERIVED survives"
assert_eq UNWRITTEN "$(_field "$TGT" JOURNEY-101 author_status)" "promoted JOURNEY-101 author_status=UNWRITTEN survives"
assert_exit 0 sh "$LINT" "$TGT"
rm -rf "$T"

# ═══════════════════════════════════════════════════════════════════════════════
# TASK 10 — FINAL ACCEPTANCE: increment-wide locks (deterministic + opt-in live)
# ═══════════════════════════════════════════════════════════════════════════════
CJC="$BIN/check-journey-coverage.sh"
PROMPTS="$TESTS_DIR/../gen/prompts"
JROOT="$(cd "$TESTS_DIR/.." && pwd)"
ADV="$GENDIR/adversarial/diluted-oracle"
_ids() { ( JOURNEY_MAP="$1"; export JOURNEY_MAP; . "$LIB"; journey_ids ); }

# ── Golden pipeline (deterministic): the frozen target shape is valid + complete
assert_exit 0 sh "$LINT" "$GMAP"
assert_exit 0 sh "$CJC" "$PRD" "$APP" "$GMAP" "$GMAN" "$GGAP"

# ── Duplicate-promotion guard (deterministic) — Task-9 seam #2 now GUARDED ─────
T=$(mktemp -d); TGT="$T/JOURNEY_MAP.md"
sh "$PROMOTE" "$PRD" "$APP" "$GMAP" "$GMAN" "$GGAP" "$CLEAN" "$TGT" --approve >/dev/null 2>&1
assert_eq 0 $? "acceptance: first promotion of the golden candidate succeeds"
sh "$PROMOTE" "$PRD" "$APP" "$GMAP" "$GMAN" "$GGAP" "$CLEAN" "$TGT" --approve >/dev/null 2>&1
assert_eq 1 $? "acceptance: re-promoting the same candidate is REFUSED (idempotence guard)"
assert_eq 1 "$(grep -c '^## JOURNEY-101 ' "$TGT")" "acceptance: JOURNEY-101 appears exactly once (no silent duplicate)"
rm -rf "$T"

# ── Generative prompt contracts present + guarded (Task 6/7/8) ────────────────
for _p in fanout-generator merge-dedup refuter-fidelity; do
  assert_exit 0 test -f "$PROMPTS/$_p.md"
done

# ── Increment scope assertions (deterministic) ────────────────────────────────
# NOTE (Increment 4, spec DC-3): this was originally an Increment-3 lock
# proving NO forward-scoped engine files existed yet. The simulator engine
# has since shipped (journey/bin/simulator-gen-slice.sh, journey/gen/
# runners/simulator-run.sh, journey/gen/prompts/simulator-brain.md,
# journey/gen/runners/simulator.workflow.md) — updated in the SAME commit
# as those files land (house rule 5: read the lock test first, update it
# alongside the doc/file it locks). Extracted/persona-engine/blind-
# authoring engines remain later increments and stay locked out here.
#
# NOTE (Increment 5, spec DC-5): same rule applied again — the reality
# engine's intake gate has now shipped (journey/bin/journey-reality-
# intake.sh), so "*reality*" is removed from the blocked glob below,
# mirroring exactly how "*simulator*" was removed above. Extracted
# baseline (Step 0) stays explicitly deferred per the goal doc's scope
# section and remains locked out.
#
# NOTE (EXTRACTED-baseline E1, spec I7/§14 Lock 5): same rule applied a
# third time — the E1 staging contract has now shipped
# (journey/bin/lint-journey-extracted.sh), so "*extracted*" is removed from
# the blocked glob below, the same deliberate, narrow unlock "*simulator*"
# and "*reality*" each received when their own engines shipped. Only
# "*extracted*" is removed — persona-engine/blind-authoring engines remain
# later increments and stay locked out. Spec Lock 5 requires the general
# protection be proven TESTED, not merely assumed to still work after this
# glob edit — see the planted-fixture assertion immediately below, which
# proves a persona-engine-named file still trips the (narrowed) guard.
assert_eq 0 "$(find "$JROOT" \( -name 'TEST_SURFACE.md' -o -name 'JOURNEY_INBOX.md' \) -type f | wc -l | tr -d ' ')" \
  "scope: no TEST_SURFACE.md / JOURNEY_INBOX.md present"
assert_eq 0 "$(find "$JROOT/bin" "$JROOT/gen" -type f \( -iname '*persona-engine*' -o -iname '*blind*' \) | wc -l | tr -d ' ')" \
  "scope: no persona-engine/blind-authoring engine files (simulator + reality-intake + extracted-staging shipped, Increments 4-5/E1)"

# ── General-protection proof (spec Lock 5): the narrowed glob still bans
# persona-engine/blind — proven on a PLANTED fixture, not assumed from the
# absence above (an absence proves nothing about whether the glob still
# WORKS; it could just as easily mean the glob syntax broke). A sandbox
# tree outside $JROOT is used so this test never depends on, or risks
# corrupting, the real journey/bin or journey/gen directories. ──────────────
_SG=$(mktemp -d)
mkdir -p "$_SG/bin" "$_SG/gen"
touch "$_SG/bin/persona-engine-run.sh" "$_SG/gen/blind-author-slice.sh"
_sg_hits="$(find "$_SG/bin" "$_SG/gen" -type f \( -iname '*persona-engine*' -o -iname '*blind*' \) | wc -l | tr -d ' ')"
assert_eq 2 "$_sg_hits" \
  "scope guard general protection: a planted persona-engine/blind-named file still trips the (narrowed) glob"
rm -rf "$_SG"

# every DERIVED journey in the shipped maps is author_status UNWRITTEN or EXEMPT (never WRITTEN)
_bad_as=0
for _m in "$GMAP" "$ADV/JOURNEY_MAP.generated.md"; do
  for _jid in $(_ids "$_m"); do
    [ "$(_field "$_m" "$_jid" origin)" = "DERIVED" ] || continue
    case "$(_field "$_m" "$_jid" author_status)" in
      UNWRITTEN|EXEMPT) : ;;
      *) _bad_as=$((_bad_as + 1)) ;;
    esac
  done
done
assert_eq 0 "$_bad_as" "scope: every DERIVED journey is author_status UNWRITTEN/EXEMPT (no tested-status claim)"

# runtime truth stays ledger-only: no runtime field keys in JOURNEY_MAP intent files
assert_eq 0 "$(grep -rlE '^[[:space:]]*(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):' "$GMAP" "$ADV/JOURNEY_MAP.generated.md" "$JROOT/JOURNEY_MAP.template.md" 2>/dev/null | wc -l | tr -d ' ')" \
  "scope: no runtime-truth field keys in JOURNEY_MAP intent (runtime truth is ledger-only)"

# ── Opt-in live golden + adversarial regression (RUN_LLM_GEN=1) ───────────────
if [ "${RUN_LLM_GEN:-0}" != "1" ]; then
  printf 'ok: live golden/adversarial regression SKIPPED (RUN_LLM_GEN unset) — deterministic-only, no model or network invoked\n'
elif [ -z "${JOURNEY_GEN_BACKEND:-}" ]; then
  printf 'ok: RUN_LLM_GEN=1 but no JOURNEY_GEN_BACKEND — live regression explicitly skipped; no network invoked\n'
  RUN_LLM_GEN=1 sh "$RUNNER" >/dev/null 2>&1
  assert_eq 1 $? "acceptance: runner fails closed under RUN_LLM_GEN=1 with no backend"
else
  printf 'RUN_LLM_GEN=1 + backend present: running live golden + adversarial regression...\n'
  _LOUT=$(mktemp -d)
  # (4) golden generation regression — fan-out + merge over the frozen golden docs
  RUN_LLM_GEN=1 JOURNEY_GEN_BACKEND="$JOURNEY_GEN_BACKEND" JOURNEY_RUNNER=playwright sh "$RUNNER" "$GENDIR/SSOT.md" "$PRD" "$APP" "$_LOUT" >/dev/null 2>&1
  _lg="$_LOUT/JOURNEY_MAP.generated.md"; _lm="$_LOUT/JOURNEY_COVERAGE_MANIFEST.json"; _lp="$_LOUT/JOURNEY_COVERAGE_GAPS.md"
  assert_exit 0 sh "$LINT" "$_lg"
  assert_exit 0 sh "$CJC" "$PRD" "$APP" "$_lg" "$_lm" "$_lp"
  # equivalent to the frozen expected: DERIVED/UNWRITTEN, golden anchors covered, AC-2 preserved
  _live_bad=0
  for _jid in $(_ids "$_lg"); do
    [ "$(_field "$_lg" "$_jid" origin)" = DERIVED ] || _live_bad=$((_live_bad + 1))
    [ "$(_field "$_lg" "$_jid" author_status)" = UNWRITTEN ] || _live_bad=$((_live_bad + 1))
  done
  assert_eq 0 "$_live_bad" "live: every generated journey is origin=DERIVED / author_status=UNWRITTEN"
  assert_contains "$(jq -r '._index|keys|join(" ")' "$_lm")" "FEAT-001" "live: coverage _index accounts for the golden anchors"
  assert_contains "$(cat "$_lg")" "immediately after upload" "live: generated oracle preserves FEAT-001 AC-2 (no dilution)"
  # (5) adversarial refuter regression — refuter on the diluted-oracle fixture BLOCKS AC-2
  "$JOURNEY_GEN_BACKEND" "$PROMPTS/refuter-fidelity.md" "$ADV" > "$_LOUT/fidelity.md" 2>/dev/null
  if grep -qiE '^[[:space:]]*block:.*AC-2' "$_LOUT/fidelity.md"; then
    printf 'ok: live refuter BLOCKS the diluted oracle naming AC-2\n'
  else
    printf 'FAIL: live refuter did not BLOCK the diluted oracle (AC-2)\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1))
  fi
  rm -rf "$_LOUT"
fi

# ── Anti-vacuous promote (review C4): zero DERIVED journeys is a refusal ──────
# Pre-fix, an empty candidate sailed through --approve and printed PROMOTED
# while appending nothing — a green light on a vacuous run.
_EV=$(mktemp -d)
printf '# JOURNEY_MAP — generated (empty candidate)\n' > "$_EV/empty-map.md"
_everr=$(sh "$PROMOTE" "$PRD" "$APP" "$_EV/empty-map.md" "$GMAN" "$GGAP" "$CLEAN" "$_EV/JOURNEY_MAP.md" --approve 2>&1 >/dev/null); _evec=$?
if [ "$_evec" -ne 0 ]; then printf 'ok: promote: empty candidate (zero DERIVED) refused\n'; else
  printf 'FAIL: promote: empty candidate PROMOTED vacuously\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
assert_contains "$_everr" "EMPTY_CANDIDATE" "promote: refusal names EMPTY_CANDIDATE"
[ ! -f "$_EV/JOURNEY_MAP.md" ]
assert_eq 0 $? "promote: no target map written on empty-candidate refusal"
rm -rf "$_EV"

# ── Provenance gate wired into promotion (review rec #2) ─────────────────────
# The diluted-oracle candidate is lint-clean and coverage-complete; with a
# CLEAN fidelity review (refuter miss) it previously PROMOTED. The provenance
# gate must now refuse it deterministically — the refuter is a second opinion,
# not the last line of defense.
_PV=$(mktemp -d)
_pverr=$(sh "$PROMOTE" "$PRD" "$APP" "$ADV/JOURNEY_MAP.generated.md" \
  "$ADV/JOURNEY_COVERAGE_MANIFEST.json" "$ADV/JOURNEY_COVERAGE_GAPS.md" \
  "$CLEAN" "$_PV/JOURNEY_MAP.md" --approve 2>&1 >/dev/null); _pvec=$?
if [ "$_pvec" -ne 0 ]; then printf 'ok: promote: diluted oracle + refuter miss REFUSED (provenance gate)\n'; else
  printf 'FAIL: promote: diluted oracle + clean fidelity PROMOTED (refuter was the last line of defense)\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
assert_contains "$_pverr" "provenance" "promote: refusal attributes the provenance gate"
[ ! -f "$_PV/JOURNEY_MAP.md" ]
assert_eq 0 $? "promote: no write on provenance refusal"
rm -rf "$_PV"

# ── Fidelity binding (review I6): review must be hash-bound to the candidate ──
_sha256() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'; else shasum -a 256 "$1" | awk '{print $1}'; fi; }
_FB=$(mktemp -d)
# (a) unstamped fidelity (no reviewed_sha256 line) → refused
_fberr=$(sh "$PROMOTE" "$PRD" "$APP" "$GMAP" "$GMAN" "$GGAP" "$RAW_CLEAN" "$_FB/m.md" --approve 2>&1 >/dev/null); _fbec=$?
if [ "$_fbec" -ne 0 ]; then printf 'ok: promote: unstamped fidelity refused (no reviewed_sha256)\n'; else
  printf 'FAIL: promote: unstamped fidelity accepted\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
assert_contains "$_fberr" "reviewed_sha256" "promote: refusal names reviewed_sha256"
# (b) stale stamp (hash of a DIFFERENT candidate) → refused
{ printf 'reviewed_sha256: %s\n' "$(_sha256 "$ADV/JOURNEY_MAP.generated.md")"; cat "$RAW_CLEAN"; } > "$_FB/stale.md"
_fberr=$(sh "$PROMOTE" "$PRD" "$APP" "$GMAP" "$GMAN" "$GGAP" "$_FB/stale.md" "$_FB/m.md" --approve 2>&1 >/dev/null); _fbec=$?
if [ "$_fbec" -ne 0 ]; then printf 'ok: promote: stale fidelity (other candidate hash) refused\n'; else
  printf 'FAIL: promote: stale fidelity accepted\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
# (c) correctly stamped → passes all fidelity gates (and promotes)
{ printf 'reviewed_sha256: %s\n' "$(_sha256 "$GMAP")"; cat "$RAW_CLEAN"; } > "$_FB/ok.md"
sh "$PROMOTE" "$PRD" "$APP" "$GMAP" "$GMAN" "$GGAP" "$_FB/ok.md" "$_FB/m.md" --approve >/dev/null 2>&1
assert_eq 0 $? "promote: correctly stamped fidelity promotes"
# (d) stamped but INCOMPLETE (no line for JOURNEY-102) → refused
{ printf 'reviewed_sha256: %s\n' "$(_sha256 "$GMAP")"
  grep -v "JOURNEY-102" "$RAW_CLEAN"; } > "$_FB/incomplete.md"
_fberr=$(sh "$PROMOTE" "$PRD" "$APP" "$GMAP" "$GMAN" "$GGAP" "$_FB/incomplete.md" "$_FB/m2.md" --approve 2>&1 >/dev/null); _fbec=$?
if [ "$_fbec" -ne 0 ]; then printf 'ok: promote: fidelity with an unreviewed journey refused\n'; else
  printf 'FAIL: promote: fidelity silent on JOURNEY-102 accepted\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
assert_contains "$_fberr" "FIDELITY_INCOMPLETE" "promote: refusal names FIDELITY_INCOMPLETE"
rm -rf "$_FB"
