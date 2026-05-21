from __future__ import annotations

import unittest

from django.db import IntegrityError

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory


class PhaseLogAppendOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()

    def test_phase_log_rows_are_append_only(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="DRAFT",
            created_by="master-7",
            schema_version=1,
        )
        phase_log = IncidentPhaseLog.objects.create(
            incident=incident,
            phase_from=None,
            phase_to=1,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            actor_user_id="master-7",
            actor_role_code="MASTER",
        )

        phase_log.phase_to = 2
        with self.assertRaises(IntegrityError):
            phase_log.save()

        with self.assertRaises(IntegrityError):
            phase_log.delete()

    def test_field_history_rows_are_append_only(self) -> None:
        history = SafetyFieldHistory.objects.create(
            parent_table="vims_safety_incident",
            parent_id=41,
            field_name="narrative",
            old_value="before",
            new_value="after",
            actor_user_id="master-7",
            actor_role_code="MASTER",
        )

        history.new_value = "later"
        with self.assertRaises(IntegrityError):
            history.save()

        with self.assertRaises(IntegrityError):
            history.delete()
