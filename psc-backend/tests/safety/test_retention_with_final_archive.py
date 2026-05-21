from __future__ import annotations

from datetime import timedelta
import os
from pathlib import Path
import shutil
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.tasks.retention_job import run_retention_job


class RetentionWithFinalArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        self.current_at = timezone.make_aware(timezone.datetime(2026, 4, 30, 12, 0))
        self.storage_root = Path("test-output") / "retention-final-archive"
        shutil.rmtree(self.storage_root, ignore_errors=True)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.original_export_root = os.environ.get("SAFETY_EXPORT_ROOT")
        os.environ["SAFETY_EXPORT_ROOT"] = str(self.storage_root)

    def tearDown(self) -> None:
        shutil.rmtree(self.storage_root, ignore_errors=True)
        if self.original_export_root is None:
            os.environ.pop("SAFETY_EXPORT_ROOT", None)
        else:
            os.environ["SAFETY_EXPORT_ROOT"] = self.original_export_root

    def test_retention_job_only_purges_records_marked_as_archived(self) -> None:
        archived_at = self.current_at - timedelta(days=1096)
        archived_record = Incident.objects.create(
            incident_number="INC/2022/ARCHIVED",
            vessel_id="7",
            state=Incident.State.CLOSED,
            current_phase=9,
            occurred_at=archived_at,
            reported_at=archived_at,
            is_archived=True,
            archived_at=archived_at,
            created_by="dpa-7",
            schema_version=2,
        )
        active_old_record = Incident.objects.create(
            incident_number="INC/2022/ACTIVE",
            vessel_id="7",
            state=Incident.State.CLOSED,
            current_phase=9,
            occurred_at=archived_at,
            reported_at=archived_at,
            created_by="dpa-7",
            schema_version=2,
        )

        result = run_retention_job(now=self.current_at)

        self.assertEqual(result.deleted_record_count, 1)
        self.assertFalse(Incident.objects.filter(pk=archived_record.pk).exists())
        self.assertTrue(Incident.objects.filter(pk=active_old_record.pk).exists())
