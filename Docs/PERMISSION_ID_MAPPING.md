# Permission ID Mapping

This document records every `form_id` and `process_id` used by the current repo for Inspection, Circular, and ORB.

## 1. What the Prefixes Mean

- `PSC_F_` means `PSC` form permission.
- `PSC_P_` means `PSC` process permission.
- `form_id` gates access to a screen, section, or feature area.
- `process_id` gates an action inside that area.

Legacy IDs also exist in the repo:

- `F_###` normalizes to `PSC_F_###`
- `P_###` normalizes to `PSC_P_###`

That normalization happens in the frontend auth helpers before permission checks.

## 2. Where Permissions Are Stored

The shared permission source is the unmanaged SQL table `dbo.msc_profiles`.

Database columns used for permissions:

- `profile_id`
- `profile_name`
- `work_side`
- `form_ids`
- `process_ids`

Storage format:

- `form_ids` and `process_ids` are stored as text columns containing JSON arrays in the live export, for example `["PSC_F_001","PSC_F_002"]`.
- The backend parses them with `parse_id_list()`, which accepts JSON arrays first and falls back to comma-separated strings.
- The Django model is unmanaged and mapped directly to `msc_profiles`.

Auth resolution paths:

- Office users: `mapping_role_user -> master_role -> msc_profiles`
- Vessel users: `master_applied_rank.rank_name -> msc_profiles`
- Global reviewer mapping: `mapping_role_user.role_id -> msc_profiles.profile_id -> Mapping_CrewAssReviewers`
- Fleet-wide read-only scope exception: `Chief Accounting Officer` keeps its own profile name but receives `has_global_vessel_access = true` so read dashboards/lists are not vessel-filtered.

## 3. Full ID Catalog

### 3.1 Form IDs

| Form ID | Module | Meaning |
|---|---|---|
| `PSC_F_001` | Inspection | Dashboard |
| `PSC_F_002` | Inspection | Inspections |
| `PSC_F_003` | Inspection | Deficiencies |
| `PSC_F_004` | Inspection | CARs |
| `PSC_F_005` | Inspection | Notifications |
| `PSC_F_006` | Inspection | Sync |
| `PSC_F_007` | Inspection | Reports |
| `PSC_F_008` | Inspection | Settings |
| `PSC_F_009` | Circular | Office/admin workspace |
| `PSC_F_010` | Circular | Overlay/modal workspace |
| `PSC_F_011` | Circular | Follow-up / approval panel |
| `PSC_F_012` | Circular | Filters |
| `PSC_F_013` | Circular | Notifications |
| `PSC_F_014` | ORB | Entry form |
| `PSC_F_015` | ORB | Table / drafts |
| `PSC_F_016` | ORB | Pending entries |
| `PSC_F_017` | ORB | Approved entries |
| `PSC_F_018` | ORB | Report filter |
| `PSC_F_019` | ORB | Report view |

### 3.2 Process IDs

| Process ID | Module | Meaning |
|---|---|---|
| `PSC_P_001` | Inspection | View dashboard |
| `PSC_P_002` | Inspection | View inspections |
| `PSC_P_003` | Inspection | Create inspection |
| `PSC_P_004` | Inspection | View inspection detail |
| `PSC_P_005` | Inspection | Edit inspection |
| `PSC_P_006` | Inspection | Submit follow up |
| `PSC_P_007` | Inspection | View deficiencies |
| `PSC_P_008` | Inspection | Allocate deficiency |
| `PSC_P_009` | Inspection | View CARs |
| `PSC_P_010` | Inspection | Edit CAR |
| `PSC_P_011` | Inspection | CAR workflow |
| `PSC_P_012` | Inspection | View notifications |
| `PSC_P_013` | Inspection | Manage notifications |
| `PSC_P_014` | Inspection | View sync |
| `PSC_P_015` | Inspection | View reports |
| `PSC_P_016` | Inspection | View settings |
| `PSC_P_017` | Circular | Save draft |
| `PSC_P_018` | Circular | Submit for approval |
| `PSC_P_019` | Circular | View pending requests |
| `PSC_P_020` | Circular | View approved notification |
| `PSC_P_021` | Circular | Download approved PDF |
| `PSC_P_022` | Circular | Delete approved notification |
| `PSC_P_023` | Circular | Download approved attachment |
| `PSC_P_024` | Circular | Publish |
| `PSC_P_025` | Circular | View pending request |
| `PSC_P_026` | Circular | Approve |
| `PSC_P_027` | Circular | Reject |
| `PSC_P_028` | Circular | View filters |
| `PSC_P_029` | Circular | Download PDF |
| `PSC_P_030` | Circular | View list |
| `PSC_P_031` | Circular | View detail |
| `PSC_P_032` | Circular | Acknowledge |
| `PSC_P_033` | Circular | View crew status |
| `PSC_P_034` | Circular | Remind crew |
| `PSC_P_035` | Circular | Download notification PDF |
| `PSC_P_036` | Circular | Access PDF viewer |
| `PSC_P_037` | ORB | Edit draft |
| `PSC_P_038` | ORB | Delete draft |
| `PSC_P_039` | ORB | Filter reports |
| `PSC_P_040` | ORB | Approve entry |
| `PSC_P_041` | ORB | Reject entry |
| `PSC_P_042` | ORB | Save approved entry PDF |
| `PSC_P_043` | ORB | Select code in entry form |

