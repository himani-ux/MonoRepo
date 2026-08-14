# Generated manually for VIMS Audit Phase 1 Step 1.1 on 2026-07-27.

import uuid

from django.db import migrations, models
from django.utils import timezone


CREATE_AUDIT_DOMAIN_TABLES_SQL = r"""
IF OBJECT_ID('dbo.audit_detail', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_detail (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        psc_inspection_id char(32) NOT NULL,
        audit_classification varchar(30) NOT NULL,
        auditee_type varchar(30) NOT NULL,
        auditee_office_dept varchar(40) NULL,
        audit_subtype varchar(40) NOT NULL,
        audit_subtype_other nvarchar(200) NULL,
        lead_auditor_name nvarchar(200) NOT NULL,
        lead_auditor_designation nvarchar(200) NULL,
        lead_auditor_company nvarchar(200) NOT NULL,
        lead_auditor_qual nvarchar(200) NULL,
        conductor_user_id varchar(100) NULL,
        lead_auditor_user_id varchar(100) NULL,
        pic_user_id_resolved varchar(100) NULL,
        trigger_reason varchar(40) NOT NULL,
        audit_plan_id uniqueidentifier NULL,
        parent_audit_id char(32) NULL,
        audit_start_date date NOT NULL,
        audit_end_date date NULL,
        opening_meeting_at datetimeoffset NULL,
        closing_meeting_at datetimeoffset NULL,
        audit_scope nvarchar(max) NULL,
        terms_of_reference nvarchar(max) NULL,
        audit_summary nvarchar(max) NULL,
        equipment_tested nvarchar(max) NULL,
        prev_internal_ca_verified varchar(10) NULL,
        prev_external_ca_verified varchar(10) NULL,
        status varchar(30) NOT NULL DEFAULT 'PLANNED',
        audit_date_year_month AS (CONVERT(char(7), audit_start_date, 126)) PERSISTED,
        external_audit_subtypes_csv nvarchar(200) NULL,
        external_audit_org_id uniqueidentifier NULL,
        external_audit_org_type varchar(20) NULL,
        external_lead_auditor_name nvarchar(200) NULL,
        external_lead_auditor_credential nvarchar(200) NULL,
        flag_state_code varchar(10) NULL,
        parent_audit_event_id uniqueidentifier NULL,
        linked_cert_ids_csv nvarchar(500) NULL,
        certificate_impact varchar(40) NULL,
        external_closure_status varchar(30) NULL,
        is_cycle_resetting bit NOT NULL DEFAULT 0,
        cycle_reset_reason nvarchar(max) NULL,
        cycle_reset_authorised_by varchar(100) NULL,
        cycle_reset_authorised_at datetimeoffset NULL,
        late_registration_reason nvarchar(max) NULL,
        late_registered_by varchar(100) NULL,
        late_registered_at datetimeoffset NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL,
        is_deleted bit NOT NULL DEFAULT 0,
        client_id uniqueidentifier NULL,
        sync_version int NOT NULL DEFAULT 1,
        CONSTRAINT UQ_audit_detail_psc_inspection UNIQUE (psc_inspection_id)
    );
END;

IF OBJECT_ID('dbo.audit_standards', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_standards (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_detail_id uniqueidentifier NOT NULL,
        standard_code varchar(20) NOT NULL,
        sequence_no int NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        CONSTRAINT UQ_audit_standards UNIQUE (audit_detail_id, standard_code)
    );
END;

IF OBJECT_ID('dbo.audit_team_member', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_team_member (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_detail_id uniqueidentifier NOT NULL,
        member_name nvarchar(200) NOT NULL,
        member_designation nvarchar(200) NULL,
        member_company nvarchar(200) NULL,
        member_role varchar(40) NULL,
        sequence_no int NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        is_deleted bit NOT NULL DEFAULT 0
    );
END;

IF OBJECT_ID('dbo.audit_meeting_attendee', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_meeting_attendee (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_detail_id uniqueidentifier NOT NULL,
        attendee_name nvarchar(200) NOT NULL,
        attendee_rank nvarchar(100) NULL,
        opening_present bit NOT NULL DEFAULT 0,
        closing_present bit NOT NULL DEFAULT 0,
        sequence_no int NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        is_deleted bit NOT NULL DEFAULT 0
    );
END;

IF OBJECT_ID('dbo.audit_area_summary', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_area_summary (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_detail_id uniqueidentifier NOT NULL,
        area_code varchar(40) NOT NULL,
        status varchar(20) NULL,
        remarks nvarchar(max) NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        CONSTRAINT UQ_audit_area_summary UNIQUE (audit_detail_id, area_code)
    );
END;

IF OBJECT_ID('dbo.audit_schedule_block', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_schedule_block (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_detail_id uniqueidentifier NOT NULL,
        block_date date NULL,
        time_from time NULL,
        time_to time NULL,
        activity nvarchar(300) NULL,
        sequence_no int NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        is_deleted bit NOT NULL DEFAULT 0
    );
END;

IF OBJECT_ID('dbo.audit_finding', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_finding (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        psc_deficiency_id char(32) NOT NULL,
        audit_detail_id uniqueidentifier NOT NULL,
        audit_classification varchar(30) NOT NULL,
        finding_type varchar(20) NOT NULL,
        nc_category varchar(20) NULL,
        observation_category varchar(40) NULL,
        standard_code varchar(20) NULL,
        rule_book_type varchar(20) NULL,
        rule_clause_id uniqueidentifier NULL,
        clause_ref_text nvarchar(200) NULL,
        objective_evidence nvarchar(max) NULL,
        description nvarchar(max) NULL,
        checklist_item_id uniqueidentifier NULL,
        priority varchar(20) NOT NULL DEFAULT 'MEDIUM',
        original_due_date date NULL,
        extended_due_date date NULL,
        extension_reason nvarchar(max) NULL,
        is_overdue bit NOT NULL DEFAULT 0,
        certificates_at_risk nvarchar(100) NULL,
        is_fleetwide_relevance bit NOT NULL DEFAULT 0,
        linked_circular_id uniqueidentifier NULL,
        is_external bit NOT NULL DEFAULT 0,
        applies_to_cert_ids_csv nvarchar(500) NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        is_deleted bit NOT NULL DEFAULT 0,
        CONSTRAINT UQ_audit_finding_psc_deficiency UNIQUE (psc_deficiency_id)
    );
END;

IF OBJECT_ID('dbo.audit_finding_clause', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_finding_clause (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_finding_id uniqueidentifier NOT NULL,
        rule_book_type varchar(20) NOT NULL,
        rule_clause_id uniqueidentifier NULL,
        clause_ref_text nvarchar(200) NULL,
        clause_subref_text nvarchar(200) NULL,
        is_primary bit NOT NULL DEFAULT 0,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        is_deleted bit NOT NULL DEFAULT 0
    );
END;

IF OBJECT_ID('dbo.audit_finding_nc', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_finding_nc (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_finding_id uniqueidentifier NOT NULL UNIQUE,
        immediate_action_text nvarchar(max) NULL,
        immediate_action_completed_at date NULL,
        master_immediate_sign_name nvarchar(200) NULL,
        master_immediate_sign_at datetimeoffset NULL,
        rca_method varchar(40) NULL,
        rca_method_other nvarchar(200) NULL,
        rca_template_id uniqueidentifier NULL,
        problem_statement nvarchar(max) NULL,
        why_1 nvarchar(max) NULL,
        why_2 nvarchar(max) NULL,
        why_3 nvarchar(max) NULL,
        why_4 nvarchar(max) NULL,
        why_5 nvarchar(max) NULL,
        root_cause_categories nvarchar(200) NULL,
        root_cause_summary nvarchar(max) NULL,
        corrective_action_text nvarchar(max) NULL,
        target_completion_date date NULL,
        actual_completion_date date NULL,
        preventive_action_text nvarchar(max) NULL,
        sms_amendment_required bit NOT NULL DEFAULT 0,
        sms_amendment_doc_ref nvarchar(200) NULL,
        drafted_by_user_id varchar(100) NULL,
        effectiveness_review_date date NULL,
        effectiveness_review_method varchar(40) NULL,
        effectiveness_assessment_text nvarchar(max) NULL,
        effectiveness_outcome varchar(20) NULL,
        effectiveness_further_action_text nvarchar(max) NULL,
        effectiveness_signer_name nvarchar(200) NULL,
        effectiveness_signer_at datetimeoffset NULL,
        effectiveness_overdue bit NOT NULL DEFAULT 0,
        is_external_tier varchar(20) NULL,
        acceptance_review_date date NULL,
        acceptance_rca_adequacy_text nvarchar(max) NULL,
        acceptance_decision varchar(20) NULL,
        acceptance_return_reason nvarchar(max) NULL,
        acceptance_signer_name nvarchar(200) NULL,
        acceptance_signer_at datetimeoffset NULL,
        verifying_auditor_name nvarchar(200) NULL,
        verifying_authority_org nvarchar(200) NULL,
        verification_method varchar(40) NULL,
        certificate_endorsement_type varchar(40) NULL,
        certificate_endorsement_ref nvarchar(100) NULL,
        auditor_assessment_text nvarchar(max) NULL,
        final_closure_status varchar(30) NULL,
        resubmit_by_date date NULL,
        auditor_verification_sign_at datetimeoffset NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL
    );
END;

IF OBJECT_ID('dbo.audit_finding_obs', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_finding_obs (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_finding_id uniqueidentifier NOT NULL UNIQUE,
        responded_by_name nvarchar(200) NULL,
        responded_by_rank nvarchar(100) NULL,
        target_closure_date date NULL,
        immediate_action_text nvarchar(max) NULL,
        root_cause_text nvarchar(max) NULL,
        corrective_action_text nvarchar(max) NULL,
        preventive_action_text nvarchar(max) NULL,
        sms_amendment_required bit NOT NULL DEFAULT 0,
        sms_amendment_doc_ref nvarchar(200) NULL,
        actual_closure_date date NULL,
        master_sign_name nvarchar(200) NULL,
        master_sign_at datetimeoffset NULL,
        acceptance_review_date date NULL,
        acceptance_adequacy_text nvarchar(max) NULL,
        acceptance_decision varchar(20) NULL,
        acceptance_return_reason nvarchar(max) NULL,
        acceptance_signer_name nvarchar(200) NULL,
        acceptance_signer_at datetimeoffset NULL,
        verifying_auditor_name nvarchar(200) NULL,
        verifying_authority_org nvarchar(200) NULL,
        verification_method varchar(40) NULL,
        auditor_remarks_text nvarchar(max) NULL,
        closure_status varchar(30) NULL,
        resubmit_by_date date NULL,
        auditor_verification_sign_at datetimeoffset NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL
    );
END;

IF OBJECT_ID('dbo.audit_finding_signature', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_finding_signature (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_finding_id uniqueidentifier NOT NULL,
        signer_user_id varchar(100) NULL,
        signature_event_type varchar(40) NOT NULL,
        signed_at datetimeoffset NULL,
        signed_pdf_attachment_id uniqueidentifier NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL
    );
END;

IF OBJECT_ID('dbo.audit_finding_sign_event', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_finding_sign_event (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_finding_id uniqueidentifier NOT NULL,
        user_id varchar(100) NOT NULL,
        rank_at_signing varchar(60) NULL,
        part_label varchar(20) NOT NULL,
        claimed_sign_datetime datetimeoffset NULL,
        actual_entered_at datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        backdate_reason nvarchar(max) NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.audit_signature', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_signature (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_detail_id uniqueidentifier NOT NULL,
        lead_auditor_sign_at datetimeoffset NULL,
        master_sign_at datetimeoffset NULL,
        seq_manager_close_at datetimeoffset NULL,
        signature_image_path nvarchar(500) NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL
    );
END;

IF OBJECT_ID('dbo.audit_attachment', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_attachment (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_detail_id uniqueidentifier NOT NULL,
        audit_finding_id uniqueidentifier NULL,
        file_name nvarchar(255) NOT NULL,
        file_path nvarchar(500) NOT NULL,
        file_size int NULL,
        mime_type varchar(100) NOT NULL,
        category varchar(40) NOT NULL,
        attachment_version varchar(20) NOT NULL DEFAULT 'FINAL',
        attestation_required bit NOT NULL DEFAULT 0,
        attestation_note nvarchar(max) NULL,
        description nvarchar(500) NULL,
        linked_pdf_generation_id uniqueidentifier NULL,
        pdf_hash_validation_status varchar(30) NULL,
        validated_at datetimeoffset NULL,
        validator_message nvarchar(500) NULL,
        uploaded_by varchar(100) NOT NULL,
        uploaded_at datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        is_deleted bit NOT NULL DEFAULT 0
    );
END;

IF OBJECT_ID('dbo.audit_pdf_generation', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.audit_pdf_generation (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_detail_id uniqueidentifier NOT NULL,
        audit_finding_id uniqueidentifier NULL,
        pdf_kind varchar(40) NOT NULL,
        pdf_version int NOT NULL DEFAULT 1,
        content_hash char(64) NOT NULL,
        qr_payload nvarchar(max) NULL,
        is_superseded bit NOT NULL DEFAULT 0,
        generated_by varchar(100) NOT NULL,
        generated_at datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.notification_delivery_log', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.notification_delivery_log (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        psc_notification_id char(32) NOT NULL,
        channel varchar(20) NOT NULL,
        recipient_address nvarchar(254) NULL,
        status varchar(30) NOT NULL DEFAULT 'PENDING',
        attempt_count int NOT NULL DEFAULT 0,
        first_attempted_at datetimeoffset NULL,
        last_attempted_at datetimeoffset NULL,
        last_error nvarchar(max) NULL,
        sent_at datetimeoffset NULL,
        resolved_offline_reason nvarchar(max) NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.cert_writeback_outbox', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.cert_writeback_outbox (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_detail_id uniqueidentifier NOT NULL,
        vessel_cert_id uniqueidentifier NOT NULL,
        writeback_payload nvarchar(max) NOT NULL,
        expected_cert_version int NOT NULL,
        status varchar(30) NOT NULL DEFAULT 'QUEUED',
        attempt_count int NOT NULL DEFAULT 0,
        last_error nvarchar(max) NULL,
        dead_lettered_at datetimeoffset NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL
    );
END;

IF OBJECT_ID('dbo.flag_state_notification_log', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.flag_state_notification_log (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        audit_detail_id uniqueidentifier NOT NULL,
        notified_at datetimeoffset NULL,
        notified_to nvarchar(200) NULL,
        ack_received_at datetimeoffset NULL,
        notification_ref nvarchar(200) NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL
    );
END;
"""


