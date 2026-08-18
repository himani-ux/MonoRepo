# Audit Response - 2026-08-18

## Four Open Items

1. Authoritative commit:
   The authoritative branch is `main` in `https://github.com/himani-ux/VIMS_Audit.git` after pull. Do not use `a2f308127f1e9b03137408deb08c5fe1a7e6ad52` or `a87176d`. The current repo contains `QUALITY_GATE_STAMP.json` and `audit_docsuite/AUDIT_RUNTIME_GAPS.md` for direct review.

2. Rerun list:
   `JOURNEY-11` is back on the rerun list. `JOURNEY-1` and `JOURNEY-9` are also treated as unvalidated until rerun with raw evidence. No earlier narrative pass is being claimed as final evidence.

3. UAT report format:
   Going forward, every journey result will be packaged as `UAT_REPORT_<date>.md` using `journey/docs/uat-report-format.md`, with path:line evidence quotes, raw output/logs, route tested, account/persona used, record IDs, and artifact hashes or screenshots where manual evidence is used.

4. Credential rotation:
   Credential rotation is still a separate account-admin item. No plaintext passwords are included in this repo response. Code/evidence review can continue in parallel, but final closure needs one-line confirmation from the account owner with rotated accounts and rotation date.

## Direct Status

Original rerun report base, kept here only as historical evidence for that rerun:

`2063e624035637e263473588c96ff9bb3afd5fb2 - Add audit response 4`

Current authoritative review target is the latest `main` branch after pull, as stated in the four-item answer above.

Rerun report created:

`audit_docsuite/UAT_REPORT_2026-08-18_RERUN.md`

No Audit journey has been marked as passed in this rerun report. The report separates actual product/screen gaps from test setup blockers so the next action is clear.

Evidence is included below so the status can be reviewed without another clarification round.

## Product Or Workflow Gaps Found

These are the concrete gaps that need product/workflow attention:

| Journey | Route / area | Result | What is missing |
| --- | --- | --- | --- |
| JOURNEY-3 | `/audit/audits/A1170000-0000-0000-0000-000000000002` | FAILED | Audit detail opens, but expected Submit, Scorecard, Vessel Acknowledge, and findings controls are not visible for the tested record/actor. |
| JOURNEY-5 | `/audit/findings/A1170000-0000-0000-0000-000000000007/nc` | FAILED | NC Closure page opens, but it reports NC closure not found. |
| JOURNEY-7 | `/audit/findings/A1170000-0000-0000-0000-000000000007/nc` | FAILED | Lead Auditor / effectiveness verification controls are not visible. |
| JOURNEY-8 | `/audit/findings/A1170000-0000-0000-0000-000000000012/obs` | FAILED | Observation Closure page opens, but it reports Observation closure not found. |
| JOURNEY-14 | Acting HoD assignment | FAILED | Acting HoD assignment data exists locally, but no confirmed frontend route exists for the Acting HoD screen. |

## Test Setup Blockers

These journeys could not be browser-rerun in this report because, at the time of the rerun, the local journey runner package and required journey environment values were missing:

`JOURNEY-1, JOURNEY-2, JOURNEY-4, JOURNEY-6, JOURNEY-9, JOURNEY-10, JOURNEY-11, JOURNEY-12, JOURNEY-13`

Post-sync correction:

- The runner-folder blocker has since been closed by commit `5ee3062 Sync audit journey test docs`.
- `journey/surface-check` is now present in the repo.
- The remaining setup items are credentials/env values through the secret channel and installing runner dependencies before browser execution.

Required runtime config:

- `APP_BASE_URL`
- `JOURNEY_USERNAME`
- `JOURNEY_PASSWORD`
- `JOURNEY_AUDIT_ID`
- `JOURNEY_NC_FINDING_ID`
- `JOURNEY_OBS_FINDING_ID`
- `JOURNEY_EXTERNAL_AUDIT_ID`
- `JOURNEY_ACTING_HOD_ROUTE`

Credentials should be shared through the approved secret channel only, not in markdown.

## Local IDs Available For Next Rerun

These IDs are available locally and can be used for the next proper journey run:

| Record | ID |
| --- | --- |
| Audit plan | `A1170000-0000-0000-0000-000000000001` |
| Audit detail | `A1170000-0000-0000-0000-000000000002` |
| NC finding | `A1170000-0000-0000-0000-000000000007` |
| Observation finding | `A1170000-0000-0000-0000-000000000012` |
| Acting HoD assignment | `A1170000-0000-0000-0000-000000000030` |

External audit close-out remains blocked because no local external audit detail row exists.

## What We Need To Close The Blockers

1. Install the synced `journey/surface-check` runner dependencies from its lock file before browser execution.
2. Provide required test-user credentials through the secret channel.
3. Confirm the exact Acting HoD frontend route, or schedule/build the missing screen.
4. Create or provide one local external audit detail record for JOURNEY-12 close-out.
5. Rerun the listed journeys using the UAT report format with command output, route, account/persona, record IDs, and screenshots/artifact hashes where manual evidence is used.

