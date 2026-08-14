from __future__ import annotations

import os
import unittest
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import django
from django.apps import apps
from django.db import connection


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-nc-closure-test-secret-key-1234567890",
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
from apps.car.models import ActivityHistory  # noqa: E402
from apps.inspection.audit.models import (  # noqa: E402
    AuditDetail,
    AuditFinding,
    AuditFindingNC,
    MasterRcaTemplate,
)
from apps.inspection.audit.permissions import AUDIT_P_003, AUDIT_P_004  # noqa: E402
from apps.inspection.audit.services.finding import create_audit_finding  # noqa: E402
from apps.inspection.audit.views import (  # noqa: E402
    AuditFindingNcClosureView,
    AuditFindingNcDraftView,
    AuditFindingNcPartView,
    AuditRcaTemplateMasterView,
)
from apps.inspection.audit.jobs.effectiveness_review import mark_effectiveness_reviews_overdue  # noqa: E402
from apps.inspection.deficiency_models import CAR, CARStatus, Deficiency  # noqa: E402
from apps.inspection.models import Inspection  # noqa: E402
from apps.inspection.workflow import WorkflowAction  # noqa: E402
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402


SCHEMA_MODELS = [
    Inspection,
    CAR,
    Deficiency,
    ActivityHistory,
    AuditDetail,
    AuditFinding,
    AuditFindingNC,
    MasterRcaTemplate,
]


def make_user(
    *,
    role: str = RoleCodes.OFFICE_SSQE,
    user_type: str = "OFFICE",
    user_id: str = "auditor-1",
    process_ids: list[str] | None = None,
    vessel_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        process_ids=process_ids or [],
        vessel_ids=vessel_ids or [],
        display_name="Audit User",
        username="audit_user",
        is_authenticated=True,
    )


