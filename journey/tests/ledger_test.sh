# shellcheck shell=sh
# ledger_test.sh — TDD proofs for the Task-3 runtime ledger layer (brief §H).
# All 12 proofs. Run via: sh journey/tests/ledger_test.sh
# Also executed by journey/tests/run.sh (sourced, not subshell).
#
# P2 fix (M-T1-4 class, root-caused by V-T6): every mktemp template below
# now has its Xs TERMINAL. A template whose X run is followed by a literal
# suffix (e.g. the old `/tmp/ledger-stamp-XXXXXXXX.json`) is NOT randomized
# by BSD mktemp (macOS) — it mkstemp()s the literal filename verbatim. The
# first run of this file on a clean host "worked" by accident (nothing
# occupied that literal path yet); the created file then survived past this
# script's own EXIT trap whenever the process was killed before the trap
# ran (e.g. an agent timeout), and every subsequent run collided on that
# leftover literal file with `mkstemp failed ... File exists` — a
# self-perpetuating flake. Reproduced by hand: create the literal file
# `/tmp/ledger-stamp-XXXXXXXX.json` by hand, then run this script — proof-12a
# fails (`stamp GREEN with valid fields → exit 0` / `stamped ledger
# validates`) because the guarded mktemp below now reports the collision
# instead of silently handing an empty path to the stamper.
#
# Every mktemp call is also now fail-closed: on mktemp failure, a dedicated
# `FAIL: ...` line is emitted, ASSERT_FAILS is incremented, and the
# dependent proof body is skipped — never given an empty path to silently
# mis-exercise (an unguarded `_ledger12a=$(mktemp ...)` on failure keeps
# `_ledger12a` empty; `rm -f ""` no-ops and `JOURNEY_STATUS_FILE=""` hands
# the stamper a blank path, so the proof's PASS/FAIL becomes an accident of
# what an empty-path run happens to do, not a test of stamper behavior).
# This mirrors the file's own established skip-fail idiom (proof-26's
# `mktemp -d ... || _p26_root=""` + `if [ -n "$_p26_root" ]; then ... else
# FAIL; fi`), and the same MKTEMP_FAILED-class guard `check-uat-evidence.sh`
# / `check-uat-verification.sh` use for their own scratch-file mktemp
# (M-T1-4).

. "$(dirname "$0")/assert.sh"
. "$(dirname "$0")/../lib/journey-ledger.sh"

HERE="$(cd "$(dirname "$0")" && pwd)"
FIXTURES="$HERE/fixtures/ledger"
FETCH="$HERE/../lib/journey-ledger-fetch.sh"
STAMP="$HERE/../bin/journey-status-stamp.sh"

# ── local helper: assert exit code is non-zero ────────────────────────────────
assert_nonzero() { # ACTUAL_CODE MSG
  if [ "$1" -ne 0 ]; then
    printf 'ok: %s\n' "$2"
  else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1))
  fi
}

# ── cleanup registry ─────────────────────────────────────────────────────────
_L3_TMPFILES=""
_l3_register_tmp() { _L3_TMPFILES="$_L3_TMPFILES $1"; }
trap 'rm -f $_L3_TMPFILES' EXIT INT TERM

# Helper: write a temp conf file from KEY=value arguments (one per arg).
# LABEL is the calling proof's name, used only in the fail-closed message.
# Fails closed (P2/M-T1-4): mktemp failure emits a FAIL line, increments
# ASSERT_FAILS, and returns 1 with no stdout — callers gate the rest of
# their proof on a non-empty result (see `if [ -n "$_confN" ]` below), the
# same skip-fail idiom proof-26 already uses in this file.
#
# NOTE: registration is deliberately NOT done here. Every call site is
# `_confN=$(_mk_conf ...)` — a command substitution, which runs in a
# SUBSHELL. A `_l3_register_tmp` call made from inside this function would
# mutate that subshell's own copy of $_L3_TMPFILES, discarded the instant
# the substitution completes; the parent shell's registry — and therefore
# the EXIT trap — would never see it (confirmed empirically: this was the
# PRE-EXISTING behavior here, root cause of the large stray
# /tmp/ledger-conf-* pile found while diagnosing P2). Each call site
# registers its own result instead, in the parent shell, right after the
# substitution returns.
_mk_conf() { # LABEL KEY=val...
  _mkc_label="$1"; shift
  _c=$(mktemp /tmp/ledger-conf-XXXXXXXX) || {
    printf 'FAIL: %s: mktemp failed for conf file (fail-closed)\n' "$_mkc_label"
    ASSERT_FAILS=$((ASSERT_FAILS + 1))
    return 1
  }
  for _line in "$@"; do
    printf '%s\n' "$_line"
  done > "$_c"
  printf '%s\n' "$_c"
}

