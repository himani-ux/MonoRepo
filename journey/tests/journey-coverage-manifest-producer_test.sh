# shellcheck shell=sh
# journey-coverage-manifest-producer_test.sh — owner ruling, ITEM 3 (2026-07-14).
#
# JOURNEY_COVERAGE_MANIFEST.json is GENERATED EVIDENCE, not a manually authored
# SSOT. Before generate-journey-coverage-manifest.sh existed, the only thing that
# could write it was an LLM merge backend — so a project with a hand-authored
# journey map had no way to obtain one except to TYPE IT. A hand-typed coverage
# manifest is a claim about coverage wearing the costume of evidence: anything a
# human can type to make a gate pass is not evidence.
#
# The producer therefore:
#   * derives ONLY from canonical machine-readable anchors (FEAT ids + priority,
#     AFJ ids, the JOURNEY_MAP's own covers:/flows:, formal gap records);
#   * NEVER infers a mapping from a structural coincidence — a journey covers an
#     AFJ when its `flows:` field SAYS SO. Inventing the mapping would let the
#     framework manufacture coverage the project never declared;
#   * is deterministic: identical inputs => byte-identical output, no timestamps;
#   * fails CLOSED on a missing source, a malformed/ambiguous anchor, an unknown
#     journey/feature mapping, duplicate mappings, or a malformed gap;
#   * ships a DRIFT CHECK so a committed manifest cannot be hand-edited: --check
#     regenerates and refuses any difference (MANIFEST_STALE).
#
# The anti-false-green core (mp-D2/mp-D3): a manifest hand-edited to fabricate
# coverage for a gapped FEAT is caught by the drift check — which is the whole
# point of the ruling. "No manifest content may be hand-entered to make a gate
# pass."

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
GEN="$TESTS_DIR/../bin/generate-journey-coverage-manifest.sh"
CJC="$TESTS_DIR/../bin/check-journey-coverage.sh"
COV="$TESTS_DIR/fixtures/gen/coverage/pass"

_mp=$(mktemp -d)
trap 'rm -rf "$_mp"' EXIT INT TERM

_gen() { # OUT_FILE [DIR] -> generate from a bundle dir (default: the pass fixture)
  _d="${2:-$COV}"
  sh "$GEN" "$_d/PRD.md" "$_d/APP_FLOW.md" "$_d/JOURNEY_MAP.generated.md" \
            "$_d/JOURNEY_COVERAGE_GAPS.md" > "$1" 2>"$_mp/err.txt"
}
_gate() { # MANIFEST [DIR]
  _d="${2:-$COV}"
  sh "$CJC" "$_d/PRD.md" "$_d/APP_FLOW.md" "$_d/JOURNEY_MAP.generated.md" \
            "$1" "$_d/JOURNEY_COVERAGE_GAPS.md" 2>&1
}

# ══════════════════════════════════════════════════════════════════════════════
# A. COMPLETE COVERAGE + APPROVED GAPS (the golden bundle has both: FEAT-001/002
#    and AFJ-001/002 are journeyed; FEAT-003 and AFJ-003 are formally gapped).
# ══════════════════════════════════════════════════════════════════════════════
_gen "$_mp/m.json"; _e=$?
assert_eq "0" "$_e" "mp-A1: producer emits a manifest for the golden bundle"

_o=$(_gate "$_mp/m.json"); _e=$?
assert_eq "0" "$_e" "mp-A2: check-journey-coverage PASSES against the GENERATED manifest"

# The generated manifest must carry the real accounting, not an empty shell.
assert_eq "FEAT-001" "$(jq -r '.["JOURNEY-101"].covers[0]' "$_mp/m.json")" \
  "mp-A3: journey covers are derived from the map"
assert_eq "AFJ-001"  "$(jq -r '.["JOURNEY-101"].flows[0]' "$_mp/m.json")" \
  "mp-A3: journey flows are derived from the map"
assert_eq "JOURNEY-101" "$(jq -r '._index["FEAT-001"].journeys[0]' "$_mp/m.json")" \
  "mp-A4: _index reverse-maps a covered FEAT to its journey"
assert_eq "FEAT-003" "$(jq -r '._index["FEAT-003"].gap' "$_mp/m.json")" \
  "mp-A5: _index records the APPROVED GAP for FEAT-003"
assert_eq "0" "$(jq -r '._index["FEAT-003"].journeys | length' "$_mp/m.json")" \
  "mp-A5: and credits it with zero journeys"
assert_eq "null" "$(jq -r '._index["FEAT-001"].gap' "$_mp/m.json")" \
  "mp-A6: a covered FEAT carries no gap"

