# Permission ID Mapping

This document maps the `form_ids` and `process_ids` used by this project to the permissions/features they control.

Source of permission values in auth flow:

- Office users: `mapping_role_user -> master_role -> msc_profiles`
- Vessel users: `master_applied_rank.rank_name -> msc_profiles`
- Frontend guards read `form_ids` and `process_ids` from authenticated user state

Primary source files used for this mapping:

- `psc-frontend/src/lib/utils/permission-ids.ts`
- `psc-frontend/src/legacy/vims-basic/pages/circular/Dashboard.jsx`
- `psc-frontend/src/legacy/vims-basic/pages/orb/Dashboard.jsx`

## 1. PSC App Permission Mapping

Source: `psc-frontend/src/lib/utils/permission-ids.ts`

### Form IDs

| Form ID | Permission / Feature |
|---|---|
| `PSC_F_001` | Dashboard |
| `PSC_F_002` | Inspections |
| `PSC_F_003` | Deficiencies |
| `PSC_F_004` | CARs |
| `PSC_F_005` | Notifications |
| `PSC_F_006` | Sync |
| `PSC_F_007` | Reports |
| `PSC_F_008` | Settings |

### Process IDs

| Process ID | Permission / Feature |
|---|---|
| `PSC_P_001` | View Dashboard |
| `PSC_P_002` | View Inspections |
| `PSC_P_003` | Create Inspection |
| `PSC_P_004` | View Inspection Detail |
| `PSC_P_005` | Edit Inspection |
| `PSC_P_006` | Submit Follow Up |
| `PSC_P_007` | View Deficiencies |
| `PSC_P_008` | Allocate Deficiency |
| `PSC_P_009` | View CARs |
| `PSC_P_010` | Edit CAR |
| `PSC_P_011` | CAR Workflow |
| `PSC_P_012` | View Notifications |
| `PSC_P_013` | Manage Notifications |
| `PSC_P_014` | View Sync |
| `PSC_P_015` | View Reports |
| `PSC_P_016` | View Settings |

## 2. Legacy Circular Permission Mapping

Source: `psc-frontend/src/legacy/vims-basic/pages/circular/Dashboard.jsx`

The legacy Circular dashboard maps backend IDs to UI capability names.

### Form IDs

| Form ID | Permission / Feature |
|---|---|
| `F_004` | Filters |
| `F_005` | Notifications |

### Process IDs

| Process ID | Permission / Feature |
|---|---|
| `P_012` | View Filters |
| `P_013` | Download PDF |
| `P_014` | View Notification List |
| `P_015` | View Notification Detail |
| `P_016` | Acknowledge Notification |
| `P_017` | View Crew Status |
| `P_018` | Remind Crew |
| `P_019` | Download Notification PDF |
| `P_020` | Access PDF Viewer |

### Effective legacy Circular permission checks

| Requirement in UI | Required IDs |
|---|---|
| Use search / department filter / type filter / criticality filter / unread toggle | `F_004` + `P_012` |
| Download from filters area | `F_004` + `P_013` |
| View notification list | `F_005` + `P_014` |
| View notification detail | `F_005` + `P_015` |
| Acknowledge notification | `F_005` + `P_016` |
| View crew status | `F_005` + `P_017` |
| Remind crew | `F_005` + `P_018` |
| Download notification PDF | `F_005` + `P_019` |
| Access PDF viewer | `F_005` + `P_020` |

## 3. Legacy ORB Permission Mapping

Source: `psc-frontend/src/legacy/vims-basic/pages/orb/Dashboard.jsx`

### Form IDs

| Form ID | Permission / Feature |
|---|---|
| `F_006` | ORB Entry Form |
| `F_007` | ORB Table |
| `F_008` | Pending Entries |
| `F_009` | Approved Entries |
| `F_010` | Report Filter |
| `F_011` | Report View |

### Process IDs

| Process ID | Permission / Feature |
|---|---|
| `P_021` | Edit Draft |
| `P_022` | Delete Draft |
| `P_023` | Filter Reports |
| `P_024` | Approve Entry |
| `P_025` | Reject Entry |
| `P_026` | Save Approved Entry PDF |
| `P_027` | Select Code in Entry Form |

### Effective legacy ORB permission checks

| Requirement in UI | Required IDs |
|---|---|
| Access ORB entry form | `F_006` |
| Select code in entry form | `F_006` + `P_027` |
| Access ORB table | `F_007` |
| Edit table draft | `F_007` + `P_021` |
| Delete table draft | `F_007` + `P_022` |
| Access pending entries | `F_008` |
| Approve pending entry | `F_008` + `P_024` |
| Reject pending entry | `F_008` + `P_025` |
| Access approved entries | `F_009` |
| Save approved entry PDF | `F_009` + `P_026` |
| Access report filter | `F_010` |
| Filter reports | `F_010` + `P_023` |
| Access report view | `F_011` |

## 4. Notes

- The project currently supports both legacy IDs (`F_###`, `P_###`) and PSC-prefixed IDs (`PSC_F_###`, `PSC_P_###`) in permission checks.
- The database-backed permission source is `msc_profiles.form_ids` and `msc_profiles.process_ids`.
- This document reflects mappings explicitly present in the current repository. If new IDs are added later in code or database data, this document will need to be updated.
