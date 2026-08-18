# JOURNEY_MAP — lint fixture: invalid enum value (priority: P9)

## JOURNEY-001 — "bad-enum probe: priority out of range"
origin:          PERSONA
persona:         test persona
goal:            accomplish the goal
priority:        P9
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
