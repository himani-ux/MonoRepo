# JOURNEY_MAP — persona golden fixture

## JOURNEY-201 — "Ops user double-submits a corrected invoice"
origin:          PERSONA
persona:         P1 (Operations User)
goal:            upload an invoice CSV and see it accepted despite habitual double-clicking
priority:        P0
covers:          FEAT-001
flows:           AFJ-001
oracle_surface:  UI
negative_states: schema_error
data_fixtures:
steps:
  1. land on /invoices (state: EMPTY)
  2. upload malformed.csv -> schema_error displayed inline (misbehavior: uploads-wrong-file-first)
  3. fix the CSV locally, re-upload corrected.csv, clicking submit twice (misbehavior: double-clicks-submit)
  4. observe status=ACCEPTED in the invoice list
oracle:          the row shows status=ACCEPTED AND the file appears in the invoice list immediately after upload
evidence:        []
test:            tests/journeys/journey-201.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
