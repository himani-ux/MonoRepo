# VIMS Safety Module - Session Task List

> Disposable per-session work plan. Clear between sessions. The source of truth for what to build is `IMPLEMENTATION_PLAN.md`; this file tracks the current session's subset only.

## Current session
- [x] Read session startup docs in required order through the Phase 0.1 decision surface.
- [x] Confirm current state from `progress.txt` (`Phase 0 - not started`, next step `0.1`).
- [x] Verify whether the actual VIMS monorepo is available in the current workspace.
- [ ] Confirm the real monorepo checkout path and platform prerequisites:
  - `apps/reporting/`
  - `apps/inspection/`
  - shared auth chain
  - DB router
  - `config/urls.py`
  - React `src/routes/`
- [ ] Execute Step `0.1` in the actual monorepo:
  - create `apps/safety/` scaffold and package stubs
  - register `SafetyConfig`
  - add `urls.py` / `admin.py` placeholders
  - create empty backend subpackages
  - create `tests/safety/test_app_registration.py`
  - create `tests/safety/test_db_connection.py`
- [ ] Run focused Step `0.1` verification in the monorepo:
  - app registration resolves
  - DB router keeps Safety on `ksm_marine_live`
  - no new DB alias introduced
  - live read preconditions for `master_role`, `master_RoleByVessel`, `master_applied_rank`

## Active blocker
- Current workspace is the handover package only. The Step `0.1` target paths from `IMPLEMENTATION_PLAN.md` do not exist here: `apps/`, `config/`, `src/`, `tests/`.
- Per `MONOREPO_KICKOFF_CHECKLIST.md`, implementation starts only after the actual VIMS monorepo is present locally.

## Review notes
<!-- Append review notes at session end. -->
