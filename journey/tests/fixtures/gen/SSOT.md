# KLOSS Framework — Step-1 SSOT

## Personas

### P1 — "Operations User"
goal:             process uploaded documents day to day
context:          back-office, high volume, interrupted often
tech_savviness:   medium
error_tendency:   high
patience_budget:  2
known_misbehaviors:
  - uploads-wrong-file-first
  - double-clicks-submit
  - refreshes-during-pending

A back-office ops user who processes uploaded documents day to day.
Cares about reliability: a failure must be clearly actionable (not
silently lost) so they can correct and retry without support escalation.

### P2 — "Finance Reviewer"
goal:             audit accepted documents for compliance
context:          finance team, monthly review cycles, methodical
tech_savviness:   high
error_tendency:   low
patience_budget:  4
known_misbehaviors: [none: methodical reviewer; follows the documented flow]

A finance-team member who audits accepted documents for compliance.
Needs clear audit trails and at-a-glance status visibility across all
submitted documents.

## System Context

The document-upload pipeline accepts CSV files, validates them against
a schema, and surfaces errors inline so the ops user can correct and
retry without leaving the page.  Accepted documents enter an immutable
audit log visible to the finance reviewer.
