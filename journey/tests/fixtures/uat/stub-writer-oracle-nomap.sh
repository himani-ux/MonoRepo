#!/bin/sh
# shellcheck shell=sh
# stub-writer-oracle-nomap.sh PROMPT_FILE INPUT_FILE -> stdout
#
# Same shape as stub-writer-backend.sh's [C-absent] claim, plus a
# well-formed `- oracle_clause:` reference. Proves the runner's oracle-ref
# fail-closed precondition (uat-write-run.sh): a claim referencing an
# oracle clause with JOURNEY_MAP unset must die before install -- the
# runner cannot adjudicate scope without a map, and refuses to guess
# (journey/tests/uat-write-run_test.sh).
set -u
in="${2:?usage: stub-writer-oracle-nomap.sh PROMPT_FILE INPUT_FILE}"

[ -n "${UAT_STUB_SENTINEL:-}" ] && : > "$UAT_STUB_SENTINEL"

_date="$(sed -n 's/^REPORT_DATE: //p' "$in" | head -1)"
_commit="$(sed -n 's/^REPO_COMMIT: //p' "$in" | head -1)"

cat <<EOF
# UAT-REPORT
report_date: $_date
repo_commit: $_commit
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: Invoice hash verification is missing
- journey_ids: JOURNEY-101
- grade: [C-absent]
- claim: The app never confirms an uploaded invoice's hash matches the source manifest.
- search: grep -rFn -- "hash matches source manifest" src/
- oracle_clause: JOURNEY-101#1
EOF
