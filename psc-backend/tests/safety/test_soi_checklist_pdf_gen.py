from __future__ import annotations

from datetime import date
from io import BytesIO
import unittest

from PyPDF2 import PdfReader

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection

from apps.safety.models import SOIInspection, SOIInspectionArea
from apps.safety.repositories import SOIRepository
from apps.safety.services import SOIChecklistGenerator


class SOIChecklistPdfGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_soi_tables()
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_area(area_id=13, area_name="Cross-cutting Safety & Culture", section_12_flag=True)
        self._insert_item(area_id=3, area_name="Navigating Bridge & Monkey Island", item_number="3.1")
        self._insert_item(area_id=13, area_name="Cross-cutting Safety & Culture", item_number="13.1")

    def test_pdf_generation_embeds_unique_id_and_qr_image(self) -> None:
        inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/ABC/26/01",
            cycle_label="Q2/2026",
            planned_date=date(2026, 5, 1),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            checklist_unique_id="SOI-0000007-20260501-0001",
            created_by="co-7",
        )
        SOIInspectionArea.objects.create(inspection_id=inspection.id, area_id=3, schema_version=1)
        SOIInspectionArea.objects.create(inspection_id=inspection.id, area_id=13, schema_version=1)

        result = SOIChecklistGenerator(soi_repository=SOIRepository()).render_for_inspection(
            inspection_id=inspection.id,
            output_format="PDF",
        )

        self.assertEqual(result.output_format, "PDF")
        self.assertEqual(result.content_type, "application/pdf")
        self.assertTrue(result.file_name.endswith(".pdf"))
        self.assertTrue(result.content.startswith(b"%PDF"))

        reader = PdfReader(BytesIO(result.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("SOI-0000007-20260501-0001", text)
        self.assertIn("SOI/ABC/26/01", text)
        self.assertIn("13: Cross-cutting Safety", text)
        self.assertIn("Emergency lighting is inspected and available", text)

        first_page_resources = reader.pages[0].get("/Resources")
        xobjects = first_page_resources.get("/XObject") if first_page_resources else None
        self.assertTrue(xobjects)
        self.assertGreaterEqual(len(xobjects), 1)

    def test_table_header_rule_does_not_overlap_first_checklist_row(self) -> None:
        pdf = _RecordingPdf()
        SOIChecklistGenerator(soi_repository=SOIRepository())._draw_pdf_item_rows(
            pdf,
            rows=[
                {
                    "area": "1: External Deck Structure",
                    "subsection": "1: External Deck Structure",
                    "item_number": "1",
                    "description": "Decks clean, clear of oil, grease and non-slippery",
                }
            ],
            origin_y=640,
        )

        header_rule_y = pdf.lines[0][1]
        first_row_y = next(
            y
            for _x, y, text in pdf.strings
            if text == "1: External Deck Structure"
        )

        self.assertGreaterEqual(header_rule_y - first_row_y, 10)

    def _insert_area(
        self,
        *,
        area_id: int,
        area_name: str,
        section_12_flag: bool = False,
    ) -> None:
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
                [area_id, area_name, section_12_flag, area_id, True, "v1.0"],
            )

    def _insert_item(self, *, area_id: int, area_name: str, item_number: str) -> None:
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
                    int(f"{area_id}{item_number.replace('.', '')}"),
                    area_id,
                    area_name,
                    1,
                    "General",
                    item_number,
                    "Emergency lighting is inspected and available",
                    "BASELINE",
                    True,
                    "v1.0",
                    1,
                ],
            )


class _RecordingPdf:
    def __init__(self) -> None:
        self.lines: list[tuple[float, float, float, float]] = []
        self.strings: list[tuple[float, float, str]] = []

    def setFont(self, *_args) -> None:
        return None

    def drawString(self, x: float, y: float, text: str) -> None:
        self.strings.append((x, y, text))

    def line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.lines.append((x1, y1, x2, y2))

    def rect(self, *_args, **_kwargs) -> None:
        return None
