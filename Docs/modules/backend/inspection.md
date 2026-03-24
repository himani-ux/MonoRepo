# Inspection Module

## Path

- `psc-backend/apps/inspection/`

## Purpose

This is the core PSC workflow module. It owns inspection lifecycle, deficiency registration, dashboard aggregates, PSC follow-up handling, Excel export, and the DefIntel reporting endpoints.

## Owns

- Inspection records and report uploads
- Inspection workflow: `DRAFT -> SUBMITTED -> PIC_REVIEWED -> DPA_CLOSED`
- Deficiency records linked to inspections
- Deficiency allocation and workflow transitions
- Bulk deficiency submit for vessel master
- Follow-up registration against PSC inspections
- Dashboard KPI endpoint
- DefIntel OpenSource import, checklist preview/export, prediction

## Main Files

- `models.py`: inspection header and uploaded report records
- `deficiency_models.py`: deficiency and auto-created CAR linkage
- `views.py`: inspection CRUD and status transitions
- `deficiency_views.py`: deficiency create/list/allocate/workflow APIs
- `followup_views.py`: follow-up registration
- `dashboard_views.py`: aggregated dashboard response
- `signals.py`: auto-create CAR and auto-clear deficiency hooks
- `workflow.py`: unified CAR/deficiency role routing helpers
- `defintel_*`: reporting/import/prediction support

## Workflow

1. A vessel master creates an inspection draft and uploads the report.
2. Deficiencies are added under the inspection.
3. Each new deficiency triggers `auto_create_car`, creating a 1:1 CAR placeholder.
4. The inspection is submitted for office review.
5. PIC review and DPA close complete the inspection lifecycle.
6. If the inspection is PSC, vessel master can register follow-up updates that adjust deficiency action codes and optionally attach a follow-up report.

## Dependencies

- `apps/accounts` for role and vessel access checks
- `apps/car` activity history and downstream CAR handling
- `apps.notifications` for inspection close and follow-up alerts
- `apps.masters` for coding and hierarchy data

## Notes

- This module is the center of the modern PSC backend.
- Although `workflow.py` contains CAR transition logic, the execution endpoints live in `apps/car`; the inspection module mainly owns reviewer routing helpers and legacy deficiency workflow compatibility.
