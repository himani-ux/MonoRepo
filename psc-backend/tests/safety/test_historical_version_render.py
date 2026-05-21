from __future__ import annotations

from datetime import datetime, timezone
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection

from apps.safety.models import SOIInspection
from apps.safety.repositories import SOIRepository
from apps.safety.serializers import SOIInspectionSerializer
from apps.safety.services.checklist_version_resolver import ChecklistVersionResolver


class HistoricalChecklistVersionRenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()

    def test_historical_soi_renders_against_creation_time_version(self) -> None:
        inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/ABC/26/01",
            cycle_label="Q2/2026",
            state=SOIInspection.State.PLANNED,
            planned_date="2026-04-20",
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            section_12_included=False,
            schema_version=1,
            created_by="co-7",
            updated_by="co-7",
        )
        SOIInspection.objects.filter(pk=inspection.pk).update(
            created_date=datetime(2026, 4, 20, 9, 0, tzinfo=timezone.utc),
        )
        inspection.refresh_from_db()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE master_soi_checklist_version
                SET active = 0, effective_to = %s
                WHERE version_label = %s
                """,
                ["2026-05-15", "v1.0"],
            )
            cursor.execute(
                """
                INSERT INTO master_soi_checklist_version (
                    version_label,
                    effective_from,
                    effective_to,
                    source_description,
                    active,
                    created_by,
                    created_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "v2.0",
                    "2026-05-16",
                    None,
                    "Section 12 refresh",
                    True,
                    "dpa-1",
                    "2026-05-16 00:00:00",
                ],
            )

        serializer = SOIInspectionSerializer(
            inspection,
            context={
                "checklist_version_resolver": ChecklistVersionResolver(),
                "soi_repository": SOIRepository(),
            },
        )

        self.assertEqual(serializer.data["checklist_version"]["version_label"], "v1.0")
        self.assertEqual(serializer.data["checklist_version"]["effective_to"], "2026-05-15")
