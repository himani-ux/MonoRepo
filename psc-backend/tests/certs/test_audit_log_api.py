from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch
import uuid

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.backends import AuthenticatedUser
from apps.certs.services.audit_log_repository import AuditLogRepository
from apps.certs.views.audit_views import AuditLogDetailView, AuditLogExportView, AuditLogListView


def make_user(
    *,
    role: str,
    form_ids: list[str] | None = None,
    process_ids: list[str] | None = None,
    vessel_ids: list[str] | None = None,
    user_type: str = "OFFICE",
) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=f"{role.lower().replace(' ', '-')}-1",
        user_type=user_type,
        full_name=f"{role} User",
        role=role,
        employee_id=f"{role[:3].upper()}001",
        form_ids=form_ids or [],
        process_ids=process_ids or [],
        vessel_ids=vessel_ids or [],
    )


def audit_event(**overrides):
    event = {
        "audit_id": uuid.uuid4(),
        "timestamp_utc": "2026-06-29T08:30:00Z",
        "vessel_id": uuid.uuid4(),
        "actor_user_id": "dpa-1",
        "actor_role": "DPA",
        "action": "update_tracked_item",
        "entity_type": "tracked_item",
        "entity_id": str(uuid.uuid4()),
        "before_json": '{"status": "current"}',
        "after_json": '{"status": "window_open"}',
        "reason": "Annual survey window opened.",
        "event_metadata": '{"source": "api.certs.tracked_items"}',
        "retention_tier": "hot",
        "archived_at": None,
        "schema_version": 1,
    }
    event.update(overrides)
    return event


class CertAuditLogApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.dpa = make_user(role="DPA", form_ids=["CERT_F_008"])
        self.dpa_exporter = make_user(role="DPA", form_ids=["CERT_F_008"], process_ids=["CERT_P_005"])
        self.fm_exporter = make_user(role="Fleet Manager", form_ids=["CERT_F_008"], process_ids=["CERT_P_005"])
        self.fm = make_user(role="Fleet Manager", form_ids=["CERT_F_008"])
        self.marine_supt = make_user(role="Marine Sup'tt", form_ids=["CERT_F_008"], vessel_ids=["vessel-a"])
        self.tracked_item_reader = make_user(role="Fleet Manager", form_ids=["CERT_F_002"])
        self.external_auditor = make_user(role="External Auditor", form_ids=["CERT_F_008"], user_type="EXTERNAL_AUDITOR")

    @patch("apps.certs.views.audit_views.repository")
    def test_dpa_lists_full_fleet_audit_log_with_field_map_keys(self, repository) -> None:
        repository.list_events.return_value = MagicMock(
            count=1,
            page=1,
            page_size=25,
            includes_cold_tier=False,
            results=[audit_event(vessel_id=None)],
        )
        request = self.factory.get("/api/certs/audit-log/?action=update_tracked_item&pageSize=99")
        force_authenticate(request, user=self.dpa)

        response = AuditLogListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["pageSize"], 25)
        self.assertEqual(response.data["results"][0]["action"], "update_tracked_item")
        self.assertEqual(response.data["results"][0]["before"]["status"], "current")
        self.assertEqual(response.data["results"][0]["eventMetadata"]["source"], "api.certs.tracked_items")
        repository.list_events.assert_called_once()
        self.assertIsNone(repository.list_events.call_args.kwargs["vessel_scope"])

    @patch("apps.certs.views.audit_views.repository")
    def test_fm_lists_full_fleet_audit_log(self, repository) -> None:
        repository.list_events.return_value = MagicMock(
            count=0,
            page=1,
            page_size=25,
            includes_cold_tier=False,
            results=[],
        )
        request = self.factory.get("/api/certs/audit-log/")
        force_authenticate(request, user=self.fm)

        response = AuditLogListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(repository.list_events.call_args.kwargs["vessel_scope"])

    @patch("apps.certs.views.audit_views.repository")
    def test_supt_audit_log_is_scoped_to_assigned_vessels(self, repository) -> None:
        repository.list_events.return_value = MagicMock(
            count=1,
            page=1,
            page_size=25,
            includes_cold_tier=False,
            results=[audit_event(vessel_id="vessel-a")],
        )
        request = self.factory.get("/api/certs/audit-log/")
        force_authenticate(request, user=self.marine_supt)

        response = AuditLogListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(repository.list_events.call_args.kwargs["vessel_scope"], ["vessel-a"])

    @patch("apps.certs.views.audit_views.repository")
    def test_audit_log_requires_cert_audit_form_and_blocks_external_auditor(self, repository) -> None:
        for user in (self.tracked_item_reader, self.external_auditor):
            with self.subTest(role=user.role):
                request = self.factory.get("/api/certs/audit-log/")
                force_authenticate(request, user=user)

                response = AuditLogListView.as_view()(request)

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.list_events.assert_not_called()

    @patch("apps.certs.views.audit_views.repository")
    def test_detail_returns_404_when_event_is_outside_scope(self, repository) -> None:
        audit_id = uuid.uuid4()
        repository.get_event.return_value = None
        request = self.factory.get(f"/api/certs/audit-log/{audit_id}/")
        force_authenticate(request, user=self.marine_supt)

        response = AuditLogDetailView.as_view()(request, audit_id=audit_id)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        repository.get_event.assert_called_once_with(str(audit_id), vessel_scope=["vessel-a"])

    @patch("apps.certs.services.audit_log_repository.connection")
    def test_repository_applies_scope_filters_and_server_side_pagination(self, connection) -> None:
        cursor = MagicMock()
        cursor.description = [("audit_id",), ("retention_tier",)]
        cursor.fetchone.return_value = (1,)
        cursor.fetchall.return_value = [(uuid.uuid4(), "cold")]
        connection.cursor.return_value.__enter__.return_value = cursor

        page = AuditLogRepository().list_events(
            filters={"action": "print", "retentionTier": "cold", "page": 2, "pageSize": 100},
            vessel_scope=["vessel-a", "vessel-b"],
        )

        self.assertEqual(page.count, 1)
        self.assertEqual(page.page, 2)
        self.assertEqual(page.page_size, 25)
        self.assertTrue(page.includes_cold_tier)
        executed_sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
        self.assertIn("vessel_id IN (%s, %s)", executed_sql)
        self.assertIn("retention_tier = %s", executed_sql)
        self.assertIn("OFFSET %s ROWS FETCH NEXT %s ROWS ONLY", executed_sql)

    @patch("apps.certs.views.audit_views.record_audit_event")
    @patch("apps.certs.views.audit_views.export_service")
    def test_dpa_exports_filtered_audit_log_as_watermarked_artifact(self, export_service, record_audit_event) -> None:
        export_service.export.return_value = {
            "print_id": "SQE-S633-FLEET-20260630-001",
            "scope": "audit_log_export",
            "vessels_json": '["vessel-a"]',
            "sections_json": "[]",
            "filters_json": '{"action": "update_tracked_item"}',
            "custom_cert_ids_json": "[]",
            "user_id": "dpa-1",
            "user_role": "DPA",
            "timestamp_utc": "2026-06-30T05:00:00Z",
            "system_state_hash": "A1B2C3D4",
            "watermark_applied": "INTERNAL",
            "watermark_recipient": "DPA audit export",
            "pdf_blob_id": "pdf-blob",
            "excel_blob_id": "csv-blob",
            "bundle_zip_blob_id": None,
            "recipient_email": "",
            "page_count": 1,
            "generation_status": "success",
            "failure_message": "",
        }
        request = self.factory.post(
            "/api/certs/audit-log/export/",
            {"filters": {"action": "update_tracked_item", "vesselId": "vessel-a"}},
            format="json",
        )
        force_authenticate(request, user=self.dpa_exporter)

        response = AuditLogExportView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["printId"], "SQE-S633-FLEET-20260630-001")
        self.assertEqual(response.data["scope"], "audit_log_export")
        self.assertEqual(response.data["watermarkApplied"], "INTERNAL")
        self.assertEqual(response.data["pdfBlobId"], "pdf-blob")
        self.assertEqual(response.data["excelBlobId"], "csv-blob")
        export_service.export.assert_called_once_with(
            filters={"action": "update_tracked_item", "vesselId": "vessel-a"},
            actor=self.dpa_exporter,
        )
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "print")
        self.assertEqual(record_audit_event.call_args.kwargs["entity_type"], "print_artifact")
        self.assertEqual(record_audit_event.call_args.kwargs["entity_id"], "SQE-S633-FLEET-20260630-001")
        self.assertEqual(record_audit_event.call_args.kwargs["metadata"]["source"], "api.certs.audit_log.export")

    @patch("apps.certs.views.audit_views.export_service")
    def test_audit_export_is_dpa_only_and_requires_print_process(self, export_service) -> None:
        for user in (self.dpa, self.fm_exporter):
            with self.subTest(role=user.role, process_ids=user.process_ids):
                request = self.factory.post("/api/certs/audit-log/export/", {"filters": {}}, format="json")
                force_authenticate(request, user=user)

                response = AuditLogExportView.as_view()(request)

                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        export_service.export.assert_not_called()

    @patch("apps.certs.services.audit_log_repository.connection")
    def test_repository_exports_filtered_rows_without_page_size_cap(self, connection) -> None:
        cursor = MagicMock()
        cursor.description = [("audit_id",), ("action",), ("retention_tier",)]
        cursor.fetchall.return_value = [(uuid.uuid4(), "update_tracked_item", "hot")]
        connection.cursor.return_value.__enter__.return_value = cursor

        rows = AuditLogRepository().export_events(
            filters={"action": "update_tracked_item", "vesselId": "vessel-a"},
            vessel_scope=None,
        )

        self.assertEqual(rows[0]["action"], "update_tracked_item")
        executed_sql = cursor.execute.call_args.args[0]
        self.assertIn("FROM dbo.vims_certs_audit_log", executed_sql)
        self.assertIn("action = %s", executed_sql)
        self.assertIn("vessel_id = %s", executed_sql)
        self.assertIn("FETCH NEXT 5000 ROWS ONLY", executed_sql)
