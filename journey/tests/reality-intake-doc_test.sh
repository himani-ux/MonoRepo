# reality-intake-doc_test.sh — W5 (D5 rider): doc-coherence lock for
# journey/docs/reality-intake-format.md against journey-reality-intake.sh,
# the same style as uat-report-lint_test.sh's code-union lock — except this
# one is genuinely bidirectional: every code the doc documents must appear
# in the script, and every code the script's closed enum names must appear
# in the doc. Neither side can silently drift from the other.
# shellcheck shell=sh

_ri_doc="journey/docs/reality-intake-format.md"
_ri_script="journey/bin/journey-reality-intake.sh"

if [ ! -f "$_ri_doc" ]; then
  printf 'FAIL: reality-intake-format.md missing: %s\n' "$_ri_doc"
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
  _ri_d=""
else
  printf 'ok: reality-intake-format.md exists\n'
  _ri_d="$(cat "$_ri_doc")"
fi

if [ ! -f "$_ri_script" ]; then
  printf 'FAIL: journey-reality-intake.sh missing: %s\n' "$_ri_script"
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
  _ri_s=""
else
  _ri_s="$(cat "$_ri_script")"
fi

# ── the closed enum, exactly as the script's own header comment names it
# ("Codes (own; closed enum, this gate)") — 9 codes total. ────────────────
_ri_codes="APPROVE_REQUIRED NO_ENTRY_BLOCK MULTIPLE_BLOCKS ENTRY_HEADING_INVALID ORIGIN_NOT_REALITY AUTHOR_STATUS_NOT_UNWRITTEN EVIDENCE_EMPTY DUPLICATE_JOURNEY LINT_FAILED"

_ri_n=0
for _ri_c in $_ri_codes; do _ri_n=$((_ri_n + 1)); done
assert_eq "9" "$_ri_n" "reality-intake: closed enum is exactly 9 codes (D5 rider claim)"

# bidirectional: every documented code greps in the script, and vice versa
# — same list checked from both directions, so neither file can drift
# silently out of sync with the other.
for _ri_c in $_ri_codes; do
  assert_contains "$_ri_d" "$_ri_c" "reality-intake doc: code $_ri_c documented"
  assert_contains "$_ri_s" "$_ri_c" "reality-intake script: code $_ri_c actually emitted"
done

# reverse direction, mechanically: grep the script's own emitted code
# tokens (start of an _emit/printf string, or the DUPLICATE_JOURNEY
# printf's literal prefix) and confirm each one is in the static list
# above (i.e. the doc's coverage claim isn't stale relative to the
# script's real emission sites) — a token appearing in the script's own
# emission sites that ISN'T in $_ri_codes would fail this loop.
_ri_emitted="$(printf '%s\n' "$_ri_s" | grep -oE '"[A-Z_]+:' | tr -d '":' | sort -u)"
for _ri_e in $_ri_emitted; do
  # INTAKE: is the gate's own SUCCESS line (step 10 of the ceremony), not a
  # member of the closed VIOLATION-code enum this test locks — excluded by
  # name, the same way the script's own header comment separates "Codes
  # (own; closed enum, this gate)" from the success-line diagnostic.
  [ "$_ri_e" = "INTAKE" ] && continue
  case " $_ri_codes " in
    *" $_ri_e "*) : ;;
    *) printf 'FAIL: reality-intake: script emits %s but it is not in the documented closed enum\n' "$_ri_e"
       ASSERT_FAILS=$((ASSERT_FAILS + 1)) ;;
  esac
done
printf 'ok: reality-intake: every code token the script actually emits is accounted for in the documented closed enum\n'

