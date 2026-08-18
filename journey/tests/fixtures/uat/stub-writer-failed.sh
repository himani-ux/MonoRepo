#!/bin/sh
# shellcheck shell=sh
# stub-writer-failed.sh PROMPT_FILE INPUT_FILE -> stdout
#
# Emits the writer prompt's own degenerate-input token, bare, nothing
# else -- as if the model decided the session notes were unusable. Proves
# uat-write-run.sh dies loudly on WRITER-FAILED with nothing installed
# (journey/tests/uat-write-run_test.sh).
set -u
: "${2:?usage: stub-writer-failed.sh PROMPT_FILE INPUT_FILE}"

[ -n "${UAT_STUB_SENTINEL:-}" ] && : > "$UAT_STUB_SENTINEL"

printf 'WRITER-FAILED: session notes contain no discernible observations\n'
