from __future__ import annotations

import os
import unittest
import uuid
from datetime import date
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
            SECRET_KEY="audit-obs-closure-test-secret-key-1234567890",
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
    AuditFindingOBS,
    AuditFindingSignEvent,
)
from apps.inspection.audit.permissions import AUDIT_P_003, AUDIT_P_004, AUDIT_P_008  # noqa: E402
from apps.inspection.audit.services.finding import create_audit_finding  # noqa: E402
from apps.inspection.audit.views import AuditFindingObsClosureView, AuditFindingObsPartView  # noqa: E402
from apps.inspection.deficiency_models import CAR, Deficiency  # noqa: E402
from apps.inspection.models import Inspection  # noqa: E402
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402


SCHEMA_MODELS = [
    Inspection,
    CAR,
    Deficiency,
    ActivityHistory,
    AuditDetail,
    AuditFinding,
    AuditFindingOBS,
    AuditFindingSignEvent,
]


def make_user(
    *,
    role: str = RoleCodes.OFFICE_SSQE,
    user_type: str = "OFFICE",
    user_id: str = "auditor-1",
    process_ids: list[str] | None = None,
    vessel_ids: list[str] | None = None,
    vessel_id=None,
    rank: str | None = None,
):
    return SimpleNamespace(
        id=user_id,
        role=role,
        user_type=user_type,
        process_ids=process_ids or [],
        vessel_ids=vessel_ids or [],
        vessel_id=str(vessel_id) if vessel_id else None,
        rank=rank,
        display_name="Audit User",
        username="audit_user",
        is_authenticated=True,
    )


