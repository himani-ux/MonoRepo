from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch
import tempfile
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.safety.models import EvidenceItem, Incident, IncidentEvidence, WitnessInterview
from apps.safety.views.incident_phase3 import (
    IncidentPhase3AttachmentUploadView,
    IncidentPhase3EvidenceView,
    IncidentPhase3InterviewAttachmentView,
    IncidentPhase3InterviewDetailView,
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
        self.interview_attachment_view = IncidentPhase3InterviewAttachmentView.as_view()
        self.interview_detail_view = IncidentPhase3InterviewDetailView.as_view()

    def test_phase3_tabs_accept_independent_writes_and_preserve_other_tabs(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
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

    def test_phase4_document_evidence_is_available_before_phase_four_is_reached(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/001-EARLY-EVIDENCE",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=2,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        get_request = self.factory.get(f"/api/safety/incidents/{incident.pk}/phase-4/evidence/")
        force_authenticate(get_request, user=build_user())

        get_response = self.view(get_request, id=incident.pk)

        self.assertEqual(get_response.status_code, 200)
        self.assertIn("paper", get_response.data)

        with tempfile.TemporaryDirectory() as storage_root, patch.dict(
            "os.environ",
            {"SAFETY_EXPORT_ROOT": storage_root},
        ):
            document = SimpleUploadedFile(
                "early-evidence.pdf",
                b"%PDF-1.4\n%early\n",
                content_type="application/pdf",
            )
            upload_request = self.factory.post(
                f"/api/safety/incidents/{incident.pk}/phase-4/evidence/attachments/",
                {
                    "description": "Uploaded before root cause and next actions were completed.",
                    "file": document,
                    "tab_key": "paper",
                    "title": "Early evidence upload",
                },
                format="multipart",
            )
            force_authenticate(upload_request, user=build_user())

            upload_response = self.attachment_view(upload_request, id=incident.pk)

        self.assertEqual(upload_response.status_code, 201)
        self.assertEqual(upload_response.data["attachment"]["title"], "Early evidence upload")
        tab = IncidentEvidence.objects.get(incident=incident, tab_code=IncidentEvidence.TabCode.PAPER)
        self.assertEqual(tab.entry_count, 1)

    def test_phase3_photo_upload_stores_attachment_metadata_in_evidence_item(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/002",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
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

    def test_phase3_pdf_upload_stores_attachment_metadata_in_evidence_item(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/002-PDF",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        with tempfile.TemporaryDirectory() as storage_root, patch.dict(
            "os.environ",
            {"SAFETY_EXPORT_ROOT": storage_root},
        ):
            document = SimpleUploadedFile(
                "engine-log.pdf",
                b"%PDF-1.4\n%test\n",
                content_type="application/pdf",
            )
            request = self.factory.post(
                f"/api/safety/incidents/{incident.pk}/evidence/attachments/",
                {
                    "file": document,
                    "description": "Deck and engine log pages relevant to the incident.",
                    "tab_key": "paper",
                    "title": "Engine log extract",
                },
                format="multipart",
            )
            force_authenticate(request, user=build_user())

            response = self.attachment_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 201)
        attachment = response.data["attachment"]
        self.assertEqual(attachment["content_type"], "application/pdf")
        self.assertEqual(attachment["description"], "Deck and engine log pages relevant to the incident.")
        self.assertEqual(attachment["title"], "Engine log extract")
        self.assertTrue(attachment["attachment_path"].endswith(".pdf"))

        tab = IncidentEvidence.objects.get(incident=incident, tab_code=IncidentEvidence.TabCode.PAPER)
        self.assertEqual(tab.entry_count, 1)
        self.assertEqual(tab.structured_data["attachments"][0]["content_type"], "application/pdf")
        self.assertEqual(tab.structured_data["attachments"][0]["description"], "Deck and engine log pages relevant to the incident.")
        self.assertEqual(tab.structured_data["attachments"][0]["title"], "Engine log extract")

        item = EvidenceItem.objects.get(incident=incident, item_type=EvidenceItem.ItemType.PHYSICAL)
        self.assertEqual(item.metadata_json["attachment_path"], attachment["attachment_path"])
        self.assertEqual(item.description, "Deck and engine log pages relevant to the incident.")
        self.assertEqual(item.metadata_json["description"], "Deck and engine log pages relevant to the incident.")
        self.assertEqual(item.metadata_json["title"], "Engine log extract")
        self.assertEqual(item.title, "Engine log extract")

    def test_phase4_document_metadata_patch_updates_existing_attachment(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/002-PDF-EDIT",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        with tempfile.TemporaryDirectory() as storage_root, patch.dict(
            "os.environ",
            {"SAFETY_EXPORT_ROOT": storage_root},
        ):
            document = SimpleUploadedFile(
                "engine-log.pdf",
                b"%PDF-1.4\n%test\n",
                content_type="application/pdf",
            )
            upload_request = self.factory.post(
                f"/api/safety/incidents/{incident.pk}/phase-4/evidence/attachments/",
                {
                    "file": document,
                    "description": "Initial description.",
                    "tab_key": "paper",
                    "title": "Initial title",
                },
                format="multipart",
            )
            force_authenticate(upload_request, user=build_user())
            upload_response = self.attachment_view(upload_request, id=incident.pk)

            attachment_path = upload_response.data["attachment"]["attachment_path"]
            patch_request = self.factory.patch(
                f"/api/safety/incidents/{incident.pk}/phase-4/evidence/attachments/?path={attachment_path}",
                {
                    "description": "Updated description for the same file.",
                    "title": "Updated engine log",
                },
                format="json",
            )
            force_authenticate(patch_request, user=build_user())
            patch_response = self.attachment_view(patch_request, id=incident.pk)

        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.data["attachment"]["attachment_path"], attachment_path)
        self.assertEqual(patch_response.data["attachment"]["title"], "Updated engine log")

        tab = IncidentEvidence.objects.get(incident=incident, tab_code=IncidentEvidence.TabCode.PAPER)
        self.assertEqual(tab.entry_count, 1)
        self.assertEqual(len(tab.structured_data["attachments"]), 1)
        self.assertEqual(tab.structured_data["attachments"][0]["title"], "Updated engine log")
        self.assertEqual(
            tab.structured_data["attachments"][0]["description"],
            "Updated description for the same file.",
        )

        item = EvidenceItem.objects.get(incident=incident, item_type=EvidenceItem.ItemType.PHYSICAL)
        self.assertEqual(item.title, "Updated engine log")
        self.assertEqual(item.description, "Updated description for the same file.")
        self.assertEqual(item.metadata_json["attachment_path"], attachment_path)

    def test_phase3_interview_create_counts_people_evidence_tab(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/003",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
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

    def test_phase4_interview_patch_updates_existing_witness_statement(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/004",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        interview = WitnessInterview.objects.create(
            incident=incident,
            witness_name="AB Witness",
            interview_type=WitnessInterview.InterviewType.INFORMAL,
            reason_formal_impossible="Initial statement only.",
            meeting_notes="Original statement.",
            conclusion_notes="Original remark.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/phase-4/interviews/{interview.id}/",
            {
                "conclusion_notes": "Updated remark.",
                "interview_type": "INFORMAL",
                "meeting_notes": "Updated statement.",
                "reason_formal_impossible": "Initial statement only.",
                "witness_name": "AB Witness",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.interview_detail_view(request, id=incident.pk, interview_id=interview.id)

        self.assertEqual(response.status_code, 200)
        interview.refresh_from_db()
        self.assertEqual(WitnessInterview.objects.filter(incident=incident).count(), 1)
        self.assertEqual(interview.meeting_notes, "Updated statement.")
        self.assertEqual(interview.conclusion_notes, "Updated remark.")

    def test_phase4_interview_statement_attachment_downloads_data_url(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/004-STATEMENT-DOWNLOAD",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=4,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        interview = WitnessInterview.objects.create(
            incident=incident,
            witness_name="AB Witness",
            interview_type=WitnessInterview.InterviewType.INFORMAL,
            reason_formal_impossible="Statement uploaded from Phase 4.",
            meeting_notes="Witness statement.",
            conclusion_notes="Remark.",
            witness_signature="data:application/pdf;base64,JVBERi0xLjQKJXdpdG5lc3MK",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        request = self.factory.get(
            f"/api/safety/incidents/{incident.pk}/phase-4/interviews/{interview.id}/statement-attachment/"
        )
        force_authenticate(request, user=build_user())

        response = self.interview_attachment_view(request, id=incident.pk, interview_id=interview.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("witness-statement-", response["Content-Disposition"])
        self.assertEqual(response.content, b"%PDF-1.4\n%witness\n")
