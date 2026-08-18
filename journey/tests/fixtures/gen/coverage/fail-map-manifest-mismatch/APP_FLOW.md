# APP_FLOW — coverage-gate fixture

## User Journeys

### AFJ-001 — "Login flow"
covers_features: FEAT-001
steps:
  1. land on /login (EMPTY)
  2. submit valid credentials
  3. observe dashboard

### AFJ-002 — "Upload flow"
covers_features: FEAT-002
steps:
  1. land on /upload
  2. choose a file
  3. observe ACCEPTED

### AFJ-003 — "Export flow"
covers_features: FEAT-003
steps:
  1. land on /admin/export
  2. request export
  3. download archive
