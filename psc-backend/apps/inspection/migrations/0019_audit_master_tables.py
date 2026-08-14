# Generated manually for VIMS Audit Phase 1 Step 1.2 on 2026-07-27.

import uuid

from django.db import migrations, models
from django.utils import timezone


CREATE_AUDIT_MASTER_TABLES_SQL = r"""
IF OBJECT_ID('dbo.master_audit_plan', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_audit_plan (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        target_vessel_id uniqueidentifier NULL,
        target_office_dept varchar(40) NULL,
        audit_classification varchar(30) NOT NULL,
        audit_standards_csv nvarchar(100) NOT NULL,
        planned_window_start date NULL,
        planned_window_end date NULL,
        extended_due_date date NULL,
        extension_form_ref nvarchar(100) NULL,
        extension_requested_at datetimeoffset NULL,
        extension_requested_by varchar(100) NULL,
        extension_requested_reason nvarchar(max) NULL,
        extension_approved_at datetimeoffset NULL,
        extension_approved_by varchar(100) NULL,
        extension_approved_reason nvarchar(max) NULL,
        flag_notified bit NOT NULL DEFAULT 0,
        flag_notification_date date NULL,
        flag_notification_ref nvarchar(100) NULL,
        flag_notification_attachment nvarchar(500) NULL,
        is_additional bit NOT NULL DEFAULT 0,
        additional_reason nvarchar(max) NULL,
        trigger_event_type varchar(30) NULL,
        trigger_event_ref nvarchar(200) NULL,
        cancellation_reason nvarchar(max) NULL,
        next_planned_date date NULL,
        cancelled_by varchar(100) NULL,
        cancelled_at datetimeoffset NULL,
        status varchar(30) NOT NULL DEFAULT 'PLANNED',
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL,
        is_deleted bit NOT NULL DEFAULT 0
    );
END;

IF OBJECT_ID('dbo.master_audit_classification', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_audit_classification (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        classification_code varchar(30) NOT NULL,
        display_name nvarchar(100) NOT NULL,
        is_active bit NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        CONSTRAINT UQ_master_audit_classification_code UNIQUE (classification_code)
    );
END;

IF OBJECT_ID('dbo.master_audit_subtype', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_audit_subtype (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        classification_code varchar(30) NOT NULL,
        subtype_code varchar(40) NOT NULL,
        display_name nvarchar(120) NOT NULL,
        is_external bit NOT NULL DEFAULT 0,
        is_active bit NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        CONSTRAINT UQ_master_audit_subtype UNIQUE (classification_code, subtype_code)
    );
END;

IF OBJECT_ID('dbo.master_audit_finding_category', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_audit_finding_category (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        category_code varchar(30) NOT NULL,
        display_name nvarchar(100) NOT NULL,
        default_target_days int NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        CONSTRAINT UQ_master_audit_finding_category_code UNIQUE (category_code)
    );
END;

IF OBJECT_ID('dbo.master_audit_area', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_audit_area (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        area_code varchar(40) NOT NULL,
        display_name nvarchar(120) NOT NULL,
        is_vessel_only bit NOT NULL DEFAULT 0,
        sequence_no int NOT NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        CONSTRAINT UQ_master_audit_area_code UNIQUE (area_code)
    );
END;

IF OBJECT_ID('dbo.master_audit_checklist', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_audit_checklist (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        checklist_code varchar(20) NOT NULL,
        name nvarchar(150) NOT NULL,
        auditee_type varchar(30) NOT NULL,
        scope_dept varchar(40) NULL,
        ship_type_scope varchar(60) NULL,
        source_form_ref varchar(40) NOT NULL,
        code_version varchar(40) NULL,
        is_active bit NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        CONSTRAINT UQ_master_audit_checklist_code UNIQUE (checklist_code)
    );
END;

IF OBJECT_ID('dbo.master_audit_checklist_item', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_audit_checklist_item (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        master_audit_checklist_id uniqueidentifier NOT NULL,
        location_code varchar(20) NULL,
        item_code varchar(20) NOT NULL,
        question nvarchar(max) NOT NULL,
        guideline nvarchar(max) NULL,
        regulation_ref nvarchar(200) NULL,
        ksm_sms_ref nvarchar(200) NULL,
        ship_type varchar(30) NULL,
        sequence_no int NOT NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_audit_qualified_auditor', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_audit_qualified_auditor (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id varchar(100) NOT NULL,
        qualification_text nvarchar(200) NOT NULL,
        qualification_date date NOT NULL,
        expiry_date date NOT NULL,
        scope_standards_csv varchar(60) NOT NULL,
        qualifying_body nvarchar(200) NULL,
        certificate_attachment_id uniqueidentifier NULL,
        auditor_scope varchar(20) NOT NULL,
        qualified_for_seq bit NOT NULL DEFAULT 0,
        is_active bit NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL
    );
END;

IF OBJECT_ID('dbo.master_hod_assignment', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_hod_assignment (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        dept varchar(40) NOT NULL,
        user_id varchar(100) NOT NULL,
        is_acting bit NOT NULL DEFAULT 0,
        effective_from date NOT NULL,
        effective_to date NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_rca_template', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_rca_template (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        category varchar(40) NOT NULL,
        title nvarchar(200) NOT NULL,
        template_text nvarchar(max) NOT NULL,
        example_evidence_hint nvarchar(500) NULL,
        applicable_def_categories nvarchar(200) NULL,
        code_version varchar(40) NULL,
        is_active bit NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL
    );
END;

IF OBJECT_ID('dbo.master_audit_window_rule', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_audit_window_rule (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        standard_code varchar(20) NOT NULL,
        subtype_code varchar(40) NOT NULL,
        window_open_offset_months int NOT NULL,
        window_close_offset_months int NOT NULL,
        cadence_months int NOT NULL,
        regulatory_citation nvarchar(200) NOT NULL,
        is_active bit NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_ism_clause', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_ism_clause (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        clause_no varchar(20) NOT NULL,
        clause_text nvarchar(max) NOT NULL,
        section_no varchar(10) NULL,
        code_version varchar(40) NOT NULL DEFAULT 'ISM 2018',
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_isps_clause', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_isps_clause (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        section_no varchar(20) NOT NULL,
        section_title nvarchar(300) NOT NULL,
        section_text nvarchar(max) NULL,
        code_version varchar(40) NOT NULL DEFAULT 'ISPS 2003',
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_mlc_title', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_mlc_title (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        title_no varchar(20) NOT NULL,
        regulation_no varchar(20) NULL,
        standard_a_code varchar(20) NULL,
        title_text nvarchar(max) NOT NULL,
        code_version varchar(60) NOT NULL DEFAULT 'MLC 2006 (2014/2016/2018/2022 amendments)',
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_solas_chapter', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_solas_chapter (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        chapter_no varchar(10) NOT NULL,
        regulation_no varchar(20) NULL,
        title nvarchar(300) NOT NULL,
        code_version varchar(40) NOT NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_stcw_section', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_stcw_section (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        section_no varchar(20) NOT NULL,
        title nvarchar(300) NOT NULL,
        code_version varchar(40) NOT NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_marpol_annex', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_marpol_annex (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        annex_no varchar(10) NOT NULL,
        regulation_no varchar(20) NULL,
        title nvarchar(300) NOT NULL,
        code_version varchar(40) NOT NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_colreg_rule', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_colreg_rule (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        rule_no varchar(10) NOT NULL,
        title nvarchar(300) NOT NULL,
        code_version varchar(40) NOT NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_ksm_sms_chapter', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_ksm_sms_chapter (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        chapter_code varchar(40) NOT NULL,
        chapter_name nvarchar(200) NOT NULL,
        code_version varchar(40) NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_external_audit_org', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_external_audit_org (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        name nvarchar(200) NOT NULL,
        org_type varchar(20) NOT NULL,
        country varchar(80) NULL,
        linked_class_society_ref varchar(40) NULL,
        is_active bit NOT NULL DEFAULT 1,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.vessel_audit_ro_delegation', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.vessel_audit_ro_delegation (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        target_vessel_id uniqueidentifier NOT NULL,
        standard_code varchar(20) NOT NULL,
        master_external_audit_org_id uniqueidentifier NOT NULL,
        effective_from date NOT NULL,
        effective_to date NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;

IF OBJECT_ID('dbo.master_external_auditor', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_external_auditor (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        name nvarchar(200) NOT NULL,
        master_external_audit_org_id uniqueidentifier NULL,
        review_status varchar(20) NOT NULL DEFAULT 'PENDING_REVIEW',
        last_seen_at datetimeoffset NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET(),
        updated_by varchar(100) NULL,
        updated_date datetimeoffset NULL
    );
END;

IF OBJECT_ID('dbo.master_external_auditor_category_map', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.master_external_auditor_category_map (
        id uniqueidentifier NOT NULL PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        free_text_pattern nvarchar(200) NOT NULL,
        canonical_iacs_code varchar(20) NOT NULL,
        created_by varchar(100) NULL,
        created_date datetimeoffset NOT NULL DEFAULT SYSDATETIMEOFFSET()
    );
END;
"""


