# JOURNEY_MAP — lint fixture: WRITTEN author_status with empty test field

## JOURNEY-001 — "written-empty-test probe: author_status WRITTEN but test field is blank"
origin:          PERSONA
persona:         test persona
goal:            accomplish the goal
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
test:
runner:          playwright
author_status:   WRITTEN
exemptions:      []
