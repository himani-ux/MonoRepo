# Candidate — golden simulator brain output for bundle p1 (P1 x golden TEST_SURFACE)

## JOURNEY-CANDIDATE — "Ops user abandons after two failed retries on a schema error"
origin:          SIMULATOR
persona:         P1 (Operations User)
goal:            process uploaded documents day to day
priority:        P2
covers:          invoices_list
oracle_surface:  UI
negative_states: ERROR
steps:
  1. land on /invoices, click "Upload invoice" (misbehavior: uploads-wrong-file-first)
  2. observe ERROR state via testid=upload-error after the first upload
  3. retry the upload once more, same malformed file out of habit (misbehavior: double-clicks-submit)
  4. ERROR persists; patience_budget (2) exhausted — abandon, leave /invoices
oracle:          testid=upload-error remains visible AND no row reaches SUCCESS in testid=invoice-status after 2 attempts
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

```json field_sources
{
  "goal":   { "from": "SSOT", "ref": "persona P1 goal" },
  "steps":  { "from": "RUN",  "ref": "path actually driven" },
  "oracle": { "from": "RUN",  "ref": "outcome actually observed" }
}
```

## SIM-TRACE
  - persona: P1
  - goal: process uploaded documents day to day
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 2
  - path: land on /invoices, click role=button[name="Upload invoice"]
  - path: upload a file, observe testid=upload-error (ERROR state)
  - path: retry upload once more without changing the file
  - stuck_point: no visible affordance telling the persona WHY the file was rejected before retrying
  - stuck_point: abandoned at patience_budget (2) with the ERROR still on screen
