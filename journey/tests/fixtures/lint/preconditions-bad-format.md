# JOURNEY_MAP — lint fixture (negative): preconditions entry missing the colon

## JOURNEY-001 — "preconditions-bad-format probe: entry has no colon separator"
origin:          PERSONA
persona:         P2 (impatient ops user)
goal:            upload a corrected invoice
priority:        P0
covers:          FEAT-012
flows:           AF-3
oracle_surface:  UI
negative_states: schema_error
data_fixtures:
preconditions:
  - auth dev-bridge
steps:
  1. land on /invoices
  2. upload malformed file → inject schema_error
oracle:          row status=ACCEPTED
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