DROP_AUDIT_DOMAIN_TABLES_SQL = r"""
DROP TABLE IF EXISTS dbo.flag_state_notification_log;
DROP TABLE IF EXISTS dbo.cert_writeback_outbox;
DROP TABLE IF EXISTS dbo.notification_delivery_log;
DROP TABLE IF EXISTS dbo.audit_pdf_generation;
DROP TABLE IF EXISTS dbo.audit_attachment;
DROP TABLE IF EXISTS dbo.audit_signature;
DROP TABLE IF EXISTS dbo.audit_finding_sign_event;
DROP TABLE IF EXISTS dbo.audit_finding_signature;
DROP TABLE IF EXISTS dbo.audit_finding_obs;
DROP TABLE IF EXISTS dbo.audit_finding_nc;
DROP TABLE IF EXISTS dbo.audit_finding_clause;
DROP TABLE IF EXISTS dbo.audit_finding;
DROP TABLE IF EXISTS dbo.audit_schedule_block;
DROP TABLE IF EXISTS dbo.audit_area_summary;
DROP TABLE IF EXISTS dbo.audit_meeting_attendee;
DROP TABLE IF EXISTS dbo.audit_team_member;
DROP TABLE IF EXISTS dbo.audit_standards;
DROP TABLE IF EXISTS dbo.audit_detail;
"""


