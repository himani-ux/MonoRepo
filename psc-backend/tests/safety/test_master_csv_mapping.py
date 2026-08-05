from __future__ import annotations

import unittest

from apps.safety.management.commands.seed_master_safety import (
    CSV_HEADER_MAP,
    load_bias_guard_rows,
    load_incident_type_rows,
    load_soi_area_rows,
    load_soi_area_item_rows,
    load_soi_checklist_version_rows,
    read_csv_rows,
)

EXPECTED_INCIDENT_TYPE_NAMES = [
    "Collision",
    "Grounding",
    "Stranding",
    "Touched bottom at berth / anchorage",
    "Touched bottom in rivers / canals",
    "Allision with Jetty / Berth / Locks",
    "Allision with other Vessels",
    "Allision with ice",
    "Allision with Navigation Aids / Buoys / Other objects",
    "Foundering",
    "Capsizing / Loss of Stability",
    "Flooding",
    "Explosion",
    "Fire",
    "Cargo Damage",
    "Hull / Structural Failure",
    "The fouling or damaging by a vessel of a pipeline or submarine cable",
    "The fouling or damaging by a vessel of an aid to navigation other than allision",
    "The fouling or damaging by a vessel of a port/terminal installation",
    "Failure of ship's equipment resulting in loss of vessel's electrical power",
    "Failure of ship's equipment resulting in loss of propulsion",
    "Failure of ship's equipment resulting in loss of steering capabilities",
    "Failure of ship's equipment resulting in a delay of cargo operation of more than 6 hours",
    "Failure of ship's equipment rendering the vessel in any other way unseaworthy",
    "Failure of ship's equipment or hull resulting in cargo damage",
    "Crew Injury",
    "Pollution",
    "Breach of Local Regulations",
    "Stowaway Incident",
    "Security Incident",
    "Breach of Cyber Security",
    "Other",
]


class SafetyMasterCsvMappingTests(unittest.TestCase):
    def test_locked_csv_headers_are_respected(self) -> None:
        for filename, expected_headers in CSV_HEADER_MAP.items():
            rows = read_csv_rows(filename)
            self.assertGreater(len(rows), 0, filename)
            self.assertEqual(tuple(rows[0].keys()), expected_headers)

    def test_soi_checklist_csv_maps_to_expected_row_count(self) -> None:
        rows = load_soi_area_item_rows()
        self.assertEqual(len(rows), 329)

    def test_fixture_payload_counts_match_docs(self) -> None:
        self.assertEqual(len(load_soi_area_rows()), 13)
        incident_type_rows = load_incident_type_rows()
        self.assertEqual(len(incident_type_rows), 32)
        self.assertEqual(
            [row["type_name"] for row in incident_type_rows],
            EXPECTED_INCIDENT_TYPE_NAMES,
        )
        self.assertNotIn(
            "IMO_MISSING_VESSEL",
            {row["type_code"] for row in incident_type_rows},
        )
        self.assertEqual(len(load_bias_guard_rows()), 8)
        self.assertEqual(len(load_soi_checklist_version_rows()), 1)
