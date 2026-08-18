#!/bin/sh
# journey-extracted-confirm.sh MAP EXTRACTED MANIFEST [GAPS] [--approve]
#
# Human-approved EXTRACTED->map promotion gate — the confirm gate (spec
# §4.3, §14 — task E5). Promotes ONLY confirmation_status: CONFIRMED
# entries from EXTRACTED (JOURNEY_EXTRACTED.md) into MAP as real
# JOURNEY-5xx blocks (501-599, spec §14 §5 tightening). Never automatic —
# see --approve below. Promotion is a transaction: MAP and EXTRACTED are
# both updated, or neither is.
#
# ── SIGNATURE NOTE (§14-forced deviation from the spec §4.3 draft) ─────────
# The design spec's §4.3 draft text reads
#   journey-extracted-confirm.sh MAP EXTRACTED [--approve]
# but §14 Q6 ratifies gate-enforced FEAT-grammar covers, which requires
# checking every covers: token's EXISTENCE against the MANIFEST's own
# `feat:` lines (COVERS_UNKNOWN_FEAT) — a check this gate cannot perform
# without reading MANIFEST directly. The ratified signature is therefore
#   journey-extracted-confirm.sh MAP EXTRACTED MANIFEST [GAPS] [--approve]
# MANIFEST is a new required positional arg; GAPS is optional (passed
# through to the composed check-extraction-coverage.sh unchanged) and is
# distinguished from --approve by NOT starting with `--` — --approve may
# appear in any argument position (mirrors journey-inbox-triage.sh /
# journey-reality-intake.sh / uat-report-promote.sh), the remaining args
# stay positional in their original relative order.
#
# ── --approve refuses BEFORE any other work (house rule 7) ─────────────────
# Without --approve: refuse immediately. Nothing is read (not even a file
# readability check), nothing is written. This happens before usage
# validation too — a malformed invocation without --approve still refuses
# on APPROVE_REQUIRED, never on a USAGE error.
#
# ── With --approve, in order ────────────────────────────────────────────────
#   1. usage validation (3 or 4 positional args: MAP EXTRACTED MANIFEST
#      [GAPS]) -> exit 2.
#   2. MAP and EXTRACTED exist and are readable -> exit 2. GAPS, if given,
#      exists -> exit 2. MANIFEST's existence is deliberately NOT checked
#      here (same posture journey-extracted-stage.sh / check-extraction-
#      coverage.sh take: MANIFEST_MISSING is a CHAIN code, brought "for
#      free" by composing check-extraction-coverage.sh below, not a
#      usage-class exit-2 check — a brand-new project legitimately has no
#      MANIFEST.md yet).
#   3. compose, in order, fail-closed, as EXECUTABLES (never reimplemented):
#        a. lint-journey-extracted.sh EXTRACTED           -> LINT_FAILED
#        b. lint-journey-map.sh MAP                       -> LINT_FAILED
#        c. check-extraction-coverage.sh MANIFEST EXTRACTED [GAPS]
#           -> pass-through of its own chain codes (MANIFEST_MISSING,
#              EXTRACTION_STALE, UNKNOWN_ANCHOR, MISSING_EXTRACTION, ...) —
#              this composition brings the MANIFEST staleness + anchor
#              completeness checks "for free"; this gate never
#              re-implements them.
#   4. selection: entries whose confirmation_status is CONFIRMED (read via
#      the SAME first-match extracted_field accessor every gate uses —
#      L11 discipline) AND which carry NO promoted_as stamp are
#      promotable. Entries WITH a valid promoted_as (composition already
#      guarantees its grammar + CONFIRMED-only precondition, since
#      lint-journey-extracted.sh's PROMOTED_AS_INVALID check ran in step
#      3a) are TERMINAL (spec §14 Q7) — skipped for promotion, printed on
#      stdout/stderr as inventory (their citations/manifest bindings were
#      already re-checked by the composed gates in step 3, regardless of
#      confirmation_status or promoted_as — "integrity was re-checked",
#      not re-checked again here). Zero promotable AND zero terminal ->
#      NO_CONFIRMED_ENTRIES (anti-vacuous). Zero promotable but >=1
#      terminal -> a legitimate no-op: print the inventory, exit 0 (an
#      all-promoted file is not a vacuous pass).
#   5. per-entry promotion checks on every PROMOTABLE entry, fail-slow
#      (all accumulate before refusing):
#        - grade must be exactly [C]                         -> GRADE_NOT_C
#        - the entry must carry oracle: not oracle_gap: (composition
#          already guarantees exactly one of the two is present)
#                                                       -> ORACLE_GAP_UNRESOLVED
#        - covers:, Q6's five requirements:
#            1. every token matches ^FEAT-([A-Z]+-)?[0-9]+$    -> COVERS_NOT_FEAT
#            2/3. exact-token existence in MANIFEST's feat: ids,
#                 never substring                        -> COVERS_UNKNOWN_FEAT
#            4. no duplicate tokens                       -> COVERS_DUPLICATE
#            5. >=1 valid FEAT anchor (a lone invalid token yields exactly
#               its ONE primary code above — COVERS_NOT_FEAT or
#               COVERS_UNKNOWN_FEAT — never an additional "empty anchor
#               set" code; whitelist-first, same discipline as check-
#               extraction-coverage.sh's ANCHOR_TOKEN_INVALID, L22)
#   6. collisions (I8): every promotable entry's norm_covers+norm_oracle
#      key vs every EXISTING map journey (any origin) AND vs every OTHER
#      promotable entry (sibling comparison, i<j only) -> EXTRACTED_COLLIDES
#      (fail-slow, whole run refused). promoted_as-stamped (terminal)
#      entries are excluded from the comparison set — they were never
#      selected as promotable in step 4 to begin with.
#   7. any accumulated problem from steps 5/6 -> whole run refused, exit 1.
#      Nothing has been written yet at this point (all-or-nothing).
#   8. extraction_provenance stamp precursors, fail closed before any
#      write: pick a sha256 tool (TOOL_MISSING otherwise) and hash the
#      CURRENT $EXTRACTED file's bytes (the human-reviewed content, before
#      this run adds any promoted_as stamp) -> first 12 hex chars is the
#      `confirmed:` value shared by every entry promoted THIS run;
#      extraction_commit is read once from EXTRACTED's own header.
#   9. id assignment: 501 upward, skipping ALL existing map ids of any
#      block AND ids already assigned earlier in this same loop. Any
#      assignment that would exceed 599 -> RANGE_EXHAUSTED (spec §14 §5
#      tightening: "extension requires separate owner ratification"),
#      whole run refused — still before any write.
#  10. promoted block construction, per entry: copy persona/goal/priority/
#      covers/flows/oracle_surface/negative_states/steps/oracle/runner
#      unchanged; force origin: EXTRACTED, author_status: UNWRITTEN,
#      evidence: [] (Lock 4); INJECT data_fixtures: [] and exemptions: []
#      (L25 — journey-inbox-triage.sh:312/332 does the IDENTICAL injection
#      for its own SIMULATOR promotions, because these two fields are
#      REQUIRED_FIELDS in lint-journey-map.sh's schema but are never
#      carried by a pre-confirmation candidate — without this injection,
#      promotion dead-ends at the composed map-lint self-check, proven
#      empirically in V-E1); test:'s literal `<n>` placeholder token
#      substituted with the assigned numeric id (a concrete test value
#      with no `<n>` token copies through byte-identical — commit
#      4b08dcb's precedent); NEW map field extraction_provenance:
#      "EXTRACTED-<n> commit:<40-hex> confirmed:<12-hex>" (spec §14 Q1).
#      Staging-only fields (needs_human_confirm, confirmation_status,
#      grade, extraction_sources, prior_e2e, resolution, resolved_from,
#      rejected_reason) are NEVER copied — they simply aren't read here.
#  11. temp + trap + mv (house rule 8), both files created together (L17
#      ordering, mirrors journey-inbox-triage.sh): temp map built first
#      (existing MAP + every promoted block appended), composed
#      lint-journey-map.sh self-check on the temp map (LINT_FAILED
#      otherwise) -> L23 postcondition (every assigned JOURNEY-<id> block
#      asserted non-empty in the temp map BEFORE any rename — defense in
#      depth) -> temp staging built (existing EXTRACTED with a
#      `promoted_as: JOURNEY-<id>` line stamped directly after each
#      promoted entry's FIRST confirmation_status: line — L11 first-match
#      semantics), composed lint-journey-extracted.sh self-check on the
#      temp staging (LINT_FAILED otherwise, re-linted pre-rename) -> mv
#      MAP first, THEN mv EXTRACTED second (L17: the map write is the SSOT
#      mutation; the staging update is only the audit-trail annotation of
#      a fact the map write already established).
#  12. success: one `PROMOTED: EXTRACTED-<n> -> JOURNEY-<id>` line per
#      promotion, plus a summary line. Exit 0.
#
# Any failure at any point before step 11's renames -> the temp+trap
# cleans both temps; neither MAP nor EXTRACTED is touched (house rule 8).
#
# ── Codes (own; closed enum, this gate) ─────────────────────────────────────
#   APPROVE_REQUIRED        — --approve absent (refuses before any other work)
#   LINT_FAILED              — EXTRACTED failed lint-journey-extracted.sh, OR
#                               MAP failed lint-journey-map.sh (pre-flight or
#                               self-check on the temp), OR the temp staging
#                               this gate built failed its own self-check
#   NO_CONFIRMED_ENTRIES     — zero confirmation_status: CONFIRMED entries at
#                               all (promotable or terminal) — anti-vacuous
#   GRADE_NOT_C: <id>: <grade>          — grade is not exactly [C]
#   ORACLE_GAP_UNRESOLVED: <id>         — entry still carries oracle_gap:
#   COVERS_NOT_FEAT: <id>: <token>      — a covers: token fails the anchored
#                                          FEAT grammar (spec §14 Q6)
#   COVERS_UNKNOWN_FEAT: <id>: <token>  — a grammatically-valid FEAT token
#                                          does not exist in MANIFEST's own
#                                          feat: lines (exact match, never
#                                          substring)
#   COVERS_DUPLICATE: <id>: <token>     — a covers: token repeats
#   EXTRACTED_COLLIDES: <id> vs <other-id> — normalized covers+oracle
#                                          collide with an existing map
#                                          journey (any origin) or a sibling
#                                          promotable entry (I8)
#   RANGE_EXHAUSTED: ... — no free JOURNEY id remains in 501-599 (extension
#                          requires separate owner ratification, spec §14)
#   TOOL_MISSING             — no sha256sum/shasum on PATH (needed for the
#                               extraction_provenance confirmed: stamp)
#   MKTEMP_FAILED            — the fail-closed accumulator itself could not
#                               be created
# + pass-through of whatever lint-journey-extracted.sh / lint-journey-map.sh
# / check-extraction-coverage.sh emit on their own composed calls.
#
# Usage error / missing MAP or EXTRACTED (or GAPS if given): exit 2 (house
# convention). Gate violation (APPROVE_REQUIRED, LINT_FAILED,
# NO_CONFIRMED_ENTRIES, GRADE_NOT_C, ORACLE_GAP_UNRESOLVED, COVERS_NOT_FEAT,
# COVERS_UNKNOWN_FEAT, COVERS_DUPLICATE, EXTRACTED_COLLIDES,
# RANGE_EXHAUSTED, TOOL_MISSING, MKTEMP_FAILED): exit 1. Success: exit 0.
#
# Deps: POSIX sh, awk, grep, sed, mktemp, sha256sum|shasum.
# shellcheck shell=sh

