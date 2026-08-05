# Safety Crew Injury Schema Deployment

Date: 2026-06-22

## Purpose

Incident Phase 1 injury capture supports both crew and non-crew. Existing non-crew fields remain available. Crew injury adds rank, age, vessel/location, and OCIMF reporting. The current UI does not show a separate injury **Describe What Happened** field; `what_happened_narrative` remains nullable legacy storage/API compatibility and is not printed in the current Incident PDF. Estimated-cost entry is no longer shown in Phase 1; current cost capture belongs to Phase 7 Loss Evaluation, while legacy injury cost columns remain available for older records and fallback exports.

## Dropdown Master Update - 2026-06-23

Apply Django migration:

```powershell
python manage.py migrate safety 0048
```

Migration file:

```text
psc-backend/apps/safety/migrations/0048_add_type_of_activity_injury_dropdowns.py
```

New master table:

```text
vims_safety_injury_dropdown_option
```

The table has a UUID primary key and stores the dropdown options for:

```text
TYPE_OF_ACTIVITY
nature_of_injury
source_of_injury
affected_body_areas
```

The existing injury record text columns continue to store the selected value. If the user selects `Others(Specify)`, the typed value is stored in the same injury record field.

Reference API:

```text
GET /api/safety/reference/injury-dropdown-options/
GET /api/safety/reference/injury-dropdown-options/?field_key=NATURE_OF_INJURY
GET /api/safety/reference/injury-dropdown-options/?field_key=TYPE_OF_ACTIVITY
```

### Type of Activity

```text
Anchoring
Ballast operations
Bunkering
Cargo operations
Cold work
Derusting
Drills & Exercises
Enclosed space entry
Handling of chemicals
Helicopter operations
Hot work
In Dry Dock
Lifting operations (mechanical)
Manual handling
Mooring / Unmooring – tugs used
Mooring / Unmooring – no tugs
Navigation – Pilot onboard
Navigation – without Pilot
Overhauling machinery
Painting
STS operations
Transfer of personnel by ladder
Transfer of personnel by basket
Use of power tools
Use of stairs
Walking on same level
Work aloft
Work in pressurised piping or equipment
Work outboard
Working in electrical equipment
Working in galley
Others(Specify)
```

### Nature of Injury

```text
Amputation
Asphyxia
Burn (chemical)
Burn (heat/cold)
Concussion / Brain injury
Crushing / Bruises
Cuts / Lacerations
Dislocation
Drowning
Effects of chemicals
Electric shock
Foreign body (eye)
Fracture
Heat stroke
Hypothermia
Inflammation
Internal injury
Loss of consciousness
Loss of sight
Scratches / Abrasions
Sprains and strains
Other (specify)
```

### Source of Injury

```text
Contact with chemicals
Contact with heat
Contact with cold
Pressure release
Electricity
Slip, trip, fall (same level)
Fall from height (>1.8m)
Fire, explosion
Hand tools
Immersion in water
Radiation
Struck by / against
Manual handling
Mechanical lifting
Pollution
Falling object
Cut by sharp instruments
Inhalation of toxic or corrosive substances
Lack of O2
Caught in / on / in between objects
Over exposure to cold
Over exposure to heat
Other (specify)
```

### Affected Areas of the Body

```text
Abdomen
Arm(s)
Back
Chest
Eye(s)
Feet
Fingers
Hand(s)
Head
Internal
Leg(s)
Neck
Toes
Other (specify)
```

## Migration

Apply Django migration:

```powershell
python manage.py migrate safety 0046
```

Migration file:

```text
psc-backend/apps/safety/migrations/0046_enhance_injury_record_for_crew.py
```

## Table Modified

```text
vims_safety_external_party_injury
```

The table name is retained for compatibility, but its functional meaning is now the Phase 1 injury record.

## Column Changes

Existing columns changed to allow blank values so crew injury rows do not require non-crew fields:

```sql
party_name NVARCHAR(128) NULL
party_type VARCHAR(32) NULL
company_name NVARCHAR(128) NULL
severity NVARCHAR(64) NULL
```

New discriminator:

```sql
injured_person_type VARCHAR(16) NOT NULL DEFAULT 'NON_CREW'
```

New crew details:

```sql
crew_rank NVARCHAR(128) NULL
crew_age SMALLINT NULL
crew_activity_type NVARCHAR(128) NULL
shore_assistance_required BIT NULL
vessel_location NVARCHAR(128) NULL
onboard_location NVARCHAR(128) NULL
last_port NVARCHAR(128) NULL
departure_date DATE NULL
vessel_condition VARCHAR(16) NULL
```

Investigation/detail fields. `what_happened_narrative` is legacy compatibility only in the current UI/PDF; the incident-level narrative is authoritative:

```sql
what_happened_narrative NVARCHAR(MAX) NULL
nature_of_injury NVARCHAR(255) NULL
source_of_injury NVARCHAR(255) NULL
affected_body_areas NVARCHAR(255) NULL
first_aid_details NVARCHAR(MAX) NULL
why_it_happened_analysis NVARCHAR(MAX) NULL
regulation_or_procedure_breach NVARCHAR(MAX) NULL
risk_assessment_carried_out VARCHAR(8) NULL
toolbox_meeting_carried_out VARCHAR(8) NULL
prevention_action_taken_required NVARCHAR(MAX) NULL
```

New OCIMF flags:

```sql
ocimf_fatality BIT NULL
ocimf_permanent_total_disability BIT NULL
ocimf_permanent_partial_disability BIT NULL
ocimf_lost_workday_case BIT NULL
ocimf_restricted_workday_case BIT NULL
ocimf_medical_treatment_case BIT NULL
ocimf_first_aid_case BIT NULL
```

New estimated cost fields:

```sql
cost_medicines_onboard DECIMAL(12,2) NULL
cost_doctor_visits DECIMAL(12,2) NULL
cost_repatriation DECIMAL(12,2) NULL
cost_evacuation DECIMAL(12,2) NULL
cost_off_hire DECIMAL(12,2) NULL
cost_vessel_delays DECIMAL(12,2) NULL
cost_man_hours_lost DECIMAL(12,2) NULL
cost_deviation DECIMAL(12,2) NULL
cost_miscellaneous DECIMAL(12,2) NULL
miscellaneous_expenses_reason NVARCHAR(MAX) NULL
total_estimated_cost DECIMAL(12,2) NULL
```

## API Contract

`external_party_injury` remains the nested Phase 1 payload key for compatibility.

On Phase 1 or incident update, a populated `external_party_injury` payload creates or updates the injury row. A null or omitted `external_party_injury` payload does not delete an existing injury row; deletion must be handled as an explicit future action if required.

For non-crew:

```json
{
  "injured_person_type": "NON_CREW",
  "party_name": "Pilot name",
  "party_type": "PILOT",
  "company_name": "Company",
  "severity": "First aid",
  "notes": "Details"
}
```

For crew:

```json
{
  "injured_person_type": "CREW",
  "crew_rank": "ABLE SEAMAN",
  "crew_age": 31,
  "shore_assistance_required": true,
  "vessel_condition": "LOADED",
  "ocimf_lost_workday_case": false,
  "total_estimated_cost": "0.00"
}
```
