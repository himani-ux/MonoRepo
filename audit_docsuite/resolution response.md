# Resolution Response

## Resolution Status

The `RESOLUTION_08-18.md` file identifies the Audit Gap 2 issues and proposes next steps, but it does not fully close every item.

## Implemented Locally

- Added qualified-auditor master APIs using `AUDIT_P_009`.
- Added external-audit-organisation APIs using `AUDIT_P_019`.
- Added vessel RO delegation APIs using `AUDIT_P_020`.
- Added authentication and process-ID checks.
- Added validation for qualification dates, active organisations, and overlapping RO delegation periods.
- Added focused tests and backend documentation.
- No database migration, frontend master screen, or duplicate office/crew identity table was added.

## Still Pending From The Resolution

### Approval

The resolution marks the new decision for `AUDIT_P_019` and `AUDIT_P_020` as proposed and pending formal approval. The APIs were implemented locally because implementation was requested, but the decision still requires formal confirmation.

### Real Operational Data

The resolution says real qualified auditors, external audit organisations, and vessel RO delegations must be supplied or reviewed by the business owner. Developers must not invent production-looking rows. The local implementation does not seed real data.

### Official Permission Configuration

The new permission IDs must be formally registered and added to the official permission/profile configuration for the intended users, especially SEQ Manager. Code-level permission support alone does not create the required production `msc_profiles` records.

### Documentation Correction

The resolution identifies incorrect PRD wording claiming that some operational tables are seeded. This correction belongs to the document owner and must follow the approved document reissue process.

### ORB Security Confirmation

ORB is not an active security blocker in the current configured application flow. ORB page and process access is governed through `msc_profiles` `form_ids` and `process_ids`, so users without the assigned ORB access cannot reach the relevant ORB screens or actions through the application. The earlier `AllowAny` concern should be treated as stale/unreachable review context unless a currently registered public route proves otherwise.

Direct code check on `psc-backend/modules/orb/orb/views.py` confirms the following for the four named ORB functions:

- `get_operations`: `@permission_classes([AllowAny])` is not present. Only `@api_view(['GET'])` is present. This function is not registered in `psc-backend/modules/orb/orb/urls.py`.
- `list_for_chief`: `@permission_classes([AllowAny])` is not present. Only `@api_view(['GET'])` is present. This function is not registered in `psc-backend/modules/orb/orb/urls.py`.
- `get_all_crew_onboarding_history`: `@permission_classes([AllowAny])` is not present. Only `@api_view(["GET"])` is present. This function is not registered in `psc-backend/modules/orb/orb/urls.py`.
- `get_vessel_id_for_current_user`: `@permission_classes([AllowAny])` is not present. Only `@api_view(["GET"])` is present. This function is registered as `api/get-current-user-vessel/` and has an explicit session check that returns HTTP 401 when `request.session['logged_in']` is missing.

Conclusion: for these four ORB functions specifically, `AllowAny` is not currently active in the local `Complete_VIMS` code. Three of the four are not URL-registered, and the only registered function requires session login.

## 08-19 Local Implementation Update

### Audit Plan Edit UUID Error

Resolved locally. The Audit plan detail/edit lookup now casts the incoming route ID as `uniqueidentifier` before querying `master_audit_plan`, which avoids the SQL Server conversion failure for hyphenated UUID route values.

Evidence:

- `psc-backend/apps/inspection/audit/views/plan.py`
- `psc-backend/tests/audit/test_plan_api.py`
- Test run: `python -m unittest tests.audit.test_plan_api -v` passed locally before this update.

### Audit Dashboard Routes

Resolved locally under `CR-149`.

- `/audit` now redirects to `/audit/dashboard`.
- `/audit/dashboard` now renders a read-only Audit dashboard using the existing Audit Plan Register API.
- The existing Audit sidebar group now includes an `Audit Dashboard` child link for Audit-authorized users.
- No backend endpoint, database table, migration, or new permission ID was added.

Evidence:

- `psc-frontend/src/App.tsx`
- `psc-frontend/src/routes/audit/index.tsx`
- `psc-frontend/src/routes/audit/dashboard.tsx`
- `psc-frontend/src/routes/audit/dashboard.test.tsx`
- `psc-frontend/src/components/layout/sidebar.tsx`
- `psc-frontend/src/components/layout/sidebar.test.tsx`

### Local Master Data Evidence

Checked against the local database on 2026-08-19:

- `master_audit_qualified_auditor`: 1 total row, 0 active rows. The only row is `DEMO.LEAD` and `is_active = 0`.
- `master_external_audit_org`: 1 total row, 0 active rows. The only row is a demo external audit organisation and `is_active = 0`.
- `vessel_audit_ro_delegation`: 1 total row. The table is effective-date based and has no `is_active` column.

Conclusion: the API surfaces exist locally, but real approved master data is still not present locally.

### Lead Auditor Selection And External Audit Registration

Current local code stores Lead Auditor identity on the audit record via the registration payload. It does not automatically derive a selectable Lead Auditor list from active `master_audit_qualified_auditor` rows yet.

External audit registration currently requires `external_audit_org_id` in the payload. The current registration service does not automatically resolve an organisation from `vessel_audit_ro_delegation`.

These are implementation/data gaps to be addressed only after the required business/SSOT decision is clear.

## Conclusion

The backend implementation gap from 08-18 is addressed locally, the Audit plan UUID edit error is fixed locally, and the `/audit` plus `/audit/dashboard` route gap is implemented locally. Full operational closure still depends on formal approval, approved master data, official permission/profile configuration, and the PRD correction.
