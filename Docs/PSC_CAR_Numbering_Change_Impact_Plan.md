# PSC-CAR Numbering Change - Impact/Planning Notes

**Date:** 2026-08-10  
**Scope:** Forward-only implementation completed without schema or historical data changes.

## Objective

Move future PSC-CAR numbers to a vessel-aware format:

`<VESSEL_CODE>-PSC-<YEAR>-<SEQUENCE>`

Example: `EAT-PSC-2026-001`

Existing CAR numbers must remain unchanged.

## Rule to enforce

- Sequence is **per vessel + per calendar year**.
- Restart at `001` for each vessel and each year.
- Preserve old historical numbers such as `PSC-2026-001` and do **not** overwrite them.
- Do not retroactively renumber old records unless a separate approval is taken.

## Implemented state

- CAR number is currently generated in:
  - `psc-backend/apps/inspection/deficiency_models.py` → `CAR.generate_car_number()`
- Auto-creation of CAR happens in:
  - `psc-backend/apps/inspection/signals.py` (post_save on `Deficiency`)
- New auto-created CARs use vessel-aware yearly sequence (`VESSEL-PSC-YYYY-SEQ`) using existing `psc_car`, `psc_deficiency`, and `psc_inspection` relationships.
- Legacy no-context generator calls still return `PSC-YYYY-SEQ` for compatibility with internal helpers/tests.

## Files/DB areas that will be affected

### Core numbering tables (must be considered)

1. `psc_car.car_number`
   - Column stores all CAR IDs and is currently the source of uniqueness/search.
   - Length is `VARCHAR(20)`; verify vessel-code length and year/sequence still fit.

### Related CAR-text surfaces (non-key storage, data values include CAR number)

2. `psc_activity_history.event_description`  
   - Stores strings like `CAR {car_number} created...`
3. `psc_audit_log`
   - Audit captures field-level changes; if car numbers are updated, `old_value/new_value` captures will reflect changes.
4. Notification payloads (not schema fields in the same way, but text output):
   - `psc-backend/apps/notifications/signals.py`
   - `psc-backend/apps/notifications/management/commands/check_overdue_actions.py`
   - `psc_backend/apps/car/views.py` (messages/comments)
5. Report/filename surfaces:
   - `psc-backend/apps/car/report_views.py`
   - `psc-backend/apps/inspection/report_views.py`
   - `psc-backend/apps/car/reports.py`
6. Search/filter API surfaces:
   - `psc-backend/apps/car/views.py` (`car_number__icontains` filter)

### Data consistency boundaries (must remain untouched to avoid breakage)

- `psc_deficiency` / `psc_inspection` links to `CAR` are FK-based and do not need update.
- `psc_corrective_action`, `psc_evidence`, `psc_physical_verification` and similar child tables link by `car_id`, not by number.
- `psc_car` uniqueness is enforced on `car_number`; sequence/format change must keep uniqueness.

## DB impact

- No mandatory mass DML on historical rows.
- No mandatory rename/reparenting of FK-linked CAR references.
- No schema change was made.
- No datatype change was made.
- No sequence counter table was added. Sequence is derived from existing CAR rows for the same vessel/year.

## Applied impact-safe plan

1. Keep legacy CARs unchanged.
2. Update generator method used by `auto_create_car` to pick vessel-aware sequence.
3. Resolve vessel code through `Deficiency -> Inspection -> vessel_id -> VesselData`.
4. Add targeted tests for:
   - new format for future rows;
   - same-vessel yearly increment;
   - per-vessel sequence isolation.
5. Validate external outputs:
   - CAR list/search APIs,
   - CAR detail payloads,
   - CAR export filename generation,
   - audit/notification message text.

## Risk watch-list (before approving rollout)

- Any place parsing CAR by fixed regex (`PSC-YYYY-SEQ`) will break.
- Long/unknown vessel codes can cause format breakage if `car_number` width is insufficient.
- If a vessel code cannot be resolved, the code falls back to a deterministic short vessel token so CAR creation can continue within the existing column length.
- Legacy CAR references in historic emails/PDFs are external artifacts; changing old rows would destroy traceability.

## Deployment stance

- Default: **apply vessel-aware numbering only for new CARs**.
- Optional separate follow-up: if explicit business approval is given later, plan a second change to migrate old CAR history and generated files.
