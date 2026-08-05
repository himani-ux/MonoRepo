from __future__ import annotations

import unittest

import django
from django.apps import apps
from django.core.management import call_command
from django.db import connection


def bootstrap_django() -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="safety-phase-0-5-seed-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "apps.safety",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
        )

    if not apps.ready:
        django.setup()


TABLE_DDL = (
    """
    CREATE TABLE IF NOT EXISTS master_mscat_taxonomy (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        legacy_int_id INTEGER UNIQUE,
        category_id INTEGER NOT NULL,
        category_name TEXT NOT NULL,
        subcode_id TEXT NOT NULL,
        subcode_description TEXT NOT NULL,
        cause_type TEXT NOT NULL,
        active INTEGER NOT NULL,
        seeded_version TEXT NOT NULL,
        schema_version INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS master_immediate_causes (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        legacy_int_id INTEGER UNIQUE,
        category_id INTEGER NOT NULL,
        category_name TEXT NOT NULL,
        subcode_id TEXT NOT NULL,
        subcode_description TEXT NOT NULL,
        cause_type TEXT NOT NULL,
        active INTEGER NOT NULL,
        seeded_version TEXT NOT NULL,
        schema_version INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS master_loss_types (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        legacy_int_id INTEGER UNIQUE,
        loss_type_id INTEGER NOT NULL,
        loss_type_name TEXT NOT NULL,
        description TEXT NOT NULL,
        active INTEGER NOT NULL,
        seeded_version TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS master_soi_area (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        legacy_int_id INTEGER UNIQUE,
        area_id INTEGER NOT NULL,
        area_name TEXT NOT NULL,
        section_12_flag INTEGER NOT NULL,
        display_order INTEGER NOT NULL,
        active INTEGER NOT NULL,
        seeded_version TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS master_soi_area_item (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        legacy_int_id INTEGER UNIQUE,
        area_id INTEGER NOT NULL,
        area_name TEXT NOT NULL,
        subsection_id INTEGER NOT NULL,
        subsection_name TEXT NOT NULL,
        item_number TEXT NOT NULL,
        description TEXT NOT NULL,
        tier TEXT NOT NULL,
        active INTEGER NOT NULL,
        seeded_version TEXT NOT NULL,
        schema_version INTEGER NOT NULL,
        updated_by TEXT NULL,
        updated_date TEXT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS master_soi_checklist_version (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        legacy_int_id INTEGER UNIQUE,
        version_label TEXT NOT NULL,
        effective_from TEXT NOT NULL,
        effective_to TEXT NULL,
        source_description TEXT NOT NULL,
        active INTEGER NOT NULL,
        created_by TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS master_safety_incident_type (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        legacy_int_id INTEGER UNIQUE,
        type_code TEXT NOT NULL,
        type_name TEXT NOT NULL,
        imo_reportable INTEGER NOT NULL,
        description TEXT NOT NULL,
        active INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS master_safety_bias_guard (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        legacy_int_id INTEGER UNIQUE,
        guard_code TEXT NOT NULL,
        guard_name TEXT NOT NULL,
        family TEXT NOT NULL,
        description TEXT NOT NULL,
        bit_position INTEGER NOT NULL,
        active INTEGER NOT NULL
    )
    """,
)

TABLE_NAMES = (
    "master_mscat_taxonomy",
    "master_immediate_causes",
    "master_loss_types",
    "master_soi_area",
    "master_soi_area_item",
    "master_soi_checklist_version",
    "master_safety_incident_type",
    "master_safety_bias_guard",
)


class SafetySeedMasterCommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()
        with connection.cursor() as cursor:
            for ddl in TABLE_DDL:
                cursor.execute(ddl)

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            for table_name in TABLE_NAMES:
                cursor.execute(f"DELETE FROM {table_name}")

    def _count_rows(self, table_name: str) -> int:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]

    def test_seed_master_safety_populates_all_reference_tables(self) -> None:
        call_command("seed_master_safety")

        self.assertEqual(self._count_rows("master_mscat_taxonomy"), 174)
        self.assertEqual(self._count_rows("master_immediate_causes"), 52)
        self.assertEqual(self._count_rows("master_loss_types"), 7)
        self.assertEqual(self._count_rows("master_soi_area"), 13)
        self.assertEqual(self._count_rows("master_soi_area_item"), 329)
        self.assertEqual(self._count_rows("master_soi_checklist_version"), 1)
        self.assertEqual(self._count_rows("master_safety_incident_type"), 32)
        self.assertEqual(self._count_rows("master_safety_bias_guard"), 8)

    def test_seed_master_safety_is_idempotent_on_rerun(self) -> None:
        call_command("seed_master_safety")
        call_command("seed_master_safety")

        self.assertEqual(self._count_rows("master_mscat_taxonomy"), 174)
        self.assertEqual(self._count_rows("master_immediate_causes"), 52)
        self.assertEqual(self._count_rows("master_loss_types"), 7)
        self.assertEqual(self._count_rows("master_soi_area"), 13)
        self.assertEqual(self._count_rows("master_soi_area_item"), 329)
        self.assertEqual(self._count_rows("master_soi_checklist_version"), 1)
        self.assertEqual(self._count_rows("master_safety_incident_type"), 32)
        self.assertEqual(self._count_rows("master_safety_bias_guard"), 8)
