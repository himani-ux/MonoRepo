#!/bin/sh
# lint-journey-inbox.sh PATH_TO_INBOX
#
# Validates every candidate block in a JOURNEY_INBOX.md against the KLOSS
# inbox schema (spec §4.2, journey/docs/journey-inbox-format.md). Exits 0 if
# every block is schema-valid; prints each problem as "CODE: message" to
# stderr and exits 1 if any block fails. All violations are accumulated
# before exiting (fail-slow, not fail-fast) — never `| while read` (a known
# fail-open class: a pipeline subshell loses counter mutations).
#
# The inbox carries the SAME parsing idiom as lint-journey-map.sh (shared
# accessors in journey/lib/journey-lib.sh: inbox_ids/inbox_block/inbox_field,
# added alongside journey_ids/journey_block/journey_field) so the two lints
# can never disagree about how a block is extracted. This lint validates
# schema COMPLETENESS (required fields present) plus the inbox-specific
# grammar (promotion_status, simulator_trace, restricted origin/author_status,
# the paste-promotion-bypass guard). It deliberately does NOT re-validate the
# map-inherited enums (priority, oracle_surface, runner, ...) — that is
# lint-journey-map.sh's job, re-run by the triage gate on the promoted block,
# so the two never disagree about what a valid value looks like.
#
# Closed code list
# ─────────────────
# File-level:
#   BAD_HEADER               — first line is not exactly "# JOURNEY-INBOX"
#   FORBIDDEN_JOURNEY_HEADER — literal "## JOURNEY-" found anywhere in the
#                               file (paste-promotion bypass guard — inbox
#                               entries never carry map headers)
#   RUNTIME_FIELD            — a runtime-truth field key (ci_status,
#                               last_run, ci_run_id, ci_artifact,
#                               failure_summary) found anywhere in the file
#                               (same code name as journey-gen-check-candidate.sh
#                               / lint-journey-tests.sh for this exact class)
#   DUPLICATE_INBOX_ID        — an INBOX-<n> id appears more than once
#   BAD_INBOX_ID              — an INBOX-<n> id is not a positive integer (zero)
#   NO_INBOX_ENTRIES          — anti-vacuous: a file with a valid header but
#                               zero "## INBOX-<n>" entries
#
# Per-entry schema:
#   MISSING_FIELD: <id>: <field>   — a required field key is absent
#   BLANK_FIELD: <id>: <field>     — a required-nonblank field's value is blank
#   BAD_ORIGIN: <id>: <value>      — origin present but not exactly SIMULATOR
#                                     (mirrors journey-gen-check-candidate.sh's
#                                     BAD_ORIGIN code name)
#   BAD_AUTHOR_STATUS: <id>: <value> — author_status present but not exactly
#                                     UNWRITTEN (mirrors the candidate
#                                     checker's BAD_AUTHOR_STATUS code name)
#   BAD_PROMOTION_STATUS: <id>: <value> — not one of PROPOSED|ACCEPTED|REJECTED
#   REJECTED_REASON_MISSING: <id>  — promotion_status is REJECTED but
#                                     rejected_reason is absent or blank
#   PROMOTED_AS_INVALID: <id>: <value> — promoted_as present but either (a)
#                                     its value does not match ^JOURNEY-[0-9]+$
#                                     or (b) promotion_status (read via the
#                                     same first-match accessor as the
#                                     BAD_PROMOTION_STATUS check) is not
#                                     exactly ACCEPTED. `promoted_as:` is an
#                                     OPTIONAL, append-only extension (T2,
#                                     spec DC-2): the triage gate
#                                     (journey-inbox-triage.sh) stamps it onto
#                                     an entry's `promotion_status: ACCEPTED`
#                                     line immediately after promoting it, as
#                                     an audit trail — `promoted_as: JOURNEY-301`.
#                                     It is never required (its absence is
#                                     never flagged) and is grammar-checked
#                                     only when present.
#
# simulator_trace: grammar (block field, 2-space-indented "  - <key>: <value>"
# entries, same idiom as steps:/preconditions:):
#   TRACE_MISSING: <id>            — simulator_trace: field entirely absent
#   TRACE_FORMAT: <id>: <line>     — an entry line doesn't match
#                                     "  - <key>: <value>"
#   TRACE_KEY_UNKNOWN: <id>: <key> — well-formed entry, key outside
#                                     {persona, goal, app_build, runner,
#                                     patience_budget, path, stuck_point,
#                                     evidence}
#   TRACE_FIELD_MISSING: <id>: <key>   — a required-exactly-once scalar key
#                                     (persona/goal/app_build/runner/
#                                     patience_budget) has zero occurrences
#   TRACE_FIELD_DUPLICATE: <id>: <key> — a required-exactly-once scalar key
#                                     appears more than once
#   TRACE_TOKEN_INVALID: <id>: <key>: <value> — persona/app_build/runner
#                                     value contains whitespace or characters
#                                     outside [A-Za-z0-9._/-]
#   TRACE_PATIENCE_BUDGET_INVALID: <id>: <value> — patience_budget is not a
#                                     positive integer
#   TRACE_PATH_EMPTY: <id>         — zero "path:" entries (required >= 1)
#   TRACE_EVIDENCE_EMPTY: <id>     — zero "evidence:" entries (required >= 1)
#   TRACE_EVIDENCE_INVALID: <id>: <value> — an evidence relpath starts with
#                                     "/" or contains a ".." segment
#
# Usage error / missing file: exit 2 (matches lint-journey-map.sh).
#
# shellcheck shell=sh