class AuditNcClosureApiTests(unittest.TestCase):
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

    def _create_audit_detail(self, *, auditee_type="VESSEL", vessel_id=None):
        inspection = Inspection.objects.create(
            vessel_id=vessel_id or self.vessel_id,
            inspection_type="AUDIT",
            inspection_date=date(2026, 7, 29),
            port_place="Singapore",
            country="Singapore",
            inspector_name="Lead Auditor",
            report_reference="F602-2026-001",
            created_by="auditor-1",
        )
        audit_detail = AuditDetail.objects.create(
            psc_inspection_id=inspection.id.hex,
            vessel_id=(vessel_id or self.vessel_id).hex,
            audit_classification="INTERNAL",
            auditee_type=auditee_type,
            auditee_office_dept="SEQ" if auditee_type == "OFFICE_DEPT" else None,
            audit_subtype="ANNUAL_INTERNAL",
            lead_auditor_name="Lead Auditor",
            lead_auditor_company="KSM",
            lead_auditor_user_id="lead-1",
            trigger_reason="SCHEDULED",
            audit_start_date=date(2026, 7, 29),
            status="IN_PROGRESS",
            created_by="auditor-1",
        )
        return inspection, audit_detail

    def _create_finding(self, *, finding_type="NC", nc_category="MINOR_NC", auditee_type="VESSEL"):
        _inspection, audit_detail = self._create_audit_detail(auditee_type=auditee_type)
        if finding_type == "NC":
            return audit_detail, create_audit_finding(
                audit_detail_id=audit_detail.id,
                finding_type="NC",
                nc_category=nc_category,
                description="Audit NC requiring closure.",
                objective_evidence="Observed during audit.",
                def_code_id="10101",
                certificates_at_risk="DOC",
                created_by="auditor-1",
            ).finding
        return audit_detail, create_audit_finding(
            audit_detail_id=audit_detail.id,
            finding_type="OBSERVATION",
            observation_category="OFI",
            description="Audit observation for routing test.",
            objective_evidence="Observed during audit.",
            def_code_id="10101",
            created_by="auditor-1",
        ).finding

    def _get_nc(self, finding_id, user):
        request = self.factory.get(f"/api/audit/findings/{finding_id}/nc/")
        force_authenticate(request, user=user)
        return AuditFindingNcClosureView.as_view()(request, id=finding_id)

    def _put_part(self, finding_id, part, payload, user):
        request = self.factory.put(f"/api/audit/findings/{finding_id}/nc/{part}/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditFindingNcPartView.as_view(part_name=part)(request, id=finding_id)

    def _post_draft(self, finding_id, payload, user):
        request = self.factory.post(f"/api/audit/findings/{finding_id}/nc/draft/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditFindingNcDraftView.as_view()(request, id=finding_id)

    def _get_rca_templates(self, user, *, category=""):
        request = self.factory.get("/api/audit/masters/rca-templates/", {"category": category})
        force_authenticate(request, user=user)
        return AuditRcaTemplateMasterView.as_view()(request)

    def test_get_nc_creates_closure_record_and_returns_part_a(self) -> None:
        audit_detail, finding = self._create_finding(nc_category="MINOR_NC")
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._get_nc(finding.id, user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AuditFindingNC.objects.count(), 1)
        self.assertEqual(response.data["data"]["finding_id"], str(finding.id))
        self.assertEqual(response.data["data"]["part_a"]["auditor_name"], audit_detail.lead_auditor_name)
        self.assertEqual(response.data["data"]["part_a"]["nc_classification"], "MINOR_NC")
        self.assertTrue(response.data["data"]["car"]["car_number"].startswith("TST-PSC-2026-"))

    def test_part_b_c_d_save_dense_form_fields(self) -> None:
        _audit_detail, finding = self._create_finding(nc_category="MAJOR_NC")
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        part_b = self._put_part(
            finding.id,
            "part-b",
            {
                "immediate_action_text": "Fire door was secured and watchkeeper briefed.",
                "immediate_action_completed_at": "2026-07-30",
            },
            user,
        )
        part_c = self._put_part(
            finding.id,
            "part-c",
            {
                "rca_method": "FIVE_WHY",
                "problem_statement": "Fire door failed to close during accommodation round.",
                "why_1": "Closer arm was loose.",
                "root_cause_categories": ["EQUIPMENT_FAILURE", "SUPERVISION_FAILURE"],
                "root_cause_summary": "The door closer inspection was missed during routine rounds and the loose arm was not detected before the audit.",
            },
            user,
        )
        part_d = self._put_part(
            finding.id,
            "part-d",
            {
                "corrective_action_text": "Replace closer arm and verify all accommodation fire doors.",
                "target_completion_date": "2026-08-05",
                "preventive_action_text": "Add fire-door closer checks to the weekly accommodation inspection.",
                "sms_amendment_required": True,
                "sms_amendment_doc_ref": "SMS-A-20",
            },
            user,
        )

        self.assertEqual(part_b.status_code, 200)
        self.assertEqual(part_c.status_code, 200)
        self.assertEqual(part_d.status_code, 200)
        nc = AuditFindingNC.objects.get(audit_finding_id=finding.id)
        self.assertEqual(nc.rca_method, "FIVE_WHY")
        self.assertEqual(nc.root_cause_categories, "EQUIPMENT_FAILURE,SUPERVISION_FAILURE")
        self.assertTrue(nc.sms_amendment_required)
        self.assertEqual(part_d.data["data"]["part_d"]["sms_amendment_doc_ref"], "SMS-A-20")

    def test_major_nc_part_b_allows_wizard_draft_before_completion_date(self) -> None:
        _audit_detail, finding = self._create_finding(nc_category="MAJOR_NC")
        finding.created_date = datetime(2026, 7, 29, 12, tzinfo=timezone.utc)
        finding.save(update_fields=["created_date"])
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        draft = self._put_part(
            finding.id,
            "part-b",
            {
                "immediate_action_text": "Area was isolated and the watch team was briefed.",
            },
            user,
        )
        late_completion = self._put_part(
            finding.id,
            "part-b",
            {
                "immediate_action_text": "Area was isolated and the watch team was briefed.",
                "immediate_action_completed_at": "2026-08-10",
            },
            user,
        )

        self.assertEqual(draft.status_code, 200)
        self.assertEqual(draft.data["data"]["part_b"]["immediate_action_text"], "Area was isolated and the watch team was briefed.")
        self.assertEqual(late_completion.status_code, 400)
        self.assertEqual(late_completion.data["error"], "AUDIT_NC_CLOSURE_VALIDATION")

    def test_part_c_rejects_short_root_cause_summary(self) -> None:
        _audit_detail, finding = self._create_finding()
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._put_part(
            finding.id,
            "part-c",
            {
                "rca_method": "FIVE_WHY",
                "root_cause_summary": "Too short.",
            },
            user,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "AUDIT_NC_CLOSURE_VALIDATION")

    def test_rca_template_endpoint_returns_active_templates_for_wizard(self) -> None:
        MasterRcaTemplate.objects.create(
            category="TRAINING_GAP",
            title="Permit refresher missed",
            template_text="The assigned team had not completed the latest permit refresher before the task.",
            example_evidence_hint="Training matrix and toolbox meeting record.",
            applicable_def_categories="MINOR_NC,MAJOR_NC",
            code_version="Rev 01 Jan-2026",
            is_active=True,
        )
        MasterRcaTemplate.objects.create(
            category="EQUIPMENT_FAILURE",
            title="Inactive sample",
            template_text="Inactive template.",
            is_active=False,
        )
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._get_rca_templates(user, category="training_gap")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["category"], "TRAINING_GAP")
        self.assertEqual(len(response.data["data"]["templates"]), 1)
        template = response.data["data"]["templates"][0]
        self.assertEqual(template["title"], "Permit refresher missed")
        self.assertIn("permit refresher", template["template_text"])
        self.assertEqual(template["code_version"], "Rev 01 Jan-2026")

    def test_office_draft_saves_part_b_c_and_moves_car_to_office_drafted(self) -> None:
        _audit_detail, finding = self._create_finding(nc_category="MINOR_NC")
        supt = make_user(
            role=RoleCodes.OFFICE_SUPT,
            user_type="OFFICE",
            user_id="supt-1",
            process_ids=[AUDIT_P_003],
            vessel_ids=[str(self.vessel_id)],
        )

        response = self._post_draft(
            finding.id,
            {
                "comment": "Office drafted closure for vessel review.",
                "immediate_action_text": "Temporary containment was drafted for Master review.",
                "rca_method": "FIVE_WHY",
                "problem_statement": "Crew could not complete the draft unaided.",
                "root_cause_categories": ["TRAINING_GAP"],
                "root_cause_summary": "Office review found the vessel team needed a clearer starting point before completing the RCA narrative.",
            },
            supt,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["car"]["status"], CARStatus.OFFICE_DRAFTED)
        nc = AuditFindingNC.objects.get(audit_finding_id=finding.id)
        self.assertEqual(nc.drafted_by_user_id, "supt-1")
        self.assertEqual(nc.rca_method, "FIVE_WHY")
        car = CAR.objects.get(deficiency__id=uuid.UUID(str(finding.psc_deficiency_id)))
        self.assertEqual(car.status, CARStatus.OFFICE_DRAFTED)
        self.assertEqual(car.last_action, WorkflowAction.DRAFT_FOR_VESSEL)

    def test_office_draft_requires_audit_p003(self) -> None:
        _audit_detail, finding = self._create_finding(nc_category="MINOR_NC")
        supt_without_gate = make_user(
            role=RoleCodes.OFFICE_SUPT,
            user_type="OFFICE",
            user_id="supt-no-gate",
            process_ids=[],
            vessel_ids=[str(self.vessel_id)],
        )

        response = self._post_draft(
            finding.id,
            {
                "immediate_action_text": "Temporary containment was drafted.",
                "root_cause_summary": "This office draft is long enough for validation but should not pass authorization.",
            },
            supt_without_gate,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(AuditFindingNC.objects.count(), 1)
        nc = AuditFindingNC.objects.get(audit_finding_id=finding.id)
        self.assertIsNone(nc.drafted_by_user_id)

    def test_parts_e_f_g_require_audit_p004_and_persist_lead_auditor_fields(self) -> None:
        _audit_detail, finding = self._create_finding()
        conductor = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])
        lead = make_user(user_id="lead-1", process_ids=[AUDIT_P_004], vessel_ids=[str(self.vessel_id)])

        forbidden = self._put_part(
            finding.id,
            "part-f",
            {
                "acceptance_review_date": "2026-08-30",
                "acceptance_decision": "ACCEPTED",
            },
            conductor,
        )
        allowed = self._put_part(
            finding.id,
            "part-f",
            {
                "certificates_at_risk": ["DOC", "SMC"],
                "acceptance_review_date": "2026-08-30",
                "acceptance_rca_adequacy_text": "RCA is adequate for the sampled condition.",
                "acceptance_decision": "ACCEPTED",
                "acceptance_signer_name": "Lead Auditor",
                "acceptance_signer_at": "2026-08-30T10:00:00Z",
            },
            lead,
        )
        part_g = self._put_part(
            finding.id,
            "part-g",
            {
                "verifying_auditor_name": "Lead Auditor",
                "verifying_authority_org": "KSM",
                "verification_method": "DOCUMENT_REVIEW",
                "certificate_endorsement_type": "DOC",
                "final_closure_status": "CLOSED",
            },
            lead,
        )

        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(part_g.status_code, 200)
        finding.refresh_from_db()
        self.assertEqual(finding.certificates_at_risk, "DOC,SMC")
        nc = AuditFindingNC.objects.get(audit_finding_id=finding.id)
        self.assertEqual(nc.acceptance_decision, "ACCEPTED")
        self.assertEqual(nc.final_closure_status, "CLOSED")

    def test_not_effective_effrev_reopens_car_for_rework(self) -> None:
        _audit_detail, finding = self._create_finding()
        lead = make_user(user_id="lead-1", process_ids=[AUDIT_P_004], vessel_ids=[str(self.vessel_id)])
        car = CAR.objects.get(deficiency__id=uuid.UUID(str(finding.psc_deficiency_id)))
        car.status = CARStatus.LEAD_AUDITOR_CLOSED
        car.save(update_fields=["status"])

        response = self._put_part(
            finding.id,
            "part-e",
            {
                "effectiveness_review_date": "2026-09-30",
                "effectiveness_review_method": "OFFICE_DOC_REVIEW",
                "effectiveness_assessment_text": "The first corrective action did not prevent recurrence.",
                "effectiveness_outcome": "NOT_EFFECTIVE",
                "effectiveness_further_action_text": "The vessel must revise the corrective action plan and submit fresh evidence for Lead Auditor review.",
                "effectiveness_signer_name": "Lead Auditor",
                "effectiveness_signer_at": "2026-09-30T10:00:00Z",
            },
            lead,
        )

        self.assertEqual(response.status_code, 200)
        car.refresh_from_db()
        self.assertEqual(car.status, CARStatus.PENDING_MASTER_REVIEW)
        self.assertEqual(car.last_action, WorkflowAction.REQUEST_REWORK)

    def test_effectiveness_overdue_job_marks_incomplete_reviews_after_expiry(self) -> None:
        _audit_detail, finding = self._create_finding()
        nc = AuditFindingNC.objects.create(
            audit_finding_id=finding.id,
            effectiveness_review_date=date(2026, 8, 1),
            created_by="lead-1",
        )

        updated = mark_effectiveness_reviews_overdue(today=date(2026, 10, 1))

        self.assertEqual(updated, 1)
        nc.refresh_from_db()
        self.assertTrue(nc.effectiveness_overdue)

    def test_office_nc_rejects_vessel_certificate_at_risk(self) -> None:
        _audit_detail, finding = self._create_finding(auditee_type="OFFICE_DEPT")
        lead = make_user(process_ids=[AUDIT_P_004])

        response = self._put_part(
            finding.id,
            "part-f",
            {
                "certificates_at_risk": ["SMC"],
                "acceptance_decision": "ACCEPTED",
            },
            lead,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "AUDIT_NC_CLOSURE_VALIDATION")
        finding.refresh_from_db()
        self.assertEqual(finding.certificates_at_risk, "DOC")

    def test_nc_endpoint_rejects_observation_finding(self) -> None:
        _audit_detail, finding = self._create_finding(finding_type="OBSERVATION")
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._get_nc(finding.id, user)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "NOT_NC_FINDING")
        self.assertEqual(AuditFindingNC.objects.count(), 0)


if __name__ == "__main__":
    unittest.main()
