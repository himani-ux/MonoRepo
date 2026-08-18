# JOURNEY-INBOX

## INBOX-1 — "candidate 1"
promotion_status: ACCEPTED
origin:          SIMULATOR
persona:         P2 (impatient ops user)
goal:            goal text for candidate 1
priority:        P1
covers:          FEAT-601
oracle_surface:  UI
negative_states: err_1
steps:
  1. land on /page-1
  2. err_1 happens
  3. recover
oracle:          row status=ACCEPTED AND GET /invoices returns the row
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
covers:          FEAT-602
oracle_surface:  UI
negative_states: err_2
steps:
  1. land on /page-2
  2. err_2 happens
  3. recover
oracle:          error message shown AND resend link available
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
covers:          FEAT-603
oracle_surface:  UI
negative_states: err_3
steps:
  1. land on /page-3
  2. err_3 happens
  3. recover
oracle:          some oracle text
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

## INBOX-4 — "candidate 4"
promotion_status: REJECTED
rejected_reason: duplicate of an existing journey, already covered
origin:          SIMULATOR
persona:         P2 (impatient ops user)
goal:            goal text for candidate 4
priority:        P1
covers:          FEAT-604
oracle_surface:  UI
negative_states: err_4
steps:
  1. land on /page-4
  2. err_4 happens
  3. recover
oracle:          some other oracle text
evidence:        traces/inbox-4-sim.zip
test:            tests/journeys/journey-inbox-4.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P2
  - goal: goal text for candidate 4
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 2
  - path: land on /page-4
  - evidence: traces/inbox-4-sim.zip
