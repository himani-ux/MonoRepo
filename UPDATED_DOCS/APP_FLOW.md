# APP_FLOW.md — Application Flow & Screen Inventory
## Inspection Module — PSC/RS/Audit Close-out System
**Version:** 1.1 | **Baseline Date:** 2026-02-03 | **Later Updates:** 2026-03-26

---

## 1. Route Structure

```
/                           → Redirect to /inspections
/login                      → Login Page
/inspections                → Inspection List (FEAT-INS-010)
/inspections/new            → Create Inspection (FEAT-INS-001)
/inspections/:id            → Inspection Detail (FEAT-INS-011)
/inspections/:id/edit       → Edit Inspection (FEAT-INS-007, FEAT-INS-008)
/inspections/:id/follow-up  → Register Follow-up (FEAT-DEF-002)
/cars                       → CAR List (FEAT-CAR-009)
/cars/:id                   → CAR Detail (FEAT-CAR-010)
/cars/:id/edit              → Edit CAR (FEAT-CAR-002)
/notifications              → Notification Center (FEAT-NOTIF-001)
/settings                   → User Settings
/sync                       → Sync Status (FEAT-SYNC-001)
```

---

### 1.1 Current Route Override (Added Later)

The route block above is the original v1.0 baseline. The live application was changed later and now uses the current route map below.

```
/                           -> Redirect to /dashboard or /cars (permission-based)
/login                      -> Login Page
/dashboard                  -> KPI Dashboard
/inspections                -> Inspection List
/inspections/new            -> Create Inspection
/inspections/:id            -> Inspection Detail
/inspections/:id/edit       -> Edit Inspection
/inspections/:id/follow-up  -> Register Follow-up
/deficiencies               -> Deficiency Workflow Dashboard
/cars                       -> CAR List
/cars/:id                   -> CAR Detail
/cars/:id/edit              -> Edit CAR
/notifications              -> Notification Center
/reports                    -> Reports / DefIntel Workspace
/settings                   -> User Settings
/circular/*                 -> Circular Module
/orb/*                      -> ORB Module
/sync                       -> Sync Status
```

### 1.2 Later-Added Screen Notes

These changes were made later on after the original v1.0 screen inventory:

- `/dashboard` was added as the primary landing page for users with dashboard permission
- `/deficiencies` was added as a dedicated workflow screen for deficiency allocation and review
- `/reports` was expanded into a real DefIntel/OpenSource workspace
- `/settings` now includes company logo management for PDF reports
- `/circular/*` was added as an embedded legacy module inside the shared VIMS shell
- `/orb/*` was added as a hybrid module, with vessel users staying on the legacy ORB route tree and office users using the native approved-entries page
- the shared header now exposes Circular and ORB quick actions only when the current path starts with the corresponding module root
- older v1.0 journey examples that mention legacy CAR states such as `DRAFT` and `PIC_ACCEPTED` should be read as historical baseline text; the live CAR workflow now uses the unified workflow documented in `docs/LATER_CHANGES.md`

### Update (2026-03-26)
This document was reviewed against the current React router in `psc-frontend/src/App.tsx`.

Current implementation notes:

- `GET /` does not always redirect to `/inspections`; authenticated users with dashboard permission are redirected to `/dashboard`, while other authenticated users are redirected to `/cars`
- `/reports` and `/settings` are implemented routes, not placeholders
- `/deficiencies` is a dedicated workflow route backed by a real page component and API hooks
- login success returns to the protected route the user originally attempted, otherwise the app falls back to the default permission-based redirect logic

### 1.3 Shared App Shell (Added Later)

The current post-login UI is a shared shell used by Inspection, Circular, and ORB.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ Header: VIMS logo | Circular actions | ORB actions | Notifications | User   │
├───────────────────────────────────────────────────────────────────────────────┤
│ Sidebar / Mobile Drawer                                                      │
│ ┌ Inspection                                                                 │
│ │ └ PSC                                                                     │
│ │   ├ Dashboard                                                             │
│ │   ├ Inspections                                                           │
│ │   ├ Deficiencies                                                          │
│ │   ├ CARs                                                                  │
│ │   ├ Notifications                                                         │
│ │   ├ Sync                                                                  │
│ │   ├ Reports                                                               │
│ │   └ Settings                                                              │
│ ├ Circular                                                                  │
│ └ ORB                                                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│ Main content area                                                            │
└───────────────────────────────────────────────────────────────────────────────┘
```

**Shell Behavior:**
- the `Inspection` node is the primary navigation group and expands to `PSC` plus the existing module destinations
- `Circular` and `ORB` are separate module links in the same authenticated shell
- the header keeps the global notification bell and user menu on every authenticated screen
- module-specific quick actions appear only when the route starts with `/circular` or `/orb`
- `Inspection` visibility is driven by `form_ids`, while the in-screen actions use `process_ids`
- `Circular` and `ORB` visibility is driven by legacy auth context after the modern login payload is bridged into the legacy store

**Permission View:**
| Module | Screen / Area | `form_ids` | `process_ids` |
|---|---|---|---|
| Inspection | Sidebar, bottom nav, and core PSC workflow | `PSC_F_001` to `PSC_F_008` | `PSC_P_001` to `PSC_P_016` |
| Circular | Office / admin workspace | `PSC_F_009` | `PSC_P_017`, `PSC_P_018`, `PSC_P_019`, `PSC_P_024` |
| Circular | Overlay / modal workspace | `PSC_F_010` | - |
| Circular | Follow-up / approval panel | `PSC_F_011` | `PSC_P_025`, `PSC_P_026`, `PSC_P_027` |
| Circular | Dashboard filters | `PSC_F_012` | `PSC_P_028`, `PSC_P_029` |
| Circular | Notifications workspace | `PSC_F_013` | `PSC_P_030`, `PSC_P_031`, `PSC_P_032`, `PSC_P_033`, `PSC_P_034`, `PSC_P_035`, `PSC_P_036` |
| Circular | Approved notifications library actions | - | `PSC_P_020`, `PSC_P_021`, `PSC_P_022`, `PSC_P_023` |
| ORB | Entry form | `PSC_F_014` | `PSC_P_043` |
| ORB | Draft / table workspace | `PSC_F_015` | `PSC_P_037`, `PSC_P_038` |
| ORB | Pending entries view | `PSC_F_016` | `PSC_P_040`, `PSC_P_041` |
| ORB | Approved entries view | `PSC_F_017` | `PSC_P_042` |
| ORB | Report filter | `PSC_F_018` | `PSC_P_039` |
| ORB | Report view | `PSC_F_019` | - |

---

## 2. Screen Inventory

### 2.1 Authentication

#### SCREEN: Login (`/login`)
**Purpose:** User authentication
**Data Required:** None
**User Roles:** All (unauthenticated)

**Layout:**
```
┌─────────────────────────────────────┐
│           [Company Logo]            │
│                                     │
│    ┌─────────────────────────┐     │
│    │ Email/Username          │     │
│    └─────────────────────────┘     │
│    ┌─────────────────────────┐     │
│    │ Password                │     │
│    └─────────────────────────┘     │
│                                     │
│    [        Login Button       ]    │
│                                     │
│    Forgot Password?                 │
└─────────────────────────────────────┘
```

**Actions:**
| Action | Trigger | Result |
|--------|---------|--------|
| Submit credentials | Click Login | Validate → Success: redirect to the originally requested protected page, otherwise continue to the permission-based default landing route |
| Failed login | Invalid credentials | Show error: "Invalid email or password" |
| Forgot password | Click link | Show password reset flow |

**Error States:**
- Invalid credentials: "Invalid email or password"
- Account locked: "Account locked. Contact administrator."
- Network error: "Unable to connect. Check your connection."

---

### 2.2 Inspection Management

#### SCREEN: Inspection List (`/inspections`)
**Purpose:** View all inspections with filters
**Data Required:** `GET /api/psc/inspections/`
**User Roles:** All authenticated
**PRD Reference:** FEAT-INS-010

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [≡] Inspections                    [🔔] [👤]               │
├─────────────────────────────────────────────────────────────┤
│ Filters: [Type ▼] [Status ▼] [Date Range] [🔍 Search]      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 🚢 MV Example          PSC - INITIAL     15 Jan 2026   ││
│ │ Singapore | TOKYO MOU                                  ││
│ │ Deficiencies: 3 (2 open)        Status: SUBMITTED     ││
│ │ [🔴 DETENTION]                                         ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 🚢 MV Sample           RS                 10 Jan 2026   ││
│ │ Rotterdam | N/A                                        ││
│ │ Deficiencies: 1 (0 open)        Status: DPA_CLOSED    ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ [Load More] or Pagination                                   │
├─────────────────────────────────────────────────────────────┤
│ [+ Create Inspection]                              FAB      │
└─────────────────────────────────────────────────────────────┘
```

