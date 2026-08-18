#!/bin/sh
# check-extraction-coverage.sh MANIFEST EXTRACTED [GAPS] — gate E3
# (spec §4.3/§7.3/§8, §14 Q3).
#
# The MANIFEST consumer chain (B5, I5): Step 0's MANIFEST.md machine block
# is the single deterministic bridge between Stage 4b's model output and the
# journey layer. This gate re-derives the manifest's anchors itself (never
# trusts a candidate's own claims about what exists) and proves, fail-closed,
# that nothing was silently dropped between "the codebase has this many
# behavior-bearing FEATs / flow-bearing screens" and "the staging file
# accounts for every one of them, or explicitly gaps it". Coverage is
# accounting, not fidelity (doc-derived lesson, restated here): this gate
# never judges whether a staged candidate is a GOOD reverse-engineering of a
# journey — that is the human confirmation step's job. It only proves the
# manifest's anchors and the staging file's anchors agree.
#
# ── Composition ─────────────────────────────────────────────────────────
# Composes lint-journey-extracted.sh EXTRACTED FIRST, as an executable
# (never reimplemented) — schema grammar is that gate's job; a non-zero
# lint exit is reported as LINT_FAILED and this gate stops. LINT_FAILED is
# NOT one of spec §7.3's enum members — it is the same house
# composition-idiom pass-through code check-uat-preconditions.sh and
# check-extracted-provenance.sh (task E2) both use.
#
# ── The chain: four fail-closed stages, in order (spec §8) ────────────────
# Each stage is a hard gate over the one before it: a stage that finds any
# violation accumulates ALL of that stage's violations (fail-slow within
# the stage, house rule 2 — never `| while read`, a pipeline subshell loses
# counter mutations) and then halts the run — later stages never run against
# data an earlier stage has already proven untrustworthy.
#
#   (1) PARSE — MANIFEST.md exists and carries a well-formed
#       `EXTRACTION-MANIFEST BEGIN`/`END` block:
#         MANIFEST_MISSING        — MANIFEST does not exist as a file
#                                    (this is a CHAIN code, exit 1 — NOT a
#                                    caller/usage error like a missing
#                                    EXTRACTED or GAPS path below. A brand
#                                    new project legitimately has no
#                                    MANIFEST.md yet; the chain must name
#                                    that as its own deterministic state,
#                                    not a shell usage mistake)
#         MANIFEST_BLOCK_MISSING  — MANIFEST exists but no BEGIN/END block
#         MANIFEST_BLOCK_AMBIGUOUS — more than one complete BEGIN/END block
#                                    (or stray surplus delimiter lines): a
#                                    first-END-wins extractor would silently
#                                    parse only block 1 and let block 2's
#                                    anchors escape accounting (V-E3 F1;
#                                    append-only §7.3 addition — §8's prose
#                                    names the ambiguity class, the draft
#                                    enum assigned it no code)
#         MANIFEST_FORMAT         — any non-blank line inside the block
#                                    violating the fixed grammar: exactly
#                                    one `manifest_version: <value>` line,
#                                    exactly one `extraction_commit: <40-hex>`
#                                    line, and zero or more `feat:`/
#                                    `screen:`/`e2e_test:` lines with
#                                    pipe-delimited FIXED keys (never a
#                                    freeform key set). Every VALUE matches
#                                    `^[A-Za-z0-9._/:=,-]+$` (spec §4.1) —
#                                    no whitespace, no `|` inside a value.
#                                    `behaviors=`/`states_filled=` are
#                                    additionally constrained to
#                                    `[0-9]+` (needed for the `>=1`
#                                    completeness comparison in stage 4 to
#                                    be well-defined; still the same code).
#                                    One `MANIFEST_FORMAT` line per
#                                    offending manifest line (fail-slow).
#   (2) SOUNDNESS — internally consistent:
#         MANIFEST_DUPLICATE      — a feat id / screen id / e2e_test path
#                                    repeats within the block (one message
#                                    per duplicate, fail-slow), OR a token
#                                    appears in MORE THAN ONE namespace
#                                    (feat/screen/e2e_test — V-E3 F3: a
#                                    cross-namespace collision would let
#                                    one staging token credit two required
#                                    anchors; same code, its own
#                                    cross-namespace message)
#         MANIFEST_COMMIT_MISMATCH — the block's `extraction_commit:` does
#                                    not equal EXTRACTED's own header
#                                    `extraction_commit:`
#   (3) FRESHNESS — EXTRACTED's `manifest_sha256:` header must equal the
#       CURRENT sha256 of the manifest's machine block (the exact bytes
#       from the `EXTRACTION-MANIFEST BEGIN` line through the
#       `EXTRACTION-MANIFEST END` line, inclusive — same definition as
#       journey/docs/journey-extracted-format.md §3.1's "sha256 of
#       MANIFEST.md's machine block", NOT the whole file):
#         EXTRACTION_STALE        — sha mismatch; re-stage
#         TOOL_MISSING             — no sha256sum/shasum on PATH
#   (4) COMPLETENESS — both directions (the B5 core):
#         ANCHOR_TOKEN_INVALID: EXTRACTED-<n>: <token> — a staging covers:/
#           flows: token failing the `^[A-Za-z0-9._-]+$` whitelist, checked
#           BEFORE any membership test (V-E3 F2, L22
#           whitelist-before-use; name and class precedented by
#           journey/bin/author-bundle.sh's identical code from the T4c
#           wave; append-only §7.3 addition). Paired with `set -f` around
#           the token loops so a glob character in a staging value can
#           never pathname-expand against the caller's cwd into a false
#           coverage credit.
#         UNKNOWN_ANCHOR: EXTRACTED-<n>: <token> — an entry's covers: or
#           flows: token (comma-split, exact-match, never substring — Q6
#           spirit) does not exist anywhere in the manifest. covers: tokens
#           are checked against the union of feat: ids AND screen: ids
#           (staging entries may legitimately still be screen-anchored
#           pre-confirmation, spec §9.5). flows: tokens are checked against
#           the union of every screen's declared `flows=` values. `[]` is
#           the empty-list sentinel and contributes ZERO tokens in either
#           direction (L20: an empty list means NO anchors, never ALL).
#         MISSING_EXTRACTION: <anchor> — every `feat:` line with
#           `behaviors>=1`, and every `screen:` line that DOES declare a
#           `flows=` value, must be accounted for by >=1 staged entry
#           (checked across ALL entries regardless of
#           confirmation_status — REJECTED and promoted_as-stamped
#           terminal entries still count as "this anchor was
#           extraction-attempted", spec §14 Q7's "terminal entries still
#           integrity-checked" — this is accounting, not a quality
#           judgment) OR by a valid, unexpired gap entry (only when GAPS
#           was given).
#
#           THE FLOWS-MEMBERSHIP DESIGN (this gate's own reading of spec
#           §4.3's "covers/flows membership" parenthetical, decided here
#           because the design spec leaves the exact mechanics open): a
#           FEAT anchor is covered iff some entry's `covers:` set contains
#           that FEAT id (flows: values are AFJ-shaped and a FEAT id can
#           never legitimately appear there, but the membership test itself
#           is symmetric/harmless to run against both pools). A SCREEN
#           anchor (one that declares `flows=`) is covered EITHER (a)
#           directly — some entry's `covers:` set contains the screen's own
#           id (the "screen-anchored covers entry credits a screen" case,
#           spec §9.5) — OR (b) indirectly — some entry's `flows:` set
#           contains ANY one of that screen's declared `flows=` tokens (an
#           entry that flows through one of a screen's AFJ ids has, by
#           construction, exercised that screen, even without naming the
#           screen id in its own `covers:`). Both paths are proven against
#           the golden coverage fixture in the test suite (path (a) via a
#           screen-anchored-covers-only entry; path (b) via a
#           flows-token-only entry, no covers: token naming that screen at
#           all).
#
#           GAPS credit (spec §14 Q3 — the EXTRACTED_GAPS.md own artifact,
#           SAME grammar and SAME date-comparison mechanics as
#           journey/bin/check-persona-coverage.sh's PERSONA_COVERAGE_GAPS.md
#           precedent — the gaps-artifact this gate INHERITS, not
#           reinvents): entries carry `source_id:` / `source_type:` (FEAT |
#           SCREEN — the persona precedent hardcodes FEAT only because
#           persona coverage only ever gaps FEATs; this gate's anchors span
#           both feat and flow-bearing-screen anchors, so the enum is
#           widened, append-only, no other mechanic changed) /
#           `reason:` / `owner:` / `reviewer:` / `expires: YYYY-MM-DD`.
#           `expires:` is compared to today via the IDENTICAL string
#           comparison check-persona-coverage.sh uses
#           (`[ "$_gex" \< "$_today" ]` — YYYY-MM-DD sorts lexically) — no
#           second duration literal, no EXTRACTED-specific expiry config
#           (Q3, binding). The expiry date itself is set at FIRST staging
#           and must survive re-staging unchanged — that write-time
#           discipline is `journey-extracted-stage.sh`'s job (task E4, not
#           yet built); this gate only reads and compares whatever
#           `expires:` value is present at run time.
#             GAP_FORMAT   — malformed record: bad source_type, a blank
#                            reason/owner/reviewer, or expires: not
#                            YYYY-MM-DD shaped
#             GAP_EXPIRED  — well-formed but expires before today; an
#                            expired gap is not a coverage credit (same
#                            wording, same semantics as
#                            PERSONA_COVERAGE_GAP's GAP_EXPIRED)
#             NO_GAP_ENTRIES — anti-vacuous append (append-only enum
#                            addition, same precedent as task E2's
#                            PRIOR_E2E_MISSING/NO_SOURCE_LINES additions to
#                            spec §7.2's draft): a GAPS arg was explicitly
#                            given but the file declares ZERO gap records.
#                            RATIONALE: unlike check-persona-coverage.sh
#                            (where a MISSING gaps file silently means zero
#                            gaps — a project that has never needed one
#                            never has to create one), this gate's GAPS arg
#                            is OPTIONAL and its presence is a project's own
#                            deliberate declaration "I keep gap entries
#                            here". A file that exists, was explicitly
#                            passed, and carries no entries at all is
#                            indistinguishable from a forgotten/emptied
#                            file — an anti-vacuous state exactly like an
#                            empty JOURNEY_EXTRACTED.md
#                            (NO_EXTRACTED_ENTRIES) or an empty
#                            PRD/SSOT (NO_ANCHORS): loud failure, not a
#                            silent "0 gaps, nothing to check" pass. When
#                            the GAPS arg is omitted entirely, this code
#                            never fires — gap credit is simply
#                            unavailable, and every otherwise-uncovered
#                            anchor fails as a plain MISSING_EXTRACTION.
#
# No temp files are used anywhere in this gate (pure shell variables +
# command substitution, the same no-mktemp style lint-journey-extracted.sh
# uses) — so MKTEMP_FAILED is deliberately NOT shipped (task instruction:
# ship it only if temps are used).
#
# ── Usage / argument handling ──────────────────────────────────────────
# MANIFEST and EXTRACTED are required positional args; GAPS is an optional
# third arg (a project that keeps EXTRACTED_GAPS.md entries passes its
# path here). Wrong arg count, a missing/unreadable EXTRACTED file, or a
# GAPS path that was GIVEN but does not exist, are all caller/usage errors
# — exit 2, this gate's OWN message (same "missing-files exit 2" symmetry
# check-extracted-provenance.sh (task E2) applies to its EXTRACTED/
# REPO_ROOT args). MANIFEST's absence is deliberately NOT in this exit-2
# class — see MANIFEST_MISSING above.
#
# ── Codes (closed enum, 15 total) ──────────────────────────────────────
#   LINT_FAILED (pass-through, not a schema code)
#   MANIFEST_MISSING  MANIFEST_BLOCK_MISSING  MANIFEST_BLOCK_AMBIGUOUS
#   MANIFEST_FORMAT  MANIFEST_DUPLICATE  MANIFEST_COMMIT_MISMATCH
#   EXTRACTION_STALE
#   ANCHOR_TOKEN_INVALID  UNKNOWN_ANCHOR  MISSING_EXTRACTION
#   GAP_FORMAT  GAP_EXPIRED  NO_GAP_ENTRIES
#   TOOL_MISSING
#
# Usage / missing EXTRACTED / missing (but given) GAPS: exit 2.
# Any chain violation: exit 1, CODE: message to stderr, fail-slow within
# each stage (never fail-fast mid-stage; house rule 2). Success: one
# summary line (anchors checked, entries checked, gaps credited), exit 0.
#
# Deps: POSIX sh, awk, grep, sed, sort, date, sha256sum|shasum.
# shellcheck shell=sh

