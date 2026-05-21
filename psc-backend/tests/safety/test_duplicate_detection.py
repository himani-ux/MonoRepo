from __future__ import annotations

from datetime import timedelta
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.services import IncidentLinker


class DuplicateDetectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.linker = IncidentLinker()

    def test_same_day_same_vessel_close_position_flags_candidate(self) -> None:
        occurred_at = timezone.now()
        source = Incident.objects.create(
            incident_number="ABC/2026/010",
            vessel_id="ABC",
            state="IN_PROGRESS",
            current_phase=4,
            incident_type_id=11,
            occurred_at=occurred_at,
            latitude="1.300000",
            longitude="103.800000",
            narrative="Engine room smoke alarm during purifier restart after maintenance.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        candidate = Incident.objects.create(
            incident_number="ABC/2026/011",
            vessel_id="ABC",
            state="IN_PROGRESS",
            current_phase=4,
            incident_type_id=11,
            occurred_at=occurred_at + timedelta(hours=3),
            latitude="1.320000",
            longitude="103.790000",
            narrative="Purifier restart triggered smoke alarm in engine room after maintenance work.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        Incident.objects.create(
            incident_number="ABC/2026/012",
            vessel_id="ABC",
            state="IN_PROGRESS",
            current_phase=4,
            incident_type_id=11,
            occurred_at=occurred_at + timedelta(days=2),
            latitude="5.000000",
            longitude="110.000000",
            narrative="Unrelated cargo-handling delay in another port.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        results = self.linker.detect_duplicates(
            source.vessel_id,
            (occurred_at - timedelta(hours=24), occurred_at + timedelta(hours=24)),
            "engine room smoke alarm purifier restart maintenance",
            incident_type_id=11,
            latitude=1.300000,
            longitude=103.800000,
            source_incident_id=source.pk,
        )

        self.assertEqual([result.incident_id for result in results], [candidate.pk])
        self.assertLessEqual(results[0].distance_nm, 10.0)
        self.assertLessEqual(results[0].overlap_hours, 24.0)
        self.assertGreater(results[0].narrative_overlap, 0.0)
