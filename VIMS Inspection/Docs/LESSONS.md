# LESSONS.md — Learning & Pattern Library
## Inspection Module — PSC/RS/Audit Close-out System
**Version:** 1.0 | **Date:** 2026-02-03

---

## Purpose

This file captures mistakes made, patterns discovered, and rules that prevent errors from recurring. Review at the start of every session.

---

## How to Use This File

**After ANY correction from the user:**
1. Document what went wrong
2. Explain why it happened
3. Write a rule that prevents it
4. Categorize appropriately

**Format:**
```
### [Category] Brief Description
**Date:** YYYY-MM-DD
**What went wrong:** Description of the error
**Why it happened:** Root cause analysis
**Rule to prevent:** Concrete rule to follow
**Related docs:** Links to relevant documentation
```

---

## Categories

- **DESIGN** — Visual/styling mistakes
- **COMPONENT** — Component architecture errors
- **API** — Backend/API mistakes
- **DATA** — Database/state management issues
- **VALIDATION** — Form/input validation errors
- **SYNC** — Offline/sync related issues
- **WORKFLOW** — Process/workflow mistakes
- **GENERAL** — Other lessons

---

## Lessons

### [WORKFLOW] Mandatory Post-Close Work Should Be Surfaced as Operational Queue State
**Date:** 2026-02-11
**What went wrong:** Even after PV auto-create on close, users could still miss completion because CAR list/dashboard did not expose a first-class "due now" operational view.
**Why it happened:** Verification state existed in detail context, but there was no list-level computed signal to drive queue-based behavior.
**Rule to prevent:** For any mandatory follow-up task, expose a list-level computed due field (`*_due`) and a dedicated filter so operations can run from queue view, not only detail pages.
**Related docs:** apps/car/serializers.py `CARListSerializer`, apps/car/views.py `CARListView` filter/annotation, Docs/PRD.md FEAT-PV-001/002

---

### [API] Prefer Reusing Existing List Metadata for Dashboard Counts
**Date:** 2026-02-11
**What went wrong:** The first instinct for dashboard tiles is to add a new count endpoint, which increases API surface and maintenance burden.
**Why it happened:** Count metrics were treated as a separate feature instead of a filtered-list projection.
**Rule to prevent:** If paginated list responses already return `total_count`, derive dashboard counts by querying the list with a narrow filter (for example `pv_due=true`) before adding a new endpoint.
**Related docs:** apps/car/views.py list pagination contract, psc-frontend/src/routes/dashboard/index.tsx

---

### [WORKFLOW] Close Transition Side Effects Must Create PV Idempotently and Reuse Existing Notification Path
**Date:** 2026-02-11
**What went wrong:** Closing a CAR could leave no PV record unless someone manually created it, making post-close verification effectively skippable in the data model.
**Why it happened:** CLOSE_CAR transition logic set `verification_pending` but did not enforce creation of the dependent PV entity or reuse the existing PV-created notification flow.
**Rule to prevent:** For mandatory post-transition artifacts, add side effects directly in the transition handler with an idempotency guard (`exists` check) and call the already-approved notification helper rather than creating parallel notification logic.
**Related docs:** Docs/PRD.md FEAT-PV-001/FEAT-PV-002 intent, apps/car/views.py `CARWorkflowView`, apps/notifications/signals.py `notify_physical_verification_created`

---

### [API] Report Sections Must Be Gated by Business Status, Not Record Existence
**Date:** 2026-02-11
**What went wrong:** PDF logic was keyed to whether PV data existed, which allowed OPEN (incomplete) PV context to appear in external-facing reports.
**Why it happened:** Section rendering checks were presence-based (`if pv`) instead of state-based (`if pv.status == CLOSED`).
**Rule to prevent:** For compliance-facing exports, gate optional sections on completion status and add explicit ordering tests when section placement is a requirement (for example, below DPA comments).
**Related docs:** Docs/PRD.md report/PV acceptance criteria, apps/car/reports.py `_build_physical_verification`, Docs/DESIGN_SYSTEM.md PDF section guidance

---

### [API] Inspection Create RBAC Must Enforce Role + Inspection Type Together
**Date:** 2026-02-10
**What went wrong:** Inspection create permissions allowed office roles to create all inspection types, including `PSC` and `RS`, even though those types are intended to be master-only.
**Why it happened:** RBAC checks only validated role membership and did not evaluate `inspection_type` on create requests.
**Rule to prevent:** For create endpoints with type-specific ownership rules, enforce permission on both actor role and submitted entity type in backend permission classes, then mirror restrictions in frontend type selection/submit guards.
**Related docs:** Docs/VALIDATION_RULES.md Section 2.1, Docs/BACKEND_STRUCTURE.md Section 11.1, Docs/DEBUG_AGENT.md Step 4

---

### [API] Report Feature Closure Must Validate Rendered Acceptance Criteria, Not Only Endpoint Contracts
**Date:** 2026-02-08
**What went wrong:** FEAT-RPT-001 was marked complete while the PDF header still showed `"[Company Logo]"`, and tests focused on payload/RBAC/format checks without explicit section-completeness assertions.
**Why it happened:** Verification emphasized API behavior and binary/PDF signature checks, but did not include acceptance-criteria-level rendering checks for report content/sections.
**Rule to prevent:** For report/export features, add explicit criterion tests before marking complete: (1) required visual/header element is rendered (no placeholders), (2) all required sections are built/asserted, and (3) traceability includes a linked feature report file in `test_progress.txt`.
**Related docs:** Docs/PRD.md FEAT-RPT-001, Docs/DESIGN_SYSTEM.md Section 12 (PDF Report Styling), Docs/test_progress.txt

---

### [API] Inspection Status Transitions Must Always Emit Required Activity + Notification Side Effects
**Date:** 2026-02-08
**What went wrong:** `InspectionPICReviewView` and `InspectionDPACloseView` changed inspection status but did not create required `ActivityHistory` events; DPA close also did not create the required vessel-facing notification.
**Why it happened:** Transition handlers implemented state mutation but skipped FEAT-INS-005/006 side-effect requirements (audit timeline + notification trigger), so workflow completion was not traceable in activity/notification tables.
**Rule to prevent:** For every status transition endpoint, implement a parity checklist before merge: (1) status mutation, (2) sync_version increment, (3) required activity event, and (4) required notification pipeline trigger per PRD/BACKEND contracts.
**Related docs:** Docs/PRD.md FEAT-INS-005 and FEAT-INS-006, Docs/BACKEND_STRUCTURE.md activity history + notification sections, Docs/VALIDATION_RULES.md Sections 2.3 and 2.4

---

### [VALIDATION] Physical Verification Must Enforce OPEN Uniqueness and Non-Future Close Dates
**Date:** 2026-02-07
**What went wrong:** Physical verification creation allowed multiple `OPEN` records for the same CAR, and close accepted a `visit_date` in the future.
**Why it happened:** PV create view only checked CAR status precondition and skipped the "existing OPEN PV" precondition; close serializer required `visit_date` but did not validate date range against today.
**Rule to prevent:** For stateful child records, enforce documented preconditions explicitly in the write endpoint (or DB constraint) and validate both requiredness and temporal bounds for date fields.
**Related docs:** Docs/VALIDATION_RULES.md Section 7.1 and 7.2, Docs/PRD.md FEAT-PV-001 and FEAT-PV-002, Docs/BACKEND_STRUCTURE.md Section 10.8

---

### [API] CAR Detail Timeline Must Aggregate Related Activity Entity Types
**Date:** 2026-02-07
**What went wrong:** CAR detail activity history only queried `ActivityHistory` rows where `entity_type='CAR'` and `entity_id=<car_id>`. This excluded FEAT-HIST-001 timeline events written as `entity_type='EVIDENCE'` (`EVIDENCE_UPLOADED`) and `entity_type='ACTION'` (`ACTION_COMPLETED`).
**Why it happened:** Read-path logic assumed all CAR timeline entries are stored under CAR entity keys, but the activity schema is polymorphic and stores child-entity events under their own entity IDs.
**Rule to prevent:** For parent detail timelines, always aggregate activity rows across all documented related entity types (parent + child entities) using related IDs; do not hard-filter to only the parent entity type.
**Related docs:** Docs/PRD.md FEAT-HIST-001, Docs/BACKEND_STRUCTURE.md Sections 5.1 and 10.5

---

### [GENERAL] Cross-Reference Audit Is Mandatory Before Declaring Docs Complete
**Date:** 2026-02-05
**What went wrong:** Session 2 claimed "Updated all cross-references between documents" in progress.txt, but 5 categories of contradiction survived: CLAUDE.md tech stack versions disagreed with TECH_STACK.md; IMPLEMENTATION_PLAN.md used namespaced API paths while BACKEND_STRUCTURE.md and APP_FLOW.md used flat paths; master data endpoint names differed across 3 docs; inspection report file format rules conflicted across PRD.md, VALIDATION_RULES.md, and APP_FLOW.md; progress.txt listed EXISTING_SCHEMA.md as completed but the file didn't exist.
**Why it happened:** No systematic cross-reference verification was performed. Each doc was reviewed in isolation. "Cross-references updated" was written optimistically without proof.
**Rule to prevent:**
- After any documentation session, run an explicit cross-reference audit:
  1. Grep all `/api/psc/` endpoint paths across BACKEND_STRUCTURE, IMPLEMENTATION_PLAN, and APP_FLOW — they must match exactly
  2. Compare version numbers in CLAUDE.md tech stack summary against TECH_STACK.md — they must match exactly
  3. Compare validation rules across PRD.md acceptance criteria, VALIDATION_RULES.md rules, and APP_FLOW.md screen specs — they must match exactly
  4. Verify every file listed in CLAUDE.md canonical docs table actually exists
  5. Verify every file listed in progress.txt completed section actually exists
- Never write "cross-references updated" in progress.txt without running this audit and documenting results
- progress.txt claims must be verifiable. If you can't prove it, don't write it.
**Related docs:** All canonical docs, progress.txt

---

### [GENERAL] Documentation-First Approach Works
**Date:** 2026-02-03
**What went wrong:** N/A (Proactive lesson)
**Why it happened:** Industry best practice
**Rule to prevent:** Always read canonical docs before implementing. Never start coding without checking PRD.md, APP_FLOW.md, and relevant specs.
**Related docs:** CLAUDE.md Session Startup Sequence

---

### [DESIGN] DefCode Must Always Be Visible
**Date:** 2026-02-03
**What went wrong:** N/A (Critical business requirement documented proactively)
**Why it happened:** Regulatory/operational requirement for maritime inspections
**Rule to prevent:** On ANY screen showing deficiencies, the DefCode MUST be prominently displayed. Check every deficiency-related component for DefCode visibility.
**Related docs:** PRD.md FEAT-INS-003, CLAUDE.md Business Rules

---

### [DATA] 1:1 Deficiency-to-CAR Relationship
**Date:** 2026-02-03
**What went wrong:** N/A (Critical business rule documented proactively)
**Why it happened:** Business requirement — every deficiency must have a tracking mechanism
**Rule to prevent:** 
- CAR creation is AUTOMATIC via database trigger when deficiency is created
- Never implement manual CAR creation
- Never allow deficiency without CAR
**Related docs:** BACKEND_STRUCTURE.md auto-CAR trigger, PRD.md FEAT-CAR-001

---

### [VALIDATION] Evidence Requirements Are Strict
**Date:** 2026-02-03
**What went wrong:** N/A (Critical validation rule documented proactively)
**Why it happened:** Regulatory compliance requires photographic evidence
**Rule to prevent:**
- CAR submission requires ≥1 BEFORE evidence AND ≥1 AFTER evidence
- Both frontend and backend must validate
- File limits: 3MB max, PDF/JPG/JPEG only
**Related docs:** PRD.md FEAT-CAR-003, FEAT-CAR-004

---

### [WORKFLOW] State Machines Are Enforced
**Date:** 2026-02-03
**What went wrong:** N/A (Architecture decision documented proactively)
**Why it happened:** Business process requires specific approval workflow
**Rule to prevent:**
- Inspection: DRAFT → SUBMITTED → PIC_REVIEWED → DPA_CLOSED
- CAR: DRAFT → SUBMITTED → PIC_ACCEPTED → DPA_CLOSED (with REWORK branch)
- Never allow invalid transitions
- Validate on both frontend (disable invalid actions) and backend (reject invalid requests)
**Related docs:** BACKEND_STRUCTURE.md Part 11 State Machines

---

### [COMPONENT] Always Implement All Three States
**Date:** 2026-02-03
**What went wrong:** N/A (Pattern documented proactively)
**Why it happened:** Best practice for robust UX
**Rule to prevent:**
- Every data-fetching component needs: Loading, Empty, Error states
- Use LoadingSkeleton, EmptyState, ErrorState from shared components
- Never show blank screens
**Related docs:** FRONTEND_GUIDELINES.md Section 3.3, APP_FLOW.md Empty States

---

### [DESIGN] Mobile-First Is Mandatory
**Date:** 2026-02-03
**What went wrong:** N/A (Architecture decision)
**Why it happened:** >50% of users are on vessels with mobile devices
**Rule to prevent:**
- Start every component with mobile layout
- Use Tailwind responsive prefixes (md:, lg:) for desktop enhancements
- Test at 375px width first
**Related docs:** DESIGN_SYSTEM.md Section 7 Breakpoints, FRONTEND_GUIDELINES.md Section 8

---

### [API] Match Contracts Exactly
**Date:** 2026-02-03
**What went wrong:** N/A (Rule documented proactively)
**Why it happened:** API contracts are pre-defined and documented
**Rule to prevent:**
- Every endpoint must match BACKEND_STRUCTURE.md request/response shapes
- Use exact field names (snake_case for backend)
- Include all required fields
- Return correct HTTP status codes
**Related docs:** BACKEND_STRUCTURE.md Part 3 API Contracts

---

### [SYNC] Offline Requires Careful Planning
**Date:** 2026-02-03
**What went wrong:** N/A (Architecture note)
**Why it happened:** Vessels often have no internet connectivity
**Rule to prevent:**
- Every mutation must work offline (queue in IndexedDB)
- Implement retry logic: 3 attempts, exponential backoff (1s, 2s, 4s)
- Storage limit: 150MB, warn at <10MB
- Conflicts resolved by Office only
**Related docs:** PRD.md FEAT-SYNC-*, BACKEND_STRUCTURE.md Part 9

---

### [DATA] Never Use user.crew_id for UUID Matching — Always Use user.id
**Date:** 2026-02-10
**What went wrong:** Crew members were never recognized as 'owner' or 'reviewer' in the CAR workflow. `_get_user_workflow_roles()` used `user.crew_id` (CRW string like 'CRW0002') for UUID matching against `assigned_crew_id`/`reviewer_crew_id` (HRM501 UUIDs). Same bug in `validate_transition()` and `deficiency-workflow-actions.tsx`.
**Why it happened:** `AuthenticatedUser.crew_id` is the human-readable CrewID code (e.g., 'CRW0002'), NOT the HRM501 UUID. The code used `getattr(user, 'crew_id', None) or getattr(user, 'id', None)` which always resolved to the CRW string since it's truthy.
**Rule to prevent:**
- `user.crew_id` = CrewID string code (CRW0002) — for display only
- `user.id` = HRM501 UUID — for ALL permission/matching comparisons
- NEVER use `user.crew_id or user.id` pattern — always use `user.id` directly
- Always use `_uuid_match()` for UUID comparisons (handles char(32) vs hyphenated format)
**Related docs:** BACKEND_STRUCTURE.md accounts section, apps/accounts/backends.py AuthenticatedUser

---