# ── Proof 1: green.json via test-fixture conf → exit 0, stdout has GREEN ─────
_conf1=$(_mk_conf proof-1 \
  "LEDGER_SOURCE=test-fixture" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "ALLOW_TEST_FIXTURE=1" \
  "LEDGER_PATH=$FIXTURES/green.json")
if [ -n "$_conf1" ]; then
  _l3_register_tmp "$_conf1"
  _out1=$(sh "$FETCH" "$_conf1" 2>/dev/null)
  _ec1=$?
  assert_eq "0" "$_ec1" "proof-1: green.json fetch exits 0"
  assert_contains "$_out1" "JOURNEY-001" "proof-1: stdout contains JOURNEY-001"
  assert_contains "$_out1" "GREEN" "proof-1: stdout contains GREEN"
fi

# ── Proof 2: red.json and flaky.json validate exit 0 ─────────────────────────
journey_ledger_validate "$FIXTURES/red.json" 2>/dev/null
assert_eq "0" "$?" "proof-2: red.json validates exit 0"

journey_ledger_validate "$FIXTURES/flaky.json" 2>/dev/null
assert_eq "0" "$?" "proof-2: flaky.json validates exit 0"

# ── Proof 3: malformed ledger → exit non-zero, no stdout ─────────────────────
_conf3=$(_mk_conf proof-3 \
  "LEDGER_SOURCE=test-fixture" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "ALLOW_TEST_FIXTURE=1" \
  "LEDGER_PATH=$FIXTURES/malformed.json")
if [ -n "$_conf3" ]; then
  _l3_register_tmp "$_conf3"
  _out3=$(sh "$FETCH" "$_conf3" 2>/dev/null)
  _ec3=$?
  assert_eq "" "$_out3" "proof-3: malformed → no stdout"
  assert_nonzero "$_ec3" "proof-3: malformed → exit non-zero"
fi

# ── Proof 4: missing file → fail closed ───────────────────────────────────────
_conf4=$(_mk_conf proof-4 \
  "LEDGER_SOURCE=test-fixture" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "ALLOW_TEST_FIXTURE=1" \
  "LEDGER_PATH=$FIXTURES/nonexistent-file.json")
if [ -n "$_conf4" ]; then
  _l3_register_tmp "$_conf4"
  _out4=$(sh "$FETCH" "$_conf4" 2>/dev/null)
  _ec4=$?
  assert_eq "" "$_out4" "proof-4: missing file → no stdout"
  assert_nonzero "$_ec4" "proof-4: missing file → exit non-zero"
fi

# ── Proof 5: untrusted source → fail closed ───────────────────────────────────
_conf5=$(_mk_conf proof-5 \
  "LEDGER_SOURCE=test-fixture" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "ALLOW_TEST_FIXTURE=1" \
  "LEDGER_PATH=$FIXTURES/untrusted-source.json")
if [ -n "$_conf5" ]; then
  _l3_register_tmp "$_conf5"
  _out5=$(sh "$FETCH" "$_conf5" 2>/dev/null)
  _ec5=$?
  assert_eq "" "$_out5" "proof-5: untrusted-source → no stdout"
  assert_nonzero "$_ec5" "proof-5: untrusted-source → exit non-zero"
fi

# ── Proof 6: GREEN without ci_run_id → fail closed ───────────────────────────
_conf6=$(_mk_conf proof-6 \
  "LEDGER_SOURCE=test-fixture" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "ALLOW_TEST_FIXTURE=1" \
  "LEDGER_PATH=$FIXTURES/green-missing-runid.json")
if [ -n "$_conf6" ]; then
  _l3_register_tmp "$_conf6"
  _out6=$(sh "$FETCH" "$_conf6" 2>/dev/null)
  _ec6=$?
  assert_eq "" "$_out6" "proof-6: GREEN-missing-runid → no stdout"
  assert_nonzero "$_ec6" "proof-6: GREEN-missing-runid → exit non-zero"
fi

# ── Proof 7: GREEN without ci_artifact → fail closed ─────────────────────────
_conf7=$(_mk_conf proof-7 \
  "LEDGER_SOURCE=test-fixture" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "ALLOW_TEST_FIXTURE=1" \
  "LEDGER_PATH=$FIXTURES/green-missing-artifact.json")
