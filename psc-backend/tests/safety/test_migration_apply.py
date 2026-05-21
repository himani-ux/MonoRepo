from __future__ import annotations

import importlib
import unittest

import django
from django.apps import apps
from django.db import connection
from django.db.migrations.state import ProjectState


SAFETY_TABLES = {
    "master_immediate_causes",
    "master_loss_types",
    "master_mscat_taxonomy",
    "master_safety_bias_guard",
    "master_safety_incident_type",
    "master_soi_area",
    "master_soi_area_item",
    "master_soi_checklist_version",
    "vims_safety_bias_guard_response",
    "vims_safety_blame_override",
    "vims_safety_cause_tag",
    "vims_safety_chain_of_custody",
    "vims_safety_corrective_action",
    "vims_safety_evidence_deadline_task",
    "vims_safety_evidence_item",
    "vims_safety_fact",
    "vims_safety_field_history",
    "vims_safety_incident",
    "vims_safety_incident_evidence",
    "vims_safety_incident_phase5_assessment",
    "vims_safety_incident_phase_log",
    "vims_safety_recommendation",
    "vims_safety_scm_agenda",
    "vims_safety_scm_attendance",
    "vims_safety_scm_meeting",
    "vims_safety_safeguard_failure",
    "vims_safety_soi_applicability_log",
    "vims_safety_soi_finding",
    "vims_safety_soi_inspection",
    "vims_safety_soi_inspection_area",
    "vims_safety_soi_trainee",
    "vims_safety_soi_vessel_area_map",
    "vims_safety_witness_interview",
}


def bootstrap_django() -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="safety-phase-0-6-migration-test-secret-key-1234567890",
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


def drop_safety_tables() -> None:
    existing_tables = set(connection.introspection.table_names())
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF")
        for table_name in sorted(existing_tables & SAFETY_TABLES):
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        cursor.execute("PRAGMA foreign_keys = ON")


class SafetyMigrationApplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()
        cls.migration_module = importlib.import_module("apps.safety.migrations.0001_initial")

    def setUp(self) -> None:
        drop_safety_tables()

    def test_initial_migration_creates_all_safety_tables(self) -> None:
        migration = self.migration_module.Migration("0001_initial", "safety")
        self.assertTrue(migration.initial)
        self.assertEqual(migration.dependencies, [])

        project_state = ProjectState()
        with connection.schema_editor() as schema_editor:
            for operation in migration.operations:
                next_state = project_state.clone()
                operation.state_forwards("safety", next_state)
                operation.database_forwards("safety", schema_editor, project_state, next_state)
                project_state = next_state

        existing_tables = set(connection.introspection.table_names())
        self.assertTrue(SAFETY_TABLES.issubset(existing_tables))
        self.assertFalse(any(name.startswith("safety_") for name in existing_tables))

    def test_master_soi_area_item_uses_text_item_number_shape(self) -> None:
        project_state = ProjectState()
        with connection.schema_editor() as schema_editor:
            for operation in self.migration_module.Migration("0001_initial", "safety").operations:
                next_state = project_state.clone()
                operation.state_forwards("safety", next_state)
                operation.database_forwards("safety", schema_editor, project_state, next_state)
                project_state = next_state

        with connection.cursor() as cursor:
            description = connection.introspection.get_table_description(cursor, "master_soi_area_item")
        columns = {column.name: column for column in description}
        self.assertIn("item_number", columns)
