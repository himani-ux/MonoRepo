# JOURNEY-INBOX

## INBOX-1 — "Persona P2 stalls on invoice re-upload after schema error"
promotion_status: PROPOSED
origin:          SIMULATOR
persona:         P2 (impatient ops user)
goal:            upload a corrected invoice after the first was rejected, and see it accepted
priority:        P1
covers:          FEAT-012
oracle_surface:  UI+API
negative_states: schema_error, retry_upload
steps:
  1. land on /invoices
  2. upload malformed.csv → inject schema_error
oracle:          row status=ACCEPTED AND GET /invoices returns the row
evidence:        traces/inbox-1-sim.zip
test:            tests/journeys/journey-inbox-1.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P2
  - goal: upload a corrected invoice after the first was rejected
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 3
  - path: land on /invoices
  - evidence: traces/inbox-1-sim.zip

## INBOX-1 — "A second, smuggled block reusing the same id"
promotion_status: PROPOSED
origin:          SIMULATOR
persona:         P2 (impatient ops user)
goal:            a duplicate id candidate
priority:        P1
covers:          FEAT-013
oracle_surface:  UI+API
negative_states: schema_error
steps:
  1. land on /invoices
oracle:          row status=ACCEPTED
evidence:        traces/inbox-1b-sim.zip
test:            tests/journeys/journey-inbox-1b.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P2
  - goal: a duplicate id candidate
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 3
  - path: land on /invoices
  - evidence: traces/inbox-1b-sim.zip
