from __future__ import annotations

from datetime import datetime, timedelta
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_soi_tables


bootstrap_django()

from apps.safety.models import Incident, SOIFinding, SOIInspection
from apps.safety.services.heinrich_ratio import HeinrichRatioService


def aware(year: int, month: int, day: int) -> datetime:
    return timezone.make_aware(datetime(year, month, day, 12, 0))


class HeinrichRatioServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_soi_tables()
        self.current_at = aware(2026, 4, 30)
        self.service = HeinrichRatioService(now_func=lambda: self.current_at)

    def test_build_panel_returns_full_pyramid_with_green_confidence(self) -> None:
        self._create_incident("INC/2026/7001", risk_band=Incident.RiskBand.RED, imo_classifier=Incident.ImoClassifier.SMC)
        self._create_incident(
            "INC/2026/7002",
            risk_band=Incident.RiskBand.YELLOW,
            imo_classifier=Incident.ImoClassifier.MC,
            occurred_at=self.current_at - timedelta(days=20),
        )
        self._create_incident(
            "INC/2026/7003",
            risk_band=Incident.RiskBand.GREEN,
            imo_classifier=Incident.ImoClassifier.MI,
            occurred_at=self.current_at - timedelta(days=30),
        )
        self._create_incident(
            "INC/2026/7004",
            risk_band=Incident.RiskBand.GREEN,
            imo_classifier=Incident.ImoClassifier.MI,
            occurred_at=self.current_at - timedelta(days=40),
        )
        self._create_incident(
            "INC/2026/7005",
            risk_band=Incident.RiskBand.GREEN,
            imo_classifier=Incident.ImoClassifier.MI,
            occurred_at=self.current_at - timedelta(days=50),
        )
        for index in range(20):
            self._create_near_miss(
                f"NM/2026/71{index:02d}",
                occurred_at=self.current_at - timedelta(days=5 + index),
            )

        inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/7/2026/01",
            cycle_label="Q2/2026",
            state=SOIInspection.State.REPORTED,
            planned_date=self.current_at.date(),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            created_by="co-7",
            updated_by="co-7",
            schema_version=1,
        )
        SOIFinding.objects.create(
            inspection_id=inspection.id,
            area_id=3,
            title="Open bridge observation",
            description="Bridge observation recorded in the rolling window.",
            severity=SOIFinding.Severity.MED,
            priority=SOIFinding.Priority.MED,
            status=SOIFinding.Status.OPEN,
            created_by="co-7",
            created_date=self.current_at - timedelta(days=15),
            schema_version=1,
        )

        payload = self.service.build_panel(vessel_id="7", as_of=self.current_at)

        self.assertEqual(payload["confidence"]["status"], "GREEN")
        self.assertFalse(payload["reporting_culture_gap"]["is_gap"])
        self.assertEqual(
            [layer["actual"] for layer in payload["layers"]],
            [1, 1, 3, 20, 1],
        )
        self.assertEqual(payload["layers"][0]["benchmark"], 1)
        self.assertEqual(payload["layers"][3]["label"], "Near miss")

    def test_build_panel_flags_reporting_culture_gap_and_excludes_superseded_rows(self) -> None:
        self._create_incident(
            "INC/2026/8001",
            risk_band=Incident.RiskBand.RED,
            imo_classifier=Incident.ImoClassifier.SMC,
        )
        self._create_incident(
            "INC/2026/8002",
            risk_band=Incident.RiskBand.YELLOW,
            imo_classifier=Incident.ImoClassifier.MC,
            superseded_by_id=99,
        )

        payload = self.service.build_panel(vessel_id="7", as_of=self.current_at)

        self.assertEqual(payload["confidence"]["status"], "AMBER")
        self.assertTrue(payload["reporting_culture_gap"]["is_gap"])
        self.assertIn("near misses", payload["reporting_culture_gap"]["message"])
        self.assertEqual(
            [layer["actual"] for layer in payload["layers"]],
            [1, 0, 0, 0, 0],
        )

    def _create_incident(
        self,
        incident_number: str,
        *,
        risk_band: str,
        imo_classifier: str,
        occurred_at: datetime | None = None,
        superseded_by_id: int | None = None,
    ) -> Incident:
        return Incident.objects.create(
            incident_number=incident_number,
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=5,
            risk_band=risk_band,
            imo_classifier=imo_classifier,
            occurred_at=occurred_at or self.current_at - timedelta(days=10),
            superseded_by_id=superseded_by_id,
            created_by="dpa-7",
            updated_by="dpa-7",
            schema_version=1,
        )

    def _create_near_miss(self, incident_number: str, *, occurred_at: datetime) -> Incident:
        return Incident.objects.create(
            incident_number=incident_number,
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            occurred_at=occurred_at,
            created_by="crew-7",
            updated_by="dpa-7",
            schema_version=1,
        )