if [ -n "$_conf7" ]; then
  _l3_register_tmp "$_conf7"
  _out7=$(sh "$FETCH" "$_conf7" 2>/dev/null)
  _ec7=$?
  assert_eq "" "$_out7" "proof-7: GREEN-missing-artifact → no stdout"
  assert_nonzero "$_ec7" "proof-7: GREEN-missing-artifact → exit non-zero"
fi

# ── Proof 8: RED without failure_summary → fail closed ───────────────────────
_conf8=$(_mk_conf proof-8 \
  "LEDGER_SOURCE=test-fixture" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "ALLOW_TEST_FIXTURE=1" \
  "LEDGER_PATH=$FIXTURES/red-missing-summary.json")
if [ -n "$_conf8" ]; then
  _l3_register_tmp "$_conf8"
  _out8=$(sh "$FETCH" "$_conf8" 2>/dev/null)
  _ec8=$?
  assert_eq "" "$_out8" "proof-8: RED-missing-summary → no stdout"
  assert_nonzero "$_ec8" "proof-8: RED-missing-summary → exit non-zero"
fi

# ── Proof 9: missing id → NOT_RUN (never synthesizes GREEN) ───────────────────
_json9=$(cat "$FIXTURES/green.json")
_status9=$(journey_ledger_status "$_json9" "JOURNEY-999")
assert_eq "NOT_RUN" "$_status9" "proof-9: absent JOURNEY-999 → NOT_RUN"

# ── Proof 10: template + good fixture contain no runtime-truth keys ───────────
# grep exits 0 if found (bad), 1 if not found (good)
grep -qE '^(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):' \
  "$HERE/../JOURNEY_MAP.template.md" 2>/dev/null
assert_eq "1" "$?" "proof-10: JOURNEY_MAP.template.md has no runtime keys"

grep -qE '^(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):' \
  "$HERE/fixtures/good/JOURNEY_MAP.md" 2>/dev/null
assert_eq "1" "$?" "proof-10: fixtures/good/JOURNEY_MAP.md has no runtime keys"

# ── Proof 11a: test-fixture without ALLOW_TEST_FIXTURE=1 → fail closed ───────
_conf11a=$(_mk_conf proof-11a \
  "LEDGER_SOURCE=test-fixture" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "LEDGER_PATH=$FIXTURES/green.json")
# NOTE: ALLOW_TEST_FIXTURE intentionally absent
if [ -n "$_conf11a" ]; then
  _l3_register_tmp "$_conf11a"
  _out11a=$(sh "$FETCH" "$_conf11a" 2>/dev/null)
  _ec11a=$?
  assert_eq "" "$_out11a" "proof-11a: no ALLOW_TEST_FIXTURE → no stdout"
  assert_nonzero "$_ec11a" "proof-11a: no ALLOW_TEST_FIXTURE → exit non-zero"
fi

# ── Proof 11b: test-fixture without EXPECTED_SOURCE → fail closed ─────────────
_conf11b=$(_mk_conf proof-11b \
  "LEDGER_SOURCE=test-fixture" \
  "ALLOW_TEST_FIXTURE=1" \
  "LEDGER_PATH=$FIXTURES/green.json")
# NOTE: EXPECTED_SOURCE intentionally absent
if [ -n "$_conf11b" ]; then
  _l3_register_tmp "$_conf11b"
  _out11b=$(sh "$FETCH" "$_conf11b" 2>/dev/null)
  _ec11b=$?
  assert_eq "" "$_out11b" "proof-11b: no EXPECTED_SOURCE → no stdout"
  assert_nonzero "$_ec11b" "proof-11b: no EXPECTED_SOURCE → exit non-zero"
fi

# ── Proof 12a: stamp GREEN with --run-id + --artifact → validates ─────────────
# Template: Xs TERMINAL (P2 fix) — was /tmp/ledger-stamp-XXXXXXXX.json, whose
# Xs were NOT the last characters of the template; BSD mktemp does not
# randomize a non-terminal X run, so it mkstemp()'d that literal filename
# every time. Guarded fail-closed (P2/M-T1-4): a mktemp failure (including a
# collision with debris left by an interrupted prior run) now fails this
# proof loudly instead of handing the stamper an empty path.
_ledger12a=$(mktemp /tmp/ledger-stamp-json-XXXXXXXX) || _ledger12a=""
if [ -n "$_ledger12a" ]; then
  _l3_register_tmp "$_ledger12a"
  rm -f "$_ledger12a"  # Let stamper create it from scratch

  JOURNEY_STATUS_FILE="$_ledger12a" \
  JOURNEY_LEDGER_SOURCE="test-fixture://ci" \
    sh "$STAMP" JOURNEY-001 GREEN --run-id "gha-001" --artifact "artifacts/j001.zip" \
    >/dev/null 2>/dev/null
  _ec12a=$?
  assert_eq "0" "$_ec12a" "proof-12a: stamp GREEN with valid fields → exit 0"

  journey_ledger_validate "$_ledger12a" 2>/dev/null
  assert_eq "0" "$?" "proof-12a: stamped ledger validates"