# ══════════════════════════════════════════════════════════════════════════════
# B. DETERMINISM — identical inputs => byte-identical output, no timestamps.
# ══════════════════════════════════════════════════════════════════════════════
_gen "$_mp/d1.json"; _gen "$_mp/d2.json"
if cmp -s "$_mp/d1.json" "$_mp/d2.json"; then
  printf 'ok: %s\n' "mp-B1: two runs are BYTE-IDENTICAL"
else
  printf 'FAIL: %s\n' "mp-B1: two runs differ"; ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi
# No environment-dependent value may leak into the artifact.
_today=$(date +%Y)
assert_not_contains "$(cat "$_mp/d1.json")" "$_today" "mp-B2: no timestamp/year leaks into the manifest"
assert_not_contains "$(cat "$_mp/d1.json")" "/tmp"    "mp-B3: no filesystem path leaks into the manifest"
assert_not_contains "$(cat "$_mp/d1.json")" "$(whoami)" "mp-B4: no username leaks into the manifest"

# ══════════════════════════════════════════════════════════════════════════════
# C. PLAIN *and* CANONICALLY PREFIXED identifiers are both first-class.
#    The golden bundle, id-renamed FEAT-00N -> FEAT-AUD-10N and NOTHING else,
#    must produce the identical accounting.
# ══════════════════════════════════════════════════════════════════════════════
mkdir -p "$_mp/pfx"
for _f in PRD.md APP_FLOW.md JOURNEY_MAP.generated.md JOURNEY_COVERAGE_GAPS.md; do
  sed -e 's/FEAT-001/FEAT-AUD-101/g' -e 's/FEAT-002/FEAT-AUD-102/g' \
      -e 's/FEAT-003/FEAT-AUD-103/g' "$COV/$_f" > "$_mp/pfx/$_f"
done
_gen "$_mp/pfx.json" "$_mp/pfx"; _e=$?
assert_eq "0" "$_e" "mp-C1: producer accepts CANONICALLY PREFIXED ids (FEAT-AUD-101)"
assert_eq "FEAT-AUD-101" "$(jq -r '.["JOURNEY-101"].covers[0]' "$_mp/pfx.json")" \
  "mp-C2: and derives the prefixed id, not a truncation"
assert_eq "FEAT-AUD-103" "$(jq -r '._index["FEAT-AUD-103"].gap' "$_mp/pfx.json")" \
  "mp-C3: and gaps the prefixed id"
_o=$(_gate "$_mp/pfx.json" "$_mp/pfx"); _e=$?
assert_eq "0" "$_e" "mp-C4: the gate passes against the prefixed generated manifest"
# Prefix-invariance: the accounting must be the SAME SHAPE, not accidentally different.
assert_eq "$(jq -S '._index | length' "$_mp/m.json")" "$(jq -S '._index | length' "$_mp/pfx.json")" \
  "mp-C5: prefixed and plain bundles yield the same _index cardinality"

# ══════════════════════════════════════════════════════════════════════════════
# D. MANIFEST DRIFT — the committed artifact cannot be hand-edited.
# ══════════════════════════════════════════════════════════════════════════════
sh "$GEN" "$COV/PRD.md" "$COV/APP_FLOW.md" "$COV/JOURNEY_MAP.generated.md" \
          "$COV/JOURNEY_COVERAGE_GAPS.md" --check "$_mp/m.json" >/dev/null 2>&1
assert_eq "0" "$?" "mp-D1: drift check PASSES on a freshly generated manifest"

# THE anti-false-green case: hand-edit the manifest to fabricate coverage for the
# FEAT that is only gapped. Without the drift check this is exactly how a human
# makes a coverage gate go green by typing.
jq '.["JOURNEY-101"].covers = ["FEAT-001","FEAT-003"]
    | ._index["FEAT-003"] = {"journeys":["JOURNEY-101"],"gap":null}' \
  "$_mp/m.json" > "$_mp/forged.json"
sh "$GEN" "$COV/PRD.md" "$COV/APP_FLOW.md" "$COV/JOURNEY_MAP.generated.md" \
          "$COV/JOURNEY_COVERAGE_GAPS.md" --check "$_mp/forged.json" > "$_mp/drift.txt" 2>&1
assert_eq "1" "$?" "mp-D2: drift check REFUSES a hand-forged manifest"
assert_contains "$(cat "$_mp/drift.txt")" "MANIFEST_STALE" "mp-D2: and names MANIFEST_STALE"

