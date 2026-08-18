# JOURNEY_MAP — lint fixture: forbidden runtime-truth field (ci_status)

## JOURNEY-001 — "runtime-field probe: ci_status must not appear in map"
origin:          PERSONA
persona:         test persona
goal:            accomplish the goal
priority:        P1
covers:          FEAT-001
flows:           AF-1
oracle_surface:  UI
ci_status:       GREEN
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