else
  printf 'FAIL: proof-12a: mktemp failed (fail-closed)\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi

# ── Proof 12b: stamp GREEN without --run-id → exit non-zero, no valid record ──
_ledger12b=$(mktemp /tmp/ledger-stamp2-json-XXXXXXXX) || _ledger12b=""
if [ -n "$_ledger12b" ]; then
  _l3_register_tmp "$_ledger12b"
  rm -f "$_ledger12b"  # Ensure we start fresh

  JOURNEY_STATUS_FILE="$_ledger12b" \
  JOURNEY_LEDGER_SOURCE="test-fixture://ci" \
    sh "$STAMP" JOURNEY-001 GREEN --artifact "artifacts/j001.zip" \
    >/dev/null 2>/dev/null
  _ec12b=$?
  assert_nonzero "$_ec12b" "proof-12b: stamp GREEN without --run-id → exit non-zero"

  # If the stamper wrote anything (bug), it must not validate as valid GREEN
  if [ -f "$_ledger12b" ]; then
    journey_ledger_validate "$_ledger12b" 2>/dev/null
    _ec12b_v=$?
    assert_nonzero "$_ec12b_v" "proof-12b: file written on bad stamp must not validate"
  fi
else
  printf 'FAIL: proof-12b: mktemp failed (fail-closed)\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi

# ── Proof 29: P4 regression — stamp survives leftover debris from the OLD
# non-terminal-X template (M-T1-4/BSD-mktemp class, same as P2 but in the
# PRODUCTION stamper itself: journey-status-stamp.sh:141). Before the P4
# fix, `mktemp "$dir/.journey-stamp-XXXXXXXX.json"` was NOT randomized by
# BSD mktemp (Xs not terminal) — it mkstemp()'d that literal filename every
# time. A leftover file at that literal path (left behind by a killed CI
# job, or created by a still-running concurrent stamp before its own
# rename) made every subsequent stamp in the same ledger dir fail closed
# with `mkstemp failed ... File exists`, even though nothing was actually
# wrong with the ledger itself. Reproduced by hand pre-fix (see the fix-wave
# report): planting `$dir/.journey-stamp-XXXXXXXX.json` then calling the
# unfixed stamper reproduced exactly this failure (rc=1). Post-fix the Xs
# are terminal, so the stamper's own mktemp call never collides with that
# literal legacy name — this proof plants the debris and asserts the stamp
# still succeeds.
_p29_dir=$(mktemp -d /tmp/ledger-p29-XXXXXXXX) || _p29_dir=""
if [ -n "$_p29_dir" ]; then
  : > "$_p29_dir/.journey-stamp-XXXXXXXX.json"
  JOURNEY_STATUS_FILE="$_p29_dir/status.json" \
  JOURNEY_LEDGER_SOURCE="test-fixture://ci" \
    sh "$STAMP" JOURNEY-P29 GREEN --run-id "gha-p29" --artifact "artifacts/p29.zip" \
    >/dev/null 2>/dev/null
  _ec29=$?
  assert_eq "0" "$_ec29" "proof-29: stamp succeeds despite legacy-template leftover debris (P4 regression)"
  if [ -f "$_p29_dir/status.json" ]; then
    _status29=$(journey_ledger_status "$(cat "$_p29_dir/status.json")" "JOURNEY-P29")
    assert_eq "GREEN" "$_status29" "proof-29: stamped record actually reflects the new stamp, not stale debris"
  else
    printf 'FAIL: proof-29: no status.json written\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1))
  fi
  rm -rf "$_p29_dir"
else
  printf 'FAIL: proof-29: mktemp -d failed\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi

# ── Proof 13: staleness check — fresh ledger passes ──────────────────────────
_now_ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
_fresh13=$(mktemp /tmp/ledger-fresh-json-XXXXXXXX) || _fresh13=""
if [ -n "$_fresh13" ]; then
  _l3_register_tmp "$_fresh13"
  jq --arg ts "$_now_ts" \
    '. | .generated_at = $ts | .journeys["JOURNEY-001"].last_run = $ts' \
    "$FIXTURES/green.json" > "$_fresh13"
  _conf13=$(_mk_conf proof-13 \
    "LEDGER_SOURCE=test-fixture" \
    "EXPECTED_SOURCE=test-fixture://trusted" \
    "ALLOW_TEST_FIXTURE=1" \
    "LEDGER_MAX_AGE_SECONDS=86400" \
    "LEDGER_PATH=$_fresh13")
  if [ -n "$_conf13" ]; then
    _l3_register_tmp "$_conf13"
    _out13=$(sh "$FETCH" "$_conf13" 2>/dev/null)
    _ec13=$?
    assert_eq "0" "$_ec13" "proof-13: fresh ledger staleness check → exit 0"
    assert_contains "$_out13" "GREEN" "proof-13: stdout has GREEN"
  fi
