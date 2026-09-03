# Near Miss Draft Prefix Formal Number Plan

## Status

Implemented locally for future Near Miss create, vessel review, and rework-submission flows. Existing server rows are not changed by this code change; they still require the separate DB update/backfill step when the user deploys Safety changes to server.

## Enhancement Request

When a vessel-side Near Miss is submitted to office and the Near Miss state becomes `READY_FOR_OFFICE_COMMENTS`, the visible Near Miss number should stop showing the `DRAFT-` prefix.

Current draft-style example:

```text
DRAFT-YCF/2026/T008
```

Expected formal-style format after office submission:

```text
YCF/2026/008
```

The numeric suffix is assigned by the existing formal number allocator for the vessel/year sequence. The implementation does not perform a literal SQL string replacement in application code.

## Current Number Storage

The Near Miss number is not stored in a separate Near Miss table or a separate `near_miss_number` column.

Near Miss records are stored in the shared Safety incident table:

```text
Table: vims_safety_incident
```

The same table holds both Incident and Near Miss records. Near Miss records are identified by `record_type = 'NEAR_MISS'`.

## Table And Column Impact

| Table | Column | Current purpose | Will be affected? | Impact |
| --- | --- | --- | --- | --- |
| `vims_safety_incident` | `incident_number` | Holds the visible Incident/Near Miss reference number. For Near Miss, this currently holds values like `DRAFT-YCF/2026/T008`. | Yes | This is the main column that would change from draft number to formal number when state becomes `READY_FOR_OFFICE_COMMENTS`. |
| `vims_safety_incident` | `state` | Holds the workflow state, including `PENDING_VESSEL_REVIEW`, `READY_FOR_OFFICE_COMMENTS`, and later office states. | Yes | This column triggers the timing of the number change. The state value itself already exists and does not need a schema change. |
| `vims_safety_incident` | `record_type` | Identifies whether the row is `INCIDENT` or `NEAR_MISS`. | Read only | Used to ensure the logic applies only to Near Miss rows. No value change required. |
| `vims_safety_incident` | `id` | Primary identifier used by APIs and related records. | No | This should not change. Internal references should continue to use the same row ID. |
| `vims_safety_incident_phase_log` | comment/message fields | Stores historical workflow log text. | No direct update | Historical logs may already contain the old draft number. They should normally remain unchanged as audit history. |
| Notification table | message/payload fields | Stores user notifications. | No direct update | Old notifications may still show the draft number if they were created before formalization. New notifications should use the formal number after the transition. |
| Search / export / PDF consumers | read `incident_number` | Display or export the Near Miss number. | Indirectly affected | These areas will show the formal number automatically after `incident_number` changes. Existing generated PDFs/files should not be renamed automatically. |

## Important Technical Point

Do not simply remove the text `DRAFT-`.

If only the prefix is removed:

```text
DRAFT-YCF/2026/T008
```

would become:

```text
YCF/2026/T008
```

That is still not a clean formal number because it keeps the `T` draft marker.

The safer approach is to use the existing formal number allocation logic, which produces:

```text
YCF/2026/008
```

## Safe Implementation Plan

1. Keep the draft number while the Near Miss is still under vessel-side review.

2. Detect the transition where the Near Miss state becomes:

```text
READY_FOR_OFFICE_COMMENTS
```

3. At that transition, check the current `incident_number`.

4. If `incident_number` starts with `DRAFT-`, allocate a formal number using the existing formal number allocator.

5. The formal number must remove both the `DRAFT-` prefix and the `T` draft marker. For example, `DRAFT-YCF/2026/T008` must become `YCF/2026/008`, not `YCF/2026/T008`.

6. Save the state change and number change in the same database transaction.

7. If the number is already formal, do nothing. This keeps the operation idempotent and avoids generating a second number on retry.

8. Apply this in all flows that can enter `READY_FOR_OFFICE_COMMENTS`, including:

