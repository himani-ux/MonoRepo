from __future__ import annotations

from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.views.near_miss_triage import NearMissTriageView


def build_user(
    *,
    role_name: str = "DPA",
    process_ids: list[str] | None = None,
    user_id: str = "dpa-1",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_002"],
        process_ids=["SAF_P_002"] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class NearMissHighPrioritySupersedeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = NearMissTriageView.as_view()
        self.near_miss = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T015",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state=Incident.State.READY_FOR_DPA_TRIAGE,
            current_phase=1,
            occurred_at=timezone.now(),
            reported_at=timezone.now(),
            incident_type_id=7,
            narrative=(
                "Crew reported a machinery-space ignition source next to leaked oil residue, "
                "and the watch team secured the area before a fire started."
            ),
            near_miss_priority="LOW",
            reporter_id="crew-9",
            reporter_name="Crew Reporter",
            reporter_rank="OILER",
            created_by="crew-9",
            updated_by="crew-9",
            schema_version=1,
        )

    def test_high_priority_triage_can_supersede_to_incident(self) -> None:
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/triage/",
            {
                "near_miss_priority": "HIGH",
                "supersede_to_incident": True,
                "override_reason": "Potential machinery-space fire exposure requires full incident workflow.",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["suggested_priority"], "HIGH")
        self.assertIsNotNone(response.data["superseded_incident"])
        self.assertEqual(response.data["superseded_incident"]["record_type"], "INCIDENT")

        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.state, "SUPERSEDED")
        self.assertIsNotNone(self.near_miss.superseded_by_id)
        self.assertEqual(self.near_miss.linked_incident_id, self.near_miss.superseded_by_id)

        new_incident = Incident.objects.get(pk=self.near_miss.superseded_by_id)
        self.assertEqual(new_incident.record_type, Incident.RecordType.INCIDENT)
        self.assertEqual(new_incident.linked_incident_id, self.near_miss.pk)

    def test_supersede_to_incident_requires_dpa_reason(self) -> None:
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/triage/",
            {
                "near_miss_priority": "HIGH",
                "supersede_to_incident": True,
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Supersede-to-incident requires", str(response.data))