def uuid_pk():
    return models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)


def created_fields():
    return [
        ("created_by", models.CharField(blank=True, max_length=100, null=True)),
        ("created_date", models.DateTimeField(default=timezone.now)),
    ]


def soft_delete_field():
    return ("is_deleted", models.BooleanField(default=False))


def updated_fields():
    return [
        ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
        ("updated_date", models.DateTimeField(blank=True, null=True)),
    ]


class Migration(migrations.Migration):
    dependencies = [
        ("inspection", "0017_alter_inspectionreport_description"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=CREATE_AUDIT_DOMAIN_TABLES_SQL,
                    reverse_sql=DROP_AUDIT_DOMAIN_TABLES_SQL,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name="AuditDetail",
                    fields=[
                        ("id", uuid_pk()),
                        ("psc_inspection_id", models.CharField(max_length=32, unique=True)),
                        ("audit_classification", models.CharField(max_length=30)),
                        ("auditee_type", models.CharField(max_length=30)),
                        ("auditee_office_dept", models.CharField(blank=True, max_length=40, null=True)),
                        ("audit_subtype", models.CharField(max_length=40)),
                        ("audit_subtype_other", models.CharField(blank=True, max_length=200, null=True)),
                        ("lead_auditor_name", models.CharField(max_length=200)),
                        ("lead_auditor_designation", models.CharField(blank=True, max_length=200, null=True)),
                        ("lead_auditor_company", models.CharField(max_length=200)),
                        ("lead_auditor_qual", models.CharField(blank=True, max_length=200, null=True)),
                        ("conductor_user_id", models.CharField(blank=True, max_length=100, null=True)),
                        ("lead_auditor_user_id", models.CharField(blank=True, max_length=100, null=True)),
                        ("pic_user_id_resolved", models.CharField(blank=True, max_length=100, null=True)),
                        ("trigger_reason", models.CharField(max_length=40)),
                        ("audit_plan_id", models.UUIDField(blank=True, null=True)),
                        ("parent_audit_id", models.CharField(blank=True, max_length=32, null=True)),
                        ("audit_start_date", models.DateField()),
                        ("audit_end_date", models.DateField(blank=True, null=True)),
                        ("opening_meeting_at", models.DateTimeField(blank=True, null=True)),
                        ("closing_meeting_at", models.DateTimeField(blank=True, null=True)),
                        ("audit_scope", models.TextField(blank=True, null=True)),
                        ("terms_of_reference", models.TextField(blank=True, null=True)),
                        ("audit_summary", models.TextField(blank=True, null=True)),
                        ("equipment_tested", models.TextField(blank=True, null=True)),
                        ("prev_internal_ca_verified", models.CharField(blank=True, max_length=10, null=True)),
                        ("prev_external_ca_verified", models.CharField(blank=True, max_length=10, null=True)),
                        ("status", models.CharField(default="PLANNED", max_length=30)),
                        ("external_audit_subtypes_csv", models.CharField(blank=True, max_length=200, null=True)),
                        ("external_audit_org_id", models.UUIDField(blank=True, null=True)),
                        ("external_audit_org_type", models.CharField(blank=True, max_length=20, null=True)),
                        ("external_lead_auditor_name", models.CharField(blank=True, max_length=200, null=True)),
                        ("external_lead_auditor_credential", models.CharField(blank=True, max_length=200, null=True)),
                        ("flag_state_code", models.CharField(blank=True, max_length=10, null=True)),
                        ("parent_audit_event_id", models.UUIDField(blank=True, null=True)),
                        ("linked_cert_ids_csv", models.CharField(blank=True, max_length=500, null=True)),
                        ("certificate_impact", models.CharField(blank=True, max_length=40, null=True)),
                        ("external_closure_status", models.CharField(blank=True, max_length=30, null=True)),
                        ("is_cycle_resetting", models.BooleanField(default=False)),
                        ("cycle_reset_reason", models.TextField(blank=True, null=True)),
                        ("cycle_reset_authorised_by", models.CharField(blank=True, max_length=100, null=True)),
                        ("cycle_reset_authorised_at", models.DateTimeField(blank=True, null=True)),
                        ("late_registration_reason", models.TextField(blank=True, null=True)),
                        ("late_registered_by", models.CharField(blank=True, max_length=100, null=True)),
                        ("late_registered_at", models.DateTimeField(blank=True, null=True)),
                        *created_fields(),
                        *updated_fields(),
                        soft_delete_field(),
                        ("client_id", models.UUIDField(blank=True, null=True)),
                        ("sync_version", models.IntegerField(default=1)),
                    ],
                    options={"db_table": "audit_detail"},
                ),
                migrations.CreateModel(
                    name="AuditStandard",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_detail_id", models.UUIDField()),
                        ("standard_code", models.CharField(max_length=20)),
                        ("sequence_no", models.IntegerField(default=1)),
                        *created_fields(),
                    ],
                    options={
                        "db_table": "audit_standards",
                        "constraints": [
                            models.UniqueConstraint(
                                fields=("audit_detail_id", "standard_code"),
                                name="UQ_audit_standards",
                            )
                        ],
                    },
                ),
                migrations.CreateModel(
                    name="AuditTeamMember",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_detail_id", models.UUIDField()),
                        ("member_name", models.CharField(max_length=200)),
                        ("member_designation", models.CharField(blank=True, max_length=200, null=True)),
                        ("member_company", models.CharField(blank=True, max_length=200, null=True)),
                        ("member_role", models.CharField(blank=True, max_length=40, null=True)),
                        ("sequence_no", models.IntegerField(default=1)),
                        *created_fields(),
                        soft_delete_field(),
                    ],
                    options={"db_table": "audit_team_member"},
                ),
                migrations.CreateModel(
                    name="AuditMeetingAttendee",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_detail_id", models.UUIDField()),
                        ("attendee_name", models.CharField(max_length=200)),
                        ("attendee_rank", models.CharField(blank=True, max_length=100, null=True)),
                        ("opening_present", models.BooleanField(default=False)),
                        ("closing_present", models.BooleanField(default=False)),
                        ("sequence_no", models.IntegerField(default=1)),
                        *created_fields(),
                        soft_delete_field(),
                    ],
                    options={"db_table": "audit_meeting_attendee"},
                ),
                migrations.CreateModel(
                    name="AuditAreaSummary",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_detail_id", models.UUIDField()),
                        ("area_code", models.CharField(max_length=40)),
                        ("status", models.CharField(blank=True, max_length=20, null=True)),
                        ("remarks", models.TextField(blank=True, null=True)),
                        *created_fields(),
                    ],
                    options={
                        "db_table": "audit_area_summary",
                        "constraints": [
                            models.UniqueConstraint(
                                fields=("audit_detail_id", "area_code"),
                                name="UQ_audit_area_summary",
                            )
                        ],
                    },
                ),
                migrations.CreateModel(
                    name="AuditScheduleBlock",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_detail_id", models.UUIDField()),
                        ("block_date", models.DateField(blank=True, null=True)),
                        ("time_from", models.TimeField(blank=True, null=True)),
                        ("time_to", models.TimeField(blank=True, null=True)),
                        ("activity", models.CharField(blank=True, max_length=300, null=True)),
                        ("sequence_no", models.IntegerField(default=1)),
                        *created_fields(),
                        soft_delete_field(),
                    ],
                    options={"db_table": "audit_schedule_block"},
                ),
                migrations.CreateModel(
                    name="AuditFinding",
                    fields=[
                        ("id", uuid_pk()),
                        ("psc_deficiency_id", models.CharField(max_length=32, unique=True)),
                        ("audit_detail_id", models.UUIDField()),
                        ("audit_classification", models.CharField(max_length=30)),
                        ("finding_type", models.CharField(max_length=20)),
                        ("nc_category", models.CharField(blank=True, max_length=20, null=True)),
                        ("observation_category", models.CharField(blank=True, max_length=40, null=True)),
                        ("standard_code", models.CharField(blank=True, max_length=20, null=True)),
                        ("rule_book_type", models.CharField(blank=True, max_length=20, null=True)),
                        ("rule_clause_id", models.UUIDField(blank=True, null=True)),
                        ("clause_ref_text", models.CharField(blank=True, max_length=200, null=True)),
                        ("objective_evidence", models.TextField(blank=True, null=True)),
                        ("description", models.TextField(blank=True, null=True)),
                        ("checklist_item_id", models.UUIDField(blank=True, null=True)),
                        ("priority", models.CharField(default="MEDIUM", max_length=20)),
                        ("original_due_date", models.DateField(blank=True, null=True)),
                        ("extended_due_date", models.DateField(blank=True, null=True)),
                        ("extension_reason", models.TextField(blank=True, null=True)),
                        ("is_overdue", models.BooleanField(default=False)),
                        ("certificates_at_risk", models.CharField(blank=True, max_length=100, null=True)),
                        ("is_fleetwide_relevance", models.BooleanField(default=False)),
                        ("linked_circular_id", models.UUIDField(blank=True, null=True)),
                        ("is_external", models.BooleanField(default=False)),
                        ("applies_to_cert_ids_csv", models.CharField(blank=True, max_length=500, null=True)),
                        *created_fields(),
                        soft_delete_field(),
                    ],
                    options={"db_table": "audit_finding"},
                ),
                migrations.CreateModel(
                    name="AuditFindingClause",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_finding_id", models.UUIDField()),
                        ("rule_book_type", models.CharField(max_length=20)),
                        ("rule_clause_id", models.UUIDField(blank=True, null=True)),
                        ("clause_ref_text", models.CharField(blank=True, max_length=200, null=True)),
                        ("clause_subref_text", models.CharField(blank=True, max_length=200, null=True)),
                        ("is_primary", models.BooleanField(default=False)),
                        *created_fields(),
                        soft_delete_field(),
                    ],
                    options={"db_table": "audit_finding_clause"},
                ),
                migrations.CreateModel(
                    name="AuditFindingNC",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_finding_id", models.UUIDField(unique=True)),
                        ("immediate_action_text", models.TextField(blank=True, null=True)),
                        ("immediate_action_completed_at", models.DateField(blank=True, null=True)),
                        ("master_immediate_sign_name", models.CharField(blank=True, max_length=200, null=True)),
                        ("master_immediate_sign_at", models.DateTimeField(blank=True, null=True)),
                        ("rca_method", models.CharField(blank=True, max_length=40, null=True)),
                        ("rca_method_other", models.CharField(blank=True, max_length=200, null=True)),
                        ("rca_template_id", models.UUIDField(blank=True, null=True)),
                        ("problem_statement", models.TextField(blank=True, null=True)),
                        ("why_1", models.TextField(blank=True, null=True)),
                        ("why_2", models.TextField(blank=True, null=True)),
                        ("why_3", models.TextField(blank=True, null=True)),
                        ("why_4", models.TextField(blank=True, null=True)),
                        ("why_5", models.TextField(blank=True, null=True)),
                        ("root_cause_categories", models.CharField(blank=True, max_length=200, null=True)),
                        ("root_cause_summary", models.TextField(blank=True, null=True)),
                        ("corrective_action_text", models.TextField(blank=True, null=True)),
                        ("target_completion_date", models.DateField(blank=True, null=True)),
                        ("actual_completion_date", models.DateField(blank=True, null=True)),
                        ("preventive_action_text", models.TextField(blank=True, null=True)),
                        ("sms_amendment_required", models.BooleanField(default=False)),
                        ("sms_amendment_doc_ref", models.CharField(blank=True, max_length=200, null=True)),
                        ("drafted_by_user_id", models.CharField(blank=True, max_length=100, null=True)),
                        ("effectiveness_review_date", models.DateField(blank=True, null=True)),
                        ("effectiveness_review_method", models.CharField(blank=True, max_length=40, null=True)),
                        ("effectiveness_assessment_text", models.TextField(blank=True, null=True)),
                        ("effectiveness_outcome", models.CharField(blank=True, max_length=20, null=True)),
                        ("effectiveness_further_action_text", models.TextField(blank=True, null=True)),
                        ("effectiveness_signer_name", models.CharField(blank=True, max_length=200, null=True)),
                        ("effectiveness_signer_at", models.DateTimeField(blank=True, null=True)),
                        ("effectiveness_overdue", models.BooleanField(default=False)),
                        ("is_external_tier", models.CharField(blank=True, max_length=20, null=True)),
                        ("acceptance_review_date", models.DateField(blank=True, null=True)),
                        ("acceptance_rca_adequacy_text", models.TextField(blank=True, null=True)),
                        ("acceptance_decision", models.CharField(blank=True, max_length=20, null=True)),
                        ("acceptance_return_reason", models.TextField(blank=True, null=True)),
                        ("acceptance_signer_name", models.CharField(blank=True, max_length=200, null=True)),
                        ("acceptance_signer_at", models.DateTimeField(blank=True, null=True)),
                        ("verifying_auditor_name", models.CharField(blank=True, max_length=200, null=True)),
                        ("verifying_authority_org", models.CharField(blank=True, max_length=200, null=True)),
                        ("verification_method", models.CharField(blank=True, max_length=40, null=True)),
                        ("certificate_endorsement_type", models.CharField(blank=True, max_length=40, null=True)),
                        ("certificate_endorsement_ref", models.CharField(blank=True, max_length=100, null=True)),
                        ("auditor_assessment_text", models.TextField(blank=True, null=True)),
                        ("final_closure_status", models.CharField(blank=True, max_length=30, null=True)),
                        ("resubmit_by_date", models.DateField(blank=True, null=True)),
                        ("auditor_verification_sign_at", models.DateTimeField(blank=True, null=True)),
                        *created_fields(),
                        *updated_fields(),
                    ],
                    options={"db_table": "audit_finding_nc"},
                ),
                migrations.CreateModel(
                    name="AuditFindingOBS",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_finding_id", models.UUIDField(unique=True)),
                        ("responded_by_name", models.CharField(blank=True, max_length=200, null=True)),
                        ("responded_by_rank", models.CharField(blank=True, max_length=100, null=True)),
                        ("target_closure_date", models.DateField(blank=True, null=True)),
                        ("immediate_action_text", models.TextField(blank=True, null=True)),
                        ("root_cause_text", models.TextField(blank=True, null=True)),
                        ("corrective_action_text", models.TextField(blank=True, null=True)),
                        ("preventive_action_text", models.TextField(blank=True, null=True)),
                        ("sms_amendment_required", models.BooleanField(default=False)),
                        ("sms_amendment_doc_ref", models.CharField(blank=True, max_length=200, null=True)),
                        ("actual_closure_date", models.DateField(blank=True, null=True)),
                        ("master_sign_name", models.CharField(blank=True, max_length=200, null=True)),
                        ("master_sign_at", models.DateTimeField(blank=True, null=True)),
                        ("acceptance_review_date", models.DateField(blank=True, null=True)),
                        ("acceptance_adequacy_text", models.TextField(blank=True, null=True)),
                        ("acceptance_decision", models.CharField(blank=True, max_length=20, null=True)),
                        ("acceptance_return_reason", models.TextField(blank=True, null=True)),
                        ("acceptance_signer_name", models.CharField(blank=True, max_length=200, null=True)),
                        ("acceptance_signer_at", models.DateTimeField(blank=True, null=True)),
                        ("verifying_auditor_name", models.CharField(blank=True, max_length=200, null=True)),
                        ("verifying_authority_org", models.CharField(blank=True, max_length=200, null=True)),
                        ("verification_method", models.CharField(blank=True, max_length=40, null=True)),
                        ("auditor_remarks_text", models.TextField(blank=True, null=True)),
                        ("closure_status", models.CharField(blank=True, max_length=30, null=True)),
                        ("resubmit_by_date", models.DateField(blank=True, null=True)),
                        ("auditor_verification_sign_at", models.DateTimeField(blank=True, null=True)),
                        *created_fields(),
                        *updated_fields(),
                    ],
                    options={"db_table": "audit_finding_obs"},
                ),
                migrations.CreateModel(
                    name="AuditFindingSignature",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_finding_id", models.UUIDField()),
                        ("signer_user_id", models.CharField(blank=True, max_length=100, null=True)),
                        ("signature_event_type", models.CharField(max_length=40)),
                        ("signed_at", models.DateTimeField(blank=True, null=True)),
                        ("signed_pdf_attachment_id", models.UUIDField(blank=True, null=True)),
                        *created_fields(),
                        *updated_fields(),
                    ],
                    options={"db_table": "audit_finding_signature"},
                ),
                migrations.CreateModel(
                    name="AuditFindingSignEvent",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_finding_id", models.UUIDField()),
                        ("user_id", models.CharField(max_length=100)),
                        ("rank_at_signing", models.CharField(blank=True, max_length=60, null=True)),
                        ("part_label", models.CharField(max_length=20)),
                        ("claimed_sign_datetime", models.DateTimeField(blank=True, null=True)),
                        ("actual_entered_at", models.DateTimeField(default=timezone.now)),
                        ("backdate_reason", models.TextField(blank=True, null=True)),
                        *created_fields(),
                    ],
                    options={"db_table": "audit_finding_sign_event"},
                ),
                migrations.CreateModel(
                    name="AuditSignature",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_detail_id", models.UUIDField()),
                        ("lead_auditor_sign_at", models.DateTimeField(blank=True, null=True)),
                        ("master_sign_at", models.DateTimeField(blank=True, null=True)),
                        ("seq_manager_close_at", models.DateTimeField(blank=True, null=True)),
                        ("signature_image_path", models.CharField(blank=True, max_length=500, null=True)),
                        *created_fields(),
                        *updated_fields(),
                    ],
                    options={"db_table": "audit_signature"},
                ),
                migrations.CreateModel(
                    name="AuditAttachment",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_detail_id", models.UUIDField()),
                        ("audit_finding_id", models.UUIDField(blank=True, null=True)),
                        ("file_name", models.CharField(max_length=255)),
                        ("file_path", models.CharField(max_length=500)),
                        ("file_size", models.IntegerField(blank=True, null=True)),
                        ("mime_type", models.CharField(max_length=100)),
                        ("category", models.CharField(max_length=40)),
                        ("attachment_version", models.CharField(default="FINAL", max_length=20)),
                        ("attestation_required", models.BooleanField(default=False)),
                        ("attestation_note", models.TextField(blank=True, null=True)),
                        ("description", models.CharField(blank=True, max_length=500, null=True)),
                        ("linked_pdf_generation_id", models.UUIDField(blank=True, null=True)),
                        ("pdf_hash_validation_status", models.CharField(blank=True, max_length=30, null=True)),
                        ("validated_at", models.DateTimeField(blank=True, null=True)),
                        ("validator_message", models.CharField(blank=True, max_length=500, null=True)),
                        ("uploaded_by", models.CharField(max_length=100)),
                        ("uploaded_at", models.DateTimeField(default=timezone.now)),
                        (soft_delete_field()),
                    ],
                    options={"db_table": "audit_attachment"},
                ),
                migrations.CreateModel(
                    name="AuditPdfGeneration",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_detail_id", models.UUIDField()),
                        ("audit_finding_id", models.UUIDField(blank=True, null=True)),
                        ("pdf_kind", models.CharField(max_length=40)),
                        ("pdf_version", models.IntegerField(default=1)),
                        ("content_hash", models.CharField(max_length=64)),
                        ("qr_payload", models.TextField(blank=True, null=True)),
                        ("is_superseded", models.BooleanField(default=False)),
                        ("generated_by", models.CharField(max_length=100)),
                        ("generated_at", models.DateTimeField(default=timezone.now)),
                    ],
                    options={"db_table": "audit_pdf_generation"},
                ),
                migrations.CreateModel(
                    name="NotificationDeliveryLog",
                    fields=[
                        ("id", uuid_pk()),
                        ("psc_notification_id", models.CharField(max_length=32)),
                        ("channel", models.CharField(max_length=20)),
                        ("recipient_address", models.CharField(blank=True, max_length=254, null=True)),
                        ("status", models.CharField(default="PENDING", max_length=30)),
                        ("attempt_count", models.IntegerField(default=0)),
                        ("first_attempted_at", models.DateTimeField(blank=True, null=True)),
                        ("last_attempted_at", models.DateTimeField(blank=True, null=True)),
                        ("last_error", models.TextField(blank=True, null=True)),
                        ("sent_at", models.DateTimeField(blank=True, null=True)),
                        ("resolved_offline_reason", models.TextField(blank=True, null=True)),
                        *created_fields(),
                    ],
                    options={"db_table": "notification_delivery_log"},
                ),
                migrations.CreateModel(
                    name="CertWritebackOutbox",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_detail_id", models.UUIDField()),
                        ("vessel_cert_id", models.UUIDField()),
                        ("writeback_payload", models.TextField()),
                        ("expected_cert_version", models.IntegerField()),
                        ("status", models.CharField(default="QUEUED", max_length=30)),
                        ("attempt_count", models.IntegerField(default=0)),
                        ("last_error", models.TextField(blank=True, null=True)),
                        ("dead_lettered_at", models.DateTimeField(blank=True, null=True)),
                        *created_fields(),
                        *updated_fields(),
                    ],
                    options={"db_table": "cert_writeback_outbox"},
                ),
                migrations.CreateModel(
                    name="FlagStateNotificationLog",
                    fields=[
                        ("id", uuid_pk()),
                        ("audit_detail_id", models.UUIDField()),
                        ("notified_at", models.DateTimeField(blank=True, null=True)),
                        ("notified_to", models.CharField(blank=True, max_length=200, null=True)),
                        ("ack_received_at", models.DateTimeField(blank=True, null=True)),
                        ("notification_ref", models.CharField(blank=True, max_length=200, null=True)),
                        *created_fields(),
                        *updated_fields(),
                    ],
                    options={"db_table": "flag_state_notification_log"},
                ),
            ],
        ),
    ]

