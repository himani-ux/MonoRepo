# shellcheck shell=sh
# surface-staleness_test.sh — check-surface-staleness.sh proofs (spec G2):
# promote-time provenance anchor (surface-promote.sh) + the standalone
# staleness re-check gate. Model: surface-promote_test.sh (fixture-copy
# idiom) + uat-evidence_test.sh (TOOL_MISSING PATH-shim idiom).

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
CSS="$TESTS_DIR/../bin/check-surface-staleness.sh"
SP="$TESTS_DIR/../bin/surface-promote.sh"
GENDIR="$TESTS_DIR/fixtures/gen"
SFX="$TESTS_DIR/fixtures/surface"

_sst_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

_sst_sha256() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else return 1; fi
}

_sst_t=$(mktemp -d)
cp "$GENDIR/APP_FLOW.md" "$_sst_t/APP_FLOW.md"
cp "$SFX/TEST_SURFACE.golden.md" "$_sst_t/TEST_SURFACE.md"

# ── sst-1: wrong arg count → exit 2 ────────────────────────────────────────
sh "$CSS" only-one-arg >/dev/null 2>&1
assert_eq 2 $? "sst-1a: 1 arg → exit 2"
sh "$CSS" a b c >/dev/null 2>&1
assert_eq 2 $? "sst-1b: 3 args → exit 2"

# ── sst-2: missing surface file → exit 2 ───────────────────────────────────
sh "$CSS" "$_sst_t/NOPE_SURFACE.md" "$_sst_t/APP_FLOW.md" >/dev/null 2>&1
assert_eq 2 $? "sst-2: missing TEST_SURFACE → exit 2"

# ── sst-3: missing app_flow file → exit 2 ──────────────────────────────────
sh "$CSS" "$_sst_t/TEST_SURFACE.md" "$_sst_t/NOPE_FLOW.md" >/dev/null 2>&1
assert_eq 2 $? "sst-3: missing APP_FLOW → exit 2"

# ── sst-4: no provenance sibling → PROVENANCE_MISSING (the .current.md ────
#    killer: an unanchored surface NEVER passes) ───────────────────────────
_o=$(sh "$CSS" "$_sst_t/TEST_SURFACE.md" "$_sst_t/APP_FLOW.md" 2>&1); _ec=$?
_sst_nonzero "$_ec" "sst-4: no provenance sibling fails"
assert_contains "$_o" "PROVENANCE_MISSING" "sst-4: names PROVENANCE_MISSING"

# ── sst-5: malformed provenance (garbage first line) → PROVENANCE_FORMAT ──
printf 'not a hash at all\n' > "$_sst_t/TEST_SURFACE.md.provenance"
_o=$(sh "$CSS" "$_sst_t/TEST_SURFACE.md" "$_sst_t/APP_FLOW.md" 2>&1); _ec=$?
_sst_nonzero "$_ec" "sst-5: malformed provenance fails"
assert_contains "$_o" "PROVENANCE_FORMAT" "sst-5: names PROVENANCE_FORMAT"

# ── sst-6: correct-format but WRONG hash → SURFACE_STALE ──────────────────
_sst_zeros=$(printf '%064d' 0)
printf 'app_flow_sha256: %s\n' "$_sst_zeros" > "$_sst_t/TEST_SURFACE.md.provenance"
_o=$(sh "$CSS" "$_sst_t/TEST_SURFACE.md" "$_sst_t/APP_FLOW.md" 2>&1); _ec=$?
_sst_nonzero "$_ec" "sst-6: wrong-hash provenance fails"
assert_contains "$_o" "SURFACE_STALE" "sst-6: names SURFACE_STALE"

# ── sst-7: full loop — surface-promote.sh --approve stamps the sibling, ───
#    then check-surface-staleness.sh passes against it ────────────────────
rm -f "$_sst_t/TEST_SURFACE.md.provenance"
_sst_target="$_sst_t/promoted/TEST_SURFACE.md"
mkdir -p "$_sst_t/promoted"
sh "$SP" "$_sst_t/APP_FLOW.md" "$SFX/TEST_SURFACE.golden.md" "$_sst_target" --approve >/dev/null 2>&1
assert_eq 0 $? "sst-7a: promote --approve succeeds on the golden pair"
[ -f "$_sst_target.provenance" ]
assert_eq 0 $? "sst-7b: sibling .provenance file exists after promote"
_sst_expect_sha=$(_sst_sha256 "$_sst_t/APP_FLOW.md")
_sst_expect_line="app_flow_sha256: $_sst_expect_sha"
_sst_actual_line=$(cat "$_sst_target.provenance")
assert_eq "$_sst_expect_line" "$_sst_actual_line" "sst-7c: provenance content is exactly app_flow_sha256: <recomputed sha256>"
_o=$(sh "$CSS" "$_sst_target" "$_sst_t/APP_FLOW.md" 2>&1); _ec=$?
assert_eq 0 "$_ec" "sst-7d: freshly promoted surface passes the staleness gate"

