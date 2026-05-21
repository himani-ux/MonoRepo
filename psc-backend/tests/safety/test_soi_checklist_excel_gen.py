from __future__ import annotations

from datetime import date
from io import BytesIO
import unittest

from openpyxl import load_workbook

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection

from apps.safety.models import SOIInspection, SOIInspectionArea
from apps.safety.repositories import SOIRepository
from apps.safety.services import SOIChecklistGenerator


class SOIChecklistExcelGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_soi_tables()
        self._insert_area(area_id=5, area_name="Mooring Deck + Forward Station")
        self._insert_item(area_id=5, area_name="Mooring Deck + Forward Station")

    def test_excel_generation_embeds_unique_id_and_image(self) -> None:
        inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/ABC/26/05",
            cycle_label="Q2/2026",
            planned_date=date(2026, 5, 3),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            checklist_unique_id="SOI-0000007-20260503-0005",
            created_by="co-7",
        )
        SOIInspectionArea.objects.create(inspection_id=inspection.id, area_id=5, schema_version=1)

        result = SOIChecklistGenerator(soi_repository=SOIRepository()).render_for_inspection(
            inspection_id=inspection.id,
            output_format="XLSX",
        )

        self.assertEqual(result.output_format, "XLSX")
        self.assertEqual(
            result.content_type,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(result.file_name.endswith(".xlsx"))

        workbook = load_workbook(BytesIO(result.content))
        worksheet = workbook.active
        self.assertEqual(worksheet["B3"].value, "SOI-0000007-20260503-0005")
        self.assertEqual(worksheet["B2"].value, "SOI/ABC/26/05")
        self.assertEqual(worksheet["D10"].value, "Mooring line snap-back zones are marked")
        self.assertEqual(len(getattr(worksheet, "_images", [])), 1)

    def _insert_area(self, *, area_id: int, area_name: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_soi_area (
                    area_id,
                    area_name,
                    section_12_flag,
                    display_order,
                    active,
                    seeded_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [area_id, area_name, False, area_id, True, "v1.0"],
            )

    def _insert_item(self, *, area_id: int, area_name: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_soi_area_item (
                    legacy_int_id,
                    area_id,
                    area_name,
                    subsection_id,
                    subsection_name,
                    item_number,
                    description,
                    tier,
                    active,
                    seeded_version,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    int(f"{area_id}01"),
                    area_id,
                    area_name,
                    1,
                    "Deck safety",
                    "5.1",
                    "Mooring line snap-back zones are marked",
                    "BASELINE",
                    True,
                    "v1.0",
                    1,
                ],
            )
