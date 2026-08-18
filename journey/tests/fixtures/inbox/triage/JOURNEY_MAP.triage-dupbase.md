# JOURNEY_MAP — intent SSOT (fixture, triage tests)

## JOURNEY-500 — "Existing journey that a candidate will duplicate"
origin:          PERSONA
persona:         P1 (careful ops user)
goal:            existing goal text
priority:        P0
covers:          FEAT-500
flows:           []
oracle_surface:  UI
negative_states: dup_error
data_fixtures:   []
steps:
  1. land on /dup
  2. dup_error happens
  3. recover
oracle:          value=1   AND  stuff=2
evidence:        []
test:            tests/journeys/journey-500.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
