# Frontend Inspection Workflow

## Path

- `psc-frontend/src/routes/inspections/`
- `psc-frontend/src/routes/deficiencies/`
- `psc-frontend/src/components/inspection/`
- `psc-frontend/src/hooks/use-inspections.ts`
- `psc-frontend/src/hooks/use-deficiencies.ts`
- `psc-frontend/src/lib/api/inspections.ts`
- `psc-frontend/src/lib/api/deficiencies.ts`

## Purpose

This module renders the end-to-end inspection workflow in the modern frontend: list, create, detail, edit, deficiency entry, deficiency review dashboard, and PSC follow-up wizard.

## Owns

- Inspection list filters and Excel export trigger
- New inspection draft form and initial report upload
- Inspection detail view with deficiency modal
- Edit inspection and office-assist edit flow
- Follow-up registration wizard
- Deficiency workflow dashboard and detail dialog

## Workflow

1. `/inspections` lists inspection records with URL-backed filters and pagination.
2. `/inspections/new` creates a draft and optionally uploads the initial report.
3. `/inspections/:id` shows reports, deficiencies, and action affordances.
4. Adding a deficiency from detail triggers backend deficiency creation and automatic CAR creation.
5. `/deficiencies` surfaces vessel-side review and allocation state across deficiencies.
6. `/inspections/:id/follow-up` runs the multi-step PSC follow-up wizard, including optional upload of up to three PDF reports.

## Dependencies

- Master data hooks for MOU, PSC codes, CLC, PIC, and crew lists
- Auth/process permissions from the app shell
- CAR module, because each deficiency owns a linked CAR

## Notes

- The page layer keeps URL search params as the filter source of truth.
- The inspection detail screen is the handoff point into downstream CAR work.
