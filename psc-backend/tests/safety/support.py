from __future__ import annotations

import django

from django.apps import apps
from django.db import connection


def bootstrap_django(*, root_urlconf: str | None = None) -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="safety-phase-1-1-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "rest_framework",
                "apps.safety",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            ROOT_URLCONF=root_urlconf or "config.urls",
            ALLOWED_HOSTS=["testserver", "localhost"],
            USE_TZ=True,
        )
    elif root_urlconf is not None:
        settings.ROOT_URLCONF = root_urlconf

    if not apps.ready:
        django.setup()


def recreate_incident_table() -> None:
    from apps.safety.models import (
        ChainOfCustody,
        CorrectiveAction,
        EvidenceDeadlineTask,
        EvidenceItem,
        ExternalPartyInjury,
        Incident,
        IncidentBiasGuardResponse,
        IncidentBlameOverride,
        IncidentCauseTag,
        IncidentEvidence,
        IncidentFact,
        IncidentPhase5Assessment,
        IncidentPhaseLog,
        IncidentSafeguardFailure,
        Recommendation,
        RecommendationVerification,
        SafetyFieldHistory,
        WitnessInterview,
    )

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_evidence_deadline_task")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_witness_interview")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_chain_of_custody")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_blame_override")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_bias_guard_response")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_safeguard_failure")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_cause_tag")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_incident_phase5_assessment")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_evidence_item")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_incident_evidence")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_fact")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_corrective_action")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_recommendation_verification")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_recommendation")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_field_history")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_incident_phase_log")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_external_party_injury")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_incident")
        cursor.execute("PRAGMA foreign_keys = ON")

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Incident)
        schema_editor.create_model(IncidentPhaseLog)
        schema_editor.create_model(SafetyFieldHistory)
        schema_editor.create_model(ExternalPartyInjury)
        schema_editor.create_model(IncidentEvidence)
        schema_editor.create_model(EvidenceItem)
        schema_editor.create_model(ChainOfCustody)
        schema_editor.create_model(WitnessInterview)
        schema_editor.create_model(EvidenceDeadlineTask)
        schema_editor.create_model(IncidentFact)
        schema_editor.create_model(IncidentPhase5Assessment)
        schema_editor.create_model(IncidentCauseTag)
        schema_editor.create_model(IncidentSafeguardFailure)
        schema_editor.create_model(IncidentBiasGuardResponse)
        schema_editor.create_model(IncidentBlameOverride)
        schema_editor.create_model(Recommendation)
        schema_editor.create_model(RecommendationVerification)
        schema_editor.create_model(CorrectiveAction)


def recreate_master_notification_table() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS master_notification")
        cursor.execute(
            """
            CREATE TABLE master_notification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module_code VARCHAR(32) NOT NULL,
                record_id BIGINT NOT NULL,
                recipient_ref VARCHAR(64) NOT NULL,
                notification_kind VARCHAR(64) NOT NULL,
                title VARCHAR(256) NOT NULL,
                message TEXT NOT NULL,
                delivery_channel VARCHAR(32) NOT NULL,
                payload_json TEXT NULL,
                created_at DATETIME NOT NULL
            )
            """
        )


def recreate_scm_tables() -> None:
    from apps.safety.models import SCMAgendaItem, SCMAttendance, SCMLegacyField, SCMMeeting, SCMSignature, SafetyFieldHistory

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_signature")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_legacy_field")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_agenda")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_attendance")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_meeting")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_field_history")
        cursor.execute("PRAGMA foreign_keys = ON")

    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(SCMMeeting)
        schema_editor.create_model(SCMAttendance)
        schema_editor.create_model(SCMSignature)
        schema_editor.create_model(SCMAgendaItem)
        schema_editor.create_model(SCMLegacyField)
        schema_editor.create_model(SafetyFieldHistory)


