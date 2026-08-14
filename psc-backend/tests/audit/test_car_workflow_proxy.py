from __future__ import annotations

import os
import unittest
import uuid
from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import django
from django.apps import apps
from django.db import connection
from django.utils import timezone


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-car-workflow-test-secret-key-1234567890",
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
from apps.car.models import ActivityHistory, AuditLog  # noqa: E402
from apps.car.views import CARWorkflowView  # noqa: E402
from apps.inspection.audit.models import (  # noqa: E402
    AuditAttachment,
    AuditDetail,
    AuditFinding,
    AuditFindingNC,
    AuditFindingSignature,
    CertWritebackOutbox,
)
from apps.inspection.audit.permissions import AUDIT_P_004, AUDIT_P_008, AUDIT_P_013  # noqa: E402
from apps.inspection.audit.services.finding import create_audit_finding  # noqa: E402
from apps.inspection.audit.views import AuditFindingCarWorkflowView  # noqa: E402
from apps.inspection.deficiency_models import CAR, CARStatus, Deficiency  # noqa: E402
from apps.inspection.models import Inspection  # noqa: E402
from apps.inspection.workflow import WorkflowAction  # noqa: E402
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402


SCHEMA_MODELS = [
    Inspection,
    CAR,
    Deficiency,
    ActivityHistory,
    AuditLog,
    AuditDetail,
    AuditFinding,
    AuditFindingNC,
    AuditFindingSignature,
    AuditAttachment,
    CertWritebackOutbox,
]


def make_user(
    *,
    role: str,
    user_type: str,
    user_id: str,
    display_name: str,
    vessel_id=None,
    rank: str | None = None,
    crew_id: str | None = None,
    process_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        vessel_id=str(vessel_id) if vessel_id else None,
        process_ids=process_ids or [],
        display_name=display_name,
        username=display_name.lower().replace(" ", "_"),
        rank=rank,
        crew_id=crew_id,
        is_authenticated=True,
    )


