# check-extraction-coverage_test.sh — gate E3, the MANIFEST consumer chain
# (spec §4.3/§7.3/§8, §14 Q3). Fixture idiom: a static golden MANIFEST.md +
# a static golden JOURNEY_EXTRACTED.md carrying a PLACEHOLDER
# manifest_sha256, sed-stamped with the REAL sha256 of the manifest's
# machine block at test-setup time (mirrors check-extracted-provenance_test.sh's
# real-commit sed-stamping idiom) — every RED case is a one-thing-different
# sed mutation off that same golden pair, same style throughout this suite.
# shellcheck shell=sh
. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
GATE="$TESTS_DIR/../bin/check-extraction-coverage.sh"
FX="$TESTS_DIR/fixtures/extracted/coverage/good"
LINTFX="$TESTS_DIR/fixtures/extracted/lint"

_ecc_tmp="$(mktemp -d)"

_ecc_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

# ── the exact block-extraction + hashing recipe the gate itself uses
# (journey/bin/check-extraction-coverage.sh stage 1 / stage 3) — duplicated
# here deliberately (not sourced) so the test proves the gate's OWN
# documented recipe, not just "whatever the gate happens to compute".
_ecc_block() { # MANIFEST_PATH -> the EXTRACTION-MANIFEST BEGIN..END block, inclusive
  awk '
    /^EXTRACTION-MANIFEST BEGIN$/ { inblk = 1; print; next }
    /^EXTRACTION-MANIFEST END$/   { if (inblk) { print; found = 1 }; exit }
    inblk { print }
    END { if (!found) exit 3 }
  ' "$1"
}
if command -v sha256sum >/dev/null 2>&1; then _ECC_SHATOOL="sha256sum"
else _ECC_SHATOOL="shasum -a 256"; fi
_ecc_sha() { # MANIFEST_PATH -> sha256 of its machine block
  # shellcheck disable=SC2119
  _ecc_block "$1" | $_ECC_SHATOOL | awk '{print $1}'
}

# _ecc_stamp MANIFEST_PATH EXTRACTED_SRC -> writes a manifest_sha256-stamped
# copy of EXTRACTED_SRC to stdout (extraction_commit is already correct in
# every fixture below — only manifest_sha256 needs runtime stamping).
_ecc_stamp() {
  _sha="$(_ecc_sha "$1")"
  sed "s/^manifest_sha256:.*/manifest_sha256:   $_sha/" "$2"
}

GOOD_MF="$FX/MANIFEST.md"
GOOD_GP="$FX/EXTRACTED_GAPS.md"
good_ex="$_ecc_tmp/good/JOURNEY_EXTRACTED.md"; mkdir -p "$_ecc_tmp/good"
_ecc_stamp "$GOOD_MF" "$FX/JOURNEY_EXTRACTED.md" > "$good_ex"

# ═══════════════════════════════════════════════════════════════════════
# Golden pass: everything green
# ═══════════════════════════════════════════════════════════════════════

out="$(/bin/sh "$GATE" "$GOOD_MF" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "0" "$rc" "golden: MANIFEST + EXTRACTED + GAPS all green"
assert_contains "$out" "OK: 4 anchor(s) required (2 feat, 2 screen), 3 staged entries checked, 1 gap(s) credited" \
  "golden: success summary line (anchors checked, entries credited, gaps credited)"
assert_not_contains "$out" "NO_GAP_ENTRIES" "golden: a real non-empty gaps file never trips NO_GAP_ENTRIES (anti-vacuous, negative direction)"

# golden run WITHOUT the optional GAPS arg: FEAT-020 has no covering entry
# and (with no GAPS arg) no credit is even possible -> MISSING_EXTRACTION,
# but every OTHER anchor (entry-covered) still passes.
out="$(/bin/sh "$GATE" "$GOOD_MF" "$good_ex" 2>&1)"; rc=$?
assert_eq "1" "$rc" "golden minus GAPS arg: FEAT-020 has no gap credit available -> fails"
assert_contains "$out" "MISSING_EXTRACTION: FEAT-020" "golden minus GAPS arg: names the uncovered feat"
assert_contains "$out" "no GAPS file given" "golden minus GAPS arg: states gap credit is unavailable"
assert_not_contains "$out" "MISSING_EXTRACTION: SCR-login" "golden minus GAPS arg: SCR-login is still entry-covered"
assert_not_contains "$out" "MISSING_EXTRACTION: SCR-checkout" "golden minus GAPS arg: SCR-checkout is still entry-covered via flows"

