# JOURNEY-INBOX

## INBOX-1 — "pre-existing malformed promoted_as"
promotion_status: ACCEPTED
promoted_as:     not-a-journey-id
origin:          SIMULATOR
persona:         P2
goal:            goal text
priority:        P1
covers:          FEAT-002
oracle_surface:  UI
negative_states: e
steps:
  1. e happens
oracle:          done=true
evidence:        traces/x.zip
test:            tests/journeys/x.spec.ts
runner:          playwright
author_status:   UNWRITTEN
simulator_trace:
  - persona: P2
  - goal: goal text
  - app_build: b1
  - runner: playwright
  - patience_budget: 1
  - path: p1
  - evidence: traces/x.zip