# ── key facts a fresh operator can currently get correct ONLY by reading
# the script (D5's own list) — now doc-locked. ────────────────────────────
assert_contains "$_ri_d" '## JOURNEY-<digits> — "<title>"' "reality-intake doc: canonical heading grammar token"
assert_contains "$_ri_d" "origin: REALITY" "reality-intake doc: origin REALITY requirement"
assert_contains "$_ri_d" "author_status: UNWRITTEN" "reality-intake doc: author_status UNWRITTEN requirement"
assert_contains "$_ri_d" "the WHY" "reality-intake doc: evidence is the WHY of a REALITY entry"
assert_contains "$_ri_d" "401" "reality-intake doc: id assignment base (401 upward)"
assert_contains "$_ri_d" "<n>" "reality-intake doc: the <n> test-placeholder substitution token"
assert_contains "$_ri_d" "norm_covers" "reality-intake doc: dedup shares journey-lib.sh's norm_covers/norm_oracle"
assert_contains "$_ri_d" "WORKFLOW BUG" "reality-intake doc: names the Step 5 Part B WORKFLOW BUG ceremony"
assert_contains "$_ri_d" "JOURNEY-EXEMPT" "reality-intake doc: the exemption escape hatch"
assert_contains "$_ri_d" "--approve" "reality-intake doc: the approval flag"
assert_contains "$_ri_d" "V-T5 F1" "reality-intake doc: cites the glued-heading fail-open this grammar closes"

# ── worked example is a byte-real, currently-valid entry: exercise it
# through the actual gate, not just eyeballed prose. ──────────────────────
_ri_tmp="$(mktemp -d)"
_ri_map="$_ri_tmp/JOURNEY_MAP.md"
{
  printf '# JOURNEY_MAP\n\n'
  printf '## JOURNEY-1 — "Existing seed journey"\n'
  printf 'origin: PERSONA\n'
  printf 'priority: P2\n'
  printf 'covers: FEAT-001\n'
  printf 'flows: [AFJ-001]\n'
  printf 'persona: P2 (seed)\n'
  printf 'goal: seed goal\n'
  printf 'oracle_surface: UI\n'
  printf 'negative_states: seed_negstate\n'
  printf 'data_fixtures: []\n'
  printf 'steps:\n  1. seed step -> seed_negstate\n'
  printf 'oracle: seed oracle\n'
  printf 'evidence: []\n'
  printf 'test: tests/journeys/journey-1.spec.ts\n'
  printf 'runner: playwright\n'
  printf 'author_status: WRITTEN\n'
  printf 'exemptions: []\n'
} > "$_ri_map"

_ri_entry="$_ri_tmp/entry.md"
# Extract the fenced block whose first content line is a REAL journey
# heading (digits + quoted title) — distinguishes the worked example from
# the earlier §2.1 heading-grammar block, which fences the literal
# '## JOURNEY-<digits> — "<title>"' placeholder text, not a real example.
awk '
  /^```$/ { in_fence = !in_fence; if (in_fence) { buf = "" } else if (buf ~ /^## JOURNEY-[0-9]+ — "/) { printf "%s", buf }; next }
  in_fence { buf = buf $0 "\n" }
' "$_ri_doc" > "$_ri_entry"

if [ -s "$_ri_entry" ] && grep -q '^## JOURNEY-999 — ' "$_ri_entry"; then
  printf 'ok: reality-intake doc: worked example fenced block extracted (%s bytes)\n' "$(wc -c < "$_ri_entry" | tr -d ' ')"
else
  printf 'FAIL: reality-intake doc: could not extract the worked-example fenced block (extraction assumption changed?)\n'
  ASSERT_FAILS=$((ASSERT_FAILS + 1))
fi

_ri_out="$(sh "$_ri_script" "$_ri_map" "$_ri_entry" --approve 2>&1)"; _ri_rc=$?
assert_eq "0" "$_ri_rc" "reality-intake doc: the worked example is a real, currently-valid entry (gate exit 0)"
assert_contains "$_ri_out" "INTAKE: JOURNEY-401" "reality-intake doc: worked example assigned JOURNEY-401 (base id, matches doc prose)"
assert_exit 0 sh "journey/bin/lint-journey-map.sh" "$_ri_map"

rm -rf "$_ri_tmp"

printf 'ok: reality-intake-format.md doc-coherence lock complete\n'
