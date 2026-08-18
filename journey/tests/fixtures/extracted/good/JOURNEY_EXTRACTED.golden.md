# JOURNEY-EXTRACTED
extraction_commit: abcdef0123456789abcdef0123456789abcdef01
manifest_sha256:   abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789

## EXTRACTED-1 — "Invoice resubmission after a schema-error rejection"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [C]
origin:              EXTRACTED
persona:             ops user (inferred from the route's auth middleware)
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

## EXTRACTED-2 — "Password reset flow disagreement between doc and code"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [X]
origin:              EXTRACTED
persona:             any authenticated user
goal:                reset a forgotten password
priority:            P2
covers:              FEAT-020
flows:               []
oracle_surface:      UI
negative_states:     token_expired
steps:
  1. land on /reset-password
  2. request reset link
  3. token_expired on click
oracle:              a new reset link is issued after expiry
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/routes/auth.ts:88 — "router.post('/reset-password', issueOneTimeToken)"
  - docs/FLW.md#Password reset

## EXTRACTED-3 — "Booking conflict warning surfaces only after save"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [I]
origin:              EXTRACTED
persona:             receptionist
goal:                book a room without double-booking it
priority:            P2
covers:              FEAT-031
flows:               []
oracle_surface:      UI+API
negative_states:     double_submit
steps:
  1. open the booking form for room 3
  2. submit a booking that conflicts with an existing one
  3. observe no warning until AFTER the save completes -> double_submit
oracle_gap:          what does the booking list show immediately after a conflicting save — a duplicate row, or a rejected insert?
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/routes/bookings.ts:61 — "if (conflict) { warnAfterSave(); }"

## EXTRACTED-4 — "Export-to-CSV button with no observable handler"
needs_human_confirm: true
confirmation_status: REJECTED
rejected_reason:     the cited button has no wired click handler anywhere in the bundle — dead markup, not a real journey
grade:               [G]
origin:              EXTRACTED
persona:             ops user
goal:                export the invoices list to CSV
priority:            P2
covers:              FEAT-014
flows:               []
oracle_surface:      UI
negative_states:     export_error
steps:
  1. land on /invoices
  2. click the "Export CSV" button
oracle:              a CSV file download begins
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/components/InvoicesToolbar.tsx:19 — "<button>Export CSV</button>"

## EXTRACTED-5 — "Invoice resubmission — resolved doc/code conflict, promoted"
needs_human_confirm: true
confirmation_status: CONFIRMED
grade:               [C]
origin:              EXTRACTED
persona:             ops user
goal:                resubmit a corrected invoice and see it accepted, with the API contract confirmed
priority:            P1
covers:              FEAT-014
flows:               []
oracle_surface:      UI+API
negative_states:     schema_error
steps:
  1. land on /invoices
  2. upload malformed.csv -> inject schema_error
  3. re-upload corrected.csv
  4. observe the row transition to ACCEPTED
oracle:              row status=ACCEPTED AND GET /invoices returns the row with updated_at refreshed
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/routes/invoices.ts:47 — "return res.status(200).json({ status: 'ACCEPTED', row })"
  - docs/FLW.md#Invoice resubmission
prior_e2e:           tests/e2e/invoice-resubmit.spec.ts
resolution:          docs/FLW.md#Invoice resubmission claims the response omits the row body; src/routes/invoices.ts:47 (cited above) shows the row IS returned in the 200 response — code is current, doc is stale (predates commit that added the row to the payload). Code wins per Step 0 staleness rules.
resolved_from:       [X]
promoted_as:         JOURNEY-501

## EXTRACTED-6 — "Password reset — documented cooldown after repeated requests has no rate-limit code"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [X]
origin:              EXTRACTED
persona:             any authenticated user
goal:                reset a forgotten password without being silently rate-limited
priority:            P2
covers:              FEAT-020
flows:               []
oracle_surface:      API
negative_states:     rate_limited
steps:
  1. request a password reset link
  2. request it repeatedly in quick succession
oracle_gap:          docs/FLW.md#Password reset documents a cooldown after repeated requests, but no rate-limit code exists anywhere in the reset route — is the cooldown unimplemented, or was it intentionally cut?
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - docs/FLW.md#Password reset
  - search: grep -rFn -- "rateLimit" src
