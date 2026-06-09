from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.views.incident import IncidentDetailView, IncidentListCreateView


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


class IncidentCrudApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.list_view = IncidentListCreateView.as_view()
        self.detail_view = IncidentDetailView.as_view()

    @staticmethod
    def _response_rows(response_data):
        if isinstance(response_data, dict) and isinstance(response_data.get("results"), list):
            return response_data["results"]
        return response_data

    def test_create_list_and_patch_incident(self) -> None:
        create_request = self.factory.post(
            "/api/safety/incidents/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "occurred_at": "2026-04-27T10:00:00Z",
                "reported_at": "2026-04-27T10:30:00Z",
                "narrative": "Initial scene secured and witness list started.",
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user())

        create_response = self.list_view(create_request)

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["incident_number"], "DRAFT-ABC/2026/T001")
        self.assertEqual(create_response.data["draft_reference"], "DRAFT-ABC/2026/T001")
        self.assertEqual(create_response.data["current_phase"], 1)

        incident_id = create_response.data["id"]

        list_request = self.factory.get("/api/safety/incidents/")
        force_authenticate(list_request, user=build_user(form_ids=["SAF_F_001"], process_ids=[]))
        list_response = self.list_view(list_request)

        self.assertEqual(list_response.status_code, 200)
        rows = self._response_rows(list_response.data)
        listed_ids = {str(row["id"]) for row in rows}
        self.assertIn(str(incident_id), listed_ids)

        patch_request = self.factory.patch(
            f"/api/safety/incidents/{incident_id}/",
            {"narrative": "Updated narrative after witness confirmation."},
            format="json",
        )
        force_authenticate(patch_request, user=build_user())
        patch_response = self.detail_view(patch_request, id=incident_id)

        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.data["narrative"], "Updated narrative after witness confirmation.")
        self.assertEqual(
            Incident.objects.get(pk=incident_id).narrative,
            "Updated narrative after witness confirmation.",
        )

    def test_list_is_scoped_by_vessel(self) -> None:
        Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="DRAFT",
            created_by="master-7",
            schema_version=1,
            occurred_at=datetime(2026, 4, 27, 10, 0, tzinfo=timezone.utc),
        )
        Incident.objects.create(
            incident_number="DRAFT-XYZ/2026/T001",
            vessel_id="8",
            state="DRAFT",
            created_by="master-8",
            schema_version=1,
            occurred_at=datetime(2026, 4, 27, 11, 0, tzinfo=timezone.utc),
        )

        list_request = self.factory.get("/api/safety/incidents/")
        force_authenticate(
            list_request,
            user=build_user(form_ids=["SAF_F_001"], process_ids=[], vessel_ids=["7"]),
        )

        list_response = self.list_view(list_request)

        self.assertEqual(list_response.status_code, 200)
        rows = self._response_rows(list_response.data)
        self.assertTrue(rows)
        self.assertTrue(all(row["vessel_id"] == "7" for row in rows))
        self.assertNotIn("8", {row["vessel_id"] for row in rows})

    def test_create_requires_top_four_officer_role(self) -> None:
        create_request = self.factory.post(
            "/api/safety/incidents/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user(role_name="HOD"))

        create_response = self.list_view(create_request)

        self.assertEqual(create_response.status_code, 403)
