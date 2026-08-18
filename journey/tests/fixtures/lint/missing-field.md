# JOURNEY_MAP — lint fixture: missing required field (goal)

## JOURNEY-001 — "missing-field probe: goal is absent"
origin:          PERSONA
persona:         test persona
priority:        P1
covers:          FEAT-001
flows:           AF-1
oracle_surface:  UI
negative_states: error_state
data_fixtures:
steps:
  1. navigate to page
  2. inject error_state condition
oracle:          verify outcome
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