**Actions:**
| Action | Trigger | Result |
|--------|---------|--------|
| View detail | Tap inspection card | Navigate to `/inspections/:id` |
| Create new | Tap FAB | Navigate to `/inspections/new` |
| Filter | Change filter | Reload list with filters |
| Search | Enter search term | Filter by vessel name, port |
| Refresh | Pull down (mobile) | Reload data |

**Empty State:**
- **No inspections:** "No inspections recorded yet. Previous inspection records (up to 3 years) will appear here once uploaded." [Create First Inspection]
- **No filter results:** "No inspections found. No inspections match your current filter criteria." [Clear Filters]

**Loading State:**
- Skeleton cards (3-5 placeholders)
- Spinner in filter area during search

**Offline Indicator:**
- Banner: "📴 Offline - Showing cached data"
- Last sync time displayed

---

#### SCREEN: Create Inspection (`/inspections/new`)
**Purpose:** Create new inspection record
**Data Required:** 
- `GET /api/psc/masters/mou/` (MOU list)
- `GET /api/psc/masters/psc-action-codes/` (Action codes)
- `GET /api/psc/masters/psc-def-codes/` (Deficiency codes)
**User Roles:** Vessel Master, Office
**PRD Reference:** FEAT-INS-001, FEAT-INS-003

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [←] New Inspection                              [Save Draft]│
├─────────────────────────────────────────────────────────────┤
│ INSPECTION DETAILS                                          │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Inspection Type *        [PSC           ▼]              ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ PSC Subtype *            [INITIAL       ▼]              ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Inspection Date *        [📅 15 Jan 2026]               ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Port/Place *             [Singapore              ]      ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Country                  [Singapore              ]      ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ MOU                      [TOKYO MOU      ▼]             ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Authority                [MPA Singapore          ]      ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Inspector Name           [John Inspector         ]      ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Report Reference         [PSC-2026-001           ]      ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ [ ] Detention                                           ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ INSPECTION REPORT                                           │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 📄 No report attached                                   ││
│ │ [+ Upload Report]                                      ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ DEFICIENCIES                                                │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ No deficiencies added yet                               ││
│ │ [+ Add Deficiency]                                      ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Cancel]                                    [Create Draft]  │
└─────────────────────────────────────────────────────────────┘
```

**Conditional Fields:**
- PSC Subtype: Only visible when Inspection Type = PSC
- MOU: Only visible when Inspection Type = PSC

**Validation (On Create):**
| Field | Rule | Error Message |
|-------|------|---------------|
| inspection_type | Required | "Inspection type is required" |
| inspection_date | Required, not future | "Inspection date cannot be in the future" |
| port_place | Required | "Port/Place is required" |

**Actions:**
| Action | Trigger | Result |
|--------|---------|--------|
| Create Draft | Click button | Validate → Save → Navigate to `/inspections/:id` |
| Cancel | Click Cancel | Confirm dialog → Navigate back |
| Upload Report | Click upload | Open file picker (PDF, JPG, JPEG; 3MB max) |
| Add Deficiency | Click add | Open deficiency modal |

---

#### SCREEN: Add Deficiency Modal
**Purpose:** Add deficiency to inspection
**Parent:** Create/Edit Inspection
**PRD Reference:** FEAT-INS-003

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Add Deficiency                                        [✕]   │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐│
│ │ DefCode *               [🔍 Search or Select    ▼]      ││
│ │                         10101 - Fire doors              ││
│ │                         10102 - Fire dampers            ││
│ │                         10103 - Fire detection          ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Description *                                           ││
│ │ [Fire damper in engine room found                    ]  ││
│ │ [inoperative during inspection...                    ]  ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Action Code *           [30 - Deficiency rectified  ▼]  ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Target Date             [📅 22 Jan 2026]                ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ⓘ A CAR will be automatically created for this deficiency  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Cancel]                                    [Add Deficiency]│
└─────────────────────────────────────────────────────────────┘
```

