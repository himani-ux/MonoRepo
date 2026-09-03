from __future__ import annotations

import os
import tempfile
import unittest
import uuid
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import django
from django.apps import apps
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import override_settings
from django.utils import timezone


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-registration-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "apps.accounts",
                "apps.masters",
                "apps.inspection",
                "apps.car",
                "apps.notifications",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            ROOT_URLCONF="core.urls",
        )

    if not apps.ready:
        django.setup()


bootstrap_django()

from apps.accounts.models import RoleCodes  # noqa: E402
from apps.inspection.audit.models import (  # noqa: E402
    AuditAttachment,
    AuditDetail,
    AuditMeetingAttendee,
    AuditScheduleBlock,
    AuditStandard,
    AuditTeamMember,
    MasterAuditPlan,
    MasterAuditQualifiedAuditor,
    MasterExternalAuditOrg,
    VesselAuditRoDelegation,
)
from apps.inspection.audit.permissions import AUDIT_P_001, AUDIT_P_003, AUDIT_P_013  # noqa: E402
from apps.inspection.audit.services import auditor_selection, registration as registration_service  # noqa: E402
from apps.inspection.audit.services import vessels as vessel_service  # noqa: E402
from apps.inspection.audit.views import AuditRegistrationView  # noqa: E402
from apps.inspection.models import Inspection  # noqa: E402
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402


SCHEMA_MODELS = [
    Inspection,
    AuditDetail,
    AuditAttachment,
    AuditStandard,
    AuditTeamMember,
    AuditMeetingAttendee,
    AuditScheduleBlock,
    MasterAuditPlan,
    MasterAuditQualifiedAuditor,
    MasterExternalAuditOrg,
    VesselAuditRoDelegation,
]


def make_user(
    *,
    role: str = RoleCodes.OFFICE_SSQE,
    user_type: str = "OFFICE",
    user_id: str = "auditor-1",
    process_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        process_ids=process_ids or [],
        display_name="Audit User",
        username="audit_user",
        is_authenticated=True,
    )


class AuditRegistrationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            existing_tables = set(connection.introspection.table_names())
            for model in reversed(SCHEMA_MODELS):
                if model._meta.db_table in existing_tables:
                    schema_editor.delete_model(model)
            for model in SCHEMA_MODELS:
                schema_editor.create_model(model)

    @classmethod
    def tearDownClass(cls) -> None:
        with connection.schema_editor() as schema_editor:
            for model in reversed(SCHEMA_MODELS):
                schema_editor.delete_model(model)
        super().tearDownClass()

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            for model in reversed(SCHEMA_MODELS):
                cursor.execute(f"DELETE FROM {model._meta.db_table}")
        self.factory = APIRequestFactory()
        self.vessel_id = uuid.uuid4()
        self.external_org = MasterExternalAuditOrg.objects.create(
            name="DNV",
            org_type="CLASS_SOCIETY",
            country="Singapore",
            is_active=True,
            created_by="seed",
        )
        MasterAuditQualifiedAuditor.objects.create(
            user_id="lead-1",
            qualification_text="ISM Lead Auditor",
            qualification_date=timezone.localdate() - timedelta(days=30),
            expiry_date=timezone.localdate() + timedelta(days=365),
            scope_standards_csv="ISM,ISPS,MLC,EMS",
            auditor_scope="INTERNAL",
            qualified_for_seq=True,
            created_by="seed",
        )

    def _post_registration(self, payload, user):
        request = self.factory.post("/api/audit/audits/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditRegistrationView.as_view()(request)

    def _post_registration_multipart(self, payload, user):
        request = self.factory.post("/api/audit/audits/", payload, format="multipart")
        force_authenticate(request, user=user)
        return AuditRegistrationView.as_view()(request)

    def _get_registered_audits(self, user):
        request = self.factory.get("/api/audit/audits/")
        force_authenticate(request, user=user)
        return AuditRegistrationView.as_view()(request)

    def _valid_payload(self):
        return {
            "vessel_id": str(self.vessel_id),
            "inspection_date": "2026-07-29",
            "port_place": "Singapore",
            "country": "Singapore",
            "inspector_name": "Lead Auditor",
            "report_reference": "F601-2026-001",
            "audit_classification": "INTERNAL",
            "auditee_type": "VESSEL",
            "audit_subtype": "ANNUAL_INTERNAL",
            "lead_auditor_name": "Lead Auditor",
            "lead_auditor_designation": "Marine Auditor",
            "lead_auditor_company": "KSM",
            "lead_auditor_qual": "ISM Lead Auditor",
            "lead_auditor_user_id": "lead-1",
            "trigger_reason": "SCHEDULED",
            "audit_start_date": "2026-07-29",
            "audit_end_date": "2026-07-30",
            "opening_meeting_at": "2026-07-29T09:00:00+05:30",
            "closing_meeting_at": "2026-07-30T16:00:00+05:30",
            "audit_scope": "Internal vessel audit scope.",
            "terms_of_reference": "SQE F 601 annual internal audit.",
            "prev_internal_ca_verified": "YES",
            "prev_external_ca_verified": "NA",
            "standards": ["ISM", "ISPS", "MLC", "EMS"],
            "team_members": [
                {
                    "member_name": "Co Auditor",
                    "member_designation": "Technical Superintendent",
                    "member_company": "KSM",
                    "member_role": "CO_AUDITOR",
                }
            ],
            "attendees": [
                {
                    "attendee_name": "Master Name",
                    "attendee_rank": "Master",
                    "opening_present": True,
                    "closing_present": True,
                }
            ],
            "schedule_blocks": [
                {
                    "block_date": "2026-07-29",
                    "time_from": "09:00:00",
                    "time_to": "10:00:00",
                    "activity": "Opening meeting",
                }
            ],
        }

    def _valid_external_payload(self):
        completed_on = timezone.localdate() - timedelta(days=10)
        return {
            "vessel_id": str(self.vessel_id),
            "inspection_date": completed_on.isoformat(),
            "port_place": "Singapore",
            "country": "Singapore",
            "authority": "DNV",
            "inspector_name": "External Surveyor",
            "report_reference": "DNV-SMC-2026-001",
            "audit_classification": "EXTERNAL",
            "auditee_type": "VESSEL",
            "audit_start_date": completed_on.isoformat(),
            "audit_end_date": completed_on.isoformat(),
            "standards": ["ISM", "ISPS", "MLC"],
            "external_audit_subtypes": ["SMC_RENEWAL", "MLC_RENEWAL", "ISPS_RENEWAL"],
            "external_audit_org_id": str(self.external_org.id),
            "external_audit_org_type": "CLASS_SOCIETY",
            "external_lead_auditor_name": "L. Bergstrom",
            "external_lead_auditor_credential": "IMO ISM/ISPS/MLC Auditor",
            "linked_cert_ids": [str(uuid.uuid4()), str(uuid.uuid4())],
            "external_report_file_name": "DNV-audit-report-2026.pdf",
            "external_report_file_path": "/audit/external/DNV-audit-report-2026.pdf",
            "external_report_mime_type": "application/pdf",
            "external_report_file_size": 145000,
        }

    def _confirmed_plan(self, *, status: str = "CONFIRMED") -> MasterAuditPlan:
        return MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM,ISPS",
            lead_auditor_user_id="lead-1",
            planned_window_start=timezone.localdate(),
            planned_window_end=timezone.localdate() + timedelta(days=30),
            status=status,
            created_by="seq-1",
        )

    def _confirmed_office_plan(self, *, department: str = "TECH", status: str = "CONFIRMED") -> MasterAuditPlan:
        return MasterAuditPlan.objects.create(
            target_vessel_id=None,
            target_office_dept=department,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM,ISPS",
            lead_auditor_user_id="lead-1",
            planned_window_start=timezone.localdate(),
            planned_window_end=timezone.localdate() + timedelta(days=30),
            status=status,
            created_by="seq-1",
        )

    def test_office_user_registers_internal_vessel_audit_with_f601_rows(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_003])

        response = self._post_registration(self._valid_payload(), user)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Inspection.objects.count(), 1)
        self.assertEqual(AuditDetail.objects.count(), 1)
        inspection = Inspection.objects.get()
        audit_detail = AuditDetail.objects.get()
        self.assertEqual(inspection.inspection_type, "AUDIT")
        self.assertFalse(inspection.is_detention)
        self.assertIsNone(inspection.psc_subtype)
        self.assertEqual(audit_detail.psc_inspection_id, inspection.id.hex)
        self.assertEqual(audit_detail.vessel_id, self.vessel_id.hex)
        self.assertEqual(audit_detail.status, "IN_PROGRESS")
        self.assertEqual(set(AuditStandard.objects.values_list("standard_code", flat=True)), {"ISM", "ISPS", "MLC", "EMS"})
        self.assertEqual(AuditTeamMember.objects.get().member_role, "CO_AUDITOR")
        self.assertTrue(AuditMeetingAttendee.objects.get().opening_present)
        self.assertEqual(AuditScheduleBlock.objects.get().activity, "Opening meeting")
        self.assertEqual(response.data["data"]["inspection_id"], str(inspection.id))
        self.assertEqual(response.data["data"]["status"], "IN_PROGRESS")

    def test_registered_audit_list_returns_audits_assigned_to_lead_auditor(self) -> None:
        creator = make_user(process_ids=[AUDIT_P_001, AUDIT_P_003])
        created = self._post_registration(self._valid_payload(), creator)
        self.assertEqual(created.status_code, 201)

        lead_user = make_user(user_id="lead-1", process_ids=[])
        response = self._get_registered_audits(lead_user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["count"], 1)
        row = response.data["data"]["results"][0]
        self.assertEqual(row["id"], created.data["data"]["id"])
        self.assertEqual(row["target_label"], f"Vessel {self.vessel_id.hex}")
        self.assertEqual(row["lead_auditor_name"], "Lead Auditor")
        self.assertEqual(row["status"], "IN_PROGRESS")

    def test_audit_vessel_label_map_matches_compact_and_dashed_uuid_keys(self) -> None:
        vessel_id = uuid.UUID("a1170000-0000-0000-0000-000000000001")

        with patch.object(
            vessel_service,
            "_lookup_vessel_rows",
            return_value=[
                {
                    "id": str(vessel_id),
                    "vessel_code": "EAT",
                    "vessel_name": "EAST AYUTTHAYA",
                }
            ],
        ):
            labels = vessel_service.audit_vessel_label_map([vessel_id.hex])

        self.assertEqual(labels[vessel_id.hex], "EAT - EAST AYUTTHAYA")
        self.assertEqual(labels[str(vessel_id)], "EAT - EAST AYUTTHAYA")

    def test_audit_detail_uuid_references_are_compact_for_character_columns(self) -> None:
        value = uuid.UUID("a1170000-0000-0000-0000-000000000001")

        with patch.object(registration_service, "connection", SimpleNamespace(vendor="microsoft")):
            self.assertEqual(registration_service._audit_detail_uuid_reference(value), value.hex)
            self.assertEqual(registration_service._audit_detail_uuid_reference(str(value)), value.hex)

    def test_sql_server_audit_detail_insert_casts_uniqueidentifier_columns(self) -> None:
        value = uuid.UUID("a1170000-0000-0000-0000-000000000001")

        expression, params = registration_service._sql_value_for_column(
            "id",
            value,
            {"id": {"data_type": "uniqueidentifier", "max_length": None}},
        )

        self.assertEqual(expression, "CAST(%s AS uniqueidentifier)")
        self.assertEqual(params, [str(value)])

    def test_sql_server_audit_detail_insert_casts_compact_uuid_for_uniqueidentifier_columns(self) -> None:
        value = uuid.UUID("a1170000-0000-0000-0000-000000000001")

        expression, params = registration_service._sql_value_for_column(
            "psc_inspection_id",
            value.hex,
            {"psc_inspection_id": {"data_type": "uniqueidentifier", "max_length": None}},
        )

        self.assertEqual(expression, "CAST(%s AS uniqueidentifier)")
        self.assertEqual(params, [str(value)])

    def test_sql_server_registration_child_uuid_insert_casts_audit_detail_id(self) -> None:
        value = uuid.UUID("a1170000-0000-0000-0000-000000000001")

        expression, params = registration_service._sql_value_for_column(
            "audit_detail_id",
            value.hex,
            {"audit_detail_id": {"data_type": "uniqueidentifier", "max_length": None}},
        )

        self.assertEqual(expression, "CAST(%s AS uniqueidentifier)")
        self.assertEqual(params, [str(value)])

    def test_sql_server_registration_child_rows_use_safe_insert_path(self) -> None:
        row = {
            "audit_detail_id": uuid.UUID("a1170000-0000-0000-0000-000000000001"),
            "standard_code": "ISM",
            "sequence_no": 1,
            "created_by": "auditor-1",
        }

        with (
            patch.object(registration_service, "connection", SimpleNamespace(vendor="microsoft")),
            patch.object(registration_service, "_insert_sql_server_row") as insert_row,
        ):
            registration_service._bulk_create_registration_rows(AuditStandard, "audit_standards", [row])

        insert_row.assert_called_once_with("audit_standards", row)
        self.assertEqual(AuditStandard.objects.count(), 0)

    def test_sql_server_registration_plan_lookup_casts_uuid_for_validation(self) -> None:
        plan = MasterAuditPlan(
            id=uuid.UUID("a1170000-0000-0000-0000-000000000001"),
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            lead_auditor_user_id="lead-1",
            planned_window_start=timezone.localdate(),
            planned_window_end=timezone.localdate() + timedelta(days=30),
            status="CONFIRMED",
            created_by="seq-1",
        )

        with (
            patch.object(registration_service, "connection", SimpleNamespace(vendor="microsoft")),
            patch.object(MasterAuditPlan.objects, "raw", return_value=[plan]) as raw_query,
        ):
            fetched = registration_service.get_audit_plan_by_id(str(plan.id))

        sql, params = raw_query.call_args.args
        self.assertIs(fetched, plan)
        self.assertIn("WHERE id = CAST(%s AS uniqueidentifier)", sql)
        self.assertEqual(params, [str(plan.id)])

    def test_sql_server_registration_plan_lock_casts_uuid_for_consumption(self) -> None:
        plan = MasterAuditPlan(
            id=uuid.UUID("a1170000-0000-0000-0000-000000000001"),
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            lead_auditor_user_id="lead-1",
            planned_window_start=timezone.localdate(),
            planned_window_end=timezone.localdate() + timedelta(days=30),
            status="CONFIRMED",
            created_by="seq-1",
        )

        with (
            patch.object(registration_service, "connection", SimpleNamespace(vendor="microsoft")),
            patch.object(MasterAuditPlan.objects, "raw", return_value=[plan]) as raw_query,
        ):
            fetched = registration_service.get_audit_plan_by_id(str(plan.id), for_update=True)

        sql, params = raw_query.call_args.args
        self.assertIs(fetched, plan)
        self.assertIn("FROM dbo.master_audit_plan WITH (UPDLOCK, ROWLOCK)", sql)
        self.assertIn("WHERE id = CAST(%s AS uniqueidentifier)", sql)
        self.assertEqual(params, [str(plan.id)])

    def test_sql_server_external_org_lookup_casts_uuid_for_validation(self) -> None:
        org_id = uuid.UUID("a1170000-0000-0000-0000-000000000010")
        org = MasterExternalAuditOrg(
            id=org_id,
            name="DNV",
            org_type="CLASS_SOCIETY",
            is_active=True,
            created_by="seed",
        )

        with (
            patch.object(auditor_selection, "connection", SimpleNamespace(vendor="microsoft")),
            patch.object(MasterExternalAuditOrg.objects, "raw", return_value=[org]) as raw_query,
            patch.object(MasterExternalAuditOrg.objects, "filter", side_effect=AssertionError("SQL Server lookup must cast UUID values")),
        ):
            fetched = auditor_selection.get_external_org_by_id(org_id.hex)

        sql, params = raw_query.call_args.args
        self.assertIs(fetched, org)
        self.assertIn("FROM dbo.master_external_audit_org", sql)
        self.assertIn("WHERE id = CAST(%s AS uniqueidentifier)", sql)
        self.assertEqual(params, [str(org_id)])

    def test_sql_server_external_org_delegation_lookup_casts_vessel_uuid(self) -> None:
        vessel_id = uuid.UUID("a1170000-0000-0000-0000-000000000020")
        org = MasterExternalAuditOrg(
            id=uuid.UUID("a1170000-0000-0000-0000-000000000021"),
            name="DNV",
            org_type="CLASS_SOCIETY",
            is_active=True,
            created_by="seed",
        )
        effective_on = timezone.localdate()

        with (
            patch.object(auditor_selection, "connection", SimpleNamespace(vendor="microsoft")),
            patch.object(MasterExternalAuditOrg.objects, "raw", return_value=[org]) as raw_query,
            patch.object(VesselAuditRoDelegation.objects, "filter", side_effect=AssertionError("SQL Server lookup must cast UUID values")),
            patch.object(MasterExternalAuditOrg.objects, "filter", side_effect=AssertionError("SQL Server lookup must not use ORM UUID filtering")),
        ):
            fetched = auditor_selection.resolve_external_org_for_vessel_standard(
                vessel_id=vessel_id.hex,
                standards=["ISM", "ISPS"],
                effective_on=effective_on,
            )

        sql, params = raw_query.call_args.args
        self.assertIs(fetched, org)
        self.assertIn("FROM dbo.master_external_audit_org org", sql)
        self.assertIn("INNER JOIN dbo.vessel_audit_ro_delegation delegation", sql)
        self.assertIn("delegation.target_vessel_id = CAST(%s AS uniqueidentifier)", sql)
        self.assertIn("delegation.standard_code IN (%s, %s)", sql)
        self.assertEqual(params, [str(vessel_id), "ISM", "ISPS", effective_on, effective_on])

    def test_sql_server_registerable_plan_duplicate_check_casts_audit_plan_id(self) -> None:
        class Cursor:
            sql = ""
            params = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def execute(self, sql, params=None):
                self.sql = sql
                self.params = params or []

            def fetchone(self):
                return None

        cursor = Cursor()
        plan = MasterAuditPlan(
            id=uuid.UUID("a1170000-0000-0000-0000-000000000001"),
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=timezone.localdate(),
            planned_window_end=timezone.localdate() + timedelta(days=30),
            status="CONFIRMED",
            created_by="seq-1",
        )

        with patch.object(registration_service, "connection", SimpleNamespace(vendor="microsoft", cursor=lambda: cursor)):
            registration_service.validate_registerable_audit_plan(plan)

        self.assertIn("audit_plan_id = CAST(%s AS uniqueidentifier)", cursor.sql)
        self.assertIn("is_deleted = 0", cursor.sql)
        self.assertEqual(cursor.params, [str(plan.id)])

    def test_sql_server_registerable_plan_duplicate_check_casts_excluded_audit_detail_id(self) -> None:
        class Cursor:
            sql = ""
            params = []

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def execute(self, sql, params=None):
                self.sql = sql
                self.params = params or []

            def fetchone(self):
                return None

        cursor = Cursor()
        plan_id = uuid.UUID("a1170000-0000-0000-0000-000000000001")
        audit_detail_id = uuid.UUID("a1170000-0000-0000-0000-000000000002")

        with patch.object(registration_service, "connection", SimpleNamespace(vendor="microsoft", cursor=lambda: cursor)):
            exists = registration_service._registered_audit_exists_for_plan(
                plan_id,
                exclude_audit_detail_id=audit_detail_id,
            )

        self.assertFalse(exists)
        self.assertIn("audit_plan_id = CAST(%s AS uniqueidentifier)", cursor.sql)
        self.assertIn("id <> CAST(%s AS uniqueidentifier)", cursor.sql)
        self.assertEqual(cursor.params, [str(plan_id), str(audit_detail_id)])

    def test_audit_detail_insert_length_guard_reports_truncating_field(self) -> None:
        with self.assertRaises(Exception) as raised:
            registration_service._validate_audit_detail_lengths(
                {"lead_auditor_name": "x" * 201},
                {"lead_auditor_name": {"data_type": "nvarchar", "max_length": 200}},
            )

        self.assertIn("lead_auditor_name", str(raised.exception))

    def test_audit_detail_insert_length_guard_allows_max_length_text(self) -> None:
        registration_service._validate_audit_detail_lengths(
            {"lead_auditor_name": "x" * 200},
            {"lead_auditor_name": {"data_type": "nvarchar", "max_length": 200}},
        )

    def test_default_audit_detail_uuid_references_keep_legacy_compact_format(self) -> None:
        value = uuid.UUID("a1170000-0000-0000-0000-000000000001")

        self.assertEqual(registration_service._audit_detail_uuid_reference(value), value.hex)
        self.assertEqual(registration_service._audit_detail_uuid_reference(str(value)), value.hex)

    def test_internal_registration_copies_lead_auditor_snapshot_from_plan(self) -> None:
        plan = self._confirmed_plan()
        payload = self._valid_payload()
        payload["audit_plan_id"] = str(plan.id)
        payload["lead_auditor_name"] = ""
        payload["lead_auditor_designation"] = ""
        payload["lead_auditor_company"] = ""
        payload["lead_auditor_qual"] = ""
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_003])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 201)
        audit_detail = AuditDetail.objects.get()
        self.assertEqual(str(audit_detail.audit_plan_id), str(plan.id))
        self.assertEqual(audit_detail.lead_auditor_user_id, "lead-1")
        self.assertEqual(audit_detail.lead_auditor_name, "lead-1")
        self.assertEqual(audit_detail.lead_auditor_company, "KSM")
        self.assertEqual(audit_detail.lead_auditor_qual, "ISM Lead Auditor")
        plan.refresh_from_db()
        self.assertEqual(plan.status, "IN_PROGRESS")

    def test_internal_registration_rejects_non_registerable_plan_status(self) -> None:
        plan = self._confirmed_plan(status="PLANNED")
        payload = self._valid_payload()
        payload["audit_plan_id"] = str(plan.id)
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_003])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("audit_plan_id", response.data)
        self.assertEqual(AuditDetail.objects.count(), 0)

    def test_internal_registration_rejects_office_plan_for_vessel_payload(self) -> None:
        plan = self._confirmed_office_plan(department="TECH")
        payload = self._valid_payload()
        payload["audit_plan_id"] = str(plan.id)
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_003])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("audit_plan_id", response.data)
        self.assertEqual(AuditDetail.objects.count(), 0)
        plan.refresh_from_db()
        self.assertEqual(plan.status, "CONFIRMED")

    def test_internal_registration_rejects_vessel_plan_for_office_payload(self) -> None:
        plan = self._confirmed_plan()
        payload = self._valid_payload()
        payload["audit_plan_id"] = str(plan.id)
        payload["auditee_type"] = "OFFICE_DEPT"
        payload["auditee_office_dept"] = "TECH"
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_003])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("audit_plan_id", response.data)
        self.assertEqual(AuditDetail.objects.count(), 0)
        plan.refresh_from_db()
        self.assertEqual(plan.status, "CONFIRMED")

    def test_internal_registration_rejects_plan_already_registered(self) -> None:
        plan = self._confirmed_plan()
        inspection = Inspection.objects.create(
            vessel_id=self.vessel_id,
            inspection_type="AUDIT",
            inspection_date=timezone.localdate(),
            port_place="Singapore",
            created_by="seed",
        )
        AuditDetail.objects.create(
            psc_inspection_id=inspection.id.hex,
            vessel_id=self.vessel_id.hex,
            audit_classification="INTERNAL",
            auditee_type="VESSEL",
            audit_subtype="ANNUAL_INTERNAL",
            lead_auditor_name="Lead Auditor",
            lead_auditor_company="KSM",
            trigger_reason="SCHEDULED",
            audit_plan_id=plan.id,
            audit_start_date=timezone.localdate(),
            status="IN_PROGRESS",
            created_by="seed",
        )
        payload = self._valid_payload()
        payload["audit_plan_id"] = str(plan.id)
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_003])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("audit_plan_id", response.data)
        self.assertEqual(AuditDetail.objects.count(), 1)

    def test_vessel_user_cannot_register_audit(self) -> None:
        user = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[AUDIT_P_001, AUDIT_P_003],
        )

        response = self._post_registration(self._valid_payload(), user)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Inspection.objects.count(), 0)
        self.assertEqual(AuditDetail.objects.count(), 0)

    def test_office_department_requires_department_qualifier(self) -> None:
        payload = self._valid_payload()
        payload["auditee_type"] = "OFFICE_DEPT"
        payload["auditee_office_dept"] = ""
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_003])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("auditee_office_dept", response.data)
        self.assertEqual(Inspection.objects.count(), 0)

    def test_registration_requires_audit_create_or_conduct_gate(self) -> None:
        user = make_user(role=RoleCodes.PHYSICAL_VERIFIER, user_id="no-gate", process_ids=[])

        response = self._post_registration(self._valid_payload(), user)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Inspection.objects.count(), 0)

    def test_master_registers_external_vessel_audit_post_facto_at_submitted(self) -> None:
        user = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[],
        )

        response = self._post_registration(self._valid_external_payload(), user)

        self.assertEqual(response.status_code, 201)
        audit_detail = AuditDetail.objects.get()
        self.assertEqual(audit_detail.audit_classification, "EXTERNAL")
        self.assertEqual(audit_detail.status, "SUBMITTED")
        self.assertIsNone(audit_detail.audit_plan_id)
        self.assertEqual(audit_detail.trigger_reason, "OTHER")
        self.assertEqual(audit_detail.external_audit_subtypes_csv, "SMC_RENEWAL,MLC_RENEWAL,ISPS_RENEWAL")
        self.assertEqual(audit_detail.audit_subtype, "SMC_RENEWAL")
        self.assertEqual(audit_detail.external_audit_org_type, "CLASS_SOCIETY")
        self.assertEqual(audit_detail.external_lead_auditor_name, "L. Bergstrom")
        self.assertEqual(AuditAttachment.objects.get().category, "EXTERNAL_AUDIT_REPORT")
        self.assertEqual(response.data["data"]["status"], "SUBMITTED")

    def test_external_registration_accepts_pdf_upload_and_derives_metadata(self) -> None:
        user = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[AUDIT_P_013],
        )
        pdf_bytes = b"%PDF-1.4\nexternal audit report\n%%EOF"
        payload = self._valid_external_payload()
        for field in (
            "external_report_file_name",
            "external_report_file_path",
            "external_report_mime_type",
            "external_report_file_size",
        ):
            payload.pop(field)
        payload["external_report_file"] = SimpleUploadedFile(
            "DNV-audit-report-2026.pdf",
            pdf_bytes,
            content_type="application/pdf",
        )

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self._post_registration_multipart(payload, user)

            self.assertEqual(response.status_code, 201)
            attachment = AuditAttachment.objects.get()
            self.assertEqual(attachment.category, "EXTERNAL_AUDIT_REPORT")
            self.assertEqual(attachment.file_name, "DNV-audit-report-2026.pdf")
            self.assertEqual(attachment.mime_type, "application/pdf")
            self.assertEqual(attachment.file_size, len(pdf_bytes))
            self.assertTrue(attachment.file_path.startswith(f"audit/external/{self.vessel_id}/"))
            self.assertTrue(os.path.exists(os.path.join(media_root, attachment.file_path.replace("/", os.sep))))

    def test_external_registration_accepts_temporary_pdf_upload_without_copying_file_handle(self) -> None:
        user = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[AUDIT_P_013],
        )
        pdf_bytes = b"%PDF-1.4\nexternal audit report stored as temp upload\n%%EOF"
        payload = self._valid_external_payload()
        for field in (
            "external_report_file_name",
            "external_report_file_path",
            "external_report_mime_type",
            "external_report_file_size",
        ):
            payload.pop(field)
        payload["external_report_file"] = SimpleUploadedFile(
            "temporary-external-audit-report.pdf",
            pdf_bytes,
            content_type="application/pdf",
        )

        with tempfile.TemporaryDirectory() as media_root, override_settings(
            MEDIA_ROOT=media_root,
            FILE_UPLOAD_MAX_MEMORY_SIZE=1,
        ):
            response = self._post_registration_multipart(payload, user)

            self.assertEqual(response.status_code, 201)
            attachment = AuditAttachment.objects.get()
            self.assertEqual(attachment.file_name, "temporary-external-audit-report.pdf")
            self.assertEqual(attachment.file_size, len(pdf_bytes))

    def test_external_registration_defaults_org_from_ro_delegation(self) -> None:
        VesselAuditRoDelegation.objects.create(
            target_vessel_id=self.vessel_id,
            standard_code="ISM",
            master_external_audit_org_id=self.external_org.id,
            effective_from=timezone.localdate() - timedelta(days=30),
            effective_to=timezone.localdate() + timedelta(days=365),
            created_by="seed",
        )
        payload = self._valid_external_payload()
        payload["external_audit_org_id"] = ""
        payload["external_audit_org_type"] = ""
        user = make_user(process_ids=[AUDIT_P_013])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 201)
        audit_detail = AuditDetail.objects.get()
        self.assertEqual(str(audit_detail.external_audit_org_id), str(self.external_org.id))
        self.assertEqual(audit_detail.external_audit_org_type, "CLASS_SOCIETY")

    def test_external_registration_allows_missing_external_org_without_delegation(self) -> None:
        payload = self._valid_external_payload()
        payload["external_audit_org_id"] = None
        payload["external_audit_org_type"] = "CLASS_SOCIETY"
        user = make_user(process_ids=[AUDIT_P_013])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 201)
        audit_detail = AuditDetail.objects.get()
        self.assertIsNone(audit_detail.external_audit_org_id)
        self.assertEqual(audit_detail.external_audit_org_type, "CLASS_SOCIETY")

    def test_external_registration_requires_external_mandatory_fields(self) -> None:
        payload = self._valid_external_payload()
        payload["external_audit_org_id"] = None
        payload["external_report_file_name"] = ""
        user = make_user(process_ids=[AUDIT_P_013])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertNotIn("external_audit_org_id", response.data)
        self.assertIn("external_report_file_name", response.data)
        self.assertEqual(AuditDetail.objects.count(), 0)

    def test_external_registration_over_30_days_requires_dpa_override_reason(self) -> None:
        payload = self._valid_external_payload()
        old_date = timezone.localdate() - timedelta(days=34)
        payload["inspection_date"] = old_date.isoformat()
        payload["audit_start_date"] = old_date.isoformat()
        payload["audit_end_date"] = old_date.isoformat()
        user = make_user(process_ids=[AUDIT_P_013])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("late_registration_reason", response.data)

        payload["late_registration_reason"] = "DPA override because the class report arrived after port departure and required office verification."
        allowed = self._post_registration(payload, user)

        self.assertEqual(allowed.status_code, 201)
        audit_detail = AuditDetail.objects.get()
        self.assertEqual(audit_detail.late_registered_by, "auditor-1")
        self.assertIsNotNone(audit_detail.late_registered_at)

    def test_doc_external_registration_requires_flag_state_and_cycle_year(self) -> None:
        payload = self._valid_external_payload()
        payload["external_audit_subtypes"] = ["DOC_RENEWAL"]
        payload["standards"] = ["DOC"]
        user = make_user(process_ids=[AUDIT_P_013])

        response = self._post_registration(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("flag_state_code", response.data)
        self.assertIn("cycle_year", response.data)

    def test_duplicate_open_doc_external_audit_is_blocked_per_flag_cycle(self) -> None:
        payload = self._valid_external_payload()
        payload["external_audit_subtypes"] = ["DOC_RENEWAL"]
        payload["standards"] = ["DOC"]
        payload["flag_state_code"] = "SG"
        payload["cycle_year"] = timezone.localdate().year
        user = make_user(process_ids=[AUDIT_P_013])

        first = self._post_registration(payload, user)
        second = self._post_registration(payload, user)

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        self.assertIn("flag_state_code", second.data)


if __name__ == "__main__":
    unittest.main()
