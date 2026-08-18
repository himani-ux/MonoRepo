# JOURNEY_MAP — scope fixture: P0 + P2 journeys

## JOURNEY-001 — "Recover from a rejected invoice upload"
origin:          PERSONA
persona:         P2 (impatient ops user)
goal:            upload a corrected invoice after the first was rejected, and see it accepted
priority:        P0
covers:          FEAT-012
flows:           AF-3
oracle_surface:  UI+API
negative_states: schema_error
data_fixtures:   []
steps:
  1. land on /invoices            (state: AUTHENTICATED, EMPTY list)
  2. upload malformed file         → inject schema_error
  3. fix file, re-upload
  4. observe ACCEPTED
oracle:          row status=ACCEPTED AND GET /invoices returns the row
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-002 — "Search for an invoice by ID"
origin:          PERSONA
persona:         P1 (standard user)
goal:            find a specific invoice by its ID in the UI
priority:        P2
covers:          FEAT-013
flows:           AF-4
oracle_surface:  UI
negative_states: not_found
data_fixtures:   []
steps:
  1. navigate to /invoices
  2. enter unknown ID → not_found message appears
oracle:          not_found message displayed
evidence:        []
test:            tests/journeys/journey-002.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
