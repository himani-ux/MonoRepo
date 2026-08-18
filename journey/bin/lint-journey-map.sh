#!/bin/sh
# lint-journey-map.sh PATH_TO_MAP
#
# Validates every journey block in a JOURNEY_MAP.md against the KLOSS intent schema.
# Exits 0 if every block is schema-valid; prints each problem (one per line, prefixed
# with the JOURNEY-ID) and exits 1 if any block fails.  All violations are accumulated
# before exiting (fail-slow, not fail-fast).
#
# Fixture-path convention: every entry in data_fixtures is resolved RELATIVE TO THE
# DIRECTORY CONTAINING the map file (dirname PATH_TO_MAP).  Example: if the map lives
# at /project/journey/JOURNEY_MAP.md and a block declares
#   data_fixtures: inputs/good.csv
# the lint looks for /project/journey/inputs/good.csv.
#
# Checks 0-7 validate the core intent schema (duplicate IDs, required fields,
# enum values, forbidden runtime-truth fields, anti-happy-path negative-state
# coverage, fixture existence, WRITTEN test-path sanity, EXEMPT metadata).
#
# Check 8 validates the OPTIONAL `preconditions:` block field — grammar only,
# no existence/probe checks (a later UAT preflight gate consumes these).
# When present it is a block field like `steps:`: the `preconditions:` line
# followed by one or more indented `  - <kind>: <value>` entries, where
# kind ∈ {auth, env, data, state} and value matches ^[A-Za-z0-9._/-]+$
# (non-empty, no spaces). Codes:
#   PRECONDITION_FORMAT: <id>: <offending line>  — entry doesn't match
#                                                    `- <kind>: <value>`
#                                                    (missing colon, empty or
#                                                    spaced value, etc.)
#   PRECONDITION_KIND_UNKNOWN: <id>: <kind>       — well-formed entry, kind
#                                                    outside the allowed set
#   PRECONDITION_EMPTY: <id>                      — preconditions: present,
#                                                    zero entry lines before
#                                                    the next field/heading
#
# Check 9 validates the OPTIONAL `oracle_classes:` field (spec G4, oracle
# observability classes) — grammar only, no adjudication (a later UAT
# report gate, check-uat-oracle-scope.sh, consumes these to reject browser
# gaps claimed against below-the-UI oracle clauses). When present it is a
# single-line field like `oracle:`: the value is class tokens joined by the
# literal separator ` AND `, POSITIONALLY matching this journey's own
# `oracle:` clauses (also ` AND `-joined — see `oracle:` in
# JOURNEY_MAP.template.md). Tokens ∈ {browser, lower}: `browser` = the
# clause is adjudicable from the browser/UI surface; `lower` = the clause is
# verified below the UI (unit/integration) — a browser UAT must not report
# its absence as a gap. Codes:
#   ORACLE_CLASS_UNKNOWN: <id>: <token>            — token outside
#                                                     {browser, lower}
#   ORACLE_CLASS_COUNT_MISMATCH: <id>: oracle has <n> clause(s) but
#                                 oracle_classes has <m>
#                                                   — `oracle:` and
#                                                     `oracle_classes:` split
#                                                     into a different
#                                                     number of ` AND `
#                                                     clauses (a blank/empty
#                                                     value counts as 0)
#
# Check 10 validates the OPTIONAL `extraction_provenance:` field (spec §14
# Q1, task E5) — grammar only. Written ONLY by
# journey/bin/journey-extracted-confirm.sh onto a promoted EXTRACTED-origin
# block; an audit trail naming the staging entry id, the pinned extraction
# commit, and a confirmation-time content hash of the staging file. When
# present it is a single-line field: `<EXTRACTED-id> commit:<40-hex>
# confirmed:<12-hex>`. This check is append-only and additive — a map that
# carries no `extraction_provenance:` field at all (every map that predates
# this check) is completely unaffected; existing map-lint tests are
# byte-unchanged. Code:
#   EXTRACTION_PROVENANCE_FORMAT: <id>: <offending value> — present but not
#                                  exactly `EXTRACTED-<digits> commit:<40 hex
#                                  chars> confirmed:<12 hex chars>`
#
# shellcheck shell=sh

set -u

LINT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB="$LINT_DIR/../lib/journey-lib.sh"

