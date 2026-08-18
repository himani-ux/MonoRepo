# JOURNEY-EXTRACTED
extraction_commit: 1111111111111111111111111111111111111111
manifest_sha256:   0000000000000000000000000000000000000000000000000000000000000000

## EXTRACTED-1 — "Invoice resubmission after a schema-error rejection"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [C]
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

## EXTRACTED-2 — "Login screen reachable directly (screen-anchored covers)"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [C]
origin:              EXTRACTED
persona:             any user
goal:                reach the login screen
priority:            P2
covers:              SCR-login
flows:               []
oracle_surface:      UI
negative_states:     bad_credentials
steps:
  1. land on /login
  2. submit valid credentials
oracle:              a session cookie is set and the app redirects off /login
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/routes/auth.ts:12 — "router.get('/login', renderLogin)"

## EXTRACTED-3 — "Checkout flow, covered via a flows: AFJ token (no covers: screen name)"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [C]
origin:              EXTRACTED
persona:             shopper
goal:                complete checkout
priority:            P2
covers:              FEAT-099
flows:               AFJ-002
oracle_surface:      UI+API
negative_states:     payment_declined
steps:
  1. land on /checkout
  2. submit payment
oracle:              order status=CONFIRMED
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/routes/checkout.ts:9 — "router.post('/checkout', submitPayment)"
