#!/bin/sh
# shellcheck shell=sh
# stub-writer-badcommit.sh PROMPT_FILE INPUT_FILE -> stdout
#
# Same shape as stub-writer-backend.sh, but `repo_commit:` echoes a wrong
# value instead of the runner-supplied REPO_COMMIT. Proves the runner's
# header echo check (uat-write-run.sh): the model never gets authority
# over the pinned repo_commit -- an echo mismatch must die before lint,
# evidence, or install ever run (journey/tests/uat-write-run_test.sh).
set -u
in="${2:?usage: stub-writer-badcommit.sh PROMPT_FILE INPUT_FILE}"

[ -n "${UAT_STUB_SENTINEL:-}" ] && : > "$UAT_STUB_SENTINEL"

_date="$(sed -n 's/^REPORT_DATE: //p' "$in" | head -1)"
_art1="$(grep '^evidence/journey-106-send-500.png sha256:' "$in" | sed 's/^evidence\/journey-106-send-500.png sha256://')"

cat <<EOF
# UAT-REPORT
report_date: $_date
repo_commit: 1111111111111111111111111111111111111111
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: Send action surfaced HTTP 500
- journey_ids: JOURNEY-106
- grade: [C]
- claim: Clicking Send on the PDA screen returned HTTP 500 to the user.
- evidence: artifact evidence/journey-106-send-500.png sha256:$_art1
EOF