set -u

_here="$(cd "$(dirname "$0")" && pwd)"
LIB="$_here/../lib/journey-lib.sh"

_emit() { printf '%s\n' "$*" >&2; }
_die()  { _emit "$*"; exit 1; }

# ── parse: --approve may appear anywhere; MAP/EXTRACTED/MANIFEST/[GAPS]
# stay positional in their original relative order (mirrors
# journey-inbox-triage.sh / journey-reality-intake.sh; no arrays, bash 3.2
# compatible). ───────────────────────────────────────────────────────────
APPROVE=0
_first=1
for _a in "$@"; do
  if [ "$_a" = "--approve" ]; then
    APPROVE=1
  else
    if [ "$_first" -eq 1 ]; then set -- "$_a"; _first=0
    else set -- "$@" "$_a"; fi
  fi
done

# --approve gates EVERYTHING: absent -> refuse before any other work, before
# even usage validation. Nothing read, nothing written (house rule 7).
if [ "$APPROVE" -ne 1 ]; then
  _emit "APPROVE_REQUIRED: confirmation requires human --approve (never automatic). Nothing read, nothing written."
  exit 1
fi

usage() {
  printf 'Usage: journey-extracted-confirm.sh MAP EXTRACTED MANIFEST [GAPS] [--approve]\n' >&2
  exit 2
}