**Validation:**
| Field | Rule | Error Message |
|-------|------|---------------|
| def_code | Required | "Deficiency code (DefCode) is required" |
| description | Required | "Description is required" |
| action_code | Required | "Action code is required" |

---

#### SCREEN: Inspection Detail (`/inspections/:id`)
**Purpose:** View complete inspection details
**Data Required:** `GET /api/psc/inspections/:id/`
**User Roles:** All authenticated
**PRD Reference:** FEAT-INS-011

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [←] Inspection Detail                    [⋮ More Actions]   │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐│
│ │ MV Example                              Status: SUBMITTED││
│ │ IMO: 1234567                                            ││
│ │ PSC - INITIAL | 15 Jan 2026 | Singapore                 ││
│ │ TOKYO MOU | MPA Singapore                               ││
│ │ Inspector: John Inspector                               ││
│ │ Report Ref: PSC-2026-001                                ││
│ │ [🔴 DETENTION]                                          ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ INSPECTION REPORT                                           │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 📄 PSC_Report_2026-001.pdf              [View] [📥]     ││
│ │ Uploaded: 15 Jan 2026 by Master                         ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ DEFICIENCIES (3)                                            │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ [10101] Fire dampers                    ActionCode: 30  ││
│ │ Fire damper in engine room found inoperative...         ││
│ │ CAR: PSC-2026-001 | Status: DRAFT                       ││
│ │ Target: 22 Jan 2026                          [View CAR] ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ [10205] Navigation lights               ActionCode: 17  ││
│ │ Port side navigation light defective...                 ││
│ │ CAR: PSC-2026-002 | Status: SUBMITTED                   ││
│ │ Target: 20 Jan 2026                          [View CAR] ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ACTIVITY HISTORY                                            │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 📝 Created by Master - 15 Jan 2026 10:30                ││
│ │ 📄 Report uploaded - 15 Jan 2026 11:00                  ││
│ │ ➕ Deficiency added: 10101 - 15 Jan 2026 11:15          ││
│ │ ➕ Deficiency added: 10205 - 15 Jan 2026 11:20          ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Edit]  [Register Follow-up]  [Submit for Review]           │
└─────────────────────────────────────────────────────────────┘
```

**More Actions Menu (⋮):**
- Edit Inspection (if DRAFT or has permission)
- Delete Inspection (if DRAFT, Vessel Master only)
- Export to PDF
- Register Follow-up (PSC only)

**Conditional Actions by Status:**
| Status | Vessel Master | Office | DPA |
|--------|---------------|--------|-----|
| DRAFT | Edit, Delete, Submit | Edit-assist | - |
| SUBMITTED | - | Edit, PIC Review | - |
| PIC_REVIEWED | - | - | DPA Close |
| DPA_CLOSED | - | - | - |

**Error State (404):**
- "Inspection not found. The inspection may have been deleted or you don't have access."
- [Go Back] button

---

#### SCREEN: Register Follow-up (`/inspections/:id/follow-up`)
**Purpose:** Record PSC follow-up that clears deficiencies
**Data Required:** 
- Parent inspection details
- List of open deficiencies
**User Roles:** Vessel Master only
**PRD Reference:** FEAT-DEF-002

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [←] Register Follow-up                                      │
├─────────────────────────────────────────────────────────────┤
│ Original Inspection: PSC-INITIAL | 15 Jan 2026 | Singapore  │
│                                                             │
│ FOLLOW-UP DETAILS                                           │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Follow-up Date *        [📅 20 Jan 2026]                ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Port                    [Singapore              ]       ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Authority               [MPA Singapore          ]       ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ FOLLOW-UP REPORT                                            │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ [+ Upload Follow-up Report PDF]                         ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ DEFICIENCY STATUS UPDATES                                   │
│ Select deficiencies cleared by this follow-up:              │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ [✓] [10101] Fire dampers                                ││
│ │     Current: 30 → New: [10 - Rectified      ▼]          ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ [ ] [10205] Navigation lights                           ││
│ │     Current: 17 (will remain unchanged)                 ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Cancel]                                [Register Follow-up]│
└─────────────────────────────────────────────────────────────┘
```

---

### 2.3 CAR Management

