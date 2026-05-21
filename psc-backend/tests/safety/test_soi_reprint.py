from __future__ import annotations

from datetime import date
from io import BytesIO
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.utils import timezone
from openpyxl import load_workbook
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SOIInspection, SOIInspectionArea
from apps.safety.views.soi_reprint import SOIReprintView


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


class SOIReprintTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.view = SOIReprintView.as_view()
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_area(area_id=13, area_name="Cross-cutting Safety & Culture", section_12_flag=True)

    def test_reason_is_required_for_lost_paper_recovery(self) -> None:
        inspection = self._create_downloaded_inspection()

        response = self._recover(
            inspection_id=inspection.id,
            payload={"reason": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["reason"][0], "Lost-paper recovery requires a reason.")

    def test_reprint_reuses_same_unique_id_and_logs_note(self) -> None:
        inspection = self._create_downloaded_inspection()

        response = self._recover(
            inspection_id=inspection.id,
            payload={"format": "xlsx", "reason": "Checklist soaked during deck round."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(response.content[:2], b"PK")
        workbook = load_workbook(BytesIO(response.content))
        self.assertEqual(workbook.active["B3"].value, "SOI-0000007-20260501-0001")

        inspection.refresh_from_db()
        self.assertEqual(inspection.checklist_unique_id, "SOI-0000007-20260501-0001")
        self.assertTrue(inspection.lost_paper_flag)
        self.assertIsNotNone(inspection.lost_paper_note)
        self.assertIn("Checklist soaked during deck round.", inspection.lost_paper_note)
        self.assertIn("Lost/damaged paper reported by co-7", inspection.lost_paper_note)
        self.assertRegex(
            inspection.lost_paper_note,
            r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
        )

    def test_reprint_requires_existing_download(self) -> None:
        inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/ABC/26/02",
            cycle_label="Q2/2026",
            planned_date=date(2026, 5, 2),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            created_by="co-7",
        )
        SOIInspectionArea.objects.create(inspection_id=inspection.id, area_id=3, schema_version=1)

        response = self._recover(
            inspection_id=inspection.id,
            payload={"reason": "Checklist blew overboard."},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data[0],
            "Lost-paper recovery is only available after the checklist has been downloaded.",
        )

    def _create_downloaded_inspection(self) -> SOIInspection:
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
            checklist_generated_at=timezone.now(),
            checklist_format=SOIInspection.ChecklistFormat.PDF,
            state=SOIInspection.State.DOWNLOADED,
            created_by="co-7",
        )
        SOIInspectionArea.objects.create(inspection_id=inspection.id, area_id=3, schema_version=1)
        SOIInspectionArea.objects.create(inspection_id=inspection.id, area_id=13, schema_version=1)
        return inspection

    def _recover(self, *, inspection_id: int, payload: dict[str, object]):
        request = self.factory.post(
            f"/api/safety/soi/{inspection_id}/lost-paper/recover/",
            payload,
            format="json",
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
