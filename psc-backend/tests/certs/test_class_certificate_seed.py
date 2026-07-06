from __future__ import annotations

import unittest
from unittest.mock import MagicMock
import os
from contextlib import nullcontext

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from django.core.management import call_command

from apps.certs.class_certificate_seed import (
    CLASS_CERTIFICATE_ROWS,
    CLASS_SECTION_ID,
    seed_class_certificate_rows,
)


class CertClassCertificateSeedTests(unittest.TestCase):
    def test_class_certificate_seed_shape_matches_locked_phase_1_4_scope(self) -> None:
        codes = [row.canonical_code for row in CLASS_CERTIFICATE_ROWS]

        self.assertEqual(CLASS_SECTION_ID, 1)
        self.assertEqual(len(CLASS_CERTIFICATE_ROWS), 11)
        self.assertIn("CLASS-COC", codes)
        self.assertIn("CLASS-CG2", codes)
        self.assertIn("CLASS-LI", codes)
        self.assertIn("CLASS-NOTATIONS", codes)
        self.assertIn("CLASS-BOILER-SURVEY", codes)
        self.assertIn("CLASS-PROP-SHAFT-SURVEY", codes)
        self.assertIn("CLASS-DOCKING-SURVEY", codes)
        self.assertIn("CLASS-IWS-SURVEY", codes)

    def test_class_surveys_are_children_of_coc_with_master_only_scope(self) -> None:
        top_level_codes = {row.canonical_code for row in CLASS_CERTIFICATE_ROWS if row.parent_code is None}
        child_rows = [row for row in CLASS_CERTIFICATE_ROWS if row.parent_code]

        self.assertEqual(top_level_codes, {"CLASS-COC", "CLASS-CG2", "CLASS-LI", "CLASS-NOTATIONS"})
        self.assertTrue(child_rows)
        self.assertTrue(all(row.parent_code == "CLASS-COC" for row in child_rows))
        self.assertTrue(all(row.section_id == CLASS_SECTION_ID for row in CLASS_CERTIFICATE_ROWS))
        self.assertTrue(all(row.is_class_tracked for row in CLASS_CERTIFICATE_ROWS))
        self.assertTrue(all(row.submission_scope == "master_only" for row in CLASS_CERTIFICATE_ROWS))

    def test_iws_seed_carries_age_gate_without_overriding_ship_type(self) -> None:
        iws = next(row for row in CLASS_CERTIFICATE_ROWS if row.canonical_code == "CLASS-IWS-SURVEY")

        self.assertEqual(iws.age_gate_max_years, 15)
        self.assertEqual(iws.applicable_ship_types, ("all",))

    def test_seed_inserts_missing_rows_in_parent_first_order_and_audits_creates(self) -> None:
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        inserted_ids = iter((f"00000000-0000-0000-0000-0000000000{index:02d}",) for index in range(1, 12))
        cursor.fetchone.side_effect = inserted_ids

        result = seed_class_certificate_rows(cursor, actor_id="seed_class_certificates")

        self.assertEqual(result.created_count, 11)
        self.assertEqual(result.skipped_count, 0)
        self.assertEqual(result.created_codes[0], "CLASS-COC")
        insert_sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
        self.assertIn("INSERT INTO dbo.vims_certs_catalog_row", insert_sql)
        self.assertIn("INSERT INTO dbo.vims_certs_audit_log", insert_sql)
        coc_id = "00000000-0000-0000-0000-000000000001"
        child_insert_calls = [
            call for call in cursor.execute.call_args_list
            if "INSERT INTO dbo.vims_certs_catalog_row" in call.args[0] and "CLASS-ANNUAL-SURVEY" in call.args[1]
        ]
        self.assertEqual(child_insert_calls[0].args[1][11], coc_id)

    def test_seed_skips_existing_rows_without_writing_audit_noise(self) -> None:
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            (row.canonical_code, f"existing-{index}")
            for index, row in enumerate(CLASS_CERTIFICATE_ROWS, start=1)
        ]

        result = seed_class_certificate_rows(cursor, actor_id="seed_class_certificates")

        self.assertEqual(result.created_count, 0)
        self.assertEqual(result.skipped_count, 11)
        executed_sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
        self.assertNotIn("INSERT INTO dbo.vims_certs_catalog_row", executed_sql)
        self.assertNotIn("INSERT INTO dbo.vims_certs_audit_log", executed_sql)

    def test_management_command_uses_seed_helper(self) -> None:
        cursor = MagicMock()
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        with unittest.mock.patch("apps.certs.management.commands.seed_class_certificates.connection", connection), \
            unittest.mock.patch("apps.certs.management.commands.seed_class_certificates.transaction.atomic", return_value=nullcontext()), \
            unittest.mock.patch("apps.certs.management.commands.seed_class_certificates.seed_class_certificate_rows") as seed:
            seed.return_value.created_count = 2
            seed.return_value.skipped_count = 9
            seed.return_value.created_codes = ["CLASS-COC", "CLASS-ANNUAL-SURVEY"]

            call_command("seed_class_certificates")

        self.assertIn("OBJECT_ID", cursor.execute.call_args.args[0])
        seed.assert_called_once_with(cursor, actor_id="seed_class_certificates")
