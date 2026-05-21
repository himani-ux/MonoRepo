from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.serializers.incident_phase2 import IncidentPhase2Serializer
from apps.safety.repositories import IncidentRepository


class IncidentPhase2RiskBandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.repository = IncidentRepository()

    def test_rejects_unknown_risk_band(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="SUBMITTED",
            current_phase=2,
            created_by="master-7",
            schema_version=1,
        )

        serializer = IncidentPhase2Serializer(
            incident,
            data={
                "risk_band": "BLUE",
                "imo_classifier": Incident.ImoClassifier.MI,
            },
            context={"incident_repository": self.repository},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("risk_band", serializer.errors)

    def test_band_and_classifier_coexist_without_reconciliation(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="SUBMITTED",
            current_phase=2,
            created_by="master-7",
            schema_version=1,
            latitude="12.345678",
            longitude="103.456789",
        )

        serializer = IncidentPhase2Serializer(
            incident,
            data={
                "risk_band": Incident.RiskBand.GREEN,
                "imo_classifier": Incident.ImoClassifier.SMC,
            },
            context={"incident_repository": self.repository},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