if [ $# -eq 3 ]; then
  MAP="$1"; EXTRACTED="$2"; MANIFEST="$3"; GAPS=""
elif [ $# -eq 4 ]; then
  MAP="$1"; EXTRACTED="$2"; MANIFEST="$3"; GAPS="$4"
else
  usage
fi

[ -f "$MAP" ] || {
  _emit "journey-extracted-confirm: file not found: $MAP"
  exit 2
}
[ -f "$EXTRACTED" ] || {
  _emit "journey-extracted-confirm: file not found: $EXTRACTED"
  exit 2
}
if [ -n "$GAPS" ]; then
  [ -f "$GAPS" ] || {
    _emit "journey-extracted-confirm: file not found: $GAPS"
    exit 2
  }
fi

# ── compose, in order, fail-closed, as executables (never reimplemented) ──
/bin/sh "$_here/lint-journey-extracted.sh" "$EXTRACTED"
_rc=$?
if [ "$_rc" -ne 0 ]; then
  _emit "LINT_FAILED: staging file failed lint-journey-extracted.sh: $EXTRACTED"
  exit 1
fi

/bin/sh "$_here/lint-journey-map.sh" "$MAP"
_rc=$?
if [ "$_rc" -ne 0 ]; then
  _emit "LINT_FAILED: map failed lint-journey-map.sh: $MAP"
  exit 1
fi

if [ -n "$GAPS" ]; then
  /bin/sh "$_here/check-extraction-coverage.sh" "$MANIFEST" "$EXTRACTED" "$GAPS"
else
  /bin/sh "$_here/check-extraction-coverage.sh" "$MANIFEST" "$EXTRACTED"
fi
_rc=$?
if [ "$_rc" -ne 0 ]; then
  _emit "journey-extracted-confirm: check-extraction-coverage.sh failed (fail closed; $MAP and $EXTRACTED untouched)"
  exit 1
fi

JOURNEY_MAP="$MAP"
JOURNEY_EXTRACTED="$EXTRACTED"
export JOURNEY_MAP JOURNEY_EXTRACTED
# shellcheck disable=SC1090
. "$LIB"

# ── selection (step 4): CONFIRMED via first-match extracted_field (L11);
# promoted_as-stamped entries are terminal (spec §14 Q7). ──────────────────
_promotable=""
_terminal=""
for _id in $(extracted_ids | sort -u); do
  [ -z "$_id" ] && continue
  _cs="$(extracted_field "$_id" confirmation_status 2>/dev/null)" || _cs=""
  [ "$_cs" = "CONFIRMED" ] || continue
  _blk="$(extracted_block "$_id")"
  if printf '%s\n' "$_blk" | grep -qE '^promoted_as:'; then
    _terminal="$_terminal $_id"
  else
    _promotable="$_promotable $_id"
  fi
done
_promotable="${_promotable# }"
_terminal="${_terminal# }"

for _tid in $_terminal; do
  _tpas="$(extracted_field "$_tid" promoted_as 2>/dev/null)" || _tpas=""
  _emit "ALREADY PROMOTED: $_tid -> $_tpas (terminal; skipped — integrity re-checked by the composed gates above)"
done

if [ -z "$_promotable" ] && [ -z "$_terminal" ]; then
  _emit "NO_CONFIRMED_ENTRIES: no confirmation_status: CONFIRMED entries found in $EXTRACTED"
  exit 1
fi
if [ -z "$_promotable" ]; then
  _n_terminal=0
  for _t in $_terminal; do _n_terminal=$((_n_terminal + 1)); done
  _emit "CONFIRM COMPLETE: 0 promoted; $_n_terminal already-promoted entry(ies) on file (legitimate no-op)"
  exit 0
fi

# ── MANIFEST feat: ids (for COVERS_UNKNOWN_FEAT) — MANIFEST is already
# proven well-formed by the composed check-extraction-coverage.sh call
# above (exit 0 reached this point), so no re-validation is needed here. ──
_mf_block="$(awk '
  /^EXTRACTION-MANIFEST BEGIN$/ { inblk = 1; next }
  /^EXTRACTION-MANIFEST END$/   { if (inblk) exit }
  inblk { print }
' "$MANIFEST")"
_manifest_feat_ids="$(printf '%s\n' "$_mf_block" | awk '
  /^feat: / { line = $0; sub(/^feat: /, "", line); n = split(line, f, / \| /); print f[1] }
')"

# ── per-entry promotion checks (step 5, fail-slow) ──────────────────────────
_errors=0

for _id in $_promotable; do
  _grade="$(extracted_field "$_id" grade 2>/dev/null)" || _grade=""
  if [ "$_grade" != "[C]" ]; then
    printf 'GRADE_NOT_C: %s: %s (must be exactly [C] to promote)\n' "$_id" "${_grade:-<missing>}" >&2
    _errors=$((_errors + 1))
  fi

  _blk="$(extracted_block "$_id")"
  if printf '%s\n' "$_blk" | grep -qE '^oracle_gap:'; then
    printf 'ORACLE_GAP_UNRESOLVED: %s: a human must supply a real oracle: before this candidate can promote\n' "$_id" >&2
    _errors=$((_errors + 1))
  fi

  # ── covers, Q6's five requirements ─────────────────────────────────────
  _covers="$(extracted_field "$_id" covers 2>/dev/null)" || _covers=""
  _tokens="$(printf '%s\n' "$_covers" | awk -F',' '{
    for (i = 1; i <= NF; i++) {
      t = $i
      gsub(/^[ \t]+|[ \t]+$/, "", t)
      if (t != "") print t
    }
  }')"

  if [ -z "$_tokens" ]; then
    printf 'COVERS_NOT_FEAT: %s: <blank> (at least one valid FEAT anchor is required to promote)\n' "$_id" >&2
    _errors=$((_errors + 1))
  fi

  # requirement 4: no duplicate tokens (raw, case-sensitive exact)
  for _dup in $(printf '%s\n' "$_tokens" | sort | uniq -d); do
    [ -z "$_dup" ] && continue
    printf 'COVERS_DUPLICATE: %s: %s\n' "$_id" "$_dup" >&2
    _errors=$((_errors + 1))
  done

  # requirements 1/2/3/5: grammar first (whitelist-before-use, L22 —
  # mirrors check-extraction-coverage.sh's ANCHOR_TOKEN_INVALID discipline:
  # a token failing grammar gets exactly its ONE primary code, never also
  # an existence check), then exact-token existence against the manifest's
  # own feat: ids (never substring).
  while IFS= read -r _tok; do
    [ -z "$_tok" ] && continue
    if ! printf '%s\n' "$_tok" | grep -qE '^FEAT-([A-Z]+-)?[0-9]+$'; then
      printf 'COVERS_NOT_FEAT: %s: %s\n' "$_id" "$_tok" >&2
      _errors=$((_errors + 1))
      continue
    fi
    if ! printf '%s\n' "$_manifest_feat_ids" | grep -qxF "$_tok"; then
      printf 'COVERS_UNKNOWN_FEAT: %s: %s\n' "$_id" "$_tok" >&2
      _errors=$((_errors + 1))
    fi
  done <<_COVERS_EOF_
$_tokens
_COVERS_EOF_
done

# ── collisions (step 6, I8): every promotable entry vs ALL existing map
# journeys (any origin) ─────────────────────────────────────────────────────
_map_ids="$(journey_ids | sort -u)"
for _id in $_promotable; do
  _p_covers="$(norm_covers "$(extracted_field "$_id" covers 2>/dev/null)")"
  _p_oracle="$(norm_oracle "$(extracted_field "$_id" oracle 2>/dev/null)")"
  for _mid in $_map_ids; do
    _m_covers="$(norm_covers "$(journey_field "$_mid" covers 2>/dev/null)")"
    _m_oracle="$(norm_oracle "$(journey_field "$_mid" oracle 2>/dev/null)")"
    if [ "$_p_covers" = "$_m_covers" ] && [ "$_p_oracle" = "$_m_oracle" ]; then
      printf 'EXTRACTED_COLLIDES: %s vs %s\n' "$_id" "$_mid" >&2
      _errors=$((_errors + 1))
    fi
  done
done

# ── collisions vs sibling promotable entries (i<j only, one report per pair) ─
_prev_promotable=""
for _id in $_promotable; do
  _p_covers="$(norm_covers "$(extracted_field "$_id" covers 2>/dev/null)")"
  _p_oracle="$(norm_oracle "$(extracted_field "$_id" oracle 2>/dev/null)")"
  for _sid in $_prev_promotable; do
    _s_covers="$(norm_covers "$(extracted_field "$_sid" covers 2>/dev/null)")"
    _s_oracle="$(norm_oracle "$(extracted_field "$_sid" oracle 2>/dev/null)")"
    if [ "$_p_covers" = "$_s_covers" ] && [ "$_p_oracle" = "$_s_oracle" ]; then
      printf 'EXTRACTED_COLLIDES: %s vs %s\n' "$_id" "$_sid" >&2
      _errors=$((_errors + 1))
    fi
  done
  _prev_promotable="$_prev_promotable $_id"
done

if [ "$_errors" -gt 0 ]; then
  _emit "CONFIRM REFUSED: $_errors problem(s) found above. No write to $MAP or $EXTRACTED."
  exit 1
fi

# ── step 8: extraction_provenance stamp precursors, fail closed BEFORE any
# write (TOOL_MISSING). Hashes the CURRENT $EXTRACTED bytes — the
# human-reviewed content this run is about to promote, before any
# promoted_as stamp is added. ──────────────────────────────────────────────
if command -v sha256sum >/dev/null 2>&1; then _SHATOOL="sha256sum"
elif command -v shasum >/dev/null 2>&1; then _SHATOOL="shasum -a 256"
else
  _emit "TOOL_MISSING: no sha256sum or shasum on PATH — cannot compute the extraction_provenance confirmed: stamp (fail closed)"
  exit 1
fi
# shellcheck disable=SC2086
_ext_sha_full="$($_SHATOOL < "$EXTRACTED" | awk '{print $1}')"
_ext_sha12="$(printf '%s' "$_ext_sha_full" | cut -c1-12)"

_ext_header="$(awk '/^## EXTRACTED-/{exit} {print}' "$EXTRACTED")"
_ext_commit="$(printf '%s\n' "$_ext_header" | awk '/^extraction_commit:/{sub(/^extraction_commit:[ \t]*/,""); print; exit}')"

# ── step 9: id assignment, 501 upward, skipping ALL existing map ids of any
# block AND ids already assigned this run; RANGE_EXHAUSTED past 599 (spec
# §14 §5 tightening). Still before any write. ──────────────────────────────
_used_ids="$(journey_ids)"
_next=501
_assignments=""
for _id in $_promotable; do
  while printf '%s\n' "$_used_ids" | grep -qxF "JOURNEY-$_next"; do
    _next=$((_next + 1))
  done
  if [ "$_next" -gt 599 ]; then
    _emit "RANGE_EXHAUSTED: no free JOURNEY id remains in 501-599 for $_id (extension requires separate owner ratification)"
    exit 1
  fi
  _nid="$_next"
  _assignments="$_assignments
$_id JOURNEY-$_nid"
  _used_ids="$_used_ids
JOURNEY-$_nid"
  _next=$((_next + 1))
done
_assignments="$(printf '%s\n' "$_assignments" | sed '/^$/d')"

# ---------------------------------------------------------------------------
# _write_promoted_block ENTRY_ID NEW_ID -> a "## JOURNEY-<NEW_ID> ..." block
# on stdout. Copies persona/goal/priority/covers/flows/oracle_surface/
# negative_states/steps/oracle/runner unchanged; forces origin/author_status/
# evidence (Lock 4); INJECTS data_fixtures/exemptions (L25 — see the
# journey-inbox-triage.sh:312/332 precedent this mirrors: those two fields
# are REQUIRED_FIELDS in lint-journey-map.sh's schema but are never carried
# by a pre-confirmation candidate); substitutes test:'s literal `<n>`
# placeholder with the assigned numeric id; stamps the NEW
# extraction_provenance: field (spec §14 Q1). The heading rewrite below
# matches on '^## <id> — ' (spaced em-dash) — guaranteed to match by the
# composed lint-journey-extracted.sh's ENTRY_HEADING_INVALID check, which
# already ran (step 3a) over the WHOLE staging file, including every entry
# selected as promotable here.
# ---------------------------------------------------------------------------
_write_promoted_block() {
  _eid="$1"; _nid="$2"
  _heading="$(extracted_block "$_eid" | head -n1 | sed "s/^## ${_eid} /## JOURNEY-${_nid} /")"
  printf '\n%s\n' "$_heading"
  printf '%-17s%s\n' "origin:" "EXTRACTED"
  printf '%-17s%s\n' "persona:" "$(extracted_field "$_eid" persona 2>/dev/null)"
  printf '%-17s%s\n' "goal:" "$(extracted_field "$_eid" goal 2>/dev/null)"
  printf '%-17s%s\n' "priority:" "$(extracted_field "$_eid" priority 2>/dev/null)"
  printf '%-17s%s\n' "covers:" "$(extracted_field "$_eid" covers 2>/dev/null)"
  printf '%-17s%s\n' "flows:" "$(extracted_field "$_eid" flows 2>/dev/null)"
  printf '%-17s%s\n' "oracle_surface:" "$(extracted_field "$_eid" oracle_surface 2>/dev/null)"
  printf '%-17s%s\n' "negative_states:" "$(extracted_field "$_eid" negative_states 2>/dev/null)"
  # L25 (from V-E1, binds E5 — see .superpowers/sdd/sim-reality-progress.md):
  # the composed map lint (REQUIRED_FIELDS in lint-journey-map.sh) demands
  # data_fixtures + exemptions keys on every block; staging never carries
  # them. Injected here exactly as journey-inbox-triage.sh's own
  # _write_promoted_block does at its lines 312 (data_fixtures) and 332
  # (exemptions) — or promotion dead-ends at the composed map-lint
  # self-check (proven empirically by V-E1).
  printf '%-17s%s\n' "data_fixtures:" "[]"
  extracted_block "$_eid" | awk '
    /^steps:/ { print; ins = 1; next }
    ins && /^[a-zA-Z_][a-zA-Z0-9_]*:/ { exit }
    ins { print }
  '
  printf '%-17s%s\n' "oracle:" "$(extracted_field "$_eid" oracle 2>/dev/null)"
  printf '%-17s%s\n' "evidence:" "[]"
  # test:'s literal <n> placeholder token substituted with the assigned id
  # (commit 4b08dcb's precedent) — a concrete test value carrying no <n>
  # token copies through byte-identical.
  _test_val="$(extracted_field "$_eid" test 2>/dev/null)"
  case "$_test_val" in
    *'<n>'*) _test_val="$(printf '%s' "$_test_val" | sed "s/<n>/${_nid}/g")" ;;
  esac
  printf '%-17s%s\n' "test:" "$_test_val"
  printf '%-17s%s\n' "runner:" "$(extracted_field "$_eid" runner 2>/dev/null)"
  printf '%-17s%s\n' "author_status:" "UNWRITTEN"
  printf '%-17s%s\n' "exemptions:" "[]"
  # NEW map field (spec §14 Q1): audit provenance — source candidate id +
  # pinned source commit + confirmation stamp. Validated (optional field,
  # when present) by lint-journey-map.sh's own additive Check 10.
  printf 'extraction_provenance: %s commit:%s confirmed:%s\n' "$_eid" "$_ext_commit" "$_ext_sha12"
}

