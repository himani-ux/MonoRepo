from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.views.incident_phase1 import IncidentPhase1CreateView, IncidentPhase1SubmitView


def build_user(
    *,
    role_name: str = "MASTER",
    form_ids: list[str] | None = None,
    process_ids: list[str] | None = None,
    vessel_ids: list[str] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=form_ids or ["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_001"],
        vessel_ids=vessel_ids or ["7"],
        is_global=False,
    )


class IncidentPhase1ValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.create_view = IncidentPhase1CreateView.as_view()
        self.submit_view = IncidentPhase1SubmitView.as_view()

    def test_create_rejects_vessel_outside_scope(self) -> None:
        request = self.factory.post(
            "/api/safety/incidents/phase-1/",
            {
                "vessel_id": "8",
                "vessel_code": "XYZ",
                "schema_version": 1,
            },
            format="json",
        )
        force_authenticate(request, user=build_user(vessel_ids=["7"]))

        response = self.create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["vessel_id"][0], "You are not assigned to this vessel.")

    def test_create_rejects_future_reported_at(self) -> None:
        future = datetime.now(timezone.utc) + timedelta(hours=2)
        request = self.factory.post(
            "/api/safety/incidents/phase-1/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "reported_at": future.isoformat(),
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["reported_at"][0], "Reported time cannot be in the future.")

    def test_submit_rejects_short_narrative_and_incomplete_checklist(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="DRAFT",
            current_phase=1,
            created_by="master-7",
            schema_version=1,
            narrative="Too short",
            reporter_id="master-7",
            reporter_name="Master Seven",
            reporter_rank="MASTER",
            reporter_device_fingerprint="device-abc",
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-1/submit/",
            {},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.submit_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["first_hour_checklist_done"][0],
            "Complete the first-hour scene-protection checklist before submitting Phase 1.",
        )
        self.assertEqual(
            response.data["narrative"][0],
            "Incident narrative must be at least 200 characters.",
        )