## Current Conclusion

The blockers are now separated clearly:

- Product gaps: JOURNEY-3, JOURNEY-5, JOURNEY-7, JOURNEY-8, JOURNEY-14.
- Test setup blockers: JOURNEY-1, JOURNEY-2, JOURNEY-4, JOURNEY-6, JOURNEY-9, JOURNEY-10, JOURNEY-11, JOURNEY-12, JOURNEY-13.
- Missing test data: external audit detail record for JOURNEY-12 close-out.

This should give the senior team concrete items to resolve instead of vague confirmation status.

## Evidence Pack

### 1. Original Rerun Commit And Working State

This command output belongs to the original rerun evidence package only. It is not the current authoritative branch head.

Command from the original rerun:

```text
git rev-parse HEAD
```

Output:

```text
2063e624035637e263473588c96ff9bb3afd5fb2
```

Scoped status after creating the rerun evidence files:

```text
M  Docs/progress.txt
?? audit_docsuite/UAT_REPORT_2026-08-18_RERUN.md
?? audit_docsuite/response 5.md
```

Unrelated local file not part of this evidence package:

```text
M  .serena/project.yml
```

### 2. Journey Runner Setup Evidence

The journey README requires a separate runner folder and environment variables.

Evidence:

```text
tests/journeys/README.md:11:cd journey/surface-check
tests/journeys/README.md:19:APP_BASE_URL=http://localhost:5173 \
tests/journeys/README.md:20:JOURNEY_USERNAME=<user> \
tests/journeys/README.md:21:JOURNEY_PASSWORD=<password> \
tests/journeys/README.md:22:JOURNEY_TESTS_DIR=../../tests/journeys \
tests/journeys/README.md:23:npx playwright test
tests/journeys/README.md:40:JOURNEY_AUDIT_ID=<audit_uuid>
tests/journeys/README.md:41:JOURNEY_NC_FINDING_ID=<finding_uuid>
tests/journeys/README.md:42:JOURNEY_OBS_FINDING_ID=<finding_uuid>
tests/journeys/README.md:43:JOURNEY_EXTERNAL_AUDIT_ID=<audit_uuid>
tests/journeys/README.md:44:JOURNEY_ACTING_HOD_ROUTE=<route_if_implemented>
```

Initial local folder check before the handover journey docs were synced:

```text
PRE_SYNC: Test-Path journey/surface-check returned False
```

Post-sync folder check after commit `5ee3062 Sync audit journey test docs`:

```text
PRESENT: journey/surface-check
PRESENT: journey/docs/uat-report-format.md
```

Conclusion: the runner-folder blocker is closed in the repo. Browser journey execution now requires runner dependency installation and the required env/account values.

### 3. Frontend Route Evidence

Registered routes found in `psc-frontend/src/App.tsx`:

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
```

Route absence checks:

```text
NO_MATCH: /audit and /audit/dashboard are not route-registered in psc-frontend/src/App.tsx
NO_MATCH: no Acting HoD frontend route/control match in App.tsx or sidebar.tsx
```

Conclusion:

- `/audit/dashboard` is a route gap.
- Acting HoD has DB data but no confirmed frontend route.

### 4. Audit Detail Control Evidence

The source contains the controls expected by JOURNEY-3, but the rerun report records that they were not visible for the tested record/actor.

Source evidence:

```text
psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:259:Submit Report
psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:265:Vessel Acknowledge Audit Report
psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:341:data-eid="MOCKUP-AUDIT-02:detail.scorecard_grid"
psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:361:Save Scorecard
psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:369:CardTitle>Findings
psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:371:data-eid="MOCKUP-AUDIT-02:detail.findings_table"
psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:405:Link to={`/audit/findings/${finding.id}/nc`}
psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:411:Link to={`/audit/findings/${finding.id}/nc/wizard`}
psc-frontend/src/components/audit/audit-detail/audit-detail-page.tsx:419:Link to={`/audit/findings/${finding.id}/obs`}
```

Conclusion: this points to an actor/record-state visibility problem or route-state issue, not a total absence of source code.

### 5. Journey Spec Expected Controls

The journey specs define exactly what each journey checks.

```text
tests/journeys/journey-001.spec.ts:6-7: Audit Plans, Register Audit, Create routine plan entry, Register rows, OPM F 713
tests/journeys/journey-002.spec.ts:6-7: Register Audit, Audit Classification, Audit Subtype, Lead Auditor
tests/journeys/journey-003.spec.ts:4,7: JOURNEY_AUDIT_ID; Submit, Scorecard, Vessel Acknowledge, findings
tests/journeys/journey-004.spec.ts:4,7: JOURNEY_NC_FINDING_ID; Root Cause, Save and Continue, RCA, wizard
tests/journeys/journey-005.spec.ts:4,7: JOURNEY_NC_FINDING_ID; Master / HoD Signer, signature, signed, backdate
tests/journeys/journey-006.spec.ts:4,7: JOURNEY_NC_FINDING_ID; PIC, Office, Review, Draft
tests/journeys/journey-007.spec.ts:4,7: JOURNEY_NC_FINDING_ID; Effectiveness, Verification, Lead Auditor, Review Method
tests/journeys/journey-008.spec.ts:4,7: JOURNEY_OBS_FINDING_ID; Master Close, Action Plan, Save and Continue
tests/journeys/journey-009.spec.ts:6: OPM F 713, Request extension, Cancel, Extension
tests/journeys/journey-010.spec.ts:6: Create additional audit, Additional reason, Trigger type, Additional
tests/journeys/journey-011.spec.ts:6,9: Failed notifications, Retry, notified offline, Scan-validation queue, Accept, rescan
tests/journeys/journey-012.spec.ts:6,8,11-12: External audit registration and optional external close-out route
tests/journeys/journey-013.spec.ts:8: Office Department, OFFICE_DEPT, Department, Audit Scope
tests/journeys/journey-014.spec.ts:4,7: JOURNEY_ACTING_HOD_ROUTE; Acting, HoD, effective, department
```

### 6. Database Evidence

Read-only SQL connector:

```text
server_name: HIMANI
database_name: ksm_marine_live
login_name: Himani\himan
```

Verified Audit detail:

```text
source_table: audit_detail
id: A1170000-0000-0000-0000-000000000002
status: IN_PROGRESS
audit_classification: INTERNAL
conductor_user_id: DEMO.CONDUCTOR
lead_auditor_user_id: DEMO.LEAD
pic_user_id_resolved: Aman.Oberoi
external_audit_org_id: null
```

Verified external audit availability:

```text
external_audit_count: 0
external_org_count: 0
```

Verified local records:

```text
master_audit_plan
id: A1170000-0000-0000-0000-000000000001
status: CONFIRMED
audit_classification: INTERNAL
audit_standards_csv: ISM,ISPS
target_vessel_id: A282A51B-0183-EE11-B02E-782B4610C006