## 4. Functional Matrix

### 4.1 Inspection

| Form ID | Process ID | Functionality |
|---|---|---|
| `PSC_F_001` | `PSC_P_001` | Dashboard access |
| `PSC_F_002` | `PSC_P_002` | Inspection list access |
| `PSC_F_002` | `PSC_P_003` | Create new inspection |
| `PSC_F_002` | `PSC_P_004` | Open inspection detail |
| `PSC_F_002` | `PSC_P_005` | Edit inspection |
| `PSC_F_002` | `PSC_P_006` | Submit follow up |
| `PSC_F_003` | `PSC_P_007` | Deficiency list access |
| `PSC_F_003` | `PSC_P_008` | Allocate deficiency |
| `PSC_F_004` | `PSC_P_009` | CAR list access |
| `PSC_F_004` | `PSC_P_010` | Edit CAR |
| `PSC_F_004` | `PSC_P_011` | CAR workflow actions |
| `PSC_F_005` | `PSC_P_012` | View notifications |
| `PSC_F_005` | `PSC_P_013` | Manage notifications |
| `PSC_F_006` | `PSC_P_014` | Sync screen access |
| `PSC_F_007` | `PSC_P_015` | Reports access |
| `PSC_F_008` | `PSC_P_016` | Settings access |

### 4.2 Circular

The active Circular permission surface in the repo is:

- `psc-frontend/src/legacy/vims-basic/pages/circular/*`

The dashboard bridge uses the filter/notification set below.

| Form ID | Process ID | Functionality |
|---|---|---|
| `PSC_F_009` | `PSC_P_017` | Save draft |
| `PSC_F_009` | `PSC_P_018` | Submit for approval |
| `PSC_F_009` | `PSC_P_019` | View pending requests |
| `PSC_F_009` | `PSC_P_024` | Publish |
| `PSC_F_010` | - | Overlay / modal workspace access |
| `PSC_F_011` | `PSC_P_025` | View pending request |
| `PSC_F_011` | `PSC_P_026` | Approve |
| `PSC_F_011` | `PSC_P_027` | Reject |
| `PSC_F_012` | `PSC_P_028` | View filters |
| `PSC_F_012` | `PSC_P_029` | Download PDF from filters area |
| `PSC_F_013` | `PSC_P_030` | View notification list |
| `PSC_F_013` | `PSC_P_031` | View notification detail |
| `PSC_F_013` | `PSC_P_032` | Acknowledge notification |
| `PSC_F_013` | `PSC_P_033` | View crew status |
| `PSC_F_013` | `PSC_P_034` | Remind crew |
| `PSC_F_013` | `PSC_P_035` | Download notification PDF |
| `PSC_F_013` | `PSC_P_036` | Access PDF viewer |
| - | `PSC_P_020` | View approved notification |
| - | `PSC_P_021` | Download approved PDF |
| - | `PSC_P_022` | Delete approved notification |
| - | `PSC_P_023` | Download approved attachment |

### 4.3 ORB

| Form ID | Process ID | Functionality |
|---|---|---|
| `PSC_F_014` | `PSC_P_043` | Select code in entry form |
| `PSC_F_015` | `PSC_P_037` | Edit draft |
| `PSC_F_015` | `PSC_P_038` | Delete draft |
| `PSC_F_016` | `PSC_P_040` | Approve pending entry |
| `PSC_F_016` | `PSC_P_041` | Reject pending entry |
| `PSC_F_017` | `PSC_P_042` | Save approved entry PDF |
| `PSC_F_018` | `PSC_P_039` | Filter reports |
| `PSC_F_019` | - | Report view access |

## 5. How The Frontend Uses The IDs

- `psc-frontend/src/lib/utils/permission-ids.ts` defines the PSC inspection IDs used by the modern shell.
- `psc-frontend/src/hooks/use-auth.ts` normalizes `PSC_`, `F_`, and `P_` inputs before permission checks.
- Legacy Circular and ORB pages call `WithPermission` or helper checks directly against the bridged auth payload.
- `form_ids` is usually checked for page or section visibility.
- `process_ids` is checked for button-level or action-level permissions.

## 6. Notes

- The live export `psc-backend/msc_profiles_export.sql` contains the current permission rows.
- The repo keeps both modern PSC inspection IDs and legacy Circular/ORB IDs.
- If a new form or process ID is added in code or in `msc_profiles`, this document must be updated together with the permission source.

## 7. Source Files

- `psc-backend/apps/accounts/models.py`
- `psc-backend/apps/accounts/utils.py`
- `psc-backend/apps/accounts/backends.py`
- `psc-backend/msc_profiles_export.sql`
- `psc-frontend/src/lib/utils/permission-ids.ts`
- `psc-frontend/src/hooks/use-auth.ts`
- `psc-frontend/src/legacy/vims-basic/pages/circular/Admin.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/circular/Officeuser.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/circular/Dashboard.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/circular/ApprovedNotificationsLibrary.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/Dashboard.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/CrewDashboard.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/ChiefDashboard.jsx`
