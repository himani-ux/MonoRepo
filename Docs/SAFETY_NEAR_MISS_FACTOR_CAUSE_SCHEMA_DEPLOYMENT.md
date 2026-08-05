# Safety Near Miss Factor Cause Schema Deployment

**Date:** 2026-06-15
**Scope:** Server DB changes required for the updated Near Miss create/rework form.

## Apply This Migration

Deploy Django migration:

```bash
python manage.py migrate safety 0039
```

Migration file:

```text
psc-backend/apps/safety/migrations/0039_near_miss_factor_causes.py
```

## DB Changes Required

1. Add a nullable text column to the existing incident table:

```sql
ALTER TABLE dbo.vims_safety_incident
ADD near_miss_factor_causes nvarchar(max) NULL;
```

2. Create the Near Miss cause option table:

```sql
CREATE TABLE dbo.vims_safety_near_miss_cause_option (
    id uniqueidentifier NOT NULL PRIMARY KEY,
    factor nvarchar(16) NOT NULL,
    cause_stage nvarchar(16) NOT NULL,
    option_code nvarchar(64) NOT NULL,
    option_text nvarchar(max) NOT NULL,
    display_order smallint NOT NULL DEFAULT 0,
    active bit NOT NULL DEFAULT 1,
    created_by nvarchar(128) NOT NULL DEFAULT 'system',
    created_date datetime2 NOT NULL DEFAULT sysutcdatetime(),
    updated_by nvarchar(128) NULL,
    updated_date datetime2 NULL
);
```

3. Add the unique constraint and lookup index:

```sql
ALTER TABLE dbo.vims_safety_near_miss_cause_option
ADD CONSTRAINT uq_nm_cause_option_factor_stage_code
UNIQUE (factor, cause_stage, option_code);

CREATE INDEX ix_nm_cause_option_lookup
ON dbo.vims_safety_near_miss_cause_option (active, factor, cause_stage);
```

4. Seed the dropdown data from the Django migration.

Expected seed count: **128 active rows**.

Breakdown:

| Factor | Immediate | Root |
|---|---:|---:|
| Human | 25 | 20 |
| Vessel | 20 | 9 |
| Management | 13 | 19 |
| Other | 12 | 10 |

## Compatibility Note

Do **not** drop these old Near Miss M-SCAT columns yet:

```text
near_miss_mscat_category_id
near_miss_mscat_subcode_id
near_miss_mscat_subcode_ids
```

They remain for historical records and PDF fallback. New create/rework saves clear those fields and use `near_miss_factor_causes`.

## Post-Deploy Checks

```sql
SELECT COUNT(*) AS active_cause_options
FROM dbo.vims_safety_near_miss_cause_option
WHERE active = 1;
-- Expected: 128

SELECT factor, cause_stage, COUNT(*) AS option_count
FROM dbo.vims_safety_near_miss_cause_option
WHERE active = 1
GROUP BY factor, cause_stage
ORDER BY factor, cause_stage;

SELECT TOP 5 id, incident_number, near_miss_factor_causes
FROM dbo.vims_safety_incident
WHERE record_type = 'NEAR_MISS'
ORDER BY created_date DESC;
```

API check after deploy:

```text
GET /api/safety/near-miss/cause-options/
```

The endpoint should return active Human/Vessel/Management/Other factor options for both Immediate Cause and Root Cause.

---

# Safety Near Miss Category Master Deployment

**Date:** 2026-06-18
**Scope:** Server DB changes required to stop merging Near Miss Category with Loss Category and use a dedicated Near Miss category master.

## Apply This Migration

Deploy Django migration:

```bash
python manage.py migrate safety 0041
```

Migration file:

```text
psc-backend/apps/safety/migrations/0040_near_miss_categories_master.py
psc-backend/apps/safety/migrations/0041_seed_near_miss_other_category.py
```

## DB Changes Required

Create the Near Miss category master table:

```sql
CREATE TABLE dbo.vims_safety_NM_categories (
    id uniqueidentifier NOT NULL PRIMARY KEY,
    category_name nvarchar(64) NOT NULL UNIQUE,
    display_order smallint NOT NULL DEFAULT 0,
    active bit NOT NULL DEFAULT 1,
    created_by nvarchar(128) NOT NULL DEFAULT 'system',
    created_date datetime2 NOT NULL DEFAULT sysutcdatetime(),
    updated_by nvarchar(128) NULL,
    updated_date datetime2 NULL
);

CREATE INDEX ix_nm_category_active_order
ON dbo.vims_safety_NM_categories (active, display_order);
```

Seed these **16 active categories**:

```text
PPE
Fire Safety
LSA
Safety Awareness
Work Routines
Maintenance
Machinery
Housekeeping
Seamanship
Pollution
Communication/Instructions
Navigation
Leadership
Structural
Cargo Operation
Other
```

## Manual SQL Fallback

Use this only if Django migrations are not being run on server:

