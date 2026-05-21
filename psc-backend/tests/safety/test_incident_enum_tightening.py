from __future__ import annotations

import importlib
import unittest
from datetime import datetime, timezone

from django.db import IntegrityError

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.repositories import IncidentRepository


class IncidentEnumTighteningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.repository = IncidentRepository()

    def test_repository_defaults_new_rows_to_schema_version_two(self) -> None:
        incident = self.repository.create(
            {
                "vessel_id": "7",
                "vessel_code": "ABC",
                "created_by": "master-7",
                "occurred_at": datetime(2026, 4, 30, 9, 0, tzinfo=timezone.utc),
            }
        )

        self.assertEqual(incident.schema_version, Incident.ENUM_TIGHTENED_SCHEMA_VERSION)
        self.assertEqual(incident.state, Incident.State.DRAFT)

    def test_step_8_1_migration_imports_with_current_workspace_numbering(self) -> None:
        module = importlib.import_module("apps.safety.migrations.0009_tighten_incident_enums")
        migration = module.Migration("0009_tighten_incident_enums", "safety")

        self.assertEqual(migration.dependencies, [("safety", "0008_case_study_library")])

    def test_schema_version_two_rejects_legacy_state_at_db_level(self) -> None:
        with self.assertRaises(IntegrityError):
            Incident.objects.create(
                incident_number="ABC/2026/002",
                vessel_id="7",
                state="PHASE_2",
                current_phase=2,
                created_by="master-7",
                schema_version=Incident.ENUM_TIGHTENED_SCHEMA_VERSION,
            )

    def test_schema_version_two_rejects_invalid_investigation_depth_at_db_level(self) -> None:
        with self.assertRaises(IntegrityError):
            Incident.objects.create(
                incident_number="ABC/2026/003",
                vessel_id="7",
                state=Incident.State.UNDER_REVIEW,
                current_phase=5,
                investigation_depth="LEGACY_DEEP",
                created_by="master-7",
                schema_version=Incident.ENUM_TIGHTENED_SCHEMA_VERSION,
            )
