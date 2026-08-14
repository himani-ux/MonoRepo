from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import django
from django.apps import apps
from django.core.management.base import CommandError
from django.db import connection

from apps.inspection.audit.seeds.runner import (
    SEED_TABLE_SPECS,
    read_seed_rows,
    seed_audit_masters,
    upsert_rows,
)


def bootstrap_django() -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-seed-runner-test-secret-key-1234567890",
            INSTALLED_APPS=[],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
        )

    if not apps.ready:
        django.setup()


def _handover_seed_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "audit_docsuite" / "seeds"


def _spec(csv_name: str):
    for seed_spec in SEED_TABLE_SPECS:
        if seed_spec.csv_name == csv_name:
            return seed_spec
    raise AssertionError(f"Missing seed spec for {csv_name}")


class AuditSeedRunnerTests(unittest.TestCase):
    def test_rejects_mismatched_csv_header(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            seed_dir = Path(temp_dir)
            (seed_dir / "master_audit_area.csv").write_text(
                "area_code,display_name,sequence_no\n"
                "NAV,Navigation,1\n",
                encoding="utf-8",
            )

            with self.assertRaises(CommandError) as raised:
                read_seed_rows(_spec("master_audit_area.csv"), seed_dir)

        self.assertIn("header mismatch", str(raised.exception))

    def test_dry_run_uses_documented_load_order_and_counts(self) -> None:
        summary = seed_audit_masters(seed_dir=_handover_seed_dir(), dry_run=True)

        self.assertEqual([spec.table_name for spec in SEED_TABLE_SPECS], list(summary))
        self.assertEqual(summary["master_audit_area"]["total"], 14)
        self.assertEqual(summary["master_audit_checklist"]["total"], 6)
        self.assertEqual(summary["master_audit_checklist_item"]["total"], 785)
        self.assertEqual(summary["master_rca_template"]["total"], 25)

    def test_checklist_item_resolution_requires_known_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            seed_dir = Path(temp_dir)
            (seed_dir / "master_audit_checklist_item.csv").write_text(
                "checklist_code,location_code,item_code,question,guideline,"
                "regulation_ref,ksm_sms_ref,ship_type,sequence_no\n"
                "MISSING,10,1000,Question,,,,Common,1\n",
                encoding="utf-8",
            )

            with self.assertRaises(CommandError) as raised:
                read_seed_rows(
                    _spec("master_audit_checklist_item.csv"),
                    seed_dir,
                    checklist_codes={"F605"},
                )

        self.assertIn("unknown checklist_code MISSING", str(raised.exception))

    def test_upsert_rows_inserts_then_updates_without_supplying_id(self) -> None:
        bootstrap_django()
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS master_audit_area")
            cursor.execute(
                """
                CREATE TABLE master_audit_area (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    area_code TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    is_vessel_only INTEGER NOT NULL,
                    sequence_no INTEGER NOT NULL
                )
                """
            )

            first = upsert_rows(
                cursor=cursor,
                table_name="master_audit_area",
                key_columns=("area_code",),
                columns=("area_code", "display_name", "is_vessel_only", "sequence_no"),
                rows=[
                    {
                        "area_code": "NAV",
                        "display_name": "Navigation",
                        "is_vessel_only": True,
                        "sequence_no": 1,
                    }
                ],
            )
            cursor.execute("SELECT id, display_name FROM master_audit_area WHERE area_code = %s", ["NAV"])
            generated_id, display_name = cursor.fetchone()

            second = upsert_rows(
                cursor=cursor,
                table_name="master_audit_area",
                key_columns=("area_code",),
                columns=("area_code", "display_name", "is_vessel_only", "sequence_no"),
                rows=[
                    {
                        "area_code": "NAV",
                        "display_name": "Navigation Procedures",
                        "is_vessel_only": True,
                        "sequence_no": 1,
                    }
                ],
            )
            cursor.execute("SELECT COUNT(*), id, display_name FROM master_audit_area GROUP BY id, display_name")
            count, rerun_id, rerun_display_name = cursor.fetchone()

        self.assertEqual(first, {"inserted": 1, "updated": 0, "total": 1})
        self.assertEqual(second, {"inserted": 0, "updated": 1, "total": 1})
        self.assertEqual(count, 1)
        self.assertEqual(display_name, "Navigation")
        self.assertEqual(rerun_id, generated_id)
        self.assertEqual(rerun_display_name, "Navigation Procedures")
