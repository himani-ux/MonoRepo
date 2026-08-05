# PSC CAR Renumbering Implementation Note

## Purpose

This note explains how to change existing PSC CAR numbers from the current global yearly series to a vessel-wise series, including the already-created CAR records.

Current format:

```text
PSC-{YEAR}-{SEQ}
Example: PSC-2026-001
```

Recommended vessel-wise format:

```text
PSC-{VESSEL_CODE}-{YEAR}-{SEQ}
Example: PSC-AYU-2026-001
```

## Current Logic

CAR numbers are generated when a deficiency is created.

Flow:

```text
Deficiency created
-> post_save signal runs
-> CAR.generate_car_number()
-> psc_car row is created
-> deficiency is linked to that CAR
```

The current sequence is global per year. It is not vessel-wise.

Example:

```text
Vessel A -> PSC-2026-001
Vessel B -> PSC-2026-002
Vessel A -> PSC-2026-003
```

## Required New Logic

The new sequence should be grouped by vessel and year.

Example:

```text
Vessel A -> PSC-AYU-2026-001
Vessel A -> PSC-AYU-2026-002
Vessel B -> PSC-BVSL-2026-001
Vessel B -> PSC-BVSL-2026-002
```

The vessel should be resolved through:

```text
CAR -> Deficiency -> Inspection -> Vessel
```

## Existing CAR Renumbering

If the previous 21 CARs also need to be changed, create an old-to-new mapping first.

Mapping columns:

```text
car_id
old_car_number
new_car_number
vessel_id
vessel_code
created_date
```

Recommended ordering per vessel:

```text
created_date ASC, old_car_number ASC
```

Then assign sequence from `001` per vessel per year.

## Tables To Update

Primary source:

```text
psc_car.car_number
```

Likely text references to inspect and update:

```text
activity_history.event_description
audit/history description fields
notification message fields
generated report/export metadata
file names or stored paths that include car_number
```

Most relational links should remain safe because they use IDs such as:

```text
car_id
deficiency_id
inspection_id
```

Only plain-text references need replacement.

## Generated Files

Already generated PDFs, Excel files, reports, or exported bundles will not change automatically.

Choose one approach:

```text
Option 1: delete old generated files and regenerate them after renumbering
Option 2: keep old files as historical exports and accept that they show old CAR numbers
```

For a clean demo or pre-production cleanup, Option 1 is recommended.

## Safe Migration Steps

1. Take a database backup.
2. Freeze CAR creation during migration.
3. Build the old-to-new mapping table.
4. Validate that every new CAR number is unique.
5. Update `psc_car.car_number`.
6. Replace old CAR numbers in text/history/notification columns.
7. Delete or regenerate stale generated files.
8. Run smoke checks:

```text
CAR list opens
CAR detail opens
Inspection deficiency detail shows linked CAR
CAR PDF/export uses new number
Search by new CAR number works
Old CAR number does not appear in user-facing screens
```

## Risk Notes

Renumbering old CARs is safe only if the system is still pre-production or the numbers were not formally shared.

If old CAR numbers were already used in emails, reports, printouts, audits, or external communication, changing them can create traceability confusion. In that case, keep the old 21 numbers and apply vessel-wise numbering only to future CARs.

## Recommended Final Decision

For pre-demo or pre-production data:

```text
Renumber existing 21 CARs and regenerate/delete stale exports.
```

For live production data:

```text
Keep existing CAR numbers unchanged and apply vessel-wise numbering only going forward.
```