class AuditCarWorkflowProxyTests(unittest.TestCase):
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
                cursor.execute(f"DELETE FROM {model._meta.db_table}")

        self.vessel_code_lookup = patch("apps.inspection.deficiency_models._lookup_vessel_code", return_value="TST")
        self.vessel_code_lookup.start()
        self.addCleanup(self.vessel_code_lookup.stop)

        self.factory = APIRequestFactory()
        self.vessel_id = uuid.uuid4()
        self.master = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type="VESSEL",
            user_id="master-1",
            display_name="Vessel Master",
            vessel_id=self.vessel_id,
            rank="Master",
            process_ids=[AUDIT_P_008],
        )
        self.office_supt = make_user(
            role=RoleCodes.OFFICE_SUPT,
            user_type="OFFICE",
            user_id="supt-1",
            display_name="Office Supt",
            process_ids=[AUDIT_P_004],
        )
        self.lead_auditor = make_user(
            role=RoleCodes.OFFICE_SSQE,
            user_type="OFFICE",
            user_id="lead-1",
            display_name="Lead Auditor",
            process_ids=[AUDIT_P_004],
        )
        self.dpa = make_user(
            role=RoleCodes.DPA,
            user_type="OFFICE",
            user_id="dpa-1",
            display_name="DPA",
            process_ids=[AUDIT_P_013],
        )

    def _post_proxy(self, finding_id, payload, user):
        request = self.factory.post(
            f"/api/audit/findings/{finding_id}/car/workflow/",
            payload,
            format="json",
        )
        force_authenticate(request, user=user)
        with (
            patch.object(CARWorkflowView, "_send_notifications", return_value=None),
            patch("apps.car.validators.validate_car_submission", return_value=[]),
        ):
            return AuditFindingCarWorkflowView.as_view()(request, id=finding_id)

    def _post_psc_car(self, car_id, payload, user):
        request = self.factory.post(f"/api/psc/cars/{car_id}/workflow/", payload, format="json")
        force_authenticate(request, user=user)
        with patch.object(CARWorkflowView, "_send_notifications", return_value=None):
            return CARWorkflowView.as_view()(request, id=car_id)

    def _create_audit_detail(self, *, classification="INTERNAL", lead_auditor_user_id="lead-1"):
        inspection = Inspection.objects.create(
            vessel_id=self.vessel_id,
            inspection_type="AUDIT",
            inspection_date=date(2026, 7, 29),
            port_place="Singapore",
            country="Singapore",
            created_by="auditor-1",
        )
        audit_detail = AuditDetail.objects.create(
            psc_inspection_id=inspection.id.hex,
            vessel_id=self.vessel_id.hex,
            audit_classification=classification,
            auditee_type="VESSEL",
            audit_subtype="ANNUAL_INTERNAL",
            lead_auditor_name="Lead Auditor",
            lead_auditor_company="KSM",
            lead_auditor_user_id=lead_auditor_user_id,
            trigger_reason="SCHEDULED",
            audit_start_date=date(2026, 7, 29),
            audit_end_date=date(2026, 7, 30),
            status="IN_PROGRESS",
            linked_cert_ids_csv=str(uuid.uuid4()) if classification == "EXTERNAL" else None,
            certificate_impact="CERT_VALID" if classification == "EXTERNAL" else None,
            created_by="auditor-1",
        )
        return inspection, audit_detail

    def _create_audit_finding(self, *, classification="INTERNAL"):
        _inspection, audit_detail = self._create_audit_detail(classification=classification)
        result = create_audit_finding(
            audit_detail_id=audit_detail.id,
            finding_type="NC",
            nc_category="MINOR_NC",
            description="Audit NC requiring closure workflow.",
            def_code_id="10101",
            created_by="auditor-1",
        )
        AuditFindingNC.objects.create(
            audit_finding_id=result.finding.id,
            created_by="auditor-1",
        )
        return audit_detail, result.finding, result.deficiency, result.car

    def test_car_status_choices_include_audit_nc_states(self) -> None:
        for value in (
            "OFFICE_DRAFTED",
            "SUBMITTED_TO_LEAD_AUDITOR",
            "LEAD_AUDITOR_CLOSED",
            "AWAITING_EXTERNAL_CLOSE_OUT",
            "EXTERNAL_AUDITOR_CLOSED",
        ):
            self.assertIn(value, CARStatus.values)

    def test_proxy_reaches_existing_car_workflow_for_internal_lead_auditor_submission(self) -> None:
        _audit_detail, finding, _deficiency, car = self._create_audit_finding()
        car.status = CARStatus.PIC_REVIEW
        car.save(update_fields=["status"])
        AuditFindingSignature.objects.create(
            audit_finding_id=finding.id,
            signer_user_id="supt-1",
            signature_event_type="SUPT_SIGN",
            signed_at=timezone.now(),
            created_by="supt-1",
        )

        response = self._post_proxy(
            finding.id,
            {"action": WorkflowAction.SUBMIT_TO_LEAD_AUDITOR, "comment": "PIC review accepted."},
            self.office_supt,
        )

        car.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(car.status, CARStatus.SUBMITTED_TO_LEAD_AUDITOR)
        self.assertTrue(
            ActivityHistory.objects.filter(
                event_type="CAR_WORKFLOW_SUBMIT_TO_LEAD_AUDITOR",
                entity_id=car.id,
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                entity_type="CAR",
                entity_id=car.id,
                old_value=CARStatus.PIC_REVIEW,
                new_value=CARStatus.SUBMITTED_TO_LEAD_AUDITOR,
            ).exists()
        )

    def test_proxy_requires_audit_p004_for_internal_pic_action(self) -> None:
        _audit_detail, finding, _deficiency, car = self._create_audit_finding()
        car.status = CARStatus.PIC_REVIEW
        car.save(update_fields=["status"])
        user_without_gate = make_user(
            role=RoleCodes.PHYSICAL_VERIFIER,
            user_type="OFFICE",
            user_id="supt-no-gate",
            display_name="Office User No Gate",
        )

        response = self._post_proxy(
            finding.id,
            {"action": WorkflowAction.SUBMIT_TO_LEAD_AUDITOR, "comment": "PIC review accepted."},
            user_without_gate,
        )

        car.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(car.status, CARStatus.PIC_REVIEW)

    def test_lead_auditor_closes_internal_nc_after_part_f_signature(self) -> None:
        _audit_detail, finding, _deficiency, car = self._create_audit_finding()
        car.status = CARStatus.SUBMITTED_TO_LEAD_AUDITOR
        car.save(update_fields=["status"])
        AuditFindingNC.objects.filter(audit_finding_id=finding.id).update(
            acceptance_decision="ACCEPTED",
            acceptance_signer_at=timezone.now(),
        )

        response = self._post_proxy(
            finding.id,
            {"action": WorkflowAction.LEAD_AUDITOR_CLOSE, "comment": "Part F accepted."},
            self.lead_auditor,
        )

        car.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(car.status, CARStatus.LEAD_AUDITOR_CLOSED)
        nc = AuditFindingNC.objects.get(audit_finding_id=finding.id)
        self.assertEqual(nc.effectiveness_review_date, timezone.localdate() + timedelta(days=30))
        self.assertFalse(nc.effectiveness_overdue)

    def test_master_submit_to_pic_from_office_drafted_requires_part_b_signature(self) -> None:
        _audit_detail, finding, _deficiency, car = self._create_audit_finding()
        car.status = CARStatus.OFFICE_DRAFTED
        car.save(update_fields=["status"])

        blocked = self._post_proxy(
            finding.id,
            {"action": WorkflowAction.SUBMIT_TO_PIC},
            self.master,
        )
        self.assertEqual(blocked.status_code, 400)
        self.assertIn("Signature missing for Part B/C", blocked.data["message"])

        AuditFindingNC.objects.filter(audit_finding_id=finding.id).update(
            master_immediate_sign_at=timezone.now(),
        )
        allowed = self._post_proxy(
            finding.id,
            {"action": WorkflowAction.SUBMIT_TO_PIC},
            self.master,
        )

        car.refresh_from_db()
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(car.status, CARStatus.SUBMITTED_TO_PIC)

    def test_lead_auditor_cannot_claim_pic_review_on_own_audit(self) -> None:
        _audit_detail, finding, _deficiency, car = self._create_audit_finding()
        car.status = CARStatus.SUBMITTED_TO_PIC
        car.save(update_fields=["status"])

        response = self._post_proxy(
            finding.id,
            {"action": WorkflowAction.START_PIC_REVIEW, "comment": "Trying to self-claim."},
            self.lead_auditor,
        )

        car.refresh_from_db()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "LEAD_AUDITOR_PIC_DENIED")
        self.assertEqual(car.status, CARStatus.SUBMITTED_TO_PIC)

    def test_missing_part_f_signature_blocks_lead_auditor_close(self) -> None:
        _audit_detail, finding, _deficiency, car = self._create_audit_finding()
        car.status = CARStatus.SUBMITTED_TO_LEAD_AUDITOR
        car.save(update_fields=["status"])

        response = self._post_proxy(
            finding.id,
            {"action": WorkflowAction.LEAD_AUDITOR_CLOSE, "comment": "No Part F signature."},
            self.lead_auditor,
        )

        car.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertIn("Signature missing for Part F", response.data["message"])
        self.assertEqual(car.status, CARStatus.SUBMITTED_TO_LEAD_AUDITOR)

    def test_external_nc_requires_closeout_letter_before_external_closure(self) -> None:
        audit_detail, finding, _deficiency, car = self._create_audit_finding(classification="EXTERNAL")
        car.status = CARStatus.AWAITING_EXTERNAL_CLOSE_OUT
        car.save(update_fields=["status"])

        blocked = self._post_proxy(
            finding.id,
            {"action": WorkflowAction.CONFIRM_EXTERNAL_CLOSE, "comment": "DPA confirms external closure."},
            self.dpa,
        )
        self.assertEqual(blocked.status_code, 400)
        self.assertIn("External close-out letter is required", blocked.data["message"])

        AuditAttachment.objects.create(
            audit_detail_id=audit_detail.id,
            audit_finding_id=finding.id,
            file_name="external-close-out.pdf",
            file_path="/tmp/external-close-out.pdf",
            mime_type="application/pdf",
            category="EXTERNAL_CLOSE_OUT_LETTER",
            uploaded_by="dpa-1",
        )
        with patch(
            "apps.inspection.audit.services.certs_writeback.get_cert_snapshot",
            return_value=SimpleNamespace(
                version=7,
                anniversary_date=date(2026, 7, 11),
                window_open=date(2027, 4, 11),
                window_close=date(2027, 7, 11),
                issue_date=date(2021, 7, 11),
                expiry_date=date(2026, 7, 11),
                last_done_date=date(2025, 7, 10),
                next_due_date=date(2027, 7, 11),
                status="ok",
                lifecycle_status="active",
            ),
        ):
            allowed = self._post_proxy(
                finding.id,
                {"action": WorkflowAction.CONFIRM_EXTERNAL_CLOSE, "comment": "DPA confirms external closure."},
                self.dpa,
            )

        car.refresh_from_db()
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(car.status, CARStatus.EXTERNAL_AUDITOR_CLOSED)
        outbox = CertWritebackOutbox.objects.get()
        self.assertEqual(outbox.audit_detail_id, audit_detail.id)
        self.assertEqual(outbox.expected_cert_version, 7)
        self.assertEqual(outbox.status, "QUEUED")
        self.assertIn('"certificateImpact": "CERT_VALID"', outbox.writeback_payload)

    def test_external_closure_enqueue_error_does_not_block_closure(self) -> None:
        audit_detail, finding, _deficiency, car = self._create_audit_finding(classification="EXTERNAL")
        car.status = CARStatus.AWAITING_EXTERNAL_CLOSE_OUT
        car.save(update_fields=["status"])
        AuditAttachment.objects.create(
            audit_detail_id=audit_detail.id,
            audit_finding_id=finding.id,
            file_name="external-close-out.pdf",
            file_path="/tmp/external-close-out.pdf",
            mime_type="application/pdf",
            category="EXTERNAL_CLOSE_OUT_LETTER",
            uploaded_by="dpa-1",
        )

        with (
            patch(
                "apps.inspection.audit.views.car_workflow.enqueue_external_close_writebacks",
                side_effect=RuntimeError("certs unavailable"),
            ),
            self.assertLogs("apps.inspection.audit.views.car_workflow", level="ERROR") as logs,
        ):
            response = self._post_proxy(
                finding.id,
                {"action": WorkflowAction.CONFIRM_EXTERNAL_CLOSE, "comment": "DPA confirms external closure."},
                self.dpa,
            )

        car.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(car.status, CARStatus.EXTERNAL_AUDITOR_CLOSED)
        self.assertEqual(CertWritebackOutbox.objects.count(), 0)
        self.assertIn("Audit external Certs writeback enqueue failed", logs.output[0])

    def test_psc_workflow_still_submits_to_dpa(self) -> None:
        psc_inspection = Inspection.objects.create(
            vessel_id=self.vessel_id,
            inspection_type="PSC",
            psc_subtype="INITIAL",
            inspection_date=date(2026, 7, 29),
            port_place="Singapore",
            country="Singapore",
            created_by="psc-user",
        )
        deficiency = Deficiency.objects.create(
            inspection=psc_inspection,
            def_code_id="10101",
            def_code="10101",
            description="PSC deficiency",
            created_by="psc-user",
        )
        deficiency.refresh_from_db()
        car = deficiency.car
        car.status = CARStatus.PIC_REVIEW
        car.save(update_fields=["status"])

        response = self._post_psc_car(
            car.id,
            {"action": WorkflowAction.SUBMIT_TO_DPA, "comment": "PSC PIC review complete."},
            self.office_supt,
        )

        car.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(car.status, CARStatus.SUBMITTED_TO_DPA)


if __name__ == "__main__":
    unittest.main()