set -u

_here="$(cd "$(dirname "$0")" && pwd)"
LIB_JOURNEY="$_here/../lib/journey-lib.sh"

usage() { printf 'Usage: check-extraction-coverage.sh MANIFEST EXTRACTED [GAPS]\n' >&2; exit 2; }
[ $# -eq 2 ] || [ $# -eq 3 ] || usage

MANIFEST="$1"
EXTRACTED="$2"
GAPS="${3:-}"

[ -f "$EXTRACTED" ] || {
  printf 'check-extraction-coverage: file not found: %s\n' "$EXTRACTED" >&2
  exit 2
}
if [ -n "$GAPS" ]; then
  [ -f "$GAPS" ] || {
    printf 'check-extraction-coverage: file not found: %s\n' "$GAPS" >&2
    exit 2
  }
fi

# ── compose lint-journey-extracted.sh FIRST — grammar is its job, not ours ─
/bin/sh "$_here/lint-journey-extracted.sh" "$EXTRACTED"
if [ $? -ne 0 ]; then
  printf 'LINT_FAILED: staging file failed lint-journey-extracted.sh\n' >&2
  exit 1
fi

JOURNEY_EXTRACTED="$EXTRACTED"
export JOURNEY_EXTRACTED
# shellcheck disable=SC1090
. "$LIB_JOURNEY"

problems=0
_p() { printf '%s\n' "$1" >&2; problems=$((problems + 1)); }

# split STRING into one non-empty, non-"[]" comma-separated token per line
# ("[]" is the empty-list sentinel — L20: it must mean NO tokens, never a
# token that could ever match anything).
_ec_tokens() {
  printf '%s\n' "$1" | awk -F',' '{
    for (i = 1; i <= NF; i++) {
      t = $i
      gsub(/^[ \t]+|[ \t]+$/, "", t)
      if (t != "" && t != "[]") print t
    }
  }'
}

