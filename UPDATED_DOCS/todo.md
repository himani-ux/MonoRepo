# TODO.MD — Active Session Tasks
## Inspection Module — PSC/RS/Audit Close-out System

---

## Session: 2026-02-10 (Session 76)
**Phase:** Post-implementation — Unified CAR Workflow Overhaul
**Goal:** Replace dual-status system with unified CAR.status workflow (9 statuses, 12 transitions)

---

## Tasks — ALL COMPLETE

### Step 1: Backend — Update CARStatus enum + CAR model fields
- [x] Replace CARStatus choices (5 old → 9 new)
- [x] Change CAR.status default from DRAFT to ALLOTTED
- [x] Add verification_pending, last_action* fields
- [x] Mark DefStatus as deprecated

### Step 2: Backend — Migration with data mapping
- [x] Create 0005_workflow_overhaul.py
- [x] Data migration: DRAFT→ALLOTTED, SUBMITTED→SUBMITTED_TO_PIC, etc.
- [x] Reversible migration

### Step 3: Backend — Rewrite workflow.py (state machine)
- [x] WorkflowAction class (12 named actions)
- [x] TRANSITIONS dict with role/comment rules
- [x] validate_workflow_transition(), get_available_actions(), auto_start_if_allotted()
- [x] Preserve legacy DEF workflow for backward compat

### Step 4: Backend — New views + URLs
- [x] CARWorkflowView (POST /cars/{id}/workflow/)
- [x] CARAvailableActionsView (GET /cars/{id}/available-actions/)
- [x] Update existing views with new status values
- [x] 2 new URL patterns

### Step 5: Backend — Serializer updates
- [x] CARWorkflowTransitionSerializer
- [x] CARDetailSerializer: new fields + available_actions
- [x] CARListSerializer: overdue check updated

### Step 6: Backend — Update deficiency views
- [x] car_status filter in DeficiencyListFilteredView
- [x] BulkDeficiencySubmitView: APPROVED → PENDING_MASTER_REVIEW

### Step 7: Backend — Update permissions, dashboard, signals
- [x] CanEditCAR: 5 vessel-editable statuses
- [x] Dashboard: all status refs updated
- [x] Signals: ALLOTTED default

### Step 8: Frontend — Update types + constants
- [x] CAR_STATUS (9 values) + WORKFLOW_ACTIONS (12 actions)
- [x] CARDetail type + AvailableAction interface

### Step 9: Frontend — Update format-status.ts
- [x] Variant + label mappings for 9 statuses

### Step 10: Frontend — API + hooks
- [x] transitionCAR(), getCARAvailableActions()
- [x] useTransitionCAR(), useCARAvailableActions()
- [x] DeficiencyFilters: car_status

### Step 11: Frontend — Rewrite deficiency-workflow-actions.tsx
- [x] Switch on car.status (not def_status)
- [x] Role-based buttons + comment dialog

### Step 12: Frontend — Update cards/lists/filters/pages
- [x] deficiency-card.tsx: car.status primary badge
- [x] deficiency-detail-dialog.tsx: car.status display
- [x] deficiency-list.tsx: bulk submit via PENDING_MASTER_REVIEW
- [x] routes/deficiencies/index.tsx: car_status filters
- [x] car-filters.tsx: 9 new statuses
- [x] routes/cars/[id].tsx: CARWorkflowActions replaces legacy modals
- [x] NEW: car-workflow-actions.tsx

---

## Verification

| Check | Result |
|-------|--------|
| `npx tsc --noEmit` | PASS (0 errors) |
| `npx vite build` | PASS (9.91s) |
| Migration pending | `python manage.py migrate` on live DB |

---

## Next Session TODO

- [ ] Run `python manage.py migrate` to apply 0005_workflow_overhaul
- [ ] E2E test: Login as master001, verify new status filters + workflow actions on deficiencies page
- [ ] E2E test: Login as pic001, verify Start Review + Submit to DPA on CAR detail
- [ ] E2E test: Login as dpa001, verify Close CAR + Reopen actions
- [ ] Verify auto-start: editing a CAR in ALLOTTED status transitions to IN_PROGRESS
- [ ] Verify comment dialog for mandatory-comment actions (RETURN_FOR_REWORK, CLOSE_CAR, REOPEN_CAR, REQUEST_REWORK)

---

## Session Status: COMPLETE
