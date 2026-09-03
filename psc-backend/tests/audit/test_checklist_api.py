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
            SECRET_KEY="audit-checklist-test-secret-key-1234567890",
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
    AuditDetail,
    MasterAuditChecklist,
    MasterAuditChecklistItem,
)
from apps.inspection.audit.permissions import AUDIT_P_001, AUDIT_P_003  # noqa: E402
from apps.inspection.audit.services.checklist import checklist_items_for  # noqa: E402
from apps.inspection.audit.views import AuditChecklistMasterView  # noqa: E402
from apps.inspection.models import Inspection  # noqa: E402
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402


SCHEMA_MODELS = [
    Inspection,
    AuditDetail,
    MasterAuditChecklist,
    MasterAuditChecklistItem,
]


def make_user(
    *,
    role: str = RoleCodes.OFFICE_SSQE,
    user_type: str = "OFFICE",
    user_id: str = "auditor-1",
    process_ids: list[str] | None = None,
    vessel_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        process_ids=process_ids or [],
        vessel_ids=vessel_ids or [],
        display_name="Audit User",
        username="audit_user",
        is_authenticated=True,
    )


class AuditChecklistApiTests(unittest.TestCase):
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
        self.inspection = Inspection.objects.create(
            vessel_id=self.vessel_id,
            inspection_type="AUDIT",
            inspection_date=date(2026, 8, 5),
            port_place="Singapore",
            country="Singapore",
            inspector_name="Lead Auditor",
            report_reference="F605-2026-001",
            created_by="auditor-1",
        )
        self.audit_detail = AuditDetail.objects.create(
            psc_inspection_id=self.inspection.id.hex,
            vessel_id=self.vessel_id.hex,
            audit_classification="INTERNAL",
            auditee_type="VESSEL",
            audit_subtype="ANNUAL_INTERNAL",
            lead_auditor_name="Lead Auditor",
            lead_auditor_company="KSM",
            conductor_user_id="conductor-1",
            trigger_reason="SCHEDULED",
            audit_start_date=date(2026, 8, 5),
            status="IN_PROGRESS",
            created_by="auditor-1",
        )
        self.f605 = MasterAuditChecklist.objects.create(
            checklist_code="F605",
            name="Vessel Internal Audit Checklist",
            auditee_type="VESSEL",
            ship_type_scope="Common",
            source_form_ref="F 605",
            code_version="SSQE Rev 01 Feb 2026",
            is_active=True,
            created_by="auditor-1",
        )
        MasterAuditChecklistItem.objects.create(
            master_audit_checklist_id=self.f605.id,
            location_code="BRIDGE",
            item_code="001",
            question="Bridge procedures verified?",
            ship_type="Common",
            sequence_no=2,
            created_by="auditor-1",
        )
        MasterAuditChecklistItem.objects.create(
            master_audit_checklist_id=self.f605.id,
            location_code="CARGO",
            item_code="002",
            question="Bulk cargo procedure verified?",
            ship_type="Bulk Carrier",
            sequence_no=1,
            created_by="auditor-1",
        )
        MasterAuditChecklistItem.objects.create(
            master_audit_checklist_id=self.f605.id,
            location_code="OTHER",
            item_code="003",
            question="Other ship-type procedure verified?",
            ship_type="Others",
            sequence_no=3,
            created_by="auditor-1",
        )

    def _get_checklist(self, user, *, audit_id=None, ship_type=None):
        query = {"audit_id": str(audit_id or self.audit_detail.id)}
        if ship_type:
            query["ship_type"] = ship_type
        request = self.factory.get("/api/audit/masters/checklists/", query)
        force_authenticate(request, user=user)
        return AuditChecklistMasterView.as_view()(request)

    def test_vessel_audit_returns_f605_items_in_seed_order_without_invented_ship_filter(self) -> None:
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._get_checklist(user)

        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertTrue(data["selected"])
        self.assertEqual(data["checklist"]["checklist_code"], "F605")
        self.assertIsNone(data["ship_type_filter"])
        self.assertFalse(data["item_filter_applied"])
        self.assertEqual([item["item_code"] for item in data["items"]], ["002", "001", "003"])

    def test_assigned_conductor_can_open_checklist_without_profile_wide_audit_gate(self) -> None:
        user = make_user(user_id="conductor-1", role="Conductor", process_ids=[], vessel_ids=[])

        response = self._get_checklist(user)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["selected"])

    def test_vessel_audit_can_apply_explicit_ship_type_item_filter(self) -> None:
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._get_checklist(user, ship_type="Bulk Carrier")

        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["ship_type_filter"], "Bulk Carrier")
        self.assertTrue(data["item_filter_applied"])
        self.assertEqual([item["item_code"] for item in data["items"]], ["002", "001"])

    def test_office_department_audit_returns_matching_f606_checklist(self) -> None:
        office_audit = AuditDetail.objects.create(
            psc_inspection_id=uuid.uuid4().hex,
            audit_classification="INTERNAL",
            auditee_type="OFFICE_DEPT",
            auditee_office_dept="TECH",
            audit_subtype="OFFICE_INTERNAL",
            lead_auditor_name="Lead Auditor",
            lead_auditor_company="KSM",
            trigger_reason="SCHEDULED",
            audit_start_date=date(2026, 8, 5),
            status="IN_PROGRESS",
            created_by="auditor-1",
        )
        f606 = MasterAuditChecklist.objects.create(
            checklist_code="F606_TECH",
            name="Office Internal Audit Checklist - TECH Department",
            auditee_type="OFFICE_DEPT",
            scope_dept="TECH",
            source_form_ref="F 606",
            code_version="SSQE Rev 01 Feb 2026",
            is_active=True,
            created_by="auditor-1",
        )
        MasterAuditChecklistItem.objects.create(
            master_audit_checklist_id=f606.id,
            location_code="TECH",
            item_code="010",
            question="Technical records verified?",
            sequence_no=10,
            created_by="auditor-1",
        )
        user = make_user(process_ids=[AUDIT_P_001])

        response = self._get_checklist(user, audit_id=office_audit.id)

        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["checklist"]["checklist_code"], "F606_TECH")
        self.assertEqual(data["items"][0]["question"], "Technical records verified?")

    def test_no_matching_checklist_returns_empty_success_state(self) -> None:
        office_audit = AuditDetail.objects.create(
            psc_inspection_id=uuid.uuid4().hex,
            audit_classification="INTERNAL",
            auditee_type="OFFICE_DEPT",
            auditee_office_dept="SQA",
            audit_subtype="OFFICE_INTERNAL",
            lead_auditor_name="Lead Auditor",
            lead_auditor_company="KSM",
            trigger_reason="SCHEDULED",
            audit_start_date=date(2026, 8, 5),
            status="IN_PROGRESS",
            created_by="auditor-1",
        )
        user = make_user(process_ids=[AUDIT_P_001])

        response = self._get_checklist(user, audit_id=office_audit.id)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["selected"])
        self.assertEqual(response.data["data"]["items"], [])

    def test_checklist_read_requires_audit_scope_access(self) -> None:
        user = make_user(process_ids=[])

        response = self._get_checklist(user)

        self.assertEqual(response.status_code, 403)

    def test_sql_server_checklist_lookup_casts_audit_id(self) -> None:
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])
        unsafe_get = AssertionError("Checklist audit lookup must cast route/query UUIDs on SQL Server.")

        with (
            patch(
                "apps.inspection.audit.services.detail.connection",
                SimpleNamespace(vendor="microsoft"),
            ),
            patch.object(AuditDetail.objects, "get", side_effect=unsafe_get),
            patch.object(AuditDetail.objects, "raw", return_value=[self.audit_detail]) as raw,
        ):
            response = self._get_checklist(user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(raw.call_count, 2)
        for call in raw.call_args_list:
            sql, params = call.args
            self.assertIn("FROM dbo.audit_detail", sql)
            self.assertIn("id = CAST(%s AS uniqueidentifier)", sql)
            self.assertEqual(params, [str(self.audit_detail.id)])

    def test_sql_server_checklist_item_lookup_casts_checklist_id(self) -> None:
        unsafe_filter = AssertionError("Checklist item lookup must cast checklist UUIDs on SQL Server.")
        raw_calls = []

        def raw_items(sql, params=None):
            raw_calls.append((sql, params or []))
            return []

        with (
            patch(
                "apps.inspection.audit.services.checklist.connection",
                SimpleNamespace(vendor="microsoft"),
            ),
            patch.object(MasterAuditChecklistItem.objects, "filter", side_effect=unsafe_filter),
            patch.object(MasterAuditChecklistItem.objects, "raw", side_effect=raw_items),
        ):
            items = checklist_items_for(self.f605, ship_type="Bulk Carrier")

        self.assertEqual(items, [])
        self.assertEqual(len(raw_calls), 1)
        sql, params = raw_calls[0]
        self.assertIn("FROM dbo.master_audit_checklist_item", sql)
        self.assertIn("master_audit_checklist_id = CAST(%s AS uniqueidentifier)", sql)
        self.assertEqual(params, [str(self.f605.id), "Common", "Bulk Carrier"])


if __name__ == "__main__":
    unittest.main()
