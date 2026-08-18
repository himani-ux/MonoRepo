# JOURNEY-EXTRACTED
extraction_commit: 1234567890123456789012345678901234567890
manifest_sha256:   0000000000000000000000000000000000000000000000000000000000000000

## EXTRACTED-10 — "First confirmed candidate"
needs_human_confirm: true
confirmation_status: CONFIRMED
grade:               [C]
origin:              EXTRACTED
persona:             ops user
goal:                do the first confirmed thing
priority:            P2
covers:              FEAT-100
flows:               []
oracle_surface:      UI
negative_states:     some_error
steps:
  1. do the first thing
  2. trigger some_error
  3. resolve some_error and observe success
oracle:              the first-candidate success signal is observed
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/first.ts:1 — "export function first() {}"

## EXTRACTED-11 — "Second confirmed candidate"
needs_human_confirm: true
confirmation_status: CONFIRMED
grade:               [C]
origin:              EXTRACTED
persona:             ops user
goal:                do the second confirmed thing
priority:            P2
covers:              FEAT-200
flows:               []
oracle_surface:      API
negative_states:     other_error
steps:
  1. do the second thing
  2. trigger other_error
  3. resolve other_error and observe success
oracle:              the second-candidate success signal is observed
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/second.ts:1 — "export function second() {}"

## EXTRACTED-12 — "A pending candidate, untouched by confirm"
needs_human_confirm: true
confirmation_status: PENDING
grade:               [C]
origin:              EXTRACTED
persona:             ops user
goal:                do the pending thing
priority:            P2
covers:              FEAT-100
flows:               []
oracle_surface:      UI
negative_states:     pending_error
steps:
  1. do the pending thing
  2. trigger pending_error
oracle:              the pending-candidate success signal
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/pending.ts:1 — "export function pending() {}"

## EXTRACTED-13 — "A rejected candidate, untouched by confirm"
needs_human_confirm: true
confirmation_status: REJECTED
rejected_reason:     dead markup, not a real journey
grade:               [G]
origin:              EXTRACTED
persona:             ops user
goal:                do the rejected thing
priority:            P2
covers:              FEAT-200
flows:               []
oracle_surface:      UI
negative_states:     rejected_error
steps:
  1. do the rejected thing
  2. trigger rejected_error
oracle:              the rejected-candidate success signal
evidence:            []
test:                tests/journeys/journey-<n>.spec.ts
runner:              playwright
author_status:       UNWRITTEN
extraction_sources:
  - src/rejected.ts:1 — "export function rejected() {}"
