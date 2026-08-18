# Audit Evidence Response 3 - 2026-08-17

Commit checked locally: `a2f308127f1e9b03137408deb08c5fe1a7e6ad52`

## Git Delivery Status

The latest Audit evidence response package has been pushed to:

```text
https://github.com/himani-ux/VIMS_Audit.git
branch: main
latest pushed evidence package before the UAT-tracking update: 80154b724a8fecc8b0b6a0e8fe0ca3e1d44eef46
```

This note is added so the receiving team can pull the Git repo and review the same Audit response/docs package.

Authoritative commit clarification:

- `a2f308127f1e9b03137408deb08c5fe1a7e6ad52` was the baseline commit used when the first evidence checks were performed.
- `a87176d` was the first pushed Audit evidence response package.
- `80154b724a8fecc8b0b6a0e8fe0ca3e1d44eef46` was the latest pushed evidence package before the UAT-tracking correction.
- For review, use the current `main` branch HEAD from `https://github.com/himani-ux/VIMS_Audit.git`, not the older baseline hashes.

## 1. Phase 13.4 Quality Stamp

The Phase 13.4 stamp exists in my handover copy at:

`C:\Users\himan\Desktop\VIMS_handovers\VIMS-AUDIT-HANDOVER-v5\VIMS-AUDIT-HANDOVER-v5\progress.txt`

Verbatim final Phase 13.4 entry:

```text
2026-08-14 - Final Phase 13.4 session close requested by user

Ledger updates completed:
  - root `tasks/todo.md` updated with final session close marker;
  - live `Complete_VIMS_audit_dev/tasks/todo.md` updated with final session
    close marker;
  - root `docs/LESSONS.md` updated with final session close review after L-63;
  - live `Complete_VIMS_audit_dev/Docs/LESSONS.md` updated with matching
    close review after L-084;
  - `progress.txt` updated with this final closeout marker;
  - final quality gate rerun after live-tree closeout edits.

Final verification:
  - escalated Git Bash with repo-local `jq` first in `PATH`:
    `VERDICT: PASS quality-gate reason_codes=none not_applicable_yet=0
    deferred=PB-AUD-API-P95 overall_activation_state=RESOLVED`.

QUALITY: PASS stamp=7cab688e67a2 tree=fe57e69e86d5
```

The matching `QUALITY_GATE_STAMP.json` has:

```text
result: PASS
timestamp: 2026-08-14T08:18:18Z
git_tree_hash: sha256:fe57e69e86d5533546b44b18fcdbf4366c5b8908b2e03f2e97f595a00b8c397c
```

I do not see a separate raw terminal log file for that quality run in the local copy. The evidence available locally is the verbatim `progress.txt` runner line above plus `QUALITY_GATE_STAMP.json`.

Important boundary: this stamp is not a fresh quality stamp for the current edited tree. The same progress file states that later local runtime/debug edits happened after this quality citation, so Domain 13 must be rerun before claiming the current tree is quality-stamped.

## 2. ORB Auth Decorator Verification

Effective project default:

`psc-backend/core/settings.py:214-215`

```text
DEFAULT_PERMISSION_CLASSES = rest_framework.permissions.IsAuthenticated
```

Current effective permission class check:

```text
get_operations cls_permissions= ['IsAuthenticated']
get_operations status= 401

list_for_chief cls_permissions= ['IsAuthenticated']
list_for_chief status= 401

get_all_crew_onboarding_history cls_permissions= ['IsAuthenticated']
get_all_crew_onboarding_history status= 401

get_vessel_id_for_current_user cls_permissions= ['IsAuthenticated']
get_vessel_id_for_current_user status= 401
```

Command used:

```text
python manage.py shell -c "from rest_framework.test import APIRequestFactory; from modules.orb.orb import views; f=APIRequestFactory(); names=['get_operations','list_for_chief','get_all_crew_onboarding_history','get_vessel_id_for_current_user'];
for n in names:
    view=getattr(views,n); cls=getattr(view,'cls',None)
    print(n, 'cls_permissions=', [getattr(p,'__name__',str(p)) for p in getattr(cls,'permission_classes',[])])
    resp=view(f.get('/unauth/'))
    print(n, 'status=', getattr(resp,'status_code',None))"
```

Route status:

- `get_vessel_id_for_current_user` is URL-wired at `psc-backend/modules/orb/orb/urls.py:31`.
- `get_operations`, `list_for_chief`, and `get_all_crew_onboarding_history` are not URL-wired locally, so they were verified by direct DRF view calls instead of HTTP route calls.

Tracking update: this ORB auth verification is now explicitly tracked in `audit_docsuite/AUDIT_RUNTIME_GAPS.md`. The next proper hardening step is to add a committed regression test so any future route wiring still proves unauthenticated access returns 401/403.

## 3. JOURNEY-6 Evidence

The backend guard test exists at:

`psc-backend/tests/audit/test_car_workflow_proxy.py:341`

Git-show excerpt at the checked commit:

Command used:

```text
git show HEAD:psc-backend/tests/audit/test_car_workflow_proxy.py
```

