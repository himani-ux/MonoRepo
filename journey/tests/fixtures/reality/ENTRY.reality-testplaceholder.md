## JOURNEY-1 — "Reality regression: password reset link expires early"
origin:          REALITY
persona:         P3 (locked-out user)
goal:            reset password using the emailed link before it wrongly expires
priority:        P0
covers:          FEAT-703
flows:           []
oracle_surface:  UI
negative_states: reset_link_early_expiry
data_fixtures:   []
steps:
  1. request password reset (state: UNAUTHENTICATED)
  2. open reset link within 5 minutes -> reset_link_early_expiry rejected
  3. request a new link
  4. observe reset succeeds within the stated validity window
oracle:          password updated AND login succeeds with new password
evidence:        BUG-5011, support-ticket-90144.md
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
