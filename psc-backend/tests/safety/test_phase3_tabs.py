from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.safety.models import EvidenceItem, Incident, IncidentEvidence
from apps.safety.views.incident_phase3 import (
    IncidentPhase3AttachmentUploadView,
    IncidentPhase3EvidenceView,
    IncidentPhase3InterviewView,
)


def build_user(
    *,
    role_name: str = "MASTER",
    form_ids: list[str] | None = None,
    process_ids: list[str] | None = None,
    vessel_ids: list[str] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=form_ids or ["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_002"],
        vessel_ids=vessel_ids or ["7"],
        is_global=False,
    )


class IncidentPhase3TabsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = IncidentPhase3EvidenceView.as_view()
        self.attachment_view = IncidentPhase3AttachmentUploadView.as_view()
        self.interview_view = IncidentPhase3InterviewView.as_view()

    def test_phase3_tabs_accept_independent_writes_and_preserve_other_tabs(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        first_request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/evidence/",
            {
                "position": {
                    "summary": "Bridge wing photos and deck plan marked.",
                    "entry_count": 2,
                    "structured_data": {"deck_plan_overlay": True},
                },
                "people": {
                    "summary": "Witnesses identified and fatigue panel opened.",
                    "entry_count": 1,
                    "structured_data": {
                        "health_fatigue": {
                            "mlc_reportable": True,
                            "medical_records": ["clinic note"],
                        }
                    },
                },
                "parts": {
                    "summary": "Damaged valve photographed.",
                    "entry_count": 1,
                    "structured_data": {"manual_equipment_history_reference": "PMS-REF-77"},
                },
                "paper": {
                    "summary": "Deck log, engine log, and permits captured.",
                    "entry_count": 3,
                    "structured_data": {
                        "checklist_complete": True,
                        "cargo_overlay_items": [{"code": "ULLAGE", "status": "captured"}],
                    },
                },
                "electronic": {
                    "summary": "VDR request sent; AIS request queued.",
                    "entry_count": 2,
                    "structured_data": {"vdr_capture_status": "REQUESTED"},
                },
            },
            format="json",
        )
        force_authenticate(first_request, user=build_user())

        first_response = self.view(first_request, id=incident.pk)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response.data["position"]["entry_count"], 2)
        self.assertEqual(first_response.data["paper"]["entry_count"], 3)
        self.assertEqual(IncidentEvidence.objects.count(), 5)

        incident.refresh_from_db()
        self.assertTrue(incident.marine_docs_checklist_done)
        self.assertTrue(incident.cargo_evidence_applicable)
        self.assertTrue(incident.health_fatigue_applicable)

        second_request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/evidence/",
            {
                "people": {
                    "summary": "Witness list expanded to include duty officer.",
                    "entry_count": 2,
                    "structured_data": {"witnesses": ["AB Kumar", "Duty Officer"]},
                }
            },
            format="json",
        )
        force_authenticate(second_request, user=build_user())

        second_response = self.view(second_request, id=incident.pk)

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(
            second_response.data["people"]["summary"],
            "Witness list expanded to include duty officer.",
        )
        self.assertEqual(
            second_response.data["position"]["summary"],
            "Bridge wing photos and deck plan marked.",
        )
        self.assertEqual(IncidentEvidence.objects.count(), 5)

    def test_phase3_photo_upload_stores_attachment_metadata_in_evidence_item(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/002",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        with tempfile.TemporaryDirectory() as storage_root, patch.dict(
            "os.environ",
            {"SAFETY_EXPORT_ROOT": storage_root},
        ):
            photo = SimpleUploadedFile(
                "four-angle-view.jpg",
                b"\xff\xd8\xff\xe0" + b"1" * 64,
                content_type="image/jpeg",
            )
            request = self.factory.post(
                f"/api/safety/incidents/{incident.pk}/evidence/attachments/",
                {
                    "photo": photo,
                    "tab_key": "electronic",
                },
                format="multipart",
            )
            force_authenticate(request, user=build_user())

            response = self.attachment_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 201)
        self.assertIn("attachment", response.data)
        attachment_path = response.data["attachment"]["attachment_path"]
        self.assertIn(f"incidents/{incident.pk}/phase-3/electronic/", attachment_path)

        tab = IncidentEvidence.objects.get(incident=incident, tab_code=IncidentEvidence.TabCode.ELECTRONIC)
        self.assertEqual(tab.entry_count, 1)
        self.assertEqual(tab.structured_data["attachments"][0]["attachment_path"], attachment_path)

        item = EvidenceItem.objects.get(incident=incident, item_type=EvidenceItem.ItemType.PHYSICAL)
        self.assertEqual(item.metadata_json["attachment_path"], attachment_path)

    def test_phase3_interview_create_counts_people_evidence_tab(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/003",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/interviews/",
            {
                "witness_name": "AB Witness",
                "interview_type": "INFORMAL",
                "reason_formal_impossible": "Initial short statement only.",
                "meeting_notes": "Witness saw the alarm first.",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.interview_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 201)
        tab = IncidentEvidence.objects.get(incident=incident, tab_code=IncidentEvidence.TabCode.PEOPLE)
        self.assertEqual(tab.entry_count, 1)
        self.assertIn("Witness", tab.summary)
