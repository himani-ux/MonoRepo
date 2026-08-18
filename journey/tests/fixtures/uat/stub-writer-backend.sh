#!/bin/sh
# shellcheck shell=sh
# stub-writer-backend.sh PROMPT_FILE INPUT_FILE -> stdout
#
# Test double for JOURNEY_GEN_BACKEND (journey/gen/runners/uat-write-run.sh,
# journey/tests/uat-write-run_test.sh). Reads the runner-built bundle ($2:
# REPORT_DATE:/REPO_COMMIT: lines, an ARTIFACT MANIFEST, session notes, and
# an optional JOURNEY MAP EXCERPT), echoes REPORT_DATE/REPO_COMMIT into the
# report header exactly as the writer prompt requires, and copies the two
# artifact hashes straight out of the manifest -- this stub never computes
# a hash itself, matching the real prompt's own "you cannot compute
# hashes" law.
#
# Emits the SAME five-claim shape as journey/tests/fixtures/uat/golden/
# UAT_REPORT_2026-07-08.md (byte-identical claim bodies) so it is
# lint-clean and evidence-clean against the identical fixture repo shape
# journey/tests/uat-write-run_test.sh builds (same paths/lines as
# uat-runner_test.sh's own fixture-repo builder).
#
# Also touches $UAT_STUB_SENTINEL (if set) so tests can prove whether this
# backend was actually invoked (used to assert precondition failures never
# reach the backend).
set -u
in="${2:?usage: stub-writer-backend.sh PROMPT_FILE INPUT_FILE}"

[ -n "${UAT_STUB_SENTINEL:-}" ] && : > "$UAT_STUB_SENTINEL"

_date="$(sed -n 's/^REPORT_DATE: //p' "$in" | head -1)"
_commit="$(sed -n 's/^REPO_COMMIT: //p' "$in" | head -1)"
_art1="$(grep '^evidence/journey-106-send-500.png sha256:' "$in" | sed 's/^evidence\/journey-106-send-500.png sha256://')"
_art2="$(grep '^evidence/journey-114-save-error.png sha256:' "$in" | sed 's/^evidence\/journey-114-save-error.png sha256://')"

cat <<EOF
# UAT-REPORT
report_date: $_date
repo_commit: $_commit
app_target: http://127.0.0.1:3002

Narrative prose is allowed here and carries no authority.

## UAT-CLAIM-1: Send action surfaced HTTP 500
- journey_ids: JOURNEY-106
- grade: [C]
- claim: Clicking Send on the PDA screen returned HTTP 500 to the user.
- evidence: src/pda/send.ts:12 — "throw new Error('portal timeout')"
- evidence: artifact evidence/journey-106-send-500.png sha256:$_art1

## UAT-CLAIM-2: No dev-auth bypass exists for UAT
- journey_ids: JOURNEY-106, JOURNEY-107
- grade: [C-absent]
- claim: The app has no development auth bypass usable for browser UAT.
- search: grep -rFn -- "PORTAL_MAGIC_BYPASS" config/

## UAT-CLAIM-3: Docs promise CSV export but code rejects it
- journey_ids: JOURNEY-109
- grade: [X]
- claim: PRD says invoices export to CSV; the export handler rejects csv.
- evidence: docs/PRD.md:8 — "invoices can be exported as CSV"
- evidence: src/export.ts:22 — "if (fmt === 'csv') reject()"

## UAT-CLAIM-4: Save errors likely redirect without message
- journey_ids: JOURNEY-114
- grade: [I]
- claim: Admin save failures redirect with a query flag and no visible error.
- evidence: artifact evidence/journey-114-save-error.png sha256:$_art2
- sample: 4 instances

## UAT-CLAIM-5: Tariff editor data source undetermined
- journey_ids: JOURNEY-113
- grade: [G]
- claim: Cannot determine from the browser whether tariff data load uses the versioned register.
EOF
