# Journey Coverage Gaps — VIMS Audit Module (v3)

Structured coverage-gap register consumed by the doc-format gate's `--allow-unlinked`
mode (`journey/bin/check-doc-format.sh` — its `UNLINKED_FEAT` note requires every
deferred id to become a structured gap here, never an invented journey). Coverage
accounting (`JOURNEY_MAP.md` header): 78 P0/P1 anchors = 76 journey-covered + the 2 gap
records below. Both records are build-time infrastructure with no user-facing surface —
forcing them into a user journey would fabricate behaviour no persona performs.
Reviewer values are placeholders pending Prince's confirmation at final review.

## GAP-1
source_id: FEAT-AUD-1401
source_type: FEAT
reason: build-time infrastructure (additive DB migration) — no user-facing surface to journey; validated by the migration up/down test on a copy of ksm_cms_live (IMPLEMENTATION_PLAN Phase 1 tests), not by a Playwright journey
owner: product-owner
reviewer: PENDING-PRINCE
expires: 2026-10-11

## GAP-2
source_id: FEAT-AUD-1403
source_type: FEAT
reason: build-time infrastructure (DB Table Creation Standard verification grep, MIGRATION.md §4 / IMPLEMENTATION_PLAN step 1.5 "build fails on any violation") — a build-gate script with no user surface; validated by running the grep in CI, not by a Playwright journey
owner: product-owner
reviewer: PENDING-PRINCE
expires: 2026-10-11
