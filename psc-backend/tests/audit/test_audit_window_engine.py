from __future__ import annotations

import io
import os
import unittest
import uuid
from datetime import date

import django
from django.apps import apps
from django.core.management import call_command
from django.db import connection


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-window-test-secret-key-1234567890",
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
            ROOT_URLCONF="core.urls",
        )

    if not apps.ready:
        django.setup()


bootstrap_django()

from apps.inspection.audit.jobs.audit_window import run_audit_window_tick  # noqa: E402
from apps.inspection.audit.models import MasterAuditPlan, MasterAuditWindowRule  # noqa: E402
from apps.inspection.audit.services.audit_window import compute_window_for_plan  # noqa: E402


SCHEMA_MODELS = [MasterAuditPlan, MasterAuditWindowRule]


class AuditWindowEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            existing_tables = set(connection.introspection.table_names())
            for model in reversed(SCHEMA_MODELS):
                if model._meta.db_table in existing_tables:
                    schema_editor.delete_model(model)
            for model in SCHEMA_MODELS:
                schema_editor.create_model(model)

    @classmethod
    def tearDownClass(cls) -> None:
        with connection.schema_editor() as schema_editor:
            for model in reversed(SCHEMA_MODELS):
                schema_editor.delete_model(model)
        super().tearDownClass()

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            for model in reversed(SCHEMA_MODELS):
                cursor.execute(f"DELETE FROM {model._meta.db_table}")
        self.vessel_id = uuid.uuid4()

    def _rule(self, *, open_months: int, close_months: int) -> MasterAuditWindowRule:
        return MasterAuditWindowRule.objects.create(
            standard_code="ISM",
            subtype_code="ANNUAL_INTERNAL",
            window_open_offset_months=open_months,
            window_close_offset_months=close_months,
            cadence_months=close_months,
            regulatory_citation="Test rule",
            is_active=True,
            created_by="test",
        )

    def _plan(self, **overrides) -> MasterAuditPlan:
        data = {
            "target_vessel_id": self.vessel_id,
            "audit_classification": "INTERNAL",
            "audit_standards_csv": "ISM",
            "planned_window_start": date(2026, 9, 1),
            "planned_window_end": date(2027, 1, 1),
            "status": "PLANNED",
            "created_by": "test",
        }
        data.update(overrides)
        return MasterAuditPlan.objects.create(**data)

    def test_compute_window_uses_master_rule_offsets_for_vessel_and_office(self) -> None:
        self._rule(open_months=8, close_months=12)
        vessel_plan = self._plan(target_office_dept=None)
        vessel_window = compute_window_for_plan(vessel_plan, anchor_date=date(2026, 1, 31))

        MasterAuditWindowRule.objects.all().delete()
        self._rule(open_months=9, close_months=15)
        office_plan = self._plan(
            target_vessel_id=None,
            target_office_dept="SEQ",
        )
        office_window = compute_window_for_plan(office_plan, anchor_date=date(2026, 1, 31))

        self.assertEqual(vessel_window.window_start, date(2026, 9, 30))
        self.assertEqual(vessel_window.window_end, date(2027, 1, 31))
        self.assertEqual(office_window.window_start, date(2026, 10, 31))
        self.assertEqual(office_window.window_end, date(2027, 4, 30))

    def test_tick_auto_creates_t90_draft_planned_entry_idempotently(self) -> None:
        self._rule(open_months=8, close_months=12)
        completed = self._plan(
            planned_window_start=date(2025, 9, 1),
            planned_window_end=date(2026, 1, 1),
            status="COMPLETED",
        )

        first = run_audit_window_tick(today=date(2026, 10, 3), apply=True)
        second = run_audit_window_tick(today=date(2026, 10, 3), apply=True)

        created = MasterAuditPlan.objects.exclude(id=completed.id).get()
        self.assertEqual(first.created_plans, 1)
        self.assertEqual(second.created_plans, 0)
        self.assertEqual(created.status, "PLANNED")
        self.assertEqual(created.planned_window_start, date(2026, 9, 1))
        self.assertEqual(created.planned_window_end, date(2027, 1, 1))
        self.assertEqual(created.created_by, "system.audit_window_tick")
        self.assertIn("AUDIT_WINDOW_T90_PLAN_CREATED", {event.event_type for event in first.events})

    def test_tick_excludes_additional_and_cancelled_plans_from_cadence_creation(self) -> None:
        self._rule(open_months=8, close_months=12)
        self._plan(
            planned_window_end=date(2026, 1, 1),
            status="COMPLETED",
            is_additional=True,
        )
        self._plan(
            target_vessel_id=uuid.uuid4(),
            planned_window_end=date(2026, 1, 1),
            status="CANCELLED",
        )

        result = run_audit_window_tick(today=date(2026, 10, 3), apply=True)

        self.assertEqual(result.created_plans, 0)
        self.assertEqual(MasterAuditPlan.objects.count(), 2)

    def test_tick_marks_overdue_and_critical_overdue(self) -> None:
        self._rule(open_months=8, close_months=12)
        overdue = self._plan(planned_window_end=date(2026, 8, 6), status="PLANNED")
        critical = self._plan(
            target_vessel_id=uuid.uuid4(),
            planned_window_end=date(2026, 5, 8),
            status="OVERDUE",
        )

        result = run_audit_window_tick(today=date(2026, 8, 6), apply=True)

        overdue.refresh_from_db()
        critical.refresh_from_db()
        self.assertEqual(overdue.status, "OVERDUE")
        self.assertEqual(critical.status, "CRITICAL_OVERDUE")
        self.assertEqual(result.overdue_plans, 1)
        self.assertEqual(result.critical_overdue_plans, 1)
        self.assertIn("AUDIT_OVERDUE", {event.event_type for event in result.events})
        self.assertIn("AUDIT_CRITICAL_OVERDUE", {event.event_type for event in result.events})

    def test_management_command_dry_run_does_not_mutate_until_apply(self) -> None:
        self._rule(open_months=8, close_months=12)
        plan = self._plan(planned_window_end=date(2026, 8, 6), status="PLANNED")
        out = io.StringIO()

        call_command("audit_window_tick", "--today", "2026-08-06", stdout=out)
        plan.refresh_from_db()
        self.assertEqual(plan.status, "PLANNED")
        self.assertIn("dry_run", out.getvalue())

        call_command("audit_window_tick", "--today", "2026-08-06", "--apply", stdout=io.StringIO())
        plan.refresh_from_db()
        self.assertEqual(plan.status, "OVERDUE")


if __name__ == "__main__":
    unittest.main()
