from __future__ import annotations

import os
import unittest
import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import django
from django.apps import apps
from django.db import connection


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-plan-test-secret-key-1234567890",
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
from apps.inspection.models import Inspection  # noqa: E402
from apps.inspection.audit.models import MasterAuditPlan, MasterAuditQualifiedAuditor  # noqa: E402
from apps.inspection.audit.permissions import AUDIT_P_001, AUDIT_P_002, AUDIT_P_005, AUDIT_P_006  # noqa: E402
from apps.inspection.audit.views import plan as plan_views  # noqa: E402
from apps.inspection.audit.serializers import plan as plan_serializers  # noqa: E402
from apps.inspection.audit.views import (  # noqa: E402
    AuditPlanAdditionalView,
    AuditPlanCancelView,
    AuditPlanDetailView,
    AuditPlanExtensionDecideView,
    AuditPlanExtensionRequestView,
    AuditPlanFlagNotifyView,
    AuditPlanListCreateView,
    AuditVesselOptionListView,
)
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402


SCHEMA_MODELS = [Inspection, MasterAuditPlan, MasterAuditQualifiedAuditor]


def make_user(
    *,
    role: str = RoleCodes.OFFICE_SSQE,
    user_type: str = "OFFICE",
    user_id: str = "seq-1",
    process_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        process_ids=process_ids or [],
        display_name="SEQ Manager",
        username="seq_manager",
        is_authenticated=True,
    )


class RecordingCursor:
    def __init__(self):
        self.sql = ""
        self.params = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=None):
        self.sql = sql
        self.params = list(params or [])


class RecordingConnection:
    vendor = "microsoft"

    def __init__(self):
        self.cursor_instance = RecordingCursor()

    def cursor(self):
        return self.cursor_instance


