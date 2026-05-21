from __future__ import annotations

from datetime import date, datetime, timedelta
from io import BytesIO
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest

from PyPDF2 import PdfReader

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django(root_urlconf="config.urls")

from django.db import connection
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SOIFinding, SOITrainee
from apps.safety.services.pdf_renderer import SOISummaryPdfRenderer
from apps.safety.views.soi_finding import SOISubmitFindingsView
from apps.safety.views.soi_pdf import SOISummaryPDFDownloadView


def build_user(*, role_name: str, process_ids: list[str], user_id: str = "co-7") -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_004"],
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


def aware(year: int, month: int, day: int, hour: int, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


class SOISummaryPdfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django(root_urlconf="config.urls")

    def setUp(self) -> None:
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.submit_view = SOISubmitFindingsView.as_view()
        self.download_view = SOISummaryPDFDownloadView.as_view()
        self.reported_at = aware(2026, 5, 6, 10, 15)
        self.inspection_id = self._insert_inspection()
        for area_id, area_name in (
            (3, "Navigating Bridge & Monkey Island"),
            (8, "Engine Control Room + Machinery Flat"),
        ):
            self._insert_area(area_id=area_id, area_name=area_name)
            self._insert_selected_area(area_id=area_id)
            self._insert_area_map(area_id=area_id)
        SOITrainee.objects.create(inspection_id=self.inspection_id, crew_id="cadet-17", trainee_slot=1, schema_version=1)

    def test_renderer_outputs_post_submission_summary_without_checklist_answers(self) -> None:
        SOIFinding.objects.create(
            inspection_id=self.inspection_id,
            area_id=3,
            item_id=3001,
            title="Bridge marker faded",
            description="The bridge marker paint is no longer legible and needs reapplication.",
            severity="HIGH",
            priority="HIGH",
            mscat_category_id=12,
            mscat_subcode_id="M-220",
            shell_tag="ENVIRONMENT",
            assigned_crew_id="co-7",
            status=SOIFinding.Status.PENDING_CLOSURE,
            photo_attachment_path="vessel-7/soi/bridge-marker-faded.jpg",
            created_by="co-7",
        )
        self._mark_submitted(state="REPORTED")

        result = SOISummaryPdfRenderer().render_soi_pdf(
            inspection_id=self.inspection_id,
            viewer_user=None,
            persist=False,
        )

        self.assertTrue(result.content.startswith(b"%PDF"))
        reader = PdfReader(BytesIO(result.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        self.assertIn("SOI Summary PDF", text)
        self.assertIn("Stamped Areas", text)
        self.assertIn("Findings", text)
        self.assertIn("Trainees", text)
        self.assertIn("Signatures", text)
        self.assertIn("Bridge marker faded", text)
        self.assertIn("M-220", text)
        self.assertIn("ENVIRONMENT", text)
        self.assertIn("Paper checklist: unique-ID SOI-UID-015, filed in ship SMS filing system.", text)
        self.assertIn("Audit trail: record ID", text)
        self.assertNotIn("Yes / No / N-A", text)

    def test_final_submit_generates_and_serves_soi_summary_pdf(self) -> None:
        SOIFinding.objects.create(
            inspection_id=self.inspection_id,
            area_id=3,
            item_id=3001,
            title="Bridge marker faded",
            description="The bridge marker paint is no longer legible and needs reapplication.",
            severity="LOW",
            priority="MED",
            assigned_crew_id="co-7",
            status=SOIFinding.Status.OPEN,
            created_by="co-7",
        )

        original_export_root = os.environ.get("SAFETY_EXPORT_ROOT")
        export_root = Path("test-output") / "soi-pdf-e2e"
        shutil.rmtree(export_root, ignore_errors=True)
        export_root.mkdir(parents=True, exist_ok=True)
        os.environ["SAFETY_EXPORT_ROOT"] = str(export_root)
        try:
            submit_request = self.factory.post(
                f"/api/safety/soi/{self.inspection_id}/submit/",
                {"submitted_area_ids": [3, 8]},
                format="json",
            )
            force_authenticate(
                submit_request,
                user=build_user(role_name="CO", process_ids=["SAF_P_002"]),
            )

            submit_response = self.submit_view(submit_request, id=self.inspection_id)

            self.assertEqual(submit_response.status_code, 200)
            self.assertEqual(submit_response.data["state"], "REPORTED")
            self.assertIn("pdf_export", submit_response.data)

            pdf_export = submit_response.data["pdf_export"]
            export_path = Path(pdf_export["export_path"])
            self.assertTrue(export_path.exists())
            self.assertIn(export_root.resolve(), export_path.parents)
            self.assertEqual(pdf_export["download_path"], f"/api/safety/soi/{self.inspection_id}/pdf/")

            download_request = self.factory.get(f"/api/safety/soi/{self.inspection_id}/pdf/")
            force_authenticate(
                download_request,
                user=build_user(role_name="MASTER", process_ids=["SAF_P_023"], user_id="master-7"),
            )
            download_response = self.download_view(download_request, id=self.inspection_id)

            self.assertEqual(download_response.status_code, 200)
            self.assertEqual(download_response["Content-Type"], "application/pdf")
            self.assertEqual(download_response["X-Safety-Export-Path"], str(export_path))
            self.assertEqual(download_response["X-Safety-Download-Path"], f"/api/safety/soi/{self.inspection_id}/pdf/")
        finally:
            shutil.rmtree(export_root, ignore_errors=True)
            if original_export_root is None:
                os.environ.pop("SAFETY_EXPORT_ROOT", None)
            else:
                os.environ["SAFETY_EXPORT_ROOT"] = original_export_root

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

    def _insert_inspection(self) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_inspection (
                    vessel_id,
                    inspection_reference,
                    cycle_label,
                    state,
                    planned_date,
                    safety_officer_crew_id,
                    safety_officer_department,
                    assistant_crew_id,
                    assistant_department,
                    master_crew_id,
                    checklist_unique_id,
                    checklist_generated_at,
                    checklist_format,
                    fieldwork_started_at,
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "7",
                    "SOI/ABC/26/15",
                    "Q2/2026",
                    "DOWNLOADED",
                    date(2026, 5, 5),
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    None,
                    "SOI-UID-015",
                    self.reported_at - timedelta(days=1),
                    "PDF",
                    self.reported_at - timedelta(hours=2),
                    False,
                    1,
                    False,
                    "co-7",
                ],
            )
            return int(cursor.lastrowid)

    def _insert_selected_area(self, *, area_id: int) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_inspection_area (
                    inspection_id,
                    area_id,
                    inspected,
                    last_inspected_at,
                    notes,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [self.inspection_id, area_id, False, None, None, 1],
            )

    def _insert_area_map(self, *, area_id: int) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_vessel_area_map (
                    vessel_id,
                    area_id,
                    applicable,
                    last_inspected_at,
                    due_at,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                ["7", area_id, True, None, None, 1],
            )

    def _mark_submitted(self, *, state: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE vims_safety_soi_inspection
                SET state = %s, reported_at = %s
                WHERE id = %s
                """,
                [state, self.reported_at, self.inspection_id],
            )
