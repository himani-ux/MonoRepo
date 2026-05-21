from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.services.pic_retention import PicRetentionService


def build_user(role_name: str = "SYSTEM", user_id: str = "system"):
    return SimpleNamespace(id=user_id, username=user_id, role_name=role_name)


class PicRetentionServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.service = PicRetentionService()

    def test_yellow_incident_keeps_original_pic_after_transfer(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8P1",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-original",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        result = self.service.handle_transfer(
            incident,
            incoming_pic_user_id="pic-new",
            user=build_user(),
        )

        incident.refresh_from_db()
        self.assertTrue(result["retained"])
        self.assertEqual(result["retained_pic_user_id"], "pic-original")
        self.assertEqual(incident.pic_user_id, "pic-original")