def recreate_soi_tables() -> None:
    from apps.safety.models import (
        SafetyFieldHistory,
        SOIApplicabilityLog,
        SOIInspection,
        SOIInspectionArea,
        SOIOfficerSetting,
        SOITrainee,
        SOIVesselAreaMap,
    )

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_soi_applicability_log")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_soi_officer_setting")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_soi_trainee")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_soi_inspection_area")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_soi_vessel_area_map")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_soi_finding")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_soi_inspection")
        cursor.execute("DROP TABLE IF EXISTS vims_safety_field_history")
        cursor.execute("DROP TABLE IF EXISTS master_soi_checklist_version")
        cursor.execute("DROP TABLE IF EXISTS master_soi_area_item")
        cursor.execute("DROP TABLE IF EXISTS master_soi_area")
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute(
            """
            CREATE TABLE master_soi_checklist_version (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                version_label VARCHAR(16) NOT NULL UNIQUE,
                effective_from DATE NOT NULL,
                effective_to DATE NULL,
                source_description VARCHAR(256) NOT NULL,
                active BOOLEAN NOT NULL DEFAULT 1,
                created_by VARCHAR(128) NOT NULL,
                created_date DATETIME NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE master_soi_area (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                area_id INTEGER NOT NULL UNIQUE,
                area_name VARCHAR(128) NOT NULL,
                section_12_flag BOOLEAN NOT NULL DEFAULT 0,
                display_order INTEGER NOT NULL,
                active BOOLEAN NOT NULL DEFAULT 1,
                seeded_version VARCHAR(128) NOT NULL DEFAULT 'v1.0'
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE master_soi_area_item (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                area_id INTEGER NOT NULL,
                area_name VARCHAR(128) NOT NULL,
                subsection_id INTEGER NOT NULL,
                subsection_name VARCHAR(128) NOT NULL,
                item_number VARCHAR(16) NOT NULL,
                description TEXT NOT NULL,
                tier VARCHAR(16) NOT NULL,
                active BOOLEAN NOT NULL DEFAULT 1,
                seeded_version VARCHAR(16) NOT NULL DEFAULT 'v1.0',
                schema_version INTEGER NOT NULL DEFAULT 1,
                updated_by VARCHAR(128) NULL,
                updated_date DATETIME NULL
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO master_soi_checklist_version (
                id,
                legacy_int_id,
                version_label,
                effective_from,
                effective_to,
                source_description,
                active,
                created_by,
                created_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                "00000000000000000000000000000001",
                1,
                "v1.0",
                "2026-04-17",
                None,
                "SQE S 608 baseline - SSQE Rev 02 + Section 12",
                True,
                "seed_master_safety",
                "2026-04-17 00:00:00",
            ],
        )
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(SOIInspection)
        schema_editor.create_model(SOIOfficerSetting)
        schema_editor.create_model(SOIInspectionArea)
        schema_editor.create_model(SOITrainee)
        schema_editor.create_model(SOIVesselAreaMap)
        schema_editor.create_model(SOIApplicabilityLog)
        schema_editor.create_model(SafetyFieldHistory)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE vims_safety_soi_finding (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                public_id VARCHAR(36) NULL UNIQUE,
                inspection_id BIGINT NOT NULL,
                area_id INTEGER NOT NULL,
                item_id BIGINT NULL,
                title VARCHAR(256) NOT NULL,
                description TEXT NOT NULL,
                severity VARCHAR(8) NOT NULL,
                priority VARCHAR(8) NOT NULL,
                mscat_category_id INTEGER NULL,
                mscat_subcode_id VARCHAR(16) NULL,
                shell_tag VARCHAR(32) NULL,
                assigned_crew_id VARCHAR(64) NULL,
                due_date DATE NULL,
                proposed_action TEXT NULL,
                status VARCHAR(24) NOT NULL,
                carried_forward_count INTEGER NOT NULL DEFAULT 0,
                photo_attachment_path VARCHAR(512) NULL,
                master_approved_at DATETIME NULL,
                master_approved_by VARCHAR(64) NULL,
                closed_at DATETIME NULL,
                closure_note TEXT NULL,
                schema_version INTEGER NOT NULL DEFAULT 1,
                is_deleted BOOLEAN NOT NULL DEFAULT 0,
                created_by VARCHAR(128) NOT NULL,
                created_date DATETIME NULL,
                updated_by VARCHAR(128) NULL,
                updated_date DATETIME NULL,
                CHECK (status IN ('OPEN', 'PENDING_CLOSURE', 'MASTER_APPROVED', 'CLOSED', 'CARRIED_FORWARD')),
                CHECK (severity <> 'HIGH' OR photo_attachment_path IS NOT NULL)
            )
            """
        )


def recreate_cms_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS HRM501")
        cursor.execute("DROP TABLE IF EXISTS Crew_Onboarding_History")
        cursor.execute(
            """
            CREATE TABLE Crew_Onboarding_History (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crew_id VARCHAR(64) NOT NULL,
                vessel_id VARCHAR(64) NOT NULL,
                department VARCHAR(32) NULL,
                rank VARCHAR(32) NULL,
                is_current BOOLEAN NOT NULL DEFAULT 1
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE HRM501 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crew_id VARCHAR(64) NOT NULL,
                department VARCHAR(32) NULL,
                rank VARCHAR(32) NULL
            )
            """
        )


