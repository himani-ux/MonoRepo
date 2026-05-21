from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django


bootstrap_django()

from apps.safety.models import BaseSafetyRecord, Incident


class IncidentModelTests(unittest.TestCase):
    def test_incident_inherits_base_safety_record(self) -> None:
        self.assertTrue(issubclass(Incident, BaseSafetyRecord))

    def test_current_phase_maps_to_phase_column_with_default(self) -> None:
        field = Incident._meta.get_field("current_phase")

        self.assertEqual(field.db_column, "phase")
        self.assertEqual(field.default, 1)

    def test_record_type_enum_is_locked_to_incident_and_near_miss(self) -> None:
        field = Incident._meta.get_field("record_type")
        values = {choice for choice, _label in field.choices}

        self.assertEqual(values, {Incident.RecordType.INCIDENT, Incident.RecordType.NEAR_MISS})

    def test_draft_reference_is_derived_from_draft_incident_number(self) -> None:
        incident = Incident(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="DRAFT",
            created_by="master-7",
            schema_version=1,
        )

        self.assertEqual(incident.draft_reference, "DRAFT-ABC/2026/T001")

        incident.incident_number = "ABC/2026/001"
        self.assertIsNone(incident.draft_reference)
