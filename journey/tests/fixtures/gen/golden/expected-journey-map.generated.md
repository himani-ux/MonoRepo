# JOURNEY_MAP (generated) — golden expected output for the Task-3 doc-set
#
# Frozen deterministic contract: the hand-written *expected* generator output for
# journey/tests/fixtures/gen/{SSOT,PRD,APP_FLOW}.md. Later generative tasks must
# reproduce this shape. Every journey is origin=DERIVED, author_status=UNWRITTEN.
# Runtime truth (ci_status/last_run/...) never appears here — it lives only in the
# CI-owned ledger.

## JOURNEY-101 — "Corrected invoice upload accepted"
origin:          DERIVED
persona:         P1 (Operations User)
goal:            upload an invoice CSV and, after correcting a rejected file, see it accepted
priority:        P0
covers:          FEAT-001
flows:           AFJ-001
oracle_surface:  UI
negative_states: schema_error
data_fixtures:
steps:
  1. land on /invoices (state: EMPTY)
  2. upload malformed.csv -> schema_error displayed inline
  3. fix the CSV locally, re-upload corrected.csv
  4. observe status=ACCEPTED in the invoice list
oracle:          the row shows status=ACCEPTED AND the file appears in the invoice list immediately after upload
evidence:        []
test:            tests/journeys/journey-101.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []

## JOURNEY-102 — "Invoice retry after rejection"
origin:          DERIVED
persona:         P1 (Operations User)
goal:            correct and re-upload a rejected invoice and see it accepted
priority:        P1
covers:          FEAT-002
flows:           AFJ-002
oracle_surface:  UI
negative_states: REJECTED
data_fixtures:
steps:
  1. land on /invoices with an existing REJECTED row
  2. click Retry on the rejected row
  3. upload a corrected version of the file
  4. observe the status transition: REJECTED -> ACCEPTED
oracle:          a corrected re-upload replaces the rejected entry AND the status transitions from REJECTED to ACCEPTED
evidence:        []
test:            tests/journeys/journey-102.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
