#!/bin/sh
# shellcheck shell=sh
# stub-backend-badhash.sh PROMPT_FILE INPUT_FILE -> stdout
#
# Test double for JOURNEY_GEN_BACKEND: same shape as stub-backend.sh's
# all-confirm body, but every `- checked_hash:` line reads the literal
# string "deadbeef" instead of the real hash extracted from the input.
# Proves the runner's stamp-after-validate path: check-uat-verification.sh
# recomputes the report's sha itself and rejects any echoed checked_hash
# that disagrees with it (STALE_VERIFICATION) — so this backend's output
# must never reach disk (journey/tests/uat-runner_test.sh case e).
set -u
_here="$(cd "$(dirname "$0")" && pwd)"
in="${2:?usage: stub-backend-badhash.sh PROMPT_FILE INPUT_FILE}"

[ -n "${UAT_STUB_SENTINEL:-}" ] && : > "$UAT_STUB_SENTINEL"

_tpl="$_here/templates/UAT_REPORT_2026-07-08.verification.md.in"
# @RSHA@ appears only inside "- checked_hash: @RSHA@" lines in the body
# (lines 4+, after reviewed_sha256/repo_root/blank — W1/D2), so
# substituting it with "deadbeef" here is sufficient to make every
# checked_hash line wrong without a second pass.
tail -n +4 "$_tpl" | sed 's/@RSHA@/deadbeef/g'
