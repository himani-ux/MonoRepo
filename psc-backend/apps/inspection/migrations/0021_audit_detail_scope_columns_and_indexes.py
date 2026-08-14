# Generated manually for VIMS Audit Phase 1 Step 1.3 on 2026-07-29.

from django.db import migrations, models


ADD_AUDIT_DETAIL_SCOPE_COLUMNS_SQL = r"""
IF OBJECT_ID('dbo.audit_detail', 'U') IS NULL
BEGIN
    THROW 51020, 'audit_detail is missing; apply inspection.0017 first.', 1;
END;

IF COL_LENGTH('dbo.audit_detail', 'vessel_id') IS NULL
BEGIN
    ALTER TABLE dbo.audit_detail ADD vessel_id char(32) NULL;
END;

IF COL_LENGTH('dbo.audit_detail', 'cycle_year') IS NULL
BEGIN
    ALTER TABLE dbo.audit_detail ADD cycle_year int NULL;
END;
"""


DROP_AUDIT_DETAIL_SCOPE_COLUMNS_SQL = r"""
IF COL_LENGTH('dbo.audit_detail', 'cycle_year') IS NOT NULL
BEGIN
    ALTER TABLE dbo.audit_detail DROP COLUMN cycle_year;
END;

IF COL_LENGTH('dbo.audit_detail', 'vessel_id') IS NOT NULL
BEGIN
    ALTER TABLE dbo.audit_detail DROP COLUMN vessel_id;
END;
"""


CREATE_AUDIT_INDEXES_SQL = r"""
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET NUMERIC_ROUNDABORT OFF;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_detail_classification' AND object_id = OBJECT_ID(N'dbo.audit_detail'))
BEGIN
    CREATE INDEX IX_audit_detail_classification ON dbo.audit_detail(audit_classification, auditee_type);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_detail_status' AND object_id = OBJECT_ID(N'dbo.audit_detail'))
BEGIN
    CREATE INDEX IX_audit_detail_status ON dbo.audit_detail(status);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_detail_external_org' AND object_id = OBJECT_ID(N'dbo.audit_detail'))
BEGIN
    CREATE INDEX IX_audit_detail_external_org ON dbo.audit_detail(external_audit_org_id);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_standards_detail' AND object_id = OBJECT_ID(N'dbo.audit_standards'))
BEGIN
    CREATE INDEX IX_audit_standards_detail ON dbo.audit_standards(audit_detail_id);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_team_member_detail' AND object_id = OBJECT_ID(N'dbo.audit_team_member'))
BEGIN
    CREATE INDEX IX_audit_team_member_detail ON dbo.audit_team_member(audit_detail_id);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_meeting_attendee_detail' AND object_id = OBJECT_ID(N'dbo.audit_meeting_attendee'))
BEGIN
    CREATE INDEX IX_audit_meeting_attendee_detail ON dbo.audit_meeting_attendee(audit_detail_id);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_area_summary_detail' AND object_id = OBJECT_ID(N'dbo.audit_area_summary'))
BEGIN
    CREATE INDEX IX_audit_area_summary_detail ON dbo.audit_area_summary(audit_detail_id);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_finding_detail' AND object_id = OBJECT_ID(N'dbo.audit_finding'))
BEGIN
    CREATE INDEX IX_audit_finding_detail ON dbo.audit_finding(audit_detail_id);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_finding_type_category' AND object_id = OBJECT_ID(N'dbo.audit_finding'))
BEGIN
    CREATE INDEX IX_audit_finding_type_category ON dbo.audit_finding(finding_type, nc_category);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_finding_clause_ref' AND object_id = OBJECT_ID(N'dbo.audit_finding'))
BEGIN
    CREATE INDEX IX_audit_finding_clause_ref ON dbo.audit_finding(rule_book_type, rule_clause_id);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_finding_clause_finding' AND object_id = OBJECT_ID(N'dbo.audit_finding_clause'))
BEGIN
    CREATE INDEX IX_audit_finding_clause_finding ON dbo.audit_finding_clause(audit_finding_id);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_attachment_detail' AND object_id = OBJECT_ID(N'dbo.audit_attachment'))
BEGIN
    CREATE INDEX IX_audit_attachment_detail ON dbo.audit_attachment(audit_detail_id);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_audit_attachment_finding' AND object_id = OBJECT_ID(N'dbo.audit_attachment'))
BEGIN
    CREATE INDEX IX_audit_attachment_finding ON dbo.audit_attachment(audit_finding_id);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_notification_delivery_notif' AND object_id = OBJECT_ID(N'dbo.notification_delivery_log'))
BEGIN
    CREATE INDEX IX_notification_delivery_notif ON dbo.notification_delivery_log(psc_notification_id, channel);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_notification_delivery_retry' AND object_id = OBJECT_ID(N'dbo.notification_delivery_log'))
BEGIN
    CREATE INDEX IX_notification_delivery_retry ON dbo.notification_delivery_log(status, last_attempted_at);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_cert_writeback_outbox_status' AND object_id = OBJECT_ID(N'dbo.cert_writeback_outbox'))
BEGIN
    CREATE INDEX IX_cert_writeback_outbox_status ON dbo.cert_writeback_outbox(status);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_master_audit_plan_window' AND object_id = OBJECT_ID(N'dbo.master_audit_plan'))
BEGIN
    CREATE INDEX IX_master_audit_plan_window ON dbo.master_audit_plan(planned_window_end, status);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_master_hod_assignment_resolve' AND object_id = OBJECT_ID(N'dbo.master_hod_assignment'))
BEGIN
    CREATE INDEX IX_master_hod_assignment_resolve ON dbo.master_hod_assignment(dept, effective_from, effective_to);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_master_qualified_auditor_user' AND object_id = OBJECT_ID(N'dbo.master_audit_qualified_auditor'))
BEGIN
    CREATE INDEX IX_master_qualified_auditor_user ON dbo.master_audit_qualified_auditor(user_id, is_active, expiry_date);
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UQ_audit_finding_clause_primary' AND object_id = OBJECT_ID(N'dbo.audit_finding_clause'))
BEGIN
    CREATE UNIQUE INDEX UQ_audit_finding_clause_primary
        ON dbo.audit_finding_clause(audit_finding_id)
        WHERE is_primary = 1;
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UQ_audit_detail_external_dedup' AND object_id = OBJECT_ID(N'dbo.audit_detail'))
BEGIN
    CREATE UNIQUE INDEX UQ_audit_detail_external_dedup
        ON dbo.audit_detail(vessel_id, external_audit_org_id, audit_subtype, audit_date_year_month)
        WHERE audit_classification = 'EXTERNAL' AND vessel_id IS NOT NULL;
END;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UQ_audit_detail_doc_flag_cycle_open' AND object_id = OBJECT_ID(N'dbo.audit_detail'))
BEGIN
    CREATE UNIQUE INDEX UQ_audit_detail_doc_flag_cycle_open
        ON dbo.audit_detail(flag_state_code, cycle_year)
        WHERE audit_classification = 'EXTERNAL'
          AND audit_subtype IN ('DOC_INITIAL', 'DOC_INTERIM', 'DOC_ANNUAL', 'DOC_RENEWAL')
          AND flag_state_code IS NOT NULL
          AND cycle_year IS NOT NULL
          AND status <> 'DPA_CLOSED'
          AND status <> 'CANCELLED'
          AND is_deleted = 0;
END;
"""


