from __future__ import annotations

from datetime import date, datetime, time
from io import BytesIO
import json
import os
from types import SimpleNamespace
import unittest
import uuid

import django
from django.apps import apps
from django.db import connection
from django.utils import timezone
from pypdf import PdfReader


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-pdf-test-secret-key-1234567890",
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

from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402

from apps.accounts.models import RoleCodes  # noqa: E402
from apps.car.models import ActivityHistory  # noqa: E402
from apps.inspection.audit.models import (  # noqa: E402
    AuditAreaSummary,
    AuditDetail,
    AuditFinding,
    AuditFindingClause,
    AuditFindingNC,
    AuditFindingOBS,
    AuditMeetingAttendee,
    AuditPdfGeneration,
    AuditScheduleBlock,
    AuditStandard,
    AuditTeamMember,
    MasterAuditArea,
    MasterAuditPlan,
)
from apps.inspection.audit.pdf import (  # noqa: E402
    generate_audit_nc_pdf,
    generate_audit_obs_pdf,
    generate_audit_plan_pdf,
    generate_audit_report_pdf,
)
from apps.inspection.audit.views import (  # noqa: E402
    AuditFindingNcPdfView,
    AuditFindingObsPdfView,
    AuditPlanPdfView,
    AuditReportPdfView,
)
from apps.inspection.deficiency_models import CAR, Deficiency  # noqa: E402
from apps.inspection.models import Inspection  # noqa: E402


SCHEMA_MODELS = [
    Inspection,
    CAR,
    Deficiency,
    ActivityHistory,
    MasterAuditPlan,
    AuditDetail,
    AuditStandard,
    AuditTeamMember,
    AuditMeetingAttendee,
    AuditScheduleBlock,
    MasterAuditArea,
    AuditAreaSummary,
    AuditFinding,
    AuditFindingClause,
    AuditFindingNC,
    AuditFindingOBS,
    AuditPdfGeneration,
]


def make_user(
    *,
    role: str = RoleCodes.OFFICE_SSQE,
    user_type: str = "OFFICE",
    user_id: str = "auditor-1",
    vessel_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        process_ids=["AUDIT_P_001"],
        vessel_ids=vessel_ids or [],
        display_name="Audit User",
        username="audit_user",
        is_authenticated=True,
    )


