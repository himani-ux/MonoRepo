from __future__ import annotations

import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.services import NearMissSupersedeService


class NearMissSupersedeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.service = NearMissSupersedeService()

    def test_supersede_creates_new_incident_and_marks_original_superseded(self) -> None:
        near_miss = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T009",
            vessel_id="ABC",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OPEN",
            current_phase=1,
            occurred_at=timezone.now(),
            narrative="Near miss involving unsecured purifier blind during restart.",
            reporter_id="crew-1",
            reporter_name="Crew Reporter",
            created_by="crew-1",
            updated_by="crew-1",
            schema_version=1,
        )

        new_incident = self.service.supersede_near_miss(near_miss.pk, actor_id="dpa-1")

        near_miss.refresh_from_db()
        self.assertEqual(new_incident.record_type, Incident.RecordType.INCIDENT)
        self.assertTrue(new_incident.incident_number.startswith("DRAFT-ABC/2026/T"))
        self.assertEqual(new_incident.linked_incident_id, near_miss.pk)
        self.assertEqual(new_incident.narrative, near_miss.narrative)
        self.assertEqual(near_miss.state, "SUPERSEDED")
        self.assertEqual(near_miss.superseded_by_id, new_incident.pk)
        self.assertEqual(near_miss.linked_incident_id, new_incident.pk)