else
  printf 'FAIL: proof-13: mktemp failed (fail-closed)\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi

# ── Proof 14: staleness check — stale ledger fails closed ─────────────────────
_conf14=$(_mk_conf proof-14 \
  "LEDGER_SOURCE=test-fixture" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "ALLOW_TEST_FIXTURE=1" \
  "LEDGER_MAX_AGE_SECONDS=86400" \
  "LEDGER_PATH=$FIXTURES/stale.json")
if [ -n "$_conf14" ]; then
  _l3_register_tmp "$_conf14"
  _out14=$(sh "$FETCH" "$_conf14" 2>/dev/null)
  _ec14=$?
  assert_eq "" "$_out14" "proof-14: stale ledger → no stdout"
  assert_nonzero "$_ec14" "proof-14: stale ledger → exit non-zero"
fi

# ── Proof 15: non-numeric LEDGER_MAX_AGE_SECONDS fails closed ─────────────────
_conf15=$(_mk_conf proof-15 \
  "LEDGER_SOURCE=test-fixture" \
  "EXPECTED_SOURCE=test-fixture://trusted" \
  "ALLOW_TEST_FIXTURE=1" \
  "LEDGER_MAX_AGE_SECONDS=abc" \
  "LEDGER_PATH=$FIXTURES/green.json")
if [ -n "$_conf15" ]; then
  _l3_register_tmp "$_conf15"
  _out15=$(sh "$FETCH" "$_conf15" 2>/dev/null)
  _ec15=$?
  assert_eq "" "$_out15" "proof-15: non-numeric max-age → no stdout"
  assert_nonzero "$_ec15" "proof-15: non-numeric max-age → exit non-zero"
fi

# ── Proof 16: inline-comment conf parses to clean values ──────────────────────
_conf16=$(_mk_conf proof-16 \
  "LEDGER_SOURCE=test-fixture   # test mode" \
  "EXPECTED_SOURCE=test-fixture://trusted   # trusted source" \
  "ALLOW_TEST_FIXTURE=1   # required for test-fixture" \
  "LEDGER_PATH=$FIXTURES/green.json   # the good fixture")
if [ -n "$_conf16" ]; then
  _l3_register_tmp "$_conf16"
  _out16=$(sh "$FETCH" "$_conf16" 2>/dev/null)
  _ec16=$?
  assert_eq "0" "$_ec16" "proof-16: inline-comment conf → exit 0"
  assert_contains "$_out16" "GREEN" "proof-16: inline-comment conf → stdout has GREEN"
fi

# ── Proof 17: unknown / unset LEDGER_SOURCE fails closed ──────────────────────
_conf17a=$(_mk_conf proof-17a \
  "LEDGER_SOURCE=bogus" \
  "EXPECTED_SOURCE=test-fixture://trusted")
if [ -n "$_conf17a" ]; then
  _l3_register_tmp "$_conf17a"
  _out17a=$(sh "$FETCH" "$_conf17a" 2>/dev/null)
  _ec17a=$?
  assert_eq "" "$_out17a" "proof-17a: unknown LEDGER_SOURCE → no stdout"
  assert_nonzero "$_ec17a" "proof-17a: unknown LEDGER_SOURCE → exit non-zero"
fi

_conf17b=$(_mk_conf proof-17b \
  "EXPECTED_SOURCE=test-fixture://trusted")
if [ -n "$_conf17b" ]; then
  _l3_register_tmp "$_conf17b"
  _out17b=$(sh "$FETCH" "$_conf17b" 2>/dev/null)
  _ec17b=$?
  assert_eq "" "$_out17b" "proof-17b: unset LEDGER_SOURCE → no stdout"
  assert_nonzero "$_ec17b" "proof-17b: unset LEDGER_SOURCE → exit non-zero"
fi

