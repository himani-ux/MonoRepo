# JOURNEY_MAP — lint fixture: data_fixtures entry does not exist on disk

## JOURNEY-001 — "missing-fixture probe: ghost.csv is declared but not present"
origin:          PERSONA
persona:         test persona
goal:            accomplish the goal
priority:        P1
covers:          FEAT-001
flows:           AF-1
oracle_surface:  UI
negative_states: error_state
data_fixtures:   ghost.csv
steps:
  1. navigate to page
  2. inject error_state condition
oracle:          verify outcome
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