DROP_AUDIT_MASTER_TABLES_SQL = r"""
DROP TABLE IF EXISTS dbo.master_external_auditor_category_map;
DROP TABLE IF EXISTS dbo.master_external_auditor;
DROP TABLE IF EXISTS dbo.vessel_audit_ro_delegation;
DROP TABLE IF EXISTS dbo.master_external_audit_org;
DROP TABLE IF EXISTS dbo.master_ksm_sms_chapter;
DROP TABLE IF EXISTS dbo.master_colreg_rule;
DROP TABLE IF EXISTS dbo.master_marpol_annex;
DROP TABLE IF EXISTS dbo.master_stcw_section;
DROP TABLE IF EXISTS dbo.master_solas_chapter;
DROP TABLE IF EXISTS dbo.master_mlc_title;
DROP TABLE IF EXISTS dbo.master_isps_clause;
DROP TABLE IF EXISTS dbo.master_ism_clause;
DROP TABLE IF EXISTS dbo.master_audit_window_rule;
DROP TABLE IF EXISTS dbo.master_rca_template;
DROP TABLE IF EXISTS dbo.master_hod_assignment;
DROP TABLE IF EXISTS dbo.master_audit_qualified_auditor;
DROP TABLE IF EXISTS dbo.master_audit_checklist_item;
DROP TABLE IF EXISTS dbo.master_audit_checklist;
DROP TABLE IF EXISTS dbo.master_audit_area;
DROP TABLE IF EXISTS dbo.master_audit_finding_category;
DROP TABLE IF EXISTS dbo.master_audit_subtype;
DROP TABLE IF EXISTS dbo.master_audit_classification;
DROP TABLE IF EXISTS dbo.master_audit_plan;
"""