#### SCREEN: CAR List (`/cars`)
**Purpose:** View all CARs with status tracking
**Data Required:** `GET /api/psc/cars/`
**User Roles:** All authenticated
**PRD Reference:** FEAT-CAR-009

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [≡] CARs                                   [🔔] [👤]        │
├─────────────────────────────────────────────────────────────┤
│ Filters: [Status ▼] [Source ▼] [Vessel ▼] [Overdue ☐]      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ PSC-2026-001                           Status: DRAFT    ││
│ │ [10101] Fire dampers                                    ││
│ │ MV Example | Target: 22 Jan 2026                        ││
│ │ ⚠️ Missing evidence                                     ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ PSC-2026-002                        Status: SUBMITTED   ││
│ │ [10205] Navigation lights                               ││
│ │ MV Example | Target: 20 Jan 2026                        ││
│ │ 🔴 OVERDUE                                              ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ [Load More]                                                 │
└─────────────────────────────────────────────────────────────┘
```

**Visual Indicators:**
- 🔴 OVERDUE: Red text, red left border
- ⚠️ Missing evidence: Warning icon
- Status badges with colors per DESIGN_SYSTEM.md

**Empty State:**
- "No CARs found. CARs are automatically created when deficiencies are added to inspections."

---

#### SCREEN: CAR Detail (`/cars/:id`)
**Purpose:** View and manage CAR
**Data Required:** `GET /api/psc/cars/:id/`
**User Roles:** All authenticated
**PRD Reference:** FEAT-CAR-010

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [←] CAR Detail                           [⋮ More Actions]   │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐│
│ │ PSC-2026-001                          Status: DRAFT     ││
│ │ Created: 15 Jan 2026                                    ││
│ │ Target: 22 Jan 2026                                     ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ─── DEFICIENCY ───────────────────────────────────────────  │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ DefCode: [10101] Fire dampers                           ││
│ │ Action Code: 30 - Deficiency rectified                  ││
│ │                                                         ││
│ │ Fire damper in engine room compartment 3 found          ││
│ │ inoperative during inspection. Damper blade stuck in    ││
│ │ open position, fusible link intact.                     ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ─── ROOT CAUSE ANALYSIS ──────────────────────────────────  │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ CLC Codes:                                              ││
│ │ • IC-02: Inadequate maintenance                         ││
│ │ • RJ-05: Inadequate supervision                         ││
│ │                                                         ││
│ │ Summary:                                                ││
│ │ The fire damper failed due to lack of regular           ││
│ │ maintenance checks. The planned maintenance system      ││
│ │ did not include quarterly operational tests...          ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ─── CORRECTIVE ACTIONS ───────────────────────────────────  │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ IMMEDIATE                                               ││
│ │ ┌─────────────────────────────────────────────────────┐││
│ ││ 1. Replace fire damper actuator                      │││
│ ││    Owner: Chief Engineer | Due: 18 Jan 2026          │││
│ ││    Status: ✅ Completed                              │││
│ │└─────────────────────────────────────────────────────┘││
│ │                                                         ││
│ │ LONG-TERM                                               ││
│ │ ┌─────────────────────────────────────────────────────┐││
│ ││ 2. Update PMS to include quarterly damper checks     │││
│ ││    Owner: 2nd Engineer | Due: 30 Jan 2026            │││
│ ││    Status: ⏳ Pending                                │││
│ │└─────────────────────────────────────────────────────┘││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ─── EVIDENCE ─────────────────────────────────────────────  │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ BEFORE (1)                                              ││
│ │ ┌────────┐                                              ││
│ │ │ 📷     │ Damper stuck open - 15 Jan 2026             ││
│ │ │        │ "Fire damper before repair showing..."      ││
│ │ └────────┘                                              ││
│ │                                                         ││
│ │ AFTER (1)                                               ││
│ │ ┌────────┐                                              ││
│ │ │ 📷     │ Damper operational - 18 Jan 2026            ││
│ │ │        │ "Fire damper after actuator replacement..." ││
│ │ └────────┘                                              ││
│ │                                                         ││
│ │ [+ Upload Evidence]                                     ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ─── ACTIVITY HISTORY ─────────────────────────────────────  │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 📝 CAR auto-created - 15 Jan 2026 11:15                 ││
│ │ 📷 BEFORE evidence uploaded - 15 Jan 2026 14:00         ││
│ │ ✅ Action completed: Replace actuator - 18 Jan 2026     ││
│ │ 📷 AFTER evidence uploaded - 18 Jan 2026 16:30          ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Edit CAR]                              [Submit for Review] │
└─────────────────────────────────────────────────────────────┘
```

**Conditional Actions by Status (Current Unified Workflow, Added Later):**
| Status | Vessel-side | Office PIC/Reviewer | DPA |
|--------|-------------|---------------------|-----|
| ALLOTTED | Edit, Start Work | - | - |
| IN_PROGRESS | Edit, Mark Completed | - | - |
| PENDING_CE_REVIEW | Approve & Forward, Return for Rework | - | - |
| PENDING_MASTER_REVIEW | Submit to PIC, Return for Rework | - | - |
| SUBMITTED_TO_PIC | - | Start Review, Request Rework | - |
| PIC_REVIEW | - | Submit to DPA, Request Rework | - |
| SUBMITTED_TO_DPA | - | - | Close CAR, Request Rework |
| CLOSED | - | - | Reopen |

**Office/DPA Only Section (Audit Log):**
```
─── AUDIT LOG (Office View Only) ───────────────────────────
┌─────────────────────────────────────────────────────────┐
│ 🔧 Field changed: root_cause_summary                    │
│    By: Office User | 17 Jan 2026 09:00                  │
│    Old: "Damper failed..."                              │
│    New: "The fire damper failed due to..."              │
└─────────────────────────────────────────────────────────┘
```

---

#### SCREEN: Edit CAR (`/cars/:id/edit`)
**Purpose:** Edit CAR form
**Data Required:** 
- CAR details
- `GET /api/psc/masters/clc/` (CLC codes)
- `GET /api/psc/masters/pic/` (PIC codes)
**User Roles:** Vessel Master (DRAFT/REWORK), Office (edit-assist)
**PRD Reference:** FEAT-CAR-002

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [←] Edit CAR: PSC-2026-001                     [Save Draft] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ─── DEFICIENCY (Read-only) ───────────────────────────────  │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ DefCode: [10101] Fire dampers                           ││
│ │ Description: Fire damper in engine room...              ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ─── ROOT CAUSE ANALYSIS ──────────────────────────────────  │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ CLC Codes * (Select one or more)                        ││
│ │ [🔍 Search CLC codes...]                                ││
│ │ Selected:                                               ││
│ │ [IC-02 Inadequate maintenance ✕]                        ││
│ │ [RJ-05 Inadequate supervision ✕]                        ││
│ │                                                         ││
│ │ OR Custom Cause:                                        ││
│ │ [                                               ]       ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Root Cause Summary * (min 50 characters)                ││
│ │ [The fire damper failed due to lack of regular       ]  ││
│ │ [maintenance checks. The planned maintenance system  ]  ││
│ │ [did not include quarterly operational tests...      ]  ││
│ │                                                  125/50 ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ─── CORRECTIVE ACTIONS ───────────────────────────────────  │
│                                                             │
│ IMMEDIATE ACTIONS *                                         │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 1. [Replace fire damper actuator                     ]  ││
│ │    Owner: [Chief Engineer  ▼]  Due: [📅 18 Jan 2026]   ││
│ │    [✓] Completed  Remarks: [Actuator replaced, tested] ││
│ │                                                   [🗑️] ││
│ └─────────────────────────────────────────────────────────┘│
│ [+ Add Immediate Action]                                    │
│                                                             │
│ LONG-TERM ACTIONS *                                         │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 1. [Update PMS to include quarterly damper checks    ]  ││
│ │    Owner: [2nd Engineer    ▼]  Due: [📅 30 Jan 2026]   ││
│ │    [ ] Completed                                        ││
│ │                                                   [🗑️] ││
│ └─────────────────────────────────────────────────────────┘│
│ [+ Add Long-term Action]                                    │
│                                                             │
│ ─── TARGET DATE ──────────────────────────────────────────  │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Target Date              [📅 22 Jan 2026]               ││
│ │ Revised Target Date      [📅 __ ___ ____]               ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ─── EVIDENCE ─────────────────────────────────────────────  │
│ BEFORE Evidence * (at least 1 required)                     │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ ┌────────┐                                              ││
│ │ │ 📷     │ Damper stuck open              [🗑️]         ││
│ │ └────────┘                                              ││
│ │ [+ Upload BEFORE Evidence]                              ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ AFTER Evidence * (at least 1 required)                      │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ ┌────────┐                                              ││
│ │ │ 📷     │ Damper operational             [🗑️]         ││
│ │ └────────┘                                              ││
│ │ [+ Upload AFTER Evidence]                               ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Cancel]              [Save Draft]         [Submit CAR]     │
└─────────────────────────────────────────────────────────────┘
```

**Validation (On Submit):**
| Field | Rule | Error Message |
|-------|------|---------------|
| root_cause_summary | Min 50 chars | "Root cause summary is required (minimum 50 characters)" |
| clc_codes OR custom_cause | At least 1 | "At least one root cause is required" |
| immediate_actions | At least 1 | "At least one immediate corrective action is required" |
| longterm_actions | At least 1 | "At least one long-term preventive action is required" |
| action.owner | Required each | "All corrective actions must have an assigned owner" |
| action.due_date | Required each | "All corrective actions must have due dates" |
| before_evidence | At least 1 | "At least one BEFORE evidence is required" |
| after_evidence | At least 1 | "At least one AFTER evidence is required" |

---

#### SCREEN: Upload Evidence Modal
**Purpose:** Upload evidence attachment
**Parent:** CAR Detail, Edit CAR
**PRD Reference:** FEAT-CAR-003

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Upload Evidence                                       [✕]   │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Evidence Type *          [BEFORE         ▼]             ││
│ │                          BEFORE                         ││
│ │                          AFTER                          ││
│ │                          OTHER                          ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │                                                         ││
│ │     📤 Drag & drop file here or click to browse        ││
│ │                                                         ││
│ │     Accepted: PDF, JPG, JPEG (max 3MB)                  ││
│ │                                                         ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ Selected: damper_photo.jpg (1.2MB)                          │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Description *                                           ││
│ │ [Fire damper after actuator replacement, showing     ]  ││
│ │ [damper blade in closed position...                  ]  ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Cancel]                                           [Upload] │
└─────────────────────────────────────────────────────────────┘
```