# ═══════════════════════════════════════════════════════════════════════
# Usage / missing-file (exit 2)
# ═══════════════════════════════════════════════════════════════════════

assert_exit 2 /bin/sh "$GATE"
assert_exit 2 /bin/sh "$GATE" "$GOOD_MF"
assert_exit 2 /bin/sh "$GATE" "$GOOD_MF" "$good_ex" "$GOOD_GP" extra-arg
assert_exit 2 /bin/sh "$GATE" "$GOOD_MF" "$_ecc_tmp/does-not-exist.md"
assert_exit 2 /bin/sh "$GATE" "$GOOD_MF" "$good_ex" "$_ecc_tmp/does-not-exist-gaps.md"
# MANIFEST missing is NOT a usage error (exit 2) — it is a chain code
# (MANIFEST_MISSING, exit 1). Proven below, not here.

# ═══════════════════════════════════════════════════════════════════════
# LINT_FAILED — composition pass-through (not a §7.3 schema code)
# ═══════════════════════════════════════════════════════════════════════

out="$(/bin/sh "$GATE" "$GOOD_MF" "$LINTFX/bad-header.md" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "LINT_FAILED rc"
assert_contains "$out" "LINT_FAILED" "LINT_FAILED pass-through when lint-journey-extracted.sh fails"

# generic RED helper: golden MANIFEST + one sed mutation of the (already
# sha-stamped) golden EXTRACTED, GAPS unchanged unless overridden.
_ecc_case() { # $1=name $2=sed-script(applied to good_ex) $3=expected-code-substring [$4=gaps-path]
  _d="$_ecc_tmp/$1"; mkdir -p "$_d"
  sed "$2" "$good_ex" > "$_d/JOURNEY_EXTRACTED.md"
  _gp="${4:-$GOOD_GP}"
  if [ -n "$_gp" ]; then
    _o="$(/bin/sh "$GATE" "$GOOD_MF" "$_d/JOURNEY_EXTRACTED.md" "$_gp" 2>&1)"; _rc=$?
  else
    _o="$(/bin/sh "$GATE" "$GOOD_MF" "$_d/JOURNEY_EXTRACTED.md" 2>&1)"; _rc=$?
  fi
  assert_eq "1" "$_rc" "red rc: $1"
  assert_contains "$_o" "$3" "red code: $1"
}

# ── STAGE 1 (parse) ────────────────────────────────────────────────────

_d="$_ecc_tmp/manifest-missing"; mkdir -p "$_d"
out="$(/bin/sh "$GATE" "$_d/NOPE.md" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "MANIFEST_MISSING rc (chain code, NOT exit 2)"
assert_contains "$out" "MANIFEST_MISSING" "MANIFEST_MISSING names the code"

printf '# MANIFEST\n\nno machine block here at all.\n' > "$_ecc_tmp/no-block.md"
out="$(/bin/sh "$GATE" "$_ecc_tmp/no-block.md" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "MANIFEST_BLOCK_MISSING rc"
assert_contains "$out" "MANIFEST_BLOCK_MISSING" "MANIFEST_BLOCK_MISSING names the code"

