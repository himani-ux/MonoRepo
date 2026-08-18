# JOURNEY_MAP — lint fixture (negative): oracle_classes token outside {browser, lower}

## JOURNEY-001 — "oracle-classes-bad-token probe: ui is not a valid class token"
origin:          PERSONA
persona:         P2 (impatient ops user)
goal:            upload a corrected invoice
priority:        P0
covers:          FEAT-012
flows:           AF-3
oracle_surface:  UI
negative_states: schema_error
data_fixtures:
steps:
  1. land on /invoices
  2. upload malformed file → inject schema_error
oracle:          row status=ACCEPTED AND GET /invoices returns the row
oracle_classes:  browser AND ui
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