usage() { printf 'Usage: lint-journey-map.sh PATH_TO_MAP\n' >&2; exit 2; }
[ $# -ne 1 ] && usage

MAP_PATH="$1"
[ ! -f "$MAP_PATH" ] && {
  printf 'lint-journey-map: file not found: %s\n' "$MAP_PATH" >&2
  exit 2
}

MAP_DIR="$(cd "$(dirname "$MAP_PATH")" && pwd)"
JOURNEY_MAP="$MAP_PATH"
export JOURNEY_MAP
# shellcheck disable=SC1090
. "$LIB"

# ---------------------------------------------------------------------------
# in_enum VALUE MEMBER...  — returns 0 if VALUE equals any MEMBER
# ---------------------------------------------------------------------------
in_enum() {
  _iv="$1"; shift
  for _ie; do [ "$_iv" = "$_ie" ] && return 0; done
  return 1
}

# ---------------------------------------------------------------------------
# split_csv STRING — print one whitespace-trimmed token per line
# ---------------------------------------------------------------------------
split_csv() {
  printf '%s\n' "$1" | awk '{
    n = split($0, a, /,/)
    for (i = 1; i <= n; i++) {
      gsub(/^[ \t]+|[ \t]+$/, "", a[i])
      if (a[i] != "") print a[i]
    }
  }'
}
# split_and is defined in journey-lib.sh (sourced above) — shared with
# check-uat-oracle-scope.sh so the ` AND `-grammar is parsed identically.

# ---------------------------------------------------------------------------
# Required fields (all blocks must have these keys present)
# ---------------------------------------------------------------------------
REQUIRED_FIELDS="origin persona goal priority covers flows oracle_surface \
negative_states data_fixtures steps oracle evidence test runner \
author_status exemptions"

# Subset of REQUIRED_FIELDS whose single-line VALUE must be non-empty (always).
# Excluded on purpose: data_fixtures/evidence/exemptions/flows are optional content;
# negative_states and test are empty-allowed except where Checks 4/6/7 require them
# (non-EXEMPT / WRITTEN / EXEMPT); `steps` is a MULTI-LINE field whose value lives on
# the following indented lines (not the `steps:` header), so its non-emptiness is
# enforced structurally by Check 4 (a step must reference a negative_state), not here.
NONEMPTY_FIELDS="origin persona goal priority covers oracle_surface oracle \
runner author_status"

errors=0
ids="$(journey_ids)"

# ── Check 0: no duplicate JOURNEY-ID ──────────────────────────────────────────
# journey_block() returns only the FIRST block per id, so a second same-id
# block would otherwise escape every per-block check below (review finding #3
# — an unvalidated block smuggled behind a duplicated heading).
for dup in $(printf '%s\n' "$ids" | sort | uniq -d); do
  printf 'DUPLICATE_JOURNEY_ID: %s appears more than once — only the first block is validated; a duplicate heading is a smuggling channel (fail closed)\n' "$dup"
  errors=$((errors + 1))
done
ids="$(printf '%s\n' "$ids" | sort -u)"

for id in $ids; do
  block="$(journey_block "$id")"

  # ── Check 1: required fields present ─────────────────────────────────────
  for field in $REQUIRED_FIELDS; do
    if ! printf '%s\n' "$block" | grep -qE "^${field}:"; then
      printf '%s: missing required field: %s\n' "$id" "$field"
      errors=$((errors + 1))
    fi
  done

  # ── Check 1b: NONEMPTY required fields must have a non-blank value ────────
  # journey_field returns the trimmed value (exit 1 if the key is absent — that
  # case is already reported above, so skip it here to avoid double-reporting).
  for field in $NONEMPTY_FIELDS; do
    _nv="$(journey_field "$id" "$field" 2>/dev/null)" || continue
    if [ -z "$_nv" ]; then
      printf '%s: required field is blank: %s\n' "$id" "$field"
      errors=$((errors + 1))
    fi
  done

  # ── Check 2: enum validation ─────────────────────────────────────────────
  _origin="$(journey_field "$id" origin 2>/dev/null)" || _origin=""
  if [ -n "$_origin" ] && ! in_enum "$_origin" PERSONA SIMULATOR REALITY EXTRACTED DERIVED; then
    printf '%s: invalid origin value: %s\n' "$id" "$_origin"
    errors=$((errors + 1))
  fi

  _priority="$(journey_field "$id" priority 2>/dev/null)" || _priority=""
  if [ -n "$_priority" ] && ! in_enum "$_priority" P0 P1 P2 P3; then
    printf '%s: invalid priority value: %s\n' "$id" "$_priority"
    errors=$((errors + 1))
  fi

  _osurface="$(journey_field "$id" oracle_surface 2>/dev/null)" || _osurface=""
  if [ -n "$_osurface" ] && ! in_enum "$_osurface" UI API "UI+API"; then
    printf '%s: invalid oracle_surface value: %s\n' "$id" "$_osurface"
    errors=$((errors + 1))
  fi

  _astatus="$(journey_field "$id" author_status 2>/dev/null)" || _astatus=""
  if [ -n "$_astatus" ] && ! in_enum "$_astatus" UNWRITTEN WRITTEN EXEMPT; then
    printf '%s: invalid author_status value: %s\n' "$id" "$_astatus"
    errors=$((errors + 1))
  fi

  # Review I4: an invented runner value must not survive into the canonical
  # map — same allowed set as journey-runner-resolve.sh.
  _runner="$(journey_field "$id" runner 2>/dev/null)" || _runner=""
  if [ -n "$_runner" ] && ! in_enum "$_runner" playwright maestro appium pty http stub; then
    printf '%s: invalid runner value: %s (allowed: playwright|maestro|appium|pty|http|stub)\n' "$id" "$_runner"
    errors=$((errors + 1))
  fi

  # ── Check 3: runtime-truth fields forbidden ──────────────────────────────
  if printf '%s\n' "$block" | \
      grep -qE "^(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):"; then
    printf '%s: runtime-truth field found in block\n' "$id"
    errors=$((errors + 1))
  fi

  # ── Check 4: anti-happy-path (NON-EXEMPT only) ───────────────────────────
  if [ "$_astatus" != "EXEMPT" ]; then
    _negstates="$(journey_field "$id" negative_states 2>/dev/null)" || _negstates=""
    if [ -z "$_negstates" ]; then
      printf '%s: non-exempt journey must declare at least one negative_state\n' "$id"
      errors=$((errors + 1))
    else
      # Extract steps block: lines under "steps:" up to the next top-level key:
      _steps="$(printf '%s\n' "$block" | awk '
        /^steps:/{ins=1; next}
        ins && /^[a-zA-Z_][a-zA-Z0-9_]*:/{exit}
        ins{print}
      ')"
      _found=0
      while IFS= read -r _ns; do
        [ -z "$_ns" ] && continue
        if printf '%s\n' "$_steps" | grep -qF "$_ns"; then
          _found=1
          break
        fi
      done << _NEGSTATES_EOF_
