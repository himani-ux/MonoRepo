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

### Required Resolution

Create and seed real qualified auditor master data before converting Lead Auditor fields into a strict dropdown.

Minimum required fields:

- `user_id`
- `qualification_text`
- `qualification_date`
- `expiry_date`
- `scope_standards_csv`
- `auditor_scope`
- `qualified_for_seq`
- `is_active`

### Recommended UI Behavior

The Lead Auditor field should become a dropdown sourced from `master_audit_qualified_auditor`, filtered by:

- active auditor record
- non-expired qualification
- selected audit standard
- audit scope
- SEQ qualification where applicable

After selecting an auditor, the UI should auto-fill name, designation, company, and qualification from the auditor/user profile data.

