# Candidate — golden persona generator output for bundle feat-001-p1

## JOURNEY-CANDIDATE — "Ops user double-submits a corrected invoice"
origin:          PERSONA
persona:         P1 (Operations User)
goal:            upload an invoice CSV and see it accepted despite habitual double-clicking
priority:        P0
covers:          FEAT-001
flows:           AFJ-001
oracle_surface:  UI
negative_states: schema_error
data_fixtures:
steps:
  1. land on /invoices (state: EMPTY)
  2. upload malformed.csv -> schema_error displayed inline (misbehavior: uploads-wrong-file-first)
  3. fix the CSV locally, re-upload corrected.csv, clicking submit twice (misbehavior: double-clicks-submit)
  4. observe status=ACCEPTED in the invoice list
oracle:          the row shows status=ACCEPTED AND the file appears in the invoice list immediately after upload
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []

```json field_sources
{
  "goal":            { "from": "PRD",      "ref": "FEAT-001 user_story", "quote": "As an ops user, I upload an invoice CSV and see it accepted." },
  "oracle":          { "from": "PRD",      "ref": "FEAT-001 AC-1/AC-2",  "quote": "a valid CSV is accepted and shows status=ACCEPTED; the file appears in the invoice list immediately after upload" },
  "steps":           { "from": "APP_FLOW", "ref": "AFJ-001 steps 1-4",   "quote": "land on /invoices (state: EMPTY) ... observe status=ACCEPTED in the invoice list" },
  "negative_states": { "from": "APP_FLOW", "ref": "AFJ-001 step 2 (ERROR state)", "quote": "schema_error displayed inline", "generated_minimal": false },
  "persona":         { "from": "SSOT",     "ref": "persona P1 — Operations User" }
}
```
