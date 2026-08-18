# shellcheck shell=sh
# feat-anchor-grammar_test.sh — owner ruling A (2026-07-14).
#
# The framework has ONE canonical feature-id grammar, the one check-doc-format.sh
# enforces on every PRD it accepts:
#
#     FEAT-([A-Z]+-)?[0-9]+          e.g. FEAT-001  and  FEAT-AUD-101
#
# The coverage gates anchored on the NARROWER `^## FEAT-[0-9]` instead. The
# consequence was not a polite refusal — it was silent blindness:
#
#   * check-persona-coverage.sh derived ZERO anchors from a prefixed-id PRD and
#     died NO_ANCHORS, accusing a 122-feature PRD of being empty;
#   * check-journey-coverage.sh derived an empty $FA, so every real journey's
#     covers became INVALID_SOURCE_ID "not a FEAT-ID in PRD" — the gate blaming
#     the docs for the gate's own regex;
#   * the two slicers sliced a prefixed-id PRD into nothing, and
#     check-journey-provenance.sh silently attributed a prefixed FEAT's ACs to
#     whichever plain-id FEAT happened to precede it.
#
# These tests lock BOTH forms in, and — just as importantly — lock the
# near-misses OUT, so widening the grammar cannot become "anything starting with
# FEAT is an anchor". A gate that accepts junk anchors is as dishonest as one
# that ignores real ones.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
BIN="$TESTS_DIR/../bin"
CPC="$BIN/check-persona-coverage.sh"
CJC="$BIN/check-journey-coverage.sh"
CDF="$BIN/check-doc-format.sh"
JGS="$BIN/journey-gen-slice.sh"
PGS="$BIN/persona-gen-slice.sh"
FX="$TESTS_DIR/fixtures/gen/coverage/pass"
GEN="$TESTS_DIR/fixtures/gen"

_fa=$(mktemp -d)
trap 'rm -rf "$_fa"' EXIT INT TERM

_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# A1. The SAME bundle, prefixed — identical verdict.
#
# The strongest available proof that the grammar (not the content) was the
# blocker: take the golden `pass` coverage fixture, rename FEAT-00N -> FEAT-AUD-10N
# EVERYWHERE (PRD, APP_FLOW, map, manifest, gaps), change nothing else, and demand
# the identical exit 0. If prefixed ids were merely "tolerated" rather than
# understood, the accounting (_index reconciliation, gap credits, AFJ axis) would
# not survive this transform.
# ═══════════════════════════════════════════════════════════════════════════════
_pfx="$_fa/prefixed"
mkdir -p "$_pfx"
for _f in PRD.md APP_FLOW.md JOURNEY_MAP.generated.md JOURNEY_COVERAGE_MANIFEST.json JOURNEY_COVERAGE_GAPS.md; do
  sed -e 's/FEAT-001/FEAT-AUD-101/g' \
      -e 's/FEAT-002/FEAT-AUD-102/g' \
      -e 's/FEAT-003/FEAT-AUD-103/g' \
      -e 's/FEAT-004/FEAT-AUD-104/g' "$FX/$_f" > "$_pfx/$_f"
done

sh "$CJC" "$FX/PRD.md" "$FX/APP_FLOW.md" "$FX/JOURNEY_MAP.generated.md" \
  "$FX/JOURNEY_COVERAGE_MANIFEST.json" "$FX/JOURNEY_COVERAGE_GAPS.md" >/dev/null 2>&1
assert_eq 0 $? "fa-A1a: journey-coverage passes the golden PLAIN-id bundle (regression)"

sh "$CJC" "$_pfx/PRD.md" "$_pfx/APP_FLOW.md" "$_pfx/JOURNEY_MAP.generated.md" \
  "$_pfx/JOURNEY_COVERAGE_MANIFEST.json" "$_pfx/JOURNEY_COVERAGE_GAPS.md" >/dev/null 2>&1
assert_eq 0 $? "fa-A1b: journey-coverage passes the SAME bundle with PREFIXED ids (FEAT-AUD-101)"

# check-doc-format.sh OWNS the canonical grammar — the gates copy it from there.
# So the honest assertion is PREFIX-INVARIANCE: the canonical gate must treat the
# plain and prefixed PRDs identically. (Both exit 1 here on SCREENS_SECTION_MISSING
# — this coverage fixture predates the §3b Screens contract and has no ## Screens
# section. That is a property of the fixture, not of the ids: what matters is that
# the verdict and the FEAT-side diagnostics are the SAME either way, and that
# neither PRD is ever accused of having no FEAT blocks.)
_o_plain=$(sh "$CDF" "$FX/PRD.md" "$FX/APP_FLOW.md" 2>&1); _ec_plain=$?
_o_pfx=$(sh "$CDF" "$_pfx/PRD.md" "$_pfx/APP_FLOW.md" 2>&1); _ec_pfx=$?
assert_eq "$_ec_plain" "$_ec_pfx" "fa-A1c: check-doc-format's verdict is identical for plain and prefixed ids"
assert_not_contains "$_o_pfx" "PRD_NO_FEAT_BLOCKS" "fa-A1d: the prefixed PRD is never 'a PRD with no FEAT blocks'"
assert_not_contains "$_o_pfx" "UNLINKED_FEAT" "fa-A1e: prefixed FEATs keep their covers_flows linkage"

