#!/bin/sh
# shellcheck shell=sh
# stub-writer-badclaim.sh PROMPT_FILE INPUT_FILE -> stdout
#
# Same shape as stub-writer-backend.sh's claim-1, but omits the required
# `- claim: ` line. Proves the runner composes lint-uat-report.sh (gate
# 4.1) BEFORE install: a schema-invalid model output (HEADER_MISSING --
# lint's own reuse note: "missing claim line") must never reach OUTDIR
# (journey/tests/uat-write-run_test.sh).
set -u
in="${2:?usage: stub-writer-badclaim.sh PROMPT_FILE INPUT_FILE}"

[ -n "${UAT_STUB_SENTINEL:-}" ] && : > "$UAT_STUB_SENTINEL"

_date="$(sed -n 's/^REPORT_DATE: //p' "$in" | head -1)"
_commit="$(sed -n 's/^REPO_COMMIT: //p' "$in" | head -1)"
_art1="$(grep '^evidence/journey-106-send-500.png sha256:' "$in" | sed 's/^evidence\/journey-106-send-500.png sha256://')"

cat <<EOF
# UAT-REPORT
report_date: $_date
repo_commit: $_commit
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: Send action surfaced HTTP 500
- journey_ids: JOURNEY-106
- grade: [C]
- evidence: artifact evidence/journey-106-send-500.png sha256:$_art1
EOF
