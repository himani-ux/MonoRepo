# JOURNEY_MAP — lint fixture (negative): runner not in the allowed enum
# Review I4: an invented runner value previously survived every gate.

## JOURNEY-001 — "bad runner probe"
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
oracle:          row status=ACCEPTED
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          cypress
author_status:   WRITTEN
exemptions:      []
