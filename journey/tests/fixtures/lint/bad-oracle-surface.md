# JOURNEY_MAP — lint fixture: invalid oracle_surface value (DB)
# Proves the UI | API | UI+API enum is enforced independently of priority.

## JOURNEY-001 — "bad-oracle-surface probe: oracle_surface out of enum"
origin:          PERSONA
persona:         test persona
goal:            accomplish the goal
priority:        P0
covers:          FEAT-001
flows:           AF-1
oracle_surface:  DB
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
