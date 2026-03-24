# CAR Module

## Path

- `psc-backend/apps/car/`

## Purpose

This module owns the corrective action lifecycle after a CAR already exists. The CAR record itself is defined in `apps/inspection/deficiency_models.py`, but this module controls editing, workflow transitions, corrective actions, evidence, physical verification, PDF export, activity history, and audit logging.

## Owns

- CAR list and detail APIs
- Unified CAR workflow transitions
- Root cause and CLC mapping updates
- Corrective actions create/update/complete/delete
- Evidence upload, retrieval, and delete
- Physical verification create/close
- CAR PDF export
- Activity history and audit trail

## Main Files

- `models.py`: CLC mapping, corrective actions, evidence, PV, activity history, audit log
- `views.py`: CAR endpoints plus nested action/evidence/PV APIs
- `serializers.py`: validation and detail/list response shapes
- `permissions.py`: status + role aware guards
- `report_views.py` and `reports.py`: PDF export logic
- `urls*.py`: route split by CAR, evidence, action, and PV resources

## Workflow

1. Inspection signals create a CAR in `ALLOTTED`.
2. Vessel owner or master starts work, adds root cause, links CLC, and creates corrective actions.
3. Evidence and action completion move the CAR through vessel-side review.
4. Master submits to PIC, PIC reviews, and then submits to DPA.
5. DPA closes the CAR. Closing can trigger physical verification tracking.
6. Office users can export internal or external CAR PDFs at any time.

## Dependencies

- `apps.inspection` for the underlying CAR and deficiency link
- `apps.notifications` for workflow notifications
- `apps.accounts` for role constants and user lookups

## Notes

- The real state machine is defined by `CAR.status`; legacy `Deficiency.def_status` is kept for compatibility only.
- This module is the main place where vessel-side workflow and office-side workflow converge.
