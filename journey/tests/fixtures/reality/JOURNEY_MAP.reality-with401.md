# JOURNEY_MAP — intent SSOT (fixture, reality-intake tests)

## JOURNEY-401 — "Pre-existing journey already occupying id 401"
origin:          PERSONA
persona:         P1 (careful ops user)
goal:            pre-existing goal text, unrelated to any intake candidate
priority:        P0
covers:          FEAT-900
flows:           []
oracle_surface:  UI
negative_states: preexisting_error
data_fixtures:   []
steps:
  1. land on /pre-existing
  2. preexisting_error happens
  3. recover
oracle:          preexisting oracle text
evidence:        []
test:            tests/journeys/journey-401.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