class AuditObsClosureApiTests(unittest.TestCase):
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

    def _create_audit_detail(self):
        inspection = Inspection.objects.create(
            vessel_id=self.vessel_id,
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
            vessel_id=self.vessel_id.hex,
            audit_classification="INTERNAL",
            auditee_type="VESSEL",
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

    def _create_finding(self, *, finding_type="OBSERVATION"):
        _inspection, audit_detail = self._create_audit_detail()
        if finding_type == "NC":
            return audit_detail, create_audit_finding(
                audit_detail_id=audit_detail.id,
                finding_type="NC",
                nc_category="MINOR_NC",
                description="Audit NC for Obs rejection.",
                objective_evidence="Observed during audit.",
                def_code_id="10101",
                created_by="auditor-1",
            ).finding
        return audit_detail, create_audit_finding(
            audit_detail_id=audit_detail.id,
            finding_type="OBSERVATION",
            observation_category="OFI",
            description="Observation about a weak planned maintenance follow-up.",
            objective_evidence="Observed during audit.",
            def_code_id="10101",
            created_by="auditor-1",
        ).finding

    def _get_obs(self, finding_id, user):
        request = self.factory.get(f"/api/audit/findings/{finding_id}/obs/")
        force_authenticate(request, user=user)
        return AuditFindingObsClosureView.as_view()(request, id=finding_id)

    def _put_part(self, finding_id, part, payload, user):
        request = self.factory.put(f"/api/audit/findings/{finding_id}/obs/{part}/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditFindingObsPartView.as_view(part_name=part)(request, id=finding_id)

    def test_get_obs_creates_closure_record_and_returns_part_a(self) -> None:
        audit_detail, finding = self._create_finding()
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._get_obs(finding.id, user)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AuditFindingOBS.objects.count(), 1)
        self.assertEqual(response.data["data"]["finding_id"], str(finding.id))
        self.assertEqual(response.data["data"]["state"], "NOT_STARTED")
        self.assertEqual(response.data["data"]["part_a"]["auditor_name"], audit_detail.lead_auditor_name)
        self.assertEqual(response.data["data"]["part_a"]["observation_category"], "OFI")
        self.assertTrue(response.data["data"]["car"]["car_number"].startswith("TST-PSC-2026-"))

    def test_obs_endpoint_rejects_nc_finding(self) -> None:
        _audit_detail, finding = self._create_finding(finding_type="NC")
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._get_obs(finding.id, user)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "NOT_OBSERVATION_FINDING")
        self.assertEqual(AuditFindingOBS.objects.count(), 0)

    def test_part_b_master_sign_closes_observation_terminal(self) -> None:
        _audit_detail, finding = self._create_finding()
        master = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[AUDIT_P_008],
            vessel_id=self.vessel_id,
            rank="Master",
        )

        draft = self._put_part(
            finding.id,
            "part-b",
            {
                "responded_by_name": "Chief Officer",
                "responded_by_rank": "Chief Officer",
                "target_closure_date": "2026-08-15",
                "immediate_action_text": "Crew briefed on the observation.",
                "root_cause_text": "The checklist owner had not been clearly assigned.",
                "corrective_action_text": "Assign checklist ownership in the department meeting.",
                "preventive_action_text": "Add ownership review to monthly HOD meeting.",
            },
            master,
        )
        signed = self._put_part(
            finding.id,
            "part-b",
            {
                "responded_by_name": "Chief Officer",
                "responded_by_rank": "Chief Officer",
                "target_closure_date": "2026-08-15",
                "immediate_action_text": "Crew briefed on the observation.",
                "root_cause_text": "The checklist owner had not been clearly assigned.",
                "corrective_action_text": "Assign checklist ownership in the department meeting.",
                "preventive_action_text": "Add ownership review to monthly HOD meeting.",
                "actual_closure_date": "2026-08-10",
                "master_sign_name": "Vessel Master",
                "master_sign_at": "2026-08-10T10:00:00Z",
            },
            master,
        )

        self.assertEqual(draft.status_code, 200)
        self.assertEqual(draft.data["data"]["state"], "IN_PROGRESS")
        self.assertEqual(signed.status_code, 200)
        self.assertEqual(signed.data["data"]["state"], "MASTER_CLOSED")
        obs = AuditFindingOBS.objects.get(audit_finding_id=finding.id)
        self.assertEqual(obs.master_sign_name, "Vessel Master")
        self.assertEqual(
            AuditFindingSignEvent.objects.filter(
                audit_finding_id=finding.id,
                user_id="master-1",
                part_label="OBS_PART_B",
            ).count(),
            1,
        )

    def test_part_b_requires_master_gate_for_terminal_signature(self) -> None:
        _audit_detail, finding = self._create_finding()
        conductor = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._put_part(
            finding.id,
            "part-b",
            {
                "immediate_action_text": "Crew briefed on the observation.",
                "master_sign_name": "Not Master",
                "master_sign_at": "2026-08-10T10:00:00Z",
            },
            conductor,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(AuditFindingSignEvent.objects.count(), 0)

    def test_part_b_is_terminal_after_master_closed(self) -> None:
        _audit_detail, finding = self._create_finding()
        master = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[AUDIT_P_008],
            vessel_id=self.vessel_id,
            rank="Master",
        )
        closed = self._put_part(
            finding.id,
            "part-b",
            {
                "immediate_action_text": "Crew briefed on the observation.",
                "actual_closure_date": "2026-08-10",
                "master_sign_name": "Vessel Master",
                "master_sign_at": "2026-08-10T10:00:00Z",
            },
            master,
        )
        blocked = self._put_part(
            finding.id,
            "part-b",
            {"immediate_action_text": "Changed after Master closure."},
            master,
        )

        self.assertEqual(closed.status_code, 200)
        self.assertEqual(blocked.status_code, 400)
        self.assertIn("terminal", blocked.data["message"])

    def test_parts_c_d_are_audit_trail_only_after_master_closed(self) -> None:
        _audit_detail, finding = self._create_finding()
        master = make_user(
            role=RoleCodes.VESSEL_MASTER,
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[AUDIT_P_008],
            vessel_id=self.vessel_id,
            rank="Master",
        )
        dpa = make_user(
            role=RoleCodes.DPA,
            user_type="OFFICE",
            user_id="dpa-1",
            process_ids=[AUDIT_P_004],
            vessel_ids=[str(self.vessel_id)],
        )
        self._put_part(
            finding.id,
            "part-b",
            {
                "immediate_action_text": "Crew briefed on the observation.",
                "actual_closure_date": "2026-08-10",
                "master_sign_name": "Vessel Master",
                "master_sign_at": "2026-08-10T10:00:00Z",
            },
            master,
        )

        part_c = self._put_part(
            finding.id,
            "part-c",
            {
                "acceptance_review_date": "2026-08-12",
                "acceptance_adequacy_text": "DPA review recorded after Master terminal closure.",
                "acceptance_decision": "ACCEPTED",
                "acceptance_signer_name": "DPA",
                "acceptance_signer_at": "2026-08-12T08:00:00Z",
            },
            dpa,
        )
        part_d = self._put_part(
            finding.id,
            "part-d",
            {
                "verifying_auditor_name": "Lead Auditor",
                "verifying_authority_org": "KSM",
                "verification_method": "DOCUMENT_REVIEW",
                "auditor_remarks_text": "Auditor verification recorded without reopening workflow.",
                "closure_status": "CLOSED",
                "auditor_verification_sign_at": "2026-08-13T08:00:00Z",
            },
            dpa,
        )

        self.assertEqual(part_c.status_code, 200)
        self.assertEqual(part_c.data["data"]["state"], "MASTER_CLOSED")
        self.assertEqual(part_d.status_code, 200)
        self.assertEqual(part_d.data["data"]["state"], "MASTER_CLOSED")
        obs = AuditFindingOBS.objects.get(audit_finding_id=finding.id)
        self.assertEqual(obs.acceptance_decision, "ACCEPTED")
        self.assertEqual(obs.closure_status, "CLOSED")


if __name__ == "__main__":
    unittest.main()
