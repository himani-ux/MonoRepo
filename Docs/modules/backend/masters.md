# Masters Module

## Path

- `psc-backend/apps/masters/`

## Purpose

This is the read-only reference data module. It exposes lookup APIs needed by inspection creation, deficiency coding, CAR root-cause mapping, and reviewer selection.

## Owns

- MOU master list
- PSC action codes
- PIC master list
- PSC deficiency categories and codes
- CLC categories, flat lists, and hierarchy payloads

## Main Files

- `models.py`: unmanaged mappings to master data tables
- `serializers.py`: lean serializers for code tables and CLC hierarchy
- `views.py`: list endpoints and hierarchy assembly
- `urls.py`: `/api/psc/masters/*`

## Workflow

1. Frontend forms call master-data hooks on demand.
2. The module returns filtered lists or hierarchy payloads without mutation.
3. Inspection and CAR modules store code IDs plus denormalized display codes so business records remain readable even if labels change later.

## Dependencies

- Shared SQL Server master tables
- Frontend consumers in `use-masters.ts`, inspection forms, deficiency dialogs, and CAR forms

## Notes

- This module is intentionally thin. If business logic starts appearing here, it is usually a sign that the logic belongs in inspection or CAR workflows instead.
