from __future__ import annotations

from datetime import datetime, timezone
import os
import unittest
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from apps.certs.jobs.blob_retention_sweeper import run_blob_retention_sweeper
from apps.certs.services.pdf_blob_repository import PdfBlobRepository


class PdfBlobRetentionSchedulingTests(unittest.TestCase):
    @patch("apps.certs.services.pdf_blob_repository.connection")
    def test_superseded_class_or_statutory_blob_is_scheduled_for_immediate_delete(self, connection) -> None:
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor

        PdfBlobRepository().mark_blob_superseded_for_retention(
            blob_id="old-blob",
            section_code="STATUTORY",
            is_class_tracked=False,
            retain_all_versions=False,
        )

        sql_text = "\n".join(str(call.args[0]) for call in cursor.execute.call_args_list)
        params = cursor.execute.call_args.args[1]
        self.assertIn("UPDATE dbo.vims_certs_pdf_blob", sql_text)
        self.assertIn("immediate_delete_on_supersede", params)
        self.assertIn("scheduled_delete_at = SYSUTCDATETIME()", sql_text)
        self.assertIn("is_active = 0", sql_text)
        self.assertIn("superseded_at = COALESCE", sql_text)

    @patch("apps.certs.services.pdf_blob_repository.connection")
    def test_superseded_non_statutory_blob_gets_eighteen_month_schedule(self, connection) -> None:
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor

        PdfBlobRepository().mark_blob_superseded_for_retention(
            blob_id="old-blob",
            section_code="PLANS",
            is_class_tracked=False,
            retain_all_versions=False,
        )

        sql_text = "\n".join(str(call.args[0]) for call in cursor.execute.call_args_list)
        params = cursor.execute.call_args.args[1]
        self.assertIn("retain_18_months_then_purge", params)
        self.assertIn("DATEADD(month, 18, SYSUTCDATETIME())", sql_text)

    @patch("apps.certs.services.pdf_blob_repository.connection")
    def test_retain_all_versions_blob_has_no_delete_schedule(self, connection) -> None:
        cursor = MagicMock()
        connection.cursor.return_value.__enter__.return_value = cursor

        PdfBlobRepository().mark_blob_superseded_for_retention(
            blob_id="csr-blob",
            section_code="STATUTORY",
            is_class_tracked=False,
            retain_all_versions=True,
        )

        sql_text = "\n".join(str(call.args[0]) for call in cursor.execute.call_args_list)
        params = cursor.execute.call_args.args[1]
        self.assertIn("retain_all_versions", params)
        self.assertIn("scheduled_delete_at = NULL", sql_text)


class BlobRetentionSweeperTests(unittest.TestCase):
    @patch("apps.certs.jobs.blob_retention_sweeper.connection")
    def test_sweeper_soft_marks_due_inactive_blobs_and_records_audit(self, connection) -> None:
        cursor = MagicMock()
        cursor.rowcount = 2
        cursor.fetchall.return_value = []
        connection.cursor.return_value.__enter__.return_value = cursor
        connection.introspection.table_names.return_value = ["vims_certs_pdf_blob", "vims_certs_audit_log"]
        connection.vendor = "microsoft"
        now = datetime(2026, 6, 30, 2, 0, tzinfo=timezone.utc)

        result = run_blob_retention_sweeper(now=now, delete_blob=lambda path: True)

        sql_text = "\n".join(str(call.args[0]) for call in cursor.execute.call_args_list)
        self.assertEqual(result.soft_marked, 2)
        self.assertTrue(result.audit_recorded)
        self.assertIn("delete_pending_since = %s", sql_text)
        self.assertIn("scheduled_delete_at <= %s", sql_text)
        self.assertIn("dpa_retention_override_until", sql_text)
        self.assertIn("retention_purge", str(cursor.execute.call_args_list[-1].args[1]))
        self.assertIn("dbRoleBoundary", str(cursor.execute.call_args_list[-1].args[1]))

    @patch("apps.certs.jobs.blob_retention_sweeper.connection")
    def test_sweeper_hard_deletes_delete_pending_rows_after_grace(self, connection) -> None:
        cursor = MagicMock()
        cursor.rowcount = 1
        cursor.description = [("blob_id",), ("blob_storage_path",)]
        cursor.fetchall.return_value = [
            ("blob-1", "certs/vessels/vessel-1/tracked-items/item-1/old.pdf"),
            ("blob-2", "certs/vessels/vessel-1/tracked-items/item-1/older.pdf"),
        ]
        connection.cursor.return_value.__enter__.return_value = cursor
        connection.introspection.table_names.return_value = ["vims_certs_pdf_blob", "vims_certs_audit_log"]
        connection.vendor = "microsoft"
        deleted_paths: list[str] = []

        result = run_blob_retention_sweeper(
            now=datetime(2026, 6, 30, 2, 0, tzinfo=timezone.utc),
            delete_blob=lambda path: deleted_paths.append(path) or True,
        )

        sql_text = "\n".join(str(call.args[0]) for call in cursor.execute.call_args_list)
        self.assertEqual(result.hard_deleted, 2)
        self.assertEqual(deleted_paths, [
            "certs/vessels/vessel-1/tracked-items/item-1/old.pdf",
            "certs/vessels/vessel-1/tracked-items/item-1/older.pdf",
        ])
        self.assertIn("DELETE FROM dbo.vims_certs_pdf_blob", sql_text)
        self.assertIn("delete_pending_since <= %s", sql_text)


if __name__ == "__main__":
    unittest.main()