class AuditPlanApiTests(unittest.TestCase):
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
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS VesselData")
            cursor.execute(
                """
                CREATE TABLE VesselData (
                    id TEXT PRIMARY KEY,
                    vesselCode TEXT,
                    vesselName TEXT,
                    is_deleted INTEGER DEFAULT 0
                )
                """
            )

    @classmethod
    def tearDownClass(cls) -> None:
        with connection.schema_editor() as schema_editor:
            for model in reversed(SCHEMA_MODELS):
                schema_editor.delete_model(model)
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS VesselData")
        super().tearDownClass()

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            for model in reversed(SCHEMA_MODELS):
                cursor.execute(f"DELETE FROM {model._meta.db_table}")
            cursor.execute("DELETE FROM VesselData")
        self.factory = APIRequestFactory()
        self.vessel_id = uuid.uuid4()
        MasterAuditQualifiedAuditor.objects.create(
            user_id="lead-1",
            qualification_text="ISM Lead Auditor",
            qualification_date=date(2025, 1, 1),
            expiry_date=date(2027, 1, 1),
            scope_standards_csv="ISM,ISPS,MLC",
            auditor_scope="INTERNAL",
            qualified_for_seq=True,
            created_by="seed",
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO VesselData (id, vesselCode, vesselName, is_deleted) VALUES (%s, %s, %s, 0)",
                [str(self.vessel_id), "EAT", "EAST AYUTTHAYA"],
            )

    def _list_plans(self, user, query: str = ""):
        request = self.factory.get(f"/api/audit/plans/{query}")
        force_authenticate(request, user=user)
        return AuditPlanListCreateView.as_view()(request)

    def _post_plan(self, payload, user):
        request = self.factory.post("/api/audit/plans/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditPlanListCreateView.as_view()(request)

    def _get_plan(self, plan_id, user):
        request = self.factory.get(f"/api/audit/plans/{plan_id}/")
        force_authenticate(request, user=user)
        return AuditPlanDetailView.as_view()(request, id=plan_id)

    def _patch_plan(self, plan_id, payload, user):
        request = self.factory.patch(f"/api/audit/plans/{plan_id}/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditPlanDetailView.as_view()(request, id=plan_id)

    def _post_extension(self, plan_id, payload, user):
        request = self.factory.post(f"/api/audit/plans/{plan_id}/extension/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditPlanExtensionRequestView.as_view()(request, id=plan_id)

    def _post_extension_decision(self, plan_id, payload, user):
        request = self.factory.post(f"/api/audit/plans/{plan_id}/extension/decide/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditPlanExtensionDecideView.as_view()(request, id=plan_id)

    def _post_flag_notify(self, plan_id, payload, user):
        request = self.factory.post(f"/api/audit/plans/{plan_id}/flag-notify/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditPlanFlagNotifyView.as_view()(request, id=plan_id)

    def _post_cancel(self, plan_id, payload, user):
        request = self.factory.post(f"/api/audit/plans/{plan_id}/cancel/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditPlanCancelView.as_view()(request, id=plan_id)

    def _post_additional(self, payload, user):
        request = self.factory.post("/api/audit/plans/additional/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditPlanAdditionalView.as_view()(request)

    def _list_vessels(self, user):
        request = self.factory.get("/api/audit/vessels/")
        force_authenticate(request, user=user)
        return AuditVesselOptionListView.as_view()(request)

    def _valid_payload(self):
        return {
            "target_vessel_id": str(self.vessel_id),
            "target_office_dept": "",
            "audit_classification": "INTERNAL",
            "audit_standards_csv": "ISM,ISPS,MLC",
            "lead_auditor_user_id": "lead-1",
            "planned_window_start": "2026-05-01",
            "planned_window_end": "2026-09-01",
            "status": "PLANNED",
        }

    def test_create_routine_vessel_plan_and_list_register_rows(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001])

        with patch(
            "apps.inspection.audit.services.auditor_selection.resolve_user_identity",
            return_value={
                "name": "Capt. Harman Sandhu",
                "designation": "SEQ Manager",
                "company": "KSM",
                "source": "OFFICE",
            },
        ):
            create_response = self._post_plan(self._valid_payload(), user)
            list_response = self._list_plans(user)

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(MasterAuditPlan.objects.count(), 1)
        plan = MasterAuditPlan.objects.get()
        self.assertEqual(plan.target_vessel_id, self.vessel_id)
        self.assertEqual(plan.audit_standards_csv, "ISM,ISPS,MLC")
        self.assertFalse(plan.is_additional)
        self.assertEqual(plan.created_by, "seq-1")
        self.assertEqual(create_response.data["data"]["status"], "PLANNED")
        self.assertEqual(create_response.data["data"]["target_label"], "EAT - EAST AYUTTHAYA")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["data"]["count"], 1)
        self.assertEqual(list_response.data["data"]["results"][0]["id"], str(plan.id))
        self.assertEqual(list_response.data["data"]["results"][0]["target_label"], "EAT - EAST AYUTTHAYA")
        self.assertEqual(list_response.data["data"]["results"][0]["window_label"], "2026-05-01 -> 2026-09-01")
        self.assertEqual(list_response.data["data"]["results"][0]["lead_auditor_name"], "Capt. Harman Sandhu")
        self.assertEqual(list_response.data["data"]["results"][0]["lead_auditor_designation"], "SEQ Manager")
        self.assertEqual(list_response.data["data"]["results"][0]["lead_auditor_company"], "KSM")
        self.assertEqual(list_response.data["data"]["results"][0]["lead_auditor_qual"], "ISM Lead Auditor")

    def test_plan_lead_auditor_snapshot_does_not_use_scope_as_designation(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001])

        with patch(
            "apps.inspection.audit.services.auditor_selection.resolve_user_identity",
            return_value={
                "name": "Capt. Harman Sandhu",
                "designation": "",
                "company": "KSM",
                "source": "OFFICE",
            },
        ):
            response = self._post_plan(self._valid_payload(), user)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["lead_auditor_name"], "Capt. Harman Sandhu")
        self.assertEqual(response.data["data"]["lead_auditor_designation"], "")

    def test_confirmed_plan_requires_qualified_lead_auditor(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001])
        payload = self._valid_payload()
        payload["status"] = "CONFIRMED"
        payload["lead_auditor_user_id"] = ""

        response = self._post_plan(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("lead_auditor_user_id", response.data)
        self.assertEqual(MasterAuditPlan.objects.count(), 0)

    def test_vessel_option_endpoint_returns_readable_labels_for_audit_forms(self) -> None:
        user = make_user(role="DPA", process_ids=[AUDIT_P_001])

        response = self._list_vessels(user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["data"],
            [
                {
                    "id": str(self.vessel_id),
                    "vessel_code": "EAT",
                    "vessel_name": "EAST AYUTTHAYA",
                }
            ],
        )

    def test_patch_plan_updates_editable_register_fields(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_002])
        plan = MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            status="PLANNED",
            created_by="seq-1",
        )

        response = self._patch_plan(
            plan.id,
            {
                "audit_standards_csv": "ISM,ISPS",
                "planned_window_start": "2026-05-15",
                "planned_window_end": "2026-09-15",
                "lead_auditor_user_id": "lead-1",
                "status": "CONFIRMED",
            },
            user,
        )

        self.assertEqual(response.status_code, 200)
        plan.refresh_from_db()
        self.assertEqual(plan.audit_standards_csv, "ISM,ISPS")
        self.assertEqual(plan.planned_window_start, date(2026, 5, 15))
        self.assertEqual(plan.planned_window_end, date(2026, 9, 15))
        self.assertEqual(plan.status, "CONFIRMED")
        self.assertEqual(plan.updated_by, "seq-1")
        self.assertIsNotNone(plan.updated_date)

    def test_mssql_plan_lookup_casts_hyphenated_uuid_for_detail_routes(self) -> None:
        plan = MasterAuditPlan(
            id=uuid.UUID("a1170000-0000-0000-0000-000000000001"),
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            status="CONFIRMED",
            created_by="seq-1",
        )

        with (
            patch("apps.inspection.audit.views.plan.connection", SimpleNamespace(vendor="microsoft")),
            patch.object(MasterAuditPlan.objects, "raw", return_value=[plan]) as mock_raw,
        ):
            fetched = plan_views._plan_by_id(plan.id)

        sql, params = mock_raw.call_args.args
        self.assertIs(fetched, plan)
        self.assertIn("CAST(%s AS uniqueidentifier)", sql)
        self.assertEqual(params, [str(plan.id)])

    def test_mssql_plan_create_casts_uuid_insert_fields(self) -> None:
        recording_connection = RecordingConnection()
        expected_plan = MasterAuditPlan(
            id=uuid.UUID("a1170000-0000-0000-0000-000000000001"),
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            status="CONFIRMED",
            created_by="seq-1",
        )

        with (
            patch("apps.inspection.audit.serializers.plan.connection", recording_connection),
            patch(
                "apps.inspection.audit.serializers.plan._master_audit_plan_column_types",
                return_value={"created_by": "varchar"},
            ),
            patch("apps.inspection.audit.serializers.plan._fetch_sql_server_plan", return_value=expected_plan),
        ):
            created = plan_serializers._create_sql_server_plan(
                {
                    "target_vessel_id": self.vessel_id,
                    "target_office_dept": None,
                    "audit_classification": "INTERNAL",
                    "audit_standards_csv": "ISM",
                    "lead_auditor_user_id": "lead-1",
                    "planned_window_start": date(2026, 5, 1),
                    "planned_window_end": date(2026, 9, 1),
                    "status": "CONFIRMED",
                    "created_by": "seq-1",
                }
            )

        self.assertIs(created, expected_plan)
        self.assertIn("CAST(%s AS uniqueidentifier)", recording_connection.cursor_instance.sql)
        self.assertEqual(recording_connection.cursor_instance.params[1], str(self.vessel_id))
        self.assertIn("seq-1", recording_connection.cursor_instance.params)

    def test_mssql_plan_update_casts_uuid_target_and_where_id(self) -> None:
        recording_connection = RecordingConnection()
        plan = MasterAuditPlan(
            id=uuid.UUID("a1170000-0000-0000-0000-000000000001"),
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM,ISPS",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            status="CONFIRMED",
            updated_by="seq-1",
        )

        with (
            patch("apps.inspection.audit.serializers.plan.connection", recording_connection),
            patch(
                "apps.inspection.audit.serializers.plan._master_audit_plan_column_types",
                return_value={"updated_by": "varchar"},
            ),
            patch("apps.inspection.audit.serializers.plan._fetch_sql_server_plan", return_value=plan),
        ):
            updated = plan_serializers._update_sql_server_plan(
                plan,
                ["updated_by", "target_vessel_id", "status"],
            )

        self.assertIs(updated, plan)
        self.assertIn("target_vessel_id = CAST(%s AS uniqueidentifier)", recording_connection.cursor_instance.sql)
        self.assertIn("WHERE id = CAST(%s AS uniqueidentifier)", recording_connection.cursor_instance.sql)
        self.assertIn(str(self.vessel_id), recording_connection.cursor_instance.params)
        self.assertEqual(recording_connection.cursor_instance.params[-1], str(plan.id))

    @patch("apps.inspection.audit.views.plan._dispatch_plan_notification")
    def test_confirming_plan_dispatches_audit_scheduled_notification(self, mock_dispatch) -> None:
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_002])
        plan = MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            status="PLANNED",
            created_by="seq-1",
            lead_auditor_user_id="lead-1",
        )

        response = self._patch_plan(plan.id, {"status": "CONFIRMED"}, user)

        self.assertEqual(response.status_code, 200)
        mock_dispatch.assert_called_once()
        self.assertEqual(mock_dispatch.call_args.args[0].id, plan.id)
        self.assertEqual(mock_dispatch.call_args.args[1], "AUDIT_SCHEDULED")

    @patch(
        "apps.inspection.audit.views.plan._dispatch_plan_notification",
        side_effect=RuntimeError("notification relay failed"),
    )
    def test_confirmed_plan_create_does_not_rollback_when_notification_dispatch_fails(self, mock_dispatch) -> None:
        user = make_user(process_ids=[AUDIT_P_001])
        payload = self._valid_payload()
        payload["status"] = "CONFIRMED"

        with self.assertLogs("apps.inspection.audit.views.plan", level="ERROR") as logs:
            response = self._post_plan(payload, user)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(MasterAuditPlan.objects.count(), 1)
        plan = MasterAuditPlan.objects.get()
        self.assertEqual(plan.status, "CONFIRMED")
        self.assertEqual(response.data["data"]["id"], str(plan.id))
        mock_dispatch.assert_called_once()
        self.assertIn("Audit plan notification dispatch failed after plan save", logs.output[0])

    @patch(
        "apps.inspection.audit.views.plan._dispatch_plan_notification",
        side_effect=RuntimeError("notification relay failed"),
    )
    def test_confirmed_plan_edit_does_not_rollback_when_notification_dispatch_fails(self, mock_dispatch) -> None:
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_002])
        plan = MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            status="PLANNED",
            created_by="seq-1",
            lead_auditor_user_id="lead-1",
        )

        with self.assertLogs("apps.inspection.audit.views.plan", level="ERROR") as logs:
            response = self._patch_plan(plan.id, {"status": "CONFIRMED"}, user)

        self.assertEqual(response.status_code, 200)
        plan.refresh_from_db()
        self.assertEqual(plan.status, "CONFIRMED")
        self.assertEqual(response.data["data"]["id"], str(plan.id))
        mock_dispatch.assert_called_once()
        self.assertIn("Audit plan notification dispatch failed after plan save", logs.output[0])

    def test_plan_requires_exactly_one_target(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001])
        payload = self._valid_payload()
        payload["target_office_dept"] = "SEQ"

        response = self._post_plan(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("target", str(response.data))
        self.assertEqual(MasterAuditPlan.objects.count(), 0)

    def test_step_8_1_rejects_additional_creation_path(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001])
        payload = self._valid_payload()
        payload["is_additional"] = True
        payload["additional_reason"] = "A" * 60

        response = self._post_plan(payload, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("additional audit", str(response.data).lower())
        self.assertEqual(MasterAuditPlan.objects.count(), 0)

    def test_patch_rejects_cancelled_state_outside_phase_8_3_workflow(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001, AUDIT_P_002])
        plan = MasterAuditPlan.objects.create(
            target_office_dept="SEQ",
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            status="PLANNED",
            created_by="seq-1",
        )

        response = self._patch_plan(plan.id, {"status": "CANCELLED"}, user)

        self.assertEqual(response.status_code, 400)
        plan.refresh_from_db()
        self.assertEqual(plan.status, "PLANNED")

    def test_create_requires_audit_plan_gate_and_office_user(self) -> None:
        no_gate = make_user(role=RoleCodes.PHYSICAL_VERIFIER, user_id="no-gate", process_ids=[])
        vessel_user = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[AUDIT_P_001],
        )

        no_gate_response = self._post_plan(self._valid_payload(), no_gate)
        vessel_response = self._post_plan(self._valid_payload(), vessel_user)

        self.assertEqual(no_gate_response.status_code, 403)
        self.assertEqual(vessel_response.status_code, 403)
        self.assertEqual(MasterAuditPlan.objects.count(), 0)

    def test_get_detail_returns_existing_extension_and_additional_fields_read_only(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001])
        plan = MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            extension_form_ref="OPM-F-713-2026-003",
            is_additional=True,
            additional_reason="DPA authorised additional audit after PSC follow-up.",
            trigger_event_type="PSC_INSPECTION",
            trigger_event_ref="abc123",
            status="EXTENDED",
            created_by="seq-1",
        )

        response = self._get_plan(plan.id, user)

        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["extension_form_ref"], "OPM-F-713-2026-003")
        self.assertTrue(data["is_additional"])
        self.assertEqual(data["trigger_event_type"], "PSC_INSPECTION")

    def test_extension_request_validates_reason_and_three_month_limit(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001])
        plan = MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            status="OVERDUE",
            created_by="seq-1",
        )

        short_reason_response = self._post_extension(
            plan.id,
            {
                "extension_requested_reason": "too short",
                "proposed_new_target_date": "2026-10-01",
            },
            user,
        )
        late_date_response = self._post_extension(
            plan.id,
            {
                "extension_requested_reason": "Delay caused by drydock overrun and auditor availability conflict.",
                "proposed_new_target_date": "2027-01-02",
            },
            user,
        )
        valid_response = self._post_extension(
            plan.id,
            {
                "extension_requested_reason": "Delay caused by drydock overrun and auditor availability conflict.",
                "proposed_new_target_date": "2026-11-30",
            },
            user,
        )

        self.assertEqual(short_reason_response.status_code, 400)
        self.assertEqual(late_date_response.status_code, 400)
        self.assertEqual(valid_response.status_code, 200)
        plan.refresh_from_db()
        self.assertEqual(plan.status, "EXTENSION_REQUESTED")
        self.assertEqual(plan.extended_due_date, date(2026, 11, 30))
        self.assertEqual(plan.extension_requested_by, "seq-1")

    def test_mssql_extension_request_uses_sql_server_safe_update(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001])
        plan = MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            status="OVERDUE",
            created_by="seq-1",
        )

        def fake_update(instance, update_fields):
            self.assertIn("extension_requested_by", update_fields)
            self.assertIn("updated_by", update_fields)
            return instance

        with (
            patch("apps.inspection.audit.services.plan_persistence.connection", SimpleNamespace(vendor="microsoft")),
            patch(
                "apps.inspection.audit.services.plan_persistence._update_sql_server_plan",
                side_effect=fake_update,
            ) as mock_update,
            patch.object(MasterAuditPlan, "save", side_effect=AssertionError("direct save should not run")),
        ):
            response = self._post_extension(
                plan.id,
                {
                    "extension_requested_reason": "Delay caused by drydock overrun and auditor availability conflict.",
                    "proposed_new_target_date": "2026-11-30",
                },
                user,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["status"], "EXTENSION_REQUESTED")
        mock_update.assert_called_once()

    @patch("apps.inspection.audit.views.plan._dispatch_plan_notification")
    def test_mssql_plan_workflow_followups_use_sql_server_safe_update(self, mock_dispatch) -> None:
        dpa_user = make_user(role="DPA", user_id="dpa-1", process_ids=[AUDIT_P_005, AUDIT_P_006])
        extension_plan = MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            extended_due_date=date(2026, 11, 30),
            extension_requested_reason="Delay caused by drydock overrun and auditor availability conflict.",
            status="EXTENSION_REQUESTED",
            created_by="seq-1",
        )
        flag_plan = MasterAuditPlan.objects.create(
            target_vessel_id=uuid.uuid4(),
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            extended_due_date=date(2026, 11, 30),
            status="EXTENDED",
            created_by="seq-1",
        )
        cancel_plan = MasterAuditPlan.objects.create(
            target_office_dept="SEQ",
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            status="OVERDUE",
            created_by="seq-1",
        )
        MasterAuditPlan.objects.create(
            target_office_dept="SEQ",
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 9, 16),
            planned_window_end=date(2026, 12, 15),
            status="PLANNED",
            created_by="dpa-1",
        )

        def fake_update(instance, update_fields):
            self.assertIn("updated_by", update_fields)
            return instance

        with (
            patch("apps.inspection.audit.services.plan_persistence.connection", SimpleNamespace(vendor="microsoft")),
            patch(
                "apps.inspection.audit.services.plan_persistence._update_sql_server_plan",
                side_effect=fake_update,
            ) as mock_update,
            patch.object(MasterAuditPlan, "save", side_effect=AssertionError("direct save should not run")),
        ):
            approve_response = self._post_extension_decision(
                extension_plan.id,
                {
                    "decision": "APPROVE",
                    "extension_approved_reason": "DPA reviewed the drydock evidence and accepts the proposed date.",
                },
                dpa_user,
            )
            flag_response = self._post_flag_notify(
                flag_plan.id,
                {
                    "flag_notification_date": "2026-09-10",
                    "flag_notification_ref": "FLAG-EXT-2026-09",
                    "flag_notification_attachment": "attachments/flag-extension.pdf",
                },
                dpa_user,
            )
            cancel_response = self._post_cancel(
                cancel_plan.id,
                {
                    "cancellation_reason": "Vessel entered extended repair and DPA authorised full replanning.",
                    "next_planned_date": "2026-12-15",
                    "today": "2026-09-01",
                },
                dpa_user,
            )

        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(flag_response.status_code, 200)
        self.assertEqual(cancel_response.status_code, 200)
        self.assertEqual(mock_update.call_count, 3)
        mock_dispatch.assert_any_call(extension_plan, "AUDIT_EXTENSION_APPROVED")
        mock_dispatch.assert_any_call(cancel_plan, "AUDIT_CANCELLED")

    @patch("apps.inspection.audit.views.plan._dispatch_plan_notification")
    def test_dpa_approves_and_rejects_extension_with_opm_numbering(self, mock_dispatch) -> None:
        seq_user = make_user(process_ids=[AUDIT_P_001])
        dpa_user = make_user(role="DPA", user_id="dpa-1", process_ids=[AUDIT_P_005])
        existing = MasterAuditPlan.objects.create(
            target_office_dept="SEQ",
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 1, 1),
            planned_window_end=date(2026, 5, 1),
            status="EXTENDED",
            extension_form_ref="OPM-F-713-2026-004",
            created_by="seq-1",
        )
        plan = MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            extended_due_date=date(2026, 11, 30),
            extension_requested_reason="Delay caused by drydock overrun and auditor availability conflict.",
            status="EXTENSION_REQUESTED",
            created_by="seq-1",
        )
        reject_plan = MasterAuditPlan.objects.create(
            target_vessel_id=uuid.uuid4(),
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 6, 1),
            planned_window_end=date(2026, 10, 1),
            extended_due_date=date(2026, 12, 1),
            extension_requested_reason="Delay caused by drydock overrun and auditor availability conflict.",
            status="EXTENSION_REQUESTED",
            created_by="seq-1",
        )

        no_gate_response = self._post_extension_decision(plan.id, {"decision": "APPROVE"}, seq_user)
        approve_response = self._post_extension_decision(
            plan.id,
            {
                "decision": "APPROVE",
                "extension_approved_reason": "DPA reviewed the drydock evidence and accepts the proposed date.",
            },
            dpa_user,
        )
        reject_response = self._post_extension_decision(
            reject_plan.id,
            {
                "decision": "REJECT",
                "extension_approved_reason": "DPA requires the audit to remain inside the active window.",
            },
            dpa_user,
        )

        self.assertEqual(no_gate_response.status_code, 403)
        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(reject_response.status_code, 200)
        plan.refresh_from_db()
        reject_plan.refresh_from_db()
        self.assertEqual(existing.extension_form_ref, "OPM-F-713-2026-004")
        self.assertEqual(plan.status, "EXTENDED")
        self.assertEqual(plan.extension_form_ref, "OPM-F-713-2026-005")
        self.assertEqual(plan.extension_approved_by, "dpa-1")
        self.assertEqual(reject_plan.status, "OVERDUE")
        self.assertIsNone(reject_plan.extension_form_ref)
        mock_dispatch.assert_called_once()
        self.assertEqual(mock_dispatch.call_args.args[0].id, plan.id)
        self.assertEqual(mock_dispatch.call_args.args[1], "AUDIT_EXTENSION_APPROVED")

    def test_flag_notification_capture_updates_plan(self) -> None:
        dpa_user = make_user(role="DPA", user_id="dpa-1", process_ids=[AUDIT_P_005])
        plan = MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            extended_due_date=date(2026, 11, 30),
            status="EXTENDED",
            created_by="seq-1",
        )

        response = self._post_flag_notify(
            plan.id,
            {
                "flag_notification_date": "2026-09-10",
                "flag_notification_ref": "FLAG-EXT-2026-09",
                "flag_notification_attachment": "attachments/flag-extension.pdf",
            },
            dpa_user,
        )

        self.assertEqual(response.status_code, 200)
        plan.refresh_from_db()
        self.assertTrue(plan.flag_notified)
        self.assertEqual(plan.flag_notification_date, date(2026, 9, 10))
        self.assertEqual(plan.flag_notification_ref, "FLAG-EXT-2026-09")

    @patch("apps.inspection.audit.views.plan._dispatch_plan_notification")
    def test_dpa_cancels_plan_and_auto_creates_replacement(self, mock_dispatch) -> None:
        dpa_user = make_user(role="DPA", user_id="dpa-1", process_ids=[AUDIT_P_006])
        plan = MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM,MLC",
            planned_window_start=date(2026, 5, 1),
            planned_window_end=date(2026, 9, 1),
            status="OVERDUE",
            created_by="seq-1",
        )

        invalid_response = self._post_cancel(
            plan.id,
            {
                "cancellation_reason": "too short",
                "next_planned_date": "2026-09-20",
                "today": "2026-09-01",
            },
            dpa_user,
        )
        valid_response = self._post_cancel(
            plan.id,
            {
                "cancellation_reason": "Vessel entered extended repair and DPA authorised full replanning.",
                "next_planned_date": "2026-12-15",
                "today": "2026-09-01",
            },
            dpa_user,
        )
        repeat_response = self._post_cancel(
            plan.id,
            {
                "cancellation_reason": "Vessel entered extended repair and DPA authorised full replanning.",
                "next_planned_date": "2026-12-15",
                "today": "2026-09-01",
            },
            dpa_user,
        )
        patch_response = self._patch_plan(plan.id, {"status": "CONFIRMED"}, dpa_user)

        self.assertEqual(invalid_response.status_code, 400)
        self.assertEqual(valid_response.status_code, 200)
        self.assertEqual(repeat_response.status_code, 200)
        self.assertEqual(patch_response.status_code, 400)
        plan.refresh_from_db()
        replacement = MasterAuditPlan.objects.exclude(id=plan.id).get()
        self.assertEqual(plan.status, "CANCELLED")
        self.assertEqual(plan.cancelled_by, "dpa-1")
        self.assertEqual(replacement.status, "PLANNED")
        self.assertEqual(replacement.planned_window_end, date(2026, 12, 15))
        self.assertEqual(MasterAuditPlan.objects.count(), 2)
        mock_dispatch.assert_called_once()
        self.assertEqual(mock_dispatch.call_args.args[0].id, plan.id)
        self.assertEqual(mock_dispatch.call_args.args[1], "AUDIT_CANCELLED")

    def test_create_additional_audit_is_dpa_only_and_excluded_from_ladder(self) -> None:
        seq_user = make_user(process_ids=[AUDIT_P_001])
        dpa_user = make_user(role="DPA", user_id="dpa-1", process_ids=[AUDIT_P_001])
        psc = Inspection.objects.create(
            vessel_id=self.vessel_id,
            inspection_type="PSC",
            psc_subtype="INITIAL",
            inspection_date=date(2026, 8, 1),
            port_place="Singapore",
            created_by="psc",
        )
        payload = {
            "target_vessel_id": str(self.vessel_id),
            "audit_classification": "INTERNAL",
            "audit_standards_csv": "ISM",
            "planned_window_start": "2026-09-01",
            "planned_window_end": "2026-09-10",
            "additional_reason": "DPA authorised additional audit after a PSC follow-up concern.",
            "trigger_event_type": "PSC_INSPECTION",
            "trigger_event_ref": str(psc.id),
        }

        seq_response = self._post_additional(payload, seq_user)
        dpa_response = self._post_additional(payload, dpa_user)

        self.assertEqual(seq_response.status_code, 403)
        self.assertEqual(dpa_response.status_code, 201)
        plan = MasterAuditPlan.objects.get()
        self.assertTrue(plan.is_additional)
        self.assertEqual(plan.trigger_event_type, "PSC_INSPECTION")
        self.assertEqual(plan.trigger_event_ref, str(psc.id))

    def test_additional_audit_validates_psc_and_flag_letter_trigger_evidence(self) -> None:
        dpa_user = make_user(role="DPA", user_id="dpa-1", process_ids=[AUDIT_P_001])
        base_payload = {
            "target_vessel_id": str(self.vessel_id),
            "audit_classification": "INTERNAL",
            "audit_standards_csv": "ISM",
            "planned_window_start": "2026-09-01",
            "planned_window_end": "2026-09-10",
            "additional_reason": "DPA authorised additional audit after an external trigger event.",
        }

        missing_psc_response = self._post_additional(
            {
                **base_payload,
                "trigger_event_type": "PSC_INSPECTION",
                "trigger_event_ref": str(uuid.uuid4()),
            },
            dpa_user,
        )
        missing_evidence_response = self._post_additional(
            {
                **base_payload,
                "trigger_event_type": "FLAG_LETTER",
                "trigger_event_ref": "",
            },
            dpa_user,
        )
        flag_response = self._post_additional(
            {
                **base_payload,
                "trigger_event_type": "FLAG_LETTER",
                "trigger_event_ref": "FLAG-LETTER-2026-09-10;TRIGGER_EVIDENCE=attachment-123",
            },
            dpa_user,
        )

        self.assertEqual(missing_psc_response.status_code, 400)
        self.assertEqual(missing_evidence_response.status_code, 400)
        self.assertEqual(flag_response.status_code, 201)
        self.assertEqual(MasterAuditPlan.objects.count(), 1)

    @patch("apps.inspection.audit.services.additional_audit._safety_incident_exists")
    def test_additional_audit_validates_safety_incident_trigger_reference(self, mock_incident_exists) -> None:
        dpa_user = make_user(role="DPA", user_id="dpa-1", process_ids=[AUDIT_P_001])
        missing_incident_id = uuid.uuid4()
        incident_id = uuid.uuid4()
        mock_incident_exists.side_effect = lambda candidate: candidate == incident_id
        base_payload = {
            "target_vessel_id": str(self.vessel_id),
            "audit_classification": "INTERNAL",
            "audit_standards_csv": "ISM",
            "planned_window_start": "2026-09-01",
            "planned_window_end": "2026-09-10",
            "additional_reason": "DPA authorised additional audit after a Safety incident follow-up.",
            "trigger_event_type": "INCIDENT_REPORT",
        }

        malformed_response = self._post_additional({**base_payload, "trigger_event_ref": "not-a-uuid"}, dpa_user)
        missing_response = self._post_additional({**base_payload, "trigger_event_ref": str(missing_incident_id)}, dpa_user)
        valid_response = self._post_additional({**base_payload, "trigger_event_ref": str(incident_id)}, dpa_user)

        self.assertEqual(malformed_response.status_code, 400)
        self.assertEqual(missing_response.status_code, 400)
        self.assertEqual(valid_response.status_code, 201)
        plan = MasterAuditPlan.objects.get()
        self.assertEqual(plan.trigger_event_type, "INCIDENT_REPORT")
        self.assertEqual(plan.trigger_event_ref, str(incident_id))
        self.assertEqual(mock_incident_exists.call_count, 2)


if __name__ == "__main__":
    unittest.main()