# ── Proof 18: TZ-pinned staleness boundary — regression-locks Fix-1 UTC parse ──
# Fix-1 changed BSD date parse from local-time to TZ=UTC.  On a non-UTC host
# (e.g. America/New_York, UTC-4/-5) the pre-fix path read a UTC timestamp in
# local time → it appeared ~4-5h fresher than reality → a 2h-old ledger with
# max-age 1h would pass (fail-open).  This proof discriminates on BSD-date hosts
# (macOS); on GNU-date hosts "date -d" already honors the trailing Z (UTC).
_now18=$(date +%s)
_gen18=$((_now18 - 7200))
_ts18=$(date -u -r "$_gen18" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
     || date -u -d "@$_gen18" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null)
_stale18=$(mktemp /tmp/ledger-tz-stale-json-XXXXXXXX) || _stale18=""
if [ -n "$_stale18" ]; then
  _l3_register_tmp "$_stale18"
  jq --arg ts "$_ts18" '. | .generated_at = $ts' \
    "$FIXTURES/green.json" > "$_stale18"
  _conf18=$(_mk_conf proof-18 \
    "LEDGER_SOURCE=test-fixture" \
    "ALLOW_TEST_FIXTURE=1" \
    "EXPECTED_SOURCE=test-fixture://trusted" \
    "LEDGER_MAX_AGE_SECONDS=3600" \
    "LEDGER_PATH=$_stale18")
  if [ -n "$_conf18" ]; then
    _l3_register_tmp "$_conf18"
    _out18=$(TZ=America/New_York sh "$FETCH" "$_conf18" 2>/dev/null); _ec18=$?
    assert_eq "" "$_out18" "proof-18: TZ-pinned 2h-old ledger (max-age 1h) rejected as stale"
    assert_nonzero "$_ec18" "proof-18: TZ-pinned boundary → exit non-zero (locks in Fix-1 UTC parse)"
  fi
else
  printf 'FAIL: proof-18: mktemp failed (fail-closed)\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi

# ── Proof 25: FUTURE generated_at fails closed (MIN-2) ────────────────────────
# A ledger timestamped in the future must NOT be treated as fresh (negative age
# must not slip past the staleness check).
_now25=$(date +%s)
_gen25=$((_now25 + 100000))
_ts25=$(date -u -r "$_gen25" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null \
     || date -u -d "@$_gen25" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null)
_future25=$(mktemp /tmp/ledger-future-json-XXXXXXXX) || _future25=""
if [ -n "$_future25" ]; then
  _l3_register_tmp "$_future25"
  jq --arg ts "$_ts25" '.generated_at = $ts' "$FIXTURES/green.json" > "$_future25"
  _conf25=$(_mk_conf proof-25 \
    "LEDGER_SOURCE=test-fixture" \
    "ALLOW_TEST_FIXTURE=1" \
    "EXPECTED_SOURCE=test-fixture://trusted" \
    "LEDGER_MAX_AGE_SECONDS=3600" \
    "LEDGER_PATH=$_future25")
  if [ -n "$_conf25" ]; then
    _l3_register_tmp "$_conf25"
    _out25=$(sh "$FETCH" "$_conf25" 2>/dev/null); _ec25=$?
    assert_eq "" "$_out25" "proof-25: future-dated ledger → no stdout (fail closed)"
    assert_nonzero "$_ec25" "proof-25: future generated_at rejected (not treated as fresh)"
  fi
else
  printf 'FAIL: proof-25: mktemp failed (fail-closed)\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi

# ── Proofs 19-24: ledger JSON type-strictness (final-review Minor) ────────────
# Build a temp ledger from a base fixture with one field's TYPE changed, then
# validate it directly. Runtime evidence fields must be strings when present, and
# schema_version must be the NUMBER 1 (not the string "1").
#
# LABEL is the calling proof's name, used only in the fail-closed message.
# Fails closed (P2/M-T1-4) the same way _mk_conf does: on mktemp failure, a
# dedicated FAIL line is emitted and ASSERT_FAILS incremented; callers gate
# the rest of their proof on a non-empty result. Before this fix, the shared
# non-terminal-X template meant only the FIRST of proofs 19-23 in a run could
# ever mktemp successfully — every subsequent call collided on that same
# still-live literal file and silently returned empty, and because proofs
# 19-23 all assert_nonzero (rejection expected), `journey_ledger_validate ""`
# (a nonexistent path) coincidentally ALSO returns non-zero — the proof
# "passed" without ever exercising the intended type-mutated fixture. The
# per-call guard below closes that vacuous-pass hole too: a real mktemp
# failure is now reported by name instead of masquerading as a real result.
#
# NOTE: same subshell caveat as _mk_conf above — registration happens at
# each call site, not inside this function, because every call site is a
# command substitution and this function's own $_L3_TMPFILES mutation
# would be discarded when that subshell exits.
_mk_ledger() { # LABEL BASE_FIXTURE JQ_FILTER
  _mkl_label="$1"; _mkl_base="$2"; _mkl_filter="$3"
  _ml=$(mktemp /tmp/ledger-typed-json-XXXXXXXX) || {
    printf 'FAIL: %s: mktemp failed for typed ledger (fail-closed)\n' "$_mkl_label"
    ASSERT_FAILS=$((ASSERT_FAILS + 1))
    return 1
  }
  jq "$_mkl_filter" "$FIXTURES/$_mkl_base" > "$_ml"
  printf '%s\n' "$_ml"
}

