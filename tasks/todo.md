# Safety Session Plan - Step 7.8

Session state: completed

## Scope
- Continue from `docsuite/progress.txt`, which is the live handoff and points to Step `7.8`.
- Implement Step `7.8` in the handover workspace only.
- Add the retention / orphan-cleanup backend surface without widening into Phase `8` deferral resolution or unrelated frontend work.

## Assumptions
1. The user's instruction to continue from where the workspace left off is approval to proceed directly with Step `7.8` from `docsuite/progress.txt`.
2. Because soft-archive deferral `#3` is still unresolved, the Step `7.8` retention cutoff should key off the current `archived_at` sentinel instead of inventing a second archive-state mechanism mid-phase.
3. Because `D-GAP-M33` deletes parent-tied `vims_safety_field_history` rows when the parent record is purged, the required retention/orphan cleanup audit trail in this workspace should use system-scoped append-only history rows rather than parent-bound rows that would be deleted in the same transaction.
4. Attachment cleanup in this handover workspace should operate only inside the configured Safety storage root and should skip generated `exports/` artifacts so Step `7.8` does not delete PDF bundle outputs that are outside the attachment-cleanup contract.

## Planned Work
- [x] Add the Step `7.8` backend task and service files:
  - `apps/safety/tasks/retention_job.py`
  - `apps/safety/tasks/orphan_attachment_cleanup.py`
  - `apps/safety/services/attachment_replace_handler.py`
- [x] Implement retention hard-delete behavior against the current archive sentinel:
  - purge archived Incident / Near Miss, SCM, and SOI parents older than `SAFETY_RETENTION_DAYS`
  - delete child rows that do not have real FK cascades in the handover workspace
  - remove linked attachment files from Safety storage
  - append system-scoped retention summary audit rows
- [x] Implement orphan attachment cleanup and same-filename replace handling:
  - detect referenced attachment paths from the current workspace models / audit payloads
  - delete orphan files under the Safety storage root
  - keep `exports/` artifacts out of scope
  - capture same-filename replace audit metadata
- [x] Add focused Step `7.8` coverage:
  - `tests/safety/test_retention_job.py`
  - `tests/safety/test_orphan_cleanup.py`
  - `tests/safety/test_same_filename_replace.py`
- [x] Run focused Step `7.8` verification.
- [x] Update `docsuite/progress.txt` and this file at session close with the carried seams and verification results.

## Known Drifts To Carry Explicitly
- `AGENTS.md` still says to begin at Step `0.1`, but `docsuite/progress.txt` is the authoritative live handoff.
- Step `7.8` says "hard-delete records > 1095 days old," while the lower-priority PRD wording still says attachment links persist after purge; implementation should follow the stronger Step `7.8` / backend contract and record the drift.
- The wider handover-workspace seam from Step `5.1` still applies: task helpers can exist here, but real Celery-beat registration in the actual platform runtime is still not proven in this package.

## Review Notes
- The retention job follows the current `archived_at` soft-archive sentinel because Phase `8.3` still owns the unresolved archive-shape deferral.
- Parent-bound history rows still purge with deleted Incident / Near Miss, SCM, and SOI records, so the Step `7.8` purge summary is captured in system-scoped `vims_safety_field_history` rows instead.
- `docsuite/LESSONS.md` now carries `L-067` so the retention-summary vs parent-bound history purge conflict does not get reintroduced in a later cleanup step.
- Focused verification passed:
  - `python -m unittest tests.safety.test_retention_job tests.safety.test_orphan_cleanup tests.safety.test_same_filename_replace -v`
  - `python -m unittest tests.safety.test_archive_opt_in tests.safety.test_auditor_zip -v`
