#!/bin/sh
# lint-journey-extracted.sh PATH_TO_EXTRACTED
#
# Validates every candidate block in a JOURNEY_EXTRACTED.md staging file
# against the KLOSS extracted-baseline schema (spec §4.2, §7.1, §14 —
# journey/docs/journey-extracted-format.md). Exits 0 if every block is
# schema-valid; prints each problem as "CODE: message" to stderr and exits 1
# if any block fails. All violations are accumulated before exiting
# (fail-slow, not fail-fast) — never `| while read` (a known fail-open
# class: a pipeline subshell loses counter mutations).
#
# The staging file carries the SAME parsing idiom as lint-journey-map.sh /
# lint-journey-inbox.sh (shared accessors in journey/lib/journey-lib.sh:
# extracted_ids/extracted_block/extracted_field, siblings of
# journey_ids/journey_block/journey_field and inbox_ids/inbox_block/
# inbox_field) so every gate that reads this file agrees on how a block is
# extracted. This lint validates STAGING schema completeness and grammar
# only — it deliberately does NOT: re-validate the map-inherited enums
# (priority, oracle_surface, runner, ...; that is lint-journey-map.sh's job,
# composed at confirmation), byte-verify extraction_sources citations
# against the pinned commit (check-extracted-provenance.sh, task E2),
# enforce FEAT-grammar covers (the confirm gate, task E5, spec §14 Q6), or
# check MANIFEST staleness (check-extraction-coverage.sh, task E3).
#
# Closed code list (25 codes total — spec §7.1, §14-adjusted; see
# journey/docs/journey-extracted-format.md §6.1 for full detail)
# ──────────────────────────────────────────────────────────────────────────
# File-level:
#   BAD_HEADER                — first line is not exactly "# JOURNEY-EXTRACTED"
#   EXTRACTION_COMMIT_INVALID — extraction_commit: header value is not
#                               exactly 40 lowercase hex characters
#   MANIFEST_SHA_INVALID      — manifest_sha256: header value is not exactly
#                               64 lowercase hex characters
#   FORBIDDEN_JOURNEY_HEADER  — literal "## JOURNEY-" found anywhere
#   RUNTIME_FIELD             — a runtime-truth field key found anywhere
#   DUPLICATE_EXTRACTED_ID    — an EXTRACTED-<n> id appears more than once
#   BAD_EXTRACTED_ID          — an EXTRACTED-<n> id is not a positive
#                               integer (zero)
#   NO_EXTRACTED_ENTRIES      — anti-vacuous: a valid header but zero entries
#
# Per-entry:
#   ENTRY_HEADING_INVALID     — heading is not the canonical
#                               '## EXTRACTED-<digits> — "<title>"' form
#                               (spaced em-dash, double-quoted title; checked
#                               UP FRONT, before any field check — L23)
#   NEEDS_CONFIRM_INVALID     — needs_human_confirm missing, or present but
#                               not exactly "true" (I2 — folded into ONE
#                               code; absence is exactly as wrong as `false`)
#   CONFIRM_STATUS_INVALID    — confirmation_status present but not one of
#                               PENDING | CONFIRMED | REJECTED
#   REJECTED_REASON_MISSING   — confirmation_status: REJECTED with no
#                               non-blank rejected_reason:
#   GRADE_UNKNOWN              — grade present but not one of
#                               [C] | [I] | [G] | [X]
#   MISSING_FIELD: <id>: <field>   — a required field key is absent
#   BLANK_FIELD: <id>: <field>     — a required-nonblank field's value is
#                               blank (also reused for a blank oracle: value
#                               once oracle: is known to be the chosen field
#                               — see ORACLE_EXACTLY_ONE below)
#   BAD_ORIGIN: <id>: <value>      — origin present but not exactly EXTRACTED
#   BAD_AUTHOR_STATUS: <id>: <value> — author_status present but not exactly
#                               UNWRITTEN
#   SOURCES_MISSING: <id>      — fewer than the required number of
#                               extraction_sources lines (>=1 always; >=2
#                               when grade is [X] or a resolution: line is
#                               present)
#   SOURCE_FORMAT: <id>: <line>    — an extraction_sources entry line
#                               matches neither the code-cite, the
#                               section-cite, nor the search-cite grammar
#                               (also fires on a leading "/" or ".."
#                               segment in the path, and on a section-cite
#                               whose heading contains a literal '"' — a
#                               hybrid line-cite/section-cite paste, DX-1
#                               live-characterization fix wave)
#   X_ONE_SIDED: <id>          — grade: [X] with fewer than 2
#                               extraction_sources lines (distinct from
#                               SOURCES_MISSING — names the two-sided-proof
#                               requirement specifically)
#   ORACLE_EXACTLY_ONE: <id>   — neither, or both, of oracle:/oracle_gap:
#                               present
#   ORACLE_GAP_FORMAT: <id>    — oracle_gap: present but its value is blank
#   PROMOTED_AS_INVALID: <id>: <value> — promoted_as: malformed, or present
#                               on a non-CONFIRMED entry
#   PRIOR_E2E_FORMAT: <id>: <value> — prior_e2e: present but blank, or its
#                               value starts with "/" or contains a ".."
#                               segment
#   RESOLVED_FROM_MISSING: <id>    — resolution: without resolved_from:,
#                               resolved_from: without resolution:, or
#                               resolved_from: present but not one of
#                               [X] | [G] | [I]
#
# Usage error / missing file: exit 2 (matches lint-journey-map.sh /
# lint-journey-inbox.sh). Schema violations: exit 1.
#
# shellcheck shell=sh

