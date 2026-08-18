## JOURNEY-1 — "Reality entry with literal [] evidence"
origin:          REALITY
persona:         P1 (returning customer)
goal:            complete checkout after a coupon apply fails once, without the total drifting
priority:        P0
covers:          FEAT-723
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
evidence:        []
test:            tests/journeys/journey-723.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
