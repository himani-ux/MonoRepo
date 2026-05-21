from __future__ import annotations

import unittest

from django.db import models

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.services.field_history_recorder import parse_history_value, record_field_changes


class FieldHistoryShapeFinalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()

    def test_field_history_values_use_json_fields(self) -> None:
        self.assertIsInstance(SafetyFieldHistory._meta.get_field("old_value"), models.JSONField)
        self.assertIsInstance(SafetyFieldHistory._meta.get_field("new_value"), models.JSONField)

    def test_recorder_preserves_native_boolean_values(self) -> None:
        incident = Incident.objects.create(
            incident_number="INC/2026/FH-BOOL",
            vessel_id="7",
            state="DRAFT",
            created_by="master-7",
            schema_version=2,
            awaiting_daily_report_match=False,
        )
        old_state = {"awaiting_daily_report_match": False}
        incident.awaiting_daily_report_match = True

        rows = record_field_changes(
            incident,
            old_state,
            user=None,
            field_names=("awaiting_daily_report_match",),
        )

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertIs(row.old_value, False)
        self.assertIs(row.new_value, True)

    def test_parse_history_value_supports_legacy_json_strings_without_coercing_plain_scalars(self) -> None:
        self.assertEqual(parse_history_value('{"attachment_path": "x.jpg"}'), {"attachment_path": "x.jpg"})
        self.assertEqual(parse_history_value("[1, 2, 3]"), [1, 2, 3])
        self.assertEqual(parse_history_value("GREEN"), "GREEN")
        self.assertEqual(parse_history_value("7"), "7")