# ── step 11: temp + trap + mv (house rule 8); both temps created together,
# L17 ordering (map first, staging second — mirrors journey-inbox-
# triage.sh). ────────────────────────────────────────────────────────────
_map_tmp="$(mktemp "$(dirname "$MAP")/.map-XXXXXXXX")" || {
  _emit "MKTEMP_FAILED: cannot create map temp (fail closed)"
  exit 1
}
_ext_tmp="$(mktemp "$(dirname "$EXTRACTED")/.extracted-XXXXXXXX")" || {
  rm -f "$_map_tmp"
  _emit "MKTEMP_FAILED: cannot create staging temp (fail closed)"
  exit 1
}
trap 'rm -f "$_map_tmp" "$_ext_tmp"' EXIT INT TERM

cat "$MAP" > "$_map_tmp" || _die "journey-extracted-confirm: failed to stage map temp (fail closed)"

for _line in $(printf '%s\n' "$_assignments" | tr ' ' '@'); do
  _eid="${_line%%@*}"
  _jid="${_line#*@}"
  _write_promoted_block "$_eid" "${_jid#JOURNEY-}" >> "$_map_tmp"
done

/bin/sh "$_here/lint-journey-map.sh" "$_map_tmp"
_rc=$?
if [ "$_rc" -ne 0 ]; then
  _emit "LINT_FAILED: promoted map failed lint-journey-map.sh self-check (temps cleaned; $MAP untouched)"
  exit 1
