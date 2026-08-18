extraction_commit: 0000000000000000000000000000000000000000

## JOURNEY-CANDIDATE — "Invoice resubmission after a schema-error rejection"
origin:          EXTRACTED
persona:         ops user (inferred from the route's auth middleware)
goal:            resubmit a corrected invoice after a schema-error rejection
priority:        P2
covers:          FEAT-014
flows:           []
oracle_surface:  UI+API
negative_states: schema_error
grade:           [C]
steps:
  1. land on /invoices
  2. upload malformed.csv -> inject schema_error
  3. re-upload corrected.csv
  4. observe the row transition to ACCEPTED
oracle:          row status=ACCEPTED AND GET /invoices returns the row
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

```json field_sources
{}
```

## EXTRACTION-SOURCES
  - src/routes/invoices.ts:42 — "router.post('/invoices/:id/resubmit', validateSchema, resubmitHandler)"
  - docs/FLW.md#Invoice resubmission
  - search: grep -rFn -- "sendEmail" src/routes/invoices.ts
prior_e2e:       tests/e2e/invoice-resubmit.spec.ts

## JOURNEY-CANDIDATE — "Login screen reachable directly"
origin:          EXTRACTED
persona:         any user
goal:            reach the login screen
priority:        P2
covers:          SCR-login
flows:           []
oracle_surface:  UI
negative_states: bad_credentials
grade:           [C]
steps:
  1. land on /login
  2. submit valid credentials
oracle:          a session cookie is set and the app redirects off /login
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

```json field_sources
{}
```

## EXTRACTION-SOURCES
  - src/routes/auth.ts:12 — "router.get('/login', renderLogin)"
