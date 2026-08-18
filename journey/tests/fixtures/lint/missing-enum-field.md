# JOURNEY_MAP — lint fixture: missing ENUM field (origin absent)
# Proves a MISSING enum field reports only the missing-field error, not also
# an "invalid enum" error (Task-4 hardening, guarded enum checks).

## JOURNEY-001 — "missing-enum probe: origin field absent"
persona:         test persona
goal:            accomplish the goal
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
