# Safety Incident Phase 1/2 Schema Deployment Note

Date: 2026-06-11

This file tracks the DB change required for the simplified Incident Phase 1/2 flow.

## Local schema change

Table: `vims_safety_incident`

New columns:

- `office_notified` - nullable boolean. Stores the answer for `Notified to Office?`
- `office_notification_mode` - nullable varchar(16). Stores one of:
  - `ON_CALL`
  - `WHATSAPP`
  - `EMAIL`
- `loss_type_secondary_id` - nullable integer. Stores second selected type of loss.
- `loss_type_tertiary_id` - nullable integer. Stores third selected type of loss.
- `loss_type_other` - nullable varchar(256). Stores custom loss type when user selects `Other - specify`.

New check constraint:

- `ck_vims_safety_incident_office_notification_mode`

## Server schema check

Run this first on server DB:

```sql
SELECT
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.is_nullable
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('dbo.vims_safety_incident')
  AND c.name IN (
      'office_notified',
      'office_notification_mode',
      'loss_type_secondary_id',
      'loss_type_tertiary_id',
      'loss_type_other'
  );

SELECT name
FROM sys.check_constraints
WHERE parent_object_id = OBJECT_ID('dbo.vims_safety_incident')
  AND name = 'ck_vims_safety_incident_office_notification_mode';
```

Expected result after deployment:

- All five columns should be present.
- The check constraint should be present.

## Preferred server update

Run Django migration:

```bash
python manage.py migrate safety 0037_incident_office_notification_fields
python manage.py migrate safety 0038_incident_multiple_loss_types
```

## Manual SQL fallback

Use this only if migrations are not being run on server:

```sql
ALTER TABLE dbo.vims_safety_incident
ADD office_notified bit NULL;

ALTER TABLE dbo.vims_safety_incident
ADD office_notification_mode varchar(16) NULL;

ALTER TABLE dbo.vims_safety_incident
ADD loss_type_secondary_id int NULL;

ALTER TABLE dbo.vims_safety_incident
ADD loss_type_tertiary_id int NULL;

ALTER TABLE dbo.vims_safety_incident
ADD loss_type_other varchar(256) NULL;

ALTER TABLE dbo.vims_safety_incident
ADD CONSTRAINT ck_vims_safety_incident_office_notification_mode
CHECK (
    office_notification_mode IS NULL
    OR office_notification_mode IN ('ON_CALL', 'WHATSAPP', 'EMAIL')
);
```

## Code behavior after this change

- Users no longer see IMO Classifier.
- Users no longer enter latitude/longitude.
- Users no longer see the MSC-MEPC.3 position block.
- Users select `Internal risk band`; the system derives investigation depth automatically.
- Users can select up to three `Type of loss` values.
- `Other - specify` counts as one of the three loss type values and requires text.
- Users answer `Notified to Office?`; if Yes, they select communication mode.
- Existing old timestamp columns remain for compatibility and existing reports.

## 2026-06-19 Weather Condition schema change

Scope: Incident Phase 1 now has a `Weather Condition` section.

New master table:

- `vims_safety_incident_weather_option`
- Primary key: `id uniqueidentifier`
- Stores dropdown options by `field_key`.
- Options are seeded by `0044_seed_incident_weather_options`.

Dropdown-backed incident columns:

- `weather_visibility_id`
- `weather_precipitation_id`
- `weather_sea_state_id`
- `weather_wind_scale_id`
- `weather_wind_direction_id`
- `weather_lighting_source_id`
- `weather_current_direction_id`
- `weather_ice_condition_onboard_id`
- `weather_ice_condition_at_sea_id`
- `weather_light_condition_id`

Text-area incident columns:

- `weather_current_strength_knots`
- `weather_ambient_temperature_c`

Preferred server update:

```bash
python manage.py migrate safety 0043_incident_weather_condition_fields
python manage.py migrate safety 0044_seed_incident_weather_options
```

Manual SQL fallback:

