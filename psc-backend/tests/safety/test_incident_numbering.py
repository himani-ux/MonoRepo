from __future__ import annotations

from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.repositories import IncidentRepository


class IncidentNumberingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.repository = IncidentRepository()

    def test_allocate_draft_reference_increments_per_vessel_year(self) -> None:
        first = self.repository.create(
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "created_by": "master-7",
                "occurred_at": datetime(2026, 4, 27, 10, 0, tzinfo=timezone.utc),
                "schema_version": 1,
            }
        )
        second = self.repository.create(
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "created_by": "master-7",
                "occurred_at": datetime(2026, 4, 27, 11, 0, tzinfo=timezone.utc),
                "schema_version": 1,
            }
        )

        next_year = self.repository.allocate_draft_reference("ABC", 2027)

        self.assertEqual(first.incident_number, "DRAFT-ABC/2026/T001")
        self.assertEqual(second.incident_number, "DRAFT-ABC/2026/T002")
        self.assertEqual(next_year, "DRAFT-ABC/2027/T001")

    def test_assign_number_uses_gap_free_formal_sequence(self) -> None:
        Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state="PHASE_2",
            created_by="master-7",
            schema_version=1,
        )
        Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="DRAFT",
            created_by="master-7",
            schema_version=1,
        )

        next_number = self.repository.assign_number("ABC", 2026)
        reset_number = self.repository.assign_number("ABC", 2027)

        self.assertEqual(next_number, "ABC/2026/002")
        self.assertEqual(reset_number, "ABC/2027/001")

    def test_create_retries_when_auto_draft_reference_collides(self) -> None:
        Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T012",
            vessel_id="7",
            state="DRAFT",
            created_by="master-7",
            schema_version=1,
        )

        with patch.object(
            self.repository,
            "allocate_draft_reference",
            side_effect=["DRAFT-ABC/2026/T012", "DRAFT-ABC/2026/T013"],
        ):
            incident = self.repository.create(
                {
                    "vessel_id": "7",
                    "vessel_code": "ABC",
                    "created_by": "master-7",
                    "occurred_at": datetime(2026, 4, 27, 10, 0, tzinfo=timezone.utc),
                    "schema_version": 1,
                }
            )

        self.assertEqual(incident.incident_number, "DRAFT-ABC/2026/T013")
