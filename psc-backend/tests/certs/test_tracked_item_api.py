from __future__ import annotations

import os
import unittest
from unittest.mock import ANY, MagicMock, patch
import uuid

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import resolve
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.accounts.backends import AuthenticatedUser
from apps.certs.services.tracked_item_repository import TrackedItemPage, TrackedItemRepository
from apps.certs.views.tracked_item_views import (
    TrackedItemApproveView,
    TrackedItemDetailView,
    TrackedItemListCreateView,
    TrackedItemQuarantineResolveView,
    TrackedItemRejectView,
    TrackedItemSubmitView,
    TrackedItemUploadPdfView,
    _parse_ocr_date,
)


def make_user(
    *,
    role: str,
    form_ids: list[str],
    process_ids: list[str],
    user_type: str = "OFFICE",
    vessel_id: str | None = None,
    vessel_ids: list[str] | None = None,
    has_global_vessel_access: bool | None = None,
) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=f"{role.lower().replace(' ', '-')}-1",
        user_type=user_type,
        full_name=f"{role} User",
        role=role,
        employee_id=f"{role[:3].upper()}001",
        vessel_id=vessel_id,
        vessel_ids=vessel_ids,
        has_global_vessel_access=has_global_vessel_access,
        form_ids=form_ids,
        process_ids=process_ids,
    )


def tracked_item_row(**overrides):
    row = {
        "tracked_item_id": uuid.uuid4(),
        "vessel_id": uuid.uuid4(),
        "catalog_id": uuid.uuid4(),
        "catalog_code": "STAT-IOPP",
        "catalog_display_name": "International Oil Pollution Prevention Certificate",
        "catalog_short_name": "IOPP",
        "catalog_submission_scope": "all_ranks_with_approval",
        "type": "certificate",
        "validity_type": "full",
        "form_variant": None,
        "cadence_months": 60,
        "cadence_custom_days": None,
        "parent_id": None,
        "relationship_type": None,
        "supersedes_id": None,
        "issue_date": "2026-01-01",
        "expiry_date": "2031-01-01",
        "anniversary_date": "2026-01-01",
        "window_open": "2030-10-01",
        "window_close": "2031-01-01",
        "last_done_date": "2026-01-01",
        "next_due_date": "2031-01-01",
        "postponed_until": None,
        "status": "ok",
        "certificate_number": "IOPP-001",
        "issuing_authority": "Flag",
        "place_of_issue": "Bangkok",
        "extension_authority": None,
        "extension_letter_pdf_id": None,
        "extension_reason": None,
        "pdf_attachment_id": None,
        "pdf_missing": False,
        "source": "manual",
        "last_class_sync_id": None,
        "approval_state": "approved",
        "submitted_by": None,
        "submitted_at": None,
        "approved_by": "dpa-1",
        "approved_at": "2026-06-25T00:00:00Z",
        "rejection_reason": None,
        "rejection_count": 0,
        "draft_expires_at": None,
        "lifecycle_status": "active",
        "row_version": b"\x00\x00\x00\x00\x00\x00\x00\x01",
        "version": 1,
        "created_at": "2026-06-25T00:00:00Z",
        "created_by": "dpa-1",
        "updated_at": "2026-06-25T00:00:00Z",
        "updated_by": "dpa-1",
    }
    row.update(overrides)
    return row


def pdf_blob_row(**overrides):
    row = {
        "blob_id": uuid.uuid4(),
        "tracked_item_id": uuid.uuid4(),
        "snapshot_id": None,
        "blob_storage_path": "certs/vessels/vessel-1/tracked/tracked-1/example.pdf",
        "content_sha256": "a" * 64,
        "filename": "IOPP.pdf",
        "content_size_bytes": 123456,
        "uploaded_by": "master-1",
        "uploaded_at": "2026-06-25T00:00:00Z",
        "is_active": True,
        "superseded_at": None,
        "retention_policy": "retain_18_months_then_purge",
        "scheduled_delete_at": None,
        "delete_pending_since": None,
        "dpa_retention_override_until": None,
        "ocr_payload_json": None,
        "ocr_confidence_per_field": None,
        "ocr_processed_at": None,
        "ocr_engine_version": None,
    }
    row.update(overrides)
    return row


def approval_event_row(**overrides):
    row = {
        "event_id": uuid.uuid4(),
        "tracked_item_id": uuid.uuid4(),
        "from_state": "draft",
        "to_state": "pending_master_approval",
        "actor_user_id": "chief-officer-1",
        "actor_role": "Chief Officer",
        "reason": "Submitted renewal evidence.",
        "timestamp_utc": "2026-06-25T00:00:00Z",
    }
    row.update(overrides)
    return row


def audit_log_row(**overrides):
    row = {
        "audit_id": uuid.uuid4(),
        "timestamp_utc": "2026-06-25T00:00:00Z",
        "vessel_id": uuid.uuid4(),
        "actor_user_id": "dpa-1",
        "actor_role": "DPA",
        "action": "update_tracked_item",
        "entity_type": "tracked_item",
        "entity_id": uuid.uuid4(),
        "before_json": None,
        "after_json": None,
        "reason": "Corrected certificate number.",
        "event_metadata": None,
        "retention_tier": "hot",
        "archived_at": None,
        "schema_version": 1,
    }
    row.update(overrides)
    return row


def change_log_row(**overrides):
    row = {
        "change_id": uuid.uuid4(),
        "tracked_item_id": uuid.uuid4(),
        "field_name": "certificate_number",
        "old_value": '"OLD"',
        "new_value": '"NEW"',
        "version_after": 2,
        "source_module": "CERTS",
        "source_ref": "api.certs.tracked_items",
        "changed_by": "dpa-1",
        "changed_at": "2026-06-25T00:00:00Z",
    }
    row.update(overrides)
    return row


class CertTrackedItemApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.reader = make_user(role="Fleet Manager", form_ids=["CERT_F_002"], process_ids=[])
        self.catalog_reader = make_user(role="Fleet Manager", form_ids=["CERT_F_001"], process_ids=[])
        self.dpa_writer = make_user(role="DPA", form_ids=["CERT_F_002"], process_ids=["CERT_P_001"])

    def test_uppercase_sql_server_tracked_item_ids_resolve_to_detail_and_upload_routes(self) -> None:
        uppercase_id = "71BDA68C-6F74-F111-ADE9-DA27151DA903"

        detail_match = resolve(f"/api/certs/tracked-items/{uppercase_id}/")
        upload_match = resolve(f"/api/certs/tracked-items/{uppercase_id}/upload-pdf/")

        self.assertIs(detail_match.func.view_class, TrackedItemDetailView)
        self.assertEqual(detail_match.kwargs["tracked_item_id"], uppercase_id)
        self.assertIs(upload_match.func.view_class, TrackedItemUploadPdfView)
        self.assertEqual(upload_match.kwargs["tracked_item_id"], uppercase_id)

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_list_requires_tracked_item_form_id(self, repository) -> None:
        request = self.factory.get("/api/certs/tracked-items/")
        force_authenticate(request, user=self.catalog_reader)

        response = TrackedItemListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.list_items.assert_not_called()

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_list_serializes_field_map_keys_and_computes_permanent_status(self, repository) -> None:
        row = tracked_item_row(validity_type="permanent", expiry_date=None, status="ok")
        repository.list_items.return_value = TrackedItemPage(count=1, results=[row])
        request = self.factory.get(f"/api/certs/tracked-items/?vesselId={row['vessel_id']}")
        force_authenticate(request, user=self.reader)

        response = TrackedItemListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data["results"][0]
        self.assertEqual(item["id"], str(row["tracked_item_id"]))
        self.assertEqual(item["catalogCode"], "STAT-IOPP")
        self.assertEqual(item["validityType"], "permanent")
        self.assertEqual(item["status"], "permanent")
        self.assertEqual(item["approvalState"], "approved")
        self.assertEqual(item["pdfMissing"], False)
        self.assertEqual(item["version"], 1)
        repository.list_items.assert_called_once_with(vessel_id=str(row["vessel_id"]), catalog_id=None, status_value=None)

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_detail_returns_phase_2_6_panel_aggregate(self, repository) -> None:
        row_id = uuid.uuid4()
        vessel_id = uuid.uuid4()
        submitted_by = "7e051002-a5ac-ef11-a9fa-9506b4da1af9"
        approved_by = "dpa-1"
        row = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            vessel_name="SFYC ARAYA",
            vessel_code="SFA",
            vessel_imo_number="9487043",
            pdf_missing=True,
            submitted_by=submitted_by,
            approved_by=approved_by,
        )
        repository.get_item.return_value = row
        repository.list_pdf_versions.return_value = [pdf_blob_row(tracked_item_id=row_id, uploaded_by=submitted_by)]
        repository.list_approval_events.return_value = [approval_event_row(tracked_item_id=row_id, actor_user_id=submitted_by)]
        repository.list_audit_events.return_value = [audit_log_row(entity_id=row_id, vessel_id=vessel_id, actor_user_id=approved_by)]
        repository.list_change_history.return_value = [change_log_row(tracked_item_id=row_id, changed_by=approved_by)]
        request = self.factory.get(f"/api/certs/tracked-items/{row_id}/")
        force_authenticate(request, user=self.reader)

        display_names = {
            submitted_by: "CHIEF OFFICER - Chaiwut Kwangkaeo",
            approved_by: "DPA - DPA User",
        }
        with patch(
            "apps.certs.serializers.tracked_item.resolve_principal_display_name",
            side_effect=lambda identifier: display_names.get(str(identifier)),
        ):
            response = TrackedItemDetailView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(row_id))
        self.assertEqual(response.data["vesselName"], "SFYC ARAYA")
        self.assertEqual(response.data["vesselCode"], "SFA")
        self.assertEqual(response.data["vesselImo"], "9487043")
        self.assertEqual(response.data["submittedByDisplay"], "CHIEF OFFICER - Chaiwut Kwangkaeo")
        self.assertEqual(response.data["approvedByDisplay"], "DPA - DPA User")
        self.assertTrue(response.data["pdfMissing"])
        self.assertEqual(response.data["pdfVersions"][0]["filename"], "IOPP.pdf")
        self.assertEqual(response.data["pdfVersions"][0]["uploadedByDisplay"], "CHIEF OFFICER - Chaiwut Kwangkaeo")
        self.assertEqual(response.data["approvalEvents"][0]["toState"], "pending_master_approval")
        self.assertEqual(response.data["approvalEvents"][0]["actorDisplayName"], "CHIEF OFFICER - Chaiwut Kwangkaeo")
        self.assertEqual(response.data["auditEvents"][0]["action"], "update_tracked_item")
        self.assertEqual(response.data["auditEvents"][0]["actorDisplayName"], "DPA - DPA User")
        self.assertEqual(response.data["changeHistory"][0]["fieldName"], "certificate_number")
        self.assertEqual(response.data["changeHistory"][0]["changedByDisplay"], "DPA - DPA User")
        repository.list_pdf_versions.assert_called_once_with(str(row_id))
        repository.list_approval_events.assert_called_once_with(str(row_id))
        repository.list_audit_events.assert_called_once_with(str(row_id))
        repository.list_change_history.assert_called_once_with(str(row_id))

    @patch("apps.certs.views.tracked_item_views.record_cert_change_log")
    @patch("apps.certs.views.tracked_item_views.record_audit_event")
    @patch("apps.certs.views.tracked_item_views.process_cert_pdf")
    @patch("apps.certs.views.tracked_item_views.save_uploaded_cert_pdf")
    @patch("apps.certs.views.tracked_item_views.pdf_repository")
    @patch("apps.certs.views.tracked_item_views.repository")
    def test_upload_pdf_processes_ocr_and_records_upload_and_ocr_audits(
        self,
        repository,
        pdf_repository,
        save_uploaded_cert_pdf,
        process_cert_pdf,
        record_audit_event,
        record_cert_change_log,
    ) -> None:
        row_id = uuid.uuid4()
        vessel_id = uuid.uuid4()
        blob_id = uuid.uuid4()
        item = tracked_item_row(tracked_item_id=row_id, vessel_id=vessel_id, pdf_missing=True)
        repository.get_item.return_value = item
        repository.update_item.return_value = (
            item,
            tracked_item_row(
                tracked_item_id=row_id,
                vessel_id=vessel_id,
                pdf_attachment_id=blob_id,
                pdf_missing=False,
                version=2,
            ),
        )
        save_uploaded_cert_pdf.return_value = {
            "relative_path": "certs/vessels/vessel-1/tracked/item-1/iopp.pdf",
            "absolute_path": "C:/tmp/iopp.pdf",
            "sha256": "b" * 64,
            "size": 29,
            "filename": "iopp.pdf",
        }
        pdf_repository.create_blob_for_tracked_item.return_value = pdf_blob_row(
            blob_id=blob_id,
            tracked_item_id=row_id,
            content_sha256="b" * 64,
            content_size_bytes=29,
            filename="iopp.pdf",
        )
        ocr_payload = {
            "schema_version": "certs-ocr-v1",
            "engine": "static-test",
            "context": "office",
            "status": "processed",
            "unprocessable": False,
            "fields": {
                "imo_number": {
                    "value": "9876543",
                    "raw_value": "9876543",
                    "confidence": 0.82,
                    "mode": "auto_accept",
                    "threshold": 0.8,
                    "manual_floor": 0.6,
                },
                "certificate_number": {
                    "value": None,
                    "raw_value": "IOPP-001",
                    "confidence": 0.58,
                    "mode": "manual_entry",
                    "threshold": 0.8,
                    "manual_floor": 0.6,
                },
            },
        }
        process_cert_pdf.return_value = ocr_payload
        pdf_repository.update_ocr_result.return_value = pdf_blob_row(
            blob_id=blob_id,
            tracked_item_id=row_id,
            ocr_payload_json='{"status":"processed"}',
            ocr_confidence_per_field='{"imo_number":0.82,"certificate_number":0.58}',
            ocr_processed_at="2026-06-26T10:00:00Z",
            ocr_engine_version="static-test",
        )
        upload = SimpleUploadedFile("iopp.pdf", b"%PDF-1.4 cert body", content_type="application/pdf")
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/upload-pdf/",
            {"file": upload, "reason": "Uploading renewed certificate PDF."},
            format="multipart",
        )
        force_authenticate(request, user=self.dpa_writer)

        response = TrackedItemUploadPdfView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["pdfBlob"]["id"], str(blob_id))
        self.assertEqual(response.data["ocrPayload"]["fields"]["imo_number"]["mode"], "auto_accept")
        self.assertEqual(response.data["ocrConfidencePerField"]["certificate_number"], 0.58)
        save_uploaded_cert_pdf.assert_called_once()
        pdf_repository.create_blob_for_tracked_item.assert_called_once()
        process_cert_pdf.assert_called_once_with("C:/tmp/iopp.pdf", context="office")
        pdf_repository.update_ocr_result.assert_called_once_with(str(blob_id), ocr_payload)
        self.assertEqual([call.kwargs["action"] for call in record_audit_event.call_args_list], ["upload_pdf", "ocr_processed"])
        record_cert_change_log.assert_called_once()

    def test_upload_ocr_date_parser_accepts_full_month_names(self) -> None:
        self.assertEqual(_parse_ocr_date("15 January 2024"), "2024-01-15")

    @patch("apps.certs.views.tracked_item_views.record_cert_change_log")
    @patch("apps.certs.views.tracked_item_views.record_audit_event")
    @patch("apps.certs.views.tracked_item_views.process_cert_pdf")
    @patch("apps.certs.views.tracked_item_views.save_uploaded_cert_pdf")
    @patch("apps.certs.views.tracked_item_views.pdf_repository")
    @patch("apps.certs.views.tracked_item_views.repository")
    def test_upload_pdf_auto_applies_high_confidence_ocr_metadata(
        self,
        repository,
        pdf_repository,
        save_uploaded_cert_pdf,
        process_cert_pdf,
        record_audit_event,
        record_cert_change_log,
    ) -> None:
        row_id = uuid.uuid4()
        vessel_id = uuid.uuid4()
        blob_id = uuid.uuid4()
        item = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            status="pending_first_upload",
            certificate_number=None,
            issuing_authority="Class",
            place_of_issue=None,
            issue_date=None,
            expiry_date=None,
            pdf_missing=True,
        )
        after = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            pdf_attachment_id=blob_id,
            pdf_missing=False,
            status="ok",
            certificate_number="COC-2026-001",
            issuing_authority="Nippon Kaiji Kyokai",
            place_of_issue="Tokyo",
            issue_date="2026-06-01",
            expiry_date="2031-06-01",
            version=2,
        )
        repository.get_item.return_value = item
        repository.update_item.return_value = (item, after)
        save_uploaded_cert_pdf.return_value = {
            "relative_path": "certs/vessels/vessel-1/tracked/item-1/coc.pdf",
            "absolute_path": "C:/tmp/coc.pdf",
            "sha256": "c" * 64,
            "size": 29,
            "filename": "coc.pdf",
        }
        pdf_repository.create_blob_for_tracked_item.return_value = pdf_blob_row(
            blob_id=blob_id,
            tracked_item_id=row_id,
            content_sha256="c" * 64,
            content_size_bytes=29,
            filename="coc.pdf",
        )
        ocr_payload = {
            "schema_version": "certs-ocr-v1",
            "engine": "static-test",
            "context": "office",
            "status": "processed",
            "unprocessable": False,
            "fields": {
                "certificate_number": {"value": "COC-2026-001", "confidence": 0.91, "mode": "auto_accept"},
                "issuing_authority": {"value": "Nippon Kaiji Kyokai", "confidence": 0.94, "mode": "auto_accept"},
                "place_of_issue": {"value": "Tokyo", "confidence": 0.89, "mode": "auto_accept"},
                "issue_date": {"value": "01-Jun-2026", "confidence": 0.92, "mode": "auto_accept"},
                "expiry_date": {"value": "01 Jun 2031", "confidence": 0.93, "mode": "auto_accept"},
                "imo_number": {"value": "9876543", "confidence": 0.92, "mode": "auto_accept"},
            },
        }
        process_cert_pdf.return_value = ocr_payload
        pdf_repository.update_ocr_result.return_value = pdf_blob_row(
            blob_id=blob_id,
            tracked_item_id=row_id,
            ocr_payload_json='{"status":"processed"}',
            ocr_confidence_per_field='{"certificate_number":0.91}',
            ocr_processed_at="2026-06-26T10:00:00Z",
            ocr_engine_version="static-test",
        )
        upload = SimpleUploadedFile("coc.pdf", b"%PDF-1.4 cert body", content_type="application/pdf")
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/upload-pdf/",
            {"file": upload, "reason": "Uploading certificate PDF."},
            format="multipart",
        )
        force_authenticate(request, user=self.dpa_writer)

        response = TrackedItemUploadPdfView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        repository.update_item.assert_called_once_with(
            str(row_id),
            {
                "pdfAttachmentId": str(blob_id),
                "pdfMissing": False,
                "certificateNumber": "COC-2026-001",
                "issuingAuthority": "Nippon Kaiji Kyokai",
                "placeOfIssue": "Tokyo",
                "issueDate": "2026-06-01",
                "expiryDate": "2031-06-01",
                "approvalState": "approved",
                "submittedBy": "dpa-1",
                "submittedAt": ANY,
                "approvedBy": "dpa-1",
                "approvedAt": ANY,
                "rejectionReason": None,
                "draftExpiresAt": None,
                "status": "ok",
            },
            actor_id="dpa-1",
        )
        self.assertEqual(response.data["trackedItem"]["certificateNumber"], "COC-2026-001")
        self.assertEqual(response.data["trackedItem"]["issuingAuthority"], "Nippon Kaiji Kyokai")
        self.assertEqual(response.data["trackedItem"]["issueDate"], "2026-06-01")
        self.assertEqual(response.data["trackedItem"]["expiryDate"], "2031-06-01")
        record_cert_change_log.assert_called_once()

    @patch("apps.certs.views.tracked_item_views.record_approval_event")
    @patch("apps.certs.views.tracked_item_views.record_cert_change_log")
    @patch("apps.certs.views.tracked_item_views.record_audit_event")
    @patch("apps.certs.views.tracked_item_views.process_cert_pdf")
    @patch("apps.certs.views.tracked_item_views.save_uploaded_cert_pdf")
    @patch("apps.certs.views.tracked_item_views.pdf_repository")
    @patch("apps.certs.views.tracked_item_views.repository")
    def test_sub_officer_upload_pdf_requires_master_approval(
        self,
        repository,
        pdf_repository,
        save_uploaded_cert_pdf,
        process_cert_pdf,
        record_audit_event,
        record_cert_change_log,
        record_approval_event,
    ) -> None:
        row_id = uuid.uuid4()
        vessel_id = uuid.uuid4()
        blob_id = uuid.uuid4()
        item = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="approved",
            catalog_submission_scope="all_ranks_with_approval",
        )
        after = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            pdf_attachment_id=blob_id,
            pdf_missing=False,
            approval_state="pending_master_approval",
            submitted_by="chief-officer-1",
            approved_by=None,
            approved_at=None,
            version=2,
        )
        repository.get_item.return_value = item
        repository.update_item.return_value = (item, after)
        save_uploaded_cert_pdf.return_value = {
            "relative_path": "certs/vessels/vessel-1/tracked/item-1/iopp.pdf",
            "absolute_path": "C:/tmp/iopp.pdf",
            "sha256": "d" * 64,
            "size": 29,
            "filename": "iopp.pdf",
        }
        pdf_repository.create_blob_for_tracked_item.return_value = pdf_blob_row(
            blob_id=blob_id,
            tracked_item_id=row_id,
            content_sha256="d" * 64,
            content_size_bytes=29,
            filename="iopp.pdf",
        )
        ocr_payload = {
            "schema_version": "certs-ocr-v1",
            "engine": "static-test",
            "context": "vessel",
            "status": "processed",
            "unprocessable": False,
            "fields": {
                "certificate_number": {"value": "IOPP-CO-001", "confidence": 0.88, "mode": "auto_accept"},
            },
        }
        process_cert_pdf.return_value = ocr_payload
        pdf_repository.update_ocr_result.return_value = pdf_blob_row(
            blob_id=blob_id,
            tracked_item_id=row_id,
            ocr_payload_json='{"status":"processed"}',
            ocr_confidence_per_field='{"certificate_number":0.88}',
            ocr_processed_at="2026-06-26T10:00:00Z",
            ocr_engine_version="static-test",
        )
        upload = SimpleUploadedFile("iopp.pdf", b"%PDF-1.4 cert body", content_type="application/pdf")
        user = make_user(
            role="Chief Officer",
            user_type="VESSEL",
            vessel_id=str(vessel_id),
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_001"],
        )
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/upload-pdf/",
            {"file": upload, "reason": "Chief Officer uploaded renewal certificate PDF."},
            format="multipart",
        )
        force_authenticate(request, user=user)

        response = TrackedItemUploadPdfView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["trackedItem"]["approvalState"], "pending_master_approval")
        repository.update_item.assert_called_once_with(
            str(row_id),
            {
                "pdfAttachmentId": str(blob_id),
                "pdfMissing": False,
                "certificateNumber": "IOPP-CO-001",
                "approvalState": "pending_master_approval",
                "submittedBy": "chief-officer-1",
                "submittedAt": ANY,
                "approvedBy": None,
                "approvedAt": None,
                "rejectionReason": None,
                "draftExpiresAt": None,
            },
            actor_id="chief-officer-1",
        )
        record_approval_event.assert_called_once()
        self.assertEqual(record_approval_event.call_args.kwargs["to_state"], "pending_master_approval")
        record_cert_change_log.assert_called_once()

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_upload_pdf_rejects_non_pdf_files(self, repository) -> None:
        row_id = uuid.uuid4()
        upload = SimpleUploadedFile("cert.png", b"not a pdf", content_type="image/png")
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/upload-pdf/",
            {"file": upload, "reason": "Trying an unsupported upload."},
            format="multipart",
        )
        force_authenticate(request, user=self.dpa_writer)

        response = TrackedItemUploadPdfView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)
        repository.get_item.assert_not_called()

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_detail_denies_out_of_scope_vessel(self, repository) -> None:
        row_id = uuid.uuid4()
        row = tracked_item_row(tracked_item_id=row_id, vessel_id=uuid.uuid4())
        repository.get_item.return_value = row
        scoped_reader = make_user(
            role="Marine Superintendent",
            form_ids=["CERT_F_002"],
            process_ids=[],
            vessel_ids=[str(uuid.uuid4())],
            has_global_vessel_access=False,
        )
        request = self.factory.get(f"/api/certs/tracked-items/{row_id}/")
        force_authenticate(request, user=scoped_reader)

        response = TrackedItemDetailView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.list_pdf_versions.assert_not_called()

    @patch("apps.certs.services.tracked_item_repository.connection")
    def test_repository_detail_panel_reads_scope_to_tracked_item(self, connection) -> None:
        row_id = str(uuid.uuid4())
        cursor = MagicMock()
        cursor.description = [("blob_id",), ("tracked_item_id",), ("filename",), ("is_active",)]
        cursor.fetchall.return_value = [(uuid.uuid4(), row_id, "IOPP.pdf", True)]
        connection.cursor.return_value.__enter__.return_value = cursor

        results = TrackedItemRepository().list_pdf_versions(row_id)

        self.assertEqual(results[0]["filename"], "IOPP.pdf")
        executed_sql = cursor.execute.call_args.args[0]
        self.assertIn("FROM dbo.vims_certs_pdf_blob", executed_sql)
        self.assertIn("WHERE tracked_item_id = %s", executed_sql)
        self.assertEqual(cursor.execute.call_args.args[1], [row_id])

    @patch("apps.certs.views.tracked_item_views.record_cert_change_log")
    @patch("apps.certs.views.tracked_item_views.record_audit_event")
    @patch("apps.certs.views.tracked_item_views.repository")
    def test_dpa_can_create_tracked_item_and_audit_event_is_recorded(
        self,
        repository,
        record_audit_event,
        record_cert_change_log,
    ) -> None:
        created = tracked_item_row()
        repository.create_item.return_value = created
        request = self.factory.post(
            "/api/certs/tracked-items/",
            {
                "vesselId": str(created["vessel_id"]),
                "catalogId": str(created["catalog_id"]),
                "type": "certificate",
                "validityType": "full",
                "issueDate": "2026-01-01",
                "expiryDate": "2031-01-01",
                "anniversaryDate": "2026-01-01",
                "certificateNumber": "IOPP-001",
                "issuingAuthority": "Flag",
                "placeOfIssue": "Bangkok",
                "reason": "Initial tracked item create.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa_writer)

        response = TrackedItemListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["certificateNumber"], "IOPP-001")
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "create_tracked_item")
        self.assertEqual(record_audit_event.call_args.kwargs["vessel_id"], str(created["vessel_id"]))
        record_cert_change_log.assert_called_once()
        self.assertEqual(record_cert_change_log.call_args.kwargs["tracked_item_id"], str(created["tracked_item_id"]))

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_create_rejects_client_supplied_approval_workflow_fields(self, repository) -> None:
        row = tracked_item_row()
        request = self.factory.post(
            "/api/certs/tracked-items/",
            {
                "vesselId": str(row["vessel_id"]),
                "catalogId": str(row["catalog_id"]),
                "type": "certificate",
                "validityType": "full",
                "issueDate": "2026-01-01",
                "expiryDate": "2031-01-01",
                "issuingAuthority": "Flag",
                "approvalState": "approved",
                "submittedBy": "not-the-client",
                "reason": "Trying to bypass the workflow guard.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa_writer)

        response = TrackedItemListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("approvalState", response.data)
        self.assertIn("submittedBy", response.data)
        repository.create_item.assert_not_called()

    @patch("apps.certs.views.tracked_item_views.record_cert_change_log")
    @patch("apps.certs.views.tracked_item_views.record_audit_event")
    @patch("apps.certs.views.tracked_item_views.repository")
    def test_patch_tracked_item_records_update_audit_and_change_log(
        self,
        repository,
        record_audit_event,
        record_cert_change_log,
    ) -> None:
        row_id = uuid.uuid4()
        before = tracked_item_row(tracked_item_id=row_id, certificate_number="OLD", version=1)
        after = tracked_item_row(tracked_item_id=row_id, certificate_number="NEW", version=2)
        repository.update_item.return_value = (before, after)
        request = self.factory.patch(
            f"/api/certs/tracked-items/{row_id}/",
            {"certificateNumber": "NEW", "reason": "Correct cert number."},
            format="json",
        )
        force_authenticate(request, user=self.dpa_writer)

        response = TrackedItemDetailView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["certificateNumber"], "NEW")
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "update_tracked_item")
        record_cert_change_log.assert_called_once()
        self.assertEqual(record_cert_change_log.call_args.kwargs["version_after"], 2)

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_patch_rejects_client_supplied_approval_workflow_fields(self, repository) -> None:
        row_id = uuid.uuid4()
        request = self.factory.patch(
            f"/api/certs/tracked-items/{row_id}/",
            {
                "approvalState": "approved",
                "approvedBy": "not-the-client",
                "reason": "Trying to bypass the workflow guard.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa_writer)

        response = TrackedItemDetailView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("approvalState", response.data)
        self.assertIn("approvedBy", response.data)
        repository.update_item.assert_not_called()

    @patch("apps.certs.views.tracked_item_views.record_cert_change_log")
    @patch("apps.certs.views.tracked_item_views.record_audit_event")
    @patch("apps.certs.views.tracked_item_views.repository")
    def test_quarantine_resolve_requires_valid_resolution(
        self,
        repository,
        record_audit_event,
        record_cert_change_log,
    ) -> None:
        row_id = uuid.uuid4()
        before = tracked_item_row(tracked_item_id=row_id, status="expired_at_onboarding", lifecycle_status="onboarding_quarantine")
        after = tracked_item_row(tracked_item_id=row_id, status="expired", lifecycle_status="active", version=2)
        repository.get_item.return_value = before
        repository.update_item.return_value = (before, after)
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/quarantine-resolve/",
            {"resolution": "expired", "reason": "DPA acknowledged expired legacy certificate."},
            format="json",
        )
        force_authenticate(request, user=self.dpa_writer)

        response = TrackedItemQuarantineResolveView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "expired")
        repository.update_item.assert_called_once()
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["metadata"]["source"], "api.certs.tracked_items.quarantine_resolve")
        record_cert_change_log.assert_called_once()

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_sub_officer_cannot_submit_master_only_row(self, repository) -> None:
        vessel_id = str(uuid.uuid4())
        row_id = uuid.uuid4()
        before = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="draft",
            catalog_submission_scope="master_only",
            submitted_by="chief-officer-1",
            approved_by=None,
            approved_at=None,
        )
        repository.get_item.return_value = before
        user = make_user(
            role="Chief Officer",
            user_type="VESSEL",
            vessel_id=vessel_id,
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_002"],
        )
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/submit/",
            {"version": 1, "reason": "Submitting certificate update for Master review."},
            format="json",
        )
        force_authenticate(request, user=user)

        response = TrackedItemSubmitView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "Only Master or office users may submit master_only rows.")
        repository.transition_item.assert_not_called()

    @patch("apps.certs.views.tracked_item_views.record_cert_change_log")
    @patch("apps.certs.views.tracked_item_views.record_approval_event")
    @patch("apps.certs.views.tracked_item_views.record_audit_event")
    @patch("apps.certs.views.tracked_item_views.repository")
    def test_original_submitter_can_resubmit_rejected_row_to_draft(
        self,
        repository,
        record_audit_event,
        record_approval_event,
        record_cert_change_log,
    ) -> None:
        vessel_id = str(uuid.uuid4())
        row_id = uuid.uuid4()
        before = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="rejected",
            submitted_by="chief-officer-1",
            rejection_reason="Wrong expiry date in uploaded certificate.",
            version=3,
        )
        after = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="draft",
            submitted_by="chief-officer-1",
            rejection_reason=None,
            version=4,
        )
        repository.get_item.return_value = before
        repository.transition_item.return_value = (before, after, True)
        user = make_user(
            role="Chief Officer",
            user_type="VESSEL",
            vessel_id=vessel_id,
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_002"],
        )
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/submit/",
            {"version": 3, "reason": "Correcting and resubmitting rejected certificate draft."},
            format="json",
        )
        force_authenticate(request, user=user)

        response = TrackedItemSubmitView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["approvalState"], "draft")
        self.assertEqual(repository.transition_item.call_args.kwargs["transition"], "resubmit_to_draft")
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "submit_tracked_item")
        self.assertEqual(record_approval_event.call_args.kwargs["from_state"], "rejected")
        self.assertEqual(record_approval_event.call_args.kwargs["to_state"], "draft")
        record_cert_change_log.assert_called_once()

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_non_original_submitter_cannot_resubmit_rejected_row(self, repository) -> None:
        vessel_id = str(uuid.uuid4())
        row_id = uuid.uuid4()
        before = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="rejected",
            submitted_by="chief-officer-1",
            rejection_reason="Wrong expiry date in uploaded certificate.",
            version=3,
        )
        repository.get_item.return_value = before
        user = make_user(
            role="Second Engineer",
            user_type="VESSEL",
            vessel_id=vessel_id,
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_002"],
        )
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/submit/",
            {"version": 3, "reason": "Trying to resubmit someone else's rejected draft."},
            format="json",
        )
        force_authenticate(request, user=user)

        response = TrackedItemSubmitView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["detail"], "Only the original submitter may resubmit a rejected tracked item.")
        repository.transition_item.assert_not_called()

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_quarantine_resolve_rejects_non_quarantine_row(self, repository) -> None:
        row_id = uuid.uuid4()
        repository.get_item.return_value = tracked_item_row(tracked_item_id=row_id, status="ok")
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/quarantine-resolve/",
            {"resolution": "active", "reason": "Renewal PDF uploaded."},
            format="json",
        )
        force_authenticate(request, user=self.dpa_writer)

        response = TrackedItemQuarantineResolveView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        repository.update_item.assert_not_called()

    @patch("apps.certs.services.tracked_item_repository.connection")
    def test_repository_update_increments_cas_version(self, connection) -> None:
        cursor = MagicMock()
        cursor.description = [("tracked_item_id",), ("version",)]
        cursor.fetchone.side_effect = [(uuid.uuid4(), 1), (uuid.uuid4(), 2)]
        connection.cursor.return_value.__enter__.return_value = cursor

        before, after = TrackedItemRepository().update_item(
            "11111111-1111-1111-1111-111111111111",
            {"certificateNumber": "NEW"},
            actor_id="dpa-1",
        )

        self.assertIsNotNone(before)
        self.assertIsNotNone(after)
        executed_sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
        self.assertIn("version = version + 1", executed_sql)
        self.assertIn("updated_at = SYSUTCDATETIME()", executed_sql)

    @patch("apps.certs.services.tracked_item_repository.connection")
    def test_repository_transition_enforces_expected_version_in_sql(self, connection) -> None:
        cursor = MagicMock()
        cursor.description = [("tracked_item_id",), ("version",), ("approval_state",)]
        row_id = uuid.uuid4()
        cursor.fetchone.side_effect = [
            (row_id, 2, "pending_master_approval"),
            (row_id, 3, "approved"),
        ]
        cursor.rowcount = 1
        connection.cursor.return_value.__enter__.return_value = cursor

        before, after, updated = TrackedItemRepository().transition_item(
            str(row_id),
            transition="approve",
            actor_id="master-1",
            reason="Certificate evidence reviewed and approved.",
            expected_version=2,
        )

        self.assertTrue(updated)
        self.assertIsNotNone(before)
        self.assertIsNotNone(after)
        executed_sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
        self.assertIn("version = version + 1", executed_sql)
        self.assertIn("WHERE tracked_item_id = %s AND version = %s", executed_sql)

    @patch("apps.certs.views.tracked_item_views.record_cert_change_log")
    @patch("apps.certs.views.tracked_item_views.record_approval_event")
    @patch("apps.certs.views.tracked_item_views.record_audit_event")
    @patch("apps.certs.views.tracked_item_views.repository")
    def test_sub_officer_can_submit_draft_for_master_approval(
        self,
        repository,
        record_audit_event,
        record_approval_event,
        record_cert_change_log,
    ) -> None:
        vessel_id = str(uuid.uuid4())
        row_id = uuid.uuid4()
        before = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="draft",
            submitted_by="chief-officer-1",
            approved_by=None,
            approved_at=None,
        )
        after = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="pending_master_approval",
            submitted_by="chief-officer-1",
            submitted_at="2026-06-25T01:00:00Z",
            approved_by=None,
            approved_at=None,
            version=2,
        )
        repository.get_item.return_value = before
        repository.transition_item.return_value = (before, after, True)
        user = make_user(
            role="Chief Officer",
            user_type="VESSEL",
            vessel_id=vessel_id,
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_002"],
        )
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/submit/",
            {"version": 1, "reason": "Submitting certificate update for Master review."},
            format="json",
        )
        force_authenticate(request, user=user)

        response = TrackedItemSubmitView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["approvalState"], "pending_master_approval")
        repository.transition_item.assert_called_once()
        self.assertEqual(repository.transition_item.call_args.kwargs["transition"], "submit_for_master")
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "submit_tracked_item")
        record_approval_event.assert_called_once()
        self.assertEqual(record_approval_event.call_args.kwargs["from_state"], "draft")
        self.assertEqual(record_approval_event.call_args.kwargs["to_state"], "pending_master_approval")
        record_cert_change_log.assert_called_once()

    @patch("apps.certs.views.tracked_item_views.record_cert_change_log")
    @patch("apps.certs.views.tracked_item_views.record_approval_event")
    @patch("apps.certs.views.tracked_item_views.record_audit_event")
    @patch("apps.certs.views.tracked_item_views.repository")
    def test_master_can_approve_pending_own_vessel_submission(
        self,
        repository,
        record_audit_event,
        record_approval_event,
        record_cert_change_log,
    ) -> None:
        vessel_id = str(uuid.uuid4())
        row_id = uuid.uuid4()
        before = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="pending_master_approval",
            submitted_by="chief-officer-1",
            approved_by=None,
            approved_at=None,
            version=2,
        )
        after = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="approved",
            submitted_by="chief-officer-1",
            approved_by="master-1",
            approved_at="2026-06-25T01:10:00Z",
            version=3,
        )
        repository.get_item.return_value = before
        repository.transition_item.return_value = (before, after, True)
        user = make_user(
            role="VESSEL_MASTER",
            user_type="VESSEL",
            vessel_id=vessel_id,
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_003"],
        )
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/approve/",
            {"version": 2, "reason": "Certificate evidence reviewed and approved."},
            format="json",
        )
        force_authenticate(request, user=user)

        response = TrackedItemApproveView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["approvalState"], "approved")
        self.assertEqual(repository.transition_item.call_args.kwargs["transition"], "approve")
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "approve_tracked_item")
        self.assertEqual(record_approval_event.call_args.kwargs["to_state"], "approved")
        record_cert_change_log.assert_called_once()

    @patch("apps.certs.views.tracked_item_views.record_cert_change_log")
    @patch("apps.certs.views.tracked_item_views.record_approval_event")
    @patch("apps.certs.views.tracked_item_views.record_audit_event")
    @patch("apps.certs.views.tracked_item_views.repository")
    def test_master_reject_requires_reason_and_increments_rejection_count(
        self,
        repository,
        record_audit_event,
        record_approval_event,
        record_cert_change_log,
    ) -> None:
        vessel_id = str(uuid.uuid4())
        row_id = uuid.uuid4()
        before = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="pending_master_approval",
            rejection_count=1,
            version=2,
        )
        after = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="rejected",
            rejection_reason="Wrong expiry date in uploaded certificate.",
            rejection_count=2,
            version=3,
        )
        repository.get_item.return_value = before
        repository.transition_item.return_value = (before, after, True)
        user = make_user(
            role="VESSEL_MASTER",
            user_type="VESSEL",
            vessel_id=vessel_id,
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_004"],
        )
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/reject/",
            {"version": 2, "reason": "Wrong expiry date in uploaded certificate."},
            format="json",
        )
        force_authenticate(request, user=user)

        response = TrackedItemRejectView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["approvalState"], "rejected")
        self.assertEqual(response.data["rejectionCount"], 2)
        self.assertEqual(repository.transition_item.call_args.kwargs["transition"], "reject")
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "reject_tracked_item")
        self.assertEqual(record_approval_event.call_args.kwargs["to_state"], "rejected")
        record_cert_change_log.assert_called_once()

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_reject_requires_minimum_reason(self, repository) -> None:
        vessel_id = str(uuid.uuid4())
        row_id = uuid.uuid4()
        repository.get_item.return_value = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="pending_master_approval",
        )
        user = make_user(
            role="VESSEL_MASTER",
            user_type="VESSEL",
            vessel_id=vessel_id,
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_004"],
        )
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/reject/",
            {"version": 1, "reason": "Too short"},
            format="json",
        )
        force_authenticate(request, user=user)

        response = TrackedItemRejectView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        repository.transition_item.assert_not_called()

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_second_master_approval_gets_row_version_conflict(self, repository) -> None:
        vessel_id = str(uuid.uuid4())
        row_id = uuid.uuid4()
        before = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="pending_master_approval",
            version=3,
        )
        repository.get_item.return_value = before
        repository.transition_item.return_value = (before, before, False)
        user = make_user(
            role="VESSEL_MASTER",
            user_type="VESSEL",
            vessel_id=vessel_id,
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_003"],
        )
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/approve/",
            {"version": 2, "reason": "Certificate evidence reviewed and approved."},
            format="json",
        )
        force_authenticate(request, user=user)

        response = TrackedItemApproveView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["detail"], "Tracked item was updated by another user. Refresh and retry.")

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_non_master_cannot_approve_pending_submission(self, repository) -> None:
        vessel_id = str(uuid.uuid4())
        row_id = uuid.uuid4()
        repository.get_item.return_value = tracked_item_row(
            tracked_item_id=row_id,
            vessel_id=vessel_id,
            approval_state="pending_master_approval",
        )
        user = make_user(
            role="Chief Officer",
            user_type="VESSEL",
            vessel_id=vessel_id,
            form_ids=["CERT_F_002"],
            process_ids=["CERT_P_003"],
        )
        request = self.factory.post(
            f"/api/certs/tracked-items/{row_id}/approve/",
            {"version": 1, "reason": "Trying to approve."},
            format="json",
        )
        force_authenticate(request, user=user)

        response = TrackedItemApproveView.as_view()(request, tracked_item_id=row_id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.transition_item.assert_not_called()

    @patch("apps.certs.views.tracked_item_views.repository")
    def test_create_rejects_client_supplied_computed_window_fields(self, repository) -> None:
        row = tracked_item_row()
        request = self.factory.post(
            "/api/certs/tracked-items/",
            {
                "vesselId": str(row["vessel_id"]),
                "catalogId": str(row["catalog_id"]),
                "type": "certificate",
                "validityType": "full",
                "expiryDate": "2031-01-01",
                "windowOpen": "2029-01-01",
                "reason": "Trying to write a computed field.",
                "issuingAuthority": "Flag",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa_writer)

        response = TrackedItemListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("windowOpen", response.data)
        repository.create_item.assert_not_called()

    @patch("apps.certs.services.tracked_item_repository.connection")
    @patch.object(TrackedItemRepository, "get_item")
    def test_repository_create_computes_survey_window_and_ignores_client_values(self, get_item, connection) -> None:
        row_id = uuid.uuid4()
        get_item.return_value = tracked_item_row(
            tracked_item_id=row_id,
            anniversary_date="2026-01-01",
            window_open="2030-10-01",
            window_close="2031-01-01",
            next_due_date="2031-01-01",
        )
        cursor = MagicMock()
        cursor.fetchone.return_value = (row_id,)
        connection.cursor.return_value.__enter__.return_value = cursor

        TrackedItemRepository().create_item(
            {
                "vesselId": str(uuid.uuid4()),
                "catalogId": str(uuid.uuid4()),
                "type": "certificate",
                "validityType": "full",
                "cadenceMonths": 60,
                "anniversaryDate": "2026-01-01",
                "expiryDate": "2031-01-01",
                "issuingAuthority": "Flag",
                "windowOpen": "2029-01-01",
            },
            actor_id="dpa-1",
        )

        insert_sql = cursor.execute.call_args.args[0]
        insert_params = cursor.execute.call_args.args[1]
        self.assertIn("window_open", insert_sql)
        self.assertIn("window_close", insert_sql)
        self.assertIn("next_due_date", insert_sql)
        self.assertIn("2030-10-01", [str(value) for value in insert_params])
        self.assertNotIn("2029-01-01", [str(value) for value in insert_params])

    @patch("apps.certs.services.tracked_item_repository.connection")
    def test_repository_update_recomputes_survey_window_when_cadence_changes(self, connection) -> None:
        cursor = MagicMock()
        cursor.description = [("tracked_item_id",), ("anniversary_date",), ("cadence_months",), ("version",)]
        row_id = uuid.uuid4()
        cursor.fetchone.side_effect = [
            (row_id, "2026-01-01", 12, 1),
            (row_id, "2026-01-01", 60, 2),
        ]
        connection.cursor.return_value.__enter__.return_value = cursor

        before, after = TrackedItemRepository().update_item(
            str(row_id),
            {"cadenceMonths": 60},
            actor_id="dpa-1",
        )

        self.assertIsNotNone(before)
        self.assertIsNotNone(after)
        update_sql = cursor.execute.call_args_list[1].args[0]
        self.assertIn("window_open = %s", update_sql)
        self.assertIn("window_close = %s", update_sql)
        self.assertIn("next_due_date = %s", update_sql)