# ════════════════════════════════════════════════════════════════════════
# STAGE 1 — parse: MANIFEST exists, block exists, every line grammar-valid
# ════════════════════════════════════════════════════════════════════════

[ -f "$MANIFEST" ] || {
  printf 'MANIFEST_MISSING: %s does not exist\n' "$MANIFEST" >&2
  exit 1
}

# ── block cardinality FIRST (V-E3 F1): a first-END-wins extractor over a
# manifest carrying TWO complete blocks silently parses only block 1 —
# block 2's behavior-bearing anchors escape the completeness accounting
# entirely at exit 0 (the exact B5 "ambiguous manifest input" class spec §8
# says must halt with a distinct code). Count complete BEGIN..END pairs and
# raw delimiter lines BEFORE extracting anything; anything other than
# exactly one complete block with exactly one BEGIN and one END delimiter
# line is MANIFEST_BLOCK_AMBIGUOUS — an append-only addition to spec §7.3's
# drafted enum (§8's prose names the ambiguity class but the draft assigned
# it no code; appended per the same precedent as E2's PRIOR_E2E_MISSING/
# NO_SOURCE_LINES and this gate's own NO_GAP_ENTRIES). A surplus BEGIN
# beyond the complete-pair count is the same class (a second, unclosed
# block whose content escapes accounting); a surplus stray END is rejected
# too — fail closed on structure this gate cannot prove it parsed
# completely.
_n_begin="$(grep -c '^EXTRACTION-MANIFEST BEGIN$' "$MANIFEST")"
_n_end="$(grep -c '^EXTRACTION-MANIFEST END$' "$MANIFEST")"
_n_blocks="$(awk '
  /^EXTRACTION-MANIFEST BEGIN$/ { if (!inblk) inblk = 1; next }
  /^EXTRACTION-MANIFEST END$/   { if (inblk) { blocks++; inblk = 0 }; next }
  END { print blocks + 0 }
