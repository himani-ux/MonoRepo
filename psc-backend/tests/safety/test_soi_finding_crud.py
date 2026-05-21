from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch
import uuid
import tempfile
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.soi_finding import SOIFindingListCreateView, SOIFindingPhotoUploadView


def build_user(
    *,
    role_name: str = "CO",
    process_ids: list[str] | None = None,
    user_id: str = "co-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_004"],
        process_ids=["SAF_P_002"] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class SOIFindingCrudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.view = SOIFindingListCreateView.as_view()
        self.photo_view = SOIFindingPhotoUploadView.as_view()
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_area(area_id=5, area_name="Mooring Deck + Forward Station")
        self._insert_item(item_id=301, area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_item(item_id=501, area_id=5, area_name="Mooring Deck + Forward Station")
        self.inspection_id = self._insert_inspection()
        self._insert_selected_area(area_id=3)

    def test_post_defaults_assignee_to_safety_officer_and_lists_findings(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 3,
                "checklist_unique_id": "SOI-UID-007",
                "description": "Lifebuoy line was found frayed during the bridge round.",
                "due_date": "2026-05-14",
                "priority": "MED",
                "severity": "MED",
                "title": "Frayed lifebuoy line",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["assigned_crew_id"], "co-7")
        self.assertEqual(response.data["inspection_id"], self.inspection_id)
        self.assertEqual(response.data["status"], "OPEN")
        self.assertEqual(response.data["area_id"], 3)
        self.assertIsNotNone(response.data["created_date"])

        list_request = self.factory.get(f"/api/safety/soi/{self.inspection_id}/findings/")
        force_authenticate(list_request, user=build_user(process_ids=[]))

        list_response = self.view(list_request, id=self.inspection_id)

        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["title"], "Frayed lifebuoy line")
        self.assertEqual(list_response.data[0]["assigned_crew_id"], "co-7")

    def test_post_accepts_liveware_liveware_shell_tag(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 3,
                "checklist_unique_id": "SOI-UID-007",
                "description": "Crew communication gap observed during deck access inspection.",
                "priority": "MED",
                "severity": "MED",
                "shell_tag": "Liveware-Liveware",
                "title": "Deck access communication gap",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["shell_tag"], "Liveware-Liveware")

    def test_non_safety_officer_role_cannot_register_finding(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 3,
                "checklist_unique_id": "SOI-UID-007",
                "description": "Portable light failed during round.",
                "priority": "LOW",
                "severity": "LOW",
                "title": "Portable light failed",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="MASTER", process_ids=["SAF_P_013"], user_id="master-7"),
        )

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 403)

    def test_high_severity_requires_photo(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 3,
                "checklist_unique_id": "SOI-UID-007",
                "description": "Missing emergency escape marker at the bridge exit.",
                "priority": "HIGH",
                "severity": "HIGH",
                "title": "Emergency escape marker missing",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("photo_attachment_path", response.data)

    def test_photo_upload_returns_relative_attachment_path_for_finding_payload(self) -> None:
        with tempfile.TemporaryDirectory() as storage_root, patch.dict(
            "os.environ",
            {"SAFETY_EXPORT_ROOT": storage_root},
        ):
            photo = SimpleUploadedFile(
                "bridge-marker.jpg",
                b"\xff\xd8\xff\xe0" + b"0" * 64,
                content_type="image/jpeg",
            )
            request = self.factory.post(
                f"/api/safety/soi/{self.inspection_id}/findings/photo/",
                {"photo": photo},
                format="multipart",
            )
            force_authenticate(request, user=build_user())

            response = self.photo_view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 201)
        self.assertIn("photo_attachment_path", response.data)
        self.assertTrue(response.data["photo_attachment_path"].endswith(".jpg"))
        self.assertIn(f"soi/{self.inspection_id}/findings/photos/", response.data["photo_attachment_path"])

        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 3,
                "checklist_unique_id": "SOI-UID-007",
                "description": "Emergency escape marker missing beside the bridge exit.",
                "incident_worthy_action": "KEEP_SOI_ONLY",
                "incident_worthy_reason": "Contained to the SOI finding because no crew injury or operational event occurred.",
                "photo_attachment_path": response.data["photo_attachment_path"],
                "priority": "HIGH",
                "severity": "HIGH",
                "title": "Emergency escape marker missing",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        create_response = self.view(request, id=self.inspection_id)

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["photo_attachment_path"], response.data["photo_attachment_path"])

    def test_rejects_findings_for_areas_not_selected_on_the_paper_checklist(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 5,
                "checklist_unique_id": "SOI-UID-007",
                "description": "Portable radio battery was below the required reserve.",
                "priority": "LOW",
                "severity": "LOW",
                "title": "Portable radio battery reserve low",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("area_id", response.data)

    def test_rejects_missing_or_mismatched_checklist_id(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 3,
                "checklist_unique_id": "WRONG-ID",
                "description": "Portable light failed during round.",
                "priority": "LOW",
                "severity": "LOW",
                "title": "Portable light failed",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("checklist_unique_id", response.data)

    def test_rejects_item_id_outside_selected_area(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 3,
                "checklist_unique_id": "SOI-UID-007",
                "description": "Portable light failed during round.",
                "item_id": 501,
                "priority": "LOW",
                "severity": "LOW",
                "title": "Portable light failed",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("item_id", response.data)

    def test_rejects_finding_create_after_inspection_is_closed(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE vims_safety_soi_inspection SET state = %s WHERE id = %s",
                ["CLOSED", self.inspection_id],
            )

        request = self.factory.post(
            f"/api/safety/soi/{self.inspection_id}/findings/",
            {
                "area_id": 3,
                "checklist_unique_id": "SOI-UID-007",
                "description": "Portable light failed during round.",
                "priority": "LOW",
                "severity": "LOW",
                "title": "Portable light failed",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.inspection_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("inspection_id", response.data)

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

    def _insert_item(self, *, item_id: int, area_id: int, area_name: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_soi_area_item (
                    id,
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
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    f"{item_id:032x}",
                    item_id,
                    area_id,
                    area_name,
                    1,
                    "General",
                    f"{area_id}.1",
                    "Checklist item text",
                    "BASELINE",
                    True,
                    "v1.0",
                    1,
                ],
            )

    def _insert_inspection(self) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_inspection (
                    public_id,
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
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(uuid.uuid4()),
                    "7",
                    "SOI/ABC/26/07",
                    "Q2/2026",
                    "DOWNLOADED",
                    date(2026, 5, 1),
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    "master-7",
                    "SOI-UID-007",
                    "2026-05-01 08:00:00",
                    "PDF",
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
                    public_id,
                    inspection_id,
                    area_id,
                    inspected,
                    last_inspected_at,
                    notes,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [str(uuid.uuid4()), self.inspection_id, area_id, False, None, None, 1],
            )
