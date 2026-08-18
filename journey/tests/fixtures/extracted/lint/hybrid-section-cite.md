# JOURNEY-EXTRACTED
extraction_commit: abcdef0123456789abcdef0123456789abcdef01
manifest_sha256:   abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789

## EXTRACTED-1 — "Member books an open class"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [C]
origin:              EXTRACTED
persona:             member
goal:                book an open class successfully
priority:            P2
covers:              FEAT-001
flows:               []
oracle_surface:      UI+API
negative_states:     []
steps:
  1. land on /classes/:id
  2. submit a booking for an open class
oracle:              response status=200 AND body.status == 'BOOKED'
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - docs/FLW.md#Booking — "A member books an open class from the class detail screen."
