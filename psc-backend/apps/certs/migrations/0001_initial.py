from __future__ import annotations

from django.db import migrations


TABLES = (
    "vims_certs_catalog_section",
    "vims_certs_catalog_row",
    "vims_certs_class_code_mapping",
    "vims_certs_tracked_item",
    "vims_certs_pdf_blob",
    "vims_certs_class_status_snapshot",
    "vims_certs_reconciliation_run",
    "vims_certs_reconciliation_flag",
    "vims_certs_audit_log",
    "vims_certs_alert_config",
    "vims_certs_approval_event",
    "vims_certs_notification_meta",
    "vims_certs_print_artifact",
    "vims_certs_external_auditor_access",
    "vims_certs_batch_ingest",
    "vims_certs_vessel_config",
    "vims_certs_modification_event",
    "vims_certs_settings",
    "vims_certs_cert_change_log",
)


CREATE_TABLE_SQL = [
    """
    IF OBJECT_ID(N'dbo.vims_certs_catalog_section', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_catalog_section (
        section_id INT IDENTITY(1,1) NOT NULL,
        section_code NVARCHAR(32) NOT NULL,
        display_name NVARCHAR(128) NOT NULL,
        sort_order SMALLINT NOT NULL,
        created_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_catalog_section_created_at DEFAULT SYSUTCDATETIME(),
        created_by NVARCHAR(64) NOT NULL,
        CONSTRAINT pk_vims_certs_catalog_section PRIMARY KEY CLUSTERED (section_id),
        CONSTRAINT uq_vims_certs_catalog_section_code UNIQUE (section_code)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_catalog_row', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_catalog_row (
        catalog_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_catalog_row_id DEFAULT NEWSEQUENTIALID(),
        canonical_code NVARCHAR(64) NOT NULL,
        section_id INT NOT NULL,
        display_name NVARCHAR(256) NOT NULL,
        short_name NVARCHAR(64) NULL,
        print_section_label NVARCHAR(128) NOT NULL,
        validity_type NVARCHAR(16) NOT NULL,
        cadence_months SMALLINT NULL,
        cadence_custom_days INT NULL,
        issuing_authority_type NVARCHAR(16) NOT NULL,
        is_class_tracked BIT NOT NULL CONSTRAINT df_vims_certs_catalog_row_is_class_tracked DEFAULT 0,
        submission_scope NVARCHAR(32) NOT NULL,
        parent_id UNIQUEIDENTIFIER NULL,
        relationship_type_default NVARCHAR(32) NULL,
        applicable_ship_types NVARCHAR(256) NOT NULL CONSTRAINT df_vims_certs_catalog_row_ship_types DEFAULT N'["all"]',
        mandatory_for_all_vessels BIT NOT NULL CONSTRAINT df_vims_certs_catalog_row_mandatory DEFAULT 1,
        applicability_mode NVARCHAR(24) NOT NULL CONSTRAINT df_vims_certs_catalog_row_applicability DEFAULT N'all_matching_type',
        specific_vessel_ids NVARCHAR(MAX) NULL,
        parent_supports_dynamic_children BIT NOT NULL CONSTRAINT df_vims_certs_catalog_row_dynamic DEFAULT 0,
        age_gate_max_years SMALLINT NULL,
        retain_all_versions BIT NOT NULL CONSTRAINT df_vims_certs_catalog_row_retain_all DEFAULT 0,
        linked_pms_component_id NVARCHAR(64) NULL,
        alert_lead_overrides NVARCHAR(MAX) NULL,
        regulatory_anchor NVARCHAR(256) NULL,
        legacy_remarks NVARCHAR(MAX) NULL,
        print_order INT NOT NULL CONSTRAINT df_vims_certs_catalog_row_print_order DEFAULT 0,
        is_active BIT NOT NULL CONSTRAINT df_vims_certs_catalog_row_is_active DEFAULT 1,
        created_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_catalog_row_created_at DEFAULT SYSUTCDATETIME(),
        created_by NVARCHAR(64) NOT NULL,
        updated_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_catalog_row_updated_at DEFAULT SYSUTCDATETIME(),
        updated_by NVARCHAR(64) NOT NULL,
        CONSTRAINT pk_vims_certs_catalog_row PRIMARY KEY CLUSTERED (catalog_id),
        CONSTRAINT uq_vims_certs_catalog_row_code UNIQUE (canonical_code),
        CONSTRAINT fk_vims_certs_catalog_row_section FOREIGN KEY (section_id)
            REFERENCES dbo.vims_certs_catalog_section(section_id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_class_code_mapping', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_class_code_mapping (
        mapping_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_class_code_mapping_id DEFAULT NEWSEQUENTIALID(),
        class_society NVARCHAR(8) NOT NULL,
        class_code_or_name NVARCHAR(128) NOT NULL,
        catalog_id UNIQUEIDENTIFIER NOT NULL,
        cert_or_survey_kind NVARCHAR(16) NOT NULL,
        notes NVARCHAR(MAX) NULL,
        version INT NOT NULL CONSTRAINT df_vims_certs_class_code_mapping_version DEFAULT 1,
        active BIT NOT NULL CONSTRAINT df_vims_certs_class_code_mapping_active DEFAULT 1,
        created_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_class_code_mapping_created_at DEFAULT SYSUTCDATETIME(),
        created_by NVARCHAR(64) NOT NULL,
        updated_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_class_code_mapping_updated_at DEFAULT SYSUTCDATETIME(),
        updated_by NVARCHAR(64) NOT NULL,
        CONSTRAINT pk_vims_certs_class_code_mapping PRIMARY KEY CLUSTERED (mapping_id),
        CONSTRAINT uq_vims_certs_class_code_mapping_version UNIQUE (class_society, class_code_or_name, version),
        CONSTRAINT fk_vims_certs_class_code_mapping_catalog FOREIGN KEY (catalog_id)
            REFERENCES dbo.vims_certs_catalog_row(catalog_id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_tracked_item', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_tracked_item (
        tracked_item_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_tracked_item_id DEFAULT NEWSEQUENTIALID(),
        vessel_id UNIQUEIDENTIFIER NOT NULL,
        catalog_id UNIQUEIDENTIFIER NOT NULL,
        type NVARCHAR(24) NOT NULL,
        validity_type NVARCHAR(16) NOT NULL,
        form_variant NVARCHAR(8) NULL,
        cadence_months SMALLINT NULL,
        cadence_custom_days INT NULL,
        parent_id UNIQUEIDENTIFIER NULL,
        relationship_type NVARCHAR(32) NULL,
        supersedes_id UNIQUEIDENTIFIER NULL,
        issue_date DATE NULL,
        expiry_date DATE NULL,
        anniversary_date DATE NULL,
        window_open DATE NULL,
        window_close DATE NULL,
        last_done_date DATE NULL,
        next_due_date DATE NULL,
        postponed_until DATE NULL,
        status NVARCHAR(32) NOT NULL CONSTRAINT df_vims_certs_tracked_item_status DEFAULT N'ok',
        certificate_number NVARCHAR(128) NULL,
        issuing_authority NVARCHAR(128) NOT NULL,
        place_of_issue NVARCHAR(128) NULL,
        extension_authority NVARCHAR(8) NULL,
        extension_letter_pdf_id UNIQUEIDENTIFIER NULL,
        extension_reason NVARCHAR(512) NULL,
        pdf_attachment_id UNIQUEIDENTIFIER NULL,
        pdf_missing BIT NOT NULL CONSTRAINT df_vims_certs_tracked_item_pdf_missing DEFAULT 0,
        source NVARCHAR(16) NOT NULL CONSTRAINT df_vims_certs_tracked_item_source DEFAULT N'manual',
        last_class_sync_id UNIQUEIDENTIFIER NULL,
        approval_state NVARCHAR(24) NOT NULL CONSTRAINT df_vims_certs_tracked_item_approval DEFAULT N'approved',
        submitted_by NVARCHAR(64) NULL,
        submitted_at DATETIME2(7) NULL,
        approved_by NVARCHAR(64) NULL,
        approved_at DATETIME2(7) NULL,
        rejection_reason NVARCHAR(MAX) NULL,
        rejection_count SMALLINT NOT NULL CONSTRAINT df_vims_certs_tracked_item_rejection_count DEFAULT 0,
        draft_expires_at DATETIME2(7) NULL,
        lifecycle_status NVARCHAR(24) NOT NULL CONSTRAINT df_vims_certs_tracked_item_lifecycle DEFAULT N'active',
        row_version ROWVERSION,
        version INT NOT NULL CONSTRAINT df_vims_certs_tracked_item_version DEFAULT 1,
        created_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_tracked_item_created_at DEFAULT SYSUTCDATETIME(),
        created_by NVARCHAR(64) NOT NULL,
        updated_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_tracked_item_updated_at DEFAULT SYSUTCDATETIME(),
        updated_by NVARCHAR(64) NOT NULL,
        CONSTRAINT pk_vims_certs_tracked_item PRIMARY KEY CLUSTERED (tracked_item_id),
        CONSTRAINT fk_vims_certs_tracked_item_vessel FOREIGN KEY (vessel_id)
            REFERENCES dbo.VesselData(id),
        CONSTRAINT fk_vims_certs_tracked_item_catalog FOREIGN KEY (catalog_id)
            REFERENCES dbo.vims_certs_catalog_row(catalog_id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_pdf_blob', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_pdf_blob (
        blob_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_pdf_blob_id DEFAULT NEWSEQUENTIALID(),
        tracked_item_id UNIQUEIDENTIFIER NULL,
        snapshot_id UNIQUEIDENTIFIER NULL,
        blob_storage_path NVARCHAR(512) NOT NULL,
        filename NVARCHAR(256) NOT NULL,
        content_sha256 CHAR(64) NOT NULL,
        content_size_bytes BIGINT NOT NULL,
        uploaded_by NVARCHAR(64) NOT NULL,
        uploaded_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_pdf_blob_uploaded_at DEFAULT SYSUTCDATETIME(),
        is_active BIT NOT NULL CONSTRAINT df_vims_certs_pdf_blob_is_active DEFAULT 1,
        superseded_at DATETIME2(7) NULL,
        retention_policy NVARCHAR(32) NOT NULL,
        scheduled_delete_at DATETIME2(7) NULL,
        delete_pending_since DATETIME2(7) NULL,
        dpa_retention_override_until DATETIME2(7) NULL,
        ocr_payload_json NVARCHAR(MAX) NULL,
        ocr_confidence_per_field NVARCHAR(MAX) NULL,
        ocr_processed_at DATETIME2(7) NULL,
        ocr_engine_version NVARCHAR(32) NULL,
        schema_version SMALLINT NOT NULL CONSTRAINT df_vims_certs_pdf_blob_schema_version DEFAULT 1,
        CONSTRAINT pk_vims_certs_pdf_blob PRIMARY KEY CLUSTERED (blob_id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_class_status_snapshot', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_class_status_snapshot (
        snapshot_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_class_status_snapshot_id DEFAULT NEWSEQUENTIALID(),
        vessel_id UNIQUEIDENTIFIER NOT NULL,
        class_society NVARCHAR(8) NOT NULL,
        pdf_blob_id UNIQUEIDENTIFIER NOT NULL,
        printed_on_date DATE NULL,
        uploaded_by NVARCHAR(64) NOT NULL,
        uploaded_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_class_status_snapshot_uploaded_at DEFAULT SYSUTCDATETIME(),
        parser_version NVARCHAR(32) NOT NULL,
        parse_status NVARCHAR(16) NOT NULL,
        parse_started_at DATETIME2(7) NULL,
        parse_completed_at DATETIME2(7) NULL,
        parser_timeout BIT NOT NULL CONSTRAINT df_vims_certs_class_status_snapshot_timeout DEFAULT 0,
        retry_count SMALLINT NOT NULL CONSTRAINT df_vims_certs_class_status_snapshot_retry DEFAULT 0,
        parsed_payload_json NVARCHAR(MAX) NULL,
        parsed_payload_schema_version SMALLINT NOT NULL CONSTRAINT df_vims_certs_class_status_snapshot_payload_schema DEFAULT 1,
        reconciliation_run_id UNIQUEIDENTIFIER NULL,
        upload_sha256 CHAR(64) NOT NULL,
        superseded_user_error BIT NOT NULL CONSTRAINT df_vims_certs_class_status_snapshot_superseded DEFAULT 0,
        CONSTRAINT pk_vims_certs_class_status_snapshot PRIMARY KEY CLUSTERED (snapshot_id),
        CONSTRAINT fk_vims_certs_class_status_snapshot_vessel FOREIGN KEY (vessel_id)
            REFERENCES dbo.VesselData(id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_reconciliation_run', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_reconciliation_run (
        run_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_reconciliation_run_id DEFAULT NEWSEQUENTIALID(),
        snapshot_id UNIQUEIDENTIFIER NOT NULL,
        ran_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_reconciliation_run_ran_at DEFAULT SYSUTCDATETIME(),
        matches_count INT NOT NULL CONSTRAINT df_vims_certs_reconciliation_run_matches DEFAULT 0,
        mismatches_count INT NOT NULL CONSTRAINT df_vims_certs_reconciliation_run_mismatches DEFAULT 0,
        missing_in_catalog_count INT NOT NULL CONSTRAINT df_vims_certs_reconciliation_run_missing_catalog DEFAULT 0,
        missing_in_class_count INT NOT NULL CONSTRAINT df_vims_certs_reconciliation_run_missing_class DEFAULT 0,
        conditional_stc_detected_count INT NOT NULL CONSTRAINT df_vims_certs_reconciliation_run_conditional DEFAULT 0,
        extended_postponed_detected_count INT NOT NULL CONSTRAINT df_vims_certs_reconciliation_run_extended DEFAULT 0,
        unmapped_low_confidence_count INT NOT NULL CONSTRAINT df_vims_certs_reconciliation_run_unmapped DEFAULT 0,
        flags_json NVARCHAR(MAX) NULL,
        notifications_sent_json NVARCHAR(MAX) NULL,
        mapping_version_used INT NOT NULL,
        anomaly_breaches_json NVARCHAR(MAX) NULL,
        CONSTRAINT pk_vims_certs_reconciliation_run PRIMARY KEY CLUSTERED (run_id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_reconciliation_flag', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_reconciliation_flag (
        flag_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_reconciliation_flag_id DEFAULT NEWSEQUENTIALID(),
        run_id UNIQUEIDENTIFIER NOT NULL,
        bucket NVARCHAR(32) NOT NULL,
        catalog_id UNIQUEIDENTIFIER NULL,
        tracked_item_id UNIQUEIDENTIFIER NULL,
        class_row_extract_json NVARCHAR(MAX) NULL,
        diff_json NVARCHAR(MAX) NULL,
        reviewed_by NVARCHAR(64) NULL,
        reviewed_at DATETIME2(7) NULL,
        resolution_action NVARCHAR(32) NULL,
        resolved_at DATETIME2(7) NULL,
        CONSTRAINT pk_vims_certs_reconciliation_flag PRIMARY KEY CLUSTERED (flag_id),
        CONSTRAINT fk_vims_certs_reconciliation_flag_run FOREIGN KEY (run_id)
            REFERENCES dbo.vims_certs_reconciliation_run(run_id),
        CONSTRAINT fk_vims_certs_reconciliation_flag_catalog FOREIGN KEY (catalog_id)
            REFERENCES dbo.vims_certs_catalog_row(catalog_id),
        CONSTRAINT fk_vims_certs_reconciliation_flag_tracked FOREIGN KEY (tracked_item_id)
            REFERENCES dbo.vims_certs_tracked_item(tracked_item_id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_audit_log', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_audit_log (
        audit_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_audit_log_id DEFAULT NEWSEQUENTIALID(),
        timestamp_utc DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_audit_log_timestamp DEFAULT SYSUTCDATETIME(),
        vessel_id UNIQUEIDENTIFIER NULL,
        actor_user_id NVARCHAR(64) NOT NULL,
        actor_role NVARCHAR(32) NOT NULL,
        action NVARCHAR(64) NOT NULL,
        entity_type NVARCHAR(32) NOT NULL,
        entity_id UNIQUEIDENTIFIER NULL,
        before_json NVARCHAR(MAX) NULL,
        after_json NVARCHAR(MAX) NULL,
        reason NVARCHAR(MAX) NULL,
        event_metadata NVARCHAR(MAX) NULL,
        retention_tier NVARCHAR(8) NOT NULL CONSTRAINT df_vims_certs_audit_log_retention_tier DEFAULT N'hot',
        archived_at DATETIME2(7) NULL,
        schema_version SMALLINT NOT NULL CONSTRAINT df_vims_certs_audit_log_schema_version DEFAULT 1,
        CONSTRAINT pk_vims_certs_audit_log PRIMARY KEY CLUSTERED (audit_id),
        CONSTRAINT fk_vims_certs_audit_log_vessel FOREIGN KEY (vessel_id)
            REFERENCES dbo.VesselData(id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_alert_config', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_alert_config (
        config_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_alert_config_id DEFAULT NEWSEQUENTIALID(),
        trigger_event NVARCHAR(64) NOT NULL,
        default_lead_days INT NOT NULL,
        dpa_override_lead_days INT NULL,
        recipients_default_json NVARCHAR(MAX) NOT NULL,
        dpa_override_recipients_json NVARCHAR(MAX) NULL,
        escalation_cadence_json NVARCHAR(MAX) NOT NULL,
        ocr_threshold_office DECIMAL(4,3) NOT NULL CONSTRAINT df_vims_certs_alert_config_ocr_office DEFAULT 0.800,
        ocr_threshold_vessel DECIMAL(4,3) NOT NULL CONSTRAINT df_vims_certs_alert_config_ocr_vessel DEFAULT 0.850,
        ocr_threshold_manual_floor DECIMAL(4,3) NOT NULL CONSTRAINT df_vims_certs_alert_config_ocr_floor DEFAULT 0.600,
        class_snapshot_cadence_months SMALLINT NOT NULL CONSTRAINT df_vims_certs_alert_config_snapshot_cadence DEFAULT 3,
        class_snapshot_lead_months SMALLINT NOT NULL CONSTRAINT df_vims_certs_alert_config_snapshot_lead DEFAULT 1,
        event_snapshot_grace_days SMALLINT NOT NULL CONSTRAINT df_vims_certs_alert_config_snapshot_grace DEFAULT 14,
        draft_expire_days SMALLINT NOT NULL CONSTRAINT df_vims_certs_alert_config_draft_expire DEFAULT 7,
        created_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_alert_config_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_alert_config_updated_at DEFAULT SYSUTCDATETIME(),
        updated_by NVARCHAR(64) NOT NULL,
        CONSTRAINT pk_vims_certs_alert_config PRIMARY KEY CLUSTERED (config_id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_approval_event', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_approval_event (
        event_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_approval_event_id DEFAULT NEWSEQUENTIALID(),
        tracked_item_id UNIQUEIDENTIFIER NOT NULL,
        from_state NVARCHAR(24) NOT NULL,
        to_state NVARCHAR(24) NOT NULL,
        actor_user_id NVARCHAR(64) NOT NULL,
        actor_role NVARCHAR(32) NOT NULL,
        reason NVARCHAR(MAX) NULL,
        timestamp_utc DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_approval_event_timestamp DEFAULT SYSUTCDATETIME(),
        CONSTRAINT pk_vims_certs_approval_event PRIMARY KEY CLUSTERED (event_id),
        CONSTRAINT fk_vims_certs_approval_event_tracked FOREIGN KEY (tracked_item_id)
            REFERENCES dbo.vims_certs_tracked_item(tracked_item_id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_notification_meta', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_notification_meta (
        notification_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_notification_meta_id DEFAULT NEWSEQUENTIALID(),
        master_notification_id BIGINT NOT NULL,
        trigger_event NVARCHAR(64) NOT NULL,
        cert_row_id UNIQUEIDENTIFIER NULL,
        vessel_id UNIQUEIDENTIFIER NULL,
        recipients_json NVARCHAR(MAX) NOT NULL,
        channels_json NVARCHAR(MAX) NOT NULL,
        sent_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_notification_meta_sent_at DEFAULT SYSUTCDATETIME(),
        delivery_status_json NVARCHAR(MAX) NULL,
        ack_user_id NVARCHAR(64) NULL,
        ack_at DATETIME2(7) NULL,
        ack_channel NVARCHAR(16) NULL,
        escalation_level SMALLINT NOT NULL CONSTRAINT df_vims_certs_notification_meta_escalation DEFAULT 0,
        body_content NVARCHAR(MAX) NULL,
        body_purged_at DATETIME2(7) NULL,
        idempotency_key NVARCHAR(128) NOT NULL,
        CONSTRAINT pk_vims_certs_notification_meta PRIMARY KEY CLUSTERED (notification_id),
        CONSTRAINT uq_vims_certs_notification_meta_idempotency UNIQUE (idempotency_key),
        CONSTRAINT fk_vims_certs_notification_meta_master FOREIGN KEY (master_notification_id)
            REFERENCES dbo.master_notification(id),
        CONSTRAINT fk_vims_certs_notification_meta_cert FOREIGN KEY (cert_row_id)
            REFERENCES dbo.vims_certs_tracked_item(tracked_item_id),
        CONSTRAINT fk_vims_certs_notification_meta_vessel FOREIGN KEY (vessel_id)
            REFERENCES dbo.VesselData(id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_print_artifact', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_print_artifact (
        print_id NVARCHAR(64) NOT NULL,
        scope NVARCHAR(32) NOT NULL,
        vessels_json NVARCHAR(MAX) NOT NULL,
        sections_json NVARCHAR(MAX) NULL,
        filters_json NVARCHAR(MAX) NULL,
        custom_cert_ids_json NVARCHAR(MAX) NULL,
        user_id NVARCHAR(64) NOT NULL,
        user_role NVARCHAR(32) NOT NULL,
        timestamp_utc DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_print_artifact_timestamp DEFAULT SYSUTCDATETIME(),
        system_state_hash CHAR(8) NOT NULL,
        watermark_applied NVARCHAR(32) NOT NULL,
        watermark_recipient NVARCHAR(128) NULL,
        pdf_blob_id UNIQUEIDENTIFIER NULL,
        excel_blob_id UNIQUEIDENTIFIER NULL,
        bundle_zip_blob_id UNIQUEIDENTIFIER NULL,
        recipient_email NVARCHAR(256) NULL,
        page_count INT NULL,
        generation_status NVARCHAR(16) NOT NULL CONSTRAINT df_vims_certs_print_artifact_status DEFAULT N'success',
        failure_message NVARCHAR(MAX) NULL,
        CONSTRAINT pk_vims_certs_print_artifact PRIMARY KEY CLUSTERED (print_id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_external_auditor_access', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_external_auditor_access (
        grant_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_external_auditor_access_id DEFAULT NEWSEQUENTIALID(),
        auditor_name NVARCHAR(128) NOT NULL,
        auditor_email NVARCHAR(256) NOT NULL,
        scope_json NVARCHAR(MAX) NOT NULL,
        expiry_at DATETIME2(7) NOT NULL,
        granted_by NVARCHAR(64) NOT NULL,
        granted_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_external_auditor_access_granted_at DEFAULT SYSUTCDATETIME(),
        signup_token_hash CHAR(64) NOT NULL,
        signup_token_used_at DATETIME2(7) NULL,
        token_secret_hash CHAR(64) NULL,
        last_accessed_at DATETIME2(7) NULL,
        revoked_via_expiry_edit BIT NOT NULL CONSTRAINT df_vims_certs_external_auditor_access_revoked DEFAULT 0,
        CONSTRAINT pk_vims_certs_external_auditor_access PRIMARY KEY CLUSTERED (grant_id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_batch_ingest', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_batch_ingest (
        batch_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_batch_ingest_id DEFAULT NEWSEQUENTIALID(),
        vessel_id UNIQUEIDENTIFIER NOT NULL,
        onboarding_session_id UNIQUEIDENTIFIER NULL,
        pdf_blob_ids_json NVARCHAR(MAX) NOT NULL,
        pdf_count SMALLINT NOT NULL,
        status NVARCHAR(24) NOT NULL,
        created_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_batch_ingest_created_at DEFAULT SYSUTCDATETIME(),
        created_by NVARCHAR(64) NOT NULL,
        ocr_completed_at DATETIME2(7) NULL,
        review_started_at DATETIME2(7) NULL,
        committed_at DATETIME2(7) NULL,
        committed_by NVARCHAR(64) NULL,
        cancelled_at DATETIME2(7) NULL,
        cancelled_by NVARCHAR(64) NULL,
        validation_blocks_json NVARCHAR(MAX) NULL,
        validation_warns_json NVARCHAR(MAX) NULL,
        report_csv_blob_id UNIQUEIDENTIFIER NULL,
        CONSTRAINT pk_vims_certs_batch_ingest PRIMARY KEY CLUSTERED (batch_id),
        CONSTRAINT fk_vims_certs_batch_ingest_vessel FOREIGN KEY (vessel_id)
            REFERENCES dbo.VesselData(id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_vessel_config', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_vessel_config (
        vessel_id UNIQUEIDENTIFIER NOT NULL,
        anniversary_date DATE NULL,
        ship_type NVARCHAR(32) NOT NULL,
        marine_supt_user_id NVARCHAR(64) NULL,
        technical_manager_user_id NVARCHAR(64) NULL,
        slack_channel_vessel NVARCHAR(64) NULL,
        slack_channel_office_default NVARCHAR(64) NULL,
        lifecycle_status NVARCHAR(24) NOT NULL CONSTRAINT df_vims_certs_vessel_config_lifecycle DEFAULT N'active',
        pending_disposal_started_at DATETIME2(7) NULL,
        sale_handover_bundle_blob_id UNIQUEIDENTIFIER NULL,
        flag_change_pending BIT NOT NULL CONSTRAINT df_vims_certs_vessel_config_flag_pending DEFAULT 0,
        flag_change_event_json NVARCHAR(MAX) NULL,
        class_change_pending BIT NOT NULL CONSTRAINT df_vims_certs_vessel_config_class_pending DEFAULT 0,
        mandatory_coverage_override_reason NVARCHAR(MAX) NULL,
        mandatory_coverage_override_at DATETIME2(7) NULL,
        mandatory_coverage_override_by NVARCHAR(64) NULL,
        created_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_vessel_config_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_vessel_config_updated_at DEFAULT SYSUTCDATETIME(),
        updated_by NVARCHAR(64) NOT NULL,
        CONSTRAINT pk_vims_certs_vessel_config PRIMARY KEY CLUSTERED (vessel_id),
        CONSTRAINT fk_vims_certs_vessel_config_vessel FOREIGN KEY (vessel_id)
            REFERENCES dbo.VesselData(id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_modification_event', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_modification_event (
        modification_event_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_modification_event_id DEFAULT NEWSEQUENTIALID(),
        group_started_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_modification_event_started DEFAULT SYSUTCDATETIME(),
        group_window_ends_at DATETIME2(7) NOT NULL,
        description NVARCHAR(MAX) NOT NULL,
        affected_tracked_item_ids_json NVARCHAR(MAX) NOT NULL,
        created_by NVARCHAR(64) NOT NULL,
        CONSTRAINT pk_vims_certs_modification_event PRIMARY KEY CLUSTERED (modification_event_id)
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_settings', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_settings (
        settings_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_settings_id DEFAULT NEWSEQUENTIALID(),
        singleton_key NVARCHAR(32) NOT NULL CONSTRAINT df_vims_certs_settings_singleton_key DEFAULT N'certs',
        last_heartbeat_at DATETIME2(7) NULL,
        created_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_settings_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_settings_updated_at DEFAULT SYSUTCDATETIME(),
        updated_by NVARCHAR(64) NULL,
        CONSTRAINT pk_vims_certs_settings PRIMARY KEY CLUSTERED (settings_id),
        CONSTRAINT uq_vims_certs_settings_singleton_key UNIQUE (singleton_key),
        CONSTRAINT ck_vims_certs_settings_singleton_key CHECK (singleton_key = N'certs')
    )
    """,
    """
    IF OBJECT_ID(N'dbo.vims_certs_cert_change_log', N'U') IS NULL
    CREATE TABLE dbo.vims_certs_cert_change_log (
        change_id UNIQUEIDENTIFIER NOT NULL CONSTRAINT df_vims_certs_cert_change_log_id DEFAULT NEWSEQUENTIALID(),
        tracked_item_id UNIQUEIDENTIFIER NOT NULL,
        field_name NVARCHAR(64) NOT NULL,
        old_value NVARCHAR(MAX) NULL,
        new_value NVARCHAR(MAX) NULL,
        version_after INT NOT NULL,
        source_module NVARCHAR(16) NOT NULL,
        source_ref NVARCHAR(64) NULL,
        changed_by NVARCHAR(64) NULL,
        changed_at DATETIME2(7) NOT NULL CONSTRAINT df_vims_certs_cert_change_log_changed_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT pk_vims_certs_cert_change_log PRIMARY KEY CLUSTERED (change_id),
        CONSTRAINT fk_vims_certs_cert_change_log_tracked FOREIGN KEY (tracked_item_id)
            REFERENCES dbo.vims_certs_tracked_item(tracked_item_id)
    )
    """,
]


