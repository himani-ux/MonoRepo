# JOURNEY_MAP — authority fixture: forbidden runtime-truth field in template shape
# This file is a NEGATIVE fixture. Passing it as a MAP arg to
# check-journey-authority.sh must cause the gate to FAIL (exit non-zero)
# because last_run is a runtime field that must not appear in map/template files.

## JOURNEY-000 — "template-shape probe: last_run must not appear in template"
origin:          PERSONA
persona:         template persona
goal:            demonstrate that runtime fields are rejected in template-shaped files
priority:        P1
covers:          FEAT-000
flows:           AF-0
oracle_surface:  UI+API
last_run:        2026-06-22T10:45:00Z
negative_states: error_state
data_fixtures:
steps:
  1. navigate to page
  2. inject error_state condition
oracle:          verify outcome
evidence:        []
test:            tests/journeys/journey-000.spec.ts
runner:          playwright
author_status:   WRITTEN
exemptions:      []