_l=$(_mk_ledger proof-19 green.json '.journeys["JOURNEY-001"].ci_run_id = 123')
if [ -n "$_l" ]; then
  _l3_register_tmp "$_l"
  journey_ledger_validate "$_l" >/dev/null 2>&1; assert_nonzero $? "proof-19: numeric ci_run_id rejected (must be a string)"
fi

_l=$(_mk_ledger proof-20 green.json '.journeys["JOURNEY-001"].ci_artifact = true')
if [ -n "$_l" ]; then
  _l3_register_tmp "$_l"
  journey_ledger_validate "$_l" >/dev/null 2>&1; assert_nonzero $? "proof-20: boolean ci_artifact rejected (must be a string)"
fi

_l=$(_mk_ledger proof-21 green.json '.journeys["JOURNEY-001"].last_run = 123')
if [ -n "$_l" ]; then
  _l3_register_tmp "$_l"
  journey_ledger_validate "$_l" >/dev/null 2>&1; assert_nonzero $? "proof-21: numeric last_run rejected (must be a string)"
fi

_l=$(_mk_ledger proof-22 red.json '.journeys["JOURNEY-001"].failure_summary = 123')
if [ -n "$_l" ]; then
  _l3_register_tmp "$_l"
  journey_ledger_validate "$_l" >/dev/null 2>&1; assert_nonzero $? "proof-22: numeric failure_summary rejected (must be a string)"
fi

_l=$(_mk_ledger proof-23 green.json '.schema_version = "1"')
if [ -n "$_l" ]; then
  _l3_register_tmp "$_l"
  journey_ledger_validate "$_l" >/dev/null 2>&1; assert_nonzero $? "proof-23: schema_version string \"1\" rejected (must be numeric 1)"
fi

journey_ledger_validate "$FIXTURES/green.json" >/dev/null 2>&1
assert_eq "0" "$?" "proof-24: valid green.json (correct types) still validates"

