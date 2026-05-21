from __future__ import annotations

import importlib
import unittest

from django.db import IntegrityError
from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_scm_tables, recreate_soi_tables


bootstrap_django()

from apps.safety.models import Incident, SCMMeeting, SOIInspection


class SoftArchiveFinalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_scm_tables()
        recreate_soi_tables()
        self.current_at = timezone.now()

    def test_step_8_3_migration_imports_with_current_workspace_numbering(self) -> None:
        module = importlib.import_module("apps.safety.migrations.0011_soft_archive_final")
        migration = module.Migration("0011_soft_archive_final", "safety")

        self.assertEqual(migration.dependencies, [("safety", "0010_field_history_shape")])

    def test_models_expose_explicit_archive_flag(self) -> None:
        self.assertFalse(Incident._meta.get_field("is_archived").default)
        self.assertFalse(SCMMeeting._meta.get_field("is_archived").default)
        self.assertFalse(SOIInspection._meta.get_field("is_archived").default)

    def test_incident_rejects_archive_timestamp_without_archive_flag(self) -> None:
        with self.assertRaises(IntegrityError):
            Incident.objects.create(
                incident_number="INC/2026/ARCHIVE-MISMATCH-1",
                vessel_id="7",
                state=Incident.State.CLOSED,
                current_phase=9,
                archived_at=self.current_at,
                created_by="dpa-7",
                schema_version=2,
            )

    def test_incident_rejects_archive_flag_without_archive_timestamp(self) -> None:
        with self.assertRaises(IntegrityError):
            Incident.objects.create(
                incident_number="INC/2026/ARCHIVE-MISMATCH-2",
                vessel_id="7",
                state=Incident.State.CLOSED,
                current_phase=9,
                is_archived=True,
                created_by="dpa-7",
                schema_version=2,
            )