**Validation:**
| Field | Rule | Error Message |
|-------|------|---------------|
| file | Required | "Please select a file" |
| file.type | PDF, JPG, JPEG | "Only PDF and JPG/JPEG files are allowed" |
| file.size | Max 3MB | "File size must not exceed 3MB" |
| description | Required | "Evidence description is required" |

---

### 2.4 Office Review Screens

#### SCREEN: PIC Accept/Rework Modal
**Purpose:** Office action on submitted CAR
**Parent:** CAR Detail
**PRD Reference:** FEAT-CAR-005, FEAT-CAR-006

**Accept Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Accept CAR                                            [✕]   │
├─────────────────────────────────────────────────────────────┤
│ You are accepting CAR: PSC-2026-001                         │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ PIC Comments * (mandatory)                              ││
│ │ [Root cause analysis is thorough and corrective      ]  ││
│ │ [actions are appropriate. Recommend for DPA closure. ]  ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Cancel]                                          [Accept]  │
└─────────────────────────────────────────────────────────────┘
```

**Rework Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Request Rework                                        [✕]   │
├─────────────────────────────────────────────────────────────┤
│ You are requesting rework for CAR: PSC-2026-001             │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Rework Reason * (minimum 20 characters)                 ││
│ │ [Evidence photos are unclear. Please provide higher  ]  ││
│ │ [resolution images showing the repair clearly.       ]  ││
│ │                                                   65/20 ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ ⚠️ The CAR will be returned to DRAFT status for vessel     │
│    to revise and resubmit.                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Cancel]                                  [Request Rework]  │
└─────────────────────────────────────────────────────────────┘
```

---

#### SCREEN: DPA Close Modal
**Purpose:** DPA final closure of CAR
**Parent:** CAR Detail
**PRD Reference:** FEAT-CAR-007

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ DPA Close CAR                                         [✕]   │
├─────────────────────────────────────────────────────────────┤
│ You are closing CAR: PSC-2026-001                           │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ DPA Comments * (mandatory)                              ││
│ │ [CAR satisfactorily closed. Corrective and preventive]  ││
│ │ [actions have been verified and documented properly. ]  ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ [ ] Schedule Physical Verification                          │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Cancel]                                       [Close CAR]  │
└─────────────────────────────────────────────────────────────┘
```

---

### 2.5 Sync & Offline

#### SCREEN: Sync Status (`/sync`)
**Purpose:** View sync status and manage offline data
**Data Required:** Local IndexedDB state
**User Roles:** All vessel users
**PRD Reference:** FEAT-SYNC-001

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [←] Sync Status                                             │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Connection: 🟢 Online                                   ││
│ │ Last Sync: 15 Jan 2026 14:30                            ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ STORAGE                                                     │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ ████████████████████░░░░░░░░░░ 98 MB / 150 MB          ││
│ │                                                         ││
│ │ Inspections:     1 MB                                   ││
│ │ Deficiencies:    500 KB                                 ││
│ │ CARs:            2 MB                                   ││
│ │ Attachments:     92 MB                                  ││
│ │ Masters:         2 MB                                   ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ PENDING CHANGES                                             │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 📤 2 changes waiting to sync                            ││
│ │ • CAR PSC-2026-001 updated                              ││
│ │ • Evidence uploaded (pending)                           ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ FAILED UPLOADS                                              │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ ⚠️ 1 upload failed                                      ││
│ │ • damper_photo.jpg - Network error       [Retry]        ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ CONFLICTS                                                   │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 🔴 1 conflict detected                                  ││
│ │ • CAR PSC-2026-002 - Office made changes                ││
│ │   "Waiting for office to resolve"                       ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Sync Now]                              [Clear Old Data]    │
└─────────────────────────────────────────────────────────────┘
```

**Empty States:**
- **No pending changes:** "All changes synced"
- **No failed uploads:** (Section hidden)
- **No conflicts:** (Section hidden)

