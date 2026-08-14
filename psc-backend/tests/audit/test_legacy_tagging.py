from __future__ import annotations

import unittest

import django
from django.apps import apps
from django.db import connection


def bootstrap_django() -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-legacy-tagging-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "apps.accounts",
                "apps.masters",
                "apps.inspection",
                "apps.car",
                "apps.notifications",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        )

    if not apps.ready:
        django.setup()


bootstrap_django()

from apps.inspection.audit.services.legacy_tagging import tag_legacy_audit_inspections  # noqa: E402


class AuditLegacyTaggingTests(unittest.TestCase):
    def setUp(self) -> None:
        bootstrap_django()
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS audit_legacy_inspection_tag")
            cursor.execute("DROP TABLE IF EXISTS psc_inspection")
            cursor.execute(
                """
                CREATE TABLE psc_inspection (
                    id TEXT PRIMARY KEY,
                    inspection_type TEXT NOT NULL,
                    created_date TEXT NOT NULL,
                    untouched_marker TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE audit_legacy_inspection_tag (
                    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
                    psc_inspection_id TEXT NOT NULL UNIQUE,
                    is_legacy INTEGER NOT NULL DEFAULT 1,
                    tagged_at TEXT NOT NULL,
                    tagged_by TEXT NOT NULL,
                    tag_reason TEXT NULL
                )
                """
            )

    def test_zero_row_probe_writes_no_tags(self) -> None:
        _insert_inspection(PSC_ID, "PSC", marker="keep-psc")

        result = tag_legacy_audit_inspections(apply=True)

        self.assertEqual(result.discovered, 0)
        self.assertEqual(result.inserted, 0)
        self.assertEqual(_count_rows("audit_legacy_inspection_tag"), 0)
        self.assertEqual(_source_markers(), [(PSC_ID, "keep-psc")])

    def test_dry_run_discovers_but_writes_no_tags(self) -> None:
        _insert_inspection(AUDIT_ID, "AUDIT", marker="keep-audit")
        _insert_inspection(RS_ID, "RS", marker="keep-rs")

        result = tag_legacy_audit_inspections(apply=False)

        self.assertEqual(result.discovered, 2)
        self.assertEqual(result.inserted, 0)
        self.assertTrue(result.dry_run)
        self.assertEqual(_count_rows("audit_legacy_inspection_tag"), 0)
        self.assertEqual(_source_markers(), [(AUDIT_ID, "keep-audit"), (RS_ID, "keep-rs")])

    def test_apply_inserts_only_audit_owned_tags_and_is_idempotent(self) -> None:
        _insert_inspection(AUDIT_ID, "AUDIT", marker="keep-audit")
        _insert_inspection(RS_ID, "RS", marker="keep-rs")
        _insert_inspection(PSC_ID, "PSC", marker="keep-psc")

        first = tag_legacy_audit_inspections(apply=True, tagged_by="migration-test")
        second = tag_legacy_audit_inspections(apply=True, tagged_by="migration-test")

        self.assertEqual(first.discovered, 2)
        self.assertEqual(first.already_tagged, 0)
        self.assertEqual(first.inserted, 2)
        self.assertFalse(first.dry_run)
        self.assertEqual(second.discovered, 2)
        self.assertEqual(second.already_tagged, 2)
        self.assertEqual(second.inserted, 0)
        self.assertEqual(
            _tag_rows(),
            [
                (AUDIT_ID, 1, "migration-test", "pre-deploy AUDIT/RS row"),
                (RS_ID, 1, "migration-test", "pre-deploy AUDIT/RS row"),
            ],
        )
        self.assertEqual(
            _source_markers(),
            [(AUDIT_ID, "keep-audit"), (RS_ID, "keep-rs"), (PSC_ID, "keep-psc")],
        )


def _insert_inspection(inspection_id: str, inspection_type: str, *, marker: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO psc_inspection (id, inspection_type, created_date, untouched_marker) "
            "VALUES (%s, %s, %s, %s)",
            [inspection_id, inspection_type, "2026-08-01T00:00:00+00:00", marker],
        )


def _count_rows(table_name: str) -> int:
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]


def _tag_rows() -> list[tuple[str, int, str, str]]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT psc_inspection_id, is_legacy, tagged_by, tag_reason "
            "FROM audit_legacy_inspection_tag ORDER BY psc_inspection_id"
        )
        return list(cursor.fetchall())


AUDIT_ID = "a" * 32
RS_ID = "b" * 32
PSC_ID = "c" * 32


def _source_markers() -> list[tuple[str, str]]:
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, untouched_marker FROM psc_inspection ORDER BY id")
        return list(cursor.fetchall())
