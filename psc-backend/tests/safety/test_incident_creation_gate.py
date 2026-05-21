from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.incident import IncidentListCreateView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    user_id: str = "user-1",
    user_type: str = "VESSEL",
    vessel_id: str = "7",
    vessel_code: str = "ABC",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        user_type=user_type,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_001"] if process_ids is None else process_ids,
        vessel_id=vessel_id,
        vessel_code=vessel_code,
        vessel_ids=[vessel_id],
        is_global=False,
    )


class IncidentCreationGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = IncidentListCreateView.as_view()

    def test_top_four_officer_with_create_permission_can_post_incident(self) -> None:
        request = self.factory.post(
            "/api/safety/incidents/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "record_type": "INCIDENT",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="MASTER", process_ids=["SAF_P_001"], user_id="master-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["record_type"], "INCIDENT")

    def test_vessel_user_create_uses_authenticated_vessel_context(self) -> None:
        request = self.factory.post(
            "/api/safety/incidents/",
            {
                "schema_version": 1,
                "record_type": "INCIDENT",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(
                role_name="MASTER",
                process_ids=["SAF_P_001"],
                user_id="master-ef90",
                vessel_id="EF9029C2-A192-EF11-A9F2-933342524037",
                vessel_code="MVX",
            ),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["vessel_id"], "EF9029C2-A192-EF11-A9F2-933342524037")
        self.assertTrue(str(response.data["incident_number"]).startswith("DRAFT-MVX/"))

    def test_missing_create_permission_is_rejected_even_for_top_four_officer(self) -> None:
        request = self.factory.post(
            "/api/safety/incidents/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "record_type": "INCIDENT",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="MASTER", process_ids=[], user_id="master-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 403)

    def test_non_top_four_role_cannot_create_incident_even_with_create_permission(self) -> None:
        request = self.factory.post(
            "/api/safety/incidents/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "record_type": "INCIDENT",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="HOD", process_ids=["SAF_P_001"], user_id="hod-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 403)

    def test_near_miss_creation_allows_non_top_four_role(self) -> None:
        request = self.factory.post(
            "/api/safety/incidents/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "record_type": "NEAR_MISS",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="HOD", process_ids=["SAF_P_001"], user_id="hod-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["record_type"], "NEAR_MISS")
