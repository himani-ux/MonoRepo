from __future__ import annotations

from datetime import date
from io import BytesIO
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection
from openpyxl import load_workbook
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SOIInspection, SOIInspectionArea
from apps.safety.views.soi_download import SOIDownloadView


def build_user():
    return SimpleNamespace(
        id="co-7",
        username="co-7",
        role_name="CO",
        form_ids=["SAF_F_004"],
        process_ids=["SAF_P_001"],
        vessel_ids=["7"],
        is_global=False,
    )


class SOIIdempotentDownloadTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.view = SOIDownloadView.as_view()
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_area(area_id=13, area_name="Cross-cutting Safety & Culture", section_12_flag=True)

    def test_repeat_download_reuses_same_unique_id_and_binary(self) -> None:
        inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/ABC/26/01",
            cycle_label="Q2/2026",
            planned_date=date(2026, 5, 1),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            created_by="co-7",
        )
        SOIInspectionArea.objects.create(inspection_id=inspection.id, area_id=3, schema_version=1)
        SOIInspectionArea.objects.create(inspection_id=inspection.id, area_id=13, schema_version=1)

        first_response = self._download(inspection_id=inspection.id, output_format="pdf")
        second_response = self._download(inspection_id=inspection.id, output_format="pdf")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(first_response["Content-Type"], "application/pdf")
        self.assertEqual(second_response["Content-Type"], "application/pdf")
        self.assertEqual(first_response.content, second_response.content)
        self.assertEqual(first_response["Content-Disposition"], second_response["Content-Disposition"])

        inspection.refresh_from_db()
        self.assertEqual(inspection.state, SOIInspection.State.DOWNLOADED)
        self.assertEqual(inspection.checklist_format, SOIInspection.ChecklistFormat.PDF)
        self.assertIsNotNone(inspection.checklist_generated_at)
        self.assertRegex(
            str(inspection.checklist_unique_id),
            r"^SOI-\d{7}-20260501-\d{4}$",
        )

    def test_download_accepts_uppercase_pdf_and_xlsx_query_values(self) -> None:
        pdf_inspection = self._create_inspection(reference="SOI/ABC/26/02")
        xlsx_inspection = self._create_inspection(reference="SOI/ABC/26/03")

        pdf_response = self._download(inspection_id=pdf_inspection.id, output_format="PDF")
        xlsx_response = self._download(inspection_id=xlsx_inspection.id, output_format="XLSX")

        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertEqual(xlsx_response.status_code, 200)
        self.assertIn(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            xlsx_response["Content-Type"],
        )

    def test_xlsx_download_after_pdf_returns_real_openxml_workbook(self) -> None:
        inspection = self._create_inspection(reference="SOI/ABC/26/04")

        pdf_response = self._download(inspection_id=inspection.id, output_format="PDF")
        xlsx_response = self._download(inspection_id=inspection.id, output_format="XLSX")

        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response.content[:4], b"%PDF")
        self.assertEqual(xlsx_response.status_code, 200)
        self.assertEqual(xlsx_response.content[:2], b"PK")
        workbook = load_workbook(BytesIO(xlsx_response.content))
        self.assertEqual(workbook.active["B2"].value, "SOI/ABC/26/04")

    def _create_inspection(self, *, reference: str) -> SOIInspection:
        inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference=reference,
            cycle_label="Q2/2026",
            planned_date=date(2026, 5, 1),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            created_by="co-7",
        )
        SOIInspectionArea.objects.create(inspection_id=inspection.id, area_id=3, schema_version=1)
        return inspection

    def _download(self, *, inspection_id: int, output_format: str):
        request = self.factory.get(
            f"/api/safety/soi/{inspection_id}/checklist/download/",
            {"format": output_format},
        )
        force_authenticate(request, user=build_user())
        return self.view(request, id=inspection_id)

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
