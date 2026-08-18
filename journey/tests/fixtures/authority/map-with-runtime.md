# JOURNEY_MAP — authority fixture: forbidden runtime-truth field (ci_status)
# This file is a NEGATIVE fixture. Passing it as a MAP arg to
# check-journey-authority.sh must cause the gate to FAIL (exit non-zero)
# because ci_status is a runtime field that must not appear in map files.

## JOURNEY-001 — "runtime-field probe: ci_status must not appear in map"
origin:          PERSONA
persona:         test persona
goal:            accomplish the goal
priority:        P1
covers:          FEAT-001
flows:           AF-1
oracle_surface:  UI
ci_status:       GREEN
negative_states: error_state
data_fixtures:
steps:
  1. navigate to page
  2. inject error_state condition
oracle:          verify outcome
evidence:        []
test:            tests/journeys/journey-001.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