' "$MANIFEST")"
if [ "$_n_blocks" -eq 0 ]; then
  printf 'MANIFEST_BLOCK_MISSING: no EXTRACTION-MANIFEST BEGIN/END block found in %s\n' "$MANIFEST" >&2
  exit 1
fi
if [ "$_n_blocks" -ne 1 ] || [ "$_n_begin" -ne 1 ] || [ "$_n_end" -ne 1 ]; then
  printf 'MANIFEST_BLOCK_AMBIGUOUS: %s blocks found (exactly one required; %s BEGIN / %s END delimiter lines in %s)\n' \
    "$_n_blocks" "$_n_begin" "$_n_end" "$MANIFEST" >&2
  exit 1
fi

_block="$(awk '
  /^EXTRACTION-MANIFEST BEGIN$/ { inblk = 1; print; next }
  /^EXTRACTION-MANIFEST END$/   { if (inblk) print; exit }
  inblk { print }
' "$MANIFEST")"

_mf_version_count=0
_mf_commit_count=0
while IFS= read -r _mline; do
  case "$_mline" in
    'EXTRACTION-MANIFEST BEGIN' | 'EXTRACTION-MANIFEST END' | '') continue ;;
  esac
  case "$_mline" in
    manifest_version:\ *)
      _mf_version_count=$((_mf_version_count + 1))
      printf '%s\n' "$_mline" | grep -qE '^manifest_version: [A-Za-z0-9._/:=,-]+$' \
        || _p "MANIFEST_FORMAT: $_mline"
      ;;
    extraction_commit:\ *)
      _mf_commit_count=$((_mf_commit_count + 1))
      printf '%s\n' "$_mline" | grep -qE '^extraction_commit: [0-9a-f]{40}$' \
        || _p "MANIFEST_FORMAT: $_mline (extraction_commit must be exactly 40 lowercase hex characters)"
      ;;
    feat:\ *)
      printf '%s\n' "$_mline" | grep -qE '^feat: [A-Za-z0-9._/:=,-]+ \| behaviors=[0-9]+ \| states_filled=[0-9]+ \| grade_counts=[A-Za-z0-9._/:=,-]+$' \
        || _p "MANIFEST_FORMAT: $_mline"
      ;;
    screen:\ *)
      printf '%s\n' "$_mline" | grep -qE '^screen: [A-Za-z0-9._/:=,-]+ \| route=[A-Za-z0-9._/:=,-]+( \| flows=[A-Za-z0-9._/:=,-]+)?$' \
        || _p "MANIFEST_FORMAT: $_mline"
      ;;
    e2e_test:\ *)
      printf '%s\n' "$_mline" | grep -qE '^e2e_test: [A-Za-z0-9._/:=,-]+ \| framework=[A-Za-z0-9._/:=,-]+$' \
        || _p "MANIFEST_FORMAT: $_mline"
      ;;
    *)
      _p "MANIFEST_FORMAT: unrecognized line inside the manifest block: $_mline"
      ;;
  esac