$(split_csv "$_negstates")
_NEGSTATES_EOF_
      if [ "$_found" -eq 0 ]; then
        printf '%s: no declared negative_state appears in any step\n' "$id"
        errors=$((errors + 1))
      fi
    fi
  fi

  # ── Check 5: fixture existence ───────────────────────────────────────────
  _fixtures="$(journey_field "$id" data_fixtures 2>/dev/null)" || _fixtures=""
  if [ -n "$_fixtures" ] && [ "$_fixtures" != "[]" ]; then
    while IFS= read -r _fx; do
      [ -z "$_fx" ] && continue
      if [ ! -f "$MAP_DIR/$_fx" ]; then
        printf '%s: data_fixture not found: %s\n' "$id" "$_fx"
        errors=$((errors + 1))
      fi
    done << _FIXTURES_EOF_
$(split_csv "$_fixtures")
_FIXTURES_EOF_
  fi

  # ── Check 6: test-path sanity (WRITTEN only) ─────────────────────────────
  if [ "$_astatus" = "WRITTEN" ]; then
    _test="$(journey_field "$id" test 2>/dev/null)" || _test=""
    if [ -z "$_test" ]; then
      printf '%s: author_status is WRITTEN but test field is empty\n' "$id"
      errors=$((errors + 1))
    fi
  fi

  # ── Check 7: exemption sanity (EXEMPT only) ──────────────────────────────
  if [ "$_astatus" = "EXEMPT" ]; then
    _exemptions="$(journey_field "$id" exemptions 2>/dev/null)" || _exemptions=""
    if [ -z "$_exemptions" ] || [ "$_exemptions" = "[]" ]; then
      printf '%s: EXEMPT journey must have non-empty exemptions (not [])\n' "$id"
      errors=$((errors + 1))
    else
      for _kw in tag reason owner expiry reviewer; do
        case "$_exemptions" in
          *"$_kw"*) ;;
          *)
            printf '%s: EXEMPT exemptions missing required keyword: %s\n' "$id" "$_kw"
            errors=$((errors + 1))
            ;;
        esac
      done
      # MIN-3: reject an expired exemption (expiry date before today). Only a
      # strict YYYY-MM-DD expiry is date-compared (zero-padded ISO sorts
      # chronologically); any other form is left to the keyword check above.
      _exp="$(printf '%s' "$_exemptions" | sed -n 's/.*expiry:[[:space:]]*\([0-9][0-9-]*\).*/\1/p')"
      case "$_exp" in
        [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9])
          _today="$(date -u +%Y-%m-%d)"
          _earliest="$(printf '%s\n%s\n' "$_exp" "$_today" | LC_ALL=C sort | head -n1)"
          if [ "$_exp" != "$_today" ] && [ "$_earliest" = "$_exp" ]; then
            printf '%s: EXEMPT exemption expired (expiry %s is before today %s)\n' "$id" "$_exp" "$_today"
            errors=$((errors + 1))
          fi
          ;;
      esac
    fi
  fi

  # ── Check 8: preconditions grammar (OPTIONAL field) ──────────────────────
  # preconditions: is NOT in REQUIRED_FIELDS/NONEMPTY_FIELDS — absent is fine.
  # When present it is a block field like steps: — validated for GRAMMAR ONLY
  # (existence/probe checks are a later UAT-preflight gate's job, not lint's).
  if printf '%s\n' "$block" | grep -qE '^preconditions:'; then
    _precond="$(printf '%s\n' "$block" | awk '
      /^preconditions:/{ins=1; next}
      ins && /^[a-z_]+:/{exit}
      ins && /^## /{exit}
      ins{print}
    ')"
    _pc_count=0
    while IFS= read -r _pline; do
      case "$_pline" in
        '') ;;
        '  - '*)
          _pc_count=$((_pc_count + 1))
          _pc_body="${_pline#  - }"
          if printf '%s\n' "$_pc_body" | grep -qE '^[A-Za-z][A-Za-z0-9_-]*: [A-Za-z0-9._/-]+$'; then
            _pc_kind="${_pc_body%%:*}"
            if ! in_enum "$_pc_kind" auth env data state; then
              printf 'PRECONDITION_KIND_UNKNOWN: %s: %s\n' "$id" "$_pc_kind"
              errors=$((errors + 1))
            fi
          else
            printf 'PRECONDITION_FORMAT: %s: %s\n' "$id" "$_pc_body"
            errors=$((errors + 1))
          fi
          ;;
      esac
    done << _PRECOND_EOF_
