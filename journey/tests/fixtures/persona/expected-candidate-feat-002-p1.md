# Candidate — golden persona generator output for bundle feat-002-p1

## JOURNEY-CANDIDATE — "Ops user refreshes mid-retry of a rejected invoice"
origin:          PERSONA
persona:         P1 (Operations User)
goal:            correct and re-upload a rejected invoice despite refreshing during the pending retry
priority:        P1
covers:          FEAT-002
flows:           AFJ-002
oracle_surface:  UI
negative_states: REJECTED
data_fixtures:
steps:
  1. land on /invoices with an existing REJECTED row
  2. click Retry on the rejected row
  3. upload a corrected version of the file, refreshing while it is pending (misbehavior: refreshes-during-pending)
  4. observe the status transition: REJECTED -> ACCEPTED
oracle:          a corrected re-upload replaces the rejected entry AND the status transitions from REJECTED to ACCEPTED
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []

```json field_sources
{
  "goal":            { "from": "PRD",      "ref": "FEAT-002 user_story", "quote": "As an ops user, I can correct and re-upload a rejected invoice." },
  "oracle":          { "from": "PRD",      "ref": "FEAT-002 AC-1/AC-2",  "quote": "a corrected re-upload replaces the rejected entry; the status transitions from REJECTED to ACCEPTED" },
  "steps":           { "from": "APP_FLOW", "ref": "AFJ-002 steps 1-4",   "quote": "land on /invoices with an existing REJECTED row ... observe the status transition: REJECTED -> ACCEPTED" },
  "negative_states": { "from": "APP_FLOW", "ref": "AFJ-002 states (REJECTED)", "quote": "REJECTED", "generated_minimal": false },
  "persona":         { "from": "SSOT",     "ref": "persona P1 — Operations User" }
}
```
