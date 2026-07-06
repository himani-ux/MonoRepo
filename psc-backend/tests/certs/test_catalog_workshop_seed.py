from __future__ import annotations

from contextlib import nullcontext
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from django.core.management import CommandError, call_command

from apps.certs.catalog_workshop_seed import (
    CatalogWorkshopSeedRow,
    load_catalog_workshop_rows,
    seed_certs_catalog_rows,
)


def workshop_row(**overrides) -> CatalogWorkshopSeedRow:
    values = {
        "canonical_code": "STAT-IOPP",
        "section_id": 2,
        "display_name": "International Oil Pollution Prevention Certificate",
        "short_name": "IOPP",
        "print_section_label": "Statutory & Flag",
        "validity_type": "full",
        "cadence_months": 60,
        "cadence_custom_days": None,
        "issuing_authority_type": "flag",
        "is_class_tracked": False,
        "submission_scope": "master_only",
        "parent_canonical_code": None,
        "relationship_type_default": None,
        "applicable_ship_types": ("all",),
        "mandatory_for_all_vessels": True,
        "applicability_mode": "all_matching_type",
        "specific_vessel_ids": (),
        "parent_supports_dynamic_children": False,
        "age_gate_max_years": None,
        "retain_all_versions": False,
        "linked_pms_component_id": None,
        "alert_lead_overrides": None,
        "regulatory_anchor": "MARPOL Annex I Reg 7",
        "legacy_remarks": "Workshop approved row.",
        "print_order": 120,
        "is_active": True,
    }
    values.update(overrides)
    return CatalogWorkshopSeedRow(**values)


class CertCatalogWorkshopSeedTests(unittest.TestCase):
    def test_loader_requires_final_workshop_columns(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as handle:
            handle.write("display_name,section_id\nIOPP,2\n")
            path = handle.name

        with self.assertRaises(ValueError) as raised:
            load_catalog_workshop_rows(path)

        self.assertIn("missing required column", str(raised.exception))

    def test_seed_dry_run_does_not_insert_or_audit(self) -> None:
        cursor = MagicMock()
        cursor.fetchall.return_value = []

        result = seed_certs_catalog_rows(
            cursor,
            [workshop_row()],
            actor_id="seed_certs_catalog",
            approval_ref="DPA workshop approval pending",
            dry_run=True,
        )

        self.assertEqual(result.would_create_count, 1)
        self.assertEqual(result.created_count, 0)
        executed_sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
        self.assertNotIn("INSERT INTO dbo.vims_certs_catalog_row", executed_sql)
        self.assertNotIn("INSERT INTO dbo.vims_certs_audit_log", executed_sql)

    def test_seed_inserts_missing_rows_and_records_create_audit(self) -> None:
        cursor = MagicMock()
        cursor.fetchall.return_value = []
        cursor.fetchone.return_value = ("00000000-0000-0000-0000-000000000101",)

        result = seed_certs_catalog_rows(
            cursor,
            [workshop_row()],
            actor_id="seed_certs_catalog",
            approval_ref="DPA-TechSuppt-2026-06-25",
            dry_run=False,
        )

        self.assertEqual(result.created_count, 1)
        self.assertEqual(result.skipped_count, 0)
        executed_sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
        self.assertIn("INSERT INTO dbo.vims_certs_catalog_row", executed_sql)
        self.assertIn("INSERT INTO dbo.vims_certs_audit_log", executed_sql)
        audit_call = [
            call for call in cursor.execute.call_args_list
            if "INSERT INTO dbo.vims_certs_audit_log" in call.args[0]
        ][0]
        self.assertEqual(audit_call.args[1][2], "create_catalog_row")
        self.assertIn("DPA-TechSuppt-2026-06-25", audit_call.args[1][7])

    def test_seed_can_reference_existing_parent_outside_workshop_csv(self) -> None:
        cursor = MagicMock()
        cursor.fetchall.return_value = [("CLASS-COC", "00000000-0000-0000-0000-000000000001")]
        cursor.fetchone.return_value = ("00000000-0000-0000-0000-000000000102",)

        result = seed_certs_catalog_rows(
            cursor,
            [
                workshop_row(
                    canonical_code="CLASS-ANNUAL-SURVEY-EXTRA",
                    section_id=1,
                    display_name="Class Annual Survey Extra",
                    print_section_label="Class Certificates",
                    parent_canonical_code="CLASS-COC",
                    relationship_type_default="survey_of",
                    issuing_authority_type="class",
                    is_class_tracked=True,
                )
            ],
            actor_id="seed_certs_catalog",
            approval_ref="DPA-TechSuppt-2026-06-25",
            dry_run=False,
        )

        self.assertEqual(result.created_count, 1)
        insert_call = [
            call for call in cursor.execute.call_args_list
            if "INSERT INTO dbo.vims_certs_catalog_row" in call.args[0]
        ][0]
        self.assertEqual(insert_call.args[1][11], "00000000-0000-0000-0000-000000000001")

    def test_management_command_requires_approval_for_apply(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as handle:
            handle.write(
                "canonical_code,section_id,display_name,print_section_label,validity_type,"
                "issuing_authority_type,submission_scope,print_order\n"
                "STAT-IOPP,2,International Oil Pollution Prevention Certificate,Statutory & Flag,"
                "full,flag,master_only,120\n"
            )
            path = handle.name

        with self.assertRaises(CommandError) as raised:
            call_command("seed_certs_catalog", "--input", path, "--apply")

        self.assertIn("--approved-by", str(raised.exception))

    def test_management_command_dry_run_uses_seed_helper_without_apply(self) -> None:
        cursor = MagicMock()
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="") as handle:
            handle.write(
                "canonical_code,section_id,display_name,print_section_label,validity_type,"
                "issuing_authority_type,submission_scope,print_order\n"
                "STAT-IOPP,2,International Oil Pollution Prevention Certificate,Statutory & Flag,"
                "full,flag,master_only,120\n"
            )
            path = handle.name

        with patch("apps.certs.management.commands.seed_certs_catalog.connection", connection), \
            patch("apps.certs.management.commands.seed_certs_catalog.transaction.atomic", return_value=nullcontext()), \
            patch("apps.certs.management.commands.seed_certs_catalog.seed_certs_catalog_rows") as seed:
            seed.return_value.created_count = 0
            seed.return_value.skipped_count = 0
            seed.return_value.would_create_count = 1
            seed.return_value.would_skip_count = 0

            call_command("seed_certs_catalog", "--input", path)

        seed.assert_called_once()
        self.assertTrue(seed.call_args.kwargs["dry_run"])


if __name__ == "__main__":
    unittest.main()
