from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.services.field_history_recorder import capture_model_state, record_field_changes


class FieldHistoryRecorderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()

    def test_recorder_captures_only_changed_fields_as_text(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="DRAFT",
            created_by="master-7",
            schema_version=1,
            narrative="Before",
            risk_band=Incident.RiskBand.GREEN,
        )
        old_state = capture_model_state(incident, field_names=["narrative", "risk_band", "state"])

        incident.narrative = "After"
        incident.risk_band = Incident.RiskBand.RED

        created_rows = record_field_changes(
            incident,
            old_state,
            user=SimpleNamespace(username="master-7", role_name="MASTER"),
            field_names=["narrative", "risk_band", "state"],
        )

        self.assertEqual(len(created_rows), 2)

        rows = list(SafetyFieldHistory.objects.order_by("field_name").values("field_name", "old_value", "new_value"))
        self.assertEqual(
            rows,
            [
                {"field_name": "narrative", "old_value": "Before", "new_value": "After"},
                {"field_name": "risk_band", "old_value": "GREEN", "new_value": "RED"},
            ],
        )
        self.assertTrue(all(row.changed_at is not None for row in created_rows))
