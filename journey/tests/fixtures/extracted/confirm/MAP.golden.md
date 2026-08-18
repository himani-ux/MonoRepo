# JOURNEY_MAP — journey-extracted-confirm_test.sh golden fixture (four
# pre-existing origins, ids 101/201/301/401 — collision-target fixtures).

## JOURNEY-101 — "A derived journey"
origin:          DERIVED
persona:         any user
goal:            do the derived thing
priority:        P2
covers:          FEAT-100
flows:           []
oracle_surface:  UI
negative_states: derived_error
data_fixtures:   []
steps:
  1. do the derived thing
  2. trigger derived_error
oracle:          the derived-journey success signal
evidence:        []
test:            tests/journeys/journey-101.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []

## JOURNEY-201 — "A persona journey"
origin:          PERSONA
persona:         P1 (careful user)
goal:            do the persona thing
priority:        P2
covers:          FEAT-100
flows:           []
oracle_surface:  UI
negative_states: persona_error
data_fixtures:   []
steps:
  1. do the persona thing
  2. trigger persona_error
oracle:          the persona-journey success signal
evidence:        []
test:            tests/journeys/journey-201.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []

## JOURNEY-301 — "A simulator journey"
origin:          SIMULATOR
persona:         any user
goal:            do the simulator thing
priority:        P2
covers:          FEAT-100
flows:           []
oracle_surface:  UI
negative_states: simulator_error
data_fixtures:   []
steps:
  1. do the simulator thing
  2. trigger simulator_error
oracle:          the simulator-journey success signal
evidence:        []
test:            tests/journeys/journey-301.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []

## JOURNEY-401 — "A reality journey"
origin:          REALITY
persona:         any user
goal:            do the reality thing
priority:        P2
covers:          FEAT-100
flows:           []
oracle_surface:  UI
negative_states: reality_error
data_fixtures:   []
steps:
  1. do the reality thing
  2. trigger reality_error
oracle:          the reality-journey success signal
evidence:        bug-1234
test:            tests/journeys/journey-401.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
