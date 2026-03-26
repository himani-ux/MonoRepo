# Database Schema

This document describes the schema from the application perspective. It includes:

- shared unmanaged tables
- PSC-owned tables
- legacy Circular tables
- legacy ORB tables

Where a table is unmanaged, it must be treated as read-only by Django migrations.

## 1. Schema Conventions

- Primary keys are usually `uniqueidentifier`
- Soft deletes use `is_deleted`
- Audit fields typically include `created_by`, `created_date`, `updated_by`, `updated_date`
- Offline sync tables include `client_id` and `sync_version`

## 2. Authentication and Mapping Tables

### 2.1 `VesselData`

Purpose:
- vessel master lookup used by inspection, dashboard, sync, and legacy modules

Key fields:
- `id`: vessel UUID
- `vesselName`: vessel display name
- `vesselCode`: vessel code
- `imoNumber`: IMO number
- `is_active`, `is_deleted`: active flags

Relationships:
- referenced by inspections, dashboard drill-down, sync scope, and legacy modules

### 2.2 `HRM501`

Purpose:
- crew master table for vessel-side users

Key fields:
- `id`: crew UUID
- `CrewID`: crew login/display identifier
- `first_name`, `surname`
- `rank_name`
- `department_name`
- `user_id`
- `password`
- `is_active`, `is_deleted`

Relationships:
- used for vessel authentication
- used for crew assignment display names

### 2.3 `users`

Purpose:
- office user master table

Key fields:
- `employee_id`: primary key
- `employee_name`
- `display_name`
- `email_id`
- `username`
- `password`
- `employee_role`
- `department`
- `is_active`, `is_deleted`

Relationships:
- used for office authentication
- used for office notification recipients and ownership fields

### 2.4 `master_RoleByVessel`

Purpose:
- limits office users to assigned vessels

Key fields:
- `Id`
- `VesselId`
- `RoleId`
- `UserId`
- `IsActive`
- `is_deleted`

Relationships:
- used by `core.vessel_access`

### 2.5 `master_role`

Purpose:
- office role master data

Key fields:
- `id`
- `role_name`
- `is_active`
- `is_deleted`

### 2.6 `mapping_role_user`

Purpose:
- maps office identifiers to role/profile IDs

Key fields:
- `id`
- `userid`
- `role_id`
- `is_active`
- `is_deleted`

### 2.7 `msc_profiles`

Purpose:
- stores form and process permissions for legacy office roles

Key fields:
- `id`
- `profile_id`
- `profile_name`
- `work_side`
- `form_ids`
- `process_ids`
- `is_active`
- `is_deleted`

### 2.8 `Mapping_CrewAssReviewers`

Purpose:
- global reviewer mapping for office PIC and DPA

Key fields:
- profile identifiers for PIC and DPA reviewer mapping

Used by:
- `get_office_global_reviewer_role`
- JWT claim enrichment

### 2.9 `Crew_Onboarding_History`

Purpose:
- resolves active vessel for crew and vessel-side access

Key fields:
- `id`
- `CrewID`
- `Vessel`
- `SignOnDate`
- `SignOffDate`
- `is_active`
- `is_deleted`

### 2.10 `Ship_UsersLogin`

Purpose:
- vessel login credential source

Key fields:
- `id`
- `CrewID`
- `Password`
- `is_active`
- `is_deleted`

## 3. PSC Master Tables

### 3.1 `MOU_Master`

Purpose:
- Memorandum of Understanding regions

Key fields:
- `MOU_Code`
- `MOU_Name`
- `Region`
- `Is_Active`
- `Sort_Order`

### 3.2 `PSC_Action_Codes`

Purpose:
- action taken code master

Key fields:
- `Action_Code`
- `Definition`
- `Description`
- `Is_Detention`
- `Requires_Follow_Up`
- `Is_Active`

### 3.3 `PIC_Master`

Purpose:
- person-in-charge lookup

Key fields:
- `PIC_Code`
- `PIC_Name`
- `Department`
- `Sort_Order`

### 3.4 `PSC_Def_Category`

Purpose:
- top-level PSC deficiency categories

Key fields:
- `Category_Code`
- `Category_Name`
- `Sort_Order`
- `Is_Active`

### 3.5 `PSC_Def_Subcategory`

Purpose:
- second-level PSC deficiency category grouping

Key fields:
- `Subcategory_Code`
- `Category_Code`
- `Subcategory_Name`
- `Sort_Order`
- `Is_Active`

### 3.6 `PSC_Def_Code`

Purpose:
- master PSC deficiency codes

Key fields:
- `Def_Code`
- `Category_Code`
- `Subcategory_Code`
- `Def_Name`
- `Sort_Order`
- `Is_Active`

### 3.7 `CLC_Category`

Purpose:
- cause taxonomy for CLC