### [DATA] Raw str() UUID Comparison Fails on mssql-django Managed Tables
**Date:** 2026-02-10
**What went wrong:** `CARDetailView` VESSEL_CREW access check used `str(deficiency.assigned_crew_id) != str(request.user.id)` — raw string comparison. mssql-django stores UUIDs as char(32) without hyphens in managed tables, while JWT-reconstructed `user.id` has hyphens. Comparison always failed → 403 for crew.
**Why it happened:** The char(32) vs uniqueidentifier format difference was known for ORM lookups but not consistently applied to in-Python comparisons.
**Rule to prevent:**
- NEVER use `str(uuid_a) == str(uuid_b)` for UUID comparisons
- ALWAYS use `_uuid_match()` from `apps/inspection/workflow.py` which normalizes both values
- Grep for `str(.*_id)` patterns in permission checks after adding any UUID comparison
**Related docs:** MEMORY.md SQL Server + mssql-django UUID Gotchas

---

### [WORKFLOW] Edit Page Submit Must Use Unified Workflow API, Not Legacy Endpoints
**Date:** 2026-02-10
**What went wrong:** CAR edit page's "Submit" button called the old `POST /cars/{id}/submit/` endpoint (CARSubmitView with CanSubmitCAR = VESSEL_MASTER only). Crew members got 403 because this endpoint is for "Submit to PIC" (a Master-only action). The correct action for crew is "Mark Completed" via `POST /cars/{id}/workflow/`.
**Why it happened:** The edit page was built before the unified workflow system. It hardcoded the old submit endpoint instead of using the available-actions API to determine the correct action.
**Rule to prevent:**
- All workflow transitions MUST go through the unified `/workflow/` endpoint with named actions
- Use `useCARAvailableActions()` to determine what the current user can do
- Never hardcode a specific workflow endpoint — the available-actions API is the source of truth
- Edit pages should dynamically show/hide the submit button based on available actions
**Related docs:** Docs/BACKEND_STRUCTURE.md workflow section, apps/inspection/workflow.py

---

### [WORKFLOW] determine_reviewer Must Handle All Rank Categories
**Date:** 2026-02-10
**What went wrong:** `determine_reviewer()` only routed 2E→CE and CE/CO→Master. "Other" ranks (Able Seaman, Bosun, etc.) returned (None, None), leaving `reviewer_crew_id=None`. This meant after MARK_COMPLETED, the CAR went to PENDING_CE_REVIEW with no reviewer assigned.
**Why it happened:** The routing table only covered officer ranks explicitly. Non-officer crew members were not considered.
**Rule to prevent:**
- `determine_reviewer()` must have explicit routing for ALL rank categories including RANK_OTHER
- When adding new rank classifications, verify the reviewer chain is complete
- Test with non-officer rank crew members (Able Seaman, Bosun, etc.)
**Related docs:** apps/inspection/workflow.py determine_reviewer

---

## Patterns to Reuse

### Pattern: Form with Validation
```typescript
// Use react-hook-form + zod for all forms
const form = useForm<FormData>({
  resolver: zodResolver(schema),
  defaultValues: { ... }
});
```
**When to use:** Every form in the application
**Reference:** FRONTEND_GUIDELINES.md Section 3.2

### Pattern: Data Fetching with TanStack Query
```typescript
// Use query keys consistently
export const resourceKeys = {
  all: ['resources'] as const,
  lists: () => [...resourceKeys.all, 'list'] as const,
  list: (filters: Filters) => [...resourceKeys.lists(), filters] as const,
  details: () => [...resourceKeys.all, 'detail'] as const,
  detail: (id: number) => [...resourceKeys.details(), id] as const,
};
```
**When to use:** All server state management
**Reference:** FRONTEND_GUIDELINES.md Section 4.1

### Pattern: API Error Handling
```typescript
// Centralized error handling
if (error instanceof AxiosError) {
  const apiError = error.response?.data;
  if (apiError?.details) {
    // Field-level errors
  } else if (apiError?.message) {
    toast.error(apiError.message);
  }
}
```
**When to use:** Every API call
**Reference:** FRONTEND_GUIDELINES.md Section 9.2

---

## Anti-Patterns to Avoid

### Anti-Pattern: Hardcoded Colors
❌ `className="bg-blue-500"` (unless matches DESIGN_SYSTEM.md)
✅ `className="bg-primary-500"` (maps to design token)

### Anti-Pattern: Missing Loading States
❌ Return null while loading
✅ Return <LoadingSkeleton /> while loading

### Anti-Pattern: Inline Styles
❌ `style={{ marginTop: 16 }}`
✅ `className="mt-4"` (uses spacing scale)

### Anti-Pattern: Assuming Online
❌ Direct API call without offline check
✅ Queue mutation if offline, sync when online

---

## Quick Reference Checklist

Before submitting any code:
- [ ] DefCode visible on deficiency screens?
- [ ] All three states (loading/empty/error) implemented?
- [ ] Mobile layout works at 375px?
- [ ] Using design tokens from DESIGN_SYSTEM.md?
- [ ] API matches BACKEND_STRUCTURE.md contract?
- [ ] Form validation matches PRD requirements?
- [ ] State transitions follow state machine?
- [ ] Offline scenario handled?

---

### [API] Django URL Namespace Requires app_name
**Date:** 2026-02-05
**What went wrong:** When adding masters app URL routes with `include('apps.masters.urls', namespace='masters')`, Django raised `ImproperlyConfigured: Specifying a namespace in include() without providing an app_name`.
**Why it happened:** Django requires the included urls.py module to define `app_name` when the parent URL configuration specifies a `namespace` parameter. This is a Django convention to ensure proper URL reversing.
**Rule to prevent:**
- When creating a new Django app with URL routes, ALWAYS include `app_name = 'appname'` at the top of urls.py
- Template:
  ```python
  from django.urls import path

  app_name = 'appname'  # Required for namespace in include()

  urlpatterns = [...]
  ```
**Related docs:** BACKEND_STRUCTURE.md, Django URL dispatcher documentation

---

### [API] Verify Dependencies Are Actually Installed
**Date:** 2026-02-05
**What went wrong:** `ModuleNotFoundError: No module named 'rest_framework_simplejwt'` when starting Django server, even though the package was listed in settings.py INSTALLED_APPS.
**Why it happened:** The package was specified in settings.py but was never actually installed in the virtual environment. The requirements.txt or pip install step was missed or incomplete.
**Rule to prevent:**
- After adding any package to INSTALLED_APPS, verify it's installed: `pip show <package-name>`
- When inheriting a codebase, run `pip list` to verify all expected packages are present
- Keep requirements.txt synchronized with INSTALLED_APPS
- If a ModuleNotFoundError occurs for a third-party package, first check if it's installed before debugging further
**Related docs:** TECH_STACK.md, psc-backend/requirements.txt

---

### [WORKFLOW] Always Get User Approval Before Implementation
**Date:** 2026-02-05
**What went wrong:** After completing the startup sequence (reading CLAUDE.md, progress.txt, IMPLEMENTATION_PLAN.md, LESSONS.md, and writing tasks/todo.md), jumped directly to implementation without presenting the plan to the user for approval.
**Why it happened:** Eagerness to start coding after understanding the task. Skipped step 6 of the startup sequence: "Verify plan with user — Before executing."
**Rule to prevent:**
- The startup sequence has 6 steps, not 5. Step 6 is MANDATORY.
- After writing tasks/todo.md, STOP and present the plan to the user.
- Wait for explicit approval ("yes", "proceed", etc.) before writing any code.
- The plan presentation should include: files to create, files to modify, and a brief description of what will be implemented.
- Never assume the user approves just because the plan seems straightforward.
**Related docs:** CLAUDE.md Session Startup Sequence

---

### [COMPONENT] Avoid Duplicate Keys When Mapping Shared Enum Values
**Date:** 2026-02-05
**What went wrong:** Created a status variant map using computed property names from both `INSPECTION_STATUS` and `CAR_STATUS` constants. TypeScript error: "An object literal cannot have multiple properties with the same name" because both enums share `DRAFT`, `SUBMITTED`, and `DPA_CLOSED` values.
**Why it happened:** Didn't consider that inspection and CAR status enums have overlapping string values. Using `[INSPECTION_STATUS.DRAFT]: 'draft'` and `[CAR_STATUS.DRAFT]: 'draft'` creates duplicate `'DRAFT'` keys.
**Rule to prevent:**
- When creating maps for status types, use string literals directly instead of computed property names from multiple enums
- Or use a single unified map with string keys: `{ DRAFT: 'draft', SUBMITTED: 'submitted', ... }`
- Before creating enum-keyed objects, check if different enums share values
**Related docs:** src/components/shared/status-badge.tsx

---

### [GENERAL] Verify Constant Names Before Using Them
**Date:** 2026-02-05
**What went wrong:** Used `FILE_LIMITS.MAX_FILE_SIZE` in file-upload.tsx, but the actual constant in constants.ts is `MAX_FILE_SIZE_BYTES` (not an object).
**Why it happened:** Assumed a constant structure without reading the actual file first. Made up a name that seemed reasonable.
**Rule to prevent:**
- Always read constants.ts (or relevant config file) before referencing constants
- Use IDE autocomplete or grep to find exact constant names
- Don't assume constant naming patterns - verify them
**Related docs:** src/lib/utils/constants.ts, src/components/shared/file-upload.tsx

---

### [API] Prefer Django Signals Over Database Triggers
**Date:** 2026-02-05
**What went wrong:** N/A (Architecture decision documented proactively)
**Why it happened:** BACKEND_STRUCTURE.md specifies database triggers for auto-CAR creation, but Django signals are more appropriate in a Django project.
**Rule to prevent:**
- Use Django signals (post_save, pre_save) instead of raw SQL triggers when possible
- Benefits of signals over DB triggers:
  - Better testability (can mock/disable in tests)
  - Django-native pattern (consistent with framework)
  - Easier debugging (Python stack traces)
  - No raw SQL execution required
  - Works with Django's ORM transaction handling
- Register signals in `apps.py` `ready()` method
- Template:
  ```python
  # apps.py
  def ready(self):
      from . import signals  # noqa: F401
  ```
**Related docs:** BACKEND_STRUCTURE.md Section 8, apps/inspection/signals.py

---

### [DATA] Use Denormalized Fields for Display Performance
**Date:** 2026-02-05
**What went wrong:** N/A (Pattern documented from BACKEND_STRUCTURE.md design)
**Why it happened:** Schema design pattern for avoiding JOINs in list views while maintaining FK integrity.
**Rule to prevent:**
- When a field is frequently displayed but referenced via FK, store both:
  - `{field}_id` - The actual FK/reference for integrity
  - `{field}` - Denormalized string value for display
- Example from Deficiency model:
  ```python
  def_code_id = models.CharField(max_length=5)  # FK to PSC_Def_Code
  def_code = models.CharField(max_length=10)     # Denormalized for display
  ```
- Populate denormalized field in serializer's `create()` method
- This pattern is explicitly defined in BACKEND_STRUCTURE.md schema
- Trade-off: Slight data redundancy for significant query performance gain in list views
**Related docs:** BACKEND_STRUCTURE.md Part 4.3, apps/inspection/deficiency_models.py

---

### [API] Separate URL Files for Different Resource Paths
**Date:** 2026-02-05
**What went wrong:** N/A (Pattern documented proactively)
**Why it happened:** Some resources have endpoints at multiple URL paths (e.g., deficiencies are created under inspections but updated at their own path).
**Rule to prevent:**
- When a resource has endpoints at different URL prefixes, create separate URL files:
  - `urls.py` - Main app URLs (e.g., `/api/psc/inspections/...`)
  - `urls_{resource}.py` - Separate resource URLs (e.g., `/api/psc/deficiencies/...`)
- Each URL file needs its own `app_name` for namespacing
- Include both in `core/urls.py`:
  ```python
  path('api/psc/inspections/', include('apps.inspection.urls', namespace='inspection')),
  path('api/psc/deficiencies/', include('apps.inspection.urls_deficiency', namespace='deficiency')),
  ```
- This keeps URL organization clean and follows REST conventions where resources can be accessed via multiple paths
**Related docs:** apps/inspection/urls.py, apps/inspection/urls_deficiency.py, core/urls.py

---

### [API] Verify Permission Classes Exist Before Importing
**Date:** 2026-02-05
**What went wrong:** In `followup_views.py`, imported `IsVesselMaster` from `permissions.py` without first checking if it existed. Got `ImportError: cannot import name 'IsVesselMaster'`.
**Why it happened:** Assumed a permission class with a logical name would exist based on other permission classes in the file. Didn't read permissions.py first to verify available classes.
**Rule to prevent:**
- Before importing any permission class, grep or read the permissions file to confirm it exists
- If a needed permission class doesn't exist, create it in the permissions file first
- Pattern for checking: `grep "class IsVesselMaster" apps/inspection/permissions.py`
- Common mistake: assuming symmetric names (e.g., if `IsOfficeUser` exists, `IsVesselMaster` must too)
- When creating new views, check what permission classes are available and reuse or extend them
**Related docs:** apps/inspection/permissions.py, apps/inspection/followup_views.py

---