```text
def test_lead_auditor_cannot_claim_pic_review_on_own_audit(self) -> None:
    _audit_detail, finding, _deficiency, car = self._create_audit_finding()
    car.status = CARStatus.SUBMITTED_TO_PIC
    car.save(update_fields=["status"])

    response = self._post_proxy(
        finding.id,
        {"action": WorkflowAction.START_PIC_REVIEW, "comment": "Trying to self-claim."},
        self.lead_auditor,
    )

    car.refresh_from_db()
    self.assertEqual(response.status_code, 403)
    self.assertEqual(response.data["error"], "LEAD_AUDITOR_PIC_DENIED")
    self.assertEqual(car.status, CARStatus.SUBMITTED_TO_PIC)
```

The exact backend error code is uppercase:

```text
LEAD_AUDITOR_PIC_DENIED
```

Source:

`psc-backend/apps/inspection/audit/services/car_workflow.py:110`

The journey map uses the lowercase negative-state label `lead_auditor_pic_denied`. That is a journey label, not the backend response code.

Raw test-run output:

```text
python manage.py test tests.audit.test_car_workflow_proxy.AuditCarWorkflowProxyTests.test_lead_auditor_cannot_claim_pic_review_on_own_audit -v 2

Found 1 test(s).
Skipping setup of unused database(s): default.
System check identified no issues (0 silenced).
test_lead_auditor_cannot_claim_pic_review_on_own_audit (...) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.041s

OK
```

Positive PIC browser case:

- `Aman.Oberoi` is the only Superintendent/PIC account name recorded in the current local docs.
- The second Superintendent account used for the later positive rerun is not recorded in the repo evidence I can see.
- Because of that, I would not mark the manual positive PIC case as fully evidence-packaged until the second account name, route, record ID, screenshot/log, and command/output are captured.

## 4. Unified Current Rerun List

Current unified rerun list:

```text
JOURNEY-1
JOURNEY-2
JOURNEY-3
JOURNEY-4
JOURNEY-5
JOURNEY-7
JOURNEY-8
JOURNEY-9
JOURNEY-10
JOURNEY-11
JOURNEY-12
JOURNEY-13
```

`JOURNEY-1`, `JOURNEY-9`, and `JOURNEY-11` must also be treated as unvalidated until rerun with the agreed evidence package. `JOURNEY-6` should not be listed as a DPA failure. The backend negative guard is passing, and the positive PIC path needs evidence packaging if it is to be logged as verified.

## 5. SCR-AUD-9 And SCR-AUD-10 Route Evidence

SCR-AUD-9 route:

`psc-frontend/src/App.tsx:252`

```text
path="/dpa/notifications/failed"
```

Guard:

```text
requiredAnyProcess=[
  PROCESS_IDS.AUDIT_CREATE,
  PROCESS_IDS.AUDIT_APPROVE_EXTENSION,
  PROCESS_IDS.AUDIT_CANCEL_PLAN,
]
```

These map to:

```text
AUDIT_P_001
AUDIT_P_005
AUDIT_P_006
```

SCR-AUD-10 route:

`psc-frontend/src/App.tsx:268`

```text
path="/dpa/scan-validation-queue"
```

Guard:

```text
requiredProcess={PROCESS_IDS.AUDIT_SCAN_VALIDATION}
```

Mapping:

`psc-frontend/src/lib/utils/permission-ids.ts:65`

```text
AUDIT_SCAN_VALIDATION: 'AUDIT_P_018'
```

So `AUDIT_SCAN_VALIDATION` is not a new permission ID. It is a frontend constant name that maps to the canonical RBAC permission `AUDIT_P_018`. Future reports should mention `AUDIT_P_018` to avoid naming confusion.

## 6. Credential Rotation

Credential rotation remains a separate open account-administration item.

- Plaintext passwords were removed from the local Audit response docs.
- Future password sharing should happen only through the approved secret channel.

What is not confirmed:

- Whether the four exposed test accounts were rotated.
- The rotation date.

Temporary review note:

Credential rotation should be treated as a separate account-administration follow-up, not as a blocker for reviewing the Audit evidence package in parallel. Plaintext passwords have already been removed from the local Audit response docs, and future credentials should be shared only through the approved secret channel. This item should not be closed until the account owner/admin provides the one-line confirmation: accounts rotated plus rotation date.

## UAT Report Format Requirement

Future rerun evidence must be packaged as:

```text
UAT_REPORT_<YYYY-MM-DD>.md
```

The format source is:

```text
C:\Users\himan\Desktop\VIMS_handovers\VIMS-AUDIT-HANDOVER-v5\VIMS-AUDIT-HANDOVER-v5\journey\docs\uat-report-format.md
```

The first UAT-tracking file for the current correction is:

```text
audit_docsuite/UAT_REPORT_2026-08-18.md
```

That file records that no journey pass is being claimed until the browser reruns produce proper evidence, including path:line quotes, raw output/logs, screenshots where manual, and artifact hashes where artifacts are used.