fi

# ── L23 postcondition: every assigned JOURNEY-<id> block must be non-empty
# in the temp map BEFORE any rename (defense in depth — the ENTRY_HEADING_
# INVALID check already guaranteed the rewrite would match, via
# composition in step 3a). ──────────────────────────────────────────────────
_prev_journey_map="$JOURNEY_MAP"
JOURNEY_MAP="$_map_tmp"
export JOURNEY_MAP
while IFS= read -r _line; do
  [ -z "$_line" ] && continue
  _jid="${_line#* }"
  [ -n "$(journey_block "$_jid")" ] || \
    _die "journey-extracted-confirm: assigned block $_jid missing from temp map after rewrite (fail closed; temps cleaned; $MAP and $EXTRACTED untouched)"
done << _ASSERT_EOF_
$_assignments
_ASSERT_EOF_
JOURNEY_MAP="$_prev_journey_map"
export JOURNEY_MAP

# ── build the temp staging: stamp promoted_as: JOURNEY-<id> directly after
# each promoted entry's FIRST confirmation_status: line (L11 — matches
# extracted_field's own first-match semantics). ─────────────────────────────
_assign_str=""
while IFS= read -r _line; do
  [ -z "$_line" ] && continue
  _eid="${_line%% *}"
  _jid="${_line#* }"
  _assign_str="$_assign_str $_eid=$_jid"
