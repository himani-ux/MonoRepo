# JOURNEY_MAP — lint fixture: blank priority VALUE (required field present but empty)
# Proves a blank required enum field fails as a blank-required-field error WITHOUT
# also emitting an invalid-enum error (the enum check is guarded on non-empty).

## JOURNEY-001 — "blank-priority probe"
origin:          PERSONA
persona:         test persona
goal:            accomplish the goal
priority:
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
