1. HRM501 Table – Structural Limitations and Intended Usage
1.1 Absence of Vessel Reference
The hrm501 table does not contain a vessel_id column.

Therefore:
Vessel mapping must not be derived from hrm501.

Any logic attempting to associate a crew member directly to a vessel using hrm501 is structurally incorrect.
Vessel association must be resolved through appropriate relational tables.

1.2 Absence of Password Field

The hrm501 table does not contain a password column.
Therefore:
hrm501 must not be used for authentication.
Any authentication or login logic referencing hrm501 is incorrect.
Password validation and credential verification must be handled exclusively by the appropriate authentication table.



2. Crew Authentication Source
2.1 Correct Authentication Table
All Ship-Side authentication-related operations must use the Ship_UsersLogin table.

This includes:
Username / Crew ID validation
Password storage and verification
Login status management
Account activation or deactivation logic
hrm501 must not be used for:
Password validation
Login authentication
Session handling
Separation of concerns must be maintained:
Ship_UsersLogin → Authentication
hrm501 → Crew master and rank reference


3. Rank Mapping via HRM501
3.1 Purpose of HRM501

The hrm501 table will be used specifically to determine the rank of a crew member.
It acts as a reference layer between the crew and the rank master table.

3.2 Rank Storage Structure

The rank_name column in hrm501 does not store a textual rank name.

Instead:

rank_name stores a UUID.
This UUID corresponds to the id column in the master_applied_rank table.
Correct relationship:
hrm501.rank_name  →  master_applied_rank.id (UUID)
To retrieve the actual rank name or hierarchy:
A join must be performed with master_applied_rank.
Under no circumstances should the system treat rank_name as a plain text field.


4. Vessel Relationship Mapping
4.1 Source of Vessel-Crew Relationship

Crew-to-vessel mapping must be derived from the Crew_Onboarding_History table.

The hrm501 table does not contain vessel association data and must not be used for this purpose.

4.2 Correct Relationship Flow
Crew → Crew_Onboarding_History → Vessel

The Crew_Onboarding_History table is the authoritative source for:
Vessel assignment history
Active vessel mapping
Onboarding records
Any current vessel allocation logic must be built using this table.


5. VesselData Column Name Mismatch
5.1 Identified Mismatch

There is a discrepancy between expected and actual column names in the VesselData table.
Incorrect column names currently referenced in some parts of the system:
vessel_name

vessel_code

imo_number

5.2 Correct Column Names

As verified from the VesselData table in the ksm_marine_live database, the correct column names are:

vesselName

vesselCode

imoNumber

All queries, serializers, ORM mappings, and API responses must be updated to use the correct camelCase naming.


6. Crew Assignment Field Correction
6.1 Incorrect Field Usage

The system currently references:

crew_ref_id
This is not aligned with the expected assignment logic.

6.2 Required Correction

Instead of crew_ref_id, the assignment should use:
crew_id (e.g., KSM0000 format)
The assignment reference must clearly represent:
A specific crew member (via Crew ID)
Ambiguous reference fields must be avoided to maintain relational clarity.


7. Role and Permission Management via msc_profile Table
7.1 Existing Table: msc_profile

There is already an existing table named msc_profile that supports role and permission configuration.

Observed relevant columns:

id (PK, uniqueidentifier, not null)

profile_id (uniqueidentifier, not null)

profile_name (varchar(255), not null)

work_side (bit, not null)

form_ids (varchar(max), null)

process_ids (varchar(max), null)

created_on (datetime2(7), not null)

is_active (bit, not null)

is_deleted (bit, not null)

This table should be treated as the central configuration layer for role-based permissions.

7.2 Permission Definition Strategy

All process-level and form-level permissions must be defined in the database using the following columns:

process_ids

form_ids

These fields must contain the identifiers of allowed processes and forms mapped to a given profile.

This ensures that:

Permissions are managed dynamically

No permission logic is hardcoded in application code

Changes in access control do not require redeployment

7.3 Work Side Differentiation

The work_side column differentiates role applicability:

Ship Side

Office Side

Permissions for both ship-side users and office-side users must be defined through:

process_ids

form_ids

work_side flag

This allows a single profile table to manage:

Ship-side operational permissions

Office-side administrative permissions

Without creating separate hardcoded role logic.

7.4 Architectural Principle

All permissions for:

Processes

Forms

Operational workflows

Must be retrieved from msc_profile.

The application must:

Identify the user's profile.

Read form_ids and process_ids.

Grant or restrict access dynamically.

Under no circumstances should:

Process access be hardcoded.

Form visibility be controlled using static conditional statements.

Role-based logic be embedded directly in frontend or backend source code.