done <<MF_EOF
$_block
MF_EOF

[ "$_mf_version_count" -eq 1 ] \
  || _p "MANIFEST_FORMAT: manifest_version: header line must appear exactly once (found $_mf_version_count)"
[ "$_mf_commit_count" -eq 1 ] \
  || _p "MANIFEST_FORMAT: extraction_commit: header line must appear exactly once (found $_mf_commit_count)"

if [ "$problems" -gt 0 ]; then
  printf 'check-extraction-coverage: %d problem(s) in stage 1 (parse) — fail closed\n' "$problems" >&2
  exit 1
fi

# ════════════════════════════════════════════════════════════════════════
# STAGE 2 — soundness: no duplicate anchors, commit matches EXTRACTED
# ════════════════════════════════════════════════════════════════════════

_rows="$(awk '
  /^feat: / {
    line = $0; sub(/^feat: /, "", line)
    n = split(line, f, / \| /)
    beh = f[2]; sub(/^behaviors=/, "", beh)
    printf "FEAT\t%s\t%s\n", f[1], beh
    next
  }
  /^screen: / {
    line = $0; sub(/^screen: /, "", line)
    n = split(line, f, / \| /)
    flows = ""
    if (n >= 3) { flows = f[3]; sub(/^flows=/, "", flows) }
    printf "SCREEN\t%s\t%s\n", f[1], flows
    next
  }
  /^e2e_test: / {
    line = $0; sub(/^e2e_test: /, "", line)
    n = split(line, f, / \| /)
    printf "E2E\t%s\n", f[1]
    next
  }
' <<ROWS_EOF
$_block
ROWS_EOF
)"

_all_feat_ids="$(printf '%s\n' "$_rows" | awk -F'\t' '$1=="FEAT"{print $2}')"
_feat_req_ids="$(printf '%s\n' "$_rows" | awk -F'\t' '$1=="FEAT" && ($3+0)>=1{print $2}')"
_all_screen_ids="$(printf '%s\n' "$_rows" | awk -F'\t' '$1=="SCREEN"{print $2}')"
_screen_req_rows="$(printf '%s\n' "$_rows" | awk -F'\t' '$1=="SCREEN" && $3!=""{print $2"\t"$3}')"
_all_e2e_paths="$(printf '%s\n' "$_rows" | awk -F'\t' '$1=="E2E"{print $2}')"

