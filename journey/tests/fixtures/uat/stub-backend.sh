#!/bin/sh
# shellcheck shell=sh
# stub-backend.sh PROMPT_FILE INPUT_FILE -> stdout
#
# Test double for JOURNEY_GEN_BACKEND (journey/gen/runners/uat-verify-run.sh,
# journey/tests/uat-runner_test.sh). Reads the runner-built input file ($2:
# a "CHECKED_HASH: <sha>" line, a "REPO_ROOT: <abs path>" line, a blank
# line, then the report verbatim), copies the hash back out, and emits a
# valid ALL-CONFIRM verification BODY for the 2026-07-08 golden report's
# claims (no `reviewed_sha256:`/`repo_root:` lines — the runner stamps both
# itself after this backend returns, W1/D2).
#
# Gate-valid all-confirm for that report needs claim-1/3's evidence quotes
# and claim-2's search lines (a confirm of a [C-absent] claim needs >=1
# search or check-uat-verification.sh raises ABSENCE_NO_SEARCH). Rather
# than re-deriving that shape here, this stub emits the verdict-block BODY
# of the fixture's own golden verification template verbatim (everything
# after its `reviewed_sha256: @RSHA@` line and the blank line under it),
# substituting the extracted hash for `@RSHA@` — the same fixture the
# runner test builds the report from, so the two can never drift apart.
#
# Also touches $UAT_STUB_SENTINEL (if set) so tests can prove whether this
# backend was actually invoked (used to assert precondition failures never
# reach the backend).
set -u
_here="$(cd "$(dirname "$0")" && pwd)"
in="${2:?usage: stub-backend.sh PROMPT_FILE INPUT_FILE}"

[ -n "${UAT_STUB_SENTINEL:-}" ] && : > "$UAT_STUB_SENTINEL"

hash="$(sed -n 's/^CHECKED_HASH: //p' "$in" | head -1)"

_tpl="$_here/templates/UAT_REPORT_2026-07-08.verification.md.in"
# lines 1-3 of the template are "reviewed_sha256: @RSHA@" + "repo_root:
# @REPO_ROOT@" + a blank line; line 4 onward is the verdict-block body this
# backend is responsible for (the model never emits either header line —
# W1/D2, both runner-owned).
tail -n +4 "$_tpl" | sed "s/@RSHA@/$hash/g"
