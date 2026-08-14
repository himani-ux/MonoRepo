# VIMS-AUDIT-HANDOVER handover · v5

Step 2 DocSuite complete; SSOT v0.21 frozen 2026-05-19 (issued 2026-05-20; v4
2026-07-14 — the FINAL v4 package, a complete rerun per owner Control 2; the
prior v4 build was declared VOID and rebuilt from scratch, see
`UPGRADE-v4.md`. v5 2026-07-17 — hygiene reissue + re-vendor to KLOSS
`0acd2b9`, owner-ordered per review verdict 2026-07-17; a first v5 candidate
was declared VOID (owner Control 2) for two doc-accuracy defects and rebuilt
fresh from independently verified v4 bytes, see `UPGRADE-v5.md`). COVERAGE
237/237 GREEN (N=925). **Domain 12 personas (8),
Domain 13 quality gates, and Domain 14 release runbook are GENERATED and
executable**; code-dependent quality lenses are `NOT_APPLICABLE_YET` with
activation points (no app code exists yet) — never a PASS. **Release is
BLOCKED: `deploy.method` is `DEFERRED:D-AUDRS-453` until KSM India supplies
the exact command** (7 closure facts listed in the runbook). Zero
shared-table DDL; approved-exception list EMPTY. Open: PSB-2 (pre-ship
review), PSB-4 (Tier-R), 3 agent-DRAFT mocks pending owner approval,
gap-record reviewers PENDING-PRINCE. See `docs/BLOCKERS.md`.

Start with `START_PROMPT.md`, then consult `MANIFEST.md` for the
full file index.

## Read in this order

1. `AGENTS.md` — thin entry point
2. `docs/CLAUDE.md` — **project law** (KLOSS Step 3 operating system)
3. `progress.txt` — where the project stands
4. `docs/IMPLEMENTATION_PLAN.md` — the 14-phase build blueprint (`Visual reference:` mock citations)
5. `docs/PRD.md` — features as machine-readable `FEAT-AUD-<n>` blocks (id-rename band map in §21)
6. `docs/APP_FLOW.md` — `## Screens` (routes + states) and `## User Journeys` (AFJs), original prose preserved below
7. `JOURNEY_MAP.md` — the 14 authored journeys (UNWRITTEN — intent, not runtime evidence) + `JOURNEY_COVERAGE_GAPS.md` + `JOURNEY_COVERAGE_MANIFEST.json` (generated coverage evidence, regenerate — never hand-edit)
8. `docs/PERSONAS.md` — P1..P8, mirrors the SSOT `## Personas` companion section; `PERSONA_COVERAGE_GAPS.md` holds the 2 structured gap records
9. `docs/QUALITY_GATES.md` — Domain 13 law (tool pins, thresholds, never-waivable rules AUDQ-001..003, `QUALITY-MACHINE-BLOCK`); enforced by `checks/*.sh`
10. `RELEASE_RUNBOOK.md` (root) — Domain 14 law; `deploy.method` DEFERRED, crossing BLOCKED until KSM India closes D-AUDRS-453
11. `docs/BACKEND_STRUCTURE.md` + `docs/DATA_MODEL.md`
12. `docs/PRESENT_STATE_VERIFICATION.md` — **live-DB truth; overrides SSOT §2**
13. `docs/FIELD_MAP.md` — DB→API→UI trace artefact (§11 = known UI-cell debt)
14. `MANIFEST.md` — the full file index for this package (no separate INDEX.md)

## Folder map

- `docs/` — the canonical build docs (CLAUDE.md, IMPLEMENTATION_PLAN.md, PRD.md,
  BACKEND_STRUCTURE.md, DATA_MODEL.md, PRESENT_STATE_VERIFICATION.md, FIELD_MAP.md,
  PERSONAS.md, QUALITY_GATES.md, etc.) + COVERAGE.md + GAP_ANALYSIS.md + BLOCKERS.md +
  FRAMEWORK_COMPATIBILITY.md + MOCK_COVERAGE_GAPS.md — plus `docs/seeds/` and `docs/mockups/`.
- `ssot/` — the frozen SSOT v0.21 (now carrying the dated `## Personas` companion section) +
  the interrogation register (Step 1 baseline).
- `cross-module/` — auth, Certs, Safety, CMS-WRH SSOTs for integration discipline.
- `docs/seeds/` — the seed CSV sets + provenance siblings (all DPA-reviewed 2026-05-20).
- `docs/mockups/` — per-screen visual references under the mocks contract: 9
  owner-approved `reference` mocks (byte-verbatim split of the original element-ID'd
  boards), 3 agent `draft` mocks pending owner approval, and the superseded monolith at
  `docs/mockups/legacy-audit-all-screens.html`; the one unmocked screen is gap-recorded
  in `docs/MOCK_COVERAGE_GAPS.md` (reviewer PENDING-PRINCE).
- `JOURNEY_MAP.md`, `JOURNEY_COVERAGE_GAPS.md`, `JOURNEY_COVERAGE_MANIFEST.json` (root) —
  14 journeys, origin PERSONA, all UNWRITTEN; the manifest is generated evidence
  (`journey/bin/generate-journey-coverage-manifest.sh`), never hand-authored — regenerate,
  don't edit. The coverage gate that consumes it (`journey/bin/check-journey-coverage.sh`)
  is proven executable against this exact delivered package (not just the source staging tree).
- `PERSONA_COVERAGE_GAPS.md` (root) — the 2 structured persona-coverage gap records
  (reviewer PENDING-PRINCE).
- `RELEASE_RUNBOOK.md` (root) — Domain 14 release law, generated and executable;
  `deploy.method` DEFERRED (D-AUDRS-453) is the module's one release blocker; crossing
  is BLOCKED. Never invent a deploy command.
- `checks/` — the project's own generated Domain 13 gates: `check-hygiene.sh`,
  `check-security.sh`, `check-perf.sh`, `quality-gate.sh`, `gate-detect-lib.sh`
  (see `checks/README.md`), plus `checks/release/*.sh` (`backend-tests.sh`,
  `frontend-tests.sh`, `rbac-grid-test.sh`, `psc-car-regression.sh`,
  `shared-code-diff.sh`) — required release checks, shipped FAIL-CLOSED until Phase 0
  wires them to real suites.
- `quality/`, `release/`, `journey/`, `mocks/`, `evolution/` — vendored KLOSS framework
  tooling, byte-identical to framework commit `0acd2b9` (Control 1) — see
  `docs/FRAMEWORK_COMPATIBILITY.md` for the full `827ea2b`→`0acd2b9` delta (release/ layer
  only: `release-attest.sh` MODIFIED +59 lines adding §2c runbook-linter verdict-line
  validation to the existing fail-closed gate, 2 new tests, 1 modified test). The mock,
  journey, persona, quality-contract, and release-runbook-lint gates all run against these
  delivered copies.
- `UPGRADE-v2.md`, `UPGRADE-v3.md`, `UPGRADE-v4.md`, `UPGRADE-v5.md` — re-issue history
  (what changed and why, per version; `UPGRADE-v4.md` records why the prior v4 build was
  VOID; `UPGRADE-v5.md` records why a first v5 candidate was VOID).
- `MANIFEST.md`, `PROVENANCE.md`, `PROVENANCE-MANIFEST.sha256` — generated file index and
  byte-integrity records (structure and byte integrity only, not correctness or currency).

Critical implementation invariants are restated in `START_PROMPT.md` (the copy-paste first
prompt) rather than duplicated here.
