# Audit Status Reply For Senior

Date: 2026-08-17

## 1. Live URL And Access

Live VIMS URL:

```text
https://vims.ksmpms.com
```

Current deployment status:

- Audit module code is not deployed on the live URL yet.
- Because of that, there is currently no live Audit URL/screen available for user testing.
- The existing live VIMS login continues to work for already deployed modules only.
- Audit access can be validated only after the Audit code is deployed to live.

Access users for local/development Audit journey validation:

| Role | Username | Note |
|---|---|---|
| DPA | `harman.s` | Password to be shared separately through a secure channel. |
| Master | `KSM0225` | Master account for Aarya. Password to be shared separately through a secure channel. |
| Superintendent/PIC | `Aman.Oberoi` | Password to be shared separately through a secure channel. |
| Fleet Manager | `Prince. S` | Use if available. Password to be shared separately through a secure channel. |

Current Audit build status:

- Audit is available in local/development code.
- Journey testing was run against the local/development build, not the live deployment.
- Different Audit journeys need different actors, such as DPA/SEQ, Lead Auditor/Conductor, Master, and Superintendent/PIC.

Local/development routes already built:

| Screen | Route |
|---|---|
| Audit Plan Register | `/audit/plans` |
| Register Audit | `/inspections/new` |
| Audit Detail | `/audit/audits/:auditId` |
| Checklist | `/audit/audits/:auditId/checklist` |
| NC Wizard | `/audit/findings/:findingId/nc/wizard` |
| NC Closure | `/audit/findings/:findingId/nc` |
| Observation Closure | `/audit/findings/:findingId/obs` |
| External Audit Register | `/audit/external/new` |

## 2. Current Phase 5 Journey Result

Latest local journey run result:

```text
8 passed
5 failed
1 skipped
```

Passed journeys:

- JOURNEY-1
- JOURNEY-2
- JOURNEY-4
- JOURNEY-9
- JOURNEY-10
- JOURNEY-11
- JOURNEY-12
- JOURNEY-13

Failed journeys:

- JOURNEY-3
- JOURNEY-5
- JOURNEY-6 under DPA only
- JOURNEY-7
- JOURNEY-8

Skipped journey:

- JOURNEY-14

## 3. SCR-AUD IDs Still Gapped

These are the current SCR-AUD gaps from the local Phase 5 journey run.

| SCR ID | Screen / Area | Current gap | Expected or drift? |
|---|---|---|---|
| `SCR-AUD-2` | Audit Detail | Page opens, but submit, scorecard, acknowledgement, and findings controls are not visible for the tested state/user. | Needs verification. Could be workflow-state or permission mismatch, or missing UI control wiring. |
| `SCR-AUD-4` | NC Closure | NC Closure page opens, but closure record is not found for one journey. Lead Auditor/effectiveness controls are also not visible in another journey. | Needs workflow-state-specific test data and closure-record verification. |
| `SCR-AUD-6` | Observation Closure | Observation Closure page opens, but Observation closure record is not found. | Needs Observation closure child record/state verification. |
| `SCR-AUD-13` | Acting HoD Coverage | Acting HoD assignment screen/route is absent. | Expected gap, not yet built. |

## 4. Not Counted As General Build Gaps

`JOURNEY-6` failed under DPA, but passed when rerun with Superintendent/PIC.

Meaning:

- This is actor-specific.
- It is not currently treated as a general code failure.
- The journey needs the correct user role and workflow state for that step.

## 5. Simple Summary

Register Audit is fixed.

Most already built Audit screens are reachable locally.

The live URL does not have Audit deployed yet, so live Audit access cannot be provided at this stage.

The remaining confirmed not-yet-built screen is:

```text
SCR-AUD-13 - Acting HoD Coverage
```

The remaining failed areas are:

```text
SCR-AUD-2 - Audit Detail controls
SCR-AUD-4 - NC Closure state/record/control availability
SCR-AUD-6 - Observation Closure state/record availability
```

These need to be separated during Phase 5 as:

- expected because the feature/screen is not yet built, or
- real drift because the design says the screen/control should exist but the shipped local build does not expose it correctly.