# Drift on a merely REORDERED/reformatted manifest is still drift: the artifact
# is byte-compared, so no "cosmetic" edit can sneak in beside a real one.
jq -c '.' "$_mp/m.json" > "$_mp/compact.json"
sh "$GEN" "$COV/PRD.md" "$COV/APP_FLOW.md" "$COV/JOURNEY_MAP.generated.md" \
          "$COV/JOURNEY_COVERAGE_GAPS.md" --check "$_mp/compact.json" >/dev/null 2>&1
assert_eq "1" "$?" "mp-D3: drift check REFUSES a reformatted manifest (byte comparison)"

# A STALE manifest — the map gained a journey, the committed manifest did not.
sed 's/^covers:          FEAT-002/covers:          FEAT-002, FEAT-003/' \
  "$COV/JOURNEY_MAP.generated.md" > "$_mp/moved-map.md"
sh "$GEN" "$COV/PRD.md" "$COV/APP_FLOW.md" "$_mp/moved-map.md" \
          "$COV/JOURNEY_COVERAGE_GAPS.md" --check "$_mp/m.json" >/dev/null 2>&1
assert_eq "1" "$?" "mp-D4: a manifest stale w.r.t. a CHANGED journey map is refused"

# ══════════════════════════════════════════════════════════════════════════════
# E. FAIL CLOSED — the producer refuses rather than emit something a gate eats.
# ══════════════════════════════════════════════════════════════════════════════
# E1. missing required source file
sh "$GEN" "$COV/PRD.md" "$COV/APP_FLOW.md" "$_mp/nope.md" "$COV/JOURNEY_COVERAGE_GAPS.md" \
  > /dev/null 2>"$_mp/e1.txt"
assert_eq "1" "$?" "mp-E1: a missing source file fails closed"
assert_contains "$(cat "$_mp/e1.txt")" "MISSING_SOURCE" "mp-E1: and names MISSING_SOURCE"

# E2. malformed anchor — a FEAT block with no priority
awk '/^priority:/ && !done { done=1; next } { print }' "$COV/PRD.md" > "$_mp/noprio.md"
sh "$GEN" "$_mp/noprio.md" "$COV/APP_FLOW.md" "$COV/JOURNEY_MAP.generated.md" \
          "$COV/JOURNEY_COVERAGE_GAPS.md" > /dev/null 2>"$_mp/e2.txt"
assert_eq "1" "$?" "mp-E2: a FEAT with an unparseable priority fails closed"
assert_contains "$(cat "$_mp/e2.txt")" "PRD_PRIORITY_UNPARSEABLE" "mp-E2: and names it"

# E3. malformed anchor — a user-journey heading with no AFJ id
sed 's/^### AFJ-003.*/### A journey with no id/' "$COV/APP_FLOW.md" > "$_mp/unidded.md"
sh "$GEN" "$COV/PRD.md" "$_mp/unidded.md" "$COV/JOURNEY_MAP.generated.md" \
          "$COV/JOURNEY_COVERAGE_GAPS.md" > /dev/null 2>"$_mp/e3.txt"
assert_eq "1" "$?" "mp-E3: an un-id'd APP_FLOW journey heading fails closed"
assert_contains "$(cat "$_mp/e3.txt")" "APP_FLOW_UNIDDED" "mp-E3: and names it"

# E4. a feature mapped to an UNKNOWN journey / a journey mapped to an unknown id
sed 's/^covers:          FEAT-001/covers:          FEAT-999/' \
  "$COV/JOURNEY_MAP.generated.md" > "$_mp/unknown.md"
sh "$GEN" "$COV/PRD.md" "$COV/APP_FLOW.md" "$_mp/unknown.md" \
          "$COV/JOURNEY_COVERAGE_GAPS.md" > /dev/null 2>"$_mp/e4.txt"
assert_eq "1" "$?" "mp-E4: a journey covering an id absent from the PRD fails closed"
assert_contains "$(cat "$_mp/e4.txt")" "INVALID_SOURCE_ID" "mp-E4: and names INVALID_SOURCE_ID"
# ...it is REFUSED, never silently dropped — dropping it would quietly shrink the
# coverage claim until it happened to be true.
assert_not_contains "$(cat "$_mp/e4.txt")" "FEAT-001" "mp-E4: the unknown id is refused, not swapped"

# E5. DUPLICATE mappings — the same journey id declared twice
{ cat "$COV/JOURNEY_MAP.generated.md"; printf '\n## JOURNEY-101 — "a second block with the same id"\norigin:          DERIVED\ncovers:          FEAT-002\nflows:           AFJ-002\n'; } > "$_mp/dupj.md"
sh "$GEN" "$COV/PRD.md" "$COV/APP_FLOW.md" "$_mp/dupj.md" \
          "$COV/JOURNEY_COVERAGE_GAPS.md" > /dev/null 2>"$_mp/e5.txt"