audit_finding_nc
id: A1170000-0000-0000-0000-000000000007
status: OPEN
audit_classification: INTERNAL
finding_type: NC
audit_finding_nc.id: A1170000-0000-0000-0000-000000000009
psc_deficiency_id: a1170000000000000000000000000006

audit_finding_obs
id: A1170000-0000-0000-0000-000000000012
status: OPEN
audit_classification: INTERNAL
finding_type: OBS
audit_finding_obs.id: A1170000-0000-0000-0000-000000000014
psc_deficiency_id: a1170000000000000000000000000011

master_hod_assignment
id: A1170000-0000-0000-0000-000000000030
status: ACTING
dept: DECK
user_id: DEMO.HOD
effective_from: 2026-08-01
```

Conclusion:

- Required internal Audit, NC, OBS, and Acting HoD records exist locally.
- External audit close-out cannot be tested because no external audit detail row exists locally.

### 7. Permission Evidence For Scan Validation

Frontend constant:

```text
psc-frontend/src/lib/utils/permission-ids.ts:65:AUDIT_SCAN_VALIDATION: 'AUDIT_P_018'
```

Frontend route guard:

```text
psc-frontend/src/App.tsx:271:<PermissionGuard requiredProcess={PROCESS_IDS.AUDIT_SCAN_VALIDATION}>
```

Backend permission:

```text
psc-backend/apps/inspection/audit/permissions.py:26:AUDIT_P_018 = "AUDIT_P_018"
psc-backend/apps/inspection/audit/permissions.py:510:CanValidateAuditScan = HasAuditProcessPermission.requiring(AUDIT_P_018)
```

Conclusion: `AUDIT_SCAN_VALIDATION` is not a separate permission model. It is the frontend alias for canonical `AUDIT_P_018`.

### 8. JOURNEY-6 Backend Guard Evidence

Source evidence:

```text
psc-backend/tests/audit/test_car_workflow_proxy.py:341:def test_lead_auditor_cannot_claim_pic_review_on_own_audit(self) -> None:
psc-backend/tests/audit/test_car_workflow_proxy.py:353:self.assertEqual(response.status_code, 403)
psc-backend/tests/audit/test_car_workflow_proxy.py:354:self.assertEqual(response.data["error"], "LEAD_AUDITOR_PIC_DENIED")
psc-backend/apps/inspection/audit/services/car_workflow.py:110:error="LEAD_AUDITOR_PIC_DENIED"
```

Command:

```text
python manage.py test tests.audit.test_car_workflow_proxy.AuditCarWorkflowProxyTests.test_lead_auditor_cannot_claim_pic_review_on_own_audit -v 2
```

Output:

```text
Found 1 test(s).
Skipping setup of unused database(s): default.
System check identified no issues (0 silenced).
test_lead_auditor_cannot_claim_pic_review_on_own_audit (...) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.037s

OK
```

Conclusion: the Lead Auditor cannot self-claim PIC review; the backend guard is working and returns HTTP 403 with `LEAD_AUDITOR_PIC_DENIED`.
