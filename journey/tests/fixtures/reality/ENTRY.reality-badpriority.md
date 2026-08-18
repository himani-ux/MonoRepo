## JOURNEY-1 — "Reality entry with an invalid priority enum"
origin:          REALITY
persona:         P1 (returning customer)
goal:            complete checkout after a coupon apply fails once, without the total drifting
priority:        SUPER
covers:          FEAT-725
flows:           []
oracle_surface:  UI+API
negative_states: coupon_retry_drift
data_fixtures:   []
steps:
  1. land on /checkout with items in cart (state: AUTHENTICATED)
  2. apply coupon CODE10 -> coupon_retry_drift on retry
  3. retry apply
  4. observe total matches server total
oracle:          displayed total=SERVER_TOTAL AND GET /cart returns matching total
evidence:        BUG-4821, incident-2026-07-09.md
test:            tests/journeys/journey-725.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
