#!/bin/sh
# shellcheck shell=sh
# stub-backend-missingroot.sh PROMPT_FILE INPUT_FILE -> stdout
#
# Test double for JOURNEY_GEN_BACKEND: unconditionally emits the prompt's
# own MISSING-ROOT degenerate token (W1/D2 — uat-verifier.md), regardless of
# input. Proves journey/gen/runners/uat-verify-run.sh's pass-through of this
# token: exit 1, nothing written, same shape as MISSING-REPORT/MISSING-HASH
# pass-through (journey/tests/uat-runner_test.sh).
set -u
in="${2:?usage: stub-backend-missingroot.sh PROMPT_FILE INPUT_FILE}"

[ -n "${UAT_STUB_SENTINEL:-}" ] && : > "$UAT_STUB_SENTINEL"

printf 'MISSING-ROOT\n'