set -u

LINT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB="$LINT_DIR/../lib/journey-lib.sh"

usage() { printf 'Usage: lint-journey-extracted.sh PATH_TO_EXTRACTED\n' >&2; exit 2; }
[ $# -ne 1 ] && usage

EXTRACTED_PATH="$1"
[ ! -f "$EXTRACTED_PATH" ] && {
  printf 'lint-journey-extracted: file not found: %s\n' "$EXTRACTED_PATH" >&2
  exit 2
}

JOURNEY_EXTRACTED="$EXTRACTED_PATH"
export JOURNEY_EXTRACTED
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

# ── Check H1: first line must be exactly "# JOURNEY-EXTRACTED" ────────────
_first_line="$(head -n1 "$EXTRACTED_PATH")"
if [ "$_first_line" != "# JOURNEY-EXTRACTED" ]; then
  printf 'BAD_HEADER: first line must be exactly "# JOURNEY-EXTRACTED" (got: %s)\n' "$_first_line" >&2
  errors=$((errors + 1))
fi

# ── Check H2/H3: header fields (region before the first entry heading) ────
_header="$(awk '/^## EXTRACTED-/{exit} {print}' "$EXTRACTED_PATH")"

_ec="$(printf '%s\n' "$_header" | awk '/^extraction_commit:/{sub(/^extraction_commit:[ \t]*/,""); print; exit}')"
if ! printf '%s' "$_ec" | grep -qE '^[0-9a-f]{40}$'; then
  printf 'EXTRACTION_COMMIT_INVALID: extraction_commit must be exactly 40 lowercase hex characters (got: %s)\n' "${_ec:-<missing>}" >&2
  errors=$((errors + 1))
fi

_ms="$(printf '%s\n' "$_header" | awk '/^manifest_sha256:/{sub(/^manifest_sha256:[ \t]*/,""); print; exit}')"
if ! printf '%s' "$_ms" | grep -qE '^[0-9a-f]{64}$'; then
  printf 'MANIFEST_SHA_INVALID: manifest_sha256 must be exactly 64 lowercase hex characters (got: %s)\n' "${_ms:-<missing>}" >&2
  errors=$((errors + 1))
fi

# ── Check H4: literal "## JOURNEY-" anywhere is forbidden ─────────────────
# Paste-confirmation bypass guard: a staged entry can never carry a map
# header, so this string is rejected wherever it appears, not just at
# line-start.
if grep -qF '## JOURNEY-' "$EXTRACTED_PATH"; then
  printf 'FORBIDDEN_JOURNEY_HEADER: literal "## JOURNEY-" found in the staging file — extracted entries never carry map headers\n' >&2
  errors=$((errors + 1))
fi

# ── Check H5: runtime-truth fields forbidden anywhere in the file ─────────
if grep -qE '^[[:space:]]*(ci_status|last_run|ci_run_id|ci_artifact|failure_summary):' "$EXTRACTED_PATH"; then
  printf 'RUNTIME_FIELD: runtime-truth field key found in the staging file (runtime truth lives only in the CI-owned ledger)\n' >&2
  errors=$((errors + 1))
fi

ids="$(extracted_ids)"

# ── Check H6: no duplicate EXTRACTED-<n> id ────────────────────────────────
for dup in $(printf '%s\n' "$ids" | sort | uniq -d); do
  [ -z "$dup" ] && continue
  printf 'DUPLICATE_EXTRACTED_ID: %s appears more than once — only the first block is validated\n' "$dup" >&2
  errors=$((errors + 1))
done
ids="$(printf '%s\n' "$ids" | sort -u)"

# ── Check H7: anti-vacuous — zero entries ──────────────────────────────────
if [ -z "$ids" ]; then
  printf 'NO_EXTRACTED_ENTRIES: no "## EXTRACTED-<n>" entries found in the staging file\n' >&2
  errors=$((errors + 1))
fi

# needs_human_confirm and extraction_sources are deliberately NOT in this
# list: each has its OWN dedicated code (NEEDS_CONFIRM_INVALID,
# SOURCES_MISSING) that already covers total absence — including them here
# too would double-report the same root cause under two codes (mirrors
# lint-journey-inbox.sh's simulator_trace/TRACE_MISSING precedent).
# oracle/oracle_gap are likewise excluded — ORACLE_EXACTLY_ONE covers their
# joint absence.
REQUIRED_FIELDS="confirmation_status grade origin persona goal priority \
covers flows oracle_surface negative_states steps evidence test runner \
author_status"

NONEMPTY_FIELDS="confirmation_status grade origin persona goal priority \
covers oracle_surface runner author_status"

for id in $ids; do
  [ -z "$id" ] && continue
  block="$(extracted_block "$id")"

  # ── Check E0: id must be a positive integer (never zero) ───────────────
  _num="${id#EXTRACTED-}"
  _stripped="$(printf '%s' "$_num" | sed 's/^0*//')"
  if [ -z "$_stripped" ]; then
    printf 'BAD_EXTRACTED_ID: %s: id must be a positive integer, not zero\n' "$id" >&2
    errors=$((errors + 1))
  fi

  # ── Check E1: heading grammar, UP FRONT (L23) ───────────────────────────
  # extracted_block's reader is permissive ('^## EXTRACTED-<n>([^0-9]|$)');
  # this check validates the canonical strict form independently and first,
  # before any field-level check — the same discipline
  # journey-reality-intake.sh / journey-inbox-triage.sh apply (V-T5 F1).
  _heading="$(printf '%s\n' "$block" | head -n1)"
  if ! printf '%s\n' "$_heading" | grep -qE '^## EXTRACTED-[0-9]+ — ".+"$'; then
    printf 'ENTRY_HEADING_INVALID: %s: heading must match %s (spaced em-dash, double-quoted title; found: %s)\n' \
      "$id" '## EXTRACTED-<digits> — "<title>"' "$_heading" >&2
    errors=$((errors + 1))
  fi

  # ── Check E2: required fields present ───────────────────────────────────
  for field in $REQUIRED_FIELDS; do
    if ! printf '%s\n' "$block" | grep -qE "^${field}:"; then
      printf 'MISSING_FIELD: %s: %s\n' "$id" "$field" >&2
      errors=$((errors + 1))
    fi
  done

  # ── Check E3: NONEMPTY required fields must have a non-blank value ─────
  for field in $NONEMPTY_FIELDS; do
    _nv="$(extracted_field "$id" "$field" 2>/dev/null)" || continue
    if [ -z "$_nv" ]; then
      printf 'BLANK_FIELD: %s: %s\n' "$id" "$field" >&2
      errors=$((errors + 1))
    fi
  done

  # ── Check E4: needs_human_confirm (I2) — ungated, absence == wrong ──────
  _nhc="$(extracted_field "$id" needs_human_confirm 2>/dev/null)" || _nhc=""
  if [ "$_nhc" != "true" ]; then
    printf 'NEEDS_CONFIRM_INVALID: %s: needs_human_confirm must be exactly "true" (found: %s)\n' \
      "$id" "${_nhc:-<missing>}" >&2
    errors=$((errors + 1))
  fi

  # ── Check E5: confirmation_status enum + REJECTED requires rejected_reason
  _cstatus="$(extracted_field "$id" confirmation_status 2>/dev/null)" || _cstatus=""
  if [ -n "$_cstatus" ] && ! in_enum "$_cstatus" PENDING CONFIRMED REJECTED; then
    printf 'CONFIRM_STATUS_INVALID: %s: %s\n' "$id" "$_cstatus" >&2
    errors=$((errors + 1))
  fi
  if [ "$_cstatus" = "REJECTED" ]; then
    _rreason="$(extracted_field "$id" rejected_reason 2>/dev/null)" || _rreason=""
    if [ -z "$_rreason" ]; then
      printf 'REJECTED_REASON_MISSING: %s\n' "$id" >&2
      errors=$((errors + 1))
    fi
  fi

  # ── Check E6: grade enum ────────────────────────────────────────────────
  _grade="$(extracted_field "$id" grade 2>/dev/null)" || _grade=""
  if [ -n "$_grade" ] && ! in_enum "$_grade" "[C]" "[I]" "[G]" "[X]"; then
    printf 'GRADE_UNKNOWN: %s: %s\n' "$id" "$_grade" >&2
    errors=$((errors + 1))
  fi

  # ── Check E7: origin restricted to EXTRACTED ────────────────────────────
  _origin="$(extracted_field "$id" origin 2>/dev/null)" || _origin=""
  if [ -n "$_origin" ] && [ "$_origin" != "EXTRACTED" ]; then
    printf 'BAD_ORIGIN: %s: %s (only EXTRACTED is allowed in this file)\n' "$id" "$_origin" >&2
    errors=$((errors + 1))
  fi

  # ── Check E8: author_status restricted to UNWRITTEN ─────────────────────
  _astatus="$(extracted_field "$id" author_status 2>/dev/null)" || _astatus=""
  if [ -n "$_astatus" ] && [ "$_astatus" != "UNWRITTEN" ]; then
    printf 'BAD_AUTHOR_STATUS: %s: %s (only UNWRITTEN is allowed in this file)\n' "$id" "$_astatus" >&2
    errors=$((errors + 1))
  fi

  # ── Check E9: EXACTLY ONE of oracle:/oracle_gap: (spec §9.4, L5) ────────
  _has_oracle=0
  printf '%s\n' "$block" | grep -qE '^oracle:' && _has_oracle=1
  _has_gap=0
  printf '%s\n' "$block" | grep -qE '^oracle_gap:' && _has_gap=1

  if [ "$_has_oracle" -eq 1 ] && [ "$_has_gap" -eq 1 ]; then
    printf 'ORACLE_EXACTLY_ONE: %s: both oracle: and oracle_gap: present (exactly one required)\n' "$id" >&2
    errors=$((errors + 1))
  elif [ "$_has_oracle" -eq 0 ] && [ "$_has_gap" -eq 0 ]; then
    printf 'ORACLE_EXACTLY_ONE: %s: neither oracle: nor oracle_gap: present (exactly one required)\n' "$id" >&2
    errors=$((errors + 1))
  elif [ "$_has_oracle" -eq 1 ]; then
    _oval="$(extracted_field "$id" oracle 2>/dev/null)" || _oval=""
    if [ -z "$_oval" ]; then
      printf 'BLANK_FIELD: %s: oracle\n' "$id" >&2
      errors=$((errors + 1))
    fi
  else
    _gval="$(extracted_field "$id" oracle_gap 2>/dev/null)" || _gval=""
    if [ -z "$_gval" ]; then
      printf 'ORACLE_GAP_FORMAT: %s: oracle_gap value is blank (must state the question a human must answer)\n' "$id" >&2
      errors=$((errors + 1))
    fi
  fi

  # ── Check E10: resolution:/resolved_from: pairing (spec §14 locks 2/3) ──
  _has_resolution=0
  printf '%s\n' "$block" | grep -qE '^resolution:' && _has_resolution=1
  _has_resolved_from=0
  printf '%s\n' "$block" | grep -qE '^resolved_from:' && _has_resolved_from=1

  if [ "$_has_resolution" -eq 1 ] && [ "$_has_resolved_from" -eq 0 ]; then
    printf 'RESOLVED_FROM_MISSING: %s: resolution: present without resolved_from:\n' "$id" >&2
    errors=$((errors + 1))
  elif [ "$_has_resolution" -eq 0 ] && [ "$_has_resolved_from" -eq 1 ]; then
    printf 'RESOLVED_FROM_MISSING: %s: resolved_from: present without resolution:\n' "$id" >&2
    errors=$((errors + 1))
  elif [ "$_has_resolution" -eq 1 ] && [ "$_has_resolved_from" -eq 1 ]; then
    _rf="$(extracted_field "$id" resolved_from 2>/dev/null)" || _rf=""
    if ! in_enum "$_rf" "[X]" "[G]" "[I]"; then
      printf 'RESOLVED_FROM_MISSING: %s: resolved_from must be one of [X] | [G] | [I] (found: %s)\n' "$id" "$_rf" >&2
      errors=$((errors + 1))
    fi
  fi

  # ── Check E11: extraction_sources grammar + cardinality (I1, I9) ───────
  # Three grammars are accepted, mutually exclusive by construction:
  #   code-cite:    - <path>:<line> — "<quote>"
  #   section-cite: - <path>#<heading>
  #   search-cite:  - search: grep -rFn -- "<literal>" <relpath>
  # The search-cite (DX-1, live-characterization fix wave) is the ONLY
  # legal absence-evidence form — it reuses journey/docs/uat-report-
  # format.md §2.2's restricted search-line grammar verbatim (same
  # non-empty-fixed-literal / no-quote-or-backslash / repo-relative-path
  # restrictions), byte-verified at the pinned commit by
  # check-extracted-provenance.sh (task E2), never here. A search-cite
  # counts toward this check's cardinality exactly like the other two
  # forms — an [X] entry's code side is legitimately a search-cite.
  _src="$(printf '%s\n' "$block" | awk '
    /^extraction_sources:/{ins=1; next}
    ins && /^[a-zA-Z_][a-zA-Z0-9_]*:/{exit}
    ins && /^## /{exit}
    ins{print}
  ')"

  _src_count=0
  while IFS= read -r _sline; do
    case "$_sline" in
      '') continue ;;
    esac
    _src_count=$((_src_count + 1))
    _fmt_bad=1
    _hybrid=0
    if printf '%s\n' "$_sline" | grep -qE '^  - search: grep -rFn -- "[^"\\]+" [A-Za-z0-9._/-]+$'; then
      _spath="$(printf '%s\n' "$_sline" | awk '{print $NF}')"
      case "$_spath" in
        /*|*..*) _fmt_bad=1 ;;
        *) _fmt_bad=0 ;;
      esac
    elif printf '%s\n' "$_sline" | grep -qE '^  - [A-Za-z0-9._/-]+:[0-9]+ — ".+"$'; then
      _spath="$(printf '%s\n' "$_sline" | awk -F':' '{s=$1; sub(/^  - /,"",s); print s}')"
      case "$_spath" in
        /*|*..*) _fmt_bad=1 ;;
        *) _fmt_bad=0 ;;
      esac
    elif printf '%s\n' "$_sline" | grep -qE '^  - [A-Za-z0-9._/-]+#[^#]+$'; then
      # DX-5: a section-cite heading containing a literal double-quote is
      # almost certainly a hybrid line-cite/section-cite paste (a model
      # gluing a quote onto a #heading reference) — reject it HERE, with a
      # specific, actionable message, rather than let it "validate" as a
      # section-cite whose heading text will never match a real ATX
      # heading (a confusing downstream SECTION_HEADING_MISSING at the
      # provenance gate instead of a clear grammar error at lint time).
      _sheading="$(printf '%s\n' "$_sline" | sed 's/^[^#]*#//')"
      case "$_sheading" in
        *'"'*) _fmt_bad=1; _hybrid=1 ;;
        *)
          _spath="$(printf '%s\n' "$_sline" | awk -F'#' '{s=$1; sub(/^  - /,"",s); print s}')"
          case "$_spath" in
            /*|*..*) _fmt_bad=1 ;;
            *) _fmt_bad=0 ;;
          esac
          ;;
      esac
    fi
    if [ "$_hybrid" -eq 1 ]; then
      printf 'SOURCE_FORMAT: %s: %s — looks like a hybrid cite — use a line-cite\n' "$id" "$_sline" >&2
      errors=$((errors + 1))
    elif [ "$_fmt_bad" -eq 1 ]; then
      printf 'SOURCE_FORMAT: %s: %s\n' "$id" "$_sline" >&2
      errors=$((errors + 1))
    fi
  done << _SRC_EOF_
$_src
_SRC_EOF_

  if [ "$_src_count" -eq 0 ]; then
    printf 'SOURCES_MISSING: %s: at least 1 extraction_sources line is required\n' "$id" >&2
    errors=$((errors + 1))
  elif [ "$_grade" = "[X]" ] && [ "$_src_count" -lt 2 ]; then
    printf 'X_ONE_SIDED: %s: grade [X] requires at least 2 extraction_sources lines (both sides)\n' "$id" >&2
    errors=$((errors + 1))
  elif [ "$_has_resolution" -eq 1 ] && [ "$_src_count" -lt 2 ]; then
    printf 'SOURCES_MISSING: %s: at least 2 extraction_sources lines are required when resolution: is present\n' "$id" >&2
    errors=$((errors + 1))
  fi

  # ── Check E12: prior_e2e (optional, staging-only, §9.3) ─────────────────
  if printf '%s\n' "$block" | grep -qE '^prior_e2e:'; then
    _pe="$(extracted_field "$id" prior_e2e 2>/dev/null)" || _pe=""
    _pe_bad=0
    printf '%s' "$_pe" | grep -qE '^[A-Za-z0-9._/-]+$' || _pe_bad=1
    case "$_pe" in
      /*|*..*) _pe_bad=1 ;;
    esac
    if [ "$_pe_bad" -eq 1 ]; then
      printf 'PRIOR_E2E_FORMAT: %s: %s\n' "$id" "${_pe:-<blank>}" >&2
      errors=$((errors + 1))
    fi
  fi

  # ── Check E13: promoted_as grammar (OPTIONAL field, CONFIRMED-only) ─────
  if printf '%s\n' "$block" | grep -qE '^promoted_as:'; then
    _pas="$(extracted_field "$id" promoted_as 2>/dev/null)" || _pas=""
    if ! printf '%s\n' "$_pas" | grep -qE '^JOURNEY-[0-9]+$'; then
      printf 'PROMOTED_AS_INVALID: %s: %s\n' "$id" "$_pas" >&2
      errors=$((errors + 1))
    elif [ "$_cstatus" != "CONFIRMED" ]; then
      printf 'PROMOTED_AS_INVALID: %s: promoted_as present but confirmation_status is %s (must be CONFIRMED)\n' \
        "$id" "${_cstatus:-<blank>}" >&2
      errors=$((errors + 1))
    fi
  fi

done

[ "$errors" -gt 0 ] && exit 1
exit 0