def uuid_pk():
    return models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)


def created_fields():
    return [
        ("created_by", models.CharField(blank=True, max_length=100, null=True)),
        ("created_date", models.DateTimeField(default=timezone.now)),
    ]


def updated_fields():
    return [
        ("updated_by", models.CharField(blank=True, max_length=100, null=True)),
        ("updated_date", models.DateTimeField(blank=True, null=True)),
    ]


class Migration(migrations.Migration):
    dependencies = [
        ("inspection", "0018_audit_domain_tables"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=CREATE_AUDIT_MASTER_TABLES_SQL,
                    reverse_sql=DROP_AUDIT_MASTER_TABLES_SQL,
                ),
            ],
            state_operations=[
                migrations.CreateModel(
                    name="MasterAuditPlan",
                    fields=[
                        ("id", uuid_pk()),
                        ("target_vessel_id", models.UUIDField(blank=True, null=True)),
                        ("target_office_dept", models.CharField(blank=True, max_length=40, null=True)),
                        ("audit_classification", models.CharField(max_length=30)),
                        ("audit_standards_csv", models.CharField(max_length=100)),
                        ("planned_window_start", models.DateField(blank=True, null=True)),
                        ("planned_window_end", models.DateField(blank=True, null=True)),
                        ("extended_due_date", models.DateField(blank=True, null=True)),
                        ("extension_form_ref", models.CharField(blank=True, max_length=100, null=True)),
                        ("extension_requested_at", models.DateTimeField(blank=True, null=True)),
                        ("extension_requested_by", models.CharField(blank=True, max_length=100, null=True)),
                        ("extension_requested_reason", models.TextField(blank=True, null=True)),
                        ("extension_approved_at", models.DateTimeField(blank=True, null=True)),
                        ("extension_approved_by", models.CharField(blank=True, max_length=100, null=True)),
                        ("extension_approved_reason", models.TextField(blank=True, null=True)),
                        ("flag_notified", models.BooleanField(default=False)),
                        ("flag_notification_date", models.DateField(blank=True, null=True)),
                        ("flag_notification_ref", models.CharField(blank=True, max_length=100, null=True)),
                        (
                            "flag_notification_attachment",
                            models.CharField(blank=True, max_length=500, null=True),
                        ),
                        ("is_additional", models.BooleanField(default=False)),
                        ("additional_reason", models.TextField(blank=True, null=True)),
                        ("trigger_event_type", models.CharField(blank=True, max_length=30, null=True)),
                        ("trigger_event_ref", models.CharField(blank=True, max_length=200, null=True)),
                        ("cancellation_reason", models.TextField(blank=True, null=True)),
                        ("next_planned_date", models.DateField(blank=True, null=True)),
                        ("cancelled_by", models.CharField(blank=True, max_length=100, null=True)),
                        ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                        ("status", models.CharField(default="PLANNED", max_length=30)),
                        *created_fields(),
                        *updated_fields(),
                        ("is_deleted", models.BooleanField(default=False)),
                    ],
                    options={"db_table": "master_audit_plan"},
                ),
                migrations.CreateModel(
                    name="MasterAuditClassification",
                    fields=[
                        ("id", uuid_pk()),
                        ("classification_code", models.CharField(max_length=30, unique=True)),
                        ("display_name", models.CharField(max_length=100)),
                        ("is_active", models.BooleanField(default=True)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_audit_classification"},
                ),
                migrations.CreateModel(
                    name="MasterAuditSubtype",
                    fields=[
                        ("id", uuid_pk()),
                        ("classification_code", models.CharField(max_length=30)),
                        ("subtype_code", models.CharField(max_length=40)),
                        ("display_name", models.CharField(max_length=120)),
                        ("is_external", models.BooleanField(default=False)),
                        ("is_active", models.BooleanField(default=True)),
                        *created_fields(),
                    ],
                    options={
                        "db_table": "master_audit_subtype",
                        "constraints": [
                            models.UniqueConstraint(
                                fields=("classification_code", "subtype_code"),
                                name="UQ_master_audit_subtype",
                            )
                        ],
                    },
                ),
                migrations.CreateModel(
                    name="MasterAuditFindingCategory",
                    fields=[
                        ("id", uuid_pk()),
                        ("category_code", models.CharField(max_length=30, unique=True)),
                        ("display_name", models.CharField(max_length=100)),
                        ("default_target_days", models.IntegerField(blank=True, null=True)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_audit_finding_category"},
                ),
                migrations.CreateModel(
                    name="MasterAuditArea",
                    fields=[
                        ("id", uuid_pk()),
                        ("area_code", models.CharField(max_length=40, unique=True)),
                        ("display_name", models.CharField(max_length=120)),
                        ("is_vessel_only", models.BooleanField(default=False)),
                        ("sequence_no", models.IntegerField()),
                        *created_fields(),
                    ],
                    options={"db_table": "master_audit_area"},
                ),
                migrations.CreateModel(
                    name="MasterAuditChecklist",
                    fields=[
                        ("id", uuid_pk()),
                        ("checklist_code", models.CharField(max_length=20, unique=True)),
                        ("name", models.CharField(max_length=150)),
                        ("auditee_type", models.CharField(max_length=30)),
                        ("scope_dept", models.CharField(blank=True, max_length=40, null=True)),
                        ("ship_type_scope", models.CharField(blank=True, max_length=60, null=True)),
                        ("source_form_ref", models.CharField(max_length=40)),
                        ("code_version", models.CharField(blank=True, max_length=40, null=True)),
                        ("is_active", models.BooleanField(default=True)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_audit_checklist"},
                ),
                migrations.CreateModel(
                    name="MasterAuditChecklistItem",
                    fields=[
                        ("id", uuid_pk()),
                        ("master_audit_checklist_id", models.UUIDField()),
                        ("location_code", models.CharField(blank=True, max_length=20, null=True)),
                        ("item_code", models.CharField(max_length=20)),
                        ("question", models.TextField()),
                        ("guideline", models.TextField(blank=True, null=True)),
                        ("regulation_ref", models.CharField(blank=True, max_length=200, null=True)),
                        ("ksm_sms_ref", models.CharField(blank=True, max_length=200, null=True)),
                        ("ship_type", models.CharField(blank=True, max_length=30, null=True)),
                        ("sequence_no", models.IntegerField()),
                        *created_fields(),
                    ],
                    options={"db_table": "master_audit_checklist_item"},
                ),
                migrations.CreateModel(
                    name="MasterAuditQualifiedAuditor",
                    fields=[
                        ("id", uuid_pk()),
                        ("user_id", models.CharField(max_length=100)),
                        ("qualification_text", models.CharField(max_length=200)),
                        ("qualification_date", models.DateField()),
                        ("expiry_date", models.DateField()),
                        ("scope_standards_csv", models.CharField(max_length=60)),
                        ("qualifying_body", models.CharField(blank=True, max_length=200, null=True)),
                        ("certificate_attachment_id", models.UUIDField(blank=True, null=True)),
                        ("auditor_scope", models.CharField(max_length=20)),
                        ("qualified_for_seq", models.BooleanField(default=False)),
                        ("is_active", models.BooleanField(default=True)),
                        *created_fields(),
                        *updated_fields(),
                    ],
                    options={"db_table": "master_audit_qualified_auditor"},
                ),
                migrations.CreateModel(
                    name="MasterHodAssignment",
                    fields=[
                        ("id", uuid_pk()),
                        ("dept", models.CharField(max_length=40)),
                        ("user_id", models.CharField(max_length=100)),
                        ("is_acting", models.BooleanField(default=False)),
                        ("effective_from", models.DateField()),
                        ("effective_to", models.DateField(blank=True, null=True)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_hod_assignment"},
                ),
                migrations.CreateModel(
                    name="MasterRcaTemplate",
                    fields=[
                        ("id", uuid_pk()),
                        ("category", models.CharField(max_length=40)),
                        ("title", models.CharField(max_length=200)),
                        ("template_text", models.TextField()),
                        ("example_evidence_hint", models.CharField(blank=True, max_length=500, null=True)),
                        (
                            "applicable_def_categories",
                            models.CharField(blank=True, max_length=200, null=True),
                        ),
                        ("code_version", models.CharField(blank=True, max_length=40, null=True)),
                        ("is_active", models.BooleanField(default=True)),
                        *created_fields(),
                        *updated_fields(),
                    ],
                    options={"db_table": "master_rca_template"},
                ),
                migrations.CreateModel(
                    name="MasterAuditWindowRule",
                    fields=[
                        ("id", uuid_pk()),
                        ("standard_code", models.CharField(max_length=20)),
                        ("subtype_code", models.CharField(max_length=40)),
                        ("window_open_offset_months", models.IntegerField()),
                        ("window_close_offset_months", models.IntegerField()),
                        ("cadence_months", models.IntegerField()),
                        ("regulatory_citation", models.CharField(max_length=200)),
                        ("is_active", models.BooleanField(default=True)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_audit_window_rule"},
                ),
                migrations.CreateModel(
                    name="MasterIsmClause",
                    fields=[
                        ("id", uuid_pk()),
                        ("clause_no", models.CharField(max_length=20)),
                        ("clause_text", models.TextField()),
                        ("section_no", models.CharField(blank=True, max_length=10, null=True)),
                        ("code_version", models.CharField(default="ISM 2018", max_length=40)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_ism_clause"},
                ),
                migrations.CreateModel(
                    name="MasterIspsClause",
                    fields=[
                        ("id", uuid_pk()),
                        ("section_no", models.CharField(max_length=20)),
                        ("section_title", models.CharField(max_length=300)),
                        ("section_text", models.TextField(blank=True, null=True)),
                        ("code_version", models.CharField(default="ISPS 2003", max_length=40)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_isps_clause"},
                ),
                migrations.CreateModel(
                    name="MasterMlcTitle",
                    fields=[
                        ("id", uuid_pk()),
                        ("title_no", models.CharField(max_length=20)),
                        ("regulation_no", models.CharField(blank=True, max_length=20, null=True)),
                        ("standard_a_code", models.CharField(blank=True, max_length=20, null=True)),
                        ("title_text", models.TextField()),
                        (
                            "code_version",
                            models.CharField(
                                default="MLC 2006 (2014/2016/2018/2022 amendments)",
                                max_length=60,
                            ),
                        ),
                        *created_fields(),
                    ],
                    options={"db_table": "master_mlc_title"},
                ),
                migrations.CreateModel(
                    name="MasterSolasChapter",
                    fields=[
                        ("id", uuid_pk()),
                        ("chapter_no", models.CharField(max_length=10)),
                        ("regulation_no", models.CharField(blank=True, max_length=20, null=True)),
                        ("title", models.CharField(max_length=300)),
                        ("code_version", models.CharField(max_length=40)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_solas_chapter"},
                ),
                migrations.CreateModel(
                    name="MasterStcwSection",
                    fields=[
                        ("id", uuid_pk()),
                        ("section_no", models.CharField(max_length=20)),
                        ("title", models.CharField(max_length=300)),
                        ("code_version", models.CharField(max_length=40)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_stcw_section"},
                ),
                migrations.CreateModel(
                    name="MasterMarpolAnnex",
                    fields=[
                        ("id", uuid_pk()),
                        ("annex_no", models.CharField(max_length=10)),
                        ("regulation_no", models.CharField(blank=True, max_length=20, null=True)),
                        ("title", models.CharField(max_length=300)),
                        ("code_version", models.CharField(max_length=40)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_marpol_annex"},
                ),
                migrations.CreateModel(
                    name="MasterColregRule",
                    fields=[
                        ("id", uuid_pk()),
                        ("rule_no", models.CharField(max_length=10)),
                        ("title", models.CharField(max_length=300)),
                        ("code_version", models.CharField(max_length=40)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_colreg_rule"},
                ),
                migrations.CreateModel(
                    name="MasterKsmSmsChapter",
                    fields=[
                        ("id", uuid_pk()),
                        ("chapter_code", models.CharField(max_length=40)),
                        ("chapter_name", models.CharField(max_length=200)),
                        ("code_version", models.CharField(blank=True, max_length=40, null=True)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_ksm_sms_chapter"},
                ),
                migrations.CreateModel(
                    name="MasterExternalAuditOrg",
                    fields=[
                        ("id", uuid_pk()),
                        ("name", models.CharField(max_length=200)),
                        ("org_type", models.CharField(max_length=20)),
                        ("country", models.CharField(blank=True, max_length=80, null=True)),
                        (
                            "linked_class_society_ref",
                            models.CharField(blank=True, max_length=40, null=True),
                        ),
                        ("is_active", models.BooleanField(default=True)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_external_audit_org"},
                ),
                migrations.CreateModel(
                    name="VesselAuditRoDelegation",
                    fields=[
                        ("id", uuid_pk()),
                        ("target_vessel_id", models.UUIDField()),
                        ("standard_code", models.CharField(max_length=20)),
                        ("master_external_audit_org_id", models.UUIDField()),
                        ("effective_from", models.DateField()),
                        ("effective_to", models.DateField(blank=True, null=True)),
                        *created_fields(),
                    ],
                    options={"db_table": "vessel_audit_ro_delegation"},
                ),
                migrations.CreateModel(
                    name="MasterExternalAuditor",
                    fields=[
                        ("id", uuid_pk()),
                        ("name", models.CharField(max_length=200)),
                        ("master_external_audit_org_id", models.UUIDField(blank=True, null=True)),
                        ("review_status", models.CharField(default="PENDING_REVIEW", max_length=20)),
                        ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                        *created_fields(),
                        *updated_fields(),
                    ],
                    options={"db_table": "master_external_auditor"},
                ),
                migrations.CreateModel(
                    name="MasterExternalAuditorCategoryMap",
                    fields=[
                        ("id", uuid_pk()),
                        ("free_text_pattern", models.CharField(max_length=200)),
                        ("canonical_iacs_code", models.CharField(max_length=20)),
                        *created_fields(),
                    ],
                    options={"db_table": "master_external_auditor_category_map"},
                ),
            ],
        )
    ]

