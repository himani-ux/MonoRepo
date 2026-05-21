from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.services.deadline_pauser import DeadlinePauser


def build_user(role_name: str = "DPA", user_id: str = "dpa-1"):
    return SimpleNamespace(id=user_id, username=user_id, role_name=role_name)


class DeadlinePauserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.service = DeadlinePauser()

    def test_pause_and_resume_events_are_audited_for_yellow_incident(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8D1",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        paused = self.service.sync_incident(incident, dpa_on_leave=True, user=build_user())
        resumed = self.service.sync_incident(incident, dpa_on_leave=False, user=build_user())

        self.assertTrue(paused["is_paused"])
        self.assertFalse(resumed["is_paused"])
        self.assertEqual(
            SafetyFieldHistory.objects.filter(
                parent_id=incident.pk,
                field_name="yellow_deadline_pause",
            ).count(),
            2,
        )
