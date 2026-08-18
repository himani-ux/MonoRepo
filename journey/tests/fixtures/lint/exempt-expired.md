# JOURNEY_MAP — lint fixture (negative): EXEMPT journey with an EXPIRED exemption
# The exemption metadata keywords are all present, but expiry is in the PAST, so
# lint must FAIL (an expired waiver may not silently keep a journey exempt).

## JOURNEY-001 — "exempt-expired probe: past-dated exemption must fail lint"
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
exemptions:      [{tag: DOCS-EXEMPT, reason: not yet testable, owner: alice, expiry: 2000-01-01, reviewer: bob}]