```sql
CREATE TABLE dbo.vims_safety_incident_weather_option (
    id uniqueidentifier NOT NULL PRIMARY KEY,
    field_key varchar(32) NOT NULL,
    option_label varchar(128) NOT NULL,
    display_order smallint NOT NULL DEFAULT 0,
    active bit NOT NULL DEFAULT 1,
    created_by varchar(128) NOT NULL DEFAULT 'system',
    created_date datetime2 NOT NULL DEFAULT SYSUTCDATETIME(),
    updated_by varchar(128) NULL,
    updated_date datetime2 NULL
);

ALTER TABLE dbo.vims_safety_incident_weather_option
ADD CONSTRAINT uq_inc_weather_option_field_label UNIQUE (field_key, option_label);

CREATE INDEX ix_inc_weather_option_lookup
ON dbo.vims_safety_incident_weather_option (active, field_key, display_order);

ALTER TABLE dbo.vims_safety_incident ADD weather_visibility_id uniqueidentifier NULL;
ALTER TABLE dbo.vims_safety_incident ADD weather_precipitation_id uniqueidentifier NULL;
ALTER TABLE dbo.vims_safety_incident ADD weather_sea_state_id uniqueidentifier NULL;
ALTER TABLE dbo.vims_safety_incident ADD weather_wind_scale_id uniqueidentifier NULL;
ALTER TABLE dbo.vims_safety_incident ADD weather_wind_direction_id uniqueidentifier NULL;
ALTER TABLE dbo.vims_safety_incident ADD weather_lighting_source_id uniqueidentifier NULL;
ALTER TABLE dbo.vims_safety_incident ADD weather_current_direction_id uniqueidentifier NULL;
ALTER TABLE dbo.vims_safety_incident ADD weather_current_strength_knots nvarchar(max) NULL;
ALTER TABLE dbo.vims_safety_incident ADD weather_ambient_temperature_c nvarchar(max) NULL;
ALTER TABLE dbo.vims_safety_incident ADD weather_ice_condition_onboard_id uniqueidentifier NULL;
ALTER TABLE dbo.vims_safety_incident ADD weather_ice_condition_at_sea_id uniqueidentifier NULL;
ALTER TABLE dbo.vims_safety_incident ADD weather_light_condition_id uniqueidentifier NULL;
```

## 2026-06-19 Incident Phase 2 Cause Factor schema change

Scope: Incident Phase 2 `RCA (Root Cause Analysis)` now uses the same factor-based cause master as Near Miss instead of asking the user to select M-SCAT codes for the main cause list.

Existing master used:

- `vims_safety_near_miss_cause_option`
- Factors: `HUMAN`, `MANAGEMENT`, `VESSEL`, `OTHER`
- Stages: `IMMEDIATE`, `ROOT`
- Incident `Immediate Cause` uses `IMMEDIATE` options.
- Incident `Intermediate Cause` and `Root Cause` use `ROOT` options.

Updated incident cause table:

- `vims_safety_cause_tag`

New columns:

- `cause_factor` - nullable varchar(16). Stores `HUMAN`, `MANAGEMENT`, `VESSEL`, or `OTHER`.
- `cause_option_id` - nullable uniqueidentifier. Stores selected `vims_safety_near_miss_cause_option.id`.
- `cause_option_text` - nullable text. Stores selected option text snapshot for reporting/history.
- `cause_other_text` - nullable text. Stores custom text when selected option is `Other`.

Compatibility:

- `mscat_subcode_id` remains in `vims_safety_cause_tag` for existing records and backend compatibility.
- New Phase 2 cause-factor saves set `mscat_subcode_id = 'OTHER'`.
- Safeguard failure technical fields still retain their existing M-SCAT columns.

Preferred server update:

```bash
python manage.py migrate safety 0045_incident_cause_factor_fields
```

Manual SQL fallback:

```sql
ALTER TABLE dbo.vims_safety_cause_tag ADD cause_factor varchar(16) NULL;
ALTER TABLE dbo.vims_safety_cause_tag ADD cause_option_id uniqueidentifier NULL;
ALTER TABLE dbo.vims_safety_cause_tag ADD cause_option_text nvarchar(max) NULL;
ALTER TABLE dbo.vims_safety_cause_tag ADD cause_other_text nvarchar(max) NULL;
```

## 2026-07-13 Server backup comparison before deployment

Compared backup:

```text
C:\Users\himan\Downloads\ksm_marine_live_03_July_2026 (1).zip
```

The zip contains `ksm_marine_live_03_July_2026.bak`. For comparison it was restored locally as:

```text
ksm_marine_live_03july_compare_codex
```

Comparison target:

```text
local current DB: ksm_marine_live
server backup DB: ksm_marine_live_03july_compare_codex
```

### Migration position

The restored server backup has Safety migrations only up to:

```text
0034_near_miss_place_multiselect
```

The current local DB has Safety migrations through:

```text
0058_incident_phase1_operational_fields
```

Before deploying the current code to the server, run:

```powershell
python manage.py migrate safety 0058
```

This should apply all missing Safety migrations from `0035` through `0058` in order. Do not skip the intermediate migrations; several update existing constraints, seed rows, and near-miss workflow states.

### Incident/Near Miss data note

The restored server backup has `9` rows in `dbo.vims_safety_incident`, all with:

```text
record_type = NEAR_MISS
state = PENDING_VESSEL_REVIEW
```

Near Miss uses `dbo.vims_safety_incident`. Do not use a blanket delete against `dbo.vims_safety_incident` on server unless you intentionally want to delete Near Miss records too.

### Server DB changes still missing in the 2026-07-03 backup

The backup is missing these current Safety schema/data changes:

