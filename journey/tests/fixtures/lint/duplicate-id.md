# JOURNEY_MAP — lint fixture (negative): DUPLICATE JOURNEY-ID
# Review finding #3: journey_block() returns only the FIRST block per id, so a
# second same-id block was never validated — a smuggling channel. The first
# block here is fully valid; the second is happy-path-only (its declared
# negative_state never appears in a step). Lint must fail on the duplication.

## JOURNEY-001 — "valid first block"
origin:          PERSONA
persona:         P2 (impatient ops user)
goal:            upload a corrected invoice after the first was rejected
priority:        P0
covers:          FEAT-012
flows:           AF-3
oracle_surface:  UI
negative_states: schema_error
data_fixtures:
steps:
  1. land on /invoices
  2. upload malformed file → inject schema_error
  3. re-upload corrected file
oracle:          row status=ACCEPTED
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-001 — "smuggled second block, happy-path only"
origin:          PERSONA
persona:         P2 (impatient ops user)
goal:            upload an invoice
priority:        P0
covers:          FEAT-012
flows:           AF-3
oracle_surface:  UI
negative_states: schema_error
data_fixtures:
steps:
  1. land on /invoices
  2. upload a valid file
oracle:          row status=ACCEPTED
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