ALTER_SQL = [
    (
        "vims_certs_catalog_row",
        "fk_vims_certs_catalog_row_parent",
        """
        ALTER TABLE dbo.vims_certs_catalog_row
        ADD CONSTRAINT fk_vims_certs_catalog_row_parent
        FOREIGN KEY (parent_id) REFERENCES dbo.vims_certs_catalog_row(catalog_id)
        """,
    ),
    (
        "vims_certs_tracked_item",
        "fk_vims_certs_tracked_item_parent",
        """
        ALTER TABLE dbo.vims_certs_tracked_item
        ADD CONSTRAINT fk_vims_certs_tracked_item_parent
        FOREIGN KEY (parent_id) REFERENCES dbo.vims_certs_tracked_item(tracked_item_id)
        """,
    ),
    (
        "vims_certs_tracked_item",
        "fk_vims_certs_tracked_item_supersedes",
        """
        ALTER TABLE dbo.vims_certs_tracked_item
        ADD CONSTRAINT fk_vims_certs_tracked_item_supersedes
        FOREIGN KEY (supersedes_id) REFERENCES dbo.vims_certs_tracked_item(tracked_item_id)
        """,
    ),
    (
        "vims_certs_tracked_item",
        "fk_vims_certs_tracked_item_extension_blob",
        """
        ALTER TABLE dbo.vims_certs_tracked_item
        ADD CONSTRAINT fk_vims_certs_tracked_item_extension_blob
        FOREIGN KEY (extension_letter_pdf_id) REFERENCES dbo.vims_certs_pdf_blob(blob_id)
        """,
    ),
    (
        "vims_certs_tracked_item",
        "fk_vims_certs_tracked_item_pdf_blob",
        """
        ALTER TABLE dbo.vims_certs_tracked_item
        ADD CONSTRAINT fk_vims_certs_tracked_item_pdf_blob
        FOREIGN KEY (pdf_attachment_id) REFERENCES dbo.vims_certs_pdf_blob(blob_id)
        """,
    ),
    (
        "vims_certs_tracked_item",
        "fk_vims_certs_tracked_item_class_snapshot",
        """
        ALTER TABLE dbo.vims_certs_tracked_item
        ADD CONSTRAINT fk_vims_certs_tracked_item_class_snapshot
        FOREIGN KEY (last_class_sync_id) REFERENCES dbo.vims_certs_class_status_snapshot(snapshot_id)
        """,
    ),
    (
        "vims_certs_pdf_blob",
        "fk_vims_certs_pdf_blob_tracked",
        """
        ALTER TABLE dbo.vims_certs_pdf_blob
        ADD CONSTRAINT fk_vims_certs_pdf_blob_tracked
        FOREIGN KEY (tracked_item_id) REFERENCES dbo.vims_certs_tracked_item(tracked_item_id)
        """,
    ),
    (
        "vims_certs_pdf_blob",
        "fk_vims_certs_pdf_blob_snapshot",
        """
        ALTER TABLE dbo.vims_certs_pdf_blob
        ADD CONSTRAINT fk_vims_certs_pdf_blob_snapshot
        FOREIGN KEY (snapshot_id) REFERENCES dbo.vims_certs_class_status_snapshot(snapshot_id)
        """,
    ),
    (
        "vims_certs_class_status_snapshot",
        "fk_vims_certs_class_status_snapshot_pdf_blob",
        """
        ALTER TABLE dbo.vims_certs_class_status_snapshot
        ADD CONSTRAINT fk_vims_certs_class_status_snapshot_pdf_blob
        FOREIGN KEY (pdf_blob_id) REFERENCES dbo.vims_certs_pdf_blob(blob_id)
        """,
    ),
    (
        "vims_certs_class_status_snapshot",
        "fk_vims_certs_class_status_snapshot_run",
        """
        ALTER TABLE dbo.vims_certs_class_status_snapshot
        ADD CONSTRAINT fk_vims_certs_class_status_snapshot_run
        FOREIGN KEY (reconciliation_run_id) REFERENCES dbo.vims_certs_reconciliation_run(run_id)
        """,
    ),
    (
        "vims_certs_reconciliation_run",
        "fk_vims_certs_reconciliation_run_snapshot",
        """
        ALTER TABLE dbo.vims_certs_reconciliation_run
        ADD CONSTRAINT fk_vims_certs_reconciliation_run_snapshot
        FOREIGN KEY (snapshot_id) REFERENCES dbo.vims_certs_class_status_snapshot(snapshot_id)
        """,
    ),
    (
        "vims_certs_print_artifact",
        "fk_vims_certs_print_artifact_pdf_blob",
        """
        ALTER TABLE dbo.vims_certs_print_artifact
        ADD CONSTRAINT fk_vims_certs_print_artifact_pdf_blob
        FOREIGN KEY (pdf_blob_id) REFERENCES dbo.vims_certs_pdf_blob(blob_id)
        """,
    ),
    (
        "vims_certs_print_artifact",
        "fk_vims_certs_print_artifact_excel_blob",
        """
        ALTER TABLE dbo.vims_certs_print_artifact
        ADD CONSTRAINT fk_vims_certs_print_artifact_excel_blob
        FOREIGN KEY (excel_blob_id) REFERENCES dbo.vims_certs_pdf_blob(blob_id)
        """,
    ),
    (
        "vims_certs_print_artifact",
        "fk_vims_certs_print_artifact_bundle_blob",
        """
        ALTER TABLE dbo.vims_certs_print_artifact
        ADD CONSTRAINT fk_vims_certs_print_artifact_bundle_blob
        FOREIGN KEY (bundle_zip_blob_id) REFERENCES dbo.vims_certs_pdf_blob(blob_id)
        """,
    ),
    (
        "vims_certs_batch_ingest",
        "fk_vims_certs_batch_ingest_report_blob",
        """
        ALTER TABLE dbo.vims_certs_batch_ingest
        ADD CONSTRAINT fk_vims_certs_batch_ingest_report_blob
        FOREIGN KEY (report_csv_blob_id) REFERENCES dbo.vims_certs_pdf_blob(blob_id)
        """,
    ),
    (
        "vims_certs_vessel_config",
        "fk_vims_certs_vessel_config_sale_blob",
        """
        ALTER TABLE dbo.vims_certs_vessel_config
        ADD CONSTRAINT fk_vims_certs_vessel_config_sale_blob
        FOREIGN KEY (sale_handover_bundle_blob_id) REFERENCES dbo.vims_certs_pdf_blob(blob_id)
        """,
    ),
]


