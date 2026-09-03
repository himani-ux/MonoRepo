# Audit Gaps 2

## Qualified Lead Auditor Master Data Gap

### Gap

The Audit registration flow is expected to support selecting a Lead Auditor from qualified, active, non-expired, scope-matching auditors. The supporting table exists as `master_audit_qualified_auditor`, but the repository does not currently include a seed file for this table, and the local table only has placeholder/demo data.

### Why This Matters

Without real qualified auditor data, a Lead Auditor dropdown would be empty or show only demo users. That means the system cannot reliably enforce the intended rule that the Lead Auditor must be qualified for the selected audit standards and scope.

### Current Evidence

- Model/table exists: `psc-backend/apps/inspection/audit/models/masters.py`
- Migration creates the table: `psc-backend/apps/inspection/migrations/0019_audit_master_tables.py`
- No repository seed file exists for `master_audit_qualified_auditor`
- Existing seed files cover other audit masters, but not the qualified auditor master

### Office User Data Gap

If Lead Auditor selection is restricted to office users or vessel users, the system should not ask users to type auditor details manually.

Existing office users and vessel crew must come from the common user/crew master tables. Audit-specific master tables should not become duplicate identity stores for those users.

Important rule:

Office role/profile alone should not make a user eligible as Lead Auditor. For example, a Marine Superintendent profile identifies the user's office role, but qualified-auditor eligibility must still come from `master_audit_qualified_auditor`.

## External Audit Organisation Master Data Gap

### Gap

External Audit registration can optionally capture an external audit organisation, but the supporting table `master_external_audit_org` is currently empty and the repository does not include a seed file for this master.

### Why This Matters

Without external audit organisation master data, the External Audit registration dropdown cannot provide real organisations such as class societies, flag administrations, or recognised external audit bodies. Users can still register an external audit by selecting the organisation type, but the exact organisation remains uncaptured until approved master data exists.

### Current Evidence

- Model/table exists: `psc-backend/apps/inspection/audit/models/masters.py`
- Migration creates the table: `psc-backend/apps/inspection/migrations/0019_audit_master_tables.py`
- No repository seed file exists for `master_external_audit_org`
- Current DB observation: `master_external_audit_org` has no usable rows

## Vessel RO Delegation Master Data Gap

### Gap

External Audit and RO delegation logic expects vessel-level recognised organisation delegation data, but `vessel_audit_ro_delegation` currently has no usable rows after ignoring demo data.

### Why This Matters

Without real vessel RO delegation rows, the system cannot reliably resolve which recognised organisation is delegated for a vessel and standard. This affects External Audit registration, class/RO-linked validation, and any future dropdown/filtering that depends on vessel-specific RO delegation.

### Current Evidence

- Model/table exists: `psc-backend/apps/inspection/audit/models/masters.py`
- Migration creates the table: `psc-backend/apps/inspection/migrations/0019_audit_master_tables.py`
- Current DB observation: `vessel_audit_ro_delegation` has only demo data and no usable rows

## Implementation Status (2026-08-20)

The missing backend API surface has been added locally. Most endpoints use existing tables; Qualifying Body choices use the additive `aud_master_qual_body` table from migration `0026_audit_qualifying_body_master`:

- `master_audit_qualified_auditor`: `GET/POST` collection and `GET/PATCH` detail, gated by `AUDIT_P_009`
- `aud_master_qual_body`: `GET/POST` collection and `GET/PATCH` detail, gated by `AUDIT_P_009`
- `master_external_audit_org`: `GET` collection is available to audit registration users with `AUDIT_P_001`, `AUDIT_P_003`, `AUDIT_P_013`, or `AUDIT_P_019`; `POST` collection and `GET/PATCH` detail remain gated by `AUDIT_P_019`
- `vessel_audit_ro_delegation`: `GET/POST` collection and `GET/PATCH` detail, gated by `AUDIT_P_020`

The `master_audit_qualified_auditor` frontend maintenance screen now exists at `/audit/masters/qualified-auditors` and is gated by `AUDIT_P_009`. It can create, edit, activate, and deactivate qualified-auditor rows through the existing API. Its Employee/User ID field now uses a dropdown of active office users from `users` that have an active mapped `master_role`, showing each user's display name and mapped `master_role.role_name` while saving the selected `employee_id`. Its Qualifying Body field now reads active, non-deleted choices from `aud_master_qual_body` while still saving the selected body name into the existing `master_audit_qualified_auditor.qualifying_body` text column.

The implementation seeds only generic qualifying-body names and any existing qualifying-body text already present in qualified-auditor rows. It does not seed real auditor eligibility, external audit organisation, RO delegation, office-user, or vessel-crew production data. Those tables still require approved operational data before the corresponding workflows can be fully exercised.
