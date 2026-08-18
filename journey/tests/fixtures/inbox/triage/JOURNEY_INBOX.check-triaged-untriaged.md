# JOURNEY-INBOX

## INBOX-1 — "candidate 1"
promotion_status: PROPOSED
origin:          SIMULATOR
persona:         P2 (impatient ops user)
goal:            goal text for candidate 1
priority:        P1
covers:          FEAT-712
oracle_surface:  UI
negative_states: err_1
steps:
  1. land on /page-1
  2. err_1 happens
  3. recover
oracle:          oracle text a
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

## INBOX-2 — "candidate 2"
promotion_status: ACCEPTED
origin:          SIMULATOR
persona:         P2 (impatient ops user)
goal:            goal text for candidate 2
priority:        P1
covers:          FEAT-713
oracle_surface:  UI
negative_states: err_2
steps:
  1. land on /page-2
  2. err_2 happens
  3. recover
oracle:          oracle text b
evidence:        traces/inbox-2-sim.zip
test:            tests/journeys/journey-inbox-2.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P2
  - goal: goal text for candidate 2
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 2
  - path: land on /page-2
  - evidence: traces/inbox-2-sim.zip

## INBOX-3 — "candidate 3"
promotion_status: PROPOSED
origin:          SIMULATOR
persona:         P2 (impatient ops user)
goal:            goal text for candidate 3
priority:        P1
covers:          FEAT-714
oracle_surface:  UI
negative_states: err_3
steps:
  1. land on /page-3
  2. err_3 happens
  3. recover
oracle:          oracle text c
evidence:        traces/inbox-3-sim.zip
test:            tests/journeys/journey-inbox-3.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P2
  - goal: goal text for candidate 3
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 2
  - path: land on /page-3
  - evidence: traces/inbox-3-sim.zip
