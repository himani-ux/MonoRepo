# shellcheck shell=sh
# journey-ledger.sh — Validation and status-lookup helpers for the CI-owned
# runtime ledger.  Source this file; do not execute it directly.
#
# Public interface:
#   journey_ledger_validate FILE
#   journey_ledger_status   JSON_STRING ID
#
# Deps: jq (1.5+), POSIX sh.
# Runtime truth (ci_status etc.) lives EXCLUSIVELY in the CI-owned ledger.
# This library must NEVER read from or write to JOURNEY_MAP.md.

# ── journey_ledger_validate FILE ─────────────────────────────────────────────
# Exit 0 iff FILE is a valid ledger per brief §C.
# On any violation: exit non-zero and print the reason to stderr.
# Fail closed: unreadable / malformed / missing required fields / invalid record
# all produce non-zero exit.
journey_ledger_validate() {
  _jlv_f="$1"

  # Rule 1: file must be readable
  if [ ! -r "$_jlv_f" ]; then
    printf 'journey_ledger_validate: file not readable: %s\n' "$_jlv_f" >&2
    return 1
  fi

  # Rule 1 cont: must parse as valid JSON
  if ! jq -e . "$_jlv_f" >/dev/null 2>&1; then
    printf 'journey_ledger_validate: not valid JSON: %s\n' "$_jlv_f" >&2
    return 1
  fi

  # Rule 2: top-level metadata. schema_version must be the NUMBER 1, not the
  # string "1" (jq: "1" == 1 is false), and not 2 / 1.0 etc.
  if ! jq -e '.schema_version == 1' "$_jlv_f" >/dev/null 2>&1; then
    printf 'journey_ledger_validate: schema_version must be numeric 1 (string "1" is rejected)\n' >&2
    return 1
  fi

  _jlv_ga=$(jq -r '.generated_at // empty' "$_jlv_f")
  if [ -z "$_jlv_ga" ]; then
    printf 'journey_ledger_validate: generated_at is missing or empty\n' >&2
    return 1
  fi

  _jlv_src=$(jq -r '.source // empty' "$_jlv_f")
  if [ -z "$_jlv_src" ]; then
    printf 'journey_ledger_validate: source is missing or empty\n' >&2
    return 1
  fi

  _jlv_jtype=$(jq -r 'if (.journeys | type) == "object" then "ok" else "fail" end' \
    "$_jlv_f")
  if [ "$_jlv_jtype" != "ok" ]; then
    printf 'journey_ledger_validate: .journeys must be an object\n' >&2
    return 1
  fi

  # Rule 3: per-record validation
  # jq exits 0 if it emits output (errors found) or 1 if empty (no errors).
  # We use `any` to detect the first violation and surface all via iteration.
  _jlv_errors=$(jq -r '
    def nonstr($v): ($v != null) and (($v | type) != "string");
    .journeys | to_entries[] |
    .key as $id |
    .value as $r |
    (
      if (nonstr($r.last_run) or nonstr($r.ci_run_id)
          or nonstr($r.ci_artifact) or nonstr($r.failure_summary)) then
        "record \($id): runtime evidence fields (last_run/ci_run_id/ci_artifact/failure_summary) must be strings when present"
      elif ($r.ci_status != "NOT_RUN" and
          $r.ci_status != "GREEN" and
          $r.ci_status != "RED" and
          $r.ci_status != "FLAKY") then
        "record \($id): ci_status invalid: \($r.ci_status // "null")"
      elif $r.ci_status == "GREEN" and (
        ($r.last_run    == null or $r.last_run    == "") or
        ($r.ci_run_id   == null or $r.ci_run_id   == "") or
        ($r.ci_artifact == null or $r.ci_artifact == "")
      ) then
        "record \($id): GREEN requires non-null non-empty last_run, ci_run_id, ci_artifact"
      elif ($r.ci_status == "RED" or $r.ci_status == "FLAKY") and
        ($r.failure_summary == null or $r.failure_summary == "") then
        "record \($id): \($r.ci_status) requires non-null non-empty failure_summary"
      else
        empty
      end
    )
  ' "$_jlv_f" 2>&1)

  if [ -n "$_jlv_errors" ]; then
    printf 'journey_ledger_validate: %s\n' "$_jlv_errors" >&2
    return 1
  fi

  return 0
}

# ── journey_ledger_status JSON_STRING ID ─────────────────────────────────────
# Echo the ci_status for ID from the given JSON string, or "NOT_RUN" if the ID
# is absent from .journeys.  Never echoes GREEN for an absent id.
journey_ledger_status() {
  _jls_json="$1"
  _jls_id="$2"
  printf '%s\n' "$_jls_json" | jq -r --arg id "$_jls_id" '
    .journeys[$id].ci_status // "NOT_RUN"
  '
}
