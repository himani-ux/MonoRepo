# Product Requirements Document

## FEAT-001 — "Invoice upload"
priority: P0
covers_flows: AFJ-001
user_story: As an ops user, I upload an invoice CSV and see it accepted.
acceptance_criteria:
  - AC-1: a valid CSV is accepted and shows status=ACCEPTED
  - AC-2: the file appears in the invoice list immediately after upload

## FEAT-002 — "Invoice retry after rejection"
priority: P1
covers_flows: AFJ-002
user_story: As an ops user, I can correct and re-upload a rejected invoice.
acceptance_criteria:
  - AC-1: a corrected re-upload replaces the rejected entry
  - AC-2: the status transitions from REJECTED to ACCEPTED

## FEAT-003 — "Invoice export"
priority: P2
user_story: As a finance reviewer, I can export accepted invoices to CSV.
acceptance_criteria:
  - AC-1: accepted invoices can be downloaded as a CSV export

## FEAT-004 — "Bulk invoice upload"
priority: P0
user_story: As an ops user, I can upload multiple invoices in a single batch.
acceptance_criteria:
  - AC-1: a ZIP of valid CSVs is accepted and each appears in the invoice list
  - AC-2: each entry shows status=ACCEPTED after the batch completes
edge_cases:
  - if any file in the ZIP is malformed, that file is rejected with row-level errors
