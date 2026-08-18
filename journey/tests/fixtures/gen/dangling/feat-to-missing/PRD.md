# Product Requirements Document

## FEAT-001 — "Invoice upload"
priority: P0
covers_flows: AFJ-001
user_story: As an ops user, I upload an invoice CSV and see it accepted.
acceptance_criteria:
  - AC-1: a valid CSV is accepted and shows status=ACCEPTED

## FEAT-005 — "Bulk document export"
priority: P0
covers_flows: AFJ-999
user_story: As an ops user, I can export a batch of documents.
acceptance_criteria:
  - AC-1: a bulk export ZIP is generated with all accepted documents
