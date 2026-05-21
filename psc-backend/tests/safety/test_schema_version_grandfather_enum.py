from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident


class SchemaVersionGrandfatherEnumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()

    def test_schema_version_one_keeps_legacy_state_phase_and_depth_readable(self) -> None:
        legacy_incident = Incident.objects.create(
            incident_number="ABC/2025/001",
            vessel_id="7",
            state="PHASE_2",
            current_phase=0,
            investigation_depth="LEGACY_DEEP",
            created_by="legacy-import",
            schema_version=1,
        )

        fetched = Incident.objects.get(pk=legacy_incident.pk)

        self.assertEqual(fetched.schema_version, 1)
        self.assertEqual(fetched.state, "PHASE_2")
        self.assertEqual(fetched.current_phase, 0)
        self.assertEqual(fetched.investigation_depth, "LEGACY_DEEP")

    def test_schema_version_one_near_miss_keeps_open_state_readable(self) -> None:
        legacy_near_miss = Incident.objects.create(
            incident_number="DRAFT-ABC/2025/T014",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OPEN",
            current_phase=1,
            created_by="legacy-import",
            schema_version=1,
        )

        fetched = Incident.objects.get(pk=legacy_near_miss.pk)

        self.assertEqual(fetched.record_type, Incident.RecordType.NEAR_MISS)
        self.assertEqual(fetched.state, "OPEN")
