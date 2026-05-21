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
        self.assertEqual(len(load_incident_type_rows()), 11)
        self.assertEqual(len(load_bias_guard_rows()), 8)
        self.assertEqual(len(load_soi_checklist_version_rows()), 1)