# ── Proof 26: git-branch mode — a same-named TAG must not shadow the branch ──
# Attack (post-merge review, CRITICAL): branch protection does NOT cover the
# tag namespace. With an unqualified `git fetch origin journey-status`, git's
# short-name resolution prefers refs/tags/ over refs/heads/, so an attacker
# who pushes a TAG named `journey-status` at forged-but-schema-valid content
# gets their ledger into FETCH_HEAD. The adapter must read the BRANCH.
_p26_root=$(mktemp -d /tmp/ledger-p26-XXXXXXXX) || _p26_root=""
if [ -n "$_p26_root" ]; then
  git init -q --bare "$_p26_root/origin.git"
  git init -q "$_p26_root/work"

  # Legit CI-owned ledger on the (protected) branch
  sed 's/gha-1284571/gha-legit-branch/' "$FIXTURES/green.json" \
    > "$_p26_root/work/JOURNEY_STATUS.json"
  git -C "$_p26_root/work" add JOURNEY_STATUS.json
  git -C "$_p26_root/work" -c user.email=t@t -c user.name=t \
    commit -qm "legit ledger"
  git -C "$_p26_root/work" push -q "$_p26_root/origin.git" \
    "HEAD:refs/heads/journey-status"

  # Forged ledger (schema-valid, same .source string) on a SAME-NAMED TAG
  sed 's/gha-1284571/gha-FORGED-tag/' "$FIXTURES/green.json" \
    > "$_p26_root/work/JOURNEY_STATUS.json"
  git -C "$_p26_root/work" add JOURNEY_STATUS.json
  git -C "$_p26_root/work" -c user.email=t@t -c user.name=t \
    commit -qm "forged ledger"
  git -C "$_p26_root/work" tag journey-status
  git -C "$_p26_root/work" push -q "$_p26_root/origin.git" \
    "refs/tags/journey-status"

  # Consumer repo whose origin carries BOTH refs
  git init -q "$_p26_root/consumer"
  git -C "$_p26_root/consumer" remote add origin "$_p26_root/origin.git"

  _conf26=$(_mk_conf proof-26 \
    "LEDGER_SOURCE=git-branch" \
    "LEDGER_REF=journey-status" \
    "LEDGER_PATH=JOURNEY_STATUS.json" \
    "LEDGER_MAX_AGE_SECONDS=315360000" \
    "EXPECTED_SOURCE=test-fixture://trusted")
  if [ -n "$_conf26" ]; then
    _l3_register_tmp "$_conf26"
    _out26=$(cd "$_p26_root/consumer" && sh "$FETCH" "$_conf26" 2>/dev/null)
    _ec26=$?
    assert_eq "0" "$_ec26" "proof-26: git-branch fetch of protected branch succeeds"
    assert_contains "$_out26" "gha-legit-branch" \
      "proof-26: adapter emits the BRANCH ledger (tag cannot shadow)"
    assert_not_contains "$_out26" "gha-FORGED-tag" \
      "proof-26: forged same-named tag content never emitted"
  fi

  # ── Proof 27: refs/tags/* is never a trust root, even when explicit ──────
  _conf27=$(_mk_conf proof-27 \
    "LEDGER_SOURCE=git-branch" \
    "LEDGER_REF=refs/tags/journey-status" \
    "LEDGER_PATH=JOURNEY_STATUS.json" \
    "LEDGER_MAX_AGE_SECONDS=315360000" \
    "EXPECTED_SOURCE=test-fixture://trusted")
  if [ -n "$_conf27" ]; then
    _l3_register_tmp "$_conf27"
    _out27=$(cd "$_p26_root/consumer" && sh "$FETCH" "$_conf27" 2>/dev/null)
    _ec27=$?
    assert_nonzero "$_ec27" "proof-27: explicit refs/tags/ LEDGER_REF rejected (fail closed)"
    assert_eq "" "$_out27" "proof-27: refs/tags/ ref emits nothing to stdout"
  fi

  # ── Proof 30: P4 regression — fetch (git-branch mode) survives leftover
  # debris from the OLD non-terminal-X template
  # (journey/lib/journey-ledger-fetch.sh:126, same M-T1-4/BSD-mktemp class
  # as P2, but in the PRODUCTION fetch adapter itself). Before the P4 fix,
  # `mktemp "${TMPDIR:-/tmp}/journey-ledger-XXXXXXXX.json"` was NOT
  # randomized by BSD mktemp (Xs not terminal) — it mkstemp()'d that
  # literal filename every time, so a concurrent/subsequent fetch (or
  # debris left by a killed job) collided with `mkstemp failed ... File
  # exists` on a totally healthy ledger. Post-fix the Xs are terminal, so
  # planting that legacy literal path first must not affect the fetch.
  : > "${TMPDIR:-/tmp}/journey-ledger-XXXXXXXX.json"
  _out30=$(cd "$_p26_root/consumer" && sh "$FETCH" "$_conf26" 2>/dev/null)
  _ec30=$?
  assert_eq "0" "$_ec30" "proof-30: git-branch fetch succeeds despite legacy-template leftover debris (P4 regression)"
  assert_contains "$_out30" "gha-legit-branch" "proof-30: fetch still emits the real branch ledger"
  rm -f "${TMPDIR:-/tmp}/journey-ledger-XXXXXXXX.json"

  rm -rf "$_p26_root"
else
  printf 'FAIL: proof-26 mktemp -d failed\n'; ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi

# ── Proof 28: production modes REQUIRE LEDGER_MAX_AGE_SECONDS (spec §4.5) ────
# Staleness enforcement was opt-in; an arbitrarily old but well-formed GREEN
# passed. In git-branch / ci-artifact modes a conf without the key now fails
# closed. (test-fixture mode keeps it optional — fixtures have frozen dates.)
_conf28=$(_mk_conf proof-28 \
  "LEDGER_SOURCE=ci-artifact" \
  "LEDGER_ARTIFACT=$FIXTURES/green.json" \
  "EXPECTED_SOURCE=test-fixture://trusted")
if [ -n "$_conf28" ]; then
  _l3_register_tmp "$_conf28"
  _out28=$(sh "$FETCH" "$_conf28" 2>/dev/null); _ec28=$?
  assert_nonzero "$_ec28" "proof-28: ci-artifact conf without LEDGER_MAX_AGE_SECONDS fails closed"
  _err28=$(sh "$FETCH" "$_conf28" 2>&1 >/dev/null)
  assert_contains "$_err28" "LEDGER_MAX_AGE_SECONDS" "proof-28: failure names the missing staleness key"
fi
