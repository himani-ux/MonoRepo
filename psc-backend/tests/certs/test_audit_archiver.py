from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO
import os
import unittest
from unittest.mock import MagicMock, patch

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from django.core.management import call_command


class CertAuditArchiverTests(unittest.TestCase):
    @patch("apps.certs.jobs.audit_archiver.connection")
    def test_archiver_flips_hot_rows_purges_five_year_rows_and_audits_summary(self, connection) -> None:
        from apps.certs.jobs.audit_archiver import run_audit_archiver

        now = datetime(2026, 6, 30, 4, 0, tzinfo=timezone.utc)
        cursor = MagicMock()
        rowcounts = [3, 2, 1]

        def execute_side_effect(*_args, **_kwargs):
            cursor.rowcount = rowcounts.pop(0)

        cursor.execute.side_effect = execute_side_effect
        connection.vendor = "microsoft"
        connection.introspection.table_names.return_value = ["vims_certs_audit_log"]
        connection.cursor.return_value.__enter__.return_value = cursor

        result = run_audit_archiver(now=now)

        self.assertEqual(result.cold_flipped, 3)
        self.assertEqual(result.purged, 2)
        self.assertTrue(result.audit_recorded)
        self.assertEqual(result.hot_cutoff.isoformat(), "2024-06-30T04:00:00+00:00")
        self.assertEqual(result.purge_cutoff.isoformat(), "2021-06-30T04:00:00+00:00")
        executed_sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
        self.assertIn("UPDATE dbo.vims_certs_audit_log", executed_sql)
        self.assertIn("SET retention_tier = %s", executed_sql)
        self.assertIn("archived_at = %s", executed_sql)
        self.assertIn("WHERE timestamp_utc <= %s", executed_sql)
        self.assertIn("retention_tier = %s", executed_sql)
        self.assertIn("DELETE FROM dbo.vims_certs_audit_log", executed_sql)
        self.assertIn("INSERT INTO dbo.vims_certs_audit_log", executed_sql)
        self.assertIn("retention_purge", cursor.execute.call_args_list[-1].args[1])

    @patch("apps.certs.jobs.audit_archiver.connection")
    def test_archiver_noops_when_audit_table_is_missing(self, connection) -> None:
        from apps.certs.jobs.audit_archiver import run_audit_archiver

        connection.introspection.table_names.return_value = []

        result = run_audit_archiver(now=datetime(2026, 6, 30, 4, 0, tzinfo=timezone.utc))

        self.assertEqual(result.cold_flipped, 0)
        self.assertEqual(result.purged, 0)
        self.assertFalse(result.audit_recorded)
        self.assertEqual(result.reason, "missing_audit_log_table")

    @patch("apps.certs.management.commands.archive_audit_log.run_audit_archiver")
    def test_management_command_is_scheduler_target(self, run_audit_archiver) -> None:
        from apps.certs.jobs.audit_archiver import AuditArchiverResult

        run_audit_archiver.return_value = AuditArchiverResult(
            cold_flipped=4,
            purged=1,
            audit_recorded=True,
            hot_cutoff=datetime(2024, 6, 30, 4, 0, tzinfo=timezone.utc),
            purge_cutoff=datetime(2021, 6, 30, 4, 0, tzinfo=timezone.utc),
            reason="completed",
        )

        call_command("archive_audit_log", now_utc="2026-06-30T04:00:00Z", stdout=StringIO(), verbosity=0)

        self.assertEqual(
            run_audit_archiver.call_args.kwargs["now"].isoformat(),
            "2026-06-30T04:00:00+00:00",
        )
