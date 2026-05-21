from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.services import IncidentLinkError, IncidentLinker


class MultiVesselLinkingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.linker = IncidentLinker()

    def test_bidirectional_link_is_persisted(self) -> None:
        first = Incident.objects.create(
            incident_number="AAA/2026/001",
            vessel_id="AAA",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        second = Incident.objects.create(
            incident_number="BBB/2026/001",
            vessel_id="BBB",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        linked_first, linked_second = self.linker.link_multi_vessel_incidents([first.pk, second.pk])

        self.assertEqual(linked_first.linked_incident_id, second.pk)
        self.assertEqual(linked_second.linked_incident_id, first.pk)

    def test_cycle_prevention_rejects_relinking_to_third_record(self) -> None:
        first = Incident.objects.create(
            incident_number="AAA/2026/001",
            vessel_id="AAA",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        second = Incident.objects.create(
            incident_number="BBB/2026/001",
            vessel_id="BBB",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        third = Incident.objects.create(
            incident_number="CCC/2026/001",
            vessel_id="CCC",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        self.linker.link_multi_vessel_incidents([first.pk, second.pk])

        with self.assertRaises(IncidentLinkError):
            self.linker.link_multi_vessel_incidents([second.pk, third.pk])
