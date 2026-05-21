from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.views.incident import IncidentDetailView, IncidentListCreateView


def build_user(
    *,
    role_name: str,
    work_side: str | None = None,
    role_by_vessel_rows: list[dict[str, object]] | None = None,
    crew_onboarding_rows: list[dict[str, object]] | None = None,
    vessel_ids: list[str] | None = None,
    is_global: bool = False,
    user_id: str = "user-1",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        work_side=work_side,
        role_by_vessel_rows=role_by_vessel_rows,
        crew_onboarding_rows=crew_onboarding_rows,
        vessel_ids=vessel_ids,
        form_ids=["SAF_F_001"],
        process_ids=[],
        is_global=is_global,
    )


class CrossVesselVisibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.list_view = IncidentListCreateView.as_view()
        self.detail_view = IncidentDetailView.as_view()

        self.own_open = Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state="DRAFT",
            current_phase=1,
            created_by="master-7",
            schema_version=1,
        )
        self.other_closed = Incident.objects.create(
            incident_number="XYZ/2026/002",
            vessel_id="8",
            state="CLOSED",
            current_phase=9,
            created_by="master-8",
            schema_version=1,
        )
        self.other_open = Incident.objects.create(
            incident_number="LMN/2026/003",
            vessel_id="9",
            state="APPROVED",
            current_phase=8,
            created_by="master-9",
            schema_version=1,
        )

    def test_office_user_is_scoped_by_role_by_vessel_rows(self) -> None:
        request = self.factory.get("/api/safety/incidents/")
        force_authenticate(
            request,
            user=build_user(
                role_name="HOD-SHORE",
                work_side="OFFICE",
                role_by_vessel_rows=[{"vessel_id": 8}, {"vessel_id": 11}],
                user_id="shore-1",
            ),
        )

        response = self.list_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data], [self.other_closed.id])

    def test_ship_user_is_scoped_to_current_vessel(self) -> None:
        request = self.factory.get("/api/safety/incidents/")
        force_authenticate(
            request,
            user=build_user(
                role_name="CO",
                work_side="SHIP",
                crew_onboarding_rows=[
                    {"vessel_id": 6, "is_current": False},
                    {"vessel_id": 7, "is_current": True},
                ],
                user_id="co-7",
            ),
        )

        response = self.list_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["id"] for row in response.data], [self.own_open.id])

    def test_dpa_has_global_visibility_without_explicit_vessel_scope(self) -> None:
        request = self.factory.get("/api/safety/incidents/")
        force_authenticate(
            request,
            user=build_user(role_name="DPA", work_side="OFFICE", user_id="dpa-1"),
        )

        response = self.list_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {row["id"] for row in response.data},
            {self.own_open.id, self.other_closed.id, self.other_open.id},
        )

    def test_master_can_read_closed_incidents_fleetwide_but_not_open_other_vessels(self) -> None:
        request = self.factory.get("/api/safety/incidents/")
        force_authenticate(
            request,
            user=build_user(role_name="MASTER", vessel_ids=["7"], user_id="master-7"),
        )

        response = self.list_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {row["id"] for row in response.data},
            {self.own_open.id, self.other_closed.id},
        )

    def test_master_can_open_closed_incident_detail_outside_own_vessel_scope(self) -> None:
        request = self.factory.get(f"/api/safety/incidents/{self.other_closed.id}/")
        force_authenticate(
            request,
            user=build_user(role_name="MASTER", vessel_ids=["7"], user_id="master-7"),
        )

        response = self.detail_view(request, id=self.other_closed.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.other_closed.id)