INDEX_SQL = [
    "CREATE INDEX ix_vims_certs_catalog_row_section_active_order ON dbo.vims_certs_catalog_row(section_id, is_active, print_order)",
    "CREATE INDEX ix_vims_certs_tracked_item_vessel_status_expiry ON dbo.vims_certs_tracked_item(vessel_id, status, expiry_date)",
    "CREATE INDEX ix_vims_certs_tracked_item_catalog ON dbo.vims_certs_tracked_item(catalog_id)",
    "CREATE INDEX ix_vims_certs_tracked_item_approval_draft ON dbo.vims_certs_tracked_item(approval_state, draft_expires_at)",
    "CREATE INDEX ix_vims_certs_tracked_item_vessel_lifecycle ON dbo.vims_certs_tracked_item(vessel_id, lifecycle_status)",
    "CREATE UNIQUE INDEX uq_vims_certs_pdf_blob_tracked_sha ON dbo.vims_certs_pdf_blob(tracked_item_id, content_sha256) WHERE tracked_item_id IS NOT NULL",
    "CREATE INDEX ix_vims_certs_pdf_blob_retention ON dbo.vims_certs_pdf_blob(scheduled_delete_at, is_active)",
    "CREATE INDEX ix_vims_certs_class_status_snapshot_vessel_printed ON dbo.vims_certs_class_status_snapshot(vessel_id, printed_on_date DESC)",
    "CREATE INDEX ix_vims_certs_class_status_snapshot_parse_status ON dbo.vims_certs_class_status_snapshot(parse_status)",
    "CREATE INDEX ix_vims_certs_reconciliation_flag_review ON dbo.vims_certs_reconciliation_flag(run_id, bucket, resolved_at)",
    "CREATE INDEX ix_vims_certs_audit_log_timestamp_vessel ON dbo.vims_certs_audit_log(timestamp_utc DESC, vessel_id)",
    "CREATE INDEX ix_vims_certs_audit_log_actor_timestamp ON dbo.vims_certs_audit_log(actor_user_id, timestamp_utc DESC)",
    "CREATE INDEX ix_vims_certs_audit_log_retention ON dbo.vims_certs_audit_log(retention_tier, timestamp_utc)",
    "CREATE INDEX ix_vims_certs_notification_meta_cert_escalation ON dbo.vims_certs_notification_meta(cert_row_id, escalation_level)",
    "CREATE INDEX ix_vims_certs_print_artifact_timestamp ON dbo.vims_certs_print_artifact(timestamp_utc DESC)",
    "CREATE INDEX ix_vims_certs_print_artifact_user_timestamp ON dbo.vims_certs_print_artifact(user_id, timestamp_utc DESC)",
    "CREATE INDEX ix_vims_certs_external_auditor_access_expiry ON dbo.vims_certs_external_auditor_access(expiry_at)",
    "CREATE INDEX ix_vims_certs_batch_ingest_vessel_status ON dbo.vims_certs_batch_ingest(vessel_id, status)",
]


