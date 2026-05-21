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
from apps.safety.services.pareto_screener import ParetoScreenerService


def aware(year: int, month: int, day: int) -> datetime:
    return timezone.make_aware(datetime(year, month, day, 12, 0))


class ParetoScreenerServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_phase5_reference_tables()
        self.current_at = aware(2026, 4, 30)
        self.service = ParetoScreenerService(now_func=lambda: self.current_at)
        self._seed_taxonomy()

    def test_build_panel_returns_ranked_entries_with_cumulative_share(self) -> None:
        for index in range(5):
            self._create_root_cause(
                incident_number=f"INC/2026/PAR-A{index}",
                vessel_id="7",
                subcode_id="10.15",
                occurred_at=self.current_at - timedelta(days=10 + index),
            )
        for index in range(3):
            self._create_root_cause(
                incident_number=f"INC/2026/PAR-B{index}",
                vessel_id="9",
                subcode_id="4.09",
                occurred_at=self.current_at - timedelta(days=30 + index),
            )
        for index in range(2):
            self._create_root_cause(
                incident_number=f"INC/2026/PAR-C{index}",
                vessel_id="7",
                subcode_id="2.01",
                occurred_at=self.current_at - timedelta(days=50 + index),
            )

        payload = self.service.build_panel(as_of=self.current_at, top_n=2)

        self.assertEqual(payload["top_n"], 2)
        self.assertEqual(payload["total_occurrences"], 10)
        self.assertEqual(payload["entries"][0]["subcode_id"], "10.15")
        self.assertEqual(payload["entries"][0]["vessel_id"], "7")
        self.assertEqual(payload["entries"][0]["share_percent"], 50.0)
        self.assertEqual(payload["entries"][0]["cumulative_percent"], 50.0)
        self.assertTrue(payload["entries"][0]["within_80_cutoff"])
        self.assertEqual(payload["entries"][1]["share_percent"], 30.0)
        self.assertEqual(payload["entries"][1]["cumulative_percent"], 80.0)
        self.assertTrue(payload["entries"][1]["within_80_cutoff"])

    def _seed_taxonomy(self) -> None:
        rows = [
            (10, "Management of Change", "10.15", "Independent review absent"),
            (4, "Personnel factors", "4.09", "Inadequate familiarisation"),
            (2, "Unsafe acts", "2.01", "Procedure not followed"),
        ]
        with connection.cursor() as cursor:
            for category_id, category_name, subcode_id, description in rows:
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
                    [category_id, category_name, subcode_id, description, "BASIC_CAUSE", True, "v1", 1],
                )

    def _create_root_cause(
        self,
        *,
        incident_number: str,
        vessel_id: str,
        subcode_id: str,
        occurred_at: datetime,
    ) -> None:
        incident = Incident.objects.create(
            incident_number=incident_number,
            vessel_id=vessel_id,
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=5,
            occurred_at=occurred_at,
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
            rationale="Pareto trend sample.",
            created_by="dpa-7",
            schema_version=1,
        )
