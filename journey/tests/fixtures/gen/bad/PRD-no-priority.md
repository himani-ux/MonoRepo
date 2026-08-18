# Product Requirements Document

## FEAT-001 — "Invoice upload"
covers_flows: AFJ-001
user_story: As an ops user, I upload an invoice CSV and see it accepted.
acceptance_criteria:
  - AC-1: a valid CSV is accepted and shows status=ACCEPTED
edge_cases:
  - malformed CSV is rejected with row-level error messages