def _constraint_exists(cursor, table_name: str, constraint_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sys.objects
        WHERE parent_object_id = OBJECT_ID(%s)
          AND name = %s
        """,
        [f"dbo.{table_name}", constraint_name],
    )
    return int(cursor.fetchone()[0] or 0) > 0


def _index_exists(cursor, table_name: str, index_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sys.indexes
        WHERE object_id = OBJECT_ID(%s)
          AND name = %s
        """,
        [f"dbo.{table_name}", index_name],
    )
    return int(cursor.fetchone()[0] or 0) > 0


def _table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sys.tables
        WHERE object_id = OBJECT_ID(%s)
        """,
        [f"dbo.{table_name}"],
    )
    return int(cursor.fetchone()[0] or 0) > 0


def _grant(cursor, permission_sql: str, table_name: str, role_name: str) -> None:
    if not _table_exists(cursor, table_name):
        return
    cursor.execute(
        f"""
        IF DATABASE_PRINCIPAL_ID(N'{role_name}') IS NOT NULL
            {permission_sql} ON dbo.{table_name} TO {role_name}
        """
    )


def _apply_grants(cursor) -> None:
    append_only_tables = {
        "vims_certs_audit_log",
        "vims_certs_approval_event",
        "vims_certs_cert_change_log",
    }

    for table_name in TABLES:
        _grant(cursor, "GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES", table_name, "vims_admin")
        if table_name in append_only_tables:
            _grant(cursor, "GRANT SELECT, INSERT", table_name, "vims_app")
        else:
            _grant(cursor, "GRANT SELECT, INSERT, UPDATE, DELETE", table_name, "vims_app")

    _grant(cursor, "GRANT UPDATE (retention_tier, archived_at)", "vims_certs_audit_log", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_audit_log", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_cert_change_log", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_approval_event", "vims_jobs")
    _grant(cursor, "GRANT UPDATE (body_content, body_purged_at)", "vims_certs_notification_meta", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_notification_meta", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_print_artifact", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_external_auditor_access", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_batch_ingest", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_reconciliation_flag", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_reconciliation_run", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_modification_event", "vims_jobs")
    _grant(cursor, "GRANT UPDATE (is_active, superseded_at, scheduled_delete_at, delete_pending_since)", "vims_certs_pdf_blob", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_pdf_blob", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_tracked_item", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_vessel_config", "vims_jobs")
    _grant(cursor, "GRANT DELETE", "vims_certs_class_code_mapping", "vims_jobs")


def create_certs_schema(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return

    with schema_editor.connection.cursor() as cursor:
        for statement in CREATE_TABLE_SQL:
            cursor.execute(statement)

        for table_name, constraint_name, statement in ALTER_SQL:
            if not _constraint_exists(cursor, table_name, constraint_name):
                cursor.execute(statement)

        for statement in INDEX_SQL:
            table_name = statement.split(" ON dbo.", 1)[1].split("(", 1)[0]
            index_name = statement.split()[2]
            if not _index_exists(cursor, table_name, index_name):
                cursor.execute(statement)

        _apply_grants(cursor)


def drop_certs_schema(apps, schema_editor) -> None:
    if schema_editor.connection.vendor != "microsoft":
        return

    drop_order = (
        "vims_certs_cert_change_log",
        "vims_certs_settings",
        "vims_certs_modification_event",
        "vims_certs_vessel_config",
        "vims_certs_batch_ingest",
        "vims_certs_external_auditor_access",
        "vims_certs_print_artifact",
        "vims_certs_notification_meta",
        "vims_certs_approval_event",
        "vims_certs_alert_config",
        "vims_certs_audit_log",
        "vims_certs_reconciliation_flag",
        "vims_certs_reconciliation_run",
        "vims_certs_class_status_snapshot",
        "vims_certs_pdf_blob",
        "vims_certs_tracked_item",
        "vims_certs_class_code_mapping",
        "vims_certs_catalog_row",
        "vims_certs_catalog_section",
    )

    with schema_editor.connection.cursor() as cursor:
        for table_name in TABLES:
            cursor.execute(
                """
                DECLARE @sql NVARCHAR(MAX) = N'';
                SELECT @sql = @sql + N'ALTER TABLE '
                    + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id)) + N'.'
                    + QUOTENAME(OBJECT_NAME(parent_object_id))
                    + N' DROP CONSTRAINT ' + QUOTENAME(name) + N';'
                FROM sys.foreign_keys
                WHERE parent_object_id = OBJECT_ID(%s);
                IF @sql <> N'' EXEC sp_executesql @sql;
                """,
                [f"dbo.{table_name}"],
            )

        for table_name in drop_order:
            cursor.execute(f"IF OBJECT_ID(N'dbo.{table_name}', N'U') IS NOT NULL DROP TABLE dbo.{table_name}")


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.RunPython(create_certs_schema, drop_certs_schema),
    ]
