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
  3. re-upload corrected.csv
  4. observe retry_upload → ACCEPTED
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
  - path: upload malformed.csv
  - path: re-upload corrected.csv
  - stuck_point: hesitated after the schema_error toast
  - evidence: traces/inbox-1-sim.zip

## INBOX-2 — "Persona P3 gives up before completing password reset"
promotion_status: REJECTED
rejected_reason: duplicate of JOURNEY-014, already covers this path
origin:          SIMULATOR
persona:         P3 (low patience power user)
goal:            reset password and log back in
priority:        P2
covers:          FEAT-020
oracle_surface:  UI
negative_states: token_expired
steps:
  1. land on /reset-password
  2. request reset link
  3. token_expired on click
oracle:          error message shown AND resend link available
evidence:        traces/inbox-2-sim.zip
test:            tests/journeys/journey-inbox-2.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P3
  - goal: reset password and log back in
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 2
  - path: land on /reset-password
  - path: request reset link
  - evidence: traces/inbox-2-sim.zip
