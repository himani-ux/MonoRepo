from __future__ import annotations

import unittest

from apps.certs.catalog_section_seed import CATALOG_SECTIONS


class CertCatalogSectionSeedTests(unittest.TestCase):
    def test_catalog_section_seed_has_nine_canonical_sections_in_print_order(self) -> None:
        self.assertEqual(len(CATALOG_SECTIONS), 9)
        self.assertEqual([section.section_id for section in CATALOG_SECTIONS], list(range(1, 10)))
        self.assertEqual([section.sort_order for section in CATALOG_SECTIONS], list(range(1, 10)))
        self.assertEqual(
            [section.section_code for section in CATALOG_SECTIONS],
            [
                "CLASS",
                "STATUTORY",
                "TRADE",
                "EQUIPMENT",
                "CALIBRATIONS",
                "TESTS",
                "TYPE_APPROVAL",
                "APPROVED_PLANS",
                "MISC",
            ],
        )

    def test_catalog_section_seed_preserves_d_cert_017_labels(self) -> None:
        self.assertEqual(
            [section.display_name for section in CATALOG_SECTIONS],
            [
                "Class Certificates",
                "Statutory & Flag",
                "Trade & Commercial",
                "Equipment LSA/FFA/Nav/GMDSS",
                "Calibrations",
                "Tests & Analyses",
                "Type Approvals",
                "Approved Plans",
                "Other/Misc",
            ],
        )

