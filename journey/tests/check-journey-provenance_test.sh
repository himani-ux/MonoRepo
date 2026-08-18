# shellcheck shell=sh
# check-journey-provenance_test.sh — deterministic PROVENANCE gate proofs.
#
# Post-merge review, highest-leverage rec: the manifest already carries
# verbatim field_sources quotes and AC refs — verify them deterministically.
# Where transfer is verbatim, verification is string equality:
#   * every field_sources quote must ground verbatim (fragment-wise) in the
#     doc its `from` names;
#   * every AC-<n> declared by a covered FEAT must appear in that journey's
#     oracle manifest entry (ref or quote).
# This demotes the refuter from last-line-of-defense to second opinion on the
# oracle-dilution class.

. "$(dirname "$0")/assert.sh"

TESTS_DIR="$(cd "$(dirname "$0")" && pwd)"
PROV="$TESTS_DIR/../bin/check-journey-provenance.sh"
FX="$TESTS_DIR/fixtures/gen"
G="$FX/golden"
ADV="$FX/adversarial/diluted-oracle"

_pv_nonzero() { # ACTUAL MSG
  if [ "$1" -ne 0 ]; then printf 'ok: %s\n' "$2"; else
    printf 'FAIL: %s (expected non-zero exit, got 0)\n' "$2"
    ASSERT_FAILS=$((ASSERT_FAILS + 1)); fi
}

# ── prov-1: golden manifest is fully grounded → exit 0 ────────────────────────
_e=$(sh "$PROV" "$FX/PRD.md" "$FX/APP_FLOW.md" \
  "$G/expected-journey-map.generated.md" "$G/expected-coverage-manifest.json" \
  "$FX/SSOT.md" 2>&1); _ec=$?
assert_eq 0 "$_ec" "prov-1: golden manifest passes provenance (exit 0)"
assert_eq "" "$_e" "prov-1: no violations reported on the golden"

# ── prov-2: THE adversarial case — diluted oracle caught DETERMINISTICALLY ───
# The diluted-oracle fixture is lint-clean and coverage-complete by design;
# pre-gate it was catchable only by the refuter (a model). AC-2 of FEAT-001 is
# declared in the PRD but absent from JOURNEY-101's oracle manifest entry.
_e=$(sh "$PROV" "$FX/PRD.md" "$FX/APP_FLOW.md" \
  "$ADV/JOURNEY_MAP.generated.md" "$ADV/JOURNEY_COVERAGE_MANIFEST.json" \
  "$FX/SSOT.md" 2>&1 >/dev/null); _ec=$?
_pv_nonzero "$_ec" "prov-2: diluted oracle FAILS provenance deterministically"
assert_contains "$_e" "AC_DROPPED" "prov-2: violation class is AC_DROPPED"
assert_contains "$_e" "AC-2"       "prov-2: names the dropped criterion AC-2"
assert_contains "$_e" "JOURNEY-101" "prov-2: names the diluting journey"

# ── prov-3: fabricated quote (not in any source doc) → QUOTE_UNGROUNDED ──────
_t=$(mktemp -d)
jq '.["JOURNEY-101"].field_sources.goal.quote = "The system guarantees five nines of uptime."' \
  "$G/expected-coverage-manifest.json" > "$_t/man.json"
_e=$(sh "$PROV" "$FX/PRD.md" "$FX/APP_FLOW.md" \
  "$G/expected-journey-map.generated.md" "$_t/man.json" "$FX/SSOT.md" 2>&1 >/dev/null); _ec=$?
_pv_nonzero "$_ec" "prov-3: fabricated quote fails provenance"
assert_contains "$_e" "QUOTE_UNGROUNDED" "prov-3: violation class is QUOTE_UNGROUNDED"

# ── prov-4: elided quote grounds fragment-wise, PARAPHRASE does not ───────────
jq '.["JOURNEY-101"].field_sources.steps.quote = "arrive at the invoices page ... observe status=ACCEPTED in the invoice list"' \
  "$G/expected-coverage-manifest.json" > "$_t/man4.json"
_e=$(sh "$PROV" "$FX/PRD.md" "$FX/APP_FLOW.md" \
  "$G/expected-journey-map.generated.md" "$_t/man4.json" "$FX/SSOT.md" 2>&1 >/dev/null); _ec=$?
_pv_nonzero "$_ec" "prov-4: paraphrased fragment (not verbatim) fails provenance"
assert_contains "$_e" "QUOTE_UNGROUNDED" "prov-4: paraphrase reported as QUOTE_UNGROUNDED"

# ── prov-5: map journey with no manifest provenance → MISSING_PROVENANCE ─────
jq 'del(.["JOURNEY-102"])' "$G/expected-coverage-manifest.json" > "$_t/man5.json"
_e=$(sh "$PROV" "$FX/PRD.md" "$FX/APP_FLOW.md" \
  "$G/expected-journey-map.generated.md" "$_t/man5.json" "$FX/SSOT.md" 2>&1 >/dev/null); _ec=$?
_pv_nonzero "$_ec" "prov-5: journey without a manifest entry fails"
assert_contains "$_e" "MISSING_PROVENANCE" "prov-5: violation class is MISSING_PROVENANCE"

# ── prov-6: oracle entry without a quote → MISSING_PROVENANCE ─────────────────
jq 'del(.["JOURNEY-101"].field_sources.oracle.quote)' \
  "$G/expected-coverage-manifest.json" > "$_t/man6.json"
_e=$(sh "$PROV" "$FX/PRD.md" "$FX/APP_FLOW.md" \
  "$G/expected-journey-map.generated.md" "$_t/man6.json" "$FX/SSOT.md" 2>&1 >/dev/null); _ec=$?
_pv_nonzero "$_ec" "prov-6: oracle without a verbatim quote fails"
assert_contains "$_e" "MISSING_PROVENANCE" "prov-6: quoteless oracle is MISSING_PROVENANCE"

# ── prov-7: unknown `from` doc → BAD_SOURCE (fail closed) ─────────────────────
jq '.["JOURNEY-101"].field_sources.goal.from = "WIKI"' \
  "$G/expected-coverage-manifest.json" > "$_t/man7.json"
_e=$(sh "$PROV" "$FX/PRD.md" "$FX/APP_FLOW.md" \
  "$G/expected-journey-map.generated.md" "$_t/man7.json" "$FX/SSOT.md" 2>&1 >/dev/null); _ec=$?
_pv_nonzero "$_ec" "prov-7: unknown from-doc fails closed"
assert_contains "$_e" "BAD_SOURCE" "prov-7: violation class is BAD_SOURCE"

# ── prov-8: SSOT-sourced quote without SSOT arg → fail closed ─────────────────
jq '.["JOURNEY-101"].field_sources.persona.quote = "A back-office ops user who processes uploaded documents day to day."' \
  "$G/expected-coverage-manifest.json" > "$_t/man8.json"
_e=$(sh "$PROV" "$FX/PRD.md" "$FX/APP_FLOW.md" \
  "$G/expected-journey-map.generated.md" "$_t/man8.json" 2>&1 >/dev/null); _ec=$?
_pv_nonzero "$_ec" "prov-8: SSOT quote unverifiable without SSOT (fail closed)"
# same manifest WITH the SSOT provided verifies fine
_e=$(sh "$PROV" "$FX/PRD.md" "$FX/APP_FLOW.md" \
  "$G/expected-journey-map.generated.md" "$_t/man8.json" "$FX/SSOT.md" 2>&1 >/dev/null); _ec=$?
assert_eq 0 "$_ec" "prov-8: same SSOT quote verifies when the SSOT is provided"

rm -rf "$_t"
