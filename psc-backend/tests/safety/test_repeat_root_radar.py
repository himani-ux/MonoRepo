from __future__ import annotations

from datetime import datetime, timedelta
import unittest

from django.db import connection
from django.utils import timezone

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_phase5_reference_tables,
)


bootstrap_django()

from apps.safety.models import Incident, IncidentCauseTag, IncidentFact
from apps.safety.services.repeat_root_radar import RepeatRootRadarService


def aware(year: int, month: int, day: int) -> datetime:
    return timezone.make_aware(datetime(year, month, day, 12, 0))


class RepeatRootRadarServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_phase5_reference_tables()
        self.current_at = aware(2026, 4, 30)
        self.service = RepeatRootRadarService(now_func=lambda: self.current_at)
        self._seed_taxonomy()

    def test_build_panel_returns_fleet_and_vessel_repeat_roots(self) -> None:
        for index in range(3):
            self._create_root_cause(
                incident_number=f"INC/2026/RRA{index}",
                vessel_id="7",
                subcode_id="10.15",
                occurred_at=self.current_at - timedelta(days=10 + index),
            )
        for index in range(3):
            self._create_root_cause(
                incident_number=f"INC/2026/RRB{index}",
                vessel_id="9",
                subcode_id="4.09",
                occurred_at=self.current_at - timedelta(days=20 + index),
            )
        self._create_root_cause(
            incident_number="INC/2026/RRA-SUP",
            vessel_id="7",
            subcode_id="10.15",
            occurred_at=self.current_at - timedelta(days=4),
            superseded_by_id=111,
        )

        payload = self.service.build_panel(vessel_id="7", as_of=self.current_at)

        self.assertEqual(len(payload["fleet"]), 2)
        self.assertEqual(payload["fleet"][0]["occurrences"], 3)
        self.assertEqual(payload["fleet"][0]["relative_strength"], 100)
        self.assertEqual(payload["fleet"][0]["subcode_id"], "10.15")
        self.assertEqual(payload["vessel"][0]["subcode_id"], "10.15")
        self.assertEqual(payload["vessel"][0]["occurrences"], 3)
        self.assertEqual(payload["vessel"][0]["description"], "Independent review absent")

    def _seed_taxonomy(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_mscat_taxonomy (
                    category_id,
                    category_name,
                    subcode_id,
                    subcode_description,
                    cause_type,
                    active,
                    seeded_version,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [10, "Management of Change", "10.15", "Independent review absent", "BASIC_CAUSE", True, "v1", 1],
            )
            cursor.execute(
                """
                INSERT INTO master_mscat_taxonomy (
                    category_id,
                    category_name,
                    subcode_id,
                    subcode_description,
                    cause_type,
                    active,
                    seeded_version,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [4, "Personnel factors", "4.09", "Inadequate familiarisation", "BASIC_CAUSE", True, "v1", 1],
            )

    def _create_root_cause(
        self,
        *,
        incident_number: str,
        vessel_id: str,
        subcode_id: str,
        occurred_at: datetime,
        superseded_by_id: int | None = None,
    ) -> None:
        incident = Incident.objects.create(
            incident_number=incident_number,
            vessel_id=vessel_id,
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=5,
            occurred_at=occurred_at,
            superseded_by_id=superseded_by_id,
            created_by="dpa-7",
            updated_by="dpa-7",
            schema_version=1,
        )
        fact = IncidentFact.objects.create(
            incident=incident,
            sequence_index=1,
            fact_text=f"Fact for {incident_number}",
            source_evidence_id=1,
            created_by="dpa-7",
            schema_version=1,
        )
        IncidentCauseTag.objects.create(
            incident=incident,
            source_fact=fact,
            mscat_subcode_id=subcode_id,
            causal_layer=IncidentCauseTag.CausalLayer.ROOT,
            analysis_tool=IncidentCauseTag.AnalysisTool.STEP,
            rationale="Repeatable root cause for dashboard trend analysis.",
            created_by="dpa-7",
            schema_version=1,
        )