$_precond
_PRECOND_EOF_
    if [ "$_pc_count" -eq 0 ]; then
      printf 'PRECONDITION_EMPTY: %s\n' "$id"
      errors=$((errors + 1))
    fi
  fi

  # ── Check 9: oracle_classes grammar (OPTIONAL field, spec G4) ────────────
  # oracle_classes: is NOT in REQUIRED_FIELDS/NONEMPTY_FIELDS — absent is
  # fine. When present it is a single-line field like `oracle:` (see
  # journey_field's accessor pattern above): its value is class tokens
  # joined by literal ` AND `, positionally matching this journey's own
  # `oracle:` clauses (also ` AND `-joined). Tokens ∈ {browser, lower}.
  if printf '%s\n' "$block" | grep -qE '^oracle_classes:'; then
    _oclasses="$(journey_field "$id" oracle_classes 2>/dev/null)" || _oclasses=""
    while IFS= read -r _octok; do
      [ -z "$_octok" ] && continue
      if ! in_enum "$_octok" browser lower; then
        printf 'ORACLE_CLASS_UNKNOWN: %s: %s\n' "$id" "$_octok"
        errors=$((errors + 1))
      fi
    done << _OCLASS_EOF_
$(split_and "$_oclasses")
_OCLASS_EOF_
    _oracle="$(journey_field "$id" oracle 2>/dev/null)" || _oracle=""
    _on="$(split_and "$_oracle" | wc -l | tr -d ' ')"
    _cn="$(split_and "$_oclasses" | wc -l | tr -d ' ')"
    if [ "$_on" -ne "$_cn" ]; then
      printf 'ORACLE_CLASS_COUNT_MISMATCH: %s: oracle has %s clause(s) but oracle_classes has %s\n' \
        "$id" "$_on" "$_cn"
      errors=$((errors + 1))
    fi
  fi

  # ── Check 10: extraction_provenance grammar (OPTIONAL field, spec §14 Q1,
  # task E5) ────────────────────────────────────────────────────────────────
  # extraction_provenance: is NOT in REQUIRED_FIELDS/NONEMPTY_FIELDS — absent
  # is fine (append-only: a map without this field lints byte-identically to
  # before this check existed). When present it is a single-line field
  # (journey_field's accessor pattern), written only by
  # journey-extracted-confirm.sh: `<EXTRACTED-id> commit:<40-hex>
  # confirmed:<12-hex>`.
  if printf '%s\n' "$block" | grep -qE '^extraction_provenance:'; then
    _eprov="$(journey_field "$id" extraction_provenance 2>/dev/null)" || _eprov=""
    if ! printf '%s\n' "$_eprov" | grep -qE '^EXTRACTED-[0-9]+ commit:[0-9a-f]{40} confirmed:[0-9a-f]{12}$'; then
      printf 'EXTRACTION_PROVENANCE_FORMAT: %s: %s\n' "$id" "$_eprov"
      errors=$((errors + 1))
    fi
  fi

done

[ "$errors" -gt 0 ] && exit 1
exit 0