Key fields:
- `Category_ID`
- `Category_Code`
- `Category_Name`
- `Category_Type`
- `Parent_ID`
- `Sort_Order`

### 3.8 `CLC_Item`

Purpose:
- individual cause items

Key fields:
- `CLC_Code`
- `Category_ID`
- `Item_Name`
- `Item_Description`
- `Sort_Order`
- `Is_Active`

## 4. Inspection Tables

### 4.1 `psc_inspection`

Purpose:
- primary inspection record

Key fields:
- `id`
- `vessel_id`
- `inspection_type`
- `psc_subtype`
- `inspection_date`
- `port_place`
- `country`
- `mou_id`
- `authority`
- `inspector_name`
- `report_reference`
- `is_detention`
- `def_reported`
- `status`
- `parent_inspection`
- `revision_no`
- `pic_comment`
- `dpa_comment`
- `is_deleted`
- `client_id`
- `sync_version`

Relationships:
- one inspection has many reports
- one inspection has many deficiencies
- follow-up inspections point back to a parent inspection

### 4.2 `psc_inspection_report`

Purpose:
- uploaded inspection report files

Key fields:
- `id`
- `inspection`
- `report_type`
- `file_name`
- `file_path`
- `file_size`
- `mime_type`
- `description`
- `is_deleted`
- `uploaded_by`
- `uploaded_at`

### 4.3 `psc_deficiency`

Purpose:
- deficiency record linked to an inspection

Key fields:
- `id`
- `inspection`
- `def_code_id`
- `def_code`
- `description`
- `action_code_id`
- `action_code`
- `target_date`
- `is_cleared`
- `cleared_date`
- `cleared_by_follow_up`
- `sequence_no`
- `car`
- `assigned_crew_id`
- `def_status`
- `reviewer_crew_id`
- `owner_rank`
- `owner_name`
- `reviewer_rank`
- `reviewer_name`
- `is_deleted`
- `client_id`
- `sync_version`

Relationships:
- one deficiency belongs to one inspection
- one deficiency has one CAR
- one deficiency has many action history rows

### 4.4 `psc_deficiency_action_history`

Purpose:
- tracks action code changes over time

Key fields:
- `id`
- `deficiency`
- `previous_action_code_id`
- `previous_action_code`
- `new_action_code_id`
- `new_action_code`
- `follow_up_inspection`
- `change_reason`
- `changed_by`
- `changed_at`

### 4.5 `psc_car`

Purpose:
- CAR record auto-created from deficiencies

Key fields:
- `id`
- `car_number`
- `status`
- `root_cause_summary`
- `target_date`
- `initial_action_code`
- `pic_comment`
- `pic_accepted_by`
- `pic_accepted_at`
- `rework_reason`
- `rework_requested_by`
- `rework_requested_at`
- `rework_count`
- `dpa_comment`
- `dpa_closed_by`
- `dpa_closed_at`
- `verification_pending`
- `last_action`
- `last_action_by`
- `last_action_at`
- `last_action_comment`
- `is_deleted`
- `client_id`
- `sync_version`

Relationships:
- one CAR belongs to one deficiency
- one CAR has many corrective actions
- one CAR has many evidence records
- one CAR has many physical verification records

## 5. CAR Supporting Tables

### 5.1 `psc_car_clc_mapping`

Purpose:
- associates CARs with CLC items

Key fields:
- `id`
- `car`
- `clc_item_id`
- `custom_cause_text`
- `created_by`
- `created_date`

### 5.2 `psc_corrective_action`

Purpose:
- corrective action rows inside a CAR

Key fields:
- `id`
- `car`
- `action_type`
- `description`
- `owner_crew_id`
- `owner_user_id`
- `due_date`
- `is_completed`
- `completed_at`
- `completion_remarks`
- `sequence_no`
- `is_deleted`
- `client_id`
- `sync_version`

### 5.3 `psc_evidence`

Purpose:
- evidence attachments for a CAR

Key fields:
- `id`
- `car`
- `evidence_type`
- `file_name`
- `file_path`
- `file_size`
- `mime_type`
- `description`
- `is_deleted`
- `uploaded_by`
- `uploaded_at`
- `client_id`
- `sync_status`

### 5.4 `psc_physical_verification`

Purpose:
- physical verification visits for closed CARs

Key fields:
- `id`
- `car`
- `status`
- `scheduled_date`
- `visit_date`
- `visit_port`
- `verifier_user_id`
- `verifier_crew_id`
- `comments`
- `is_deleted`
- `created_by`
- `created_date`
- `updated_by`
- `updated_date`
- `closed_by`
- `closed_at`

### 5.5 `psc_activity_history`

Purpose:
- timeline visible to users and sync

Key fields:
- `id`
- `entity_type`
- `entity_id`
- `vessel_id`
- `event_type`
- `event_description`
- `performed_by`
- `performed_by_name`
- `performed_at`
- `metadata`