for _d in $(printf '%s\n' "$_all_feat_ids" | sort | uniq -d); do
  [ -n "$_d" ] && _p "MANIFEST_DUPLICATE: feat $_d appears more than once in the manifest block"
done
for _d in $(printf '%s\n' "$_all_screen_ids" | sort | uniq -d); do
  [ -n "$_d" ] && _p "MANIFEST_DUPLICATE: screen $_d appears more than once in the manifest block"
done
for _d in $(printf '%s\n' "$_all_e2e_paths" | sort | uniq -d); do
  [ -n "$_d" ] && _p "MANIFEST_DUPLICATE: e2e_test $_d appears more than once in the manifest block"
done

# ── cross-NAMESPACE collision (V-E3 F3): the per-kind loops above dedup
# within each namespace only — a token byte-identical as BOTH a feat: id
# and a screen: id would otherwise be accepted and let ONE staging covers:
# token credit TWO required anchors in stage 4 (a one-token-two-credits
# accounting fail-open, the B5 "ambiguous" class again). Each kind's id
# list is sort -u'd FIRST so an intra-kind duplicate (already reported
# above, its own message) cannot double-fire here — this loop reports only
# genuinely cross-namespace repeats. Same MANIFEST_DUPLICATE code, its own
# message shape.
for _d in $(printf '%s\n%s\n%s\n' \
    "$(printf '%s\n' "$_all_feat_ids" | sort -u)" \
    "$(printf '%s\n' "$_all_screen_ids" | sort -u)" \
    "$(printf '%s\n' "$_all_e2e_paths" | sort -u)" \
    | grep -v '^$' | sort | uniq -d); do
  [ -n "$_d" ] && _p "MANIFEST_DUPLICATE: $_d appears in more than one namespace (feat/screen/e2e_test) — a cross-namespace anchor collision lets one staging token credit two required anchors"
done

_mf_commit="$(printf '%s\n' "$_block" | awk '/^extraction_commit:/{sub(/^extraction_commit:[ \t]*/,""); print; exit}')"
_extracted_header="$(awk '/^## EXTRACTED-/{exit} {print}' "$EXTRACTED")"
_ext_commit="$(printf '%s\n' "$_extracted_header" | awk '/^extraction_commit:/{sub(/^extraction_commit:[ \t]*/,""); print; exit}')"

[ "$_mf_commit" = "$_ext_commit" ] \
  || _p "MANIFEST_COMMIT_MISMATCH: manifest extraction_commit ($_mf_commit) does not equal $EXTRACTED's extraction_commit ($_ext_commit)"

if [ "$problems" -gt 0 ]; then
  printf 'check-extraction-coverage: %d problem(s) in stage 2 (soundness) — fail closed\n' "$problems" >&2
  exit 1
fi

# ════════════════════════════════════════════════════════════════════════
# STAGE 3 — freshness: manifest_sha256 matches the current machine block
# ════════════════════════════════════════════════════════════════════════

if command -v sha256sum >/dev/null 2>&1; then
  _SHATOOL="sha256sum"
elif command -v shasum >/dev/null 2>&1; then
  _SHATOOL="shasum -a 256"
else
  printf 'TOOL_MISSING: no sha256sum or shasum on PATH — cannot verify manifest freshness (fail closed)\n' >&2
  exit 1
fi
# shellcheck disable=SC2086
_current_sha="$(printf '%s\n' "$_block" | $_SHATOOL | awk '{print $1}')"
_ms="$(printf '%s\n' "$_extracted_header" | awk '/^manifest_sha256:/{sub(/^manifest_sha256:[ \t]*/,""); print; exit}')"

if [ "$_current_sha" != "$_ms" ]; then
  printf 'EXTRACTION_STALE: %s manifest_sha256 (%s) does not match the current sha256 of %s'"'"'s machine block (%s) — re-stage\n' \
    "$EXTRACTED" "$_ms" "$MANIFEST" "$_current_sha" >&2
  exit 1
fi

# ════════════════════════════════════════════════════════════════════════
# STAGE 4 — completeness, both directions
# ════════════════════════════════════════════════════════════════════════

_covers_anchor_pool="$(printf '%s\n%s\n' "$_all_feat_ids" "$_all_screen_ids")"
_flows_anchor_pool="$(printf '%s\n' "$_screen_req_rows" | awk -F'\t' '{print $2}' | tr ',' '\n' \
  | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | grep -v '^$')"

