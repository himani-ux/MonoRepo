# JOURNEY-INBOX

## INBOX-1 — "candidate with placeholder test path"
promotion_status: ACCEPTED
origin:          SIMULATOR
persona:         P2 (impatient ops user)
goal:            goal text for placeholder candidate
priority:        P1
covers:          FEAT-701
oracle_surface:  UI
negative_states: err_ph
steps:
  1. land on /page-ph
  2. err_ph happens
  3. recover
oracle:          placeholder oracle text
evidence:        traces/inbox-ph-sim.zip
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P2
  - goal: goal text for placeholder candidate
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 2
  - path: land on /page-ph
  - evidence: traces/inbox-ph-sim.zip

## INBOX-2 — "candidate with concrete test path"
promotion_status: ACCEPTED
origin:          SIMULATOR
persona:         P2 (impatient ops user)
goal:            goal text for concrete-path candidate
priority:        P1
covers:          FEAT-702
oracle_surface:  UI
negative_states: err_concrete
steps:
  1. land on /page-concrete
  2. err_concrete happens
  3. recover
oracle:          concrete oracle text
evidence:        traces/inbox-concrete-sim.zip
test:            tests/journeys/journey-inbox-2.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P2
  - goal: goal text for concrete-path candidate
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 2
  - path: land on /page-concrete
  - evidence: traces/inbox-concrete-sim.zip
