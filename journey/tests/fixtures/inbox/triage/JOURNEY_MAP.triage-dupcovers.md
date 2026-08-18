# JOURNEY_MAP — intent SSOT (fixture, triage tests)

## JOURNEY-600 — "Existing journey with a single covers token"
origin:          PERSONA
persona:         P1 (careful ops user)
goal:            existing goal text for the repeated-token dedup case
priority:        P0
covers:          FEAT-001
flows:           []
oracle_surface:  UI
negative_states: dupcovers_error
data_fixtures:   []
steps:
  1. land on /dupcovers
  2. dupcovers_error happens
  3. recover
oracle:          repeated-token oracle text
evidence:        []
test:            tests/journeys/journey-600.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
