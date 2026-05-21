from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.serializers.incident_phase2 import IncidentPhase2Serializer
from apps.safety.repositories import IncidentRepository


class IncidentPhase2ImoClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.repository = IncidentRepository()

    def test_rejects_unknown_classifier(self) -> None:
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
                "risk_band": Incident.RiskBand.YELLOW,
                "imo_classifier": "CASUALTY",
            },
            context={"incident_repository": self.repository},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("imo_classifier", serializer.errors)

    def test_requires_position_for_imo_classified_casualties(self) -> None:
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
                "risk_band": Incident.RiskBand.YELLOW,
                "imo_classifier": Incident.ImoClassifier.MC,
            },
            context={"incident_repository": self.repository},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("latitude", serializer.errors)
        self.assertIn("longitude", serializer.errors)

    def test_allows_internal_only_classifier_without_position(self) -> None:
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
                "risk_band": Incident.RiskBand.GREEN,
                "imo_classifier": Incident.ImoClassifier.NOT_APPLICABLE,
            },
            context={"incident_repository": self.repository},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