def recreate_wrh_s520_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS wrh_s520_day_entry")
        cursor.execute("DROP TABLE IF EXISTS wrh_s520_month")
        cursor.execute("DROP TABLE IF EXISTS wrh_ship_time_config")
        cursor.execute(
            """
            CREATE TABLE wrh_ship_time_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vessel_id VARCHAR(64) NOT NULL,
                effective_date DATE NOT NULL,
                tz_offset_minutes INTEGER NOT NULL,
                set_by INTEGER NULL,
                set_at DATETIME NULL,
                reason TEXT NULL,
                created_at DATETIME NULL,
                sync_id VARCHAR(64) NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE wrh_s520_month (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crew_id VARCHAR(64) NOT NULL,
                vessel_id VARCHAR(64) NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                status VARCHAR(32) NULL,
                submitted_at DATETIME NULL,
                verified_by VARCHAR(64) NULL,
                verified_at DATETIME NULL,
                approved_by VARCHAR(64) NULL,
                approved_at DATETIME NULL,
                locked_at DATETIME NULL,
                unlocked_by INTEGER NULL,
                unlocked_at DATETIME NULL,
                unlock_reason TEXT NULL,
                comments TEXT NULL,
                created_at DATETIME NULL,
                updated_at DATETIME NULL,
                sync_id VARCHAR(64) NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE wrh_s520_day_entry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                s520_month_id INTEGER NOT NULL,
                crew_id VARCHAR(64) NOT NULL,
                work_date_local DATE NOT NULL,
                tz_offset_minutes INTEGER NULL,
                day_number INTEGER NULL,
                work_blocks TEXT NULL,
                hours_work REAL NULL,
                hours_rest REAL NULL,
                total_rest_24h REAL NULL,
                total_rest_7d REAL NULL,
                longest_rest_block REAL NULL,
                rest_period_count INTEGER NULL,
                max_work_gap REAL NULL,
                mlc_10h_24h_status VARCHAR(32) NULL,
                mlc_77h_7d_status VARCHAR(32) NULL,
                mlc_6h_continuous_status VARCHAR(32) NULL,
                mlc_split_max_status VARCHAR(32) NULL,
                mlc_14h_gap_status VARCHAR(32) NULL,
                is_frozen BOOLEAN NULL,
                is_not_onboard BOOLEAN NULL,
                is_dateline_skip BOOLEAN NULL,
                is_dateline_repeat CHAR(1) NULL,
                vessel_condition VARCHAR(32) NULL,
                comments TEXT NULL,
                entered_by INTEGER NULL,
                saved_at DATETIME NULL,
                ip_address VARCHAR(64) NULL,
                nc_generation_pending BOOLEAN NULL,
                created_at DATETIME NULL,
                updated_at DATETIME NULL,
                sync_id VARCHAR(64) NULL
            )
            """
        )


def recreate_phase5_reference_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS master_safety_bias_guard")
        cursor.execute("DROP TABLE IF EXISTS master_mscat_taxonomy")
        cursor.execute(
            """
            CREATE TABLE master_mscat_taxonomy (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                category_id INTEGER NOT NULL,
                category_name VARCHAR(128) NOT NULL,
                subcode_id VARCHAR(16) NOT NULL UNIQUE,
                subcode_description TEXT NOT NULL,
                cause_type VARCHAR(32) NOT NULL,
                active BOOLEAN NOT NULL DEFAULT 1,
                seeded_version VARCHAR(16) NOT NULL DEFAULT 'v1.0-Round21',
                schema_version INTEGER NOT NULL DEFAULT 1,
                updated_by VARCHAR(128) NULL,
                updated_date DATETIME NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE master_safety_bias_guard (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                guard_code VARCHAR(32) NOT NULL UNIQUE,
                guard_name VARCHAR(128) NOT NULL,
                family VARCHAR(16) NOT NULL,
                description TEXT NOT NULL,
                bit_position INTEGER NOT NULL,
                active BOOLEAN NOT NULL DEFAULT 1
            )
            """
        )


