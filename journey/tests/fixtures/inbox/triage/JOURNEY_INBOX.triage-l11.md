# JOURNEY-INBOX

## INBOX-1 — "candidate 1"
promotion_status: ACCEPTED
origin:          SIMULATOR
persona:         P2 (impatient ops user)
goal:            goal text for candidate 1
priority:        P1
covers:          FEAT-960
oracle_surface:  UI
negative_states: err_1
steps:
  1. land on /page-1
  2. err_1 happens
  3. recover
oracle:          clean oracle text
evidence:        traces/inbox-1-sim.zip
test:            tests/journeys/journey-inbox-1.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P2
  - goal: goal text for candidate 1
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 2
  - path: land on /page-1
  - evidence: traces/inbox-1-sim.zip

## INBOX-2 — "L11 attack: duplicate promotion_status lines"
promotion_status: PROPOSED
promotion_status: ACCEPTED
origin:          SIMULATOR
persona:         P3 (low patience power user)
goal:            goal text for the attack entry
priority:        P2
covers:          FEAT-961
oracle_surface:  UI
negative_states: err_2
steps:
  1. land on /page-2
  2. err_2 happens
  3. recover
oracle:          attack oracle text
evidence:        traces/inbox-2-sim.zip
test:            tests/journeys/journey-inbox-2.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P3
  - goal: goal text for the attack entry
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 2
  - path: land on /page-2
  - evidence: traces/inbox-2-sim.zip
