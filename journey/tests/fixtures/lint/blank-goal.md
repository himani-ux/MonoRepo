# JOURNEY_MAP — lint fixture: blank goal VALUE (required content field present but empty)

## JOURNEY-001 — "blank-goal probe"
origin:          PERSONA
persona:         test persona
goal:
priority:        P0
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