def seed_phase5_reference_tables() -> None:
    from apps.safety.management.commands.seed_master_safety import (
        load_bias_guard_rows,
        load_mscat_taxonomy_rows,
    )

    mscat_rows = load_mscat_taxonomy_rows()
    bias_guard_rows = load_bias_guard_rows()

    with connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO master_mscat_taxonomy (
                id,
                legacy_int_id,
                category_id,
                category_name,
                subcode_id,
                subcode_description,
                cause_type,
                active,
                seeded_version,
                schema_version,
                updated_by,
                updated_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 1, 'v1.0-Round21', 1, NULL, NULL)
            """,
            [
                (
                    f"{index:032x}",
                    index,
                    row["category_id"],
                    row["category_name"],
                    row["subcode_id"],
                    row["subcode_description"],
                    row["cause_type"],
                )
                for index, row in enumerate(mscat_rows, start=1)
            ],
        )
        cursor.executemany(
            """
            INSERT INTO master_safety_bias_guard (
                id,
                legacy_int_id,
                guard_code,
                guard_name,
                family,
                description,
                bit_position,
                active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    f"{10000 + index:032x}",
                    index,
                    row["guard_code"],
                    row["guard_name"],
                    row["family"],
                    row["description"],
                    row["bit_position"],
                    row["active"],
                )
                for index, row in enumerate(bias_guard_rows, start=1)
            ],
        )


def recreate_purchase_requisition_table() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS pur_requisition")
        cursor.execute(
            """
            CREATE TABLE pur_requisition (
                id INTEGER PRIMARY KEY,
                status VARCHAR(32) NOT NULL,
                is_archived BOOLEAN NOT NULL DEFAULT 0
            )
            """
        )


def recreate_mscmepc3_support_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS master_loss_types")
        cursor.execute("DROP TABLE IF EXISTS master_safety_incident_type")
        cursor.execute("DROP TABLE IF EXISTS VesselData")
        cursor.execute("DROP TABLE IF EXISTS NoonReport")
        cursor.execute(
            """
            CREATE TABLE master_loss_types (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                loss_type_id INTEGER NOT NULL,
                loss_type_name VARCHAR(64) NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE master_safety_incident_type (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                type_name VARCHAR(128) NOT NULL,
                type_code VARCHAR(32) NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE VesselData (
                id VARCHAR(64) PRIMARY KEY,
                vesselCode VARCHAR(8) NULL,
                vesselName VARCHAR(128) NULL,
                imoNumber VARCHAR(32) NULL,
                flags VARCHAR(64) NULL,
                ClassificationSociety VARCHAR(64) NULL,
                grt DECIMAL(18,3) NULL,
                nrt DECIMAL(18,3) NULL,
                deadweight DECIMAL(18,3) NULL,
                LastPortofcall VARCHAR(128) NULL,
                ShipOwner TEXT NULL,
                ShipManagement TEXT NULL,
                is_deleted BOOLEAN NULL DEFAULT 0
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE NoonReport (
                id VARCHAR(64) NOT NULL,
                auto_id INTEGER NOT NULL,
                VesselID VARCHAR(8) NULL,
                ReportDate DATETIME NULL,
                VoyageNo VARCHAR(100) NULL,
                VoyCondition VARCHAR(250) NULL,
                Lattitude1 INTEGER NULL,
                Lattitude2 INTEGER NULL,
                Lattitude3 VARCHAR(1) NULL,
                Longitude1 INTEGER NULL,
                Longitud2 INTEGER NULL,
                Longitud3 VARCHAR(1) NULL,
                WeatherRemarks TEXT NULL,
                WindForce INTEGER NULL,
                SeaState INTEGER NULL,
                CurrentStrength DECIMAL(9,2) NULL,
                TotalCargoWeight DECIMAL(18,2) NULL
            )
            """
        )


