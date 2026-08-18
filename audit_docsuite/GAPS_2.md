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

### Office User Source Recommendation

If Lead Auditor selection is restricted to office users, the system should not ask users to type auditor details manually.

Recommended source split:

- `master_audit_qualified_auditor` should be used for qualification and eligibility.
- Existing office user/profile master data should be used for person details.

The Lead Auditor dropdown should resolve `master_audit_qualified_auditor.user_id` against the existing office user/profile data and display practical labels such as:

`Name - Designation - Standards Scope - Qualification Expiry`

When a Lead Auditor is selected, the system should save:

- `audit_detail.lead_auditor_user_id`
- `audit_detail.lead_auditor_name`
- `audit_detail.lead_auditor_designation`
- `audit_detail.lead_auditor_company`
- `audit_detail.lead_auditor_qual`

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

### Required Resolution

Create and seed real external audit organisation master data before making External Audit registration fully dropdown-driven.

Minimum required fields:

- `name`
- `org_type`
- `country`
- `linked_class_society_ref`
- `is_active`

Recommended organisation types:

- `CLASS_SOCIETY`
- `FLAG_STATE`
- `PORT_STATE`
- `CUSTOMER`
- `OTHER`

### Recommended UI Behavior

The External Audit organisation field should become a dropdown sourced from active rows in `master_external_audit_org`.

When an organisation is selected, the UI should auto-fill or constrain:

- external organisation type
- linked class society reference, if present
- country, if present

If the organisation is missing, SEQ/DPA should be able to add it through a controlled master-data process instead of typing one-off values inside the audit registration form.

## Vessel RO Delegation Master Data Gap

### Gap

External Audit and RO delegation logic expects vessel-level recognised organisation delegation data, but `vessel_audit_ro_delegation` currently has no usable rows after ignoring demo data.

### Why This Matters

Without real vessel RO delegation rows, the system cannot reliably resolve which recognised organisation is delegated for a vessel and standard. This affects External Audit registration, class/RO-linked validation, and any future dropdown/filtering that depends on vessel-specific RO delegation.

### Current Evidence

- Model/table exists: `psc-backend/apps/inspection/audit/models/masters.py`
- Migration creates the table: `psc-backend/apps/inspection/migrations/0019_audit_master_tables.py`
- Current DB observation: `vessel_audit_ro_delegation` has only demo data and no usable rows

### Required Resolution

Create and seed real vessel RO delegation data.

Minimum required fields:

- `target_vessel_id`
- `standard_code`
- `master_external_audit_org_id`
- `effective_from`
- `effective_to`

### Recommended UI Behavior

When registering an External Audit, the system should use the selected vessel and standard to pre-filter or suggest the correct recognised organisation from `vessel_audit_ro_delegation`.

If no delegation row exists, the UI should show a clear master-data warning instead of silently allowing an incorrect organisation selection.
