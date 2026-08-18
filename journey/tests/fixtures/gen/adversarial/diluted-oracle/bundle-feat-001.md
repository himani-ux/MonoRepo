# Bundle: FEAT-001

## PRD Source

## FEAT-001 — "Invoice upload"
priority: P0
covers_flows: AFJ-001
user_story: As an ops user, I upload an invoice CSV and see it accepted.
acceptance_criteria:
  - AC-1: a valid CSV is accepted and shows status=ACCEPTED
  - AC-2: the file appears in the invoice list immediately after upload
edge_cases:
  - malformed CSV is rejected with row-level error messages shown inline



## APP_FLOW Source

### AFJ-001 — "Corrected invoice upload"
covers_features: FEAT-001
steps:
  1. land on /invoices (state: EMPTY)
  2. upload malformed.csv -> schema_error displayed inline
  3. fix the CSV locally, re-upload corrected.csv
  4. observe status=ACCEPTED in the invoice list
states: [EMPTY, ERROR, SUCCESS]



## Persona Context

## Personas

### P1 — Operations User
A back-office ops user who processes uploaded documents day to day.
Cares about reliability: a failure must be clearly actionable (not
silently lost) so they can correct and retry without support escalation.

### P2 — Finance Reviewer
A finance-team member who audits accepted documents for compliance.
Needs clear audit trails and at-a-glance status visibility across all
submitted documents.

SCHEMA: journey/JOURNEY_MAP.template.md
