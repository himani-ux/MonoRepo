# JOURNEY_MAP — intent SSOT (fixture)

## JOURNEY-001 — "Recover from a rejected invoice upload"
origin:          PERSONA
persona:         P2 (impatient ops user)
goal:            upload a corrected invoice after the first was rejected, and see it accepted
priority:        P0
covers:          FEAT-012
flows:           AF-3
oracle_surface:  UI+API
negative_states: schema_error, retry_upload
data_fixtures:   malformed.csv, corrected.csv
steps:
  1. land on /invoices            (state: AUTHENTICATED, EMPTY list)
  2. upload malformed.csv          → inject schema_error
  3. fix file, re-upload corrected.csv
  4. observe retry_upload → ACCEPTED
oracle:          row status=ACCEPTED AND GET /invoices returns the row
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
