from __future__ import annotations

import os
import unittest
import uuid

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from apps.certs.services.coverage import compute_mandatory_coverage_from_rows


def catalog_row(**overrides):
    row = {
        "catalog_id": "catalog-iopp",
        "canonical_code": "STAT-IOPP",
        "display_name": "International Oil Pollution Prevention Certificate",
        "short_name": "IOPP",
        "section_id": 2,
        "section_code": "STATUTORY",
        "section_name": "Statutory & Flag",
        "applicable_ship_types": '["all"]',
        "mandatory_for_all_vessels": True,
        "applicability_mode": "all_matching_type",
        "specific_vessel_ids": None,
        "is_active": True,
    }
    row.update(overrides)
    return row


def tracked_row(**overrides):
    row = {
        "tracked_item_id": "tracked-iopp",
        "catalog_id": "catalog-iopp",
        "status": "ok",
        "pdf_missing": True,
    }
    row.update(overrides)
    return row


class CertMandatoryCoverageTests(unittest.TestCase):
    def test_coverage_uses_catalog_denominator_and_lists_uncreated_mandatory_rows(self) -> None:
        result = compute_mandatory_coverage_from_rows(
            vessel_id="vessel-1",
            ship_type="bulk_carrier",
            catalog_rows=[
                catalog_row(catalog_id="catalog-iopp", canonical_code="STAT-IOPP"),
                catalog_row(catalog_id="catalog-loadline", canonical_code="STAT-LOADLINE"),
                catalog_row(
                    catalog_id="catalog-tanker-only",
                    canonical_code="STAT-TANKER",
                    applicable_ship_types='["tanker"]',
                ),
            ],
            tracked_rows=[
                tracked_row(catalog_id="catalog-iopp", status="ok", pdf_missing=True),
            ],
            config={"mandatory_coverage_override_reason": None},
        )

        self.assertEqual(result["mandatoryCount"], 2)
        self.assertEqual(result["coveredCount"], 1)
        self.assertEqual(result["percent"], 50.0)
        self.assertEqual(result["missing"][0]["catalogId"], "catalog-loadline")
        self.assertIsNone(result["missing"][0]["trackedItemId"])
        self.assertEqual(result["missing"][0]["reason"], "missing_tracked_item")

    def test_coverage_override_is_inactive_once_coverage_reaches_100_percent(self) -> None:
        result = compute_mandatory_coverage_from_rows(
            vessel_id="vessel-1",
            ship_type="bulk_carrier",
            catalog_rows=[catalog_row(catalog_id="catalog-iopp")],
            tracked_rows=[tracked_row(catalog_id="catalog-iopp", status="ok")],
            config={
                "mandatory_coverage_override_reason": "Pending original to arrive by courier.",
                "mandatory_coverage_override_at": "2026-06-26T10:00:00Z",
                "mandatory_coverage_override_by": "dpa-1",
            },
        )

        self.assertEqual(result["percent"], 100.0)
        self.assertFalse(result["overrideActive"])

    def test_superseded_rollback_rows_do_not_satisfy_mandatory_coverage(self) -> None:
        catalog_id = str(uuid.uuid4())
        result = compute_mandatory_coverage_from_rows(
            vessel_id="vessel-1",
            ship_type="bulk_carrier",
            catalog_rows=[catalog_row(catalog_id=catalog_id)],
            tracked_rows=[
                {
                    "tracked_item_id": str(uuid.uuid4()),
                    "catalog_id": catalog_id,
                    "status": "superseded",
                    "lifecycle_status": "onboarding_quarantine",
                }
            ],
            config={},
        )

        self.assertEqual(result["percent"], 0.0)
        self.assertEqual(result["missing"][0]["reason"], "pending_first_upload")

    def test_specific_vessel_catalog_rows_count_only_for_that_vessel(self) -> None:
        result = compute_mandatory_coverage_from_rows(
            vessel_id="vessel-1",
            ship_type="bulk_carrier",
            catalog_rows=[
                catalog_row(
                    catalog_id="catalog-specific",
                    canonical_code="STAT-SPECIAL",
                    applicable_ship_types='["tanker"]',
                    applicability_mode="specific_vessel_ids",
                    specific_vessel_ids='["vessel-1"]',
                ),
                catalog_row(
                    catalog_id="catalog-other-vessel",
                    canonical_code="STAT-OTHER",
                    applicability_mode="specific_vessel_ids",
                    specific_vessel_ids='["vessel-2"]',
                ),
            ],
            tracked_rows=[],
            config={},
        )

        self.assertEqual(result["mandatoryCount"], 1)
        self.assertEqual(result["missing"][0]["catalogCode"], "STAT-SPECIAL")


if __name__ == "__main__":
    unittest.main()
