from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django


bootstrap_django()

from apps.safety.models import SOIApplicabilityLog, SOIInspection, SOIVesselAreaMap


class SOIModelTests(unittest.TestCase):
    def test_inspection_uses_expected_table_and_defaults(self) -> None:
        inspection = SOIInspection(
            vessel_id="7",
            inspection_reference="SOI/ABC/26/01",
            cycle_label="Q2/2026",
            planned_date="2026-05-01",
            safety_officer_crew_id="so-7",
            safety_officer_department="DECK",
            assistant_crew_id="asst-7",
            assistant_department="ENGINE",
            created_by="so-7",
        )

        self.assertEqual(inspection._meta.db_table, "vims_safety_soi_inspection")
        self.assertEqual(inspection.state, SOIInspection.State.PLANNED)
        self.assertEqual(inspection.section_12_included, False)
        self.assertEqual(
            [choice for choice, _label in SOIInspection.State.choices],
            ["PLANNED", "DOWNLOADED", "IN_FIELDWORK", "REPORTED", "CLOSED"],
        )

    def test_area_map_uses_expected_table_and_default_applicable_true(self) -> None:
        area_map = SOIVesselAreaMap(vessel_id="7", area_id=3)

        self.assertEqual(area_map._meta.db_table, "vims_safety_soi_vessel_area_map")
        self.assertEqual(area_map.applicable, True)
        self.assertEqual(area_map.schema_version, 1)

    def test_applicability_log_uses_expected_table(self) -> None:
        log_row = SOIApplicabilityLog(
            vessel_id="7",
            area_id=3,
            old_applicable=True,
            new_applicable=False,
            reason="Cargo oil room does not exist on this vessel class.",
            master_requested_by="master-7",
            master_signature="Captain Example|device-abc",
        )

        self.assertEqual(log_row._meta.db_table, "vims_safety_soi_applicability_log")
        self.assertIsNone(log_row.dpa_decision)
