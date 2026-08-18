# Candidate — golden simulator brain output for bundle p2 (P2 x golden TEST_SURFACE)

## JOURNEY-CANDIDATE — "Finance reviewer stalls on a transient error before the audit list settles"
origin:          SIMULATOR
persona:         P2 (Finance Reviewer)
goal:            audit accepted documents for compliance
priority:        P2
covers:          invoices_list
oracle_surface:  UI+API
negative_states: ERROR
steps:
  1. land on /invoices, open role=table[name="Invoices"] to review accepted rows
  2. query GET /invoices, observe a transient ERROR on first load
  3. retry via role=button[name="Retry"], observe testid=invoice-list settle to SUCCESS
  4. cross-check testid=invoice-status against the audit trail expectation
oracle:          testid=invoice-list reaches SUCCESS AND GET /invoices returns the row set the reviewer expects
evidence:        []
test:            tests/journeys/journey-<n>.spec.ts
runner:          playwright
author_status:   UNWRITTEN

```json field_sources
{
  "goal":   { "from": "SSOT", "ref": "persona P2 goal" },
  "steps":  { "from": "RUN",  "ref": "path actually driven" },
  "oracle": { "from": "RUN",  "ref": "outcome actually observed" }
}
```

## SIM-TRACE
  - persona: P2
  - goal: audit accepted documents for compliance
  - app_build: build-2026-07-10
  - runner: playwright
  - patience_budget: 4
  - path: land on /invoices, open role=table[name="Invoices"]
  - path: observe a transient ERROR on first load
  - path: click role=button[name="Retry"], observe testid=invoice-list settle to SUCCESS
  - stuck_point: brief hesitation on whether the ERROR meant data loss before retrying
  - evidence: traces/p2-audit-retry.png
