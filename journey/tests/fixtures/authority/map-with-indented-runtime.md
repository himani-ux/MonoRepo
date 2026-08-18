# JOURNEY_MAP — authority fixture: forbidden runtime-truth field, INDENTED (N-1)
# NEGATIVE fixture. The runtime field key `last_run` is indented (leading
# whitespace). Passing this as a MAP arg to check-journey-authority.sh must FAIL:
# the gate must reject runtime-truth keys regardless of leading indentation,
# consistent with journey-gen-promote.sh's `^[[:space:]]*` scan.

## JOURNEY-001 — "indented runtime-field probe: last_run must not appear in map"
origin:          PERSONA
persona:         test persona
goal:            accomplish the goal
priority:        P1
covers:          FEAT-001
flows:           AF-1
oracle_surface:  UI
  last_run:      2026-06-22T10:45:00Z
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