# ── GAPS (optional third arg; own artifact, persona-gaps grammar/mechanics
#    inherited exactly — Q3) ────────────────────────────────────────────
_valid_gap_feat_ids=""
_valid_gap_screen_ids=""
if [ -n "$GAPS" ]; then
  _gaps_tsv="$(awk '
    /^source_id:/ {
      if (id != "") printf "%s\t%s\t%s\t%s\t%s\t%s\n", id, ty, rs, ow, rv, ex
      id = $0; sub(/^source_id:[ \t]*/, "", id); sub(/[ \t]+$/, "", id)
      ty = ""; rs = ""; ow = ""; rv = ""; ex = ""; next
    }
    /^source_type:/ { ty = $0; sub(/^source_type:[ \t]*/, "", ty); sub(/[ \t]+$/, "", ty) }
    /^reason:/      { rs = $0; sub(/^reason:[ \t]*/, "", rs); sub(/[ \t]+$/, "", rs) }
    /^owner:/       { ow = $0; sub(/^owner:[ \t]*/, "", ow); sub(/[ \t]+$/, "", ow) }
    /^reviewer:/    { rv = $0; sub(/^reviewer:[ \t]*/, "", rv); sub(/[ \t]+$/, "", rv) }
    /^expires:/     { ex = $0; sub(/^expires:[ \t]*/, "", ex); sub(/[ \t]+$/, "", ex) }
    END { if (id != "") printf "%s\t%s\t%s\t%s\t%s\t%s\n", id, ty, rs, ow, rv, ex }
  ' "$GAPS")"

  if [ -z "$_gaps_tsv" ]; then
    _p "NO_GAP_ENTRIES: $GAPS was given but declares zero gap entries (anti-vacuous — delete the file or add entries)"
  else
    _today="$(date +%Y-%m-%d)" || {
      printf 'TOOL_MISSING: cannot get today'"'"'s date (fail closed)\n' >&2
      exit 1
    }
    while IFS="$(printf '\t')" read -r _gid _gty _grs _gow _grv _gex; do
      [ -n "$_gid" ] || continue
      _bad=0
      case "$_gty" in
        FEAT | SCREEN) : ;;
        *) _p "GAP_FORMAT: gap $_gid source_type '$_gty' (must be FEAT or SCREEN)"; _bad=1 ;;
      esac
      for _v in "$_grs" "$_gow" "$_grv"; do
        [ -n "$_v" ] || { _p "GAP_FORMAT: gap $_gid has a blank reason/owner/reviewer field"; _bad=1; break; }
      done
      case "$_gex" in
        [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9])
          if [ "$_gex" \< "$_today" ]; then
            _p "GAP_EXPIRED: gap $_gid expired $_gex (today: $_today) — an expired gap is not a coverage credit"
            _bad=1
          fi ;;
        *) _p "GAP_FORMAT: gap $_gid expires '$_gex' not YYYY-MM-DD"; _bad=1 ;;
      esac
      if [ "$_bad" -eq 0 ]; then
        case "$_gty" in
          FEAT)   _valid_gap_feat_ids="$_valid_gap_feat_ids
$_gid" ;;
          SCREEN) _valid_gap_screen_ids="$_valid_gap_screen_ids
$_gid" ;;
        esac
      fi
    done <<GAPS_EOF
$_gaps_tsv
GAPS_EOF
  fi
fi