def recreate_taxonomy_reference_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS master_safety_case_study")
        cursor.execute("DROP TABLE IF EXISTS master_safety_incident_type")
        cursor.execute("DROP TABLE IF EXISTS master_loss_types")
        cursor.execute("DROP TABLE IF EXISTS master_immediate_causes")
        cursor.execute(
            """
            CREATE TABLE master_immediate_causes (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                category_id INTEGER NOT NULL,
                category_name VARCHAR(128) NOT NULL,
                subcode_id VARCHAR(16) NOT NULL,
                subcode_description TEXT NOT NULL,
                cause_type VARCHAR(32) NOT NULL,
                active BOOLEAN NOT NULL DEFAULT 1,
                seeded_version VARCHAR(16) NOT NULL DEFAULT 'v1.0',
                schema_version INTEGER NOT NULL DEFAULT 1,
                updated_by VARCHAR(128) NULL,
                updated_date DATETIME NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE master_loss_types (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                loss_type_id INTEGER NOT NULL UNIQUE,
                loss_type_name VARCHAR(64) NOT NULL,
                description VARCHAR(128) NOT NULL,
                active BOOLEAN NOT NULL DEFAULT 1,
                seeded_version VARCHAR(16) NOT NULL DEFAULT 'v1.0'
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE master_safety_incident_type (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                type_code VARCHAR(32) NOT NULL UNIQUE,
                type_name VARCHAR(128) NOT NULL,
                imo_reportable BOOLEAN NOT NULL DEFAULT 0,
                description TEXT NULL,
                active BOOLEAN NOT NULL DEFAULT 1
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE master_safety_case_study (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                slug VARCHAR(64) NOT NULL UNIQUE,
                title VARCHAR(128) NOT NULL,
                event_type VARCHAR(128) NOT NULL,
                loss_summary VARCHAR(256) NOT NULL,
                incident_date DATE NOT NULL,
                immediate_cause_codes VARCHAR(128) NOT NULL,
                basic_cause_codes VARCHAR(128) NOT NULL,
                narrative TEXT NOT NULL,
                recommendations TEXT NOT NULL,
                source_label VARCHAR(128) NOT NULL DEFAULT 'DNV worked solution',
                active BOOLEAN NOT NULL DEFAULT 1,
                display_order INTEGER NOT NULL DEFAULT 0,
                created_by VARCHAR(128) NOT NULL DEFAULT 'seed_case_studies',
                created_date DATETIME NULL,
                updated_by VARCHAR(128) NULL,
                updated_date DATETIME NULL
            )
            """
        )


def recreate_near_miss_reference_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS master_mscat_taxonomy")
        cursor.execute("DROP TABLE IF EXISTS master_loss_types")
        cursor.execute("DROP TABLE IF EXISTS master_safety_incident_type")
        cursor.execute(
            """
            CREATE TABLE master_safety_incident_type (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                type_code VARCHAR(64) NOT NULL UNIQUE,
                type_name VARCHAR(128) NOT NULL,
                imo_reportable BOOLEAN NOT NULL DEFAULT 0,
                description TEXT NULL,
                active BOOLEAN NOT NULL DEFAULT 1
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE master_loss_types (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                loss_type_id INTEGER NOT NULL UNIQUE,
                loss_type_name VARCHAR(64) NOT NULL,
                description VARCHAR(128) NOT NULL,
                active BOOLEAN NOT NULL DEFAULT 1,
                seeded_version VARCHAR(16) NOT NULL DEFAULT 'v1.0'
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE master_mscat_taxonomy (
                id CHAR(32) PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                legacy_int_id INTEGER UNIQUE,
                category_id INTEGER NOT NULL,
                category_name VARCHAR(128) NOT NULL,
                subcode_id VARCHAR(16) NOT NULL UNIQUE,
                subcode_description TEXT NOT NULL,
                cause_type VARCHAR(32) NOT NULL,
                active BOOLEAN NOT NULL DEFAULT 1,
                seeded_version VARCHAR(16) NOT NULL DEFAULT 'v1.0-Round21',
                schema_version INTEGER NOT NULL DEFAULT 1,
                updated_by VARCHAR(128) NULL,
                updated_date DATETIME NULL
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO master_safety_incident_type (
                id, legacy_int_id, type_code, type_name, imo_reportable, description, active
            ) VALUES ('00000000000000000000000000000001', 1, 'PERSONAL_NEAR_MISS', 'Personal near miss', 0, 'Near miss fixture', 1)
            """
        )
        cursor.execute(
            """
            INSERT INTO master_loss_types (
                id, legacy_int_id, loss_type_id, loss_type_name, description, active, seeded_version
            ) VALUES ('00000000000000000000000000000002', 1, 1, 'People', 'People exposure', 1, 'v1.0')
            """
        )
        cursor.execute(
            """
            INSERT INTO master_mscat_taxonomy (
                id,
                legacy_int_id,
                category_id,
                category_name,
                subcode_id,
                subcode_description,
                cause_type,
                active
            ) VALUES ('00000000000000000000000000000003', 1, 10, 'Immediate Causes', '10.01', 'Unsafe condition observed', 'Immediate', 1)
            """
        )
