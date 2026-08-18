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

External Audit registration expects users to select an external audit organisation, but the supporting table `master_external_audit_org` is currently empty and the repository does not include a seed file for this master.

### Why This Matters

Without external audit organisation master data, the External Audit registration dropdown cannot provide real organisations such as class societies, flag administrations, or recognised external audit bodies. Users would either be blocked from registering an external audit or forced into manual/free-text workarounds.

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