**Storage Warning (< 10MB):**
```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Storage nearly full (8 MB remaining)                     │
│ Please connect to internet and sync to free up space.       │
│ Old attachments (>1 year) will be auto-purged.              │
└─────────────────────────────────────────────────────────────┘
```

---

### 2.6 Notifications

#### SCREEN: Notification Center (`/notifications`)
**Purpose:** View all notifications
**Data Required:** Notification list from server/local
**User Roles:** All authenticated
**PRD Reference:** FEAT-NOTIF-001

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [←] Notifications                          [Mark All Read]  │
├─────────────────────────────────────────────────────────────┤
│ TODAY                                                       │
│ ┌─────────────────────────────────────────────────────────┐│
│ │ 🔵 CAR PSC-2026-001 created for deficiency 10101        ││
│ │    15 Jan 2026 11:15                                    ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─────────────────────────────────────────────────────────┐│
│ │    CAR PSC-2026-002 submitted by MV Example             ││
│ │    15 Jan 2026 14:00                                    ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ YESTERDAY                                                   │
│ ┌─────────────────────────────────────────────────────────┐│
│ │    PIC accepted CAR PSC-2025-045                        ││
│ │    14 Jan 2026 09:30                                    ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ EARLIER                                                     │
│ ...                                                         │
└─────────────────────────────────────────────────────────────┘
```

**Unread indicator:** 🔵 blue dot

---

### 2.7 Later-Added Operational Screens

#### SCREEN: Dashboard (`/dashboard`)
**Purpose:** KPI landing screen for office users and vessel users with dashboard permission
**Data Required:** `GET /api/psc/dashboard/`
**User Roles:** Permission-based (`PSC_P_001`)

**Current Behavior:**
- shows inspection volume, open CARs, overdue CARs, detention count, top deficiency codes, missing evidence count, overdue actions, CAR status distribution, and monthly deficiency trend
- office users can drill down by vessel; vessel users are automatically scoped to their own vessel
- the current frontend includes a repeat-deficiencies card, but when the backend does not provide repeat-deficiency data the page shows a clear "Not available" state

#### SCREEN: Deficiency Workflow (`/deficiencies`)
**Purpose:** Dedicated workflow dashboard for allocation and review of deficiencies/CARs
**Data Required:** `GET /api/psc/deficiencies/`
**User Roles:** Permission-based (`PSC_P_007`)

**Current Behavior:**
- filter by CAR workflow status
- optional "Awaiting Review" toggle
- open deficiency detail dialog from the list
- supports office vessel filtering through query params when available

#### SCREEN: Reports / DefIntel Workspace (`/reports`)
**Purpose:** Reporting workspace for DefIntel/OpenSource tooling
**Data Required:**
- `POST /api/psc/reports/opensource/import/`
- `POST /api/psc/reports/vessel-prep/preview/`
- `POST /api/psc/reports/vessel-prep/export/`
- `GET /api/psc/reports/defintel/predict-defcodes/`
**User Roles:** Permission-based (`PSC_P_015`), with OpenSource import restricted to office users

**Current Behavior:**
- import monthly OpenSource Excel workbooks
- preview/export vessel preparation checklist
- run deficiency-code prediction by Port or MOU
- disables server-dependent actions when offline or when the API is unreachable

#### SCREEN: Settings (`/settings`)
**Purpose:** Company branding configuration for generated PDFs
**Data Required:** `GET /api/psc/auth/company-logo/`, `POST /api/psc/auth/company-logo/`
**User Roles:** Permission-based (`PSC_P_016`)

**Current Behavior:**
- any office user can upload or replace the company logo
- vessel users have read-only visibility of logo status
- accepted formats are PNG/JPG up to 2 MB

## 2.8 Circular Module

#### SCREEN: Circular Shell (`/circular/*`)
**Purpose:** Legacy Circular workflow embedded in the shared VIMS shell
**Data Required:** Legacy Circular routes/services plus bridged auth state
**User Roles:** Office, Ship

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [≡] VIMS                      [Circular Actions] [🔔] [👤]  │
├─────────────────────────────────────────────────────────────┤
│ Sidebar / Drawer                                            │
│ ┌ Inspection                                               │
│ │ └ PSC                                                    │
│ │   ├ Dashboard                                            │
│ │   ├ Inspections                                          │
│ │   ├ Deficiencies                                         │
│ │   ├ CARs                                                 │
│ │   ├ Notifications                                        │
│ │   ├ Sync                                                 │
│ │   ├ Reports                                              │
│ │   └ Settings                                             │
│ ├ Circular                                                 │
│ └ ORB                                                      │
├─────────────────────────────────────────────────────────────┤
│ Main content area                                           │
└─────────────────────────────────────────────────────────────┘
```

**Route Map:**
| Route | Purpose | Role |
|------|---------|------|
| `/circular` | Role-based entry redirect | Office / Ship |
| `/circular/dashboard` | Circular office dashboard | Office |
| `/circular/office` | Circular office user panel | Office |
| `/circular/admin` | Circular admin panel | Office admin |
| `/circular/admin/all-notifications` | Admin-wide notification queue | Office admin |
| `/circular/user/notifications` | User notification inbox | Office |
| `/circular/user/drafts` | Draft notification workspace | Office |
| `/circular/approved-library` | Approved notification library | Shared |
| `/circular/ship-dashboard` | Ship-side dashboard | Ship |
| `/circular/pdf-viewer` | PDF review and acknowledgment flow | Shared |

**Current Behavior:**
- `LegacyBasicProvider` maps modern vessel users to the legacy `ship` user type
- the default route sends office users to `dashboard`, ship users to `ship-dashboard`, and unknown users to `role-landing`
- Circular keeps its legacy document and notification flows inside the modern shell without altering Inspection screens

#### SCREEN: Circular Office Panel (`/circular/office`)
**Purpose:** Create and manage circular notifications
**Data Required:** Legacy circular master data, vessel/rank selectors, notification metadata
**User Roles:** Office

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [←] Circular Office Panel                  [Submit] [Save] │
├─────────────────────────────────────────────────────────────┤
│ CORE DATA                                                   │
│ ┌ Document Type ▼ ┐ ┌ Department ▼ ┐ ┌ Priority ▼ ┐        │
│ ┌ Subject ───────────────────────────────────────────────┐ │
│ ┌ Body / Notification text ──────────────────────────────┐ │
│ ┌ Attachments / Files ──────────────────────────────────┐ │
│                                                             │
│ RECIPIENTS                                                  │
│ ┌ Vessel selector ───────────────────────────────────────┐ │
│ ┌ Rank selector / grouped ranks ─────────────────────────┐ │
│                                                             │
│ ACTIONS                                                     │
│ [Send] [Save Draft] [View Pending] [View Submitted]         │
└─────────────────────────────────────────────────────────────┘
```

**Current Behavior:**
- office users can compose notifications, target vessels/ranks, and work with draft and submitted request states
- admin users can access the broader notification administration route

#### SCREEN: Circular PDF Viewer (`/circular/pdf-viewer`)
**Purpose:** Review a circular attachment and acknowledge it after reading
**Data Required:** `notificationId` query param, crew identity, PDF attachment URL
**User Roles:** Shared

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [Review Document]                         [Download PDF]    │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐│
│ │ Scrollable PDF canvas / rendered pages                 ││
│ │                                                         ││
│ │ Page 1 ... Page N                                      ││
│ └─────────────────────────────────────────────────────────┘│
│                                                             │
│ [Acknowledge] appears after scrolling to the bottom         │
└─────────────────────────────────────────────────────────────┘
```

**Current Behavior:**
- the document URL is resolved from the backend using the notification and crew identity
- the acknowledgment action appears only after the viewer reaches the bottom of the document
- the page supports direct PDF download before acknowledgment

## 2.9 ORB Module

#### SCREEN: ORB Shell (`/orb/*`)
**Purpose:** Integrated ORB workflow and report archive
**Data Required:** Legacy ORB routes/services for vessel users, native approved-entries page for office users
**User Roles:** Vessel, Office

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [≡] VIMS                      [ORB Actions] [🔔] [👤]      │
├─────────────────────────────────────────────────────────────┤
│ Sidebar / Drawer                                            │
│ ┌ Inspection                                               │
│ │ └ PSC                                                    │
│ │   ├ Dashboard                                            │
│ │   ├ Inspections                                          │
│ │   ├ Deficiencies                                         │
│ │   ├ CARs                                                 │
│ │   ├ Notifications                                        │
│ │   ├ Sync                                                 │
│ │   ├ Reports                                              │
│ │   └ Settings                                             │
│ ├ Circular                                                 │
│ └ ORB                                                      │
├─────────────────────────────────────────────────────────────┤
│ Main content area                                           │
└─────────────────────────────────────────────────────────────┘
```

**Route Map:**
| Route | Purpose | Role |
|------|---------|------|
| `/orb` | Role-based entry redirect | Vessel / Office |
| `/orb/dashboard` | Legacy ORB operational dashboard | Vessel |
| `/orb/all-entries` | All non-deleted ORB entries | Vessel |
| `/orb/approved-entries` | Approved entry table | Vessel |
| `/orb/rejected-entries` | Rejected entry table | Vessel |
| `/orb/deleted-entries` | Deleted entry table | Vessel |
| `/orb/pdf-archive` | Paginated PDF archive | Vessel |
| `/orb/orb-guidelines` | ORB guidance documents | Vessel |

**Current Behavior:**
- vessel users stay on the legacy ORB route tree
- office users are redirected to the native `e-ORB` approved-entries page
- the shared ORB header exposes Approved, Rejected, Deleted, PDFs, and Guidelines shortcuts only while the route starts with `/orb`

#### SCREEN: ORB Vessel Dashboard (`/orb/dashboard`)
**Purpose:** Vessel-side ORB workspace for drafting, reviewing, and approving entries
**Data Required:** ORB operations, codes, tanks, latest entry date, vessel list
**User Roles:** Vessel

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [ORB Dashboard]                                             │
├─────────────────────────────────────────────────────────────┤
│ ENTRY FORM                                                  │
│ ┌ Code ▼ ┐ ┌ Vessel ▼ ┐ ┌ Tank ▼ ┐                          │
│ ┌ Details / operation fields ─────────────────────────────┐ │
│ ┌ Date / time / position inputs ─────────────────────────┐ │
│                                                             │
│ TABLE / DRAFTS                                              │
│ ┌ Rows of draft entries with edit/delete actions          ┐ │
│                                                             │
│ PENDING / APPROVED PANELS                                   │
│ ┌ Pending Entries Card ┐ ┌ Approved Entries Card          ┐ │
│ ┌ Report Filter        ┐ ┌ Report View                    ┐ │
└─────────────────────────────────────────────────────────────┘
```

**Current Behavior:**
- the dashboard combines entry creation, draft editing, approval workflow, and report generation views
- permissions determine which cards, actions, and tables are visible

#### SCREEN: ORB Approved Entries (`/orb/approved-entries`)
**Purpose:** View approved vessel ORB entries
**Data Required:** Approved entries API plus vessel context
**User Roles:** Vessel

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Approved ORB Entries                                        │
├─────────────────────────────────────────────────────────────┤
│ Vessel: MV Example        [Refresh]                         │
├─────────────────────────────────────────────────────────────┤
│ ┌ Date ┐ ┌ Code ┐ ┌ Item No. ┐ ┌ Record of operations... ┐ │
│ │ rows split line-by-line for review and traceability      │ │
└─────────────────────────────────────────────────────────────┘
```

**Current Behavior:**
- each approved record is expanded into line-level rows so the item numbering remains traceable
- the table supports refresh without losing the current vessel context

#### SCREEN: ORB Office e-ORB (`/orb`)
**Purpose:** Office-approved entries workspace for fleet-wide review
**Data Required:** Vessel list, approved entries list, date filter, code filter
**User Roles:** Office

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ [e-ORB]                      Office view of approved ORB   │
├─────────────────────────────────────────────────────────────┤
│ Filters: [From date] [To date] [Code ▼] [Load]              │
├─────────────────────────────────────────────────────────────┤
│ Vessel selector                                             │
│ ┌ Approved ORB entry table with parsed line-item rows      │
│ └ Empty state / loading skeleton                            │
└─────────────────────────────────────────────────────────────┘
```

**Current Behavior:**
- office users can switch vessels and filter by date range or code
- the page renders the same line-splitting logic as the vessel approved view, but across the fleet

#### SCREEN: ORB PDF Archive (`/orb/pdf-archive`)
**Purpose:** Browse downloadable ORB PDFs
**Data Required:** PDF archive API and vessel context
**User Roles:** Vessel

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ PDF Archive                                                 │
├─────────────────────────────────────────────────────────────┤
│ Vessel: MV Example                                          │
│ ┌ Title ┐ ┌ Description ┐ ┌ Created By ┐ ┌ Created At ┐     │
│ ┌ Download buttons per row                                  │
│ [Previous]  Page X of Y  [Next]                             │
└─────────────────────────────────────────────────────────────┘
```

#### SCREEN: ORB Guidelines (`/orb/orb-guidelines`)
**Purpose:** Show the correct-entry and software guideline documents
**Data Required:** Static guideline PDFs
**User Roles:** Vessel

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Guidelines                                                  │
├─────────────────────────────────────────────────────────────┤
│ [ORB Correct Entries Guidelines]                            │
│ [Software Guidelines]                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Navigation Structure

Later navigation behavior added after the original baseline:

- users with dashboard permission now land on `/dashboard`; others land on `/cars`
- navigation visibility is permission-driven via form/process IDs
- `/deficiencies` and `/reports` are not placeholder routes; they are implemented screens in the current frontend
- `/circular` and `/orb` are now first-class authenticated module roots inside the same shell as Inspection
- module-specific action buttons are rendered in the shared header only when the current path belongs to that module

### 3.1 Main Navigation (Sidebar/Bottom Tab)

**Shared Shell Navigation:**
```
┌─────────────────────────────────────┐
│ Inspection ▾                         │
│   PSC ▾                              │
│     Dashboard                        │
│     Inspections                      │
│     Deficiencies                     │
│     CARs                             │
│     Notifications                    │
│     Sync                             │
│     Reports                          │
│     Settings                         │
│ Circular                             │
│ ORB                                  │
└─────────────────────────────────────┘
```

Navigation notes:

- `Inspection` is the primary group in the authenticated shell
- `PSC` opens automatically when any PSC route is active
- `Circular` and `ORB` are sibling module roots and remain visible in the same sidebar tree
- the mobile bottom nav continues to expose the core Inspection workflow destinations only

### 3.2 User Journeys

#### Journey 1: Vessel Master Creates Inspection with Deficiencies
```
Login → Inspection List → [+ Create] → Create Inspection Form
    → Fill details → [Add Deficiency] → Deficiency Modal → Save
    → [Upload Report] → File picker → Upload
    → [Submit] → Inspection Detail (SUBMITTED)
```

#### Journey 2: Vessel Master Completes CAR
```
CAR List → Select CAR → CAR Detail → [Edit CAR]
    → Fill root cause → Add CLC codes
    → Add immediate action → Add long-term action
    → [Upload BEFORE evidence] → Upload modal
    → [Upload AFTER evidence] → Upload modal
    → [Submit CAR] → CAR Detail (SUBMITTED)
```

#### Journey 3: Office PIC Reviews CAR
```
CAR List (filter: SUBMITTED) → Select CAR → CAR Detail
    → Review details → [Accept] → Accept modal → Enter comments
    → [Accept] → CAR Detail (PIC_ACCEPTED)
```

#### Journey 4: DPA Closes CAR
```
CAR List (filter: PIC_ACCEPTED) → Select CAR → CAR Detail
    → Review details → [Close CAR] → Close modal → Enter comments
    → [Close CAR] → CAR Detail (DPA_CLOSED)
```

#### Journey 5: Vessel Master Registers PSC Follow-up
```
Inspection List → Select PSC Inspection → Inspection Detail
    → [Register Follow-up] → Follow-up Form
    → Enter follow-up details → Select cleared deficiencies
    → [Register Follow-up] → Inspection Detail (follow-up linked)
```

#### Journey 6: Office User Opens Circular
```
Login → Shared Shell → Sidebar: Circular → /circular
    → Role-based redirect → Circular Dashboard or Ship Dashboard
    → Open Office Panel / Notifications / Drafts / PDF Viewer
```

#### Journey 7: Ship User Uses Circular PDF Viewer
```
Login → Shared Shell → Sidebar: Circular → /circular/ship-dashboard
    → Open notification → /circular/pdf-viewer?notificationId=...
    → Read document → Scroll to bottom → Acknowledge
```

#### Journey 8: Vessel User Works in ORB
```
Login → Shared Shell → Sidebar: ORB → /orb
    → Dashboard → Entry Form / Draft Table / Pending / Approved / Reports
    → Review entries → Approved / Rejected / Deleted / PDF Archive
```

#### Journey 9: Office User Reviews e-ORB Entries
```
Login → Shared Shell → Sidebar: ORB → native office approved-entries page
    → Select vessel → Apply date/code filters
    → Review parsed line-item table → Refresh or change vessel
```

---

Note on later workflow changes:

- the Journey 2-4 CAR examples above are the original v1.0 flow snapshots
- the live CAR flow now uses `ALLOTTED -> IN_PROGRESS -> PENDING_CE_REVIEW -> PENDING_MASTER_REVIEW -> SUBMITTED_TO_PIC -> PIC_REVIEW -> SUBMITTED_TO_DPA -> CLOSED`
- rework and reopen actions send the CAR back into the vessel-side review path instead of the legacy `PIC_ACCEPTED` / `DPA_CLOSED` states
- the live implementation now uses the unified CAR workflow documented in `docs/LATER_CHANGES.md`
- the current operational statuses are `ALLOTTED`, `IN_PROGRESS`, `PENDING_CE_REVIEW`, `PENDING_MASTER_REVIEW`, `SUBMITTED_TO_PIC`, `PIC_REVIEW`, `SUBMITTED_TO_DPA`, and `CLOSED`

## 4. Document References

| Document | Reference |
|----------|-----------|
| PRD.md | Feature IDs (FEAT-*) for each screen |
| DESIGN_SYSTEM.md | Colors, typography, spacing tokens |
| FRONTEND_GUIDELINES.md | Component implementation details |
| BACKEND_STRUCTURE.md | API endpoint contracts |
| VALIDATION_RULES.md | Field validation rules |
| TECH_STACK.md | Package versions and dependencies |

---

**Document Control:**
- Created: 2026-02-03
- Updated: 2026-03-26
- Author: System Generated
