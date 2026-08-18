#!/bin/sh
# shellcheck shell=sh
# stub-writer-oracle-inscope.sh PROMPT_FILE INPUT_FILE -> stdout
#
# Same shape as stub-writer-oracle-nomap.sh, but references clause #2
# (browser-classed in journey/tests/uat-write-run_test.sh's archetype map,
# mirroring journey/tests/uat-oracle-scope_test.sh's own JOURNEY_MAP_full
# fixture) instead of clause #1 (lower-classed). Proves the POSITIVE path:
# with JOURNEY_MAP set, a genuine browser-gap [C-absent] claim citing a
# browser-classed clause passes check-uat-oracle-scope.sh and installs
# cleanly.
set -u
in="${2:?usage: stub-writer-oracle-inscope.sh PROMPT_FILE INPUT_FILE}"

[ -n "${UAT_STUB_SENTINEL:-}" ] && : > "$UAT_STUB_SENTINEL"

_date="$(sed -n 's/^REPORT_DATE: //p' "$in" | head -1)"
_commit="$(sed -n 's/^REPO_COMMIT: //p' "$in" | head -1)"

cat <<EOF
# UAT-REPORT
report_date: $_date
repo_commit: $_commit
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: Row visibility is missing
- journey_ids: JOURNEY-101
- grade: [C-absent]
- claim: The uploaded row never appears in /invoices.
- search: grep -rFn -- "row visible in" src/
- oracle_clause: JOURNEY-101#2
EOF
