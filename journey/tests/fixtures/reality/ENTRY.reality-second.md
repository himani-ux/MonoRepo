## JOURNEY-1 — "Reality regression: export CSV truncates rows over 10k"
origin:          REALITY
persona:         P2 (ops analyst)
goal:            export a report with more than 10,000 rows and get every row, not a truncated file
priority:        P1
covers:          FEAT-702
flows:           []
oracle_surface:  UI+API
negative_states: export_row_truncation
data_fixtures:   []
steps:
  1. land on /reports/export (state: AUTHENTICATED, LARGE_DATASET)
  2. request CSV export of 12000 rows -> export_row_truncation observed
  3. re-request export
  4. observe file row count matches source count
oracle:          exported file row_count=12000 AND GET /reports/export/status returns COMPLETE
evidence:        BUG-4902, support-ticket-88213.md
test:            tests/journeys/journey-702.spec.ts
runner:          playwright
author_status:   UNWRITTEN
exemptions:      []
