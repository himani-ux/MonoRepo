from __future__ import annotations

import unittest
from importlib import import_module

from apps.certs import iopp_variant


class CertIoppVariantTests(unittest.TestCase):
    def test_detects_catalog_codes_that_try_to_split_iopp_form_variants(self) -> None:
        self.assertTrue(iopp_variant.is_iopp_variant_catalog_code("STAT-IOPP-A"))
        self.assertTrue(iopp_variant.is_iopp_variant_catalog_code("STAT-IOPP-B"))
        self.assertFalse(iopp_variant.is_iopp_variant_catalog_code("STAT-IOPP"))
        self.assertFalse(iopp_variant.is_iopp_variant_catalog_code("CLASS-ANNUAL-SURVEY"))

    def test_normalizes_tracked_item_form_variant_values(self) -> None:
        self.assertEqual(iopp_variant.normalize_form_variant("a"), "A")
        self.assertEqual(iopp_variant.normalize_form_variant("B"), "B")
        self.assertEqual(iopp_variant.normalize_form_variant("N/A"), "n/a")
        self.assertEqual(iopp_variant.normalize_form_variant(None), "n/a")

    def test_rejects_unknown_form_variant_values(self) -> None:
        with self.assertRaises(ValueError):
            iopp_variant.normalize_form_variant("C")

    def test_migration_adds_iopp_catalog_and_form_variant_constraints(self) -> None:
        migration_module = import_module("apps.certs.migrations.0002_iopp_variant_constraints")
        combined_sql = "\n".join(statement for _, _, statement in migration_module.CONSTRAINT_SQL)

        self.assertIn("ck_vims_certs_tracked_item_form_variant", combined_sql)
        self.assertIn("form_variant IN (N'A', N'B', N'n/a')", combined_sql)
        self.assertIn("ck_vims_certs_catalog_row_no_iopp_variant_code", combined_sql)
        self.assertIn("UPPER(canonical_code) NOT LIKE N'%-IOPP-A'", combined_sql)


if __name__ == "__main__":
    unittest.main()
