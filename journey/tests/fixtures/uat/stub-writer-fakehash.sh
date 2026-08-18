#!/bin/sh
# shellcheck shell=sh
# stub-writer-fakehash.sh PROMPT_FILE INPUT_FILE -> stdout
#
# Same shape as stub-writer-backend.sh's claim-1, but the artifact evidence
# line carries an invented hash instead of copying the manifest's real
# one. Proves the runner composes check-uat-evidence.sh (gate 4.2) BEFORE
# install: an artifact evidence line whose hash the gate cannot verify
# against the real bytes (ARTIFACT_HASH_MISMATCH) must never reach OUTDIR
# (journey/tests/uat-write-run_test.sh) -- exactly the "you cannot compute
# hashes; any artifact evidence not in the manifest is forbidden" law the
# writer prompt teaches.
set -u
in="${2:?usage: stub-writer-fakehash.sh PROMPT_FILE INPUT_FILE}"

[ -n "${UAT_STUB_SENTINEL:-}" ] && : > "$UAT_STUB_SENTINEL"

_date="$(sed -n 's/^REPORT_DATE: //p' "$in" | head -1)"
_commit="$(sed -n 's/^REPO_COMMIT: //p' "$in" | head -1)"

cat <<EOF
# UAT-REPORT
report_date: $_date
repo_commit: $_commit
app_target: http://127.0.0.1:3002

## UAT-CLAIM-1: Send action surfaced HTTP 500
- journey_ids: JOURNEY-106
- grade: [C]
- claim: Clicking Send on the PDA screen returned HTTP 500 to the user.
- evidence: artifact evidence/journey-106-send-500.png sha256:0000000000000000000000000000000000000000000000000000000000000000
EOF