done << _ASSIGN_EOF_
$_assignments
_ASSIGN_EOF_

awk -v assign="$_assign_str" '
  BEGIN {
    n = split(assign, pairs, " ")
    for (i = 1; i <= n; i++) {
      if (pairs[i] == "") continue
      split(pairs[i], kv, "=")
      map[kv[1]] = kv[2]
    }
  }
  /^## EXTRACTED-[0-9]+/ {
    match($0, /EXTRACTED-[0-9]+/)
    cur = substr($0, RSTART, RLENGTH)
    seen = 0
    print
    next
  }
  {
    if (cur != "" && !seen && (cur in map) && $0 ~ /^confirmation_status:/) {
      print
      printf "%-17s%s\n", "promoted_as:", map[cur]
      seen = 1
      next
    }
    print
  }
' "$EXTRACTED" > "$_ext_tmp"

/bin/sh "$_here/lint-journey-extracted.sh" "$_ext_tmp"
_rc=$?
if [ "$_rc" -ne 0 ]; then
  _emit "LINT_FAILED: updated staging failed lint-journey-extracted.sh self-check (temps cleaned; $MAP and $EXTRACTED untouched)"
  exit 1
fi

# ── both temps lint-clean: mv map first, staging second (L17 ordering). ────
mv "$_map_tmp" "$MAP" || _die "journey-extracted-confirm: failed to write $MAP (fail closed)"
mv "$_ext_tmp" "$EXTRACTED" || _die "journey-extracted-confirm: failed to write $EXTRACTED (fail closed) -- $MAP was already updated; reconcile manually"
trap - EXIT INT TERM

for _line in $(printf '%s\n' "$_assignments" | tr ' ' '@'); do
  _eid="${_line%%@*}"
  _jid="${_line#*@}"
  _emit "PROMOTED: $_eid -> $_jid"
done

_n_promoted=$(printf '%s\n' "$_assignments" | grep -c .)
_n_terminal=0
for _t in $_terminal; do _n_terminal=$((_n_terminal + 1)); done
_emit "CONFIRM COMPLETE: $_n_promoted promoted; $_n_terminal already-promoted entry(ies) skipped (terminal)"
exit 0
