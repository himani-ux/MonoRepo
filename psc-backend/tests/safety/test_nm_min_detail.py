from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.near_miss import NearMissListCreateView


def build_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="wiper-7",
        username="wiper-7",
        role_name="WIPER",
        form_ids=["SAF_F_002"],
        process_ids=["SAF_P_001"],
        vessel_ids=["7"],
        is_global=False,
    )


class NearMissMinimumDetailTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = NearMissListCreateView.as_view()

    def test_submit_rejects_description_shorter_than_100_characters(self) -> None:
        request = self.factory.post(
            "/api/safety/near-miss/",
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "narrative": "Too short to pass the Step 2.4 near-miss minimum-detail contract.",
                "near_miss_priority": "LOW",
                "reporter_name": "Deck Wiper",
                "reporter_rank": "WIPER",
                "reporter_user_id": "wiper-7",
                "schema_version": 1,
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["narrative"][0],
            "Near-miss description must be at least 100 characters (D-GAP-M38).",
        )
