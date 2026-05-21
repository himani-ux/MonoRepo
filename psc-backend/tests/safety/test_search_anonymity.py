from __future__ import annotations

from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_scm_tables,
    recreate_soi_tables,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.views.search import SafetyCrossRecordSearchView


def build_user(*, role_name: str, form_ids: list[str] | None = None, user_id: str = "viewer-1"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=form_ids or ["SAF_F_005"],
        process_ids=[],
        vessel_ids=["7"],
        is_global=role_name in {"DPA", "FM"},
    )


class CrossRecordSearchAnonymityTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_scm_tables()
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.view = SafetyCrossRecordSearchView.as_view()
        self.near_miss = Incident.objects.create(
            incident_number="NM/2026/051",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="TRIAGED",
            current_phase=1,
            near_miss_priority="LOW",
            occurred_at=timezone.now(),
            narrative="Reporter identified a manifold pressure wobble before cargo transfer started.",
            reporter_id="crew-51",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            reporter_email="crew51@example.test",
            created_by="crew-51",
            updated_by="crew-51",
            schema_version=1,
        )

    def test_master_view_masks_reporter_name_in_search_hits(self) -> None:
        request = self.factory.get("/api/safety/search/?q=manifold")
        force_authenticate(request, user=build_user(role_name="MASTER", user_id="master-7"))

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["include_archived"])
        self.assertEqual(response.data["counts"]["NEAR_MISS"], 1)
        self.assertEqual(
            response.data["groups"]["NEAR_MISS"][0]["reporter_name"],
            "Anonymous Reporter",
        )

    def test_dpa_view_retains_reporter_name_in_search_hits(self) -> None:
        request = self.factory.get("/api/safety/search/?q=manifold")
        force_authenticate(request, user=build_user(role_name="DPA", user_id="dpa-1"))

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["include_archived"])
        self.assertEqual(
            response.data["groups"]["NEAR_MISS"][0]["reporter_name"],
            "Crew Reporter",
        )

    def test_short_queries_are_rejected(self) -> None:
        request = self.factory.get("/api/safety/search/?q=ma")
        force_authenticate(request, user=build_user(role_name="DPA", user_id="dpa-1"))

        response = self.view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("at least 3 characters", str(response.data["detail"]))
