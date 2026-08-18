# JOURNEY_MAP — intent SSOT (fixture, reality-intake tests)

## JOURNEY-500 — "Existing journey that a reality entry will duplicate"
origin:          PERSONA
persona:         P1 (careful ops user)
goal:            existing goal text
priority:        P0
covers:          FEAT-800
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
