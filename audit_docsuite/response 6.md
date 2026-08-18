# Audit Response 6 - Repo-Verifiable Status Package - 2026-08-18

## Review Target

Repo: `https://github.com/himani-ux/VIMS_Audit.git`

Branch: `main`

Use the latest `main` after pull. If choosing between `a2f308127f1e9b03137408deb08c5fe1a7e6ad52` and `a87176d`, neither should be treated as the current authority after the later audit evidence commits.

Current evidence base before this response file:

- `5ee30623ec496118752b422c79289f0ea84f6f5e` - `Sync audit journey test docs`
- `218fcfb` - `Add audit rerun evidence package`
- `2063e62` - `Add audit response 4`

Primary files to review in the repo:

- `audit_docsuite/response 6.md`
- `audit_docsuite/response 5.md`
- `audit_docsuite/UAT_REPORT_2026-08-18_RERUN.md`
- `audit_docsuite/JOURNEY_RUNTIME_RUN_2026-08-17.md`
- `audit_docsuite/AUDIT_RUNTIME_GAPS.md`
- `journey/docs/uat-report-format.md`
- `journey/surface-check/package.json`
- `tests/journeys/README.md`
- `tests/journeys/`

## Current Answers

### 1. Authoritative Commit

The current repo state is the latest `main` after the audit evidence commits. The commit `5ee30623ec496118752b422c79289f0ea84f6f5e` is the current evidence base before this response file, because it adds the synced journey runner and journey documentation that were missing when `response 5` was first created.

Evidence:

```text
git rev-parse HEAD
5ee30623ec496118752b422c79289f0ea84f6f5e

git log --oneline -3
5ee3062 Sync audit journey test docs
218fcfb Add audit rerun evidence package
2063e62 Add audit response 4
```

### 2. Journey Runner And UAT Format

The previous "runner missing" blocker is closed in the repo.

Evidence:

```text
journey/surface-check/package.json:2:  "name": "journey-surface-check",
journey/surface-check/package.json:11:    "check-surface": "node check-surface.mjs",
journey/surface-check/package.json:12:    "test:journeys": "playwright test --config=playwright.config.mjs"
tests/journeys/README.md:11:cd journey/surface-check
journey/docs/uat-report-format.md:29:A UAT report is one file, `UAT_REPORT_<YYYY-MM-DD>[-<n>].md`
```

Current runtime requirement:

- Install runner dependencies from `journey/surface-check`.
- Set `APP_BASE_URL`, journey IDs, and account env values.
- Credentials must be supplied through the secret channel only.
- No plaintext passwords are written in this response package.

### 3. Current Journey Classification

No browser journey is marked passed in `audit_docsuite/UAT_REPORT_2026-08-18_RERUN.md`.

Product or workflow gaps:

| Journey | Current classification | Evidence file |
| --- | --- | --- |
| JOURNEY-3 | Audit detail route opens, but expected controls were not visible for the tested record/actor. | `audit_docsuite/UAT_REPORT_2026-08-18_RERUN.md` |
| JOURNEY-5 | NC closure route opens, but the page says NC closure not found. | `audit_docsuite/UAT_REPORT_2026-08-18_RERUN.md` |
| JOURNEY-7 | Lead Auditor/effectiveness controls were not visible. | `audit_docsuite/UAT_REPORT_2026-08-18_RERUN.md` |
| JOURNEY-8 | Observation closure route opens, but the page says Observation closure not found. | `audit_docsuite/UAT_REPORT_2026-08-18_RERUN.md` |
| JOURNEY-14 | Acting HoD assignment route is not implemented/registered on the frontend. | `audit_docsuite/UAT_REPORT_2026-08-18_RERUN.md` |

Runtime rerun required with proper env/account values:

`JOURNEY-1, JOURNEY-2, JOURNEY-4, JOURNEY-6, JOURNEY-9, JOURNEY-10, JOURNEY-11, JOURNEY-12, JOURNEY-13`

JOURNEY-12 also needs a real external audit detail record before the optional external close-out step can be claimed.

### 4. JOURNEY-6 Evidence

Backend negative guard is implemented and tested: a Lead Auditor cannot claim PIC review on their own audit.

Account evidence status:

- `Aman.Oberoi` is the recorded Superintendent/PIC account in the local evidence files.
- The second Superintendent account name is not recorded in the repo evidence package.
- Because that account name, screenshot/log, and command output are not captured, this response does not claim a browser UAT pass for the positive PIC case.
- The backend negative rule is still verified by the regression test below.

Code evidence:

```text
psc-backend/tests/audit/test_car_workflow_proxy.py:341:test_lead_auditor_cannot_claim_pic_review_on_own_audit
psc-backend/tests/audit/test_car_workflow_proxy.py:354:self.assertEqual(response.data["error"], "LEAD_AUDITOR_PIC_DENIED")
psc-backend/apps/inspection/audit/services/car_workflow.py:110:error="LEAD_AUDITOR_PIC_DENIED"
```

