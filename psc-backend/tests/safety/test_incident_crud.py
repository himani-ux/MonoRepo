from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import ExternalPartyInjury, Incident
from apps.safety.services.incident_weather_schema_guard import (
    _ensure_sql_server_incident_weather_columns,
    _ensure_sql_server_weather_option_table_id,
)
from apps.safety.views.incident import IncidentDetailView, IncidentListCreateView, IncidentRegisterVesselListView


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
        self.vessel_list_view = IncidentRegisterVesselListView.as_view()

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

    def test_create_incident_accepts_selected_weather_uuid(self) -> None:
        weather_id = "00000000-0000-4000-8000-000000000001"
        create_request = self.factory.post(
            "/api/safety/incidents/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "occurred_at": "2026-04-27T10:00:00Z",
                "reported_at": "2026-04-27T10:30:00Z",
                "narrative": "Initial scene secured and witness list started.",
                "weather_visibility_id": weather_id,
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user())

        create_response = self.list_view(create_request)

        self.assertEqual(create_response.status_code, 201)
        incident = Incident.objects.get(pk=create_response.data["id"])
        self.assertEqual(str(incident.weather_visibility_id), weather_id)

    def test_create_incident_persists_nested_injury_details(self) -> None:
        create_request = self.factory.post(
            "/api/safety/incidents/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "schema_version": 1,
                "occurred_at": "2026-04-27T10:00:00Z",
                "reported_at": "2026-04-27T10:30:00Z",
                "narrative": "Injury details captured during initial report.",
                "external_party_injury": {
                    "injured_person_type": ExternalPartyInjury.InjuredPersonType.CREW,
                    "crew_rank": "Chief Officer",
                    "crew_activity_type": "Hot work",
                    "nature_of_injury": "Cuts / Lacerations",
                    "cost_medicines_onboard": "123.45",
                    "total_estimated_cost": "123.45",
                },
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user())

        create_response = self.list_view(create_request)

        self.assertEqual(create_response.status_code, 201)
        injury = ExternalPartyInjury.objects.get(incident_id=create_response.data["id"])
        self.assertEqual(injury.injured_person_type, ExternalPartyInjury.InjuredPersonType.CREW)
        self.assertEqual(injury.crew_rank, "Chief Officer")
        self.assertEqual(injury.crew_activity_type, "Hot work")
        self.assertEqual(str(injury.total_estimated_cost), "123.45")

    def test_patch_incident_with_null_injury_preserves_existing_injury_details(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T009",
            vessel_id="7",
            state="DRAFT",
            current_phase=1,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        ExternalPartyInjury.objects.create(
            incident=incident,
            injured_person_type=ExternalPartyInjury.InjuredPersonType.CREW,
            crew_rank="Chief Officer",
            crew_activity_type="Hot work",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        patch_request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/",
            {
                "narrative": "Updated details while injury section was not changed.",
                "external_party_injury": None,
            },
            format="json",
        )
        force_authenticate(patch_request, user=build_user())

        patch_response = self.detail_view(patch_request, id=incident.pk)

        self.assertEqual(patch_response.status_code, 200)
        injury = ExternalPartyInjury.objects.get(incident=incident)
        self.assertEqual(injury.crew_rank, "Chief Officer")
        self.assertEqual(injury.crew_activity_type, "Hot work")

    def test_sql_server_weather_guard_uses_django_uuid_storage_shape(self) -> None:
        class CapturingCursor:
            def __init__(self) -> None:
                self.statements: list[str] = []

            def execute(self, sql: str) -> None:
                self.statements.append(sql)

        cursor = CapturingCursor()

        _ensure_sql_server_incident_weather_columns(cursor)

        combined_sql = "\n".join(cursor.statements)
        self.assertIn("ADD weather_visibility_id CHAR(32) NULL", combined_sql)
        self.assertIn("DATA_TYPE = N'uniqueidentifier'", combined_sql)
        self.assertIn("LOWER(REPLACE(CONVERT(CHAR(36), weather_visibility_id)", combined_sql)

    def test_sql_server_weather_guard_converts_option_master_id_to_char32(self) -> None:
        class CapturingCursor:
            def __init__(self) -> None:
                self.statements: list[str] = []

            def execute(self, sql: str) -> None:
                self.statements.append(sql)

        cursor = CapturingCursor()

        _ensure_sql_server_weather_option_table_id(cursor)

        combined_sql = "\n".join(cursor.statements)
        self.assertIn("TABLE_NAME = N'vims_safety_incident_weather_option'", combined_sql)
        self.assertIn("DATA_TYPE = N'uniqueidentifier'", combined_sql)
        self.assertIn("ADD id_char32 CHAR(32) NULL", combined_sql)
        self.assertIn("LOWER(REPLACE(CONVERT(CHAR(36), id)", combined_sql)

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

    def test_incident_register_vessel_options_use_available_vessel_resolver(self) -> None:
        request = self.factory.get("/api/safety/incidents/vessels/")
        user = build_user(form_ids=["SAF_F_001"], process_ids=[], role_name="DPA", vessel_ids=[])
        force_authenticate(request, user=user)

        with patch(
            "apps.safety.views.incident._list_available_vessels",
            return_value=[
                {
                    "id": "vessel-ycf",
                    "vessel_code": "YCF",
                    "vessel_name": "YC FORTITUDE",
                }
            ],
        ) as resolver:
            response = self.vessel_list_view(request)

        self.assertEqual(response.status_code, 200)
        resolver.assert_called_once_with(user=user)
        self.assertEqual(
            response.data,
            [
                {
                    "id": "vessel-ycf",
                    "vessel_code": "YCF",
                    "vessel_name": "YC FORTITUDE",
                }
            ],
        )

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
