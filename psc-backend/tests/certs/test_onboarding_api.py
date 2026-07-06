from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch
import uuid

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.certs.views.onboarding_views import (
    OnboardingBatchCommitView,
    OnboardingBatchDetailView,
    OnboardingBatchPreviewView,
    OnboardingCoverageOverrideView,
    OnboardingProfileView,
    OnboardingRollbackView,
    OnboardingSessionDetailView,
    OnboardingSessionListCreateView,
)
from apps.certs.services.onboarding_repository import OnboardingRepository
from tests.certs.test_tracked_item_api import make_user, pdf_blob_row, tracked_item_row


def vessel_row(**overrides):
    row = {
        "vessel_id": str(uuid.uuid4()),
        "vessel_code": "KSMF",
        "vessel_name": "KSM Fortitude",
        "imo_number": "9876543",
        "flag": "Panama",
        "class_society": "NK",
    }
    row.update(overrides)
    return row


def config_row(**overrides):
    row = {
        "vessel_id": str(uuid.uuid4()),
        "anniversary_date": "2026-01-15",
        "ship_type": "bulk_carrier",
        "marine_supt_user_id": "marine-1",
        "technical_manager_user_id": "tech-1",
        "lifecycle_status": "onboarding_in_progress",
        "mandatory_coverage_override_reason": None,
        "mandatory_coverage_override_at": None,
        "mandatory_coverage_override_by": None,
        "updated_at": "2026-06-26T09:00:00Z",
        "updated_by": "dpa-1",
    }
    row.update(overrides)
    return row


def batch_row(**overrides):
    row = {
        "batch_id": str(uuid.uuid4()),
        "vessel_id": str(uuid.uuid4()),
        "onboarding_session_id": str(uuid.uuid4()),
        "pdf_blob_ids_json": "[]",
        "pdf_count": 1,
        "status": "ready_for_review",
        "created_at": "2026-06-26T09:00:00Z",
        "created_by": "dpa-1",
        "ocr_completed_at": "2026-06-26T09:05:00Z",
        "review_started_at": None,
        "committed_at": None,
        "committed_by": None,
        "cancelled_at": None,
        "cancelled_by": None,
        "validation_blocks_json": None,
        "validation_warns_json": None,
        "report_csv_blob_id": None,
    }
    row.update(overrides)
    return row


class CertOnboardingApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.dpa = make_user(
            role="DPA",
            form_ids=["CERT_F_005"],
            process_ids=["CERT_P_001", "CERT_P_002", "CERT_P_010"],
        )
        self.fm = make_user(role="Fleet Manager", form_ids=["CERT_F_005"], process_ids=["CERT_P_002"])
        self.no_access = make_user(role="DPA", form_ids=["CERT_F_002"], process_ids=["CERT_P_001"])

    @patch("apps.certs.views.onboarding_views.repository")
    def test_wizard_state_requires_onboarding_form_permission(self, repository) -> None:
        request = self.factory.get("/api/certs/onboarding/9876543/")
        force_authenticate(request, user=self.no_access)

        response = OnboardingSessionDetailView.as_view()(request, vessel_id="9876543")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.get_wizard_state.assert_not_called()

    @patch("apps.certs.views.onboarding_views.repository")
    def test_wizard_state_serializes_seven_steps_batches_and_gap_fill_counts(self, repository) -> None:
        vessel = vessel_row()
        config = config_row(vessel_id=vessel["vessel_id"])
        tracked_item = tracked_item_row(vessel_id=vessel["vessel_id"], pdf_missing=True)
        batch = batch_row(vessel_id=vessel["vessel_id"], pdf_count=2)
        repository.get_wizard_state.return_value = {
            "vessel": vessel,
            "config": config,
            "batches": [batch],
            "items": [tracked_item],
            "coverage": {
                "percent": 0,
                "mandatoryCount": 1,
                "coveredCount": 0,
                "missing": [tracked_item],
                "overrideActive": False,
                "overrideReason": None,
                "overrideAt": None,
                "overrideBy": None,
            },
        }
        request = self.factory.get("/api/certs/onboarding/9876543/")
        force_authenticate(request, user=self.dpa)

        response = OnboardingSessionDetailView.as_view()(request, vessel_id="9876543")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["vessel"]["imo"], "9876543")
        self.assertEqual(len(response.data["steps"]), 7)
        self.assertEqual(response.data["currentStep"], 3)
        self.assertEqual(response.data["batches"][0]["status"], "ready_for_review")
        self.assertEqual(response.data["mandatoryCoverage"]["missing"][0]["trackedItemId"], str(tracked_item["tracked_item_id"]))
        repository.get_wizard_state.assert_called_once_with("9876543")

    @patch("apps.certs.views.onboarding_views.repository")
    def test_wizard_state_returns_to_step_one_after_onboarding_rollback(self, repository) -> None:
        vessel = vessel_row()
        repository.get_wizard_state.return_value = {
            "vessel": vessel,
            "config": config_row(
                vessel_id=vessel["vessel_id"],
                anniversary_date=None,
                ship_type="all",
                marine_supt_user_id=None,
                technical_manager_user_id=None,
                lifecycle_status="onboarding_in_progress",
            ),
            "batches": [],
            "items": [],
            "coverage": {
                "percent": 0,
                "mandatoryCount": 0,
                "coveredCount": 0,
                "missing": [],
                "overrideActive": False,
                "overrideReason": None,
                "overrideAt": None,
                "overrideBy": None,
            },
        }
        request = self.factory.get(f"/api/certs/onboarding/{vessel['vessel_id']}/")
        force_authenticate(request, user=self.dpa)

        response = OnboardingSessionDetailView.as_view()(request, vessel_id=vessel["vessel_id"])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["currentStep"], 1)
        self.assertEqual(response.data["steps"][0]["status"], "current")

    @patch("apps.certs.views.onboarding_views.record_audit_event")
    @patch("apps.certs.views.onboarding_views.repository")
    def test_profile_save_updates_existing_vessel_config_fields_and_audits(self, repository, record_audit_event) -> None:
        vessel = vessel_row()
        before = config_row(vessel_id=vessel["vessel_id"], anniversary_date=None)
        after = config_row(vessel_id=vessel["vessel_id"], anniversary_date="2026-02-01")
        repository.resolve_vessel.return_value = vessel
        repository.save_profile.return_value = (before, after)
        request = self.factory.post(
            f"/api/certs/onboarding/{vessel['vessel_id']}/profile/",
            {
                "anniversaryDate": "2026-02-01",
                "shipType": "bulk_carrier",
                "marineSuptUserId": "marine-2",
                "technicalManagerUserId": "tech-2",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = OnboardingProfileView.as_view()(request, vessel_id=vessel["vessel_id"])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["config"]["anniversaryDate"], "2026-02-01")
        repository.save_profile.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "onboarding_step_complete")
        self.assertEqual(record_audit_event.call_args.kwargs["vessel_id"], vessel["vessel_id"])

    @patch("apps.certs.views.onboarding_views.repository")
    def test_gap_fill_state_serializes_pdf_ocr_modes(self, repository) -> None:
        vessel_id = str(uuid.uuid4())
        batch_id = str(uuid.uuid4())
        tracked_id = str(uuid.uuid4())
        blob = pdf_blob_row(
            blob_id=uuid.uuid4(),
            tracked_item_id=tracked_id,
            ocr_payload_json=(
                '{"status":"processed","unprocessable":false,'
                '"fields":{"certificate_number":{"value":null,"raw_value":"IOPP-001",'
                '"confidence":0.58,"mode":"manual_entry","threshold":0.8,"manual_floor":0.6,"required":true}}}'
            ),
            ocr_confidence_per_field='{"certificate_number":0.58}',
        )
        repository.get_batch_gap_fill.return_value = {
            "batch": batch_row(batch_id=batch_id, vessel_id=vessel_id),
            "vessel": vessel_row(vessel_id=vessel_id),
            "pdfs": [blob],
            "itemsByBlobId": {str(blob["blob_id"]): tracked_item_row(tracked_item_id=tracked_id, vessel_id=vessel_id)},
        }
        request = self.factory.get(f"/api/certs/onboarding/batch/{batch_id}/")
        force_authenticate(request, user=self.dpa)

        response = OnboardingBatchDetailView.as_view()(request, batch_id=batch_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        pdf = response.data["pdfs"][0]
        self.assertEqual(pdf["ocrPayload"]["fields"]["certificate_number"]["mode"], "manual_entry")
        self.assertEqual(pdf["ocrConfidencePerField"]["certificate_number"], 0.58)
        self.assertEqual(pdf["trackedItem"]["id"], str(tracked_id))

    @patch("apps.certs.views.onboarding_views.record_audit_event")
    @patch("apps.certs.views.onboarding_views.repository")
    def test_batch_preview_persists_validation_blocks_and_audits(self, repository, record_audit_event) -> None:
        vessel_id = str(uuid.uuid4())
        batch_id = str(uuid.uuid4())
        batch = batch_row(batch_id=batch_id, vessel_id=vessel_id)
        repository.get_batch_gap_fill.return_value = {
            "batch": batch,
            "vessel": vessel_row(vessel_id=vessel_id),
            "pdfs": [],
            "itemsByBlobId": {},
        }
        repository.evaluate_batch_validation.return_value = {
            "batch": batch_row(
                batch_id=batch_id,
                vessel_id=vessel_id,
                status="commit_pending",
                validation_blocks_json='[{"code":"required_field_missing"}]',
                validation_warns_json="[]",
            ),
            "blocks": [{"code": "required_field_missing", "severity": "block", "message": "Certificate type is required."}],
            "warns": [],
            "canCommit": False,
            "requiresWarningAck": False,
            "preview": {"pdfCount": 1, "commitCount": 0},
        }
        request = self.factory.post(f"/api/certs/onboarding/batch/{batch_id}/preview/", {}, format="json")
        force_authenticate(request, user=self.dpa)

        response = OnboardingBatchPreviewView.as_view()(request, batch_id=batch_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["canCommit"])
        self.assertEqual(response.data["validationBlocks"][0]["code"], "required_field_missing")
        repository.evaluate_batch_validation.assert_called_once_with(str(batch_id))
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "validation_block")
        self.assertEqual(record_audit_event.call_args.kwargs["vessel_id"], vessel_id)

    @patch("apps.certs.views.onboarding_views.record_audit_event")
    @patch("apps.certs.views.onboarding_views.repository")
    def test_batch_commit_requires_warning_ack_then_commits(self, repository, record_audit_event) -> None:
        vessel_id = str(uuid.uuid4())
        batch_id = str(uuid.uuid4())
        batch = batch_row(batch_id=batch_id, vessel_id=vessel_id)
        repository.get_batch_gap_fill.return_value = {
            "batch": batch,
            "vessel": vessel_row(vessel_id=vessel_id),
            "pdfs": [],
            "itemsByBlobId": {},
        }
        repository.evaluate_batch_validation.return_value = {
            "batch": batch_row(
                batch_id=batch_id,
                vessel_id=vessel_id,
                status="commit_pending",
                validation_blocks_json="[]",
                validation_warns_json='[{"code":"expiry_date_in_past"}]',
            ),
            "blocks": [],
            "warns": [{"code": "expiry_date_in_past", "severity": "warn", "message": "Expiry date is in the past."}],
            "canCommit": True,
            "requiresWarningAck": True,
            "preview": {"pdfCount": 1, "commitCount": 1},
        }
        repository.mark_batch_committed.return_value = batch_row(
            batch_id=batch_id,
            vessel_id=vessel_id,
            status="committed",
            validation_blocks_json="[]",
            validation_warns_json='[{"code":"expiry_date_in_past"}]',
            report_csv_blob_id="11111111-1111-1111-1111-111111111111",
        )
        repository.create_batch_report_csv.return_value = "11111111-1111-1111-1111-111111111111"
        repository.evaluate_batch_idempotency.return_value = {
            "blocks": [],
            "skippedDuplicates": [],
            "supersededPdfs": [],
        }
        repository.apply_batch_idempotency.return_value = {
            "blocks": [],
            "skippedDuplicates": [],
            "supersededPdfs": [],
        }

        request = self.factory.post(f"/api/certs/onboarding/batch/{batch_id}/commit/", {}, format="json")
        force_authenticate(request, user=self.dpa)
        response = OnboardingBatchCommitView.as_view()(request, batch_id=batch_id)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        repository.mark_batch_committed.assert_not_called()

        ack_request = self.factory.post(
            f"/api/certs/onboarding/batch/{batch_id}/commit/",
            {"acknowledgeWarnings": True},
            format="json",
        )
        force_authenticate(ack_request, user=self.dpa)
        ack_response = OnboardingBatchCommitView.as_view()(ack_request, batch_id=batch_id)

        self.assertEqual(ack_response.status_code, status.HTTP_200_OK)
        self.assertEqual(ack_response.data["batch"]["status"], "committed")
        self.assertEqual(ack_response.data["batch"]["reportCsvBlobId"], "11111111-1111-1111-1111-111111111111")
        repository.create_batch_report_csv.assert_called_once()
        repository.mark_batch_committed.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "onboarding_step_complete")

    @patch("apps.certs.views.onboarding_views.record_audit_event")
    @patch("apps.certs.views.onboarding_views.repository")
    def test_batch_commit_blocks_same_cert_number_until_supersede_confirmed(self, repository, record_audit_event) -> None:
        vessel_id = str(uuid.uuid4())
        batch_id = str(uuid.uuid4())
        batch = batch_row(batch_id=batch_id, vessel_id=vessel_id)
        repository.get_batch_gap_fill.return_value = {
            "batch": batch,
            "vessel": vessel_row(vessel_id=vessel_id),
            "pdfs": [],
            "itemsByBlobId": {},
        }
        repository.evaluate_batch_validation.return_value = {
            "batch": batch_row(
                batch_id=batch_id,
                vessel_id=vessel_id,
                status="commit_pending",
                validation_blocks_json="[]",
                validation_warns_json="[]",
            ),
            "blocks": [],
            "warns": [],
            "canCommit": True,
            "requiresWarningAck": False,
            "preview": {"pdfCount": 1, "commitCount": 1},
        }
        repository.evaluate_batch_idempotency.return_value = {
            "blocks": [
                {
                    "code": "supersede_confirmation_required",
                    "severity": "block",
                    "message": "A certificate with this number already exists.",
                    "blobId": "new-blob",
                    "filename": "iopp-renewal.pdf",
                    "field": "certificate_number",
                    "value": "existing-blob",
                    "certificateNumber": "IOPP-001",
                }
            ],
            "skippedDuplicates": [],
            "supersededPdfs": [],
        }

        request = self.factory.post(f"/api/certs/onboarding/batch/{batch_id}/commit/", {}, format="json")
        force_authenticate(request, user=self.dpa)
        response = OnboardingBatchCommitView.as_view()(request, batch_id=batch_id)

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["validationBlocks"][0]["code"], "supersede_confirmation_required")
        repository.mark_batch_committed.assert_not_called()
        repository.create_batch_report_csv.assert_not_called()
        repository.apply_batch_idempotency.assert_not_called()
        record_audit_event.assert_not_called()

    @patch("apps.certs.views.onboarding_views.record_audit_event")
    @patch("apps.certs.views.onboarding_views.repository")
    def test_batch_commit_applies_skip_and_supersede_audits(self, repository, record_audit_event) -> None:
        vessel_id = str(uuid.uuid4())
        batch_id = str(uuid.uuid4())
        batch = batch_row(batch_id=batch_id, vessel_id=vessel_id)
        repository.get_batch_gap_fill.return_value = {
            "batch": batch,
            "vessel": vessel_row(vessel_id=vessel_id),
            "pdfs": [],
            "itemsByBlobId": {},
        }
        repository.evaluate_batch_validation.return_value = {
            "batch": batch_row(
                batch_id=batch_id,
                vessel_id=vessel_id,
                status="commit_pending",
                validation_blocks_json="[]",
                validation_warns_json="[]",
            ),
            "blocks": [],
            "warns": [],
            "canCommit": True,
            "requiresWarningAck": False,
            "preview": {"pdfCount": 2, "commitCount": 2},
        }
        idempotency_result = {
            "blocks": [],
            "skippedDuplicates": [
                {
                    "blobId": "duplicate-blob",
                    "existingBlobId": "existing-blob",
                    "trackedItemId": "tracked-1",
                    "certificateNumber": "IOPP-001",
                    "sha256": "a" * 64,
                    "filename": "iopp-copy.pdf",
                }
            ],
            "supersededPdfs": [
                {
                    "blobId": "new-blob",
                    "existingBlobId": "old-blob",
                    "trackedItemId": "tracked-2",
                    "certificateNumber": "LOADLINE-001",
                    "oldSha256": "b" * 64,
                    "newSha256": "c" * 64,
                    "filename": "loadline-renewed.pdf",
                }
            ],
        }
        repository.evaluate_batch_idempotency.return_value = idempotency_result
        repository.apply_batch_idempotency.return_value = idempotency_result
        repository.mark_batch_committed.return_value = batch_row(
            batch_id=batch_id,
            vessel_id=vessel_id,
            status="committed",
            validation_blocks_json="[]",
            validation_warns_json="[]",
            report_csv_blob_id="11111111-1111-1111-1111-111111111111",
        )
        repository.create_batch_report_csv.return_value = "11111111-1111-1111-1111-111111111111"

        request = self.factory.post(
            f"/api/certs/onboarding/batch/{batch_id}/commit/",
            {
                "supersedeDecisions": [
                    {"blobId": "new-blob", "existingBlobId": "old-blob", "confirm": True}
                ]
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa)
        response = OnboardingBatchCommitView.as_view()(request, batch_id=batch_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repository.apply_batch_idempotency.assert_called_once_with(idempotency_result, actor=self.dpa)
        actions = [call.kwargs["action"] for call in record_audit_event.call_args_list]
        self.assertEqual(actions, ["upload_pdf", "supersede_pdf", "onboarding_step_complete"])
        self.assertEqual(record_audit_event.call_args_list[0].kwargs["metadata"]["skippedDuplicate"], True)
        self.assertEqual(record_audit_event.call_args_list[1].kwargs["metadata"]["existingBlobId"], "old-blob")

    @patch("apps.certs.views.onboarding_views.repository")
    def test_hub_lists_in_progress_onboardings_for_fm_read(self, repository) -> None:
        vessel = vessel_row()
        repository.list_onboarding_sessions.return_value = [
            {
                "vessel": vessel,
                "config": config_row(vessel_id=vessel["vessel_id"]),
                "batchCount": 2,
                "currentStep": 6,
                "mandatoryCoveragePercent": 75,
                "pendingFmSignoff": True,
                "lastActivity": "2026-06-26T09:00:00Z",
                "startedAt": "2026-06-25T09:00:00Z",
                "startedBy": "dpa-1",
            }
        ]
        request = self.factory.get("/api/certs/onboarding/")
        force_authenticate(request, user=self.fm)

        response = OnboardingSessionListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["currentStep"], 6)
        self.assertTrue(response.data["results"][0]["pendingFmSignoff"])

    @patch("apps.certs.views.onboarding_views.record_audit_event")
    @patch("apps.certs.views.onboarding_views.repository")
    def test_coverage_override_requires_vessel_scope_and_records_coverage_audit(self, repository, record_audit_event) -> None:
        vessel = vessel_row()
        before = config_row(vessel_id=vessel["vessel_id"], mandatory_coverage_override_reason=None)
        after = config_row(
            vessel_id=vessel["vessel_id"],
            mandatory_coverage_override_reason="Original statutory certificate being re-issued by flag state.",
            mandatory_coverage_override_by="dpa-1",
        )
        repository.resolve_vessel.return_value = vessel
        repository.update_coverage_override.return_value = (before, after)
        scoped_superintendent = make_user(
            role="Technical Superintendent",
            form_ids=["CERT_F_005"],
            process_ids=["CERT_P_001"],
            vessel_ids=[str(uuid.uuid4())],
        )
        request = self.factory.post(
            f"/api/certs/onboarding/{vessel['vessel_id']}/coverage-override/",
            {"reason": "Original statutory certificate being re-issued by flag state."},
            format="json",
        )
        force_authenticate(request, user=scoped_superintendent)

        denied = OnboardingCoverageOverrideView.as_view()(request, vessel_id=vessel["vessel_id"])

        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        repository.update_coverage_override.assert_not_called()

        allowed_request = self.factory.post(
            f"/api/certs/onboarding/{vessel['vessel_id']}/coverage-override/",
            {"reason": "Original statutory certificate being re-issued by flag state."},
            format="json",
        )
        force_authenticate(allowed_request, user=self.dpa)

        response = OnboardingCoverageOverrideView.as_view()(allowed_request, vessel_id=vessel["vessel_id"])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        repository.update_coverage_override.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "coverage_override")
        self.assertEqual(record_audit_event.call_args.kwargs["metadata"]["step"], 6)

    @patch("apps.certs.views.onboarding_views.record_audit_event")
    @patch("apps.certs.views.onboarding_views.repository")
    def test_rollback_requires_scope_pre_go_live_and_records_audit(self, repository, record_audit_event) -> None:
        vessel = vessel_row()
        before = config_row(
            vessel_id=vessel["vessel_id"],
            lifecycle_status="onboarding_in_progress",
            mandatory_coverage_override_reason="Temporary missing flag certificate.",
        )
        after = config_row(
            vessel_id=vessel["vessel_id"],
            anniversary_date=None,
            lifecycle_status="onboarding_in_progress",
            mandatory_coverage_override_reason=None,
        )
        summary = {
            "cancelledBatchCount": 2,
            "supersededPdfCount": 3,
            "supersededTrackedItemCount": 4,
            "resetToStep": 1,
        }
        repository.resolve_vessel.return_value = vessel
        repository.get_vessel_config.return_value = before
        repository.rollback_onboarding.return_value = (before, after, summary)
        scoped_superintendent = make_user(
            role="Technical Superintendent",
            form_ids=["CERT_F_005"],
            process_ids=["CERT_P_010"],
            vessel_ids=[str(uuid.uuid4())],
            has_global_vessel_access=False,
        )
        denied_request = self.factory.post(
            f"/api/certs/onboarding/{vessel['vessel_id']}/rollback/",
            {"reason": "Reset failed onboarding import for this vessel before go-live."},
            format="json",
        )
        force_authenticate(denied_request, user=scoped_superintendent)

        denied = OnboardingRollbackView.as_view()(denied_request, vessel_id=vessel["vessel_id"])

        self.assertEqual(denied.status_code, status.HTTP_403_FORBIDDEN)
        repository.rollback_onboarding.assert_not_called()

        allowed_request = self.factory.post(
            f"/api/certs/onboarding/{vessel['vessel_id']}/rollback/",
            {"reason": "Reset failed onboarding import for this vessel before go-live."},
            format="json",
        )
        force_authenticate(allowed_request, user=self.dpa)
        response = OnboardingRollbackView.as_view()(allowed_request, vessel_id=vessel["vessel_id"])

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["config"]["lifecycleStatus"], "onboarding_in_progress")
        repository.rollback_onboarding.assert_called_once_with(vessel_id=vessel["vessel_id"], actor=self.dpa)
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "onboarding_rollback")
        self.assertEqual(record_audit_event.call_args.kwargs["reason"], "Reset failed onboarding import for this vessel before go-live.")
        self.assertEqual(record_audit_event.call_args.kwargs["metadata"]["resetToStep"], 1)
        self.assertEqual(record_audit_event.call_args.kwargs["metadata"]["cancelledBatchCount"], 2)

    @patch("apps.certs.views.onboarding_views.repository")
    def test_rollback_is_unavailable_after_fm_signoff(self, repository) -> None:
        vessel = vessel_row()
        repository.resolve_vessel.return_value = vessel
        repository.get_vessel_config.return_value = config_row(vessel_id=vessel["vessel_id"], lifecycle_status="active")
        request = self.factory.post(
            f"/api/certs/onboarding/{vessel['vessel_id']}/rollback/",
            {"reason": "Trying to reset after go-live should be blocked."},
            format="json",
        )
        force_authenticate(request, user=self.dpa)

        response = OnboardingRollbackView.as_view()(request, vessel_id=vessel["vessel_id"])

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["detail"], "Onboarding rollback is available only before FM sign-off.")
        repository.rollback_onboarding.assert_not_called()

    @patch("apps.certs.services.onboarding_repository.connection")
    def test_repository_rollback_cancels_batches_and_supersedes_onboarding_artifacts(self, connection) -> None:
        vessel_id = str(uuid.uuid4())
        actor = make_user(role="DPA", form_ids=["CERT_F_005"], process_ids=["CERT_P_010"])
        cursor = MagicMock()
        cursor.description = [
            ("vessel_id",),
            ("anniversary_date",),
            ("ship_type",),
            ("marine_supt_user_id",),
            ("technical_manager_user_id",),
            ("lifecycle_status",),
            ("mandatory_coverage_override_reason",),
            ("mandatory_coverage_override_at",),
            ("mandatory_coverage_override_by",),
            ("updated_at",),
            ("updated_by",),
        ]
        cursor.fetchall.side_effect = [
            [
                (
                    vessel_id,
                    "2026-01-15",
                    "bulk_carrier",
                    "marine-1",
                    "tech-1",
                    "onboarding_in_progress",
                    "Temporary missing flag certificate.",
                    "2026-06-26T09:00:00Z",
                    "dpa-1",
                    "2026-06-26T09:00:00Z",
                    "dpa-1",
                )
            ],
            [
                (
                    vessel_id,
                    None,
                    "all",
                    None,
                    None,
                    "onboarding_in_progress",
                    None,
                    None,
                    None,
                    "2026-06-26T10:00:00Z",
                    "dpa-1",
                )
            ],
        ]
        cursor.rowcount = 3
        connection.cursor.return_value.__enter__.return_value = cursor
        batch = batch_row(
            vessel_id=vessel_id,
            pdf_blob_ids_json='["11111111-1111-1111-1111-111111111111","22222222-2222-2222-2222-222222222222"]',
        )

        with patch.object(OnboardingRepository, "list_batches", return_value=[batch]):
            before, after, summary = OnboardingRepository().rollback_onboarding(vessel_id=vessel_id, actor=actor)

        self.assertEqual(before["lifecycle_status"], "onboarding_in_progress")
        self.assertEqual(after["lifecycle_status"], "onboarding_in_progress")
        self.assertEqual(summary["cancelledBatchCount"], 1)
        self.assertEqual(summary["supersededPdfCount"], 2)
        self.assertEqual(summary["supersededTrackedItemCount"], 3)
        executed_sql = "\n".join(call.args[0] for call in cursor.execute.call_args_list)
        self.assertIn("UPDATE dbo.vims_certs_batch_ingest", executed_sql)
        self.assertIn("UPDATE dbo.vims_certs_pdf_blob", executed_sql)
        self.assertIn("UPDATE dbo.vims_certs_tracked_item", executed_sql)
        self.assertIn("anniversary_date = NULL", executed_sql)


if __name__ == "__main__":
    unittest.main()
