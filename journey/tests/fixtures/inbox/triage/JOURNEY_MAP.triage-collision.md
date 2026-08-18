# JOURNEY_MAP — intent SSOT (fixture, triage tests)

## JOURNEY-301 — "Pre-existing journey occupying id 301"
origin:          PERSONA
persona:         P1 (careful ops user)
goal:            do the thing this map already knows about
priority:        P0
covers:          FEAT-900
flows:           []
oracle_surface:  UI
negative_states: preexisting_error
data_fixtures:   []
steps:
  1. land on /existing
  2. preexisting_error happens
  3. recover
oracle:          recovered=true
evidence:        []
test:            tests/journeys/journey-301.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
