# JOURNEY_MAP (generated) — coverage-gate fixture
# DEFECT: JOURNEY-103 traces to no valid source id (empty covers AND flows) → orphan.

## JOURNEY-101 — "Login to dashboard"
origin:          DERIVED
persona:         end user
goal:            log in and reach the dashboard
priority:        P0
covers:          FEAT-001
flows:           AFJ-001
oracle_surface:  UI
negative_states: auth_error
data_fixtures:
steps:
  1. land on /login (EMPTY)
  2. submit valid credentials
  3. observe dashboard
oracle:          valid credentials are accepted AND the dashboard loads
evidence:        []
test:            tests/journeys/journey-101.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []

## JOURNEY-102 — "Upload a file"
origin:          DERIVED
persona:         ops user
goal:            upload a file and see it accepted
priority:        P1
covers:          FEAT-002
flows:           AFJ-002
oracle_surface:  UI
negative_states: schema_error
data_fixtures:
steps:
  1. land on /upload
  2. choose a file
  3. observe ACCEPTED
oracle:          a valid file is accepted
evidence:        []
test:            tests/journeys/journey-102.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []

## JOURNEY-103 — "Orphan journey with no source anchor"
origin:          DERIVED
persona:         wanderer
goal:            do something untraceable to any FEAT or AFJ
priority:        P1
covers:
flows:
oracle_surface:  UI
negative_states: none
data_fixtures:
steps:
  1. wander around
oracle:          something happens
evidence:        []
test:            tests/journeys/journey-103.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
