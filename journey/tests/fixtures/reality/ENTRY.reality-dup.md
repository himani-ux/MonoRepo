## JOURNEY-1 — "Reality regression that duplicates an existing journey"
origin:          REALITY
persona:         P1 (returning customer)
goal:            a regression that turns out to already be covered by JOURNEY-500
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
oracle:          value=1 AND stuff=2
evidence:        BUG-6100, duplicate-report.md
test:            tests/journeys/journey-800.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
