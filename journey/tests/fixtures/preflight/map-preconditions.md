# JOURNEY_MAP — preflight fixture: declared preconditions, lint-clean
#
# Two journeys, modeled on journey/tests/fixtures/lint/preconditions-good.md:
# JOURNEY-001 declares auth + env preconditions (the field-run 401 archetype
# — an unconfigured dev-auth bridge and an unset base-URL env var);
# JOURNEY-002 declares data + state preconditions.

## JOURNEY-001 — "preflight probe: auth + env preconditions"
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
  - auth: dev-login-bridge
  - env: UAT_BASE_URL
steps:
  1. land on /invoices
  2. upload malformed file → inject schema_error
oracle:          row status=ACCEPTED
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []

## JOURNEY-002 — "preflight probe: data + state preconditions"
origin:          PERSONA
persona:         P2 (impatient ops user)
goal:            view vessel call schedule
priority:        P1
covers:          FEAT-013
flows:           AF-4
oracle_surface:  UI
negative_states: no_data_error
data_fixtures:
preconditions:
  - data: seeded-vessel-call
  - state: no-open-invoice
steps:
  1. land on /vessel-calls
  2. filter by empty range → inject no_data_error
oracle:          empty-state message shown
evidence:        []
test:            tests/journeys/journey-002.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
