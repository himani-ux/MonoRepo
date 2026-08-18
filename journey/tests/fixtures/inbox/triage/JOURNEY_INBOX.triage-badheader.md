# Not The Right Header

## INBOX-1 — "irrelevant, header is already broken"
promotion_status: PROPOSED
origin:          SIMULATOR
persona:         P2
goal:            irrelevant
priority:        P1
covers:          FEAT-001
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
  - goal: irrelevant
  - app_build: b1
  - runner: playwright
  - patience_budget: 1
  - path: p1
  - evidence: traces/x.zip
