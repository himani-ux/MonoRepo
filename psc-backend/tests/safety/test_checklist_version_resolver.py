from __future__ import annotations

from datetime import datetime, timezone
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection

from apps.safety.services.checklist_version_resolver import ChecklistVersionResolutionError, ChecklistVersionResolver


class ChecklistVersionResolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()

    def test_active_version_uses_current_effective_window(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE master_soi_checklist_version
                SET active = 0, effective_to = %s
                WHERE version_label = %s
                """,
                ["2026-05-15", "v1.0"],
            )
            cursor.execute(
                """
                INSERT INTO master_soi_checklist_version (
                    version_label,
                    effective_from,
                    effective_to,
                    source_description,
                    active,
                    created_by,
                    created_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "v2.0",
                    "2026-05-16",
                    None,
                    "Section 12 refresh",
                    True,
                    "dpa-1",
                    "2026-05-16 00:00:00",
                ],
            )

        resolver = ChecklistVersionResolver(clock=lambda: datetime(2026, 5, 20, tzinfo=timezone.utc))
        version = resolver.get_active_version()

        self.assertEqual(version.version_label, "v2.0")
        self.assertEqual(version.source_description, "Section 12 refresh")

    def test_missing_active_version_raises_clear_error(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM master_soi_checklist_version")

        resolver = ChecklistVersionResolver(clock=lambda: datetime(2026, 5, 20, tzinfo=timezone.utc))

        with self.assertRaises(ChecklistVersionResolutionError):
            resolver.get_active_version()