set -u

LINT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB="$LINT_DIR/../lib/journey-lib.sh"

usage() { printf 'Usage: lint-journey-inbox.sh PATH_TO_INBOX\n' >&2; exit 2; }
[ $# -ne 1 ] && usage

INBOX_PATH="$1"
[ ! -f "$INBOX_PATH" ] && {
  printf 'lint-journey-inbox: file not found: %s\n' "$INBOX_PATH" >&2
  exit 2
}

JOURNEY_INBOX="$INBOX_PATH"
export JOURNEY_INBOX
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

errors=0

# ── Check H1: first line must be exactly "# JOURNEY-INBOX" ────────────────
_first_line="$(head -n1 "$INBOX_PATH")"
if [ "$_first_line" != "# JOURNEY-INBOX" ]; then
  printf 'BAD_HEADER: first line must be exactly "# JOURNEY-INBOX" (got: %s)\n' "$_first_line" >&2
  errors=$((errors + 1))
fi

# ── Check H2: literal "## JOURNEY-" anywhere is forbidden ─────────────────
# Paste-promotion bypass guard: an inbox entry can never carry a map header,
# so this string is rejected wherever it appears, not just at line-start.
if grep -qF '## JOURNEY-' "$INBOX_PATH"; then
  printf 'FORBIDDEN_JOURNEY_HEADER: literal "## JOURNEY-" found in the inbox — inbox entries never carry map headers\n' >&2
  errors=$((errors + 1))
fi

# ── Check H3: runtime-truth fields forbidden anywhere in the file ─────────
if grep -qE '^[[:space:]]*(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):' "$INBOX_PATH"; then
  printf 'RUNTIME_FIELD: runtime-truth field key found in the inbox (runtime truth lives only in the CI-owned ledger)\n' >&2
  errors=$((errors + 1))
fi

ids="$(inbox_ids)"

# ── Check H4: no duplicate INBOX-<n> id ────────────────────────────────────
for dup in $(printf '%s\n' "$ids" | sort | uniq -d); do
  [ -z "$dup" ] && continue
  printf 'DUPLICATE_INBOX_ID: %s appears more than once — only the first block is validated\n' "$dup" >&2
  errors=$((errors + 1))
done
ids="$(printf '%s\n' "$ids" | sort -u)"

# ── Check H5: anti-vacuous — zero entries ──────────────────────────────────
if [ -z "$ids" ]; then
  printf 'NO_INBOX_ENTRIES: no "## INBOX-<n>" entries found in the inbox\n' >&2
  errors=$((errors + 1))
fi

# simulator_trace is deliberately NOT in this list: its presence is checked
# by Check E6 (TRACE_MISSING) below, which is the sole code for its absence
# — including it here too would double-report the same root cause under two
# different codes (the map lint's own precedent: a missing field never also
# emits enum-check noise for the same field).
REQUIRED_FIELDS="promotion_status origin persona goal priority covers \
oracle_surface negative_states steps oracle evidence test runner \
author_status"

NONEMPTY_FIELDS="promotion_status origin persona goal priority covers \
oracle_surface oracle runner author_status"

for id in $ids; do
  [ -z "$id" ] && continue
  block="$(inbox_block "$id")"

  # ── Check E0: id must be a positive integer (never zero) ───────────────
  _num="${id#INBOX-}"
  _stripped="$(printf '%s' "$_num" | sed 's/^0*//')"
  if [ -z "$_stripped" ]; then
    printf 'BAD_INBOX_ID: %s: id must be a positive integer, not zero\n' "$id" >&2
    errors=$((errors + 1))
  fi

  # ── Check E1: required fields present ───────────────────────────────────
  for field in $REQUIRED_FIELDS; do
    if ! printf '%s\n' "$block" | grep -qE "^${field}:"; then
      printf 'MISSING_FIELD: %s: %s\n' "$id" "$field" >&2
      errors=$((errors + 1))
    fi
  done

  # ── Check E2: NONEMPTY required fields must have a non-blank value ─────
  for field in $NONEMPTY_FIELDS; do
    _nv="$(inbox_field "$id" "$field" 2>/dev/null)" || continue
    if [ -z "$_nv" ]; then
      printf 'BLANK_FIELD: %s: %s\n' "$id" "$field" >&2
      errors=$((errors + 1))
    fi
  done

  # ── Check E3: origin restricted to SIMULATOR ────────────────────────────
  _origin="$(inbox_field "$id" origin 2>/dev/null)" || _origin=""
  if [ -n "$_origin" ] && [ "$_origin" != "SIMULATOR" ]; then
    printf 'BAD_ORIGIN: %s: %s (only SIMULATOR is allowed in the inbox)\n' "$id" "$_origin" >&2
    errors=$((errors + 1))
  fi

  # ── Check E4: author_status restricted to UNWRITTEN ─────────────────────
  _astatus="$(inbox_field "$id" author_status 2>/dev/null)" || _astatus=""
  if [ -n "$_astatus" ] && [ "$_astatus" != "UNWRITTEN" ]; then
    printf 'BAD_AUTHOR_STATUS: %s: %s (only UNWRITTEN is allowed in the inbox)\n' "$id" "$_astatus" >&2
    errors=$((errors + 1))
  fi

  # ── Check E5: promotion_status enum + REJECTED requires rejected_reason ─
  _pstatus="$(inbox_field "$id" promotion_status 2>/dev/null)" || _pstatus=""
  if [ -n "$_pstatus" ] && ! in_enum "$_pstatus" PROPOSED ACCEPTED REJECTED; then
    printf 'BAD_PROMOTION_STATUS: %s: %s\n' "$id" "$_pstatus" >&2
    errors=$((errors + 1))
  fi
  if [ "$_pstatus" = "REJECTED" ]; then
    _rreason="$(inbox_field "$id" rejected_reason 2>/dev/null)" || _rreason=""
    if [ -z "$_rreason" ]; then
      printf 'REJECTED_REASON_MISSING: %s\n' "$id" >&2
      errors=$((errors + 1))
    fi
  fi

  # ── Check E5b: promoted_as grammar (OPTIONAL field, ACCEPTED-only) ──────
  # Append-only extension (T2, spec DC-2): the triage gate stamps this after
  # promoting an entry, as an audit trail. Absence is never flagged — this
  # check only fires when the key is present at all. Reuses $_pstatus from
  # Check E5 above (same first-match accessor — L11 discipline: a
  # PROPOSED-then-ACCEPTED duplicate-scalar entry reads as PROPOSED here too,
  # so a promoted_as line stamped on such an entry would still be rejected).
  if printf '%s\n' "$block" | grep -qE '^promoted_as:'; then
    _pas="$(inbox_field "$id" promoted_as 2>/dev/null)" || _pas=""
    if ! printf '%s\n' "$_pas" | grep -qE '^JOURNEY-[0-9]+$'; then
      printf 'PROMOTED_AS_INVALID: %s: %s\n' "$id" "$_pas" >&2
      errors=$((errors + 1))
    elif [ "$_pstatus" != "ACCEPTED" ]; then
      printf 'PROMOTED_AS_INVALID: %s: promoted_as present but promotion_status is %s (must be ACCEPTED)\n' \
        "$id" "${_pstatus:-<blank>}" >&2
      errors=$((errors + 1))
    fi
  fi

  # ── Check E6: simulator_trace grammar ───────────────────────────────────
  if ! printf '%s\n' "$block" | grep -qE '^simulator_trace:'; then
    printf 'TRACE_MISSING: %s\n' "$id" >&2
    errors=$((errors + 1))
  else
    # Same block-extraction idiom lint-journey-map.sh Check 8 uses for
    # preconditions: — lines after the "simulator_trace:" header up to the
    # next top-level key or the next heading.
    _trace="$(printf '%s\n' "$block" | awk '
      /^simulator_trace:/{ins=1; next}
      ins && /^[a-z_]+:/{exit}
      ins && /^## /{exit}
      ins{print}
    ')"

    _c_persona=0; _c_goal=0; _c_app_build=0; _c_runner=0; _c_patience=0
    _c_path=0; _c_evidence=0

    while IFS= read -r _tline; do
      case "$_tline" in
        '') continue ;;
      esac
      if ! printf '%s\n' "$_tline" | grep -qE '^  - [A-Za-z][A-Za-z0-9_]*: .+$'; then
        printf 'TRACE_FORMAT: %s: %s\n' "$id" "$_tline" >&2
        errors=$((errors + 1))
        continue
      fi
      _tbody="${_tline#  - }"
      _tkey="${_tbody%%:*}"
      _tval="${_tbody#*: }"

      case "$_tkey" in
        persona|goal|app_build|runner|patience_budget|path|stuck_point|evidence) : ;;
        *)
          printf 'TRACE_KEY_UNKNOWN: %s: %s\n' "$id" "$_tkey" >&2
          errors=$((errors + 1))
          continue
          ;;
      esac

      case "$_tkey" in
        persona) _c_persona=$((_c_persona + 1)) ;;
        goal) _c_goal=$((_c_goal + 1)) ;;
        app_build) _c_app_build=$((_c_app_build + 1)) ;;
        runner) _c_runner=$((_c_runner + 1)) ;;
        patience_budget) _c_patience=$((_c_patience + 1)) ;;
        path) _c_path=$((_c_path + 1)) ;;
        evidence) _c_evidence=$((_c_evidence + 1)) ;;
      esac

      # token grammar: persona/app_build/runner values carry no whitespace
      case "$_tkey" in
        persona|app_build|runner)
          case "$_tval" in
            *[!A-Za-z0-9._/-]*)
              printf 'TRACE_TOKEN_INVALID: %s: %s: %s\n' "$id" "$_tkey" "$_tval" >&2
              errors=$((errors + 1))
              ;;
          esac
          ;;
      esac

      # patience_budget: positive integer only
      if [ "$_tkey" = "patience_budget" ]; then
        case "$_tval" in
          ''|*[!0-9]*)
            printf 'TRACE_PATIENCE_BUDGET_INVALID: %s: %s\n' "$id" "$_tval" >&2
            errors=$((errors + 1))
            ;;
          *)
            _pb_stripped="$(printf '%s' "$_tval" | sed 's/^0*//')"
            if [ -z "$_pb_stripped" ]; then
              printf 'TRACE_PATIENCE_BUDGET_INVALID: %s: %s\n' "$id" "$_tval" >&2
              errors=$((errors + 1))
            fi
            ;;
        esac
      fi

      # evidence: repo-relative relpath — no leading /, no .. segment
      if [ "$_tkey" = "evidence" ]; then
        case "$_tval" in
          /*|*..*)
            printf 'TRACE_EVIDENCE_INVALID: %s: %s\n' "$id" "$_tval" >&2
            errors=$((errors + 1))
            ;;
        esac
      fi
    done << _TRACE_EOF_
$_trace
_TRACE_EOF_

    # Explicit per-key checks (no eval / indirect expansion for a dynamic
    # "_c_$key" lookup — this file stays eval-free, matching the rest of
    # journey/bin; check-uat-preconditions.sh documents why: an eval'd
    # expansion is not safe to build from parsed-file-derived data).
    if [ "$_c_persona" -eq 0 ]; then
      printf 'TRACE_FIELD_MISSING: %s: persona\n' "$id" >&2; errors=$((errors + 1))
    elif [ "$_c_persona" -gt 1 ]; then
      printf 'TRACE_FIELD_DUPLICATE: %s: persona\n' "$id" >&2; errors=$((errors + 1))
    fi
    if [ "$_c_goal" -eq 0 ]; then
      printf 'TRACE_FIELD_MISSING: %s: goal\n' "$id" >&2; errors=$((errors + 1))
    elif [ "$_c_goal" -gt 1 ]; then
      printf 'TRACE_FIELD_DUPLICATE: %s: goal\n' "$id" >&2; errors=$((errors + 1))
    fi
    if [ "$_c_app_build" -eq 0 ]; then
      printf 'TRACE_FIELD_MISSING: %s: app_build\n' "$id" >&2; errors=$((errors + 1))
    elif [ "$_c_app_build" -gt 1 ]; then
      printf 'TRACE_FIELD_DUPLICATE: %s: app_build\n' "$id" >&2; errors=$((errors + 1))
    fi
    if [ "$_c_runner" -eq 0 ]; then
      printf 'TRACE_FIELD_MISSING: %s: runner\n' "$id" >&2; errors=$((errors + 1))
    elif [ "$_c_runner" -gt 1 ]; then
      printf 'TRACE_FIELD_DUPLICATE: %s: runner\n' "$id" >&2; errors=$((errors + 1))
    fi
    if [ "$_c_patience" -eq 0 ]; then
      printf 'TRACE_FIELD_MISSING: %s: patience_budget\n' "$id" >&2; errors=$((errors + 1))
    elif [ "$_c_patience" -gt 1 ]; then
      printf 'TRACE_FIELD_DUPLICATE: %s: patience_budget\n' "$id" >&2; errors=$((errors + 1))
    fi

    if [ "$_c_path" -eq 0 ]; then
      printf 'TRACE_PATH_EMPTY: %s\n' "$id" >&2
      errors=$((errors + 1))
    fi
    if [ "$_c_evidence" -eq 0 ]; then
      printf 'TRACE_EVIDENCE_EMPTY: %s\n' "$id" >&2
      errors=$((errors + 1))
    fi
  fi

done

[ "$errors" -gt 0 ] && exit 1
exit 0