```sql
INSERT INTO dbo.vims_safety_NM_categories
    (id, category_name, display_order, active, created_by, created_date)
VALUES
    (NEWID(), N'PPE', 1, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Fire Safety', 2, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'LSA', 3, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Safety Awareness', 4, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Work Routines', 5, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Maintenance', 6, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Machinery', 7, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Housekeeping', 8, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Seamanship', 9, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Pollution', 10, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Communication/Instructions', 11, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Navigation', 12, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Leadership', 13, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Structural', 14, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Cargo Operation', 15, 1, N'manual-server-update', SYSUTCDATETIME()),
    (NEWID(), N'Other', 16, 1, N'manual-server-update', SYSUTCDATETIME());
```

## Post-Deploy Checks

```sql
SELECT COUNT(*) AS active_nm_categories
FROM dbo.vims_safety_NM_categories
WHERE active = 1;
-- Expected: 16

SELECT category_name, display_order, active
FROM dbo.vims_safety_NM_categories
ORDER BY display_order;
```

API check after deploy:

```text
GET /api/safety/near-miss/categories/
```

The endpoint should return only the 16 Near Miss categories above. Loss Category remains separate and should not be merged into this dropdown. When user selects `Other`, the UI must require a specified category and store it as `Other: <specified text>`. The specified text after `Other:` is limited to 200 characters.

---

# 2026-07-13 Backup Comparison Before Deployment

Compared backup:

```text
C:\Users\himan\Downloads\ksm_marine_live_03_July_2026 (1).zip
```

The zip contains `ksm_marine_live_03_July_2026.bak`. It was restored locally for comparison as:

```text
ksm_marine_live_03july_compare_codex
```

## Result

The restored server backup has Safety migrations only through:

```text
0034_near_miss_place_multiselect
```

The current local DB has Safety migrations through:

```text
0058_incident_phase1_operational_fields
```

For Near Miss specifically, the backup is missing:

- `0036_rename_near_miss_office_comment_states`
- `0039_near_miss_factor_causes`
- `0040_near_miss_categories_master`
- `0041_seed_near_miss_other_category`
- `0042_near_miss_rejected_state`

The safest server update is still the normal Django migration path:

```powershell
python manage.py migrate safety 0058
```

That command applies the Near Miss migrations above and the related Incident migrations in dependency order.

## Backup Data Note

The restored server backup contains `9` Near Miss rows in `dbo.vims_safety_incident`:

```sql
SELECT record_type, state, COUNT(*) AS row_count
FROM dbo.vims_safety_incident
GROUP BY record_type, state;
```

Observed result from the restored backup:

| record_type | state | row_count |
|---|---|---:|
| `NEAR_MISS` | `PENDING_VESSEL_REVIEW` | 9 |

Because Near Miss is stored in `dbo.vims_safety_incident`, do not delete from this table during deployment unless the delete query explicitly preserves `record_type = 'NEAR_MISS'`.

## Missing Near Miss Schema/Seed Objects In Backup

The restored backup is missing the entire table:

```text
vims_safety_near_miss_cause_option
```

Current local expected active row count:

```text
128
```

The restored backup is missing the entire table:

```text
vims_safety_NM_categories
```

Current local expected active row count:

```text
16
```

The restored backup is missing this column on the shared Incident/Near Miss table:

```text
dbo.vims_safety_incident.near_miss_factor_causes
```

The restored backup also has the older incident-state check constraint, which still lists:

```text
READY_FOR_DPA_TRIAGE
TRIAGED
```

Current local constraint expects:

```text
READY_FOR_OFFICE_COMMENTS
OFFICE_COMMENTS_COMPLETED
REJECTED
```

## Post-Deploy Near Miss Checks

Run these after migrating the server:

```sql
SELECT TOP 1 name
FROM dbo.django_migrations
WHERE app = 'safety'
ORDER BY name DESC;
-- Expected: 0058_incident_phase1_operational_fields

SELECT COUNT(*) AS active_cause_options
FROM dbo.vims_safety_near_miss_cause_option
WHERE active = 1;
-- Expected: 128

SELECT factor, cause_stage, COUNT(*) AS option_count
FROM dbo.vims_safety_near_miss_cause_option
WHERE active = 1
GROUP BY factor, cause_stage
ORDER BY factor, cause_stage;

SELECT COUNT(*) AS active_nm_categories
FROM dbo.vims_safety_NM_categories
WHERE active = 1;
-- Expected: 16

SELECT COUNT(*) AS near_miss_rows
FROM dbo.vims_safety_incident
WHERE record_type = 'NEAR_MISS';
-- The 2026-07-03 backup had 9 rows. Confirm the server count is not unintentionally reduced.

SELECT name, definition
FROM sys.check_constraints
WHERE parent_object_id = OBJECT_ID('dbo.vims_safety_incident')
  AND name = 'ck_vims_safety_incident_state_schema_v2';
```
