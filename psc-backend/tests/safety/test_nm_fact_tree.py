from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
import unittest

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import EvidenceItem, Incident, IncidentFact
from apps.safety.views.near_miss_analysis import (
    NearMissAnalysisEvidenceSourceCreateView,
    NearMissAnalysisFactDetailView,
    NearMissAnalysisFactListCreateView,
    NearMissAnalysisWorkspaceView,
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
        form_ids=form_ids or ["SAF_F_002"],
        process_ids=process_ids or ["SAF_P_002"],
        vessel_ids=vessel_ids or ["7"],
        is_global=False,
    )


class NearMissFactTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.workspace_view = NearMissAnalysisWorkspaceView.as_view()
        self.evidence_create_view = NearMissAnalysisEvidenceSourceCreateView.as_view()
        self.list_create_view = NearMissAnalysisFactListCreateView.as_view()
        self.detail_view = NearMissAnalysisFactDetailView.as_view()
        self.near_miss = Incident.objects.create(
            incident_number="NM/2026/023",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="TRIAGED",
            current_phase=1,
            occurred_at=timezone.now() - timedelta(hours=1),
            near_miss_priority="HIGH",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
            narrative="A near-miss fact-tree workspace is needed because this high-priority case stayed within near-miss handling.",
        )
        self.evidence = EvidenceItem.objects.create(
            incident=self.near_miss,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title="Bridge photo",
            description="Photo proving the deck edge clearance issue.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

    def test_workspace_loads_fact_tree_only_payload_for_high_priority_near_miss(self) -> None:
        request = self.factory.get(f"/api/safety/near-miss/{self.near_miss.pk}/analysis/")
        force_authenticate(request, user=build_user())
        response = self.workspace_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["analysis_mode"], "FACT_TREE_ONLY")
        self.assertEqual(response.data["near_miss"]["id"], self.near_miss.pk)
        self.assertEqual(response.data["near_miss"]["near_miss_priority"], "HIGH")
        self.assertEqual(response.data["facts"], [])
        self.assertNotIn("causes", response.data)
        self.assertNotIn("safeguards", response.data)

    def test_workspace_supports_lightweight_near_miss_evidence_sources(self) -> None:
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/analysis/evidence/",
            {
                "evidence_type": "WITNESS_NOTE",
                "title": "Witness note - loose ladder pin",
                "description": "AB witness note recorded before the ladder pin was re-secured.",
                "source_label": "witness-note-1",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.evidence_create_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 201)
        labels = [row["label"] for row in response.data["evidence_sources"]]
        self.assertIn("Witness note - loose ladder pin", labels)
        source_ids = [row["id"] for row in response.data["evidence_sources"]]
        self.assertEqual(len(source_ids), len(set(source_ids)))

    def test_photo_evidence_requires_and_stores_image_attachment(self) -> None:
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/analysis/evidence/",
            {
                "evidence_type": "PHOTO",
                "title": "Photo - damaged pin",
                "description": "Image captured before the unsafe pin was secured.",
                "source_label": "phone-photo-2",
                "photo": SimpleUploadedFile(
                    "damaged-pin.png",
                    b"\x89PNG\r\n\x1a\n",
                    content_type="image/png",
                ),
            },
            format="multipart",
        )
        force_authenticate(request, user=build_user())

        response = self.evidence_create_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 201)
        evidence = EvidenceItem.objects.get(title="Photo - damaged pin")
        self.assertEqual(evidence.metadata_json["content_type"], "image/png")
        self.assertIn("attachment_path", evidence.metadata_json)
        self.assertIn("Photo - damaged pin", [row["label"] for row in response.data["evidence_sources"]])
        photo_source = next(row for row in response.data["evidence_sources"] if row["label"] == "Photo - damaged pin")
        self.assertTrue(photo_source["preview"]["preview_url"].endswith(f"/analysis/evidence/{evidence.pk}/photo/"))
        Path("var/www/ksm_uploads/safety", evidence.metadata_json["attachment_path"]).unlink(missing_ok=True)

    def test_fact_with_photo_evidence_returns_preview_metadata(self) -> None:
        photo_evidence = EvidenceItem.objects.create(
            incident=self.near_miss,
            item_type=EvidenceItem.ItemType.PHYSICAL,
            title="Photo - open hatch",
            description="Photo evidence linked to fact.",
            metadata_json={
                "attachment_path": "vessels/7/near-miss/1/analysis/photos/open-hatch.png",
                "content_type": "image/png",
                "file_name": "open-hatch.png",
            },
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/analysis/facts/",
            {
                "fact_text": "The hatch was open before the area was isolated.",
                "source_evidence_id": photo_evidence.pk,
                "confidence": IncidentFact.Confidence.HIGH,
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.list_create_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["evidence_preview"]["file_name"], "open-hatch.png")
        self.assertTrue(response.data["evidence_preview"]["preview_url"].endswith(f"/analysis/evidence/{photo_evidence.pk}/photo/"))

    def test_photo_evidence_rejects_missing_image_attachment(self) -> None:
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/analysis/evidence/",
            {
                "evidence_type": "PHOTO",
                "title": "Photo - missing upload",
                "description": "Photo evidence without the image file should not save.",
                "source_label": "phone-photo-3",
            },
            format="multipart",
        )
        force_authenticate(request, user=build_user())

        response = self.evidence_create_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("photo", response.data)

    def test_fact_tree_supports_add_edit_and_delete_without_causal_layer_fields(self) -> None:
        create_request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/analysis/facts/",
            {
                "fact_text": "The ladder pin was loose before any crew member stepped onto the platform.",
                "fact_timestamp": (self.near_miss.occurred_at - timedelta(minutes=3)).isoformat(),
                "source_evidence_id": self.evidence.pk,
                "confidence": IncidentFact.Confidence.HIGH,
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user())
        create_response = self.list_create_view(create_request, id=self.near_miss.pk)

        self.assertEqual(create_response.status_code, 201)
        self.assertNotIn("causal_layer", create_response.data)
        fact_id = create_response.data["id"]

        patch_request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/analysis/facts/{fact_id}/",
            {
                "fact_text": "The ladder pin was loose and the deck team secured the area immediately.",
                "confidence": IncidentFact.Confidence.MEDIUM,
            },
            format="json",
        )
        force_authenticate(patch_request, user=build_user())
        patch_response = self.detail_view(patch_request, id=self.near_miss.pk, fact_id=fact_id)

        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.data["confidence"], IncidentFact.Confidence.MEDIUM)
        self.assertTrue(
            patch_response.data["fact_text"].startswith("The ladder pin was loose and the deck team secured")
        )

        delete_request = self.factory.delete(
            f"/api/safety/near-miss/{self.near_miss.pk}/analysis/facts/{fact_id}/"
        )
        force_authenticate(delete_request, user=build_user())
        delete_response = self.detail_view(delete_request, id=self.near_miss.pk, fact_id=fact_id)

        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(self.near_miss.facts.count(), 0)

    def test_fact_sequence_duplicate_returns_validation_error(self) -> None:
        IncidentFact.objects.create(
            incident=self.near_miss,
            sequence_index=1,
            fact_text="Existing fact already uses sequence one.",
            source_evidence_id=self.evidence.pk,
            confidence=IncidentFact.Confidence.MEDIUM,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        request = self.factory.post(
            f"/api/safety/near-miss/{self.near_miss.pk}/analysis/facts/",
            {
                "fact_text": "Second fact accidentally uses the same sequence number.",
                "sequence_index": 1,
                "source_evidence_id": self.evidence.pk,
                "confidence": IncidentFact.Confidence.HIGH,
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.list_create_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("sequence_index", response.data)

    def test_low_priority_near_miss_is_rejected_from_lightweight_analysis_workspace(self) -> None:
        self.near_miss.near_miss_priority = "LOW"
        self.near_miss.save(update_fields=["near_miss_priority"])

        request = self.factory.get(f"/api/safety/near-miss/{self.near_miss.pk}/analysis/")
        force_authenticate(request, user=build_user())
        response = self.workspace_view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("HIGH-priority", str(response.data))