Fresh test output:

```text
python manage.py test tests.audit.test_car_workflow_proxy.AuditCarWorkflowProxyTests.test_lead_auditor_cannot_claim_pic_review_on_own_audit -v 2

Found 1 test(s).
System check identified no issues (0 silenced).
test_lead_auditor_cannot_claim_pic_review_on_own_audit ... ok

Ran 1 test in 0.053s
OK
```

The exact error code in code is uppercase: `LEAD_AUDITOR_PIC_DENIED`.

### 5. Screen And Route Status

| SCR ID | Screen | Current route status |
| --- | --- | --- |
| SCR-AUD-9 | DPA failed notifications | Built and route-registered at `psc-frontend/src/App.tsx:252`. |
| SCR-AUD-10 | DPA scan validation queue | Built and route-registered at `psc-frontend/src/App.tsx:268`. |
| SCR-AUD-11 | Audit dashboard | Route `/audit/dashboard` is not registered. Needs build or route wiring. |
| SCR-AUD-12 | Finding detail | Implemented as typed finding routes: NC wizard, NC closure, and OBS closure. Generic `/audit/findings/:id` is not registered. |
| SCR-AUD-14 | Auditor pre-audit dashboard | `/deficiencies` is route-registered using `ROUTES.DEFICIENCIES` at `psc-frontend/src/App.tsx:358` and `psc-frontend/src/lib/utils/constants.ts:173`. |

Route evidence:

```text
psc-frontend/src/App.tsx:210:path="/inspections/new"
psc-frontend/src/App.tsx:236:path="/audit/plans"
psc-frontend/src/App.tsx:252:path="/dpa/notifications/failed"
psc-frontend/src/App.tsx:268:path="/dpa/scan-validation-queue"
psc-frontend/src/App.tsx:278:path="/audit/external/new"
psc-frontend/src/App.tsx:288:path="/audit/external/:auditId"
psc-frontend/src/App.tsx:298:path="/audit/audits/:auditId"
psc-frontend/src/App.tsx:306:path="/audit/audits/:auditId/checklist"
psc-frontend/src/App.tsx:314:path="/audit/findings/:findingId/nc/wizard"
psc-frontend/src/App.tsx:322:path="/audit/findings/:findingId/nc"
psc-frontend/src/App.tsx:330:path="/audit/findings/:findingId/obs"
psc-frontend/src/App.tsx:358:path={ROUTES.DEFICIENCIES}
psc-frontend/src/lib/utils/constants.ts:173:DEFICIENCIES: '/deficiencies'
```

### 6. Permission Mapping

`SCR-AUD-10` uses the canonical permission `AUDIT_P_018`. The frontend alias is `AUDIT_SCAN_VALIDATION`, but it maps to `AUDIT_P_018`, so this is not a new permission constant.

Evidence:

```text
psc-frontend/src/lib/utils/permission-ids.ts:65:AUDIT_SCAN_VALIDATION: 'AUDIT_P_018'
psc-frontend/src/App.tsx:271:requiredProcess={PROCESS_IDS.AUDIT_SCAN_VALIDATION}
psc-backend/apps/inspection/audit/permissions.py:26:AUDIT_P_018 = "AUDIT_P_018"
psc-backend/apps/inspection/audit/permissions.py:510:CanValidateAuditScan = HasAuditProcessPermission.requiring(AUDIT_P_018)
```

### 7. Assignment-Based RBAC

Assignment-based RBAC is implemented in backend service code and must be validated through journey records assigned to the correct user IDs. It is not an `msc_profiles` static-row issue for Lead Auditor, Conductor, HoD, or Acting HoD.

Current status:

- Static `AUDIT_P_*` grants still gate the main screens.
- Per-record checks exist for action-time restrictions such as Lead Auditor not claiming PIC review on own audit.
- The remaining browser UAT work must deliberately write the journey users into `audit_detail.lead_auditor_user_id`, `audit_detail.conductor_user_id`, and `master_hod_assignment` for the records under test before rerunning.

### 8. Credential Rotation

No plaintext passwords are included in this repo response. Credential rotation is an account-administration action outside the codebase.

Requested handling:

- Do not block code/evidence review on credential rotation.
- Rotate the previously shared test accounts separately through the approved admin/secret channel.
- Record the rotation date after the account owner confirms it.

### 9. What To Send For Review

Send this file as the main response:

```text
audit_docsuite/response 6.md
```

Attach or point to these supporting files:

```text
audit_docsuite/UAT_REPORT_2026-08-18_RERUN.md
audit_docsuite/response 5.md
journey/docs/uat-report-format.md
tests/journeys/README.md
```

This package answers every requested item with a repo path, current classification, and evidence reference. Items that require runtime credentials, external audit test data, or account-admin rotation are classified as required actions instead of being left as vague confirmation gaps.
