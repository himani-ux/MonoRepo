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

from apps.certs.services.vessel_lifecycle import VesselLifecycleRepository
from apps.certs.views.vessel_lifecycle_views import (
    VesselClassChangeView,
    VesselDecommissionView,
    VesselFlagChangeView,
    VesselProfileView,
    VesselSaleHandoverView,
)
from tests.certs.test_tracked_item_api import make_user


def vessel_row(**overrides):
    row = {
        "vessel_id": str(uuid.uuid4()),
        "vessel_code": "KSMF",
        "vessel_name": "KSM Fortitude",
        "imo_number": "9876543",
        "flag": "Panama",
        "class_society": "NK",
    }
    row.update(overrides)
    return row


def config_row(**overrides):
    row = {
        "vessel_id": str(uuid.uuid4()),
        "anniversary_date": "2026-01-15",
        "ship_type": "bulk_carrier",
        "lifecycle_status": "active",
        "pending_disposal_started_at": None,
        "sale_handover_bundle_blob_id": None,
        "flag_change_pending": False,
        "flag_change_event_json": None,
        "class_change_pending": False,
        "mandatory_coverage_override_reason": None,
        "mandatory_coverage_override_at": None,
        "mandatory_coverage_override_by": None,
        "iws_age_gate_disabled": False,
    }
    row.update(overrides)
    return row


def lifecycle_result(**overrides):
    vessel_id = overrides.pop("vessel_id", str(uuid.uuid4()))
    result = {
        "vessel": vessel_row(vessel_id=vessel_id),
        "before": config_row(vessel_id=vessel_id),
        "after": config_row(vessel_id=vessel_id),
        "affected_tracked_items": 3,
        "artifact": None,
    }
    result.update(overrides)
    return result


class VesselLifecycleApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.vessel_id = str(uuid.uuid4())
        self.dpa = make_user(
            role="DPA",
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_008"],
            has_global_vessel_access=True,
        )
        self.fm = make_user(
            role="Fleet Manager",
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_008"],
            has_global_vessel_access=True,
        )
        self.master = make_user(
            role="MASTER",
            user_type="VESSEL",
            vessel_id=self.vessel_id,
            form_ids=["CERT_F_002"],
            process_ids=[],
        )

    @patch("apps.certs.views.vessel_lifecycle_views.repository")
    def test_profile_returns_lifecycle_fields_for_readers(self, repository) -> None:
        repository.get_profile.return_value = lifecycle_result(
            vessel_id=self.vessel_id,
            after=config_row(
                vessel_id=self.vessel_id,
                lifecycle_status="pending_disposal",
                pending_disposal_started_at="2026-06-30T00:00:00Z",
                flag_change_pending=True,
                flag_change_event_json='{"newFlagState":"Liberia"}',
                class_change_pending=True,
            ),
        )
        request = self.factory.get("/api/certs/vessel/9876543/profile/")
        force_authenticate(request, user=self.master)

        response = VesselProfileView.as_view()(request, imo="9876543")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["vessel"]["id"], self.vessel_id)
        self.assertEqual(response.data["config"]["lifecycleStatus"], "pending_disposal")
        self.assertTrue(response.data["config"]["flagChangePending"])
        self.assertTrue(response.data["config"]["classChangePending"])

    @patch("apps.certs.views.vessel_lifecycle_views.record_audit_event")
    @patch("apps.certs.views.vessel_lifecycle_views.repository")
    def test_flag_change_is_dpa_only_and_audits_invalid_reflag(self, repository, record_audit_event) -> None:
        repository.record_flag_change.return_value = lifecycle_result(
            vessel_id=self.vessel_id,
            after=config_row(vessel_id=self.vessel_id, flag_change_pending=True, flag_change_event_json='{"newFlagState":"Liberia"}'),
            affected_tracked_items=5,
        )
        request = self.factory.post(
            "/api/certs/vessel/9876543/flag-change/",
            {
                "newFlagState": "Liberia",
                "effectiveDate": "2026-07-15",
                "reason": "Registered flag state is changing after sale contract review.",
            },
            format="json",
        )
        force_authenticate(request, user=self.fm)

        denied = VesselFlagChangeView.as_view()(request, imo="9876543")

        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        repository.record_flag_change.assert_not_called()

        request = self.factory.post(
            "/api/certs/vessel/9876543/flag-change/",
            {
                "newFlagState": "Liberia",
                "effectiveDate": "2026-07-15",
                "reason": "Registered flag state is changing after sale contract review.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = VesselFlagChangeView.as_view()(request, imo="9876543")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["affectedTrackedItems"], 5)
        repository.record_flag_change.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "flag_change_event")
        self.assertEqual(record_audit_event.call_args.kwargs["entity_type"], "vessel_config")
        self.assertEqual(record_audit_event.call_args.kwargs["metadata"]["affectedTrackedItems"], 5)

    @patch("apps.certs.views.vessel_lifecycle_views.record_audit_event")
    @patch("apps.certs.views.vessel_lifecycle_views.repository")
    def test_class_change_marks_pending_supersession_and_audits(self, repository, record_audit_event) -> None:
        repository.record_class_change.return_value = lifecycle_result(
            vessel_id=self.vessel_id,
            after=config_row(vessel_id=self.vessel_id, class_change_pending=True),
            affected_tracked_items=2,
        )
        request = self.factory.post(
            "/api/certs/vessel/9876543/class-change/",
            {
                "newClassSociety": "DNV",
                "effectiveDate": "2026-08-01",
                "reason": "Owner confirmed class transfer and requires new class snapshot.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = VesselClassChangeView.as_view()(request, imo="9876543")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["affectedTrackedItems"], 2)
        repository.record_class_change.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "class_change_event")

    @patch("apps.certs.views.vessel_lifecycle_views.record_audit_event")
    @patch("apps.certs.views.vessel_lifecycle_views.service")
    @patch("apps.certs.views.vessel_lifecycle_views.repository")
    def test_sale_handover_creates_bundle_updates_config_and_audits(self, repository, service, record_audit_event) -> None:
        bundle_blob_id = str(uuid.uuid4())
        service.generate_share_bundle.return_value = {
            "print_id": "SQE-S633-9876543-20260630-001",
            "bundle_zip_blob_id": bundle_blob_id,
            "system_state_hash": "state-hash",
        }
        repository.record_sale_handover.return_value = lifecycle_result(
            vessel_id=self.vessel_id,
            after=config_row(vessel_id=self.vessel_id, lifecycle_status="sold_pending_handover", sale_handover_bundle_blob_id=bundle_blob_id),
            artifact=service.generate_share_bundle.return_value,
        )
        request = self.factory.post(
            "/api/certs/vessel/9876543/sale-handover/",
            {
                "handoverDate": "2026-09-01",
                "customCertIds": [str(uuid.uuid4())],
                "watermarkRecipient": "Buyer technical office",
                "reason": "Vessel sale handover package requested by buyer technical office.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = VesselSaleHandoverView.as_view()(request, imo="9876543")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["config"]["lifecycleStatus"], "sold_pending_handover")
        self.assertEqual(response.data["config"]["saleHandoverBundleBlobId"], bundle_blob_id)
        service.generate_share_bundle.assert_called_once()
        repository.record_sale_handover.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "sale_initiated")

    @patch("apps.certs.views.vessel_lifecycle_views.record_audit_event")
    @patch("apps.certs.views.vessel_lifecycle_views.repository")
    def test_decommission_sets_pending_disposal_and_audits(self, repository, record_audit_event) -> None:
        repository.record_decommission.return_value = lifecycle_result(
            vessel_id=self.vessel_id,
            after=config_row(vessel_id=self.vessel_id, lifecycle_status="pending_disposal", pending_disposal_started_at="2026-06-30T00:00:00Z"),
            affected_tracked_items=9,
        )
        request = self.factory.post(
            "/api/certs/vessel/9876543/decommission/",
            {
                "decommissionDate": "2026-10-01",
                "reason": "Scrap yard decommissioning notice accepted by DPA.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = VesselDecommissionView.as_view()(request, imo="9876543")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["config"]["lifecycleStatus"], "pending_disposal")
        self.assertEqual(response.data["affectedTrackedItems"], 9)
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "decommission")


class VesselLifecycleRepositoryTests(unittest.TestCase):
    @patch("apps.certs.services.vessel_lifecycle.connection")
    def test_flag_change_updates_only_non_class_statutory_rows(self, connection) -> None:
        cursor = MagicMock()
        cursor.fetchone.return_value = (3,)
        connection.cursor.return_value.__enter__.return_value = cursor
        repository = VesselLifecycleRepository()

        count = repository.mark_statutory_invalid_due_to_reflag(vessel_id="vessel-1", actor_id="dpa-1")

        sql_text = "\n".join(str(call.args[0]) for call in cursor.execute.call_args_list)
        self.assertEqual(count, 3)
        self.assertIn("invalid_due_to_reflag", sql_text)
        self.assertIn("vims_certs_catalog_section", sql_text)
        self.assertIn("section_code = 'STATUTORY'", sql_text)
        self.assertIn("is_class_tracked", sql_text)

    @patch("apps.certs.services.vessel_lifecycle.connection")
    def test_class_change_updates_class_rows_to_pending_supersession(self, connection) -> None:
        cursor = MagicMock()
        cursor.fetchone.return_value = (4,)
        connection.cursor.return_value.__enter__.return_value = cursor
        repository = VesselLifecycleRepository()

        count = repository.mark_class_rows_pending_supersession(vessel_id="vessel-1", actor_id="dpa-1")

        sql_text = "\n".join(str(call.args[0]) for call in cursor.execute.call_args_list)
        self.assertEqual(count, 4)
        self.assertIn("pending_supersession", sql_text)
        self.assertIn("ISNULL(c.is_class_tracked, 0) = 1", sql_text)
        self.assertIn("section_code = 'CLASS'", sql_text)


if __name__ == "__main__":
    unittest.main()
