from __future__ import annotations

import os
import unittest
from unittest.mock import patch
import uuid

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.certs.views.dashboard_views import FleetDashboardView, VesselDashboardView
from apps.certs.services.vessel_dashboard import VesselDashboardData
from tests.certs.test_tracked_item_api import make_user, tracked_item_row


class CertVesselDashboardApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.vessel_id = str(uuid.uuid4())
        self.reader = make_user(
            role="Fleet Manager",
            form_ids=["CERT_F_002"],
            process_ids=[],
            has_global_vessel_access=True,
        )
        self.no_tracked_item_access = make_user(role="Fleet Manager", form_ids=["CERT_F_001"], process_ids=[])

    @patch("apps.certs.views.dashboard_views.repository")
    def test_vessel_dashboard_requires_tracked_item_form_id(self, repository) -> None:
        request = self.factory.get("/api/certs/dashboard/vessel/9876543/")
        force_authenticate(request, user=self.no_tracked_item_access)

        response = VesselDashboardView.as_view()(request, imo="9876543")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.get_dashboard.assert_not_called()

    @patch("apps.certs.views.dashboard_views.fleet_repository")
    def test_fleet_dashboard_requires_fleet_manager_role_for_high_volume_surface(self, fleet_repository) -> None:
        request = self.factory.get("/api/certs/dashboard/fleet/")
        technical_superintendent = make_user(
            role="Technical Superintendent",
            form_ids=["CERT_F_004"],
            process_ids=[],
            has_global_vessel_access=True,
        )
        force_authenticate(request, user=technical_superintendent)

        response = FleetDashboardView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        fleet_repository.get_high_volume_print_activity.assert_not_called()

    @patch("apps.certs.views.dashboard_views.fleet_repository")
    def test_fleet_dashboard_serializes_dpa_bouncing_email_surface(self, fleet_repository) -> None:
        fleet_repository.get_bouncing_email_delivery.return_value = {
            "bouncingUsersCount": 2,
            "users": [
                {
                    "userId": "master-1",
                    "lastBouncedAt": "2026-06-29T11:30:00Z",
                    "criticalFallbackCount": 1,
                },
                {
                    "userId": "ce-1",
                    "lastBouncedAt": "2026-06-29T11:35:00Z",
                    "criticalFallbackCount": 0,
                },
            ],
        }
        fleet_repository.get_cadence_heartbeat.return_value = {
            "lastCadenceHeartbeat": "2026-06-29T09:15:00Z",
        }
        request = self.factory.get("/api/certs/dashboard/fleet/")
        dpa = make_user(
            role="DPA",
            form_ids=["CERT_F_002"],
            process_ids=[],
            has_global_vessel_access=True,
        )
        force_authenticate(request, user=dpa)

        response = FleetDashboardView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["bouncingEmailDelivery"]["bouncingUsersCount"], 2)
        self.assertEqual(response.data["bouncingEmailDelivery"]["users"][0]["userId"], "master-1")
        self.assertEqual(response.data["bouncingEmailDelivery"]["users"][0]["criticalFallbackCount"], 1)
        self.assertEqual(response.data["cadenceHeartbeat"]["lastCadenceHeartbeat"], "2026-06-29T09:15:00Z")
        fleet_repository.get_high_volume_print_activity.assert_not_called()

    @patch("apps.certs.views.dashboard_views.fleet_repository")
    def test_fleet_dashboard_serializes_high_volume_print_activity_for_fm(self, fleet_repository) -> None:
        fleet_repository.get_high_volume_print_activity.return_value = {
            "thresholdPerHour": 10,
            "windowMinutes": 60,
            "usersAboveThresholdCount": 1,
            "users": [
                {
                    "userId": "fm-1",
                    "userRole": "Fleet Manager",
                    "printCountLastHour": 11,
                    "lastPrintAt": "2026-06-29T10:15:00Z",
                    "lastSignalAt": "2026-06-29T10:15:01Z",
                }
            ],
        }
        request = self.factory.get("/api/certs/dashboard/fleet/")
        fm_reader = make_user(
            role="Fleet Manager",
            form_ids=["CERT_F_004"],
            process_ids=[],
            has_global_vessel_access=True,
        )
        force_authenticate(request, user=fm_reader)

        response = FleetDashboardView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["highVolumePrintActivity"]["usersAboveThresholdCount"], 1)
        self.assertEqual(response.data["highVolumePrintActivity"]["thresholdPerHour"], 10)
        self.assertEqual(response.data["highVolumePrintActivity"]["users"][0]["userId"], "fm-1")

    @patch("apps.certs.views.dashboard_views.repository")
    def test_vessel_dashboard_serializes_vessel_rollup_sections_and_items(self, repository) -> None:
        repository.get_dashboard.return_value = VesselDashboardData(
            vessel={
                "vessel_id": self.vessel_id,
                "vessel_code": "KSM",
                "vessel_name": "KSM Fortitude",
                "imo_number": "9876543",
                "flag": "Panama",
                "class_society": "NK",
                "current_master": "MASTER - Captain Anil",
            },
            config={
                "ship_type": "bulk_carrier",
                "lifecycle_status": "active",
                "mandatory_coverage_override_reason": None,
            },
            last_snapshot={
                "snapshot_id": uuid.uuid4(),
                "class_society": "NK",
                "uploaded_at": "2026-06-24T00:00:00Z",
                "parse_status": "success",
                "reconciliation_run_id": None,
            },
            sections=[
                {"section_id": 1, "section_code": "CLASS", "display_name": "Class Certificates", "sort_order": 1},
                {"section_id": 2, "section_code": "STATUTORY", "display_name": "Statutory & Flag", "sort_order": 2},
            ],
            items=[
                tracked_item_row(
                    vessel_id=self.vessel_id,
                    catalog_section_id=2,
                    catalog_section_code="STATUTORY",
                    catalog_section_name="Statutory & Flag",
                    catalog_print_order=10,
                    catalog_mandatory_for_all_vessels=True,
                    catalog_is_class_tracked=False,
                    status="pending_first_upload",
                    pdf_missing=True,
                )
            ],
            mandatory_coverage={
                "percent": 0.0,
                "mandatoryCount": 1,
                "coveredCount": 0,
                "missing": [
                    {
                        "catalogId": "catalog-iopp",
                        "catalogCode": "STAT-IOPP",
                        "displayName": "International Oil Pollution Prevention Certificate",
                        "shortName": "IOPP",
                        "sectionId": 2,
                        "sectionCode": "STATUTORY",
                        "sectionName": "Statutory & Flag",
                        "trackedItemId": "tracked-iopp",
                        "status": "pending_first_upload",
                        "reason": "pending_first_upload",
                    }
                ],
                "overrideActive": False,
                "overrideReason": None,
                "overrideAt": None,
                "overrideBy": None,
            },
        )
        request = self.factory.get("/api/certs/dashboard/vessel/9876543/")
        force_authenticate(request, user=self.reader)

        response = VesselDashboardView.as_view()(request, imo="9876543")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["vessel"]["name"], "KSM Fortitude")
        self.assertEqual(response.data["vessel"]["imo"], "9876543")
        self.assertEqual(response.data["vessel"]["currentMaster"], "MASTER - Captain Anil")
        self.assertEqual(response.data["summary"]["totalTrackedItems"], 1)
        self.assertEqual(response.data["summary"]["actionItemCount"], 1)
        self.assertEqual(response.data["mandatoryCoverage"]["percent"], 0.0)
        statutory = response.data["sections"][1]
        self.assertEqual(statutory["displayName"], "Statutory & Flag")
        self.assertEqual(statutory["statusBreakdown"]["pending_first_upload"], 1)
        self.assertEqual(statutory["items"][0]["validityShortCode"], "5-Y")

    @patch("apps.certs.views.dashboard_views.repository")
    def test_vessel_dashboard_enforces_resolved_vessel_scope(self, repository) -> None:
        repository.get_dashboard.return_value = VesselDashboardData(
            vessel={"vessel_id": self.vessel_id, "vessel_name": "KSM Fortitude"},
            config=None,
            last_snapshot=None,
            sections=[],
            items=[],
            mandatory_coverage=None,
        )
        scoped_reader = make_user(
            role="Technical Superintendent",
            form_ids=["CERT_F_002"],
            process_ids=[],
            vessel_ids=[str(uuid.uuid4())],
        )
        request = self.factory.get("/api/certs/dashboard/vessel/9876543/")
        force_authenticate(request, user=scoped_reader)

        response = VesselDashboardView.as_view()(request, imo="9876543")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
