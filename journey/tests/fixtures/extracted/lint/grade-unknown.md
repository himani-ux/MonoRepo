# JOURNEY-EXTRACTED
extraction_commit: abcdef0123456789abcdef0123456789abcdef01
manifest_sha256:   abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789

## EXTRACTED-1 — "Invoice resubmission after a schema-error rejection"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [Z]
origin:              EXTRACTED
persona:             ops user
goal:                resubmit a corrected invoice after a schema-error rejection
priority:            P2
covers:              FEAT-014
flows:               []
oracle_surface:      UI+API
negative_states:     schema_error
steps:
  1. land on /invoices
  2. upload malformed.csv -> inject schema_error
  3. re-upload corrected.csv
  4. observe the row transition to ACCEPTED
oracle:              row status=ACCEPTED AND GET /invoices returns the row
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)"