class AuditPdfGeneratorTests(unittest.TestCase):
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
        self.factory = APIRequestFactory()
        self.vessel_id = uuid.uuid4()
        self.plan = MasterAuditPlan.objects.create(
            target_vessel_id=self.vessel_id,
            audit_classification="INTERNAL",
            audit_standards_csv="ISM,ISPS,MLC,EMS",
            planned_window_start=date(2026, 7, 1),
            planned_window_end=date(2026, 8, 31),
            is_additional=False,
            status="PLANNED",
            created_by="planner",
        )
        self.inspection = Inspection.objects.create(
            vessel_id=self.vessel_id,
            inspection_type="AUDIT",
            inspection_date=date(2026, 7, 29),
            port_place="Singapore",
            country="Singapore",
            inspector_name="Lead Auditor",
            report_reference="F602-2026-001",
            created_by="auditor-1",
        )
        self.audit_detail = AuditDetail.objects.create(
            psc_inspection_id=self.inspection.id.hex,
            vessel_id=self.vessel_id.hex,
            audit_classification="INTERNAL",
            auditee_type="VESSEL",
            audit_subtype="ANNUAL_INTERNAL",
            lead_auditor_name="Lead Auditor",
            lead_auditor_designation="Marine Auditor",
            lead_auditor_company="KSM",
            lead_auditor_qual="ISO 19011",
            lead_auditor_user_id="lead-1",
            pic_user_id_resolved="pic-1",
            trigger_reason="SCHEDULED",
            audit_plan_id=self.plan.id,
            audit_start_date=date(2026, 7, 29),
            audit_end_date=date(2026, 7, 30),
            opening_meeting_at=timezone.make_aware(datetime(2026, 7, 29, 9, 0)),
            closing_meeting_at=timezone.make_aware(datetime(2026, 7, 30, 16, 0)),
            audit_scope="Internal audit scope covering ISM and ISPS.",
            terms_of_reference="Verify vessel SMS implementation against KSM SSQE Manual.",
            audit_summary="A" * 120,
            equipment_tested="Emergency generator, fire pump",
            prev_internal_ca_verified="YES",
            prev_external_ca_verified="NO",
            status="IN_PROGRESS",
            created_by="auditor-1",
        )
        for index, standard_code in enumerate(("ISM", "ISPS", "MLC", "EMS"), start=1):
            AuditStandard.objects.create(
                audit_detail_id=self.audit_detail.id,
                standard_code=standard_code,
                sequence_no=index,
            )
        AuditTeamMember.objects.create(
            audit_detail_id=self.audit_detail.id,
            member_name="Co Auditor",
            member_designation="SEQ Officer",
            member_company="KSM",
            member_role="CO_AUDITOR",
            sequence_no=1,
        )
        AuditScheduleBlock.objects.create(
            audit_detail_id=self.audit_detail.id,
            block_date=date(2026, 7, 29),
            time_from=time(9, 0),
            time_to=time(10, 30),
            activity="Opening meeting and document review",
            sequence_no=1,
        )
        AuditMeetingAttendee.objects.create(
            audit_detail_id=self.audit_detail.id,
            attendee_name="Master Name",
            attendee_rank="Master",
            opening_present=True,
            closing_present=True,
            sequence_no=1,
        )
        for index in range(1, 15):
            area = MasterAuditArea.objects.create(
                area_code=f"AREA_{index:02d}",
                display_name=f"Area {index:02d}",
                is_vessel_only=index > 8,
                sequence_no=index,
            )
            AuditAreaSummary.objects.create(
                audit_detail_id=self.audit_detail.id,
                area_code=area.area_code,
                status="N_A" if index == 14 else "SATISFACTORY",
                remarks=f"Area {index:02d} checked",
            )
        self.nc_finding = self._create_finding(
            finding_type="NC",
            nc_category="MINOR_NC",
            car_number="AUDIT-2026-001",
            description="NC finding requiring corrective action.",
            objective_evidence="Objective evidence from engine room record.",
        )
        self.obs_finding = self._create_finding(
            finding_type="OBSERVATION",
            observation_category="OFI",
            car_number="AUDIT-2026-002",
            description="Observation for improvement.",
            objective_evidence="Observation evidence from bridge log.",
        )

    def test_generates_f601_a4_portrait_audit_plan_pdf(self) -> None:
        result = generate_audit_plan_pdf(self.audit_detail)
        reader, text = self._read_pdf(result.content)

        self.assertTrue(result.content.startswith(b"%PDF"))
        self.assertEqual(len(reader.pages), 1)
        self.assert_a4_portrait(reader.pages[0])
        self.assertIn("F 601 - Audit Plan", text)
        self.assertIn("Audit Plan Time Blocks", text)
        self.assertIn("Opening meeting and document review", text)
        self.assertIn("SMS Filing Ref", text)
        self.assertIn("A-2", text)
        self.assertIn("DRAFT", text)
        self.assertIn("QR F601 v1 hash", text)

    def test_generates_f602_a4_portrait_internal_audit_report_pdf(self) -> None:
        result = generate_audit_report_pdf(self.audit_detail)
        reader, text = self._read_pdf(result.content)

        self.assertTrue(result.content.startswith(b"%PDF"))
        self.assertGreaterEqual(len(reader.pages), 1)
        self.assert_a4_portrait(reader.pages[0])
        self.assertIn("F 602 - Internal Audit Report", text)
        self.assertIn("14-Area Inspection Summary", text)
        self.assertIn("Audit Result", text)
        self.assertIn("NCs Raised", text)
        self.assertIn("Observations Raised", text)
        self.assertIn("N/A", text)
        self.assertIn("DRAFT", text)
        self.assertIn("QR F602 v1 hash", text)

    def test_generates_ksm_nc_two_page_pdf(self) -> None:
        result = generate_audit_nc_pdf(self.nc_finding)
        reader, text = self._read_pdf(result.content)

        self.assertTrue(result.content.startswith(b"%PDF"))
        self.assertEqual(len(reader.pages), 2)
        self.assert_a4_portrait(reader.pages[0])
        self.assertIn("KSM-F-NC-001 - Non-Conformity Closure Form", text)
        self.assertIn("Part A - NC Details", text)
        self.assertIn("Part G - Auditor Verification & Final Closure", text)
        self.assertIn("AUDIT-2026-001", text)
        self.assertIn("A-9", text)
        self.assertNotIn("DRAFT", text)
        self.assertIn("QR KSM_F_NC_001 v1 hash", text)

    def test_generates_ksm_obs_one_page_pdf(self) -> None:
        result = generate_audit_obs_pdf(self.obs_finding)
        reader, text = self._read_pdf(result.content)

        self.assertTrue(result.content.startswith(b"%PDF"))
        self.assertEqual(len(reader.pages), 1)
        self.assert_a4_portrait(reader.pages[0])
        self.assertIn("KSM-F-OBS-001 - Observation Closure Form", text)
        self.assertIn("Part A - Observation Details", text)
        self.assertIn("Part D - Auditor Verification & Closure Confirmation", text)
        self.assertIn("AUDIT-2026-002", text)
        self.assertIn("A-28", text)
        self.assertNotIn("DRAFT", text)
        self.assertIn("QR KSM_F_OBS_001 v1 hash", text)

    def test_draft_watermark_removed_for_submitted_audit_level_pdf(self) -> None:
        self.audit_detail.status = "SUBMITTED"
        self.audit_detail.save(update_fields=["status"])

        result = generate_audit_plan_pdf(self.audit_detail)
        _reader, text = self._read_pdf(result.content)

        self.assertNotIn("DRAFT", text)

    def test_nc_and_obs_draft_watermark_follow_closure_state(self) -> None:
        AuditFindingNC.objects.filter(audit_finding_id=self.nc_finding.id).update(final_closure_status="PIC_REVIEW")
        AuditFindingOBS.objects.filter(audit_finding_id=self.obs_finding.id).update(closure_status="DRAFT")

        nc_result = generate_audit_nc_pdf(self.nc_finding)
        obs_result = generate_audit_obs_pdf(self.obs_finding)
        _nc_reader, nc_text = self._read_pdf(nc_result.content)
        _obs_reader, obs_text = self._read_pdf(obs_result.content)

        self.assertIn("DRAFT", nc_text)
        self.assertIn("DRAFT", obs_text)

    def test_additional_audit_banner_renders_on_f601_and_f602(self) -> None:
        self.plan.is_additional = True
        self.plan.trigger_event_type = "PSC_FOLLOWUP"
        self.plan.additional_reason = "Additional audit authorised after PSC follow-up evidence." * 2
        self.plan.save(update_fields=["is_additional", "trigger_event_type", "additional_reason"])

        f601 = generate_audit_plan_pdf(self.audit_detail)
        f602 = generate_audit_report_pdf(self.audit_detail)
        _reader_601, text_601 = self._read_pdf(f601.content)
        _reader_602, text_602 = self._read_pdf(f602.content)

        self.assertIn("ADDITIONAL AUDIT - DPA AUTHORISED", text_601)
        self.assertIn("PSC_FOLLOWUP", text_601)
        self.assertIn("ADDITIONAL AUDIT - DPA AUTHORISED", text_602)
        self.assertIn("PSC_FOLLOWUP", text_602)

    def test_pdf_generation_record_versions_hash_and_qr_payload(self) -> None:
        generate_audit_plan_pdf(self.audit_detail, generated_by="generator-user")
        generate_audit_plan_pdf(self.audit_detail, generated_by="generator-user")

        records = list(
            AuditPdfGeneration.objects.filter(
                audit_detail_id=self.audit_detail.id,
                audit_finding_id__isnull=True,
                pdf_kind="F601",
            ).order_by("pdf_version")
        )
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].pdf_version, 1)
        self.assertTrue(records[0].is_superseded)
        self.assertEqual(records[1].pdf_version, 2)
        self.assertFalse(records[1].is_superseded)
        self.assertEqual(records[1].generated_by, "generator-user")
        self.assertEqual(len(records[1].content_hash), 64)
        payload = json.loads(records[1].qr_payload)
        self.assertEqual(payload["audit_detail_id"], str(self.audit_detail.id))
        self.assertIsNone(payload["finding_id"])
        self.assertEqual(payload["pdf_kind"], "F601")
        self.assertEqual(payload["pdf_version"], 2)
        self.assertEqual(payload["content_hash"], records[1].content_hash)

    def test_finding_pdf_generation_payload_includes_finding_id(self) -> None:
        generate_audit_nc_pdf(self.nc_finding)

        record = AuditPdfGeneration.objects.get(
            audit_detail_id=self.audit_detail.id,
            audit_finding_id=self.nc_finding.id,
            pdf_kind="KSM_F_NC_001",
        )
        payload = json.loads(record.qr_payload)

        self.assertEqual(payload["finding_id"], str(self.nc_finding.id))
        self.assertEqual(payload["audit_detail_id"], str(self.audit_detail.id))

    def test_pdf_views_serve_documented_endpoints(self) -> None:
        user = make_user(vessel_ids=[self.vessel_id.hex])
        cases = [
            (
                AuditPlanPdfView.as_view(),
                f"/api/audit/audits/{self.audit_detail.id}/pdf/f601/",
                {"id": self.audit_detail.id},
                "F601_AuditPlan_",
            ),
            (
                AuditReportPdfView.as_view(),
                f"/api/audit/audits/{self.audit_detail.id}/pdf/f602/",
                {"id": self.audit_detail.id},
                "F602_AuditReport_",
            ),
            (
                AuditFindingNcPdfView.as_view(),
                f"/api/audit/findings/{self.nc_finding.id}/pdf/nc/",
                {"id": self.nc_finding.id},
                "KSM_F_NC_001_",
            ),
            (
                AuditFindingObsPdfView.as_view(),
                f"/api/audit/findings/{self.obs_finding.id}/pdf/obs/",
                {"id": self.obs_finding.id},
                "KSM_F_OBS_001_",
            ),
        ]
        for view, path, kwargs, filename_prefix in cases:
            request = self.factory.get(path)
            force_authenticate(request, user=user)
            response = view(request, **kwargs)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "application/pdf")
            self.assertIn(filename_prefix, response["Content-Disposition"])
            self.assertTrue(response.content.startswith(b"%PDF"))

    def _create_finding(
        self,
        *,
        finding_type: str,
        car_number: str,
        description: str,
        objective_evidence: str,
        nc_category: str | None = None,
        observation_category: str | None = None,
    ) -> AuditFinding:
        car = CAR.objects.create(car_number=car_number, status="IN_PROGRESS", created_by="auditor-1")
        deficiency = Deficiency.objects.create(
            inspection=self.inspection,
            def_code_id="10101",
            def_code="10101",
            description=description,
            target_date=date(2026, 8, 29),
            car=car,
            created_by="auditor-1",
        )
        finding = AuditFinding.objects.create(
            psc_deficiency_id=deficiency.id.hex,
            audit_detail_id=self.audit_detail.id,
            audit_classification="INTERNAL",
            finding_type=finding_type,
            nc_category=nc_category,
            observation_category=observation_category,
            standard_code="ISM",
            rule_book_type="ISM",
            clause_ref_text="ISM 10.2",
            objective_evidence=objective_evidence,
            description=description,
            priority="MEDIUM",
            original_due_date=date(2026, 8, 29),
            certificates_at_risk="DOC" if finding_type == "NC" else None,
            created_by="auditor-1",
        )
        AuditFindingClause.objects.create(
            audit_finding_id=finding.id,
            rule_book_type="ISM",
            clause_ref_text="ISM 10.2",
            is_primary=True,
            created_by="auditor-1",
        )
        if finding_type == "NC":
            AuditFindingNC.objects.create(
                audit_finding_id=finding.id,
                immediate_action_text="Immediate containment completed.",
                immediate_action_completed_at=date(2026, 7, 30),
                master_immediate_sign_name="Master Name",
                rca_method="5-WHY",
                problem_statement="Procedure was not followed.",
                why_1="Why one",
                root_cause_categories="Procedure",
                root_cause_summary="Root cause summary with sufficient detail for the PDF.",
                corrective_action_text="Corrective action text.",
                target_completion_date=date(2026, 8, 20),
                preventive_action_text="Preventive action text.",
                effectiveness_review_date=date(2026, 9, 15),
                effectiveness_review_method="REVIEW",
                effectiveness_outcome="EFFECTIVE",
                acceptance_signer_name="Lead Auditor",
                acceptance_decision="ACCEPTED",
                verifying_auditor_name="Lead Auditor",
                verifying_authority_org="KSM",
                verification_method="DOCUMENT_REVIEW",
                final_closure_status="LEAD_AUDITOR_CLOSED",
                created_by="auditor-1",
            )
        else:
            AuditFindingOBS.objects.create(
                audit_finding_id=finding.id,
                responded_by_name="Master Name",
                responded_by_rank="Master",
                target_closure_date=date(2026, 8, 10),
                immediate_action_text="Observation immediate action.",
                root_cause_text="Observation root cause.",
                corrective_action_text="Observation corrective action.",
                preventive_action_text="Observation preventive action.",
                actual_closure_date=date(2026, 8, 8),
                master_sign_name="Master Name",
                acceptance_signer_name="DPA Name",
                acceptance_decision="ACCEPTED",
                verifying_auditor_name="Lead Auditor",
                verifying_authority_org="KSM",
                verification_method="DOCUMENT_REVIEW",
                closure_status="MASTER_CLOSED",
                created_by="auditor-1",
            )
        return finding

    def _read_pdf(self, content: bytes):
        reader = PdfReader(BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return reader, text

    def assert_a4_portrait(self, page) -> None:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        self.assertLess(width, height)
        self.assertAlmostEqual(width, 595.27, delta=1.0)
        self.assertAlmostEqual(height, 841.89, delta=1.0)