assert_eq "1" "$?" "mp-E5: a duplicate JOURNEY-id fails closed"
assert_contains "$(cat "$_mp/e5.txt")" "DUPLICATE_JOURNEY_ID" "mp-E5: and names it"

# E6. DUPLICATE/conflicting gap records — one source id in two gap records
{ cat "$COV/JOURNEY_COVERAGE_GAPS.md"
  printf '\nsource_id:    FEAT-003\nsource_type:  FEAT\nreason:       a second, conflicting record for the same id\nowner:        alice\nexpires:      2027-01-01\nreviewer:     bob\n'; } > "$_mp/dupg.md"
sh "$GEN" "$COV/PRD.md" "$COV/APP_FLOW.md" "$COV/JOURNEY_MAP.generated.md" \
          "$_mp/dupg.md" > /dev/null 2>"$_mp/e6.txt"
assert_eq "1" "$?" "mp-E6: one source id in two gap records fails closed"
assert_contains "$(cat "$_mp/e6.txt")" "AMBIGUOUS_GAP" "mp-E6: and names AMBIGUOUS_GAP"

# E7. a MALFORMED gap record (missing owner) — the producer will not encode a
#     credit the gate is going to reject.
awk '/^owner:/ && !done { done=1; next } { print }' "$COV/JOURNEY_COVERAGE_GAPS.md" > "$_mp/badgap.md"
sh "$GEN" "$COV/PRD.md" "$COV/APP_FLOW.md" "$COV/JOURNEY_MAP.generated.md" \
          "$_mp/badgap.md" > /dev/null 2>"$_mp/e7.txt"
assert_eq "1" "$?" "mp-E7: a malformed gap record fails closed"
assert_contains "$(cat "$_mp/e7.txt")" "MALFORMED_GAP" "mp-E7: and names MALFORMED_GAP"

# E8. a gap naming an id that is not an anchor at all
{ printf 'source_id:    FEAT-777\nsource_type:  FEAT\nreason:       a gap for a feature that does not exist\nowner:        alice\nexpires:      2027-01-01\nreviewer:     bob\n'; } > "$_mp/ghostgap.md"
sh "$GEN" "$COV/PRD.md" "$COV/APP_FLOW.md" "$COV/JOURNEY_MAP.generated.md" \
          "$_mp/ghostgap.md" > /dev/null 2>"$_mp/e8.txt"
assert_eq "1" "$?" "mp-E8: a gap for a non-existent anchor fails closed"
assert_contains "$(cat "$_mp/e8.txt")" "INVALID_SOURCE_ID" "mp-E8: and names INVALID_SOURCE_ID"

# ══════════════════════════════════════════════════════════════════════════════
# F. MISSING MAPPINGS — the producer must NOT invent them.
#    Empty `flows:` means the AFJs are uncovered, and the gate must SAY SO.
#    This is the property that keeps the producer honest: it would be trivial to
#    infer flows from the 1:1 covers-set coincidence, and that inference would
#    manufacture coverage the project never declared.
# ══════════════════════════════════════════════════════════════════════════════
sed 's/^flows:           AFJ-00[0-9]/flows:/' "$COV/JOURNEY_MAP.generated.md" > "$_mp/noflows.md"
_n=$(grep -c '^flows:[[:space:]]*$' "$_mp/noflows.md")
assert_eq "2" "$_n" "mp-F0: (fixture) both journeys now have an empty flows: field"
sh "$GEN" "$COV/PRD.md" "$COV/APP_FLOW.md" "$_mp/noflows.md" \
          "$COV/JOURNEY_COVERAGE_GAPS.md" > "$_mp/noflows.json" 2>/dev/null
assert_eq "0" "$?" "mp-F1: an empty flows: field is not itself an error — it is a fact"
assert_eq "0" "$(jq -r '.["JOURNEY-101"].flows | length' "$_mp/noflows.json")" \
  "mp-F2: the producer records ZERO flows — it does not infer the AFJ mapping"
_o=$(sh "$CJC" "$COV/PRD.md" "$COV/APP_FLOW.md" "$_mp/noflows.md" "$_mp/noflows.json" \
                "$COV/JOURNEY_COVERAGE_GAPS.md" 2>&1); _e=$?
assert_eq "1" "$_e" "mp-F3: and the gate then FAILS on the uncovered AFJs"
assert_contains "$_o" "COVERAGE_GAP: AFJ" "mp-F3: naming the AFJ axis, not silently passing"