| Migration | Server impact |
|---|---|
| `0035_scm_closed_state` | Updates SCM state constraint so `CLOSED` is allowed. |
| `0036_rename_near_miss_office_comment_states` | Updates Near Miss office-comment state names and the incident state check constraint. |
| `0037_incident_office_notification_fields` | Adds `office_notified`, `office_notification_mode`, and the office-notification check constraint. |
| `0038_incident_multiple_loss_types` | Adds secondary/tertiary loss type columns and `loss_type_other`. |
| `0039_near_miss_factor_causes` | Adds `near_miss_factor_causes` and creates/seeds `vims_safety_near_miss_cause_option`. |
| `0040_near_miss_categories_master` / `0041_seed_near_miss_other_category` | Creates/seeds `vims_safety_NM_categories`. |
| `0042_near_miss_rejected_state` | Adds current Near Miss rejected-state support. |
| `0043_incident_weather_condition_fields` / `0044_seed_incident_weather_options` | Adds Incident weather columns and seeds `vims_safety_incident_weather_option`. |
| `0045_incident_cause_factor_fields` | Adds cause-factor columns to `vims_safety_cause_tag`. |
| `0046_enhance_injury_record_for_crew` | Expands injury rows for crew injury reporting. |
| `0047_injury_dropdown_options_master` / `0048_add_type_of_activity_injury_dropdowns` | Creates/seeds `vims_safety_injury_dropdown_option`. |
| `0049_remove_missing_vessel_incident_type` / `0051_replace_incident_type_master_list` | Updates `master_safety_incident_type`; local has 42 rows, backup has 11. |
| `0050_incident_reporting_context_fields` | Adds reporting-context fields such as vessel location, onboard location, departure date, and vessel condition. |
| `0052_incident_office_comment` | Adds `office_comment`. |
| `0053_incident_loss_evaluation` | Creates `vims_safety_incident_loss_evaluation`. |
| `0054_alter_injurydropdownoption_field_key` | Aligns injury dropdown field key storage. |
| `0055_seed_safe_working_practice_options` | Seeds safe-working-practice options used by Loss Evaluation. |
| `0056_incident_loss_evaluation_report_type` | Adds Loss Evaluation report type. |
| `0057_remove_recommendation_tier_cardinality` | Removes the one-active-recommendation-row-per-tier limitation. |
| `0058_incident_phase1_operational_fields` | Adds `risk_assessment_carried_out`, `toolbox_meeting_carried_out`, `permit_issued`, `activity_type`, `incident_type_other`, and `vessel_location_detail`, plus YES/NO/NA check constraints. |

### Comparison highlights

In the restored backup, these tables are missing entirely:

```text
vims_safety_incident_loss_evaluation
vims_safety_incident_weather_option
vims_safety_injury_dropdown_option
vims_safety_near_miss_cause_option
vims_safety_NM_categories
```

The restored backup is missing these important `dbo.vims_safety_incident` columns:

```text
office_notified
office_notification_mode
loss_type_secondary_id
loss_type_tertiary_id
loss_type_other
near_miss_factor_causes
weather_visibility_id
weather_precipitation_id
weather_sea_state_id
weather_wind_scale_id
weather_wind_direction_id
weather_lighting_source_id
weather_current_direction_id
weather_current_strength_knots
weather_ambient_temperature_c
weather_ice_condition_onboard_id
weather_ice_condition_at_sea_id
weather_light_condition_id
shore_assistance_required
vessel_location
onboard_location
last_port
departure_date
vessel_condition
office_comment
risk_assessment_carried_out
toolbox_meeting_carried_out
permit_issued
activity_type
incident_type_other
vessel_location_detail
```

The restored backup also has older check constraints:

- `ck_vims_safety_incident_state_schema_v2` still allows old Near Miss states `READY_FOR_DPA_TRIAGE` and `TRIAGED`; local expects `READY_FOR_OFFICE_COMMENTS`, `OFFICE_COMMENTS_COMPLETED`, and `REJECTED`.
- `ck_vims_safety_scm_meeting_state` does not allow `CLOSED`; local does.

### Post-deployment verification

Run these checks on the server after migration:

```sql
SELECT TOP 1 name
FROM dbo.django_migrations
WHERE app = 'safety'
ORDER BY name DESC;
-- Expected: 0058_incident_phase1_operational_fields

SELECT name
FROM dbo.django_migrations
WHERE app = 'safety'
  AND name BETWEEN '0035' AND '0058'
ORDER BY name;
-- Expected: every Safety migration from 0035 through 0058.

SELECT COUNT(*) AS incident_type_count
FROM dbo.master_safety_incident_type;
-- Expected current local count: 42

SELECT COUNT(*) AS weather_option_count
FROM dbo.vims_safety_incident_weather_option
WHERE active = 1;
-- Expected current local count: 79

SELECT COUNT(*) AS loss_evaluation_rows
FROM dbo.vims_safety_incident_loss_evaluation;
-- Table must exist. Row count can be 0.

SELECT name, definition
FROM sys.check_constraints
WHERE parent_object_id = OBJECT_ID('dbo.vims_safety_incident')
  AND name IN (
      'ck_vims_safety_incident_state_schema_v2',
      'ck_vims_safety_incident_office_notification_mode',
      'ck_vims_safety_incident_risk_assessment',
      'ck_vims_safety_incident_toolbox_meeting',
      'ck_vims_safety_incident_permit_issued'
  );
```