- Normal vessel-side submit to office.
- Rework resubmit that goes back to office.
- Master-created Near Miss records that are created directly in office-ready state, if that route is intended to follow the same rule.

## Existing Data Handling

Existing Near Miss rows that are already in `READY_FOR_OFFICE_COMMENTS` or later states and still have `DRAFT-` numbers should not be changed with a simple SQL `REPLACE`.

If old records also need correction, handle them as a separate controlled backfill:

- Dry-run first and list affected rows.
- Use the same formal number allocator per vessel and year.
- Update rows one by one inside transactions.
- Preserve audit history and avoid duplicate numbers.

## Documentation Updates Required If Implemented

The implementation should update these documents in the same change set as the code and tests.

| Document | Content to update |
| --- | --- |
| `safety_ssot/VIMS-SAFETY-MODULE-SSOT.md` | Add or supersede the numbering decision for Near Miss: vessel-side Near Miss keeps `DRAFT-{VslCode}/{YYYY}/T{nnn}` until office submission, then receives a formal Near Miss number. State clearly whether Near Miss uses the shared Incident sequence or a separate `NM-{VslCode}/{YYYY}/{NNN}` sequence. |
| `safety_docsuite/PRD.md` | Update the Near Miss feature section to state that a Near Miss sent to office must no longer display a draft reference. Add the final expected format and clarify that both `DRAFT-` and the `T` draft marker are removed from the final number. |
| `safety_docsuite/APP_FLOW.md` | Update the Near Miss vessel review / submit-to-office flow. The transition to `READY_FOR_OFFICE_COMMENTS` should say it assigns the formal Near Miss number in the same transaction as the state change. |
| `safety_docsuite/BACKEND_STRUCTURE.md` | Update the `vims_safety_incident.incident_number` description and Near Miss endpoint behavior. Mention that `incident_number` remains the only persisted number column, `record_type='NEAR_MISS'` scopes the rule, and no new table/column is required. |
| `safety_docsuite/VALIDATION_RULES.md` | Add the validation rule: when a Near Miss enters `READY_FOR_OFFICE_COMMENTS`, the final number must not start with `DRAFT-` and must not contain the `T` draft marker. Also state the operation must be idempotent. |
| `safety_docsuite/USER_GUIDE.md` | Add plain user-facing wording: Near Miss shows as draft while under vessel review; once submitted to office it gets the final official number automatically. |
| `safety_docsuite/IMPLEMENTATION_PLAN.md` | Add an append-only amendment if the implementation changes the formal numbering contract or includes a data backfill for existing Near Miss records. |
| `crs/CR-###.md` | Required before implementation if this becomes a Tier 2 or Tier 3 change. Record the decision, affected domains, doc cascade, tests, and any backfill plan. |
| `Docs/progress.txt` | Add the Maintain Mode progress entry after implementation. |

Do not update historical logs, old notifications, or already generated PDF files only for cosmetic number changes unless a separate history rewrite is explicitly approved.

## Expected Effect

User-facing effect:

- Vessel-side draft Near Miss continues to show `DRAFT-...`.
- Once sent to office, the Near Miss shows a formal number without `DRAFT-`.
- The Near Miss list and detail pages should automatically show the updated number because they already read `incident_number`.

Database effect:

- No new table is required.
- No new column is required.
- Only `vims_safety_incident.incident_number` changes for the affected Near Miss row.
- `vims_safety_incident.state` continues to drive the workflow timing.

Historical effect:

- Old logs, old notifications, and already generated files may still contain the old draft number.
- This is acceptable unless a separate history rewrite/backfill is explicitly approved.

## Regression Tests Required If Implemented

- Near Miss created by vessel remains `DRAFT-...` while in vessel review.
- Submitting to office changes state to `READY_FOR_OFFICE_COMMENTS` and assigns a formal number.
- Duplicate submit/retry does not allocate a second formal number.
- Rework resubmit to office also formalizes the number.
- Already formal numbers remain unchanged.
- Near Miss list/detail UI shows the formal number after transition.