DROP_AUDIT_INDEXES_SQL = r"""
DROP INDEX IF EXISTS UQ_audit_detail_doc_flag_cycle_open ON dbo.audit_detail;
DROP INDEX IF EXISTS UQ_audit_detail_external_dedup ON dbo.audit_detail;
DROP INDEX IF EXISTS UQ_audit_finding_clause_primary ON dbo.audit_finding_clause;
DROP INDEX IF EXISTS IX_master_qualified_auditor_user ON dbo.master_audit_qualified_auditor;
DROP INDEX IF EXISTS IX_master_hod_assignment_resolve ON dbo.master_hod_assignment;
DROP INDEX IF EXISTS IX_master_audit_plan_window ON dbo.master_audit_plan;
DROP INDEX IF EXISTS IX_cert_writeback_outbox_status ON dbo.cert_writeback_outbox;
DROP INDEX IF EXISTS IX_notification_delivery_retry ON dbo.notification_delivery_log;
DROP INDEX IF EXISTS IX_notification_delivery_notif ON dbo.notification_delivery_log;
DROP INDEX IF EXISTS IX_audit_attachment_finding ON dbo.audit_attachment;
DROP INDEX IF EXISTS IX_audit_attachment_detail ON dbo.audit_attachment;
DROP INDEX IF EXISTS IX_audit_finding_clause_finding ON dbo.audit_finding_clause;
DROP INDEX IF EXISTS IX_audit_finding_clause_ref ON dbo.audit_finding;
DROP INDEX IF EXISTS IX_audit_finding_type_category ON dbo.audit_finding;
DROP INDEX IF EXISTS IX_audit_finding_detail ON dbo.audit_finding;
DROP INDEX IF EXISTS IX_audit_area_summary_detail ON dbo.audit_area_summary;
DROP INDEX IF EXISTS IX_audit_meeting_attendee_detail ON dbo.audit_meeting_attendee;
DROP INDEX IF EXISTS IX_audit_team_member_detail ON dbo.audit_team_member;
DROP INDEX IF EXISTS IX_audit_standards_detail ON dbo.audit_standards;
DROP INDEX IF EXISTS IX_audit_detail_external_org ON dbo.audit_detail;
DROP INDEX IF EXISTS IX_audit_detail_status ON dbo.audit_detail;
DROP INDEX IF EXISTS IX_audit_detail_classification ON dbo.audit_detail;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("inspection", "0020_audit_slack_channel_rename"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=ADD_AUDIT_DETAIL_SCOPE_COLUMNS_SQL,
                    reverse_sql=DROP_AUDIT_DETAIL_SCOPE_COLUMNS_SQL,
                ),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="auditdetail",
                    name="vessel_id",
                    field=models.CharField(blank=True, max_length=32, null=True),
                ),
                migrations.AddField(
                    model_name="auditdetail",
                    name="cycle_year",
                    field=models.IntegerField(blank=True, null=True),
                ),
            ],
        ),
        migrations.RunSQL(
            sql=CREATE_AUDIT_INDEXES_SQL,
            reverse_sql=DROP_AUDIT_INDEXES_SQL,
        ),
    ]

