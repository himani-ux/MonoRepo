## JOURNEY-1 — "First block in a two-block entry file"
origin:          REALITY
persona:         P1 (returning customer)
goal:            first block goal text
priority:        P0
covers:          FEAT-710
flows:           []
oracle_surface:  UI
negative_states: first_error
data_fixtures:   []
steps:
  1. land on /first
  2. first_error happens
  3. recover
oracle:          first oracle text
evidence:        BUG-6001
test:            tests/journeys/journey-710.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []

## JOURNEY-2 — "Second block in a two-block entry file"
origin:          REALITY
persona:         P1 (returning customer)
goal:            second block goal text
priority:        P0
covers:          FEAT-711
flows:           []
oracle_surface:  UI
negative_states: second_error
data_fixtures:   []
steps:
  1. land on /second
  2. second_error happens
  3. recover
oracle:          second oracle text
evidence:        BUG-6002
test:            tests/journeys/journey-711.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
