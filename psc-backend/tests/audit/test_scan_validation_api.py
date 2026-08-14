from __future__ import annotations

import json
import os
from types import SimpleNamespace
import unittest
import uuid

import django
from django.apps import apps
from django.db import connection


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-scan-validation-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "apps.accounts",
                "apps.masters",
                "apps.inspection",
                "apps.car",
                "apps.notifications",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
            ROOT_URLCONF="core.urls",
        )

    if not apps.ready:
        django.setup()


bootstrap_django()

from apps.accounts.models import RoleCodes  # noqa: E402
from apps.inspection.audit.models import AuditAttachment, AuditDetail, AuditFinding, AuditPdfGeneration  # noqa: E402
from apps.inspection.audit.permissions import AUDIT_P_001, AUDIT_P_018  # noqa: E402
from apps.inspection.audit.services.pdf_validation import validate_uploaded_scan  # noqa: E402
from apps.inspection.audit.views import AuditAttachmentValidateView, AuditScanValidationQueueView  # noqa: E402
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402


SCHEMA_MODELS = [
    AuditDetail,
    AuditFinding,
    AuditAttachment,
    AuditPdfGeneration,
]


def make_user(
    *,
    role: str = "DPA",
    user_type: str = "OFFICE",
    user_id: str = "dpa-1",
    process_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        process_ids=process_ids or [],
        display_name="DPA User",
        username=user_id,
        is_authenticated=True,
    )


class AuditScanValidationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            existing_tables = set(connection.introspection.table_names())
            for model in reversed(SCHEMA_MODELS):
                if model._meta.db_table in existing_tables:
                    schema_editor.delete_model(model)
            for model in SCHEMA_MODELS:
                schema_editor.create_model(model)

    @classmethod
    def tearDownClass(cls) -> None:
        with connection.schema_editor() as schema_editor:
            for model in reversed(SCHEMA_MODELS):
                schema_editor.delete_model(model)
        super().tearDownClass()

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            for model in reversed(SCHEMA_MODELS):
                cursor.execute(f'DELETE FROM "{model._meta.db_table}"')
        self.factory = APIRequestFactory()
        self.audit_detail = self._audit_detail()
        self.finding = self._finding(self.audit_detail)
        self.generation = self._pdf_generation(
            audit_detail_id=self.audit_detail.id,
            audit_finding_id=self.finding.id,
            content_hash="a" * 64,
            pdf_version=1,
        )
        self.attachment = self._attachment(
            audit_detail_id=self.audit_detail.id,
            audit_finding_id=self.finding.id,
        )

    def _queue(self, user):
        request = self.factory.get("/api/audit/dpa/scan-validation-queue/")
        force_authenticate(request, user=user)
        return AuditScanValidationQueueView.as_view()(request)

    def _validate(self, attachment_id, payload, user):
        request = self.factory.post(f"/api/audit/attachments/{attachment_id}/validate/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditAttachmentValidateView.as_view()(request, id=attachment_id)

    def _payload(self, generation: AuditPdfGeneration | None = None, **overrides):
        generation = generation or self.generation
        payload = {
            "finding_id": str(generation.audit_finding_id) if generation.audit_finding_id else None,
            "audit_detail_id": str(generation.audit_detail_id),
            "pdf_kind": generation.pdf_kind,
            "pdf_version": generation.pdf_version,
            "content_hash": generation.content_hash,
        }
        payload.update(overrides)
        return payload

    def test_matching_signed_scan_records_matched_status(self) -> None:
        result = validate_uploaded_scan(self.attachment, decoded_qr_payload=self._payload())

        self.assertEqual(result.status, "MATCHED")
        self.attachment.refresh_from_db()
        self.assertEqual(self.attachment.pdf_hash_validation_status, "MATCHED")
        self.assertEqual(self.attachment.linked_pdf_generation_id, self.generation.id)

    def test_different_finding_scan_records_mismatch_and_appears_in_queue(self) -> None:
        other_finding = self._finding(self.audit_detail)
        other_generation = self._pdf_generation(
            audit_detail_id=self.audit_detail.id,
            audit_finding_id=other_finding.id,
            content_hash="b" * 64,
            pdf_version=1,
        )
        response = self._validate(
            self.attachment.id,
            {"qr_payload": self._payload(other_generation)},
            make_user(process_ids=[AUDIT_P_018]),
        )

        self.assertEqual(response.status_code, 200)
        self.attachment.refresh_from_db()
        self.assertEqual(self.attachment.pdf_hash_validation_status, "MISMATCH_FINDING")

        queue_response = self._queue(make_user(process_ids=[AUDIT_P_018]))
        self.assertEqual(queue_response.status_code, 200)
        self.assertEqual(queue_response.data["data"]["count"], 1)
        self.assertEqual(queue_response.data["data"]["results"][0]["id"], str(self.attachment.id))

    def test_missing_qr_payload_records_unreadable_without_blocking_upload(self) -> None:
        response = self._validate(self.attachment.id, {}, make_user(process_ids=[AUDIT_P_018]))

        self.assertEqual(response.status_code, 200)
        self.attachment.refresh_from_db()
        self.assertEqual(self.attachment.pdf_hash_validation_status, "UNREADABLE")
        self.assertIn("unreadable", self.attachment.validator_message.lower())

    def test_superseded_generation_records_version_mismatch(self) -> None:
        self.generation.is_superseded = True
        self.generation.save(update_fields=["is_superseded"])
        self._pdf_generation(
            audit_detail_id=self.audit_detail.id,
            audit_finding_id=self.finding.id,
            content_hash="c" * 64,
            pdf_version=2,
        )

        validate_uploaded_scan(self.attachment, decoded_qr_payload=self._payload(self.generation))

        self.attachment.refresh_from_db()
        self.assertEqual(self.attachment.pdf_hash_validation_status, "MISMATCH_VERSION")
        self.assertEqual(self.attachment.linked_pdf_generation_id, self.generation.id)

    def test_external_audit_attachment_is_not_applicable(self) -> None:
        external_attachment = self._attachment(
            audit_detail_id=self.audit_detail.id,
            audit_finding_id=None,
            category="EXTERNAL_AUDIT_REPORT",
        )

        result = validate_uploaded_scan(external_attachment, decoded_qr_payload=self._payload())

        self.assertEqual(result.status, "NOT_APPLICABLE")
        external_attachment.refresh_from_db()
        self.assertEqual(external_attachment.pdf_hash_validation_status, "NOT_APPLICABLE")

    def test_scan_queue_and_actions_require_dpa_with_audit_p018(self) -> None:
        validate_uploaded_scan(self.attachment, decoded_qr_payload=None)
        no_gate = make_user(role=RoleCodes.PHYSICAL_VERIFIER, user_id="no-gate", process_ids=[AUDIT_P_001])
        seq_user = make_user(role=RoleCodes.OFFICE_SSQE, user_id="seq-1", process_ids=[AUDIT_P_018])

        self.assertEqual(self._queue(no_gate).status_code, 403)
        self.assertEqual(self._queue(seq_user).status_code, 403)

    def test_accept_with_reason_requires_fifty_chars_and_removes_row_from_queue(self) -> None:
        validate_uploaded_scan(self.attachment, decoded_qr_payload=None)
        dpa = make_user(process_ids=[AUDIT_P_018])

        short_response = self._validate(
            self.attachment.id,
            {"action": "ACCEPT_WITH_REASON", "reason": "too short"},
            dpa,
        )
        self.assertEqual(short_response.status_code, 400)

        reason = "DPA reviewed the wet-ink scan and accepts the QR mismatch as a documented exception."
        response = self._validate(
            self.attachment.id,
            {"action": "ACCEPT_WITH_REASON", "reason": reason},
            dpa,
        )

        self.assertEqual(response.status_code, 200)
        self.attachment.refresh_from_db()
        self.assertTrue(self.attachment.validator_message.startswith("DPA_ACCEPTED"))
        self.assertEqual(self._queue(dpa).data["data"]["count"], 0)

    def test_reject_and_request_rescan_removes_row_from_queue(self) -> None:
        validate_uploaded_scan(self.attachment, decoded_qr_payload=None)
        dpa = make_user(process_ids=[AUDIT_P_018])

        response = self._validate(
            self.attachment.id,
            {"action": "REJECT_RESCAN", "reason": "Request a clean signed scan from the vessel."},
            dpa,
        )

        self.assertEqual(response.status_code, 200)
        self.attachment.refresh_from_db()
        self.assertTrue(self.attachment.validator_message.startswith("DPA_REJECTED_RESCAN"))
        self.assertEqual(self._queue(dpa).data["data"]["count"], 0)

    def _audit_detail(self) -> AuditDetail:
        return AuditDetail.objects.create(
            psc_inspection_id=uuid.uuid4().hex,
            vessel_id=uuid.uuid4().hex,
            audit_classification="INTERNAL",
            auditee_type="VESSEL",
            audit_subtype="ANNUAL_INTERNAL",
            lead_auditor_name="Lead Auditor",
            lead_auditor_company="KSM",
            trigger_reason="SCHEDULED",
            audit_start_date="2026-07-29",
            status="IN_PROGRESS",
            created_by="auditor-1",
        )

    def _finding(self, audit_detail: AuditDetail) -> AuditFinding:
        return AuditFinding.objects.create(
            psc_deficiency_id=uuid.uuid4().hex,
            audit_detail_id=audit_detail.id,
            audit_classification="INTERNAL",
            finding_type="NC",
            nc_category="MINOR_NC",
            standard_code="ISM",
            objective_evidence="Objective evidence.",
            description="Finding description.",
            created_by="auditor-1",
        )

    def _pdf_generation(
        self,
        *,
        audit_detail_id,
        audit_finding_id,
        content_hash: str,
        pdf_version: int,
    ) -> AuditPdfGeneration:
        generation = AuditPdfGeneration.objects.create(
            audit_detail_id=audit_detail_id,
            audit_finding_id=audit_finding_id,
            pdf_kind="KSM_F_NC_001",
            pdf_version=pdf_version,
            content_hash=content_hash,
            qr_payload=json.dumps(
                {
                    "finding_id": str(audit_finding_id) if audit_finding_id else None,
                    "audit_detail_id": str(audit_detail_id),
                    "pdf_kind": "KSM_F_NC_001",
                    "pdf_version": pdf_version,
                    "content_hash": content_hash,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            generated_by="test",
        )
        return generation

    def _attachment(self, *, audit_detail_id, audit_finding_id, category="SIGNED_NC_SCAN") -> AuditAttachment:
        return AuditAttachment.objects.create(
            audit_detail_id=audit_detail_id,
            audit_finding_id=audit_finding_id,
            file_name="NC-B-signed.pdf",
            file_path="/tmp/NC-B-signed.pdf",
            file_size=1024,
            mime_type="application/pdf",
            category=category,
            uploaded_by="master-1",
        )


if __name__ == "__main__":
    unittest.main()
