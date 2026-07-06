from __future__ import annotations

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from apps.certs.services.parsers import ClassSnapshotParseError, parse_class_snapshot_pdf
from apps.certs.services.reconciliation import build_reconciliation_flags


BACKEND_ROOT = Path(__file__).resolve().parents[2]
HANDOVER_ROOT = BACKEND_ROOT.parents[1]
CORPUS_ROOT = HANDOVER_ROOT / "reference-packs" / "Class-Reference-Reports"
EXPECTED_PATH = Path(__file__).resolve().parent / "fixtures" / "class_snapshot_corpus_expected.json"


class CertClassSnapshotParserCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))

    def test_six_reference_pdfs_parse_with_pdfplumber_text_extraction_only(self) -> None:
        self.assertEqual(len(self.expected), 6)
        for expected in self.expected:
            with self.subTest(filename=expected["filename"]):
                path = CORPUS_ROOT / expected["filename"]
                self.assertTrue(path.exists(), f"missing parser corpus PDF: {path}")

                parsed = parse_class_snapshot_pdf(path, expected["classSociety"])
                payload = parsed.payload

                self.assertEqual(payload["source"], "pdfplumber_text")
                self.assertEqual(payload["class_society"], expected["classSociety"])
                self.assertEqual(payload["vessel"]["name"], expected["vesselName"])
                self.assertEqual(payload["vessel"]["imo"], expected["imo"])
                self.assertEqual(payload["printed_on_date"], expected["printedOnDate"])
                self.assertGreaterEqual(len(payload["rows"]), expected["minRows"])
                self.assertEqual(len(payload["conditions_of_class"]), expected["conditionsCount"])
                self.assertGreater(payload["text_extraction"]["char_count"], 10000)

                row_names = {row["class_code_or_name"] for row in payload["rows"]}
                for class_code_or_name in expected["mustInclude"]:
                    self.assertIn(class_code_or_name, row_names)

                if expected["classSociety"] == "KR":
                    self.assertIn("Annual Survey", row_names)
                    self.assertNotIn("Ship Name", " ".join(row_names))
                    self.assertNotIn("Work ID", " ".join(row_names))

                raw_text = "\n".join(str(row.get("raw_text") or "") for row in payload["rows"])
                self.assertNotIn("Paris MoU", raw_text)
                self.assertNotIn("Tokyo MoU", raw_text)
                self.assertNotIn("PSC Regime", raw_text)

    def test_class_snapshot_parser_has_no_ocr_fallback(self) -> None:
        with patch.dict("sys.modules", {"pdfplumber": None}):
            with self.assertRaisesRegex(ClassSnapshotParseError, "pdfplumber is required"):
                parse_class_snapshot_pdf(CORPUS_ROOT / self.expected[0]["filename"], self.expected[0]["classSociety"])

    def test_phase_4_exit_gate_parses_and_reconciles_all_reference_snapshots(self) -> None:
        self.assertEqual(len(self.expected), 6)
        for expected in self.expected:
            with self.subTest(filename=expected["filename"]):
                path = CORPUS_ROOT / expected["filename"]
                parsed = parse_class_snapshot_pdf(path, expected["classSociety"])
                payload = parsed.payload
                expected_rows = [
                    row
                    for row in payload["rows"]
                    if row.get("class_code_or_name") in set(expected["mustInclude"])
                ]
                self.assertEqual(len(expected_rows), len(expected["mustInclude"]))

                tracked_items = []
                mappings = []
                for index, row in enumerate(expected_rows, start=1):
                    catalog_id = f"{expected['imo']}-catalog-{index}"
                    tracked_item_id = f"{expected['imo']}-tracked-{index}"
                    mappings.append(
                        {
                            "class_code_or_name": row["class_code_or_name"],
                            "catalog_id": catalog_id,
                            "version": 1,
                        }
                    )
                    tracked_items.append(
                        {
                            "tracked_item_id": tracked_item_id,
                            "catalog_id": catalog_id,
                            "catalog_is_class_tracked": True,
                            "certificate_number": row.get("certificate_number"),
                            "issue_date": row.get("issue_date"),
                            "expiry_date": row.get("expiry_date"),
                            "last_done_date": row.get("last_done_date"),
                            "next_due_date": row.get("next_due_date"),
                            "postponed_until": row.get("postponed_until"),
                        }
                    )

                result = build_reconciliation_flags(
                    parsed_payload={"schema_version": payload["schema_version"], "rows": expected_rows},
                    tracked_items=tracked_items,
                    mappings=mappings,
                )

                reconciled_expected_rows = (
                    result.counts["matches_count"]
                    + result.counts["conditional_stc_detected_count"]
                    + result.counts["extended_postponed_detected_count"]
                )
                self.assertEqual(reconciled_expected_rows, len(expected_rows))
                self.assertEqual(result.counts["mismatches_count"], 0)
                self.assertEqual(result.counts["missing_in_catalog_count"], 0)
                self.assertEqual(result.counts["missing_in_class_count"], 0)
                self.assertEqual(result.counts["unmapped_low_confidence_count"], 0)
                self.assertEqual(result.anomaly_breaches, [])


if __name__ == "__main__":
    unittest.main()
