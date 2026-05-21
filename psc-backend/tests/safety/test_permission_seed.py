from __future__ import annotations

import importlib
import unittest

import django
from django.apps import apps
from django.db import connection


def bootstrap_django() -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="safety-phase-0-6-permission-test-secret-key-1234567890",
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


class SafetyPermissionSeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()
        cls.migration_module = importlib.import_module("apps.safety.migrations.0003_seed_permission_ids")
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS msc_profiles_catalog (
                    code TEXT PRIMARY KEY,
                    label TEXT NOT NULL,
                    kind TEXT NOT NULL
                )
                """
            )

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM msc_profiles_catalog")

    def _count_rows(self) -> int:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM msc_profiles_catalog")
            return cursor.fetchone()[0]

    def test_permission_seed_inserts_form_and_process_catalog_rows(self) -> None:
        with connection.schema_editor() as schema_editor:
            self.migration_module.seed_permission_catalog(None, schema_editor)

        self.assertEqual(self._count_rows(), 44)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT label, kind FROM msc_profiles_catalog WHERE code = %s",
                ["SAF_F_001"],
            )
            self.assertEqual(cursor.fetchone(), ("SAFETY_INCIDENT", "form"))
            cursor.execute(
                "SELECT label, kind FROM msc_profiles_catalog WHERE code = %s",
                ["SAF_P_004"],
            )
            self.assertEqual(cursor.fetchone(), ("SAFETY_APPROVE_CLOSE", "process"))

    def test_permission_seed_is_idempotent(self) -> None:
        with connection.schema_editor() as schema_editor:
            self.migration_module.seed_permission_catalog(None, schema_editor)
            self.migration_module.seed_permission_catalog(None, schema_editor)

        self.assertEqual(self._count_rows(), 44)
