# JOURNEY_MAP — intent SSOT (fixture, triage tests)

## JOURNEY-999 — "Broken map entry (missing priority)"
origin:          PERSONA
persona:         P1 (careful ops user)
goal:            this block is missing its priority field on purpose
covers:          FEAT-999
flows:           []
oracle_surface:  UI
negative_states: broken_error
data_fixtures:   []
steps:
  1. land on /broken
  2. broken_error happens
oracle:          recovered=true
evidence:        []
test:            tests/journeys/journey-999.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