### [COMPONENT] Read Component Props Before Using Them
**Date:** 2026-02-05
**What went wrong:** Used `onBack` prop on PageHeader component, but PageHeader only has `showBack` and `backTo` props - no `onBack` handler.
**Why it happened:** Assumed a common pattern (onBack callback) without reading the actual component implementation first.
**Rule to prevent:**
- Before using any component prop, read the component's interface/props type
- Don't assume props exist based on common patterns - verify them
- For custom back behavior (e.g., confirmation dialog), either:
  1. Use `backTo` with a route that handles the state
  2. Add an `onBack` prop to PageHeader if needed across multiple pages
  3. Handle navigation differently (don't rely on header back button)
**Related docs:** src/components/layout/page-header.tsx

---

### [GENERAL] Imports Go at the Top of the File
**Date:** 2026-02-05
**What went wrong:** Added `import { useState } from 'react';` at the bottom of inspection-form.tsx instead of with other imports at the top.
**Why it happened:** Initially forgot to import useState, then added it at the end of the file as an afterthought instead of properly placing it with other imports.
**Rule to prevent:**
- All imports must be at the top of the file, before any other code
- When adding a missing import, scroll to the top and add it with related imports
- Group imports: React first, then third-party, then local (already a standard pattern)
- If you realize you need an import while writing code, immediately add it at the top - don't defer
**Related docs:** ESLint import rules, TypeScript conventions

---

### [COMPONENT] Verify Barrel Exports Before Using Components
**Date:** 2026-02-05
**What went wrong:** Used DropdownMenu components in inspection detail page, but they weren't exported from `@/components/ui` barrel file, causing build error: `Module '"@/components/ui"' has no exported member 'DropdownMenu'`.
**Why it happened:** Assumed that all UI components in the `ui/` folder were automatically exported from the barrel file. The dropdown-menu.tsx existed but wasn't added to index.ts.
**Rule to prevent:**
- Before importing from a barrel file (@/components/ui, @/components/shared), verify the export exists
- When adding a new component file to a folder with a barrel export, immediately add the export to index.ts
- If a component exists but isn't exported, add it to the barrel file before using it
- Pattern: `grep "DropdownMenu" src/components/ui/index.ts` to verify export exists
**Related docs:** src/components/ui/index.ts, FRONTEND_GUIDELINES.md

---

### [COMPONENT] Use Full Import Paths for Layout Components
**Date:** 2026-02-05
**What went wrong:** Used `import { PageHeader } from '@/components/layout'` but no barrel file exists at that path, causing error: `Cannot find module '@/components/layout'`.
**Why it happened:** Assumed a barrel file existed for layout components like it does for UI components. Layout components require full path imports.
**Rule to prevent:**
- Layout components use full paths: `@/components/layout/page-header`
- UI components use barrel: `@/components/ui`
- Shared components use barrel: `@/components/shared`
- Check if a folder has an index.ts before using short imports
- When uncertain, use the full path - it always works
**Related docs:** src/components/layout/, FRONTEND_GUIDELINES.md

---

### [GENERAL] Remove Unused Destructured Variables
**Date:** 2026-02-05
**What went wrong:** Destructured `action_code_description` from deficiency object but never used it, causing TypeScript error during build: `'action_code_description' is declared but its value is never read`.
**Why it happened:** Destructured all fields from the type definition without considering which were actually needed in the component.
**Rule to prevent:**
- Only destructure variables you actually use
- If planning ahead for a variable, add a comment: `// TODO: will use for tooltip`
- Run `npm run type-check` after creating components to catch unused variables early
- TypeScript strict mode catches these - don't ignore the warnings
**Related docs:** tsconfig.json (noUnusedLocals), ESLint rules

---

### [COMPONENT] Verify Hook Import Paths Before Using
**Date:** 2026-02-06
**What went wrong:** Used `import { useToast } from '@/components/ui/use-toast'` but the actual path is `@/hooks/use-toast`. Build failed with "Cannot find module" error.
**Why it happened:** Assumed the toast hook would be in the UI components folder since toaster.tsx is there. Didn't check where existing files import it from.
**Rule to prevent:**
- Before importing any hook, grep the codebase to see how other files import it
- Pattern: `grep "useToast" src/routes --include="*.tsx"` to find existing usage
- UI components (`@/components/ui`) are for React components, not hooks
- Hooks live in `@/hooks/` directory
**Related docs:** FRONTEND_GUIDELINES.md, src/hooks/

---

### [COMPONENT] Check Interface Properties Before Using Them
**Date:** 2026-02-06
**What went wrong:** Used `inspection.reports[0].file_url` but InspectionReport interface has `file_path`, not `file_url`. Used `ErrorState` with `action` prop but the interface has `onRetry` and `retryLabel` instead.
**Why it happened:** Assumed property names without reading the actual interface definitions. Made educated guesses that were wrong.
**Rule to prevent:**
- Before accessing any property, use Serena's `find_symbol` to check the interface definition
- Common mistakes: `file_url` vs `file_path`, `action` vs `onRetry`, `onClick` vs `onPress`
- Read the component's props interface before using any prop
- Pattern: `mcp__serena__find_symbol` with `include_body=true` for the type/interface
**Related docs:** src/types/index.ts, src/components/shared/error-state.tsx

---

### [API] Verify Type Definitions Before Passing Data to Mutations
**Date:** 2026-02-06
**What went wrong:** Tried to pass `authority` and `report_reference` to `useUpdateInspection` mutation, but `UpdateInspectionInput` (which extends `Partial<CreateInspectionInput>`) doesn't include these fields. TypeScript error: "property does not exist in type".
**Why it happened:** The form collected more fields than the API type supports. Assumed the type would match the form data.
**Rule to prevent:**
- Before calling a mutation, check what fields the input type actually supports
- Use Serena's `find_symbol` to read the exact type definition
- Form data types and API input types may differ - map only supported fields
- If the backend accepts fields not in the type, update the type definition first
**Related docs:** src/types/index.ts (CreateInspectionInput, UpdateInspectionInput)

---

### [WORKFLOW] Always Update progress.txt at End of Session
**Date:** 2026-02-06
**What went wrong:** Steps 4.7 and 4.8 were fully implemented in Session 8, but progress.txt was never updated. It still said "CURRENT STEP: 4.7" and "Next action: Begin Step 4.7". Session 9 had to spend time verifying the true state by reading all source files and running builds before it could determine that Phase 4 was actually complete.
**Why it happened:** The previous session completed the work but ended without updating progress.txt. The "COMPLETED THIS SESSION" section still showed Step 4.6 items from the session before that.
**Rule to prevent:**
- At the END of every session (before signing off), update progress.txt with:
  1. Move completed steps from "IN PROGRESS" / "NEXT UP" to "COMPLETED" section
  2. Update "CURRENT STEP" to the actual next step
  3. Update "COMPLETED THIS SESSION" with what was done
  4. Update "SESSION HISTORY" with a session entry
  5. Update "Overall Progress" percentage
- Never end a session with stale progress.txt — it wastes the next session's time on state verification
- If you completed work, progress.txt MUST reflect it before the session ends
**Related docs:** Docs/progress.txt, CLAUDE.md Session Startup Sequence

---

### [API] Use Standard Imports in URL Files — Never Use __import__
**Date:** 2026-02-06
**What went wrong:** First version of `apps/car/urls.py` used `__import__('apps.car.views', fromlist=['CARListView'])` pattern instead of standard `from .views import CARListView`. This is ugly, non-standard, and harder to maintain.
**Why it happened:** Tried to get clever with dynamic imports instead of following the established pattern from `apps/inspection/urls.py`.
**Rule to prevent:**
- Always use standard relative imports in Django URL files: `from .views import ViewClass1, ViewClass2`
- Before writing any new URL file, read an existing one in the project to follow the same pattern
- Pattern:
  ```python
  from django.urls import path
  from .views import View1, View2

  app_name = 'appname'
  urlpatterns = [...]
  ```
- Never use `__import__()`, `importlib`, or any dynamic import mechanism in URL configuration
**Related docs:** apps/inspection/urls.py, apps/car/urls.py, Django URL dispatcher documentation

---

### [API] CAR Model Cross-App FK Pattern
**Date:** 2026-02-06
**What went wrong:** N/A (Pattern documented proactively from architectural decision)
**Why it happened:** CAR model lives in `apps/inspection/deficiency_models.py` (FK to Deficiency, already migrated), but related models (CorrectiveAction, Evidence, etc.) live in `apps/car/models.py`.
**Rule to prevent:**
- When referencing a model from another app, use string reference: `ForeignKey('inspection.CAR', ...)`
- Or import directly: `from apps.inspection.deficiency_models import CAR`
- The `apps/car/models.py` uses direct import since both apps are always installed together
- When a model is already migrated in one app, DON'T move it — create new related models in the new app with FK references
- This avoids complex migration surgery (renaming tables, updating FKs across apps)
**Related docs:** apps/inspection/deficiency_models.py, apps/car/models.py, Docs/progress.txt (Decisions Log)

---

### [API] Backend Uses Custom Pagination Format — Not DRF Standard
**Date:** 2026-02-06
**What went wrong:** N/A (Pattern documented proactively to prevent future issues)
**Why it happened:** Both InspectionListView and CARListView return `{data: [...], pagination: {page, page_size, total_count, total_pages}}`, but the frontend `PaginatedResponse<T>` type in `types/index.ts` defines `{count, next, previous, results}` (DRF standard format). The inspection list component accesses `data.results` and `data.next` which would be undefined when connected to the actual backend.
**Rule to prevent:**
- The backend uses a **custom pagination format**: `{data, pagination}` — NOT DRF's `{count, next, previous, results}`
- When creating new API response types, match the **actual backend format**, not the `PaginatedResponse<T>` type
- The CAR API layer (`lib/api/cars.ts`) uses the correct `CARPaginatedResponse` type
- The inspection API layer still uses the mismatched `PaginatedResponse` — this needs fixing during integration testing
- Always check the backend view's `list()` method to see the actual response shape before creating frontend types
**Related docs:** psc-backend/apps/car/views.py (CARListView.list), psc-backend/apps/inspection/views.py (InspectionListView.list), psc-frontend/src/types/index.ts (PaginatedResponse)

---

### [GENERAL] Serena find_symbol Uses name_path_pattern, Not name_path
**Date:** 2026-02-06
**What went wrong:** Called `mcp__serena__find_symbol` with parameter `name_path` instead of `name_path_pattern`. All 4 parallel calls failed with a Pydantic validation error: `name_path_pattern Field required`. Wasted an entire round-trip (4 calls).
**Why it happened:** The tool's description says "name_path" everywhere when explaining the concept, but the actual parameter is `name_path_pattern`. Easy to confuse.
**Rule to prevent:**
- Serena's `find_symbol` parameter is `name_path_pattern` (NOT `name_path`)
- Serena's `find_referencing_symbols` parameter is `name_path` (different from find_symbol!)
- Serena's `replace_symbol_body` parameter is `name_path` (different from find_symbol!)
- Double-check parameter names before calling Serena tools
- If a Serena call fails with a validation error, check the parameter name first
**Related docs:** Serena MCP tool definitions

---

### [GENERAL] Always Audit Imports Before Building New Components
**Date:** 2026-02-06
**What went wrong:** Two new component files had unused imports that caused the TypeScript build to fail. `evidence-section.tsx` imported `cn` from `@/lib/utils` but never used it. `activity-history.tsx` imported `Clock` from lucide-react but never used it.
**Why it happened:** Initially planned to use those imports (cn for conditional classes, Clock for timeline icons) but ended up using different approaches. Didn't clean up before committing.
**Rule to prevent:**
- After writing a new component, scan ALL imports and verify each one is actually used in the file
- If you import something "just in case," remove it if you end up not using it
- Run `npx tsc --noEmit` after creating each batch of files, not just at the end
- Common culprits: utility imports (cn, clsx), icon imports (often import more than needed)
**Related docs:** tsconfig.json (noUnusedLocals), ESLint rules

---

### [DATA] Grep All Usages Before Renaming Type Fields
**Date:** 2026-02-06
**What went wrong:** Renamed `ActivityEvent.description` to `event_description` to match the backend `ActivityHistorySerializer`. This was correct, but `inspection-detail.tsx` was already using `event.description` — if I hadn't caught it, the build would have failed (or worse, silently shown undefined at runtime).
**Why it happened:** Changed the type definition without immediately checking all consumers of that type. The rename was necessary (backend field is `event_description`), but the ripple needed to be traced.
**Rule to prevent:**
- Before renaming ANY field on a shared type, grep the codebase for all usages: `grep "event\.description" src/ --include="*.tsx" --include="*.ts"`
- Make the field rename AND all consumer fixes in the same batch of edits
- Types that are already in use (e.g., `ActivityEvent`, `Evidence`) are more dangerous to rename than new types
- Consider: will this field rename break existing code? If yes, fix all consumers FIRST
**Related docs:** src/types/index.ts, src/components/inspection/inspection-detail.tsx

---

### [COMPONENT] DatePicker Requires Controlled Approach, Not register()
**Date:** 2026-02-06
**What went wrong:** Used `{...register('due_date')}` with DatePicker component, but DatePicker's `onChange` expects `(value: string) => void` while react-hook-form's `ChangeHandler` expects `(event: { target: any }) => void`. Type mismatch caused build failure.
**Why it happened:** Assumed DatePicker would work like native input elements that are compatible with react-hook-form's `register()`. DatePicker has a custom onChange signature.
**Rule to prevent:**
- DatePicker must use controlled approach: `value={watch('field')}` + `onChange={(val) => setValue('field', val)}`
- Never use `{...register('field')}` with DatePicker
- Custom components with non-standard onChange signatures always need controlled approach
- Before using register() on any custom component, check the component's onChange type
**Related docs:** src/components/shared/date-picker.tsx

---

### [COMPONENT] ConfirmDialog Has No loading Prop
**Date:** 2026-02-06
**What went wrong:** Passed `loading={isPending}` to ConfirmDialog but it doesn't have a `loading` prop. Build failed with type error.
**Why it happened:** Assumed a common prop name existed without checking the component interface first.
**Rule to prevent:**
- ConfirmDialog props: `open`, `onOpenChange`, `title`, `description`, `children`, `confirmLabel`, `cancelLabel`, `onConfirm`, `onCancel`, `variant`, `showIcon`, `confirmDisabled`
- To disable confirm during async operations, use `confirmDisabled={isPending}` (NOT `loading`)
- Always check ConfirmDialogProps interface before using — lesson from LESSONS.md "Check Interface Properties"
**Related docs:** src/components/shared/confirm-dialog.tsx

---

### [GENERAL] Serena replace_symbol_body Adds Extra Semicolons
**Date:** 2026-02-06
**What went wrong:** Used `mcp__serena__replace_symbol_body` to add `EVIDENCE` to the `EVIDENCE_TYPES` constant. The tool replaced the body correctly but produced `} as const;;` (double semicolon). ESLint caught it as `no-extra-semi` error.
**Why it happened:** Serena's `replace_symbol_body` appends a semicolon after the replacement body, but the existing code already had a trailing semicolon as part of the `const` declaration syntax.
**Rule to prevent:**
- After ANY `replace_symbol_body` call, always run `npm run lint` to catch extra semicolons
- If the original symbol body ends with `;`, the replacement body should NOT include the trailing `;` — or vice versa
- Better yet, use `Edit` tool for single-line changes like adding a property to an object
- Save `replace_symbol_body` for larger rewrites where the full symbol body is being replaced
**Related docs:** src/lib/utils/constants.ts

---

### [COMPONENT] PV Status Is NOT In StatusType — Use Badge Directly
**Date:** 2026-02-06
**What went wrong:** `PhysicalVerificationSection` used `<StatusBadge status={physicalVerification.status} />` but PV status values ('OPEN', 'CLOSED') are not in `StatusType` (which is `InspectionStatus | CARStatus | 'OVERDUE' | 'DETENTION'`). Build failed with `Type 'string' is not assignable to type 'StatusType'`.
**Why it happened:** Assumed all status fields in the system use the same StatusType enum. PV has its own status values that are separate from inspection/CAR statuses.
**Rule to prevent:**
- `StatusBadge` only works with `StatusType` values (InspectionStatus, CARStatus, 'OVERDUE', 'DETENTION')
- For PV status (OPEN/CLOSED), use `<Badge>` directly with appropriate variant
- Before using StatusBadge, verify the status value is a valid StatusType
- Other non-standard statuses (e.g., sync status, notification status) will also need Badge, not StatusBadge
**Related docs:** src/components/shared/status-badge.tsx, src/components/car/physical-verification-section.tsx

---

### [GENERAL] Verify Prior Session Work Before Planning New Implementation
**Date:** 2026-02-06
**What went wrong:** N/A (Pattern documented proactively)
**Why it happened:** Steps 6.1-6.3 and most of 6.4 were already implemented in prior sessions but progress.txt still said "Next action: Begin Phase 6, Step 6.1." Thorough verification at session start revealed only integration work remained.
**Rule to prevent:**
- At session start, don't just read progress.txt — verify by checking if the files listed in IMPLEMENTATION_PLAN.md already exist
- Grep for key symbols/functions before writing a plan that assumes they need to be created
- Prior sessions may have implemented code without updating progress.txt (a known pattern — see LESSONS.md "Always Update progress.txt")
- Quick verification saves an entire session of redundant work
**Related docs:** Docs/progress.txt, Docs/IMPLEMENTATION_PLAN.md

---

### [GENERAL] Unused Type Imports Fail Production Build
**Date:** 2026-02-06
**What went wrong:** `use-offline-cars.ts` imported `CARListItem` type but never used it. `tsc --noEmit` passed, but `npm run build` (which runs `tsc -b`) failed with `TS6196: 'CARListItem' is declared but never used`.
**Why it happened:** Initially imported the type thinking it would be needed for return type annotations, but the hook functions inferred their types from IndexedDB queries instead.
**Rule to prevent:**
- `import type { ... }` imports are still checked by the compiler — unused types cause build failures
- After creating any file with type imports, verify each imported type is actually used
- Run `npm run build` (not just `tsc --noEmit`) as final verification — `tsc -b` is stricter
- This is a repeat of the "Always Audit Imports" lesson — applies to type imports too
**Related docs:** src/hooks/use-offline-cars.ts, tsconfig.json

---

### [WORKFLOW] Read CLAUDE.md Explicitly — Not Just CLAUDE_VIMS.md
**Date:** 2026-02-06
**What went wrong:** At session startup, read `CLAUDE_VIMS.md` but skipped explicitly reading `CLAUDE.md`. User had to ask "have you read CLAUDE.md?" to catch the oversight.
**Why it happened:** CLAUDE_VIMS.md is the extended rules file with project-specific instructions. Assumed reading it was sufficient since CLAUDE.md was already loaded in system context. But the startup sequence in CLAUDE.md itself says "Read CLAUDE.md" as step 1.
**Rule to prevent:**
- Session startup step 1 is "Read CLAUDE.md" — do it EXPLICITLY, not implicitly via system context
- CLAUDE.md and CLAUDE_VIMS.md are BOTH required reads, not either/or
- The startup sequence is: CLAUDE.md → progress.txt → IMPLEMENTATION_PLAN.md → LESSONS.md → tasks/todo.md → user approval
- Follow the sequence literally, reading each file with the Read tool
**Related docs:** Docs/CLAUDE.md (Session Startup Sequence), Docs/CLAUDE_VIMS.md

---

### [COMPONENT] loading-skeleton.tsx Has No Generic LoadingSkeleton Export
**Date:** 2026-02-06
**What went wrong:** Used `import { LoadingSkeleton } from '@/components/shared/loading-skeleton'` in notification-list.tsx, but the file only exports named skeletons (CardSkeleton, ListSkeleton, TextSkeleton, etc.) and the `LoadingSkeletonProps` interface — there is no `LoadingSkeleton` component.
**Why it happened:** Assumed a generic "LoadingSkeleton" wrapper existed because the file is named `loading-skeleton.tsx`. Didn't check actual exports before importing.
**Rule to prevent:**
- `loading-skeleton.tsx` exports: TextSkeleton, CardSkeleton, ListSkeleton, FormFieldSkeleton, FormSkeleton, DetailHeaderSkeleton, SectionSkeleton, InspectionCardSkeleton, CARCardSkeleton, DeficiencyItemSkeleton
- For generic skeleton shapes, use `Skeleton` from `@/components/ui/skeleton` instead
- Always grep or read the file's exports before importing: `grep "export" src/components/shared/loading-skeleton.tsx`
**Related docs:** src/components/shared/loading-skeleton.tsx, src/components/ui/skeleton.tsx

---

### [COMPONENT] ErrorState Prop Is message, Not description
**Date:** 2026-02-06
**What went wrong:** Passed `description` prop to ErrorState component, but the correct prop name is `message`. TypeScript would have caught this, but it's better to know upfront.
**Why it happened:** Confused with toast API which uses `description`, or with EmptyState which uses `description`. ErrorState uses `message`.
**Rule to prevent:**
- ErrorState props: `title?`, `message?`, `onRetry?`, `retryLabel?`, `className?`
- EmptyState props: `title`, `description?`, `actionLabel?`, `onAction?`
- Toast props: `title?`, `description?`, `variant?`
- These three similar components use DIFFERENT prop names for the secondary text
**Related docs:** src/components/shared/error-state.tsx, src/components/shared/empty-state.tsx

---

### [COMPONENT] React.memo() With Named Functions, Not Arrow Functions
**Date:** 2026-02-06
**What went wrong:** N/A (Pattern documented proactively from Step 8.4 memoization work)
**Why it happened:** When wrapping existing arrow function components with `memo()`, the component loses its display name in React DevTools (shows as "Anonymous" or "memo()").
**Rule to prevent:**
- When wrapping with `memo()`, convert arrow function to named function:
  ```typescript
  // BEFORE (arrow):
  export const MyCard: FC<Props> = ({ ... }) => { ... };

  // AFTER (memo + named function):
  export const MyCard: FC<Props> = memo(function MyCard({ ... }) { ... });
  ```
- Key changes: `= ({` → `= memo(function ComponentName({`, `}) => {` → `}) {`, `};` → `});`
- Import: `import { memo, type FC } from 'react'` (not `import type { FC }`)
- The named function inside `memo()` preserves the component name in React DevTools
**Related docs:** src/components/inspection/inspection-card.tsx, src/components/car/car-card.tsx

---

### [WORKFLOW] Read ALL 11 Startup Files — No Exceptions
**Date:** 2026-02-06
**What went wrong:** Only read 4 of 11 required startup files (CLAUDE_VIMS.md, progress.txt, IMPLEMENTATION_PLAN.md, LESSONS.md). User called it out: "did you read startup files?"
**Why it happened:** Prioritized speed over thoroughness. Read the most critical files and skipped docs that seemed less relevant for a performance optimization task (PRD.md, APP_FLOW.md, TECH_STACK.md, etc.).
**Rule to prevent:**
- CLAUDE_VIMS.md lists 11 mandatory startup files — read ALL of them, every session
- The full list: CLAUDE.md, CLAUDE_VIMS.md, progress.txt, IMPLEMENTATION_PLAN.md, LESSONS.md, PRD.md, APP_FLOW.md, TECH_STACK.md, BACKEND_STRUCTURE.md (header), FRONTEND_GUIDELINES.md, DESIGN_SYSTEM.md, VALIDATION_RULES.md
- Even if a doc seems irrelevant to the current task, read it anyway — context prevents mistakes
- "No exceptions" means no exceptions
**Related docs:** Docs/CLAUDE_VIMS.md (Session Startup Sequence)

---

### [DATA] Never Duplicate Type Definitions Across Files
**Date:** 2026-02-07
**What went wrong:** `SyncConflict` was defined in TWO places: `types/index.ts` (used by components, with wrong field names `vessel_version`/`server_version`/`conflict_fields`) and `lib/api/sync.ts` (matching backend response with `vessel_data`/`server_data`/`conflicting_fields`). Components imported from `@/types` and silently had the wrong type — no runtime error because the data was never populated (mock placeholder).
**Why it happened:** The type in `types/index.ts` was created early during Phase 7 planning with assumed field names. When the backend serializer was built later, `lib/api/sync.ts` got the correct type, but `types/index.ts` was never updated. The duplicate was invisible because the mock data path never tested with real API responses.
**Rule to prevent:**
- Every shared type should exist in ONE place only — `types/index.ts` for domain types
- API-layer files (`lib/api/*.ts`) should import types from `@/types`, not redefine them
- When creating a backend endpoint, grep frontend for any type with the same name and verify alignment
- Before wiring real data to a component that used mock data, verify all field names match the API response
- Pattern: `grep "interface SyncConflict" src/ --include="*.ts" --include="*.tsx"` to check for duplicates
**Related docs:** src/types/index.ts, src/lib/api/sync.ts

---

### [API] Token Blacklist --fake Migration for Shared Databases
**Date:** 2026-02-07
**What went wrong:** N/A (Solution documented proactively for future reference)
**Why it happened:** Shared dev database already had `token_blacklist` tables from another Django project, causing migration conflicts when trying to enable the app.
**Rule to prevent:**
- When a shared database has tables that match a Django app's migrations, use `migrate <app> --fake` to mark migrations as applied without running SQL
- Always verify with `python manage.py check` after faking migrations
- This is safe when the existing tables match the expected schema exactly
- If tables have different schemas, manual SQL ALTER may be needed before faking
- Document the fake migration in progress.txt so future developers know
**Related docs:** psc-backend/core/settings.py, Django migration documentation

---

### [API] Backend May Return Different Case Than Frontend Expects
**Date:** 2026-02-07
**What went wrong:** Backend JWT token claims and login response include `user_type: 'VESSEL'` (uppercase), but frontend edit pages compare with `user_type === 'vessel'` (lowercase). This caused ALL vessel master permission checks to silently fail — no error thrown, just false comparisons. Edit buttons hidden, users redirected to "Access Denied".
**Why it happened:** Backend `AuthenticatedUser` stores `user_type = 'VESSEL'` (matching database convention). Frontend `AuthUser` type declares `user_type: 'vessel' | 'office'` (lowercase). No normalization layer existed between API response and frontend state. The `useAuth()` hook's `isVessel` computed property uses role-based check (works), but direct `user_type` comparisons in edit pages used lowercase (fails).
**Rule to prevent:**
- Always normalize API response data at the API boundary (in the API layer functions)
- For enums/discriminators from backend, add a normalization function: `normalizeUser()` in `auth.ts`
- Pattern: `user_type: user.user_type?.toLowerCase() as AuthUser['user_type']`
- When adding string comparisons for API-returned values, check the ACTUAL backend response (not just the TypeScript type)
- Test with real backend data, not just TypeScript compilation
**Related docs:** psc-frontend/src/lib/api/auth.ts, psc-backend/apps/accounts/backends.py

---

### [VALIDATION] FEAT-CAR-004 Submit Must Enforce Cause + Qualified Actions
**Date:** 2026-02-07
**What went wrong:** CAR submission accepted records with no CLC/custom cause mapping and accepted IMMEDIATE actions missing owner/due date.
**Why it happened:** `CARSubmitSerializer` only checked action/evidence type counts and root cause length; it did not validate FEAT-CAR-004 cause and owner/due preconditions.
**Rule to prevent:**
- FEAT-CAR-004 submit validation must enforce:
  - At least one cause mapping (`CLC` or custom cause path in current schema)
  - At least one IMMEDIATE action with both owner and due date
  - At least one LONG_TERM action with both owner and due date
- Keep "submission ready" test setup aligned with submit preconditions, and explicitly disable specific prerequisites in gap tests that validate missing-precondition behavior.
**Related docs:** Docs/PRD.md FEAT-CAR-004, Docs/VALIDATION_RULES.md Section 4.2, psc-backend/apps/car/serializers.py, psc-backend/apps/car/tests.py

---

### [DATA] Never parseInt() on UUID Strings
**Date:** 2026-02-07
**What went wrong:** `routes/inspections/new.tsx` did `parseInt(user.vessel_id, 10)` where `vessel_id` is a UUID string like `"e2e7ff0d-ab6d-4485-afb8-aa45aa537d73"`. `parseInt` returns `NaN` (not an error!), which then fails the `!vesselId` check and shows "Unable to determine vessel" error toast.
**Why it happened:** The `CreateInspectionInput` type had `vessel_id: number`, so the code assumed it needed numeric conversion. But vessel_id is actually a UUID (string) in the database and API.
**Rule to prevent:**
- UUIDs are ALWAYS strings — never convert them with parseInt(), Number(), or any numeric function
- vessel_id, inspection_id, car_id, deficiency_id — ALL are UUID strings in this project
- If a TypeScript type says `number` for an ID field, verify against the actual API response before trusting it
- `parseInt()` on a UUID silently returns `NaN` — no error thrown, just broken logic
- Check the backend model: if the field is `UUIDField`, the frontend type MUST be `string`
**Related docs:** psc-frontend/src/types/index.ts, psc-frontend/src/routes/inspections/new.tsx

---

### [API] Backend URL Routing May Not Follow RESTful Convention
**Date:** 2026-02-07
**What went wrong:** Frontend assumed RESTful URL patterns (POST `/inspections/` to create, PUT `/inspections/{id}/` to update, DELETE `/inspections/{id}/` to delete), but backend uses explicit sub-paths: POST `/inspections/create/`, PUT `/inspections/{id}/update/`, DELETE `/inspections/{id}/delete/`. The mismatch caused 405 Method Not Allowed errors.
**Why it happened:** The backend `urls.py` docstring (lines 6-9) said the standard RESTful paths, but the actual urlpatterns (lines 43-49) use separate views with explicit sub-paths. The frontend was built based on the docstring, not the actual URL configuration.
**Rule to prevent:**
- Always check the actual `urlpatterns` in `urls.py`, not just the docstring
- `path('')` handles GET (list), `path('create/')` handles POST (create) — they're separate views
- Similarly, `path('<uuid:id>/')` handles GET (detail), `path('<uuid:id>/update/')` handles PUT
- When debugging 405 errors, the URL is reaching a view that doesn't support that HTTP method
- Compare frontend API calls against backend urlpatterns line-by-line
**Related docs:** psc-backend/apps/inspection/urls.py, psc-frontend/src/lib/api/inspections.ts

---

### [API] Duplicate Permission Classes Across Apps — Check Which One Views Import
**Date:** 2026-02-07
**What went wrong:** `CanEditCAR` exists in TWO files: `accounts/permissions.py` (correct, allows DRAFT + REWORK_REQUESTED for vessel master) and `car/permissions.py` (buggy, only allows DRAFT). The CAR views import from `car/permissions.py`, so vessel masters couldn't edit CARs in REWORK_REQUESTED status.
**Why it happened:** The permission class was originally created in `accounts/permissions.py` during Phase 2. When `apps/car/` was created in Phase 5, a new `CanEditCAR` was written in `car/permissions.py` with slightly different logic. The views were wired to the local copy.
**Rule to prevent:**
- Before creating a permission class, grep for existing ones with the same name: `grep "class CanEditCAR" psc-backend/ -r`
- If a permission class already exists in another app, either import it or keep them in sync
- When fixing a permission bug, check ALL files that define that permission class
- Prefer a single source of truth for permission logic — don't duplicate across apps
**Related docs:** psc-backend/apps/car/permissions.py, psc-backend/apps/accounts/permissions.py

---

### [VALIDATION] FEAT-CAR-002 Rules Must Be Enforced in Serializers
**Date:** 2026-02-07
**What went wrong:** CAR update accepted past `target_date`, accepted arbitrary `clc_item_ids`, and corrective actions could be created without owner/due date.
**Why it happened:** `CARUpdateSerializer` and `CorrectiveActionCreateSerializer` declared fields but had no rule-level validators for these FEAT-CAR-002 constraints.
**Rule to prevent:**
- Add serializer-level validation for all non-trivial business fields, not just type parsing
- `target_date` and `due_date` must reject past dates
- Corrective action create must require both owner (`owner_crew_id` or `owner_user_id`) and `due_date`
- `clc_item_ids` must be validated against master CLC IDs before mapping rows are written
- For unmanaged/external master dependencies in tests, patch lookup helpers so happy-path and invalid-path checks are deterministic
**Related docs:** Docs/PRD.md FEAT-CAR-002, Docs/VALIDATION_RULES.md Sections 4.1 and 5.1, psc-backend/apps/car/serializers.py

---

### [API] Auto-Create CAR Signal Must Mirror FEAT-CAR-001 Defaults and Activity Logging
**Date:** 2026-02-07
**What went wrong:** Deficiency creation auto-created a CAR in DRAFT, but left `CAR.target_date` as `NULL` and did not write a `CAR_CREATED` activity event.
**Why it happened:** The Django signal implementation in `apps/inspection/signals.py` only handled CAR row creation + linking, and omitted two FEAT-CAR-001 behaviors that were defined in docs/tests (target-date defaulting and activity timeline entry).
**Rule to prevent:**
- Any replacement of documented DB-trigger behavior with Django signals must include all documented side effects, not just primary row creation.
- For FEAT-CAR-001 auto-create flow, signal must do all of:
  1. create CAR in `DRAFT`
  2. default `CAR.target_date` to `Deficiency.target_date` or `today + 7 days`
  3. create `ActivityHistory` event `CAR_CREATED` for vessel timeline
- Keep FEAT_CAR_001 tests (`TestFEAT_CAR_001_AutoCreateCAR`) green as regression guard before closing related work.
**Related docs:** Docs/PRD.md FEAT-CAR-001, Docs/BACKEND_STRUCTURE.md Section 8.1 and Part 5.1, psc-backend/apps/inspection/signals.py, psc-backend/apps/car/tests.py

---

### [VALIDATION] FEAT-CAR-005 PIC Accept Must Enforce Comment Min Length
**Date:** 2026-02-07
**What went wrong:** PIC accept endpoint returned success for short comments (for example `"short"`), but `VALIDATION_RULES.md` Section 4.3 requires at least 10 characters.
**Why it happened:** `CARPICAcceptSerializer` declared `comment` with `min_length=1`, so request validation did not enforce the documented rule.
**Rule to prevent:**
- FEAT-CAR-005 must enforce `comment` minimum length at serializer level (`min_length=10`) before any status transition writes.
- Keep a regression test that sends a short comment and expects HTTP 400 (`test_feat_car_005_gap_validation_comment_min_10_required`).
- For comment-based state transitions, compare serializer field constraints against `VALIDATION_RULES.md` before closing the task.
**Related docs:** Docs/VALIDATION_RULES.md Section 4.3, Docs/PRD.md FEAT-CAR-005, psc-backend/apps/car/serializers.py, psc-backend/apps/car/tests.py

---

### [WORKFLOW] Always Close Debug Fixes with Progress + Lessons Updates
**Date:** 2026-02-07
**What went wrong:** A debug fix can be completed in code/tests, but if `progress.txt` and `LESSONS.md` are not updated in the same session, project state drifts and context is lost for the next session.
**Why it happened:** Documentation close-out was treated as optional after technical verification.
**Rule to prevent:**
- After every debug fix, update both `Docs/progress.txt` and `Docs/LESSONS.md` before closing the session.
- `progress.txt` must record reproduction, root cause, fix, and verification command results.
- `LESSONS.md` must capture the root mistake pattern and an actionable prevention rule.
**Related docs:** Docs/DEBUG_AGENT.md Step 7, Docs/progress.txt, Docs/LESSONS.md

---

### [CAR API CONTRACT] FEAT-CAR-007/009/010 Gaps Came from Serializer/View Drift
**Date:** 2026-02-07
**What went wrong:** CAR endpoints passed older happy-path tests but failed gap tests for FEAT-CAR-007/009/010:
- DPA close accepted short comments.
- CAR list did not support `source`, `date_from/date_to`, and `overdue` filters.
- CAR list payload lacked `is_overdue`.
- CAR detail allowed cross-vessel access for vessel users.
- CAR detail evidence payload lacked preview metadata.
**Why it happened:** Serializer and view logic drifted from documented FEAT acceptance criteria and validation rules, and payload/filter contracts were not re-verified after earlier implementation sessions.
**Rule to prevent:**
- For state-transition comments, match serializer `min_length` exactly to `VALIDATION_RULES.md` before merge.
- Treat list query params and response keys as explicit API contract; add regression tests for each documented filter/indicator.
- Enforce vessel own-vessel visibility checks in detail endpoints even when list filtering already exists.
- Include UI-required evidence preview metadata (`preview_url`) in detail payload contracts.
**Related docs:** Docs/PRD.md FEAT-CAR-007/009/010, Docs/VALIDATION_RULES.md Section 4.5, Docs/BACKEND_STRUCTURE.md Sections 10.5 and 11.2, psc-backend/apps/car/serializers.py, psc-backend/apps/car/views.py

---

### [VALIDATION] FEAT-CAR-011 Add Action Must Enforce Status + Owner Normalization
**Date:** 2026-02-07
**What broke:** Corrective action create accepted requests in invalid CAR states and treated whitespace-only `owner_user_id` as a valid owner.
**Why it broke:** `CorrectiveActionCreateView` lacked CAR status precondition checks, and `CorrectiveActionCreateSerializer` validated owner presence without normalizing blank-only strings.
**Rule to prevent:**
- Enforce FEAT-CAR-011 status precondition in the view before serializer writes: CAR must be `DRAFT` or `REWORK_REQUESTED`.
- Normalize string owner fields (`strip`) before owner-presence checks; blank-only input must never satisfy required-owner rules.
- Keep regression coverage in `TestFEAT_CAR_011_AddCorrectiveAction` for both status precondition and whitespace-owner edge case.
**Related docs:** Docs/PRD.md FEAT-CAR-011, Docs/VALIDATION_RULES.md Section 5.1, psc-backend/apps/car/serializers.py, psc-backend/apps/car/views.py, psc-backend/apps/car/tests.py

---

### [VALIDATION] FEAT-CAR-012 Completion Endpoint Must Be Idempotency-Safe
**Date:** 2026-02-07
**What broke:** Completion endpoint required `completion_remarks` even though spec marks it optional, and allowed re-completing an already completed action.
**Why it broke:** Serializer constraints drifted from `VALIDATION_RULES.md` Section 5.2, and the view lacked an explicit already-completed precondition guard.
**Rule to prevent:**
- Treat documented optional fields as optional in serializer definitions; enforce only documented limits (here: max 4000 chars).
- Add explicit already-completed guard in state-transition endpoints to prevent duplicate transitions and timeline noise.
- Keep regression coverage in `TestFEAT_CAR_012_CompleteCorrectiveAction` for optional remarks and already-completed rejection.
**Related docs:** Docs/PRD.md FEAT-CAR-012, Docs/VALIDATION_RULES.md Section 5.2, psc-backend/apps/car/serializers.py, psc-backend/apps/car/views.py, psc-backend/apps/car/tests.py

---

### [SYNC CONTRACT] FEAT-SYNC-002/003 Must Enforce Push Guards and Include Masters Bucket
**Date:** 2026-02-07
**What broke:** Sync gap tests exposed missing contract checks:
- Pull response omitted `data.masters`.
- Push accepted invalid `client_version`, future `timestamp`, duplicate `event_id`, and >100 events.
- Push checksum accepted `000...000` integrity placeholder.
**Why it broke:** Sync serializers only validated field presence/type, not Section 9.1 business rules, and pull response shape drifted from `BACKEND_STRUCTURE.md` Section 10.9.
**Rule to prevent:**
- Keep FEAT-SYNC request guards in serializer validation (not only service logic): `client_version >= 1`, timestamp not future, event count <= 100, unique `event_id`.
- Enforce checksum integrity guard in request validation; reject known invalid sentinel payload checksums.
- Keep `data.masters` present in pull response to preserve FEAT-SYNC-002 response contract.
- Add/retain regression tests for each rule in `apps/sync/tests.py`.
**Related docs:** Docs/VALIDATION_RULES.md Section 9.1, Docs/BACKEND_STRUCTURE.md Section 10.9, psc-backend/apps/sync/serializers.py, psc-backend/apps/sync/sync_service.py, psc-backend/apps/sync/tests.py

---

### [SYNC RELIABILITY] FEAT-SYNC-006 Upload Failures Must Round-Trip into Queue State
**Date:** 2026-02-07
**What broke:** Attachment uploads could fail, but queue state/UI never reflected those failures, and backend upload URLs pointed to a non-existent route.
**Why it broke:** Frontend push marked items completed before upload outcomes and treated uploads as fire-and-forget; failed rows were not included in retry selection; backend emitted `/api/psc/sync/upload/{token}` URLs without implementing the endpoint/token validation path.
**Rule to prevent:**
- Never clear sync queue items tied to attachment uploads before upload results are persisted.
- Persist FEAT-SYNC-006 terminal states directly to `syncQueue` (`FAILED` with `error_message`), then render retry UI from that source of truth.
- Push retry selection must include both `PENDING` and `FAILED` rows.
- If backend returns tokenized upload URLs, route/view/token validation must be delivered in the same change set as URL generation.
**Related docs:** Docs/PRD.md FEAT-SYNC-003/006, Docs/VALIDATION_RULES.md Section 11.4, Docs/BACKEND_STRUCTURE.md Section 10.9, psc-frontend/src/lib/sync/sync-service.ts, psc-frontend/src/lib/db/sync-queue.ts, psc-backend/apps/sync/urls.py, psc-backend/apps/sync/views.py, psc-backend/apps/sync/sync_service.py

---

### [WORKFLOW] Backend Tests Must Default to Isolated Test Settings
**Date:** 2026-02-07
**What broke:** Running `python manage.py test apps.sync.tests` used SQL Server settings, attempted to create `test_ksm_cms_dev`, and failed non-interactively (`EOFError`) when the DB already existed. Running `pytest` also failed to collect Django tests because settings/apps were not initialized.
**Why it broke:** Test execution relied on implicit operator flags (`--settings=core.settings_test`) and had no project-level pytest bootstrap for Django DB lifecycle setup.
**Rule to prevent:**
- Default `manage.py test` runs must use `core.settings_test` unless settings are explicitly provided.
- Keep a pytest bootstrap (`conftest.py`) that sets `DJANGO_SETTINGS_MODULE=core.settings_test`, calls `django.setup()`, and manages `setup_databases()/teardown_databases()`.
- Keep sync conflict resolution input constraints aligned with docs (`notes` max 1000 chars per `VALIDATION_RULES.md` 9.2) so full suites pass once DB setup is stable.
**Related docs:** Docs/DEBUG_AGENT.md (Step 1, Step 6), Docs/VALIDATION_RULES.md Section 9.2, psc-backend/manage.py, psc-backend/conftest.py, psc-backend/apps/sync/serializers.py, psc-backend/apps/sync/tests.py

---

### [SYNC CONTRACT] FEAT-SYNC-001 Pull Must Persist Masters Bucket to IndexedDB
**Date:** 2026-02-07
**What broke:** `pullFromServer()` merged inspections/deficiencies/CARs but ignored `data.masters`, so the FEAT-SYNC-001 masters-persistence test failed and offline master cache could remain stale after sync.
**Why it broke:** Frontend pull-path implementation drifted from the sync payload contract after backend added the `masters` bucket; no persistence call was wired in sync-service.
**Rule to prevent:**
- When sync pull contract contains `data.masters`, always persist it via `bulkPutMasterData()` in the same pull transaction path.
- Keep `SyncPullData` type contract in `src/lib/api/sync.ts` aligned with backend response shape (including optional buckets).
- Treat sync contract tests (`sync-service.test.ts`) as release gates for offline data integrity.
**Related docs:** Docs/PRD.md FEAT-SYNC-001/002, Docs/BACKEND_STRUCTURE.md Section 10.9, psc-frontend/src/lib/sync/sync-service.ts, psc-frontend/src/lib/api/sync.ts, psc-frontend/src/lib/sync/sync-service.test.ts

---

### [API] Inspection Edit/Delete Flows Must Apply Full Compliance Side Effects
**Date:** 2026-02-07
**What broke:** FEAT-INS gap tests failed because inspection update did not create audit entries, post-submit edits did not increment `revision_no`, and deleting a draft inspection did not soft-delete linked deficiency/CAR rows.
**Why it broke:** `InspectionUpdateView` and `InspectionDeleteView` implemented primary CRUD writes but omitted documented side effects (audit trail, revision tracking, and cascading soft-delete semantics).
**Rule to prevent:**
- Treat inspection update/delete as workflow operations, not plain CRUD; verify side effects from docs/tests before closing.
- On every successful inspection update, write one `AuditLog` `UPDATE` record; office users must set `is_office_edit_assist=True`.
- When editing non-`DRAFT` inspections, increment `revision_no`.
- When deleting `DRAFT` inspections, soft-delete related `Deficiency` and linked `CAR` records in the same transaction.
**Related docs:** Docs/PRD.md FEAT-INS-007/008/009, Docs/VALIDATION_RULES.md Section 2.5, Docs/BACKEND_STRUCTURE.md Section 10.3, psc-backend/apps/inspection/views.py, psc-backend/apps/inspection/tests.py

---

### [VALIDATION/RBAC] Inspection Create/Submit Must Enforce Contract Preconditions End-to-End
**Date:** 2026-02-08
**What broke:** Inspection gap tests exposed missing FEAT-INS-001/004 rules:
- Create accepted future `inspection_date`.
- Create did not enforce PSC `mou_id`.
- Create accepted 1-character `port_place`.
- Submit allowed vessel crew role.
- Submit did not block orphan deficiencies without linked CAR.
- Submit did not write `INSPECTION_SUBMITTED` activity history.
- API contract path mismatch: root `POST /api/psc/inspections/` was not implemented.
**Why it broke:** Validation and workflow guards drifted between serializers, permissions, and views; contract assumptions in docs were not locked by endpoint-level regression coverage.
**Rule to prevent:**
- Keep FEAT-INS create rules centralized in serializer validation (future date, PSC MOU required, port min length) for both create and update flows.
- Enforce submit role gates in permission class, not only in view/serializer preconditions.
- Treat submit as a workflow transition: validate linked entities (deficiency→CAR) and always create activity timeline events.
- Keep root contract endpoints (`POST /api/psc/inspections/`) covered even when legacy aliases (`/create/`) remain.
**Related docs:** Docs/PRD.md FEAT-INS-001/004, Docs/VALIDATION_RULES.md Sections 2.1/2.2, Docs/BACKEND_STRUCTURE.md Section 10.3, psc-backend/apps/inspection/serializers.py, psc-backend/apps/inspection/permissions.py, psc-backend/apps/inspection/views.py, psc-backend/apps/inspection/tests.py

---

### [VALIDATION] INS-002 Upload Report Description Must Be Explicitly Required
**Date:** 2026-02-08
**What broke:** FEAT-INS-002 gap test `test_gap_validation_description_should_be_mandatory` failed because upload requests without `description` returned `201 Created` instead of `400 Bad Request`.
**Why it broke:** `InspectionReportUploadSerializer` set `description` to `required=False` with `allow_blank=True`, drifting from FEAT-INS-002 acceptance criteria.
**Rule to prevent:**
- Treat report upload `description` as a required field in serializer validation; do not rely on database nullability to define API contract.
- Keep `Docs/VALIDATION_RULES.md` aligned with PRD acceptance criteria when contract-level validation changes are made.
- For every backfill gap labeled "mandatory mismatch", add a direct negative test (missing field) and run the full feature-class subset after the fix.
**Related docs:** Docs/PRD.md FEAT-INS-002, Docs/VALIDATION_RULES.md Section 8.1, psc-backend/apps/inspection/serializers.py, psc-backend/apps/inspection/tests.py

---

### [VALIDATION/WORKFLOW] INS-003 Deficiency Create Must Enforce Rule Set Across Serializer + View
**Date:** 2026-02-08
**What broke:** FEAT-INS-003 gap tests failed in five places: short descriptions and >4000 descriptions were accepted, past `target_date` was accepted, vessel users could add deficiencies on `SUBMITTED` inspections, and deficiency create wrote no `DEFICIENCY_ADDED` activity event.
**Why it broke:** Contract rules were split between layers but partially implemented. `DeficiencyCreateSerializer` lacked explicit description/date validators, and `DeficiencyCreateView` enforced status membership (`DRAFT`/`SUBMITTED`) without the documented office-only branch for `SUBMITTED`, and without timeline side-effect creation.
**Rule to prevent:**
- For FEAT-INS-003, enforce `description` length (10-4000) and non-past `target_date` directly in `DeficiencyCreateSerializer`.
- In `DeficiencyCreateView`, treat `SUBMITTED` as a conditional state: only `OFFICE` users may add deficiencies.
- On every successful deficiency create, always write `ActivityHistory` with `entity_type='DEFICIENCY'` and `event_type='DEFICIENCY_ADDED'`.
- Keep targeted class verification (`TestFEAT_INS_003_AddDeficiency`) as a regression gate after any create-flow change.
**Related docs:** Docs/PRD.md FEAT-INS-003, Docs/VALIDATION_RULES.md Section 3.1, Docs/BACKEND_STRUCTURE.md Section 10.4, psc-backend/apps/inspection/deficiency_serializers.py, psc-backend/apps/inspection/deficiency_views.py, psc-backend/apps/inspection/tests.py

---

### [COMPONENT/A11Y] Radix DialogContent Requires a Description Contract
**Date:** 2026-02-08
**What broke:** `DeficiencyModal` rendered `DialogContent` with title only, which emitted repeated Radix accessibility warnings during tests: missing dialog description / `aria-describedby`.
**Why it broke:** The modal implementation omitted `DialogDescription`, so the dialog accessibility relationship was incomplete even though behavior tests still passed.
**Rule to prevent:**
- For every Radix dialog, include either `DialogDescription` or an explicit `aria-describedby` override.
- Add a regression assertion that the rendered `role="dialog"` element has a non-empty `aria-describedby` that points to description content.
- Treat accessibility warnings in test stderr as defects, not noise.
**Related docs:** Docs/FRONTEND_GUIDELINES.md (component architecture), psc-frontend/src/components/inspection/deficiency-modal.tsx, psc-frontend/src/components/inspection/deficiency-modal.test.tsx

---

### [SYNC/STATUS-FLOW] FEAT-SYNC-005 REOPEN_FOR_MERGE Must Set CAR to REWORK_REQUESTED (Not DRAFT)
**Date:** 2026-02-08
**What broke:** Sync conflict resolution (`REOPEN_FOR_MERGE`) moved CAR to `DRAFT`, and sync tests encoded the same expectation.
**Why it broke:** Implementation and test assertions drifted from PRD acceptance criteria for FEAT-SYNC-005 (`REOPEN_FOR_MERGE: set CAR to REWORK_REQUESTED`).
**Rule to prevent:**
- For sync conflict resolution, treat `REOPEN_FOR_MERGE` as a CAR status transition to `REWORK_REQUESTED`; do not auto-transition to `DRAFT` inside the sync resolver.
- Keep resolver logic and FEAT-SYNC tests aligned with PRD language for status transitions.
- When status transitions are doc-driven, assert the exact terminal status in tests (not an inferred downstream status).
**Related docs:** Docs/PRD.md FEAT-SYNC-005, psc-backend/apps/sync/conflict_resolver.py, psc-backend/apps/sync/tests.py

---

### [QUALITY/TOOLING] Backend Static Checks Must Use Project Venv + Local Mypy Config
**Date:** 2026-02-08
**What broke:** Requested validation (`pytest -v`, `mypy .`, `ruff check .`) was initially non-actionable:
- `pytest` auto-discovery returned 0 tests because this repo uses per-app `tests.py` modules.
- `mypy`/`ruff` were missing from global Python, and mypy inherited strict/global defaults that produced framework-noise.
**Why it broke:** Toolchain execution relied on ambient environment instead of project-local setup and repo-specific config.
**Rule to prevent:**
- Run backend static checks from `psc-backend/venv` and keep a project `mypy.ini` (Django + DRF plugins, repo-appropriate excludes).
- Use explicit pytest module targets for this backend layout when global discovery is not configured.
- Treat lint auto-fixes as safe only for mechanical issues (unused imports/vars, ordering), then re-run full regression tests.
**Related docs:** docs/DEBUG_AGENT.md (verification step), psc-backend/mypy.ini, psc-backend/apps/*/tests.py

---

### [COMPONENT/A11Y] CAR Action Modals Must Include DialogDescription
**Date:** 2026-02-08
**What broke:** CAR modal tests emitted repeated Radix warnings: missing dialog description / `aria-describedby` for `DialogContent` in PIC Accept, Rework, and DPA Close flows.
**Why it broke:** `DialogContent` was rendered with `DialogTitle` only in multiple CAR action modals; the accessibility description contract was applied inconsistently after prior deficiency-modal fixes.
**Rule to prevent:**
- Every modal using Radix `DialogContent` must include `DialogDescription` (or explicit `aria-describedby={undefined}` when intentionally omitted).
- When one modal in a feature family fails an a11y contract, audit sibling modals in that family, not just the surfaced test target.
- Treat test stderr accessibility warnings as defects and close them at source-component level.
**Related docs:** Docs/FRONTEND_GUIDELINES.md, Docs/DEBUG_AGENT.md, psc-frontend/src/components/car/pic-accept-modal.tsx, psc-frontend/src/components/car/rework-modal.tsx, psc-frontend/src/components/car/dpa-close-modal.tsx, psc-frontend/src/components/car/evidence-upload-modal.tsx

---

### [WORKFLOW/VALIDATION] Mandatory Transition Comments Require Form Modals, Not Confirm Dialogs
**Date:** 2026-02-08
**What broke:** Inspection detail route allowed PIC review and DPA close with empty comments because transitions were triggered from generic confirm dialogs without input collection.
**Why it broke:** FEAT-INS-005/006 contract requires mandatory comments (min 10 chars), but route-level UI flow used `ConfirmDialog` for state transition actions and passed empty payloads.
**Rule to prevent:**
- For any transition with required input fields, use dedicated form modals with schema validation (`react-hook-form` + `zod`), not confirmation-only dialogs.
- Add route-level tests that assert mutation payload contains non-empty validated fields for the transition.
- Keep acceptance criteria and UI interaction contract aligned: if backend requires a field, route UI must collect and validate it before mutation.
**Related docs:** Docs/PRD.md FEAT-INS-005/006, Docs/VALIDATION_RULES.md Sections 2.3/2.4, psc-frontend/src/routes/inspections/[id].tsx, psc-frontend/src/components/inspection/inspection-pic-review-modal.tsx, psc-frontend/src/components/inspection/inspection-dpa-close-modal.tsx

---

### [RBAC] Assigned-Verifier Checks Must Match Actual Caller Identity
**Date:** 2026-02-08
**What broke:** CAR detail route allowed office users to close physical verification whenever `verifier_user_id` existed, even if caller was not the assigned verifier.
**Why it broke:** Permission gate checked verifier presence, not verifier identity match.
**Rule to prevent:**
- For assignment-based permissions, compare assignment field to current user identity, not just non-null assignment.
- Normalize identifiers (trim + lowercase) before comparison when values may come from different sources (`employee_id`, `id`).
- Keep DPA override explicit and isolated in permission expression.
**Related docs:** Docs/PRD.md FEAT-PV-002, Docs/BACKEND_STRUCTURE.md RBAC matrix Section 11.1, psc-frontend/src/routes/cars/[id].tsx

---

### [COMPONENT] useAuthStore Is Not Exported from use-auth.ts
**Date:** 2026-02-09
**What broke:** Vite production build failed because `deficiency-workflow-actions.tsx` imported `useAuthStore` from `@/hooks/use-auth`, but that file only exports `useAuth` (the hook wrapper). The actual store lives in `@/stores/auth-store`.
**Why it broke:** During Session 66, `useAuthStore` was used directly instead of `useAuth()`. The dev server (with HMR) didn't catch the missing export, but production build (Rollup) does.
**Rule to prevent:**
- Never import `useAuthStore` from `@/hooks/use-auth.ts` — it only exports `useAuth()`.
- The store (`useAuthStore`) lives in `@/stores/auth-store` but should rarely be used directly.
- Always prefer `useAuth()` hook which wraps the store with computed values.
- Production build (`vite build`) catches import errors that dev server misses — always run it.
**Related docs:** psc-frontend/src/hooks/use-auth.ts, psc-frontend/src/stores/auth-store.ts

---

### [RBAC] masterOnly Nav Flag Must Also Allow Office Users
**Date:** 2026-02-09
**What happened:** When implementing `masterOnly` filtering for nav items, the initial instinct was `if (item.masterOnly && !isMaster) return false` which would also hide items from office users.
**Why it matters:** Office users need to see Settings and potentially other "admin" items. The `masterOnly` flag means "hidden from crew" not "hidden from everyone except master".
**Rule to prevent:**
- `masterOnly` filter logic: `if (item.masterOnly && !isMaster && !isOffice) return false`
- Think about ALL user types (master, crew, office PIC/SSQE/DPA) when adding role-based visibility.
- Name the flag after what it restricts FROM (crew), not who it restricts TO (master).

---

### [API] Crew DEF Filtering Must Apply at Every Access Point
**Date:** 2026-02-09
**What happened:** VESSEL_CREW users should only see deficiencies assigned to them. This filter must be applied at three separate backend points: list view, detail serializer, and export view.
**Rule to prevent:**
- When adding role-based data filtering, audit ALL access paths: list endpoints, detail serializers, export/report views.
- Defense-in-depth: even if the UI button is hidden, the backend must also enforce the filter.

---

### [RBAC] Check Permission Matrix Before Exposing Nav Items to Roles
**Date:** 2026-02-09
**What happened:** Crew was shown Inspections and Deficiencies nav items even though the permission matrix shows ❌ on ALL actions for those sections. Crew only needs CARs (upload evidence, complete actions) and Notifications.
**Rule to prevent:**
- Before adding nav items, check BACKEND_STRUCTURE.md §11.1 permission matrix for what the role can actually DO on that page.
- If a role has zero actionable permissions on a page, don't show it in nav — read-only views with no actions are dead weight.
- Crew's useful pages: CARs + Notifications. Everything else is master/office territory.
- Always guard both the nav visibility AND the route itself (MasterOnlyGuard pattern).
- When redirecting crew away from restricted routes, send them to their landing page (/cars), not a page they also can't access.
- Use `user.role == 'VESSEL_CREW'` (string comparison) in views — the `RoleCodes` enum is in `accounts/models.py` but views often use raw strings.

---

### [RBAC] Office Vessel Filtering Must Use master_RoleByVessel — Not Open Access
**Date:** 2026-02-09
**What went wrong:** Office users (PIC, SSQE, Supt, PV) had `pass` / `return True` in all list views and the object-level permission check, giving them access to ALL vessels' data. Only DPA should see everything.
**Why it happened:** During initial implementation, vessel filtering for office users was deferred with `# TODO: filter by master_RoleByVessel` comments. The TODOs survived through 70 sessions because E2E testing focused on vessel users and role-based actions, not office data scoping.
**Rule to prevent:**
- Never ship `pass` or `return True` as placeholders for security-critical filtering — use `queryset.none()` as a safe default until the real filter is implemented.
- When adding vessel-scoped list views, apply the filter at EVERY access point: list views, detail permissions, export/report views.
- DPA exemption should be explicit and isolated (check role first, then apply filter for everyone else).
- Create a shared utility function (e.g., `apply_office_vessel_filter`) rather than duplicating filter logic across 4+ views.
- UUID comparison across managed (char32) and unmanaged (uniqueidentifier) tables needs normalization — always convert to UUID objects before comparing.
**Related docs:** psc-backend/core/vessel_access.py, psc-backend/apps/inspection/permissions.py, psc-backend/apps/accounts/models.py (MasterRoleByVessel)

---

### [Validation] Removing UI Fields Requires Updating All Downstream Validators
**Date:** 2026-02-09
**What happened:** Session 72 removed `due_date` from the corrective action create/edit forms per user request, but the `CARSubmitSerializer` (submit precondition validator) still required actions to have both `owner` AND `due_date`. This caused CAR Submit to return 400 Bad Request with "At least 1 immediate corrective action with owner and due date is required."
**Rule to prevent:**
- When removing a field from create/edit forms, search the entire backend for ALL validators/serializers that reference that field — not just the create/update serializer.
- Submit validators, state transition validators, and export generators may all reference the field independently.
- Pattern: `grep -r "field_name" apps/` after removing any field to find all references.
- Think of the data flow: create → validate → save → **submit** → review → close. Removing a field from step 1 must cascade through ALL subsequent steps.

---

### [DATA] Deficiency Model Field Names Differ From Serializer Output
- **Date:** 2026-02-09 (Session 74)
- **Context:** Building dashboard query for monthly DEF trend and top deficiency codes
- **Mistake:** Used `created_at` and `def_code_description` in ORM queries — neither exists on the Deficiency model
- **Root Cause:** Deficiency model uses `created_date` (not `created_at`), and `def_code_description` is a SerializerMethodField that joins to PSCDefCode master table — not a model field
- **Fix:** Use `created_date` for date-based queries. For top def codes, group by `def_code_id` and bulk-lookup descriptions from PSCDefCode separately
- **Rule:** Always check actual model field names (not serializer output field names) before writing ORM queries. Serializers often rename or add computed fields.

### [DATA] CAR Has No Direct vessel_id — Must Traverse FK Chain
- **Date:** 2026-02-09 (Session 74)
- **Context:** Scoping dashboard CAR/CorrectiveAction queries by vessel
- **Issue:** CAR model has no `vessel_id` field — it connects to vessel through `deficiency.inspection.vessel_id`
- **Fix:** Use ORM traversal: `CAR.filter(deficiency__inspection__vessel_id=vid)`, `CorrectiveAction.filter(car__deficiency__inspection__vessel_id=vid)`
- **Rule:** Before writing vessel-scoped queries on any model, check whether it has a direct `vessel_id` or requires FK chain traversal.

## Session Notes

- 2026-02-07: Added Session 33 documentation sync note after FEAT-CAR-005 fix to keep `progress.txt` and `LESSONS.md` aligned.
- 2026-02-07: Added FEAT-CAR-007/009/010 contract-drift lesson after closing all 7 documented CAR gap tests.
- 2026-02-07: Added FEAT-CAR-011/012 validation lessons after closing status/owner and completion-idempotency gaps.
- 2026-02-07: Added FEAT-SYNC-002/003 validation+response-contract lesson after closing six sync gap fixes.
- 2026-02-07: Added FEAT-SYNC-006 reliability lesson after wiring attachment failure persistence and implementing `/api/psc/sync/upload/{token}/`.
- 2026-02-07: Added FEAT-SYNC-001 masters-persistence lesson after wiring pull `data.masters` to IndexedDB bulk upsert.
- 2026-02-07: Added FEAT-INS-007/008/009 edit/delete side-effects lesson after fixing audit, revision, and cascading soft-delete gaps.
- 2026-02-08: Added FEAT-INS-001/004 validation+submit workflow lesson after closing create-rule, submit-RBAC, submit-CAR, activity-event, and root-path contract gaps.
- 2026-02-08: Added FEAT-INS-002 upload report description-mandatory validation lesson and aligned documentation in `progress.txt` and `test_progress.txt`.
- 2026-02-08: Session closed after INS-002 gap verification and documentation sync.
- 2026-02-08: Added FEAT-INS-003 deficiency create validation/precondition/activity-event lesson after closing all 5 INS-003 gap tests.
- 2026-02-08: Session closed after INS-003 closure and documentation sync.
- 2026-02-08: Added FEAT-INS-005/006 transition side-effects lesson after closing missing PIC-review/DPA-close activity events and DPA-close vessel notification.
- 2026-02-08: Session closed after INS-005/006 closure and documentation sync.
- 2026-02-08: Added DeficiencyModal Radix dialog a11y lesson and regression rule (`DialogDescription`/`aria-describedby`) after frontend depth-audit updates.
- 2026-02-08: Added CAR action modal Radix dialog a11y lesson and closed source-component warnings in PIC Accept, Rework, DPA Close, and Evidence Upload modals.
- 2026-02-08: Added FEAT-SYNC-005 status-flow lesson after correcting `REOPEN_FOR_MERGE` CAR transition from `DRAFT` to `REWORK_REQUESTED`.
- 2026-02-08: Added backend tooling lesson after aligning validation commands to project venv + local `mypy.ini` and restoring actionable static checks.
- 2026-02-08: Session closed after documentation sync (`progress.txt`, `LESSONS.md`, `test_progress.txt`) and final verification capture.
- 2026-02-08: Added FEAT-INS-005/006 route-level transition validation lesson after replacing confirm-only actions with validated comment modals.
- 2026-02-08: Added FEAT-PV-002 assigned-verifier RBAC lesson after tightening office close permission to identity match.
- 2026-02-09: Added field-name contract lesson — backend serializer field names (`comment`) don't always match frontend param names (`comments`). Always verify exact field name in serializer before wiring API calls.
- 2026-02-09: Added TanStack Query cache invalidation lesson — never use `setQueryData` with partial response objects (action endpoints return basic `Inspection`, not full `InspectionDetail`). Use `invalidateQueries` to force refetch of complete data.
- 2026-02-09: Added CAR reopen status transition lesson — `CARReopenView` was setting status to `REWORK_REQUESTED` but `CanSubmitCAR` only allows `DRAFT`. Both rework and reopen should set status to `DRAFT` for consistent vessel workflow (edit → resubmit).
- 2026-02-09: Added action button discoverability lesson — critical actions like "Request Rework" and "Reopen CAR" must appear in the sticky bottom bar, not just the overflow dropdown menu. Users miss actions hidden in kebab menus.

- 2026-02-09: Added bulk operations lesson — when implementing batch endpoints, always wrap in `transaction.atomic()` and validate ALL items before mutating ANY (fail-fast pattern). For file downloads, return the simpler format when possible (single PDF vs ZIP for 1 item) to avoid unnecessary overhead.
- 2026-02-09: Added ZIP blob download lesson — when backend may return different content types (PDF for single, ZIP for multiple), check `blob.type` on the frontend to determine file extension. Pattern: `const ext = blob.type === 'application/pdf' ? 'pdf' : 'zip'`.
- 2026-02-09: Session 67 closed after bulk DEF submission and bulk CAR PDF download features.
- 2026-02-09: Session 68 — E2E verified bulk DEF submit (select all, confirm dialog, backend persistence, UI refresh) and bulk CAR download (ZIP with 20 PDFs, correct naming). Both features passed all tests.
- 2026-02-09: Added Django shell field-name lesson — Deficiency model uses `def_status` (not `status`), `created_date` (not `created_at`). Always check model field choices from error output before retrying.
- 2026-02-09: Added venv path lesson — on Windows, use forward slashes `venv/Scripts/python.exe` (not backslashes) when running from bash/shell tools.
- 2026-02-09: Session 69 — Added crew role restriction lessons: useAuthStore import path, masterOnly nav flag must include office, and crew DEF filtering must cover all access points. Fixed pre-existing build error (useAuthStore import).
- 2026-02-09: Session 70 — Added lesson: always check permission matrix before exposing nav items. Crew had Inspections/Deficiencies visible but zero actionable permissions. Scoped crew to CARs + Notifications only.
- 2026-02-09: Session 71 — Added office vessel filtering lesson: never ship `pass`/`return True` as placeholder for security filtering. Fixed all 4 list views + object permission to use master_RoleByVessel. Created shared utility in core/vessel_access.py.
- 2026-02-09: Session 73 — Added field-removal cascading validation lesson. Removing due_date from action forms broke CARSubmitSerializer which still required it. Fixed submit validator to count-based check. Full CAR lifecycle E2E verified (DRAFT→SUBMITTED→PIC_ACCEPTED→CLOSED).
- 2026-02-09: Session 74 — Added Deficiency model field name lesson: Deficiency has `created_date` (not `created_at`), and `def_code_description` comes from serializer join to PSCDefCode master table (not a model field). Dashboard queries must use `def_code_id` for grouping and bulk-lookup descriptions separately.
- 2026-02-09: Session 74 — Added CAR vessel scoping lesson: CAR model has no direct `vessel_id` field — must traverse `deficiency__inspection__vessel_id` for vessel filtering. Same pattern for CorrectiveAction → `car__deficiency__inspection__vessel_id`.
- 2026-02-10: Session 75 — Added VesselData UUID filtering lesson: never use `VesselData.objects.filter(id__in=uuids)` — use `extra(where=[CAST(%s AS uniqueidentifier)])` with hyphenated strings instead. Added type/API field name verification lesson: always compare frontend type field names against actual API response before marking implementation complete.

### [DATA] VesselData Queries Must Use CAST for UUID Filtering
**Date:** 2026-02-10
**What went wrong:** Dashboard API returned 500 ProgrammingError for office users (PIC/SSQE). `_get_vessels_for_office_user()` used `VesselData.objects.filter(id__in=vessel_ids)` which mssql-django converts to char(32) parameters against a native `uniqueidentifier` column.
**Why it happened:** The known UUID gotcha (char(32) vs uniqueidentifier) was documented in MEMORY.md but wasn't applied when the dashboard view was written because the query looked simple and didn't trigger the usual warning signs.
**Rule to prevent:** ANY query filtering VesselData (or other unmanaged tables) by UUID must use `extra(where=[CAST(%s AS uniqueidentifier)])` — never `filter(id=...)` or `filter(id__in=...)`. The pattern:
```python
hyphenated = [str(vid) for vid in vessel_ids]
placeholders = ','.join(['CAST(%s AS uniqueidentifier)'] * len(hyphenated))
qs = VesselData.objects.filter(...).extra(where=[f'id IN ({placeholders})'], params=hyphenated)
```
**Related docs:** MEMORY.md "SQL Server + mssql-django UUID Gotchas" section

### [API] Always Verify Frontend Type Field Names Match Actual API Response
**Date:** 2026-02-10
**What went wrong:** Frontend `DeficiencyDetail` type used `def_text` for the description field, but the backend serializer returns `description`. The deficiency description never rendered on cards or in the detail dialog. The `CAR` type used `def_text` but the API returns `deficiency_description`.
**Why it happened:** Frontend types were written based on spec document naming conventions (`def_text`) without verifying against the actual serializer field names. The mismatch was never caught because TypeScript only checks type structure at compile time — accessing a non-existent property returns `undefined` at runtime, which renders as empty in JSX without errors.
**Rule to prevent:** After implementing any API-consuming component, verify field names by: (1) calling the actual API endpoint, (2) comparing the response keys against the TypeScript interface, (3) confirming the rendered output shows real data, not empty/undefined. When renaming type fields, search the entire codebase with `grep` to find all usages including test files.
**Related docs:** BACKEND_STRUCTURE.md API contracts, types/index.ts

### [WORKFLOW] Unified State Machine Replaces Dual-Status Systems
**Date:** 2026-02-10
**Context:** The deficiency workflow had a dual-status system — DefStatus on the Deficiency model (6 states) and CARStatus on the CAR model (5 states). This caused confusion about which status to display, filter by, and transition.
**Solution:** Unified to a single CAR.status with 9 states, 12 named transitions, one endpoint (`POST /cars/{id}/workflow/`), and a backend `available-actions` endpoint. DEF.def_status is deprecated (kept in DB, not updated by new logic).
**Key patterns:**
- State machine as dict: `TRANSITIONS[(current_status, action)] → {target, allowed_roles, comment_required}`
- `_get_user_workflow_roles(user, deficiency)` resolves owner/reviewer/master/pic/dpa from user attributes
- Frontend: two workflow action components — `DeficiencyWorkflowActions` (client-side role logic) and `CARWorkflowActions` (uses backend `available-actions` endpoint)
- Auto-start: ALLOTTED → IN_PROGRESS on any CAR content edit (via `auto_start_if_allotted()`)
- Legacy endpoints kept as deprecated stubs for backward compat
**Rule:** When replacing status enums, update ALL references: models, views, serializers, permissions, signals, dashboard, frontend types, constants, format-status, filters, cards, and route pages. Use `replace_all=true` for bulk string replacements (e.g., `DPA_CLOSED` → `CLOSED`).

### [FRONTEND] Replace Legacy Action Modals with Unified Workflow Component
**Date:** 2026-02-10
**Context:** The CAR detail page had 5 separate modal components (SubmitConfirmDialog, PICAcceptModal, ReworkModal, DPACloseModal, ReopenModal), each with their own state, mutation hook, and dialog. This was fragile and hard to maintain as workflow evolved.
**Solution:** Replaced with a single `CARWorkflowActions` component that fetches available actions from the backend and renders buttons dynamically. Actions requiring comments show a generic comment dialog. One transition hook (`useTransitionCAR`) handles all 12 workflow actions.
**Rule:** When building workflow UIs, prefer a data-driven approach (fetch available actions from backend) over hardcoded permission checks. This ensures frontend stays in sync with backend state machine changes.

- 2026-02-10: Session 76 — Implemented unified CAR workflow overhaul: 9 statuses, 12 named transitions, single workflow endpoint, backend available-actions endpoint, frontend components updated. DefStatus deprecated. Full TypeScript + Vite build verification passed.

### [SECURITY] Unified Workflow Endpoints Must Inherit Legacy Validation
**Date:** 2026-02-10
**What went wrong:** The unified workflow endpoint `POST /cars/{id}/workflow/` with `action=SUBMIT_TO_PIC` had NO content/evidence validation — only role and status transition checks. The legacy endpoint (`POST /cars/{id}/submit/`) had proper validation via `CARSubmitSerializer`, but the workflow path completely bypassed it. This allowed Master to submit incomplete CARs to PIC.
**Why it happened:** When building the unified workflow (Session 76), we focused on the state machine transitions and role-based access. The validation logic was left in the legacy serializer and never ported to the new code path. The two endpoints weren't connected — they were parallel paths to the same outcome.
**Rule to prevent:** When creating a new "unified" endpoint that replaces multiple legacy endpoints, audit EVERY legacy endpoint for validation logic and ensure the new endpoint inherits it. Create a shared validator function (single source of truth) and call it from both paths. Checklist: (1) Extract validation to a standalone function, (2) Legacy endpoint delegates to it, (3) New endpoint calls it, (4) Available-actions endpoint gates actions based on it.
**Related docs:** validators.py, serializers.py (CARSubmitSerializer), views.py (CARWorkflowView)

### [VALIDATION] Always .trim() User Input Before Length Checks
**Date:** 2026-02-10
**What went wrong:** Frontend `validateCarSubmission()` checked `rootCauseSummary.length` without `.trim()`, allowing a user to bypass the 50-character minimum by padding with spaces. Backend had `.strip()` but frontend didn't match.
**Why it happened:** Copy-paste oversight — the backend serializer used `.strip()` but the frontend validation function used raw `.length`.
**Rule to prevent:** All minimum-length checks on user text input must use `.trim()` (frontend) / `.strip()` (backend) before measuring length. Keep backend and frontend validation logic in sync — when one trims, the other must too.

### [PATTERN] Defense-in-Depth for Critical Workflow Actions
**Date:** 2026-02-10
**Pattern:** For actions with business-critical preconditions (like CAR submission), implement validation at multiple layers:
1. **Hide the button** — available-actions endpoint omits the action if preconditions fail
2. **Client-side check** — validate before sending request (fast feedback, uses cached data)
3. **Server-side gate** — authoritative validation in the endpoint handler (returns structured error)
4. **Error handling** — catch and display server validation errors in case client-side check is bypassed
This prevents bypass via direct API calls, stale UI state, or race conditions.

- 2026-02-10: Session 78 — Fixed CAR submission validation bypass via unified workflow. Created shared validator, gated SUBMIT_TO_PIC at 4 layers, added action description length check (50 chars), fixed .trim() on root cause. E2E testing deferred to Session 79.
- 2026-02-10: Session 80 — Replaced stored 4-stage inspection workflow with computed OPEN/CLOSED status (action_code_id based). Rewrote follow-up as 5-step wizard on same inspection. Added report_type to InspectionReport. Removed Submit/PIC Review/DPA Close workflow buttons. 20 files modified.

---

### [WORKFLOW] Prefer Computed Status Over Stored Status for Derived State
**Date:** 2026-02-10
**What changed:** Inspection had a stored `status` field with 4-stage workflow (DRAFT→SUBMITTED→PIC_REVIEWED→DPA_CLOSED). This was replaced with a computed `operational_status` (OPEN/CLOSED) derived from deficiency `action_code_id` annotations.
**Why it's better:**
- OPEN = any non-deleted deficiency has `action_code_id IS NULL OR action_code_id != 10`
- CLOSED = all non-deleted deficiencies have `action_code_id = 10` (Rectified)
- No manual status transitions needed — status updates automatically when deficiency action codes change
- Uses RawSQL scalar subquery annotations (SQL Server compatible, no GROUP BY conflicts)
- Both list and detail views share the same annotations (no N+1)
**Rule to follow:**
- When status can be derived from child record states, compute it (don't store it)
- Use queryset annotations for computed fields to avoid per-row DB queries
- For SQL Server, always use scalar RawSQL subqueries (not Django ORM aggregations with RawSQL)
- Filter by annotation name (e.g., `_open_def_count__gt=0`), not by stored field
**Related docs:** psc-backend/apps/inspection/views.py, psc-backend/apps/inspection/serializers.py

---

### [API] ActionCode Is Independent of CAR Status
**Date:** 2026-02-10
**Business rule:** A deficiency's ActionCode (e.g., 10=Rectified) is independent of its CAR.status. A DEF can be ActionCode=10 while its CAR is still open (in progress). Follow-up wizard updates action codes but does NOT touch CAR.status.
**Why it matters:** The follow-up process (vessel records PSC reinspection results) and the CAR process (corrective action lifecycle) are parallel workflows. They converge at inspection closure but progress independently.
**Rule to prevent:**
- Do NOT gate ActionCode=10 on CAR closure
- Do NOT auto-sync DEF closure with CAR status
- Follow-up endpoint updates `deficiency.action_code_id` and creates `DeficiencyActionHistory` but never touches `CAR.status`
- 1 DEF = 1 CAR always holds, but their statuses are orthogonal
**Related docs:** psc-backend/apps/inspection/followup_views.py, Docs/PRD.md

---

### [API] Follow-Up Should Update Same Record, Not Create New One
**Date:** 2026-02-10
**What changed:** The original follow-up implementation created a NEW inspection record linked to the parent. This was architecturally wrong — a PSC follow-up records the reinspection results on the SAME inspection.
**Why it matters:** Creating a new record splits the deficiency history, duplicates data, and makes reporting harder. The correct model: follow-up updates deficiency action codes on the existing inspection and optionally uploads a follow-up report (with `report_type='FOLLOW_UP'`).
**Rule to follow:**
- Follow-up = update existing deficiencies + optional report upload
- Use `report_type` field to distinguish original vs follow-up reports on the same inspection
- Store reinspection_date in ActivityHistory metadata, NOT on the inspection master record
- Wrap all updates in `transaction.atomic()` to ensure consistency
**Related docs:** psc-backend/apps/inspection/followup_views.py, psc-backend/apps/inspection/models.py

---

### [Backend] Computed Fields Must Have Matching Annotations in ALL Querysets
**Date:** 2026-02-10
**What happened:** `compute_operational_status()` relied on `getattr(obj, 'deficiency_count', 0)` but the detail view queryset only annotated `open_deficiency_count` and `closed_deficiency_count` — missing `deficiency_count`. The fallback to 0 meant YES inspections with all defs closed would incorrectly show as OPEN (because `total_count=0` → "no defs yet" → OPEN).
**Why it matters:** When a helper function uses `getattr(obj, 'field', default)`, the default silently hides the missing annotation. The code appears to work but produces wrong results for specific edge cases.
**Rule to follow:**
- When adding a computed helper that reads annotated fields, audit ALL querysets that feed into serializers using that helper
- List view and detail view querysets often diverge — they must both annotate the same fields if they share serializer logic
- Prefer failing loudly over silent defaults: consider raising if a required annotation is missing rather than defaulting to 0
**Related docs:** psc-backend/apps/inspection/views.py, psc-backend/apps/inspection/serializers.py

---

### [Backend] Safe State Transitions Need Server-Side Guards
**Date:** 2026-02-10
**Pattern:** When a field change can invalidate existing data (e.g., `def_reported` YES→NO when deficiencies exist), always validate on the server — not just the UI.
**Implementation:**
- `validate_def_reported()` on UpdateSerializer rejects NO if `deficiencies.filter(is_deleted=False).count() > 0`
- `DeficiencyCreateView` rejects POST when `inspection.def_reported == 'NO'`
- Both frontend (hide button) AND backend (reject request) enforce the constraint
**Rule:** Never rely solely on UI gating for data integrity. Every constraint needs a backend guard.
**Related docs:** psc-backend/apps/inspection/serializers.py, psc-backend/apps/inspection/deficiency_views.py

---

### [COMPONENT] React Stale Closures with Hooks in Async Flows
**Date:** 2026-02-10
**What went wrong:** `useUploadInspectionReport(createdInspectionId ?? '')` captured the empty string value at render time. When `setCreatedInspectionId(inspection.id)` was called during `handleSubmit`, the hook's mutation still used the old empty value because React state updates don't re-render mid-async-function.
**Why it happened:** React hooks capture values from the render in which they're invoked. State updates (useState setter) schedule a re-render but don't synchronously update the variable in the current closure. The upload mutation was called before the re-render occurred.
**Rule to prevent:**
- Never use a hook's mutation when the hook's input depends on state that changes in the same async function
- For two-step flows (create → use created ID), call the API directly with the fresh value instead of through a hook
- Pattern: `await api.doThing(freshId, data)` instead of `mutation.mutateAsync(data)` when the mutation captured a stale ID
**Related docs:** psc-frontend/src/routes/inspections/new.tsx

---

### [API] DRF Serializer Fields Default to required=True
**Date:** 2026-02-10
**What went wrong:** `InspectionReportUploadSerializer.description` was a CharField without `required=False`. The frontend's `uploadInspectionReport()` only sends `file` in FormData, never `description`. This caused a 400 error: `{"description":["This field is required."]}`.
**Why it happened:** DRF CharField defaults to `required=True`. When adding fields to serializers, the optionality wasn't explicitly set to match what the frontend actually sends.
**Rule to prevent:**
- When adding fields to DRF serializers, always explicitly set `required=True/False` — don't rely on defaults
- Cross-check serializer fields against the frontend API call to ensure all required fields are actually sent
- For optional fields, always provide `default=''` or `default=None` alongside `required=False`
**Related docs:** psc-backend/apps/inspection/serializers.py

---

### [COMPONENT] Chrome Blocks Programmatic .click() on Hidden File Inputs
**Date:** 2026-02-10
**What went wrong:** The file upload component used `inputRef.current?.click()` on a hidden `<input type="file">`. This worked in Edge but not Chrome, which silently blocks programmatic clicks on display:none/visibility:hidden inputs as a security measure.
**Why it happened:** Different browsers have different security policies for programmatic file input activation. Chrome is stricter than Edge.
**Rule to prevent:**
- Never hide file inputs with display:none or visibility:hidden and rely on .click()
- Instead, overlay the native input over the clickable area using: `position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer`
- The native input remains interactive, Chrome allows user-initiated clicks on it
**Related docs:** psc-frontend/src/components/shared/file-upload.tsx

---

### [DATA] Cleaning Test Data Requires Full FK Dependency Chain
**Date:** 2026-02-10
**What went wrong:** Attempted to DELETE FROM psc_car but hit FK constraint errors from psc_evidence, psc_car_clc_mapping, psc_corrective_action, and psc_physical_verification tables.
**Why it happened:** Raw SQL DELETE doesn't cascade like Django ORM's .delete(). SQL Server enforces FK constraints strictly and the delete order must respect the full dependency chain.
**Rule to prevent:**
- For bulk data cleanup, delete in this order:
  1. psc_deficiency_action_history
  2. psc_car_clc_mapping
  3. psc_corrective_action
  4. psc_evidence
  5. psc_physical_verification
  6. psc_deficiency
  7. psc_inspection_report
  8. psc_car
  9. psc_inspection
- Prefer Django ORM .delete() for active records (handles cascades automatically)
- Use raw SQL only for soft-deleted records that the ORM manager excludes
- The API delete endpoint uses soft-delete and only allows DRAFT status inspections
**Related docs:** psc-backend/apps/inspection/models.py, BACKEND_STRUCTURE.md

---

## Lesson 83: Frontend-Backend Enum Sync
**Date:** 2026-02-10 | **Session:** 83
**What happened:** Frontend PSC_SUBTYPES had MORE_DETAILED and CONCENTRATED_IC but backend had INITIAL, EXPANDED, CIC, FOLLOW_UP. Caused 400 errors on create.
**Why:** Frontend constants were created with assumed values, never validated against canonical docs (BACKEND_STRUCTURE.md).
**Rule:** Always cross-check frontend enum/constant values against backend model choices AND canonical docs before shipping. When in doubt, backend model is source of truth.
**Related docs:** BACKEND_STRUCTURE.md, psc-backend/apps/inspection/models.py, psc-frontend/src/lib/utils/constants.ts

---

## Lesson 84: assigned_crew_id is UUID, NOT CrewID String
**Date:** 2026-02-10 | **Session:** 83
**What happened:** Permission check compared user.crew_id (string like "CRW0002") against deficiency.assigned_crew_id (UUID). They never matched.
**Why:** HRM501 model has both `id` (UUID) and `CrewID` (string). The deficiency stores the UUID in assigned_crew_id, but the JWT token's crew_id claim is the CrewID string.
**Rule:** For permission checks against assigned_crew_id (UUIDField), always use `request.user.id` (UUID), NOT `request.user.crew_id` (CrewID string).
**Related docs:** psc-backend/apps/accounts/backends.py, psc-backend/apps/inspection/deficiency_models.py

---

## Lesson 85: VESSEL_CREW Needs Explicit Permission Grants
**Date:** 2026-02-10 | **Session:** 83
**What happened:** Crew couldn't edit CAR or add corrective actions because CanEditCAR and CanManageAction only allowed VESSEL_MASTER/OFFICE roles.
**Why:** Permissions were written for the initial Master-only workflow; crew assignment was added later but permissions weren't updated.
**Rule:** When adding crew assignment features, audit ALL permission classes that gate the workflow: CanEditCAR, CanManageAction, CanUploadEvidence, CanCompleteAction. Crew must be allowed through each gate they need to pass.
**Related docs:** psc-backend/apps/car/permissions.py

---

## Lesson 86: Frontend Client-Side Permission Checks Must Match Backend
**Date:** 2026-02-10 | **Session:** 83
**What happened:** Backend CanEditCAR was fixed to allow crew, but frontend canEditCAR() in [id].edit.tsx still blocked crew (only checked VESSEL_MASTER).
**Why:** Duplicate permission logic — frontend has its own canEditCAR() function that wasn't updated when backend was fixed.
**Rule:** When fixing backend permissions, ALWAYS search frontend for matching client-side permission checks. They exist in both the detail page ([id].tsx canEdit) and edit page ([id].edit.tsx canEditCAR()).
**Related docs:** psc-frontend/src/routes/cars/[id].edit.tsx, psc-frontend/src/routes/cars/[id].tsx

---

**Remember:** Every mistake is a learning opportunity. Document it here so it never happens again.

---

### [DATA] Office Notification Recipient Lookup Must Use SQL Server UUID-Safe Filtering
**Date:** 2026-02-10
**What went wrong:** CAR submission notifications (`CAR_SUBMITTED`) were not created for PIC/SSQE users even when CAR moved to `SUBMITTED_TO_PIC`. Recipient lookup returned an empty office list.
**Why it happened:** `_get_office_users_for_vessel()` filtered unmanaged `master_RoleByVessel.VesselId` with direct UUID ORM filtering. SQL Server raised conversion errors on mixed/legacy values, so lookup failed and notification pipeline had no recipients.
**Rule to prevent:**
- For unmanaged SQL Server tables with UUID-like columns, never rely on direct UUID ORM filtering as the only path.
- Implement SQL-safe fallback with `TRY_CAST(... AS uniqueidentifier) = CAST(%s AS uniqueidentifier)`.
- Normalize recipient IDs (trim + dedupe) before notification fan-out.
- Add regression tests that force direct filter failure and verify fallback behavior.
**Related docs:** `psc-backend/apps/notifications/signals.py`, `psc-backend/apps/notifications/tests.py`, `Docs/BACKEND_STRUCTURE.md` notifications section

---

### [REPORT] PDF Template Must Mirror Current UI Data Model, Not Legacy Fields
**Date:** 2026-02-10
**What went wrong:** CAR PDF still printed legacy corrective-action columns (`Due Date`, `Pending`, `Completed`) and CLC internal identifiers/prefixes (`CLC Item ...`, code-prefixed labels), while the current CAR screen expects narrative output (Immediate + Long-term/Preventive) and human-readable root-cause labels.
**Why it happened:** Report template logic (`apps/car/reports.py`) drifted from current UI/serializer semantics and retained old table-oriented mapping.
**Rule to prevent:**
- Treat PDF/export as a first-class UI surface: when CAR screen model changes, update print mapping in the same change set.
- Never print internal IDs/codes in end-user CAR reports unless explicitly required.
- For CLC output, resolve label text from master data and strip code prefixes before rendering.
- For corrective actions, print only fields that exist in current section semantics.
**Related docs:** `psc-backend/apps/car/reports.py`, `psc-frontend/src/components/car/car-form.tsx`, `Docs/APP_FLOW.md` CAR edit/detail sections

---

### [WORKFLOW] Duplicate runserver Processes Can Serve Stale Code and Fake “No Change”
**Date:** 2026-02-10
**What went wrong:** User reported “same no change” after backend patch because multiple `manage.py runserver` processes were listening on port `8000`, so requests could hit stale code paths.
**Why it happened:** Dev server lifecycle was not normalized; old background runserver processes were left running.
**Rule to prevent:**
- Before verifying a critical fix, ensure only one backend process is bound to the target port.
- If behavior appears unchanged after code changes, check listener PID(s) first, then restart cleanly.
- Use no-cache headers and timestamped filenames for exported files to avoid stale-download confusion.
**Related docs:** `psc-backend/apps/car/report_views.py`, `psc-backend/apps/inspection/report_views.py`, `Docs/DEBUG_AGENT.md`

---

### [REPORT] Keep Approval Comments in Dedicated Body Sections, Not Timeline Text
**Date:** 2026-02-10
**What went wrong:** CAR PDF `Review / Approval History` printed raw `event_description`, which included appended PIC/DPA comment text. This duplicated approval comments in timeline rows and mixed audit metadata with narrative comments.
**Why it happened:** Report history rendering was coupled to workflow activity message formatting instead of separating action metadata (who/when/what) from comment payloads intended for dedicated body fields.
**Rule to prevent:**
- In PDF/report timelines, render action metadata only; never rely on full event strings when comments can be appended.
- Put approval comments (PIC/DPA) in explicit main-body sections with deterministic data-source fallback.
- For DPA comment sourcing, prefer dedicated model field; otherwise derive from DPA-close history comment before using generic `last_action_comment`.
- Add report tests that assert both presence in body and absence in history for approval comments.
**Related docs:** `psc-backend/apps/car/reports.py`, `psc-backend/apps/car/tests.py`

---

### [WORKFLOW] Every New Workflow Transition Must Be Wired to Notification Dispatch
**Date:** 2026-02-10
**What went wrong:** CARs successfully transitioned from `PIC_REVIEW` to `SUBMITTED_TO_DPA`, but DPA users received no notification.
**Why it happened:** `CARWorkflowView._send_notifications()` was not updated when `SUBMIT_TO_DPA` transition was introduced, so the action had no notification branch.
**Rule to prevent:**
- For each workflow action in `apps/inspection/workflow.py`, verify parity in dispatch side effects: activity, audit, and notification.
- Add an explicit dispatch test per critical action in `apps/car/tests.py` (mock notify function, assert branch called).
- When adding role-specific recipient logic, add trigger-function coverage in `apps/notifications/tests.py`.
**Related docs:** `psc-backend/apps/car/views.py`, `psc-backend/apps/notifications/signals.py`, `psc-backend/apps/car/tests.py`, `psc-backend/apps/notifications/tests.py`

---

### [API] Notification Visibility Must Be Recipient-Scoped, Not Vessel-Wide
**Date:** 2026-02-10
**What went wrong:** Vessel users saw multiple notifications for one action because list/read filters matched `vessel_id` broadly, exposing notifications addressed to other crew and office users on the same vessel.
**Why it happened:** Notification query/permission logic mixed recipient-specific and vessel-wide predicates (`... OR vessel_id = user.vessel_id`) without a true broadcast notification model.
**Rule to prevent:**
- For inbox/read endpoints, enforce recipient ownership first:
  - Vessel: `recipient_type='CREW' AND recipient_id=user.crew_id`
  - Office: `recipient_type='OFFICE' AND recipient_id=user.employee_id`
- Do not use vessel_id-only filtering for recipient-specific records.
- Add tests for same-vessel cross-recipient isolation on list, mark-read, and mark-all-read.
**Related docs:** `psc-backend/apps/notifications/views.py`, `psc-backend/apps/notifications/permissions.py`, `psc-backend/apps/notifications/tests.py`, `Docs/PRD.md` FEAT-NOTIF-001

---

### [COMPONENT] High-Impact Workflow Actions Need Explicit User Confirmation
**Date:** 2026-02-10
**What went wrong:** Master could trigger send/re-send to PIC actions with a single click, increasing accidental resubmission risk after rework.
**Why it happened:** Workflow action rendering was generic and action execution was immediate; no role+action-specific confirmation gate existed for this high-impact transition.
**Rule to prevent:**
- Add a confirmation modal for critical transitions that re-enter review cycles (e.g., send/resubmit to PIC).
- Detect confirmation targets by explicit action-key allowlist from backend available-actions, not by status heuristics.
- Keep transition execution path unchanged (`executeTransition`) and preserve backend-driven comment rules (`comment_required`).
**Related docs:** `psc-frontend/src/components/car/car-workflow-actions.tsx`, `Docs/PRD.md` FEAT-CAR-004

---

### [SYNC] User-Scoped Query Keys Are Mandatory For Authenticated Notification Data
**Date:** 2026-02-10
**What went wrong:** Notification badge/list could appear empty right after login and only show data after a full refresh.
**Why it happened:** Notification queries used global query keys and were not tied to auth/recipient identity, so cache from a previous auth context could be reused on first post-login render.
**Rule to prevent:**
- For authenticated user-specific data (notifications, inbox, tasks), include a stable user scope segment in TanStack Query keys (e.g., `office:{employee_id}` / `crew:{crew_id}`).
- Gate query execution on auth readiness (`isInitialized && isAuthenticated`) plus required recipient identifiers.
- For login-sensitive surfaces, force first-mount freshness with `refetchOnMount: 'always'` when appropriate.
**Related docs:** `psc-frontend/src/hooks/use-notifications.ts`, `psc-frontend/src/hooks/use-auth.ts`, `Docs/FRONTEND_GUIDELINES.md`

---

### [REPORT] External PDF Sanitization Must Be Transition-Scoped, Not Global
**Date:** 2026-02-11
**What went wrong:** External-mode sanitization removed internal tokens globally across payload text, which risks mutating legitimate business content outside history/transition fields.
**Why it happened:** Sanitization was implemented as recursive payload string replacement instead of targeting transition-notation sources only.
**Rule to prevent:**
- Sanitize only transition-derived text (e.g., `(STATE_A -> STATE_B)` / `(STATE_A → STATE_B)`) in history/office transition paths.
- Do not globally strip `_REVIEW` / `SUBMITTED_` from all report strings.
- Keep tests scoped to transition-rendered output, not all paragraphs.
**Related docs:** `psc-backend/apps/car/reports.py`, `psc-backend/apps/car/tests.py`

---

### [DB] Model Changes Must Be Followed By Local Migration Apply Before UI Verification
**Date:** 2026-02-11
**What went wrong:** CAR list UI failed with HTTP 500 after code updates because backend schema lacked `inspection.0008_car_initial_action_code`.
**Why it happened:** Code and migration state diverged in local runtime; endpoint query path hit unapplied schema.
**Rule to prevent:**
- After introducing model fields, run and verify app migrations before functional UI checks.
- Use `showmigrations` to confirm target migration is applied.
- If UI suddenly returns 500 after backend model changes, check migration state first.
**Related docs:** `psc-backend/apps/inspection/migrations/0008_car_initial_action_code.py`, `psc-backend/apps/inspection/deficiency_models.py`
