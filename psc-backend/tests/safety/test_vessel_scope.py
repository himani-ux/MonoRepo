from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tests.safety.support import bootstrap_django, recreate_incident_table

bootstrap_django()

from apps.safety.authentication.vessel_scope import filter_by_vessel_scope, user_has_vessel_access
from apps.safety.models import SafetyFieldHistory
from apps.safety.services.field_history_recorder import parse_history_value


class DummyQuerySet:
    def __init__(self) -> None:
        self.filters: list[dict[str, object]] = []
        self.none_called = False

    def filter(self, **kwargs):
        self.filters.append(kwargs)
        return self

    def none(self):
        self.none_called = True
        return self


class SafetyVesselScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()

    def test_office_user_scopes_via_role_by_vessel_rows(self) -> None:
        qs = DummyQuerySet()
        user = SimpleNamespace(
            work_side="OFFICE",
            role_by_vessel_rows=[{"vessel_id": 11}, {"vessel_id": 13}],
            is_global=False,
        )

        filtered = filter_by_vessel_scope(qs, user)

        self.assertIs(filtered, qs)
        self.assertEqual(qs.filters, [{"vessel_id__in": ["11", "13"]}])

    @patch("apps.safety.authentication.vessel_scope._office_vessel_ids_from_vims")
    def test_office_user_prefers_vims_master_role_by_vessel_scope(self, mock_vims_scope) -> None:
        mock_vims_scope.return_value = {"7"}
        qs = DummyQuerySet()
        user = SimpleNamespace(
            user_type="OFFICE",
            work_side="OFFICE",
            role_by_vessel_rows=[{"vessel_id": 99}],
            has_global_vessel_access=False,
            is_global=False,
        )

        filtered = filter_by_vessel_scope(qs, user)

        self.assertIs(filtered, qs)
        self.assertEqual(qs.filters, [{"vessel_id__in": ["7"]}])
        mock_vims_scope.assert_called_once_with(user)

    def test_user_has_vessel_access_rejects_unassigned_vessel(self) -> None:
        user = SimpleNamespace(vessel_ids=["7"], is_global=False)

        self.assertTrue(user_has_vessel_access(user, "7"))
        self.assertFalse(user_has_vessel_access(user, "9"))

    def test_ship_user_scopes_via_current_crew_onboarding_rows(self) -> None:
        qs = DummyQuerySet()
        user = SimpleNamespace(
            work_side="SHIP",
            crew_onboarding_rows=[
                {"vessel_id": 5, "is_current": False},
                {"vessel_id": 9, "is_current": True},
            ],
            is_global=False,
        )

        filtered = filter_by_vessel_scope(qs, user)

        self.assertIs(filtered, qs)
        self.assertEqual(qs.filters, [{"vessel_id__in": ["9"]}])

    def test_office_user_scopes_via_numeric_work_side_zero(self) -> None:
        qs = DummyQuerySet()
        user = SimpleNamespace(
            work_side=0,
            role_by_vessel_rows=[{"vessel_id": 21}, {"vessel_id": 34}],
            is_global=False,
        )

        filtered = filter_by_vessel_scope(qs, user)

        self.assertIs(filtered, qs)
        self.assertEqual(qs.filters, [{"vessel_id__in": ["21", "34"]}])

    def test_ship_user_scopes_via_numeric_work_side_one(self) -> None:
        qs = DummyQuerySet()
        user = SimpleNamespace(
            work_side=1,
            crew_onboarding_rows=[
                {"vessel_id": 12, "is_current": True},
                {"vessel_id": 19, "is_current": False},
            ],
            is_global=False,
        )

        filtered = filter_by_vessel_scope(qs, user)

        self.assertIs(filtered, qs)
        self.assertEqual(qs.filters, [{"vessel_id__in": ["12"]}])

    def test_ship_user_scopes_via_direct_vessel_id_attribute(self) -> None:
        qs = DummyQuerySet()
        user = SimpleNamespace(
            work_side=1,
            vessel_id="EF9029C2-A192-EF11-A9F2-933342524037",
            is_global=False,
        )

        filtered = filter_by_vessel_scope(qs, user)

        self.assertIs(filtered, qs)
        self.assertEqual(
            qs.filters,
            [{"vessel_id__in": ["EF9029C2-A192-EF11-A9F2-933342524037"]}],
        )

    def test_field_history_preserves_scalar_values_through_json_envelope(self) -> None:
        row = SafetyFieldHistory.objects.create(
            parent_table="vims_safety_incident",
            parent_id=1,
            field_name="state",
            old_value="SUBMITTED",
            new_value="IN_PROGRESS",
            actor_user_id="master-7",
            actor_role_code="MASTER",
            schema_version=1,
        )

        stored = SafetyFieldHistory.objects.get(pk=row.pk)

        self.assertEqual(parse_history_value(stored.old_value), "SUBMITTED")
        self.assertEqual(parse_history_value(stored.new_value), "IN_PROGRESS")

    def test_global_access_bypasses_vessel_filtering(self) -> None:
        qs = DummyQuerySet()
        user = SimpleNamespace(is_global=True)

        filtered = filter_by_vessel_scope(qs, user)

        self.assertIs(filtered, qs)
        self.assertEqual(qs.filters, [])
        self.assertFalse(qs.none_called)