# ── per-entry: UNKNOWN_ANCHOR (direction a) + build the credit pools ─────
#
# TWO-LAYER injection guard on staging-supplied tokens (V-E3 F2, L22 —
# whitelist-before-use; ANCHOR_TOKEN_INVALID's name and class precedented
# by journey/bin/author-bundle.sh:122/138, the T4c ERE-closure wave):
#   (a) `set -f` while the unquoted `for _tok in $(...)` loops run —
#       without it a staging value like `covers: *` PATHNAME-EXPANDS
#       against the caller's cwd, and a cwd file named FEAT-100 becomes a
#       false coverage credit at exit 0 (verifier repro). Manifest-derived
#       values need no such guard (their stage-1 charset admits no glob
#       metacharacters), but staging covers/flows values are unvalidated
#       free text at this point.
#   (b) every staging token is whitelisted against `^[A-Za-z0-9._-]+$`
#       BEFORE any membership check or pool append — nonconforming is
#       ANCHOR_TOKEN_INVALID: EXTRACTED-<n>: <token> (append-only §7.3
#       addition, same E2/NO_GAP_ENTRIES precedent; whitelist-first means
#       an invalid token gets its ONE primary code, never a confusing
#       UNKNOWN_ANCHOR too, and can never enter the credit pools).
_entries_covers_tokens=""
_entries_flows_tokens=""
_n_entries=0
set -f
for _id in $(extracted_ids | sort -u); do
  [ -z "$_id" ] && continue
  _n_entries=$((_n_entries + 1))
  _covers_val="$(extracted_field "$_id" covers 2>/dev/null)" || _covers_val=""
  _flows_val="$(extracted_field "$_id" flows 2>/dev/null)" || _flows_val=""

  for _tok in $(_ec_tokens "$_covers_val"); do
    if ! printf '%s\n' "$_tok" | grep -qE '^[A-Za-z0-9._-]+$'; then
      _p "ANCHOR_TOKEN_INVALID: $_id: $_tok"
      continue
    fi
    printf '%s\n' "$_covers_anchor_pool" | grep -qxF "$_tok" \
      || _p "UNKNOWN_ANCHOR: $_id: $_tok"
    _entries_covers_tokens="$_entries_covers_tokens
$_tok"
  done

  for _tok in $(_ec_tokens "$_flows_val"); do
    if ! printf '%s\n' "$_tok" | grep -qE '^[A-Za-z0-9._-]+$'; then
      _p "ANCHOR_TOKEN_INVALID: $_id: $_tok"
      continue
    fi
    printf '%s\n' "$_flows_anchor_pool" | grep -qxF "$_tok" \
      || _p "UNKNOWN_ANCHOR: $_id: $_tok"
    _entries_flows_tokens="$_entries_flows_tokens
$_tok"
  done
done
set +f

# ── manifest anchors -> covered by an entry or a gap (direction b) ──────
_n_gaps_credited=0

for _fid in $_feat_req_ids; do
  [ -z "$_fid" ] && continue
  if printf '%s\n' "$_entries_covers_tokens" | grep -qxF "$_fid"; then
    continue
  fi
  if [ -n "$GAPS" ] && printf '%s\n' "$_valid_gap_feat_ids" | grep -qxF "$_fid"; then
    _n_gaps_credited=$((_n_gaps_credited + 1))
    continue
  fi
  if [ -n "$GAPS" ]; then
    _p "MISSING_EXTRACTION: $_fid (feat, behaviors>=1) has no staged entry covering it and no valid gap"
  else
    _p "MISSING_EXTRACTION: $_fid (feat, behaviors>=1) has no staged entry covering it (no GAPS file given — gap credit unavailable)"
  fi
done

while IFS="$(printf '\t')" read -r _sid _sflows; do
  [ -n "$_sid" ] || continue
  _covered=0
  if printf '%s\n' "$_entries_covers_tokens" | grep -qxF "$_sid"; then
    _covered=1
  else
    for _aft in $(_ec_tokens "$_sflows"); do
      if printf '%s\n' "$_entries_flows_tokens" | grep -qxF "$_aft"; then
        _covered=1
        break
      fi
    done
  fi
  [ "$_covered" -eq 1 ] && continue
  if [ -n "$GAPS" ] && printf '%s\n' "$_valid_gap_screen_ids" | grep -qxF "$_sid"; then
    _n_gaps_credited=$((_n_gaps_credited + 1))
    continue
  fi
  if [ -n "$GAPS" ]; then
    _p "MISSING_EXTRACTION: $_sid (screen, flows declared) has no staged entry covering it and no valid gap"
  else
    _p "MISSING_EXTRACTION: $_sid (screen, flows declared) has no staged entry covering it (no GAPS file given — gap credit unavailable)"
  fi
done <<SCREEN_EOF
$_screen_req_rows
SCREEN_EOF

if [ "$problems" -gt 0 ]; then
  printf 'check-extraction-coverage: %d problem(s) in stage 4 (completeness) — fail closed\n' "$problems" >&2
  exit 1
fi

_n_feat_req=$(printf '%s\n' "$_feat_req_ids" | grep -c '.')
_n_screen_req=$(printf '%s\n' "$_screen_req_rows" | grep -c '.')
printf 'OK: %s anchor(s) required (%s feat, %s screen), %s staged entries checked, %s gap(s) credited\n' \
  "$((_n_feat_req + _n_screen_req))" "$_n_feat_req" "$_n_screen_req" "$_n_entries" "$_n_gaps_credited"
exit 0
