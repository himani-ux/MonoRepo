# JOURNEY_MAP — lint fixture: declared negative_state not referenced in steps

## JOURNEY-001 — "negstate-no-step probe: schema_error declared but steps do not mention it"
origin:          PERSONA
persona:         test persona
goal:            accomplish the goal
priority:        P1
covers:          FEAT-001
flows:           AF-1
oracle_surface:  UI
negative_states: schema_error
data_fixtures:
steps:
  1. navigate to page
  2. click the submit button
oracle:          verify outcome
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
