# JOURNEY_MAP — lint fixture: empty negative_states on non-exempt journey

## JOURNEY-001 — "empty-negstates probe: non-exempt journey with blank negative_states"
origin:          PERSONA
persona:         test persona
goal:            accomplish the goal
priority:        P1
covers:          FEAT-001
flows:           AF-1
oracle_surface:  UI
negative_states:
data_fixtures:
steps:
  1. navigate to page
  2. submit form
oracle:          verify outcome
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
