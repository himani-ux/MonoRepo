# tests/journeys/ convention

The contract for deterministic journey tests in the KLOSS Journey Validation layer.

## Location & mapping
- **All deterministic journey tests live under `tests/journeys/`.** One spec file per journey:
  `tests/journeys/journey-<NNN>.spec.<ext>`.
- **Each journey test file maps to exactly one `JOURNEY-ID`** through the `test:` field in
  `JOURNEY_MAP.md`. The `test:` value of a journey must equal `tests/journeys/<that spec file>`.
- **Orphan files under `tests/journeys/` are rejected** by `check-journeys.sh`: any spec that no
  journey's `test:` field points to (or one pointed to by more than one journey) fails the gate.

## What journey tests are — and are not
- Journey tests are **deterministic gates**, not simulator runs. They are scripted, repeatable, and
  produce a stable pass/fail. The CI-owned ledger records their runtime result; CI is the only writer
  of that runtime truth.
- **Runtime truth is never stored in tests or in `JOURNEY_MAP.md`.** `ci_status`, `last_run`,
  `ci_run_id`, `ci_artifact`, and `failure_summary` live only in the CI-owned ledger
  (`JOURNEY_STATUS.json`). `check-journey-authority.sh` rejects any attempt to put them in the map.
- The runner that executes these specs is declared once as `JOURNEY_RUNNER` in the project's
  tech-stack file and resolved by `journey-runner-resolve.sh` — it is the only platform-specific piece.

## Out of scope for Increment 1
The **simulator, persona, reality, and blind authoring** engines are **later increments, not Task 7**.
Increment 1 ships only the deterministic-gate skeleton (map intent, out-of-band ledger, and the gates
that reconcile them). Journey tests here are hand-seeded fixtures; automated discovery/authoring comes later.
