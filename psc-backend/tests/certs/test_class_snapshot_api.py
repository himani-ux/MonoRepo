from __future__ import annotations

import os
import unittest
from unittest.mock import patch
import uuid

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import resolve
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.certs.views.snapshot_views import (
    ClassSnapshotDetailView,
    ClassSnapshotListCreateView,
    ClassSnapshotReparseView,
)
from apps.certs.views.reconciliation_views import (
    ReconciliationFlagAddMappingView,
    ReconciliationFlagMarkReviewedView,
    ReconciliationFlagNotifyMasterView,
    ReconciliationRunDetailView,
    ReconciliationRunListView,
)
from tests.certs.test_tracked_item_api import make_user


def snapshot_row(**overrides):
    row = {
        "snapshot_id": uuid.uuid4(),
        "vessel_id": uuid.uuid4(),
        "vessel_name": "KSM Fortitude",
        "imo_number": "9876543",
        "class_society": "NK",
        "pdf_blob_id": uuid.uuid4(),
        "filename": "class-status.pdf",
        "content_size_bytes": 128,
        "printed_on_date": "2026-06-01",
        "uploaded_by": "dpa-1",
        "uploaded_at": "2026-06-26T00:00:00Z",
        "parser_version": "pending-parser-v1",
        "parse_status": "pending",
        "parse_started_at": None,
        "parse_completed_at": None,
        "parser_timeout": False,
        "retry_count": 0,
        "parsed_payload_json": None,
        "parsed_payload_schema_version": 1,
        "reconciliation_run_id": None,
        "upload_sha256": "a" * 64,
        "superseded_user_error": False,
    }
    row.update(overrides)
    return row


def run_row(**overrides):
    row = {
        "run_id": uuid.uuid4(),
        "snapshot_id": uuid.uuid4(),
        "vessel_id": uuid.uuid4(),
        "vessel_name": "KSM Fortitude",
        "imo_number": "9876543",
        "class_society": "NK",
        "printed_on_date": "2026-06-01",
        "parse_status": "success",
        "parser_version": "nk-parser-v1",
        "ran_at": "2026-06-26T00:00:00Z",
        "matches_count": 2,
        "mismatches_count": 1,
        "missing_in_catalog_count": 0,
        "missing_in_class_count": 1,
        "conditional_stc_detected_count": 0,
        "extended_postponed_detected_count": 0,
        "unmapped_low_confidence_count": 0,
        "flags_json": None,
        "notifications_sent_json": None,
        "mapping_version_used": 3,
        "anomaly_breaches_json": None,
    }
    row.update(overrides)
    return row


def flag_row(**overrides):
    row = {
        "flag_id": uuid.uuid4(),
        "run_id": uuid.uuid4(),
        "bucket": "mismatch",
        "catalog_id": uuid.uuid4(),
        "catalog_display_name": "IOPP Certificate",
        "tracked_item_id": uuid.uuid4(),
        "class_row_extract_json": '{"class_code_or_name":"IOPP"}',
        "diff_json": '{"expiry_date":{"class":"2031-01-01","tracked":"2030-01-01"}}',
        "reviewed_by": None,
        "reviewed_at": None,
        "resolution_action": None,
        "resolved_at": None,
    }
    row.update(overrides)
    return row


def mapping_row(**overrides):
    row = {
        "mapping_id": uuid.uuid4(),
        "class_society": "NK",
        "class_code_or_name": "IOPP",
        "catalog_id": uuid.uuid4(),
        "cert_or_survey_kind": "renewal",
        "notes": "Mapped during reconciliation review.",
        "version": 4,
        "active": True,
        "created_at": "2026-06-26T01:00:00Z",
        "created_by": "dpa-1",
        "updated_at": "2026-06-26T01:00:00Z",
        "updated_by": "dpa-1",
    }
    row.update(overrides)
    return row


class CertClassSnapshotApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.vessel_id = str(uuid.uuid4())
        self.reconciliation_reader = make_user(
            role="Fleet Manager",
            form_ids=["CERT_F_003"],
            process_ids=[],
            has_global_vessel_access=True,
        )
        self.snapshot_uploader = make_user(
            role="DPA",
            form_ids=["CERT_F_003"],
            process_ids=["CERT_P_001"],
            has_global_vessel_access=True,
        )
        self.marine_reviewer = make_user(
            role="Marine Superintendent",
            form_ids=["CERT_F_003"],
            process_ids=["CERT_P_002"],
            vessel_ids=[self.vessel_id],
        )
        self.dpa_mapping_writer = make_user(
            role="DPA",
            form_ids=["CERT_F_003"],
            process_ids=["CERT_P_008"],
            has_global_vessel_access=True,
        )
        self.fm_with_mapping_process = make_user(
            role="Fleet Manager",
            form_ids=["CERT_F_003"],
            process_ids=["CERT_P_008"],
            has_global_vessel_access=True,
        )
        self.no_reconciliation_access = make_user(role="DPA", form_ids=["CERT_F_002"], process_ids=["CERT_P_001"])

    def test_uppercase_sql_server_reconciliation_ids_resolve_to_routes(self) -> None:
        uppercase_run_id = "2C494605-7574-F111-ADE9-DA27151DA903"
        uppercase_flag_id = "4A494605-7574-F111-ADE9-DA27151DA903"

        detail_match = resolve(f"/api/certs/reconciliation/runs/{uppercase_run_id}/")
        notify_match = resolve(f"/api/certs/reconciliation/flags/{uppercase_flag_id}/notify-master/")
        reviewed_match = resolve(f"/api/certs/reconciliation/flags/{uppercase_flag_id}/mark-reviewed/")
        mapping_match = resolve(f"/api/certs/reconciliation/flags/{uppercase_flag_id}/add-mapping/")

        self.assertIs(detail_match.func.view_class, ReconciliationRunDetailView)
        self.assertEqual(detail_match.kwargs["run_id"], uppercase_run_id)
        self.assertIs(notify_match.func.view_class, ReconciliationFlagNotifyMasterView)
        self.assertEqual(notify_match.kwargs["flag_id"], uppercase_flag_id)
        self.assertIs(reviewed_match.func.view_class, ReconciliationFlagMarkReviewedView)
        self.assertEqual(reviewed_match.kwargs["flag_id"], uppercase_flag_id)
        self.assertIs(mapping_match.func.view_class, ReconciliationFlagAddMappingView)
        self.assertEqual(mapping_match.kwargs["flag_id"], uppercase_flag_id)

    @patch("apps.certs.views.snapshot_views.repository")
    def test_snapshot_list_requires_reconciliation_form(self, repository) -> None:
        request = self.factory.get("/api/certs/class-snapshots/")
        force_authenticate(request, user=self.no_reconciliation_access)

        response = ClassSnapshotListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.list_snapshots.assert_not_called()

    @patch("apps.certs.views.snapshot_views.record_audit_event")
    @patch("apps.certs.views.snapshot_views.pdf_repository")
    @patch("apps.certs.views.snapshot_views.save_uploaded_class_snapshot_pdf")
    @patch("apps.certs.views.snapshot_views.repository")
    def test_upload_class_snapshot_creates_blob_snapshot_and_upload_audit(
        self,
        repository,
        save_uploaded_class_snapshot_pdf,
        pdf_repository,
        record_audit_event,
    ) -> None:
        snapshot_id = uuid.uuid4()
        blob_id = uuid.uuid4()
        upload = SimpleUploadedFile("class-status.pdf", b"%PDF-1.4 class status", content_type="application/pdf")
        save_uploaded_class_snapshot_pdf.return_value = {
            "relative_path": "certs/vessels/vessel-1/class-snapshots/class-status.pdf",
            "absolute_path": "C:/tmp/class-status.pdf",
            "sha256": "b" * 64,
            "size": 22,
            "filename": "class-status.pdf",
        }
        pdf_repository.create_snapshot_blob.return_value = {"blob_id": blob_id}
        repository.create_snapshot.return_value = snapshot_row(
            snapshot_id=snapshot_id,
            vessel_id=self.vessel_id,
            pdf_blob_id=blob_id,
            upload_sha256="b" * 64,
        )
        request = self.factory.post(
            "/api/certs/class-snapshots/",
            {
                "vesselId": self.vessel_id,
                "classSociety": "NK",
                "printedOnDate": "2026-06-01",
                "file": upload,
            },
            format="multipart",
        )
        force_authenticate(request, user=self.snapshot_uploader)

        response = ClassSnapshotListCreateView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["id"], str(snapshot_id))
        self.assertEqual(response.data["classSociety"], "NK")
        save_uploaded_class_snapshot_pdf.assert_called_once()
        pdf_repository.create_snapshot_blob.assert_called_once()
        repository.create_snapshot.assert_called_once()
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "upload_class_snapshot")

    @patch("apps.certs.views.snapshot_views.repository")
    def test_snapshot_detail_enforces_resolved_vessel_scope(self, repository) -> None:
        snapshot_id = uuid.uuid4()
        repository.get_snapshot.return_value = snapshot_row(snapshot_id=snapshot_id, vessel_id=self.vessel_id)
        scoped_reader = make_user(
            role="Technical Superintendent",
            form_ids=["CERT_F_003"],
            process_ids=[],
            vessel_ids=[str(uuid.uuid4())],
        )
        request = self.factory.get(f"/api/certs/class-snapshots/{snapshot_id}/")
        force_authenticate(request, user=scoped_reader)

        response = ClassSnapshotDetailView.as_view()(request, snapshot_id=snapshot_id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("apps.certs.views.snapshot_views.record_audit_event")
    @patch("apps.certs.views.snapshot_views.repository")
    def test_reparse_snapshot_records_audit_and_returns_reconciliation_run(self, repository, record_audit_event) -> None:
        snapshot_id = uuid.uuid4()
        run_id = uuid.uuid4()
        repository.reparse_snapshot.return_value = (
            snapshot_row(snapshot_id=snapshot_id, vessel_id=self.vessel_id, parse_status="success", reconciliation_run_id=run_id),
            run_row(run_id=run_id, snapshot_id=snapshot_id, vessel_id=self.vessel_id),
        )
        request = self.factory.post(f"/api/certs/class-snapshots/{snapshot_id}/reparse/", {}, format="json")
        force_authenticate(request, user=self.snapshot_uploader)

        response = ClassSnapshotReparseView.as_view()(request, snapshot_id=snapshot_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["snapshot"]["reconciliationRunId"], str(run_id))
        self.assertEqual(response.data["reconciliationRun"]["id"], str(run_id))
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "reparse_snapshot")

    @patch("apps.certs.views.reconciliation_views.repository")
    def test_run_list_serializes_bucket_counts(self, repository) -> None:
        repository.list_runs.return_value = {
            "count": 1,
            "results": [
                run_row(
                    vessel_id=self.vessel_id,
                    anomaly_breaches_json='[{"type":"mismatch_rate","severity":"critical","value":0.22,"threshold":0.15}]',
                )
            ],
        }
        request = self.factory.get("/api/certs/reconciliation/runs/")
        force_authenticate(request, user=self.reconciliation_reader)

        response = ReconciliationRunListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["mismatchesCount"], 1)
        self.assertEqual(response.data["results"][0]["anomalyBreaches"][0]["type"], "mismatch_rate")
        self.assertEqual(response.data["results"][0]["anomalyBreaches"][0]["severity"], "critical")

    @patch("apps.certs.views.reconciliation_views.repository")
    def test_run_detail_serializes_flags_and_enforces_scope(self, repository) -> None:
        run_id = uuid.uuid4()
        flag = flag_row(run_id=run_id)
        repository.get_run_detail.return_value = {
            "run": run_row(run_id=run_id, vessel_id=self.vessel_id),
            "flags": [flag],
        }
        request = self.factory.get(f"/api/certs/reconciliation/runs/{run_id}/")
        force_authenticate(request, user=self.marine_reviewer)

        response = ReconciliationRunDetailView.as_view()(request, run_id=run_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(run_id))
        self.assertEqual(response.data["flags"][0]["bucket"], "mismatch")
        self.assertEqual(response.data["flags"][0]["diff"]["expiry_date"]["tracked"], "2030-01-01")

    @patch("apps.certs.views.reconciliation_views.record_audit_event")
    @patch("apps.certs.views.reconciliation_views.repository")
    def test_mark_reviewed_requires_marine_or_dpa_and_records_reconciliation_audit(
        self,
        repository,
        record_audit_event,
    ) -> None:
        flag_id = uuid.uuid4()
        before = flag_row(flag_id=flag_id, run_id=uuid.uuid4())
        after = flag_row(
            flag_id=flag_id,
            run_id=before["run_id"],
            reviewed_by="marine-superintendent-1",
            reviewed_at="2026-06-26T01:00:00Z",
            resolution_action="marked_reviewed",
            resolved_at="2026-06-26T01:00:00Z",
        )
        repository.review_flag.return_value = {
            "before": before,
            "after": after,
            "run": run_row(run_id=before["run_id"], vessel_id=self.vessel_id),
        }
        repository.get_flag_context.return_value = {
            "flag_id": flag_id,
            "run_id": before["run_id"],
            "vessel_id": self.vessel_id,
        }
        request = self.factory.post(
            f"/api/certs/reconciliation/flags/{flag_id}/mark-reviewed/",
            {"reason": "Reviewed against the class snapshot and accepted."},
            format="json",
        )
        force_authenticate(request, user=self.marine_reviewer)

        response = ReconciliationFlagMarkReviewedView.as_view()(request, flag_id=flag_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["resolutionAction"], "marked_reviewed")
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "reconciliation_review")
        self.assertEqual(record_audit_event.call_args.kwargs["entity_type"], "reconciliation_flag")

    @patch("apps.certs.views.reconciliation_views.record_audit_event")
    @patch("apps.certs.views.reconciliation_views.repository")
    def test_dpa_can_add_class_mapping_from_unmapped_flag_and_audit_versioned_mapping(
        self,
        repository,
        record_audit_event,
    ) -> None:
        flag_id = uuid.uuid4()
        run_id = uuid.uuid4()
        catalog_id = uuid.uuid4()
        new_mapping = mapping_row(catalog_id=catalog_id)
        resolved_flag = flag_row(
            flag_id=flag_id,
            run_id=run_id,
            bucket="missing_in_catalog",
            class_row_extract_json='{"class_code_or_name":"IOPP"}',
            resolution_action="mapping_added",
            resolved_at="2026-06-26T01:00:00Z",
        )
        repository.get_flag_context.return_value = {
            "flag_id": flag_id,
            "run_id": run_id,
            "snapshot_id": uuid.uuid4(),
            "vessel_id": self.vessel_id,
            "class_society": "NK",
            "bucket": "missing_in_catalog",
            "class_row_extract_json": '{"class_code_or_name":"IOPP"}',
        }
        repository.add_mapping_for_flag.return_value = {
            "audit_action": "add_class_mapping",
            "before": None,
            "after": new_mapping,
            "flag_after": resolved_flag,
            "run": run_row(run_id=run_id, vessel_id=self.vessel_id, mapping_version_used=4),
        }
        request = self.factory.post(
            f"/api/certs/reconciliation/flags/{flag_id}/add-mapping/",
            {
                "catalogId": str(catalog_id),
                "certOrSurveyKind": "renewal",
                "notes": "Mapped from NK class status row.",
                "reason": "DPA mapped the NK IOPP row after review.",
            },
            format="json",
        )
        force_authenticate(request, user=self.dpa_mapping_writer)

        response = ReconciliationFlagAddMappingView.as_view()(request, flag_id=flag_id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["mapping"]["version"], 4)
        self.assertEqual(response.data["reconciliationRun"]["mappingVersionUsed"], 4)
        repository.add_mapping_for_flag.assert_called_once_with(
            str(flag_id),
            catalog_id=str(catalog_id),
            cert_or_survey_kind="renewal",
            notes="Mapped from NK class status row.",
            actor_id="dpa-1",
        )
        record_audit_event.assert_called_once()
        self.assertEqual(record_audit_event.call_args.kwargs["action"], "add_class_mapping")
        self.assertEqual(record_audit_event.call_args.kwargs["entity_type"], "class_code_mapping")
        self.assertEqual(record_audit_event.call_args.kwargs["after"]["version"], 4)
        self.assertEqual(record_audit_event.call_args.kwargs["metadata"]["flagId"], str(flag_id))

    @patch("apps.certs.views.reconciliation_views.repository")
    def test_fm_cannot_add_class_mapping_even_with_mapping_process(self, repository) -> None:
        flag_id = uuid.uuid4()
        request = self.factory.post(
            f"/api/certs/reconciliation/flags/{flag_id}/add-mapping/",
            {
                "catalogId": str(uuid.uuid4()),
                "certOrSurveyKind": "renewal",
                "reason": "Fleet Manager should not edit class mappings.",
            },
            format="json",
        )
        force_authenticate(request, user=self.fm_with_mapping_process)

        response = ReconciliationFlagAddMappingView.as_view()(request, flag_id=flag_id)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        repository.add_mapping_for_flag.assert_not_called()


if __name__ == "__main__":
    unittest.main()
