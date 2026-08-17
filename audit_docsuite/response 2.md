Checked locally against `Complete_VIMS`.

1. Five unaccounted screens

Current local route and file status:

| SCR ID | Screen | Status |
|---|---|---|
| `SCR-AUD-9` | DPA failed notifications, `/dpa/notifications/failed` | Built and route-wired locally. Guarded by Audit/DPA permissions. |
| `SCR-AUD-10` | DPA scan validation queue, `/dpa/scan-validation-queue` | Built and route-wired locally. Guarded by `AUDIT_SCAN_VALIDATION`. |
| `SCR-AUD-11` | Audit dashboard, `/audit/dashboard` | Not route-wired locally. This should remain a build gap. |
| `SCR-AUD-12` | Finding detail, `/audit/findings/:id` | Generic finding detail route is not route-wired locally. Only specific finding routes exist: `/audit/findings/:findingId/nc`, `/audit/findings/:findingId/nc/wizard`, and `/audit/findings/:findingId/obs`. |
| `SCR-AUD-14` | Auditor pre-audit dashboard, `/deficiencies` | Built as the reused PSC Deficiency Dashboard route. It is not a dedicated Audit-only screen. |

Impact on passed journeys:

- `JOURNEY-11` can stand only for route reachability of `SCR-AUD-9` and `SCR-AUD-10`, if tested with the correct DPA account and raw evidence.
- `JOURNEY-10` does not prove `SCR-AUD-11`, because the test opens `/audit/plans`, not `/audit/dashboard`.
- `JOURNEY-4` does not prove generic `SCR-AUD-12`, because the test opens the NC wizard route, not `/audit/findings/:id`.
- `JOURNEY-2` does not prove `SCR-AUD-14`, because the current test opens `/inspections/new`, not `/deficiencies`.

So the earlier pass labels should be treated as partial route/surface checks unless the exact required screen, account, and evidence are attached.

2. Accounts used for JOURNEY-2, JOURNEY-4, and JOURNEY-13

The journey helper uses one environment username/password at a time through `JOURNEY_USERNAME` and `JOURNEY_PASSWORD`.

The available result notes do not record which account was used per journey.

Because of that:

- `JOURNEY-2` should not be treated as validated under a Conductor until rerun with the user written into `audit_detail.conductor_user_id`.
- `JOURNEY-4` should not be treated as validated under a Crew/Action Owner until rerun with the assigned action owner record.
- `JOURNEY-13` should not be treated as validated under HoD until rerun with the HoD user resolved through `master_hod_assignment`.

3. JOURNEY-6 retest

Confirmed. `JOURNEY-6` was retested under the correct Superintendent/PIC persona.

Results:

```text
Positive PIC journey with second Superintendent: passed.
Backend negative guard test: passed.
```

So the earlier DPA failure should not be treated as a product bug. DPA is not the intended actor for that journey.

Negative guard evidence:

- Test: `test_lead_auditor_cannot_claim_pic_review_on_own_audit`
- Expected result confirmed: HTTP `403`
- Error confirmed: `LEAD_AUDITOR_PIC_DENIED`

4. RBAC / permission blocker clarification

This is not an open SSOT design question.

The designed model is:

- fixed profile permissions come from `msc_profiles`;
- Lead Auditor access comes from `audit_detail.lead_auditor_user_id`;
- Conductor access comes from `audit_detail.conductor_user_id`;
- HoD / Acting HoD access comes from `master_hod_assignment`.

Current implementation status:

- Backend per-record permission checks are wired.
- Backend action gates merge static `AUDIT_P_*` grants with per-record assignment grants.
- Audit Detail frontend reads `effective_permissions` from the API for visible actions.

Actual blocker now:

- controlled journey data and evidence are missing.
- If controls are still missing after rerunning with users deliberately assigned on the test records, then it becomes a real build bug.

5. Evidence format going forward

Going forward, each journey/screen result should include:

- commit SHA tested;
- account/persona used;
- route tested;
- record IDs used;
- command executed;
- raw Playwright output or backend/frontend log excerpt;
- screenshot for any manual verification.

Current local commit SHA checked for this response:

```text
a2f308127f1e9b03137408deb08c5fe1a7e6ad52
```

Earlier journey pass/fail labels should be treated as provisional where they do not include account, route, record ID, and raw evidence.

6. Credentials

Agreed.

Credentials should not be placed in Markdown docs or unversioned handover files.

Going forward, usernames can be listed for persona mapping, but passwords should be shared only through the approved secret channel.

The credentials already shared in plaintext should be rotated before reuse.
