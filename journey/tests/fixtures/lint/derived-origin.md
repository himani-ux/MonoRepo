# JOURNEY_MAP — lint fixture: DERIVED origin accepted
# Proves that origin=DERIVED (generated from canonical docs) passes lint.

## JOURNEY-001 — "derived-origin probe: doc-derived journey accepted by lint"
origin:          DERIVED
persona:         onboarding user
goal:            complete account setup from the generated walkthrough
priority:        P1
covers:          FEAT-001
flows:           AF-1
oracle_surface:  UI
negative_states: setup_error
data_fixtures:
steps:
  1. navigate to /onboarding
  2. inject setup_error condition
  3. observe error banner displayed
oracle:          error banner is visible and setup_error is surfaced
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
