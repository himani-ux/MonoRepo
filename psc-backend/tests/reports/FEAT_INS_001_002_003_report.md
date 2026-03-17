# Feature Test Report — FEAT-INS-001 / FEAT-INS-002 / FEAT-INS-003

**Date:** 2026-02-07  
**Suite:** `apps.inspection.tests.TestFEAT_INS_001_CreateInspection`, `TestFEAT_INS_002_UploadInspectionReport`, `TestFEAT_INS_003_AddDeficiency`  
**Command:**  
`python manage.py test apps.inspection.tests.TestFEAT_INS_001_CreateInspection apps.inspection.tests.TestFEAT_INS_002_UploadInspectionReport apps.inspection.tests.TestFEAT_INS_003_AddDeficiency -v 2 --settings=core.settings_test`

---

## Scope

- **FEAT-INS-001** Create Inspection (PRD.md §2.1, VALIDATION_RULES.md §2.1, BACKEND_STRUCTURE.md §11)
- **FEAT-INS-002** Upload Inspection Report (PRD.md §2.1, VALIDATION_RULES.md §2.2 + file rules)
- **FEAT-INS-003** Add Deficiency to Inspection (PRD.md §2.1, VALIDATION_RULES.md §3.1, BACKEND_STRUCTURE.md §10.4, §11)

---

## Summary

- **Total tests:** 27
- **Passed:** 20
- **Failed:** 7
- **Status:** Partial coverage; core happy-path and RBAC checks pass, multiple PRD/validation/audit gaps detected.

---

## Passing Coverage

### FEAT-INS-001 (Create Inspection)
- Happy path create for vessel master
- Non-PSC create with cleared PSC subtype behavior
- PSC subtype conditional validation checks
- RBAC checks (crew forbidden, unauthenticated blocked, cross-vessel forbidden)

### FEAT-INS-002 (Upload Inspection Report)
- Happy path uploads for PDF and JPEG
- Unsupported media type rejection
- File size limit (>3MB) rejection
- Not found and cross-vessel RBAC checks

### FEAT-INS-003 (Add Deficiency)
- Happy path deficiency create
- Auto-CAR creation check (1 deficiency = 1 CAR)
- Sequence number increment behavior
- Invalid def code and invalid action code validation checks
- Status precondition checks
- RBAC checks (crew forbidden, unauthenticated blocked)

---

## Detected Gaps (Expected Failures)

⚠️ **VALIDATION GAP (FEAT-INS-001): future inspection date**
- **PRD / Validation says:** inspection date cannot be future.
- **Observed code:** request accepted with 201.
- **Failing test:** `test_gap_validation_future_inspection_date_should_be_rejected`

⚠️ **VALIDATION GAP (FEAT-INS-001): MOU required for PSC**
- **PRD / Validation says:** PSC inspections require MOU.
- **Observed code:** empty `mou_id` accepted with 201.
- **Failing test:** `test_gap_validation_mou_should_be_required_for_psc`

⚠️ **VALIDATION GAP (FEAT-INS-001): port minimum length**
- **Validation says:** `port_place` min 2 characters.
- **Observed code:** one-character port accepted with 201.
- **Failing test:** `test_gap_validation_port_place_min_length`

⚠️ **VALIDATION GAP (FEAT-INS-002): report description mandatory**
- **PRD says:** description mandatory for report upload.
- **Observed code:** upload without `description` accepted with 201.
- **Failing test:** `test_gap_validation_description_should_be_mandatory`

⚠️ **AUDIT GAP (FEAT-INS-003): activity event on deficiency create**
- **PRD / Backend structure says:** activity history event should be created.
- **Observed code:** no `ActivityHistory` increment after create.
- **Failing test:** `test_gap_audit_activity_event_should_be_created`

⚠️ **VALIDATION GAP (FEAT-INS-003): deficiency description minimum length**
- **Validation says:** description min 10 chars.
- **Observed code:** short description accepted with 201.
- **Failing test:** `test_gap_validation_description_min_length`

⚠️ **VALIDATION GAP (FEAT-INS-003): target date cannot be past**
- **Validation says:** target date must be today or future.
- **Observed code:** past target date accepted with 201.
- **Failing test:** `test_gap_validation_target_date_cannot_be_past`

---

## Artifacts

- Test file: `psc-backend/apps/inspection/tests.py`
- Isolated test settings: `psc-backend/core/settings_test.py`

---

## Recommendation (Next Session)

1. Fix backend validation/audit implementation gaps above.
2. Re-run this suite until all 27 pass.
3. Continue with FEAT-INS-004 and FEAT-INS-005 backfill once base inspection flow is green.

---

## Addendum — 2026-02-08 (Session 39)

**Scope re-audited:** FEAT-INS-002 and FEAT-INS-003 (strict backfill extension)  
**Suite command:**  
`python manage.py test apps.inspection.tests.TestFEAT_INS_002_UploadInspectionReport apps.inspection.tests.TestFEAT_INS_003_AddDeficiency apps.inspection.tests.TestFEAT_INS_005_PICReviewInspection apps.inspection.tests.TestFEAT_INS_006_DPACloseInspection -v 2`

### Incremental Test Additions
- FEAT-INS-002: +3 tests
  - `test_happy_path_upload_jpg_alias`
  - `test_validation_description_max_length_500`
  - `test_rbac_unauthenticated_cannot_upload_report`
- FEAT-INS-003: +4 tests
  - `test_rbac_office_pic_can_add_deficiency`
  - `test_rbac_dpa_can_add_deficiency`
  - `test_gap_validation_description_max_length`
  - `test_gap_precondition_submitted_allows_only_office_user`

### Re-Audit Result (INS-002 + INS-003 classes)
- Total tests: 24
- Passed: 18
- Failed: 6

### Newly Confirmed Coverage
- INS-002 accepts JPG alias (`image/jpg`) in addition to PDF/JPEG.
- INS-002 enforces description max length 500.
- INS-002 unauthenticated upload is rejected.
- INS-003 allows deficiency create for OFFICE_PIC and DPA per RBAC matrix.

### Additional Gap Detections
- INS-003 description max-length rule (4000) is not enforced.
- INS-003 submitted-status precondition does not restrict vessel users as specified in VALIDATION_RULES.md §3.1.

### Existing Gap Status
- INS-002 description mandatory check remains failing against current backend behavior.
- INS-003 min-length/target-date/activity-event gaps remain failing.

### Update 2026-02-08 (INS-002 Recheck)
- INS-002 description mandatory gap is now **closed**.
- Fix applied in `psc-backend/apps/inspection/serializers.py` (`InspectionReportUploadSerializer.description` made required).
- Verification:
  - `pytest -q apps/inspection/tests.py -k test_gap_validation_description_should_be_mandatory` -> `1 passed`
  - `pytest -q apps/inspection/tests.py -k TestFEAT_INS_002_UploadInspectionReport` -> `10 passed`
