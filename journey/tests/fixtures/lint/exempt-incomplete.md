# JOURNEY_MAP — lint fixture: EXEMPT journey with incomplete exemption metadata

## JOURNEY-001 — "exempt-incomplete probe: exemptions missing owner, expiry, reviewer"
origin:          PERSONA
persona:         test persona
goal:            accomplish the goal
priority:        P1
covers:          FEAT-001
flows:           AF-1
oracle_surface:  UI
negative_states:
data_fixtures:
steps:
  1. navigate to page
  2. submit form
oracle:          verify outcome
evidence:        []
test:
runner:          playwright
author_status:   EXEMPT
exemptions:      [{tag: DOCS-EXEMPT, reason: docs not ready yet}]
