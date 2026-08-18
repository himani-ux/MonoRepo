# PRD — coverage-gate fixture
# DEFECT: FEAT-002 priority is not one of P0..P3 → PRD_PRIORITY_UNPARSEABLE (fail closed).

## FEAT-001 — "Login"
priority: P0
covers_flows: AFJ-001
user_story: As a user, I log in and reach my dashboard.
acceptance_criteria:
  - AC-1: valid credentials are accepted
  - AC-2: the dashboard loads

## FEAT-002 — "Upload"
priority: HIGH
covers_flows: AFJ-002
user_story: As an ops user, I upload a file and see it accepted.
acceptance_criteria:
  - AC-1: a valid file is accepted

## FEAT-003 — "Bulk export"
priority: P1
covers_flows: AFJ-003
user_story: As an admin, I export all records.
acceptance_criteria:
  - AC-1: an export archive is produced

## FEAT-004 — "Usage analytics"
priority: P2
user_story: As an admin, I view usage charts.
acceptance_criteria:
  - AC-1: charts render