# ── sst-8: modify the APP_FLOW copy (append a line), re-run → SURFACE_STALE
printf '\n<!-- drift injected after promote -->\n' >> "$_sst_t/APP_FLOW.md"
_o=$(sh "$CSS" "$_sst_target" "$_sst_t/APP_FLOW.md" 2>&1); _ec=$?
_sst_nonzero "$_ec" "sst-8: modified APP_FLOW after promote fails"
assert_contains "$_o" "SURFACE_STALE" "sst-8: names SURFACE_STALE"

# ── sst-9: uppercase-hex provenance → PROVENANCE_FORMAT (anchor grammar is
#    lowercase-only) ────────────────────────────────────────────────────────
_sst_i=0; _sst_upper=""
while [ "$_sst_i" -lt 64 ]; do _sst_upper="${_sst_upper}A"; _sst_i=$((_sst_i + 1)); done
printf 'app_flow_sha256: %s\n' "$_sst_upper" > "$_sst_t/TEST_SURFACE.md.provenance"
_o=$(sh "$CSS" "$_sst_t/TEST_SURFACE.md" "$_sst_t/APP_FLOW.md" 2>&1); _ec=$?
_sst_nonzero "$_ec" "sst-9: uppercase-hex provenance fails"
assert_contains "$_o" "PROVENANCE_FORMAT" "sst-9: names PROVENANCE_FORMAT (lowercase-only grammar)"

# ── sst-10: TOOL_MISSING — PATH-shimmed with every non-sha binary the ─────
#    gate/promote chain needs, deliberately omitting sha256sum/shasum
#    (same idiom as journey/tests/uat-evidence_test.sh). The gate must fail
#    closed, and promote under the same shim must fail loud WITHOUT writing
#    a provenance file (or the surface itself — nothing written at all).
_sst_shim="$_sst_t/shim"; mkdir -p "$_sst_shim"
for _b in cat grep head cut awk sed dirname basename mktemp mv rm sh sort uniq wc tr date; do
  _real="$(command -v "$_b")" && ln -s "$_real" "$_sst_shim/$_b"
done

# well-formed (correct-format) provenance so ONLY the sha-tool absence can
# be the failure reason — proves TOOL_MISSING fires before/instead of a
# spurious SURFACE_STALE
printf 'app_flow_sha256: %s\n' "$_sst_zeros" > "$_sst_t/TEST_SURFACE.md.provenance"
_o=$(PATH="$_sst_shim" /bin/sh "$CSS" "$_sst_t/TEST_SURFACE.md" "$_sst_t/APP_FLOW.md" 2>&1); _ec=$?
_sst_nonzero "$_ec" "sst-10a: gate under sha-tool-stripped PATH fails"
assert_contains "$_o" "TOOL_MISSING" "sst-10a: names TOOL_MISSING"

_sst_shimtarget="$_sst_t/shimpromoted/TEST_SURFACE.md"
mkdir -p "$_sst_t/shimpromoted"
_o=$(PATH="$_sst_shim" /bin/sh "$SP" "$_sst_t/APP_FLOW.md" "$SFX/TEST_SURFACE.golden.md" "$_sst_shimtarget" --approve 2>&1); _ec=$?
_sst_nonzero "$_ec" "sst-10b: promote under sha-tool-stripped PATH fails loud"
assert_contains "$_o" "TOOL_MISSING" "sst-10b: names TOOL_MISSING"
[ ! -f "$_sst_shimtarget.provenance" ]
assert_eq 0 $? "sst-10c: no provenance file written when the sha tool is missing"
[ ! -f "$_sst_shimtarget" ]
assert_eq 0 $? "sst-10d: no surface file written either — promotion must not succeed without stamping"

rm -rf "$_sst_t"