### 5.6 `psc_audit_log`

Purpose:
- field-level audit trail for office review and traceability

Key fields:
- `id`
- `entity_type`
- `entity_id`
- `action`
- `field_name`
- `old_value`
- `new_value`
- `performed_by`
- `performed_by_role`
- `performed_at`
- `ip_address`
- `user_agent`
- `is_office_edit_assist`

## 6. Sync Tables

### 6.1 `psc_sync_log`

Purpose:
- records sync batches

Key fields:
- `id`
- `vessel_id`
- `sync_id`
- `sync_type`
- `sync_status`
- `records_sent`
- `records_received`
- `payload_checksum`
- `started_at`
- `completed_at`
- `error_message`
- `retry_count`
- `created_by`
- `created_date`

### 6.2 `psc_sync_log_detail`

Purpose:
- records per-entity sync results

Key fields:
- `id`
- `sync_log`
- `entity_type`
- `entity_id`
- `client_id`
- `operation`
- `sync_status`
- `error_message`
- `server_version`
- `client_version`

### 6.3 `psc_sync_conflict`

Purpose:
- unresolved sync conflicts

Key fields:
- `id`
- `vessel_id`
- `entity_type`
- `entity_id`
- `server_data`
- `vessel_data`
- `conflicting_fields`
- `status`
- `resolution`
- `resolved_by`
- `resolved_at`
- `resolution_notes`
- `created_date`

### 6.4 `psc_sync_token`

Purpose:
- per-vessel last sync point

Key fields:
- `id`
- `vessel_id`
- `last_sync_at`
- `last_sync_id`
- `last_server_version`
- `updated_at`

## 7. Notification Tables

### 7.1 `psc_notification`

Purpose:
- in-app notifications

Key fields:
- `id`
- `recipient_type`
- `recipient_id`
- `vessel_id`
- `notification_type`
- `title`
- `message`
- `entity_type`
- `entity_id`
- `is_read`
- `read_at`
- `created_date`

## 8. Legacy Circular Tables

### 8.1 `msc_data`

Purpose:
- circular master/notification records

Key fields:
- `id`
- `sr_no`
- `msc_type`
- `dept`
- `category`
- `sub_category`
- `second_sub_category`
- `priority`
- `title`
- `description`
- `attachment_path`
- `published_on`
- `is_deleted`

### 8.2 `msc_notification`

Purpose:
- per-crew delivery and acknowledgment tracking

Key fields:
- `msc_sr_no`
- `crew_id`
- `delivered_at`
- `seen_at`
- `reminder_sent_at`

### 8.3 `msc_reminder`

Purpose:
- reminder tracking

### 8.4 `department`

Purpose:
- department lookup

### 8.5 `final_crew_list`

Purpose:
- legacy crew list support

### 8.6 `MscProfile`, `MscType`, `MscSubCat`, `MscPriority`, `MscCategory`, `Msc2ndSubCat`

Purpose:
- legacy Circular taxonomy and permission tables

## 9. Legacy ORB Tables

### 9.1 `ORBCodes`

Purpose:
- ORB code master

Key fields:
- `id`
- `code`
- `part`
- `description`

### 9.2 `Operations`

Purpose:
- ORB operation entries

Key fields:
- `id`
- `vessel`
- `date`
- `orb_code_id`
- `item_no`
- `record_of_operation`
- `status`
- `submitted_by`
- `submitted_at`
- `approved_by`
- `approved_at`
- `rejected_by`
- `rejected_at`
- `created_at`
- `created_by`
- `updated_at`
- `updated_by`
- `is_deleted`
- `entry_no`
- `page_no`
- `line_no`
- `IP`
- `master_print`
- `parent_entry_id`

### 9.3 `vessel_tank_details`

Purpose:
- vessel tank lookup for ORB

### 9.4 `current_vessel`

Purpose:
- currently selected vessel in legacy ORB

### 9.5 `GeneratedPDFs`

Purpose:
- metadata for exported PDFs

## 10. Text ER Diagram

```text
VesselData 1 --- n psc_inspection
psc_inspection 1 --- n psc_inspection_report
psc_inspection 1 --- n psc_deficiency
psc_deficiency 1 --- 1 psc_car
psc_car 1 --- n psc_corrective_action
psc_car 1 --- n psc_evidence
psc_car 1 --- n psc_physical_verification
psc_car n --- n CLC_Item via psc_car_clc_mapping
psc_inspection 1 --- n psc_activity_history
psc_car 1 --- n psc_activity_history
psc_sync_log 1 --- n psc_sync_log_detail
psc_sync_conflict is linked to vessel_id + entity_id
psc_notification is keyed by recipient_type + recipient_id

VesselData 1 --- n ORB Operations
VesselData 1 --- n legacy circular notification tables
HRM501 1 --- n crew-scoped workflows
users 1 --- n office-scoped workflows
```