# ═══════════════════════════════════════════════════════════════════════════════
# A2. Prefixed anchors are REAL anchors, not vacuous ones.
#
# Widening a regex until the gate stops complaining is the classic false green.
# Proof of the opposite: drop a P0/P1 prefixed FEAT's coverage and the gate must
# now NAME it. An anchor you cannot fail on is not an anchor.
# ═══════════════════════════════════════════════════════════════════════════════
_gap="$_fa/prefixed-uncovered"
mkdir -p "$_gap"
cp "$_pfx"/* "$_gap"/
# FEAT-AUD-102 loses its journey AND its gap record: manifest drops JOURNEY-102's
# coverage of it, and it has no gap. It is P1 -> required -> must be reported.
sed -e 's/"covers": \["FEAT-AUD-102"\]/"covers": []/' \
    -e 's/"FEAT-AUD-102": { "journeys": \["JOURNEY-102"\], "gap": null },/"FEAT-AUD-102": { "journeys": [], "gap": null },/' \
    "$_pfx/JOURNEY_COVERAGE_MANIFEST.json" > "$_gap/JOURNEY_COVERAGE_MANIFEST.json"
sed 's/^covers:          FEAT-AUD-102$/covers:/' "$_pfx/JOURNEY_MAP.generated.md" > "$_gap/JOURNEY_MAP.generated.md"
_o=$(sh "$CJC" "$_gap/PRD.md" "$_gap/APP_FLOW.md" "$_gap/JOURNEY_MAP.generated.md" \
       "$_gap/JOURNEY_COVERAGE_MANIFEST.json" "$_gap/JOURNEY_COVERAGE_GAPS.md" 2>&1); _ec=$?
_nonzero "$_ec" "fa-A2a: an uncovered P0/P1 PREFIXED FEAT still fails closed"
assert_contains "$_o" "COVERAGE_GAP" "fa-A2b: names COVERAGE_GAP for the prefixed id"
assert_contains "$_o" "FEAT-AUD-102" "fa-A2c: names the specific prefixed FEAT (anchor is real, not vacuous)"

# A bogus prefixed id in the manifest is still refused — the anchor SET is
# authoritative, the grammar is not a licence to invent ids.
_bogus="$_fa/prefixed-bogus"
mkdir -p "$_bogus"
cp "$_pfx"/* "$_bogus"/
sed 's/"covers": \["FEAT-AUD-101"\]/"covers": ["FEAT-AUD-999"]/' \
  "$_pfx/JOURNEY_COVERAGE_MANIFEST.json" > "$_bogus/JOURNEY_COVERAGE_MANIFEST.json"
_o=$(sh "$CJC" "$_bogus/PRD.md" "$_bogus/APP_FLOW.md" "$_bogus/JOURNEY_MAP.generated.md" \
       "$_bogus/JOURNEY_COVERAGE_MANIFEST.json" "$_bogus/JOURNEY_COVERAGE_GAPS.md" 2>&1); _ec=$?
_nonzero "$_ec" "fa-A2d: a grammatical-but-undeclared prefixed id (FEAT-AUD-999) still fails"
assert_contains "$_o" "INVALID_SOURCE_ID" "fa-A2e: names INVALID_SOURCE_ID for the undeclared prefixed id"

# ═══════════════════════════════════════════════════════════════════════════════
# A3. check-persona-coverage: plain, prefixed, and a real prefixed gap.
# ═══════════════════════════════════════════════════════════════════════════════
# Golden plain-id chain still passes (regression).
sh "$CPC" "$GEN/PRD.md" "$GEN/SSOT.md" "$TESTS_DIR/fixtures/persona/JOURNEY_MAP.persona.md" \
  "$TESTS_DIR/fixtures/persona/PERSONA_COVERAGE_GAPS.md" >/dev/null 2>&1
assert_eq 0 $? "fa-A3a: persona-coverage still passes the golden PLAIN-id chain (regression)"

# Prefixed chain: PRD with prefixed ids, a PERSONA journey covering one, a gap for
# the other. Before the ruling this died NO_ANCHORS on a perfectly good PRD.
cat > "$_fa/PRD.prefixed.md" <<'EOF'
# PRD

## FEAT-AUD-101 — "Register audit"
priority: P0
user_story: As a conductor, I register an audit.
acceptance_criteria:
  - AC-1: the audit is registered

## FEAT-AUD-102 — "Close finding"
priority: P1
user_story: As an owner, I close a finding.
acceptance_criteria:
  - AC-1: the finding closes

## FEAT-AUD-103 — "Export"
priority: P2
user_story: As a manager, I export.
acceptance_criteria:
  - AC-1: export works
EOF

cat > "$_fa/MAP.prefixed.md" <<'EOF'
# Journey Map

## JOURNEY-1 — "Ops user registers an audit and double-clicks submit"
origin:          PERSONA
persona:         P1 (Operations User)
goal:            register an audit
priority:        P0
covers:          FEAT-AUD-101
flows:
oracle_surface:  UI
steps:
  1. registers the audit (misbehavior: double-clicks-submit)
oracle:          per FEAT-AUD-101 AC-1 the audit is registered exactly once
evidence:        []
test:
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
EOF

cat > "$_fa/GAPS.prefixed.md" <<'EOF'
# Persona Coverage Gaps

## GAP-1
source_id: FEAT-AUD-102
source_type: FEAT
reason: build-time infrastructure with no user surface
owner: product-owner
reviewer: prince
expires: 2099-12-31
EOF

sh "$CPC" "$_fa/PRD.prefixed.md" "$GEN/SSOT.md" "$_fa/MAP.prefixed.md" "$_fa/GAPS.prefixed.md" >/dev/null 2>&1
assert_eq 0 $? "fa-A3b: persona-coverage passes a PREFIXED-id chain (journey + valid gap)"

# The prefixed anchors bite: remove the gap and the uncovered P1 must be named.
printf '# no gaps\n' > "$_fa/GAPS.empty.md"
_o=$(sh "$CPC" "$_fa/PRD.prefixed.md" "$GEN/SSOT.md" "$_fa/MAP.prefixed.md" "$_fa/GAPS.empty.md" 2>&1); _ec=$?
_nonzero "$_ec" "fa-A3c: an uncovered P0/P1 prefixed FEAT fails persona-coverage"
assert_contains "$_o" "PERSONA_COVERAGE_GAP" "fa-A3d: names PERSONA_COVERAGE_GAP"
assert_contains "$_o" "FEAT-AUD-102" "fa-A3e: names the uncovered prefixed FEAT"
# P2 is excluded from the anchor set, prefixed or not.
assert_not_contains "$_o" "FEAT-AUD-103" "fa-A3f: a P2 prefixed FEAT is NOT a required anchor"

# The covers-token filter accepts prefixed ids (it used to silently drop them,
# which turned a covered FEAT into an uncovered one).
_o=$(sh "$CPC" "$_fa/PRD.prefixed.md" "$GEN/SSOT.md" "$_fa/MAP.prefixed.md" "$_fa/GAPS.prefixed.md" 2>&1)
assert_not_contains "$_o" "FEAT-AUD-101" "fa-A3g: the journey's PREFIXED covers token is honoured as coverage"

# ═══════════════════════════════════════════════════════════════════════════════
# A4. Malformed near-matches are NOT anchors.
#
# The widened grammar must not become a sponge. Each of these is one character
# away from a real id and must derive ZERO anchors -> NO_ANCHORS (fail closed),
# never a silent pass and never a phantom anchor.
#   ## FEAT-abc      lowercase suffix, no digits
#   ## FEATURE-001   different token entirely
#   ## FEAT-         no id at all
#   ## FEAT-AUD-     prefix present, number missing
#   ## FEAT-AUD      prefix without the separating hyphen or a number
# ═══════════════════════════════════════════════════════════════════════════════
cat > "$_fa/PRD.malformed.md" <<'EOF'
# PRD

## FEAT-abc — "Lowercase suffix"
priority: P0
user_story: As a user, I do a thing.
acceptance_criteria:
  - AC-1: it happens

## FEATURE-001 — "Wrong token"
priority: P0
user_story: As a user, I do a thing.
acceptance_criteria:
  - AC-1: it happens

## FEAT- — "No id"
priority: P0
user_story: As a user, I do a thing.
acceptance_criteria:
  - AC-1: it happens

## FEAT-AUD- — "Prefix, no number"
priority: P0
user_story: As a user, I do a thing.
acceptance_criteria:
  - AC-1: it happens

## FEAT-AUD — "Prefix, no separator, no number"
priority: P0
user_story: As a user, I do a thing.
acceptance_criteria:
  - AC-1: it happens
EOF

_o=$(sh "$CPC" "$_fa/PRD.malformed.md" "$GEN/SSOT.md" "$_fa/MAP.prefixed.md" "$_fa/GAPS.empty.md" 2>&1); _ec=$?
_nonzero "$_ec" "fa-A4a: a PRD of malformed near-matches yields no anchors (fails closed)"
assert_contains "$_o" "NO_ANCHORS" "fa-A4b: names NO_ANCHORS — near-matches are not features"

# check-doc-format, the canonical owner of the grammar, agrees: no FEAT blocks.
_o=$(sh "$CDF" "$_fa/PRD.malformed.md" "$FX/APP_FLOW.md" 2>&1); _ec=$?
_nonzero "$_ec" "fa-A4c: check-doc-format also derives no FEAT blocks from the near-matches"
assert_contains "$_o" "PRD_NO_FEAT_BLOCKS" "fa-A4d: canonical gate names PRD_NO_FEAT_BLOCKS (grammars agree)"

# Mixed PRD: the good ids are anchored, the near-matches are ignored — the
# near-matches must not become phantom anchors that can never be covered.
cat "$_fa/PRD.prefixed.md" "$_fa/PRD.malformed.md" > "$_fa/PRD.mixed.md"
_o=$(sh "$CPC" "$_fa/PRD.mixed.md" "$GEN/SSOT.md" "$_fa/MAP.prefixed.md" "$_fa/GAPS.prefixed.md" 2>&1); _ec=$?
assert_eq 0 "$_ec" "fa-A4e: a PRD mixing valid ids with near-matches passes on the valid ids alone"
assert_not_contains "$_o" "FEAT-abc"    "fa-A4f: FEAT-abc never becomes an anchor"
assert_not_contains "$_o" "FEATURE-001" "fa-A4g: FEATURE-001 never becomes an anchor"

# Plain and prefixed ids coexist in one PRD (a module adopting prefixes mid-life).
cat > "$_fa/PRD.both.md" <<'EOF'
# PRD

## FEAT-001 — "Plain id"
priority: P0
user_story: As a user, I log in.
acceptance_criteria:
  - AC-1: login works

## FEAT-AUD-101 — "Prefixed id"
priority: P0
user_story: As a conductor, I register an audit.
acceptance_criteria:
  - AC-1: the audit is registered
EOF
cat > "$_fa/GAPS.both.md" <<'EOF'
# Persona Coverage Gaps

## GAP-1
source_id: FEAT-001
source_type: FEAT
reason: covered by the legacy suite, no persona surface
owner: product-owner
reviewer: prince
expires: 2099-12-31
EOF
sh "$CPC" "$_fa/PRD.both.md" "$GEN/SSOT.md" "$_fa/MAP.prefixed.md" "$_fa/GAPS.both.md" >/dev/null 2>&1
assert_eq 0 $? "fa-A4h: one PRD carrying BOTH plain and prefixed ids is fully accounted"

# ═══════════════════════════════════════════════════════════════════════════════
# A5. The slicers share the grammar.
#
# The gates and the slicers must split the PRD identically. If the slicer is
# blind to prefixed ids it emits zero bundles and journey generation quietly
# produces nothing to gate — a green pipeline over an empty universe.
# ═══════════════════════════════════════════════════════════════════════════════
# Bundle filenames are lower-cased by the slicers (feat-aud-101.md), so match
# case-insensitively — what is being proved is that the bundle EXISTS at all.
_has_bundle() { # DIR GLOB MSG
  _n=$(find "$1" -iname "$2" 2>/dev/null | wc -l | tr -d ' ')
  if [ "${_n:-0}" -gt 0 ]; then printf 'ok: %s\n' "$3"; else
    printf 'FAIL: %s (no bundle matched %s — a real PRD sliced into nothing)\n' "$3" "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

sh "$JGS" "$GEN/SSOT.md" "$_pfx/PRD.md" "$_pfx/APP_FLOW.md" "$_fa/out-jgs" >/dev/null 2>&1
assert_eq 0 $? "fa-A5a: journey-gen-slice accepts a PREFIXED-id PRD"
_has_bundle "$_fa/out-jgs" '*feat-aud-101*' "fa-A5b: journey-gen-slice emits a bundle for the prefixed FEAT-AUD-101"

sh "$PGS" "$GEN/SSOT.md" "$_pfx/PRD.md" "$_pfx/APP_FLOW.md" "$_fa/out-pgs" >/dev/null 2>&1
assert_eq 0 $? "fa-A5c: persona-gen-slice accepts a PREFIXED-id PRD"
_has_bundle "$_fa/out-pgs" '*feat-aud-101-p1*' "fa-A5d: persona-gen-slice emits a (FEAT-AUD-101 x persona) bundle"