# ── MANIFEST_BLOCK_AMBIGUOUS (V-E3 F1): TWO complete blocks — pre-fix, the
# first-END-wins extractor parsed only block 1, and block 2's FEAT-CCC
# (behaviors=9) escaped the completeness accounting entirely at rc=0 with
# an OK: summary (verifier repro, reproduced RED before this fix). The
# EXTRACTED file is sha-stamped against block 1 alone (exactly what a
# pre-fix pass looked like), so ONLY the new cardinality check can reject.
{ cat "$GOOD_MF"
  printf '\nEXTRACTION-MANIFEST BEGIN\nmanifest_version: 1\nextraction_commit: 1111111111111111111111111111111111111111\nfeat: FEAT-CCC | behaviors=9 | states_filled=1 | grade_counts=C:1,I:0,G:0,X:0\nEXTRACTION-MANIFEST END\n'
} > "$_ecc_tmp/two-blocks.md"
out="$(/bin/sh "$GATE" "$_ecc_tmp/two-blocks.md" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "MANIFEST_BLOCK_AMBIGUOUS rc (two complete blocks; pre-fix this was rc=0 with block 2's FEAT-CCC unaccounted)"
assert_contains "$out" "MANIFEST_BLOCK_AMBIGUOUS: 2 blocks found (exactly one required" \
  "MANIFEST_BLOCK_AMBIGUOUS names the code and the block count"
assert_not_contains "$out" "OK:" "MANIFEST_BLOCK_AMBIGUOUS: no OK summary is ever printed over an ambiguous manifest"

# same class, surplus-delimiter variant: a second BEGIN that never closes —
# its content would escape accounting exactly like a second block's did.
{ cat "$GOOD_MF"
  printf '\nEXTRACTION-MANIFEST BEGIN\nfeat: FEAT-DDD | behaviors=5 | states_filled=1 | grade_counts=C:1,I:0,G:0,X:0\n'
} > "$_ecc_tmp/stray-begin.md"
out="$(/bin/sh "$GATE" "$_ecc_tmp/stray-begin.md" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "MANIFEST_BLOCK_AMBIGUOUS rc (surplus unclosed BEGIN — same escape class)"
assert_contains "$out" "MANIFEST_BLOCK_AMBIGUOUS" "MANIFEST_BLOCK_AMBIGUOUS fires on a surplus unclosed BEGIN too"

# value with a SPACE (grade_counts value split by an embedded space)
sed 's/grade_counts=C:5,I:1,G:2,X:0/grade_counts=has space/' "$GOOD_MF" > "$_ecc_tmp/format-space.md"
out="$(/bin/sh "$GATE" "$_ecc_tmp/format-space.md" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "MANIFEST_FORMAT (space in value) rc"
assert_contains "$out" "MANIFEST_FORMAT" "MANIFEST_FORMAT (space in value) names the code"

# value with an embedded PIPE (breaks the fixed 4-field feat: shape)
sed 's/grade_counts=C:5,I:1,G:2,X:0/grade_counts=C:5,I:1|X:0/' "$GOOD_MF" > "$_ecc_tmp/format-pipe.md"
out="$(/bin/sh "$GATE" "$_ecc_tmp/format-pipe.md" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "MANIFEST_FORMAT (pipe in value) rc"
assert_contains "$out" "MANIFEST_FORMAT" "MANIFEST_FORMAT (pipe in value) names the code"

# fail-slow WITHIN stage 1: the space-value AND pipe-value mutations
# together, same manifest, same run — both independently reported.
sed 's/grade_counts=C:5,I:1,G:2,X:0/grade_counts=has space/; s/grade_counts=C:1,I:0,G:0,X:0/grade_counts=C:1|X:0/' "$GOOD_MF" \
  > "$_ecc_tmp/format-multi.md"
out="$(/bin/sh "$GATE" "$_ecc_tmp/format-multi.md" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "stage-1 fail-slow: two independent MANIFEST_FORMAT lines, one run, rc"
assert_contains "$out" "grade_counts=has space" "stage-1 fail-slow: first bad line reported"
assert_contains "$out" "grade_counts=C:1|X:0" "stage-1 fail-slow: second bad line reported in the SAME run"

# ── STAGE 2 (soundness) ────────────────────────────────────────────────

awk '1; /^feat: FEAT-014/{print}' "$GOOD_MF" > "$_ecc_tmp/dup-feat.md"
out="$(/bin/sh "$GATE" "$_ecc_tmp/dup-feat.md" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "MANIFEST_DUPLICATE rc"
assert_contains "$out" "MANIFEST_DUPLICATE: feat FEAT-014" "MANIFEST_DUPLICATE names the repeated feat"

# ── cross-NAMESPACE collision (V-E3 F3): the token COLLIDE exists as BOTH
# a feat: id (behaviors>=1) and a screen: id (flows declared). Pre-fix the
# per-kind dedup loops saw no repeat and one staging covers: COLLIDE token
# credited TWO required anchors at rc=0 (verifier repro, reproduced RED
# before this fix).
sed 's/feat: FEAT-020 | behaviors=1 | states_filled=2 | grade_counts=C:1,I:0,G:0,X:0/feat: COLLIDE | behaviors=1 | states_filled=2 | grade_counts=C:1,I:0,G:0,X:0/; s/screen: SCR-dashboard | route=\/dashboard/screen: COLLIDE | route=\/collide | flows=AFJ-009/' \
  "$GOOD_MF" > "$_ecc_tmp/collide-manifest.md"
_col_src="$_ecc_tmp/collide-src.md"
sed 's/covers:              FEAT-014/covers:              FEAT-014,COLLIDE/' "$FX/JOURNEY_EXTRACTED.md" > "$_col_src"
_col_ex="$_ecc_tmp/collide-extracted.md"
_ecc_stamp "$_ecc_tmp/collide-manifest.md" "$_col_src" > "$_col_ex"
out="$(/bin/sh "$GATE" "$_ecc_tmp/collide-manifest.md" "$_col_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "MANIFEST_DUPLICATE rc (cross-namespace COLLIDE; pre-fix this was rc=0 with one token crediting two anchors)"
assert_contains "$out" "MANIFEST_DUPLICATE: COLLIDE appears in more than one namespace" \
  "MANIFEST_DUPLICATE cross-namespace message names the colliding token"

sed 's/^extraction_commit: .*/extraction_commit: 2222222222222222222222222222222222222222/' "$GOOD_MF" \
  > "$_ecc_tmp/commit-mismatch.md"
out="$(/bin/sh "$GATE" "$_ecc_tmp/commit-mismatch.md" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "MANIFEST_COMMIT_MISMATCH rc"
assert_contains "$out" "MANIFEST_COMMIT_MISMATCH" "MANIFEST_COMMIT_MISMATCH names the code"

# ── STAGE 3 (freshness) ────────────────────────────────────────────────

# additive, behaviors=0 (harmless to completeness) manifest edit AFTER the
# golden EXTRACTED's sha was stamped -> current sha no longer matches.
{ cat "$GOOD_MF" | sed '/^EXTRACTION-MANIFEST END$/i\
feat: FEAT-500 | behaviors=0 | states_filled=0 | grade_counts=C:0,I:0,G:0,X:0
'; } > "$_ecc_tmp/stale-manifest.md"
out="$(/bin/sh "$GATE" "$_ecc_tmp/stale-manifest.md" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "EXTRACTION_STALE rc"
assert_contains "$out" "EXTRACTION_STALE" "EXTRACTION_STALE names the code"

# ── STAGE 4 (completeness) ─────────────────────────────────────────────

_ecc_case unknown-covers \
  's/covers:              FEAT-014/covers:              FEAT-014,FEAT-999/' \
  "UNKNOWN_ANCHOR: EXTRACTED-1: FEAT-999"

_ecc_case unknown-flows \
  's/flows:               AFJ-002/flows:               AFJ-002,AFJ-999/' \
  "UNKNOWN_ANCHOR: EXTRACTED-3: AFJ-999"

# ── ANCHOR_TOKEN_INVALID (V-E3 F2, L22): a staging value `covers: *` run
# from a CWD containing files named after manifest anchors. Pre-fix, the
# unquoted `for _tok in $(...)` loop PATHNAME-EXPANDED the `*` against the
# caller's cwd and a cwd file named FEAT-100 became a false coverage
# credit at rc=0 (verifier repro, reproduced RED before this fix). Post-fix
# the raw `*` (set -f keeps it unexpanded) fails the `^[A-Za-z0-9._-]+$`
# whitelist -> ANCHOR_TOKEN_INVALID, regardless of cwd contents — and the
# anchors the glob used to fake now honestly report MISSING_EXTRACTION.
sed 's/feat: FEAT-020 | behaviors=1 | states_filled=2 | grade_counts=C:1,I:0,G:0,X:0/feat: FEAT-100 | behaviors=1 | states_filled=2 | grade_counts=C:1,I:0,G:0,X:0/' \
  "$GOOD_MF" > "$_ecc_tmp/glob-manifest.md"
_glob_src="$_ecc_tmp/glob-src.md"
sed 's/covers:              FEAT-014/covers:              */' "$FX/JOURNEY_EXTRACTED.md" > "$_glob_src"
_glob_ex="$_ecc_tmp/glob-extracted.md"
_ecc_stamp "$_ecc_tmp/glob-manifest.md" "$_glob_src" > "$_glob_ex"
mkdir -p "$_ecc_tmp/glob-cwd"
: > "$_ecc_tmp/glob-cwd/FEAT-100"
: > "$_ecc_tmp/glob-cwd/FEAT-014"
: > "$_ecc_tmp/glob-cwd/SCR-login"
out="$(cd "$_ecc_tmp/glob-cwd" && /bin/sh "$GATE" "$_ecc_tmp/glob-manifest.md" "$_glob_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "ANCHOR_TOKEN_INVALID rc (covers: * in a crafted cwd; pre-fix the glob expanded and FEAT-100 was falsely credited at rc=0)"
assert_contains "$out" "ANCHOR_TOKEN_INVALID: EXTRACTED-1: *" \
  "ANCHOR_TOKEN_INVALID names the entry and the raw, UNEXPANDED token (set -f held)"
assert_not_contains "$out" "UNKNOWN_ANCHOR: EXTRACTED-1: *" \
  "whitelist-first: an invalid token gets ONE primary code, never UNKNOWN_ANCHOR on top"
assert_contains "$out" "MISSING_EXTRACTION: FEAT-100" \
  "the anchor the glob used to falsely credit now honestly reports MISSING_EXTRACTION in the same run"

# unknown flows token when NO screen in the whole manifest declares ANY
# flows= at all (the degenerate case spec discussion calls out explicitly):
# a nonempty flows: token must still fail closed, not vacuously pass
# because the anchor pool it is checked against is empty.
sed 's/screen: SCR-login | route=\/login | flows=AFJ-001/screen: SCR-login | route=\/login/; s/screen: SCR-checkout | route=\/checkout | flows=AFJ-002/screen: SCR-checkout | route=\/checkout/' \
  "$GOOD_MF" > "$_ecc_tmp/no-flows-manifest.md"
_noflows_ex="$_ecc_tmp/no-flows-extracted.md"
_ecc_stamp "$_ecc_tmp/no-flows-manifest.md" "$FX/JOURNEY_EXTRACTED.md" > "$_noflows_ex"
out="$(/bin/sh "$GATE" "$_ecc_tmp/no-flows-manifest.md" "$_noflows_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "UNKNOWN_ANCHOR (zero screens declare flows anywhere) rc"
assert_contains "$out" "UNKNOWN_ANCHOR: EXTRACTED-3: AFJ-002" \
  "UNKNOWN_ANCHOR: a flows token fails closed against an EMPTY flows-anchor pool, not vacuously"

# uncovered feat WITH a gaps arg but the gap is EXPIRED — not a credit;
# both GAP_EXPIRED and the resulting MISSING_EXTRACTION appear.
sed 's/^expires: 2099-12-31$/expires: 2020-01-01/' "$GOOD_GP" > "$_ecc_tmp/gaps-expired.md"
out="$(/bin/sh "$GATE" "$GOOD_MF" "$good_ex" "$_ecc_tmp/gaps-expired.md" 2>&1)"; rc=$?
assert_eq "1" "$rc" "GAP_EXPIRED rc"
assert_contains "$out" "GAP_EXPIRED: gap FEAT-020 expired 2020-01-01" "GAP_EXPIRED names the expired gap"
assert_contains "$out" "MISSING_EXTRACTION: FEAT-020" "GAP_EXPIRED: an expired gap is not a coverage credit — anchor still fails"

grep -v '^owner:' "$GOOD_GP" > "$_ecc_tmp/gaps-malformed.md"
out="$(/bin/sh "$GATE" "$GOOD_MF" "$good_ex" "$_ecc_tmp/gaps-malformed.md" 2>&1)"; rc=$?
assert_eq "1" "$rc" "GAP_FORMAT rc"
assert_contains "$out" "GAP_FORMAT: gap FEAT-020" "GAP_FORMAT names the malformed gap"

printf '# EXTRACTED_GAPS — empty\n\nno entries here.\n' > "$_ecc_tmp/gaps-empty.md"
out="$(/bin/sh "$GATE" "$GOOD_MF" "$good_ex" "$_ecc_tmp/gaps-empty.md" 2>&1)"; rc=$?
assert_eq "1" "$rc" "NO_GAP_ENTRIES rc (anti-vacuous: GAPS given, zero entries)"
assert_contains "$out" "NO_GAP_ENTRIES" "NO_GAP_ENTRIES names the code"

# ── Screen-anchored covers entry credits a screen: prove it in isolation ──
# Drop EXTRACTED-3 (the flows-path entry) entirely: SCR-checkout becomes
# uncovered (MISSING_EXTRACTION), but SCR-login MUST stay covered purely by
# EXTRACTED-2's `covers: SCR-login` — no flows: token names it anywhere.
awk '/^## EXTRACTED-3/{skip=1} /^## EXTRACTED-2/{skip=0} !skip' "$FX/JOURNEY_EXTRACTED.md" > "$_ecc_tmp/screen-anchor-src.md"
_sa_ex="$_ecc_tmp/screen-anchor-only.md"
_ecc_stamp "$GOOD_MF" "$_ecc_tmp/screen-anchor-src.md" > "$_sa_ex"
out="$(/bin/sh "$GATE" "$GOOD_MF" "$_sa_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "screen-anchored-covers isolation: EXTRACTED-3 dropped, SCR-checkout now uncovered"
assert_contains "$out" "MISSING_EXTRACTION: SCR-checkout" "screen-anchored-covers isolation: SCR-checkout is indeed uncovered without EXTRACTED-3"
assert_not_contains "$out" "MISSING_EXTRACTION: SCR-login" \
  "screen-anchored-covers isolation: SCR-login STAYS covered by EXTRACTED-2's covers: SCR-login alone (proves the direct screen-anchored-covers credit path)"

# ── Fail-slow: two INDEPENDENT stage-4 violation classes, one run ────────
# combine the unknown-covers mutation with dropping the GAPS credit
# entirely (omit the arg) so FEAT-020 is ALSO reported -> UNKNOWN_ANCHOR
# and MISSING_EXTRACTION, two different codes, together.
sed 's/covers:              FEAT-014/covers:              FEAT-014,FEAT-999/' "$good_ex" > "$_ecc_tmp/failslow-multi.md"
out="$(/bin/sh "$GATE" "$GOOD_MF" "$_ecc_tmp/failslow-multi.md" 2>&1)"; rc=$?
assert_eq "1" "$rc" "stage-4 fail-slow: two independent violation classes, one run, rc"
assert_contains "$out" "UNKNOWN_ANCHOR: EXTRACTED-1: FEAT-999" "stage-4 fail-slow: first independent violation (UNKNOWN_ANCHOR) present"
assert_contains "$out" "MISSING_EXTRACTION: FEAT-020" "stage-4 fail-slow: second independent violation (MISSING_EXTRACTION), a DIFFERENT code, present in the SAME run"

# ═══════════════════════════════════════════════════════════════════════
# TOOL_MISSING — PATH shim excluding sha256sum AND shasum (E2 precedent)
# ═══════════════════════════════════════════════════════════════════════

_shim_nosha="$_ecc_tmp/shim-nosha"; mkdir -p "$_shim_nosha"
for _b in sh awk sed grep tr head sort uniq cat mktemp dirname basename rm wc printf date; do
  _real="$(command -v "$_b")" && ln -s "$_real" "$_shim_nosha/$_b"
done
out="$(PATH="$_shim_nosha" /bin/sh "$GATE" "$GOOD_MF" "$good_ex" "$GOOD_GP" 2>&1)"; rc=$?
assert_eq "1" "$rc" "TOOL_MISSING (no sha256sum/shasum) rc"
assert_contains "$out" "TOOL_MISSING" "TOOL_MISSING names the code"

rm -rf "$_ecc_tmp"
