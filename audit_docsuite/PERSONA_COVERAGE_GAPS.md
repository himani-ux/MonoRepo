# Persona Coverage Gaps — VIMS Audit Module (Domain 12, D-AUDRS-295)

Structured persona-coverage gap register, consumed by `journey/bin/check-persona-coverage.sh` as **its
own artifact** (the gate never reads `JOURNEY_COVERAGE_GAPS.md` for this purpose — a persona gap must be
declared here, explicitly).

**The rule (owner brief §1): a journey is NEVER invented to satisfy the gate.** Both FEATs below are
**build-time infrastructure with no user-facing surface** — no persona performs them, so forcing them
into a user journey would fabricate behaviour that does not exist. They are validated by build/CI
evidence instead, as recorded in each record. The same two ids already carry journey-coverage gap
records in `JOURNEY_COVERAGE_GAPS.md` for the same reason; this file is the persona-lens equivalent.

Reviewer values are `PENDING-PRINCE` until confirmed at final review.

## GAP-P1
source_id: FEAT-AUD-1401
source_type: FEAT
reason: build-time infrastructure (additive Django migrations creating the 44 Audit-owned tables, zero DDL against any shared legacy table per D-AUDRS-288/289/290) — there is no screen, route or interaction for any persona to perform; validated by the Phase-1 migration up/down test on a copy of ksm_cms_live plus the pre/post schema-fingerprint probe (IMPLEMENTATION_PLAN 1.6, TEST_PLAN K-12/K-13), never by a persona journey
owner: product-owner
reviewer: PENDING-PRINCE
expires: 2026-10-12

## GAP-P2
source_id: FEAT-AUD-1403
source_type: FEAT
reason: build-time infrastructure (DB-Table-Creation-Standard verification grep, MIGRATION.md §4 / IMPLEMENTATION_PLAN step 1.5 — "build fails on any violation"; the AUDQ-002 PK gate in docs/QUALITY_GATES.md §3) — a build-gate script with no user surface; validated by running the gate in CI, never by a persona journey
owner: product-owner
reviewer: PENDING-PRINCE
expires: 2026-10-12

---

*Every other P0/P1 `FEAT-AUD-*` in `docs/PRD.md` is covered by at least one `origin: PERSONA` journey in
`JOURNEY_MAP.md` (JOURNEY-1..14, personas P1..P8 — see `docs/PERSONAS.md`). Persona set: SSOT §21
`## Personas` (D-AUDRS-295).*
