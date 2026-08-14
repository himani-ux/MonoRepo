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
            SECRET_KEY="audit-detail-test-secret-key-1234567890",
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
    AuditAreaSummary,
    AuditDetail,
    AuditFinding,
    AuditFindingClause,
    AuditMeetingAttendee,
    AuditStandard,
    AuditTeamMember,
    MasterAuditArea,
    MasterIsmClause,
)
from apps.inspection.audit.permissions import AUDIT_P_001, AUDIT_P_002, AUDIT_P_003, AUDIT_P_007, AUDIT_P_017  # noqa: E402
from apps.inspection.audit.views import (  # noqa: E402
    AuditAcknowledgeView,
    AuditDetailView,
    AuditFindingCreateView,
    AuditFindingIssueCircularView,
    AuditScorecardView,
    AuditSubmitView,
)
from apps.inspection.deficiency_models import CAR, Deficiency  # noqa: E402
from apps.inspection.models import Inspection  # noqa: E402
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402


SCHEMA_MODELS = [
    Inspection,
    CAR,
    Deficiency,
    ActivityHistory,
    AuditDetail,
    AuditStandard,
    AuditTeamMember,
    AuditMeetingAttendee,
    AuditFinding,
    AuditFindingClause,
    MasterAuditArea,
    MasterIsmClause,
    AuditAreaSummary,
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


class AuditDetailApiTests(unittest.TestCase):
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
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS msc_data")
            cursor.execute(
                """
                CREATE TABLE msc_data (
                    id varchar(36) NOT NULL PRIMARY KEY,
                    sr_no varchar(255) NULL,
                    title text NULL,
                    office_instructions text NULL,
                    hashtags varchar(255) NULL,
                    created_by varchar(255) NULL,
                    created_at datetime NULL,
                    publish_status integer NOT NULL,
                    is_active bool NULL,
                    is_deleted bool NULL,
                    vessel_id text NULL,
                    category varchar(255) NULL
                )
                """
            )

    @classmethod
    def tearDownClass(cls) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS msc_data")
        with connection.schema_editor() as schema_editor:
            for model in reversed(SCHEMA_MODELS):
                schema_editor.delete_model(model)
        super().tearDownClass()

    def setUp(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM msc_data")
            for model in reversed(SCHEMA_MODELS):
                cursor.execute(f"DELETE FROM {model._meta.db_table}")
        self.vessel_code_lookup = patch("apps.inspection.deficiency_models._lookup_vessel_code", return_value="TST")
        self.vessel_code_lookup.start()
        self.addCleanup(self.vessel_code_lookup.stop)
        self.factory = APIRequestFactory()
        self.vessel_id = uuid.uuid4()
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
            trigger_reason="SCHEDULED",
            audit_start_date=date(2026, 7, 29),
            audit_scope="Initial audit scope",
            terms_of_reference="Initial terms",
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
            member_role="CO_AUDITOR",
        )
        AuditMeetingAttendee.objects.create(
            audit_detail_id=self.audit_detail.id,
            attendee_name="Master Name",
            attendee_rank="Master",
            opening_present=True,
            closing_present=False,
        )
        for index in range(1, 15):
            MasterAuditArea.objects.create(
                area_code=f"AREA_{index:02d}",
                display_name=f"Area {index:02d}",
                is_vessel_only=index > 8,
                sequence_no=index,
            )
        self.ism_clause = MasterIsmClause.objects.create(
            clause_no="10.2",
            clause_text="The Company should ensure that non-conformities are reported.",
            section_no="10",
            code_version="ISM 2018",
            created_by="seed",
        )

    def _get_detail(self, user):
        request = self.factory.get(f"/api/audit/audits/{self.audit_detail.id}/")
        force_authenticate(request, user=user)
        return AuditDetailView.as_view()(request, id=self.audit_detail.id)

    def _patch_detail(self, payload, user):
        request = self.factory.patch(f"/api/audit/audits/{self.audit_detail.id}/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditDetailView.as_view()(request, id=self.audit_detail.id)

    def _put_scorecard(self, payload, user):
        request = self.factory.put(f"/api/audit/audits/{self.audit_detail.id}/scorecard/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditScorecardView.as_view()(request, id=self.audit_detail.id)

    def _post_finding(self, payload, user):
        request = self.factory.post(f"/api/audit/audits/{self.audit_detail.id}/findings/", payload, format="json")
        force_authenticate(request, user=user)
        return AuditFindingCreateView.as_view()(request, id=self.audit_detail.id)

    def _post_issue_circular(self, finding_id, user):
        request = self.factory.post(f"/api/audit/findings/{finding_id}/issue-circular/", {}, format="json")
        force_authenticate(request, user=user)
        return AuditFindingIssueCircularView.as_view()(request, id=finding_id)

    def _submit(self, user):
        request = self.factory.post(f"/api/audit/audits/{self.audit_detail.id}/submit/", {}, format="json")
        force_authenticate(request, user=user)
        return AuditSubmitView.as_view()(request, id=self.audit_detail.id)

    def _acknowledge(self, user):
        request = self.factory.post(f"/api/audit/audits/{self.audit_detail.id}/acknowledge/", {}, format="json")
        force_authenticate(request, user=user)
        return AuditAcknowledgeView.as_view()(request, id=self.audit_detail.id)

    def _make_submit_ready(self) -> None:
        self.audit_detail.opening_meeting_at = "2026-07-29T09:00:00+05:30"
        self.audit_detail.closing_meeting_at = "2026-07-29T17:00:00+05:30"
        self.audit_detail.audit_summary = "A" * 100
        self.audit_detail.equipment_tested = "Emergency generator\nFire pump"
        self.audit_detail.save(
            update_fields=[
                "opening_meeting_at",
                "closing_meeting_at",
                "audit_summary",
                "equipment_tested",
            ]
        )
        AuditMeetingAttendee.objects.create(
            audit_detail_id=self.audit_detail.id,
            attendee_name="Chief Engineer",
            attendee_rank="CE",
            opening_present=False,
            closing_present=True,
        )
        for index in range(1, 15):
            AuditAreaSummary.objects.create(
                audit_detail_id=self.audit_detail.id,
                area_code=f"AREA_{index:02d}",
                status="N_A" if index > 8 else "SATISFACTORY",
                remarks="Checked",
                created_by="auditor-1",
            )

    def test_get_detail_returns_header_scorecard_and_finding_counts(self) -> None:
        car = CAR.objects.create(car_number="AUDIT-2026-001", status="ALLOTTED")
        deficiency = Deficiency.objects.create(
            inspection=self.inspection,
            def_code_id="10101",
            def_code="10101",
            description="Fire door issue",
            car=car,
            created_by="auditor-1",
        )
        AuditFinding.objects.create(
            audit_detail_id=self.audit_detail.id,
            psc_deficiency_id=deficiency.id.hex,
            audit_classification="INTERNAL",
            finding_type="NC",
            nc_category="MINOR_NC",
            description="Fire door issue",
            created_by="auditor-1",
        )
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._get_detail(user)

        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["id"], str(self.audit_detail.id))
        self.assertEqual(data["inspection"]["port_place"], "Singapore")
        self.assertEqual(data["standards"], ["ISM", "ISPS", "MLC", "EMS"])
        self.assertEqual(data["counts"]["nc"], 1)
        self.assertEqual(data["counts"]["observations"], 0)
        self.assertEqual(len(data["scorecard"]), 14)
        self.assertEqual(data["scorecard"][0]["area_code"], "AREA_01")
        self.assertEqual(data["findings"][0]["car_number"], "AUDIT-2026-001")

    def test_patch_detail_updates_editable_summary_and_equipment_fields(self) -> None:
        user = make_user(process_ids=[AUDIT_P_002, AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._patch_detail(
            {
                "audit_summary": "Completed internal audit summary for Step 4.2 shell.",
                "equipment_tested": "Emergency generator\nFire pump",
                "audit_scope": "Updated scope",
                "terms_of_reference": "Updated terms",
                "prev_internal_ca_verified": "YES",
                "prev_external_ca_verified": "NA",
            },
            user,
        )

        self.assertEqual(response.status_code, 200)
        self.audit_detail.refresh_from_db()
        self.assertEqual(self.audit_detail.equipment_tested, "Emergency generator\nFire pump")
        self.assertEqual(self.audit_detail.audit_scope, "Updated scope")
        self.assertEqual(response.data["data"]["audit_summary"], "Completed internal audit summary for Step 4.2 shell.")

    def test_put_scorecard_replaces_rows_by_area_code(self) -> None:
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])
        payload = {
            "rows": [
                {"area_code": "AREA_01", "status": "SATISFACTORY", "remarks": "Good"},
                {"area_code": "AREA_09", "status": "N_A", "remarks": "Office-only equivalent"},
            ]
        }

        first = self._put_scorecard(payload, user)
        second = self._put_scorecard(
            {"rows": [{"area_code": "AREA_01", "status": "NC_RAISED", "remarks": "NC raised"}]},
            user,
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(AuditAreaSummary.objects.count(), 2)
        self.assertEqual(AuditAreaSummary.objects.get(area_code="AREA_01").status, "NC_RAISED")
        self.assertEqual(AuditAreaSummary.objects.get(area_code="AREA_09").status, "N_A")

    def test_detail_requires_audit_scope_permission(self) -> None:
        user = make_user(process_ids=[])

        response = self._get_detail(user)

        self.assertEqual(response.status_code, 403)

    def test_in_scope_create_gate_user_can_read_but_not_patch_detail(self) -> None:
        user = make_user(process_ids=[AUDIT_P_001], vessel_ids=[str(self.vessel_id)])

        get_response = self._get_detail(user)
        patch_response = self._patch_detail({"audit_summary": "Not allowed"}, user)

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(patch_response.status_code, 403)

    def test_scorecard_rejects_unknown_area_code(self) -> None:
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._put_scorecard({"rows": [{"area_code": "UNKNOWN", "status": "SATISFACTORY"}]}, user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("area_code", str(response.data))

    def test_post_finding_creates_nc_car_and_primary_clause(self) -> None:
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])
        response = self._post_finding(
            {
                "finding_type": "NC",
                "nc_category": "MINOR_NC",
                "standard_code": "ISM",
                "description": "Fire door self-closing device was not functioning.",
                "objective_evidence": "Observed during accommodation walk.",
                "def_code_id": "10101",
                "clauses": [
                    {
                        "rule_book_type": "ISM",
                        "rule_clause_id": str(self.ism_clause.id),
                        "is_primary": True,
                    }
                ],
            },
            user,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(AuditFinding.objects.count(), 1)
        self.assertEqual(AuditFindingClause.objects.count(), 1)
        self.assertEqual(CAR.objects.count(), 1)
        data = response.data["data"]
        self.assertEqual(data["finding_type"], "NC")
        self.assertEqual(data["rule_book_type"], "ISM")
        self.assertEqual(data["clause_ref_text"], "ISM 10.2")
        self.assertTrue(data["car_number"].startswith("TST-PSC-2026-"))

    def test_post_finding_rejects_after_report_finalized_with_no_car_side_effect(self) -> None:
        self.audit_detail.status = "REPORT_FINALIZED"
        self.audit_detail.save(update_fields=["status"])
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._post_finding(
            {
                "finding_type": "NC",
                "nc_category": "MINOR_NC",
                "standard_code": "ISM",
                "description": "Late finding should not be accepted.",
                "objective_evidence": "Observed after finalization.",
                "def_code_id": "10101",
                "clauses": [
                    {
                        "rule_book_type": "ISM",
                        "rule_clause_id": str(self.ism_clause.id),
                        "is_primary": True,
                    }
                ],
            },
            user,
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"], "AUDIT_FINDING_STATE")
        self.assertEqual(AuditFinding.objects.count(), 0)
        self.assertEqual(CAR.objects.count(), 0)

    def test_post_finding_auto_critical_for_major_nc_suspended_certificate_impact(self) -> None:
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._post_finding(
            {
                "finding_type": "NC",
                "nc_category": "MAJOR_NC",
                "standard_code": "ISM",
                "description": "Certificate-threatening NC.",
                "objective_evidence": "Report records suspension risk.",
                "def_code_id": "10101",
                "priority": "LOW",
                "certificate_impact": "SUSPENDED",
                "clauses": [
                    {
                        "rule_book_type": "ISM",
                        "rule_clause_id": str(self.ism_clause.id),
                        "is_primary": True,
                    }
                ],
            },
            user,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["priority"], "CRITICAL")
        self.assertEqual(AuditFinding.objects.get().priority, "CRITICAL")

    def test_post_finding_rejects_fleetwide_observation(self) -> None:
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._post_finding(
            {
                "finding_type": "OBSERVATION",
                "observation_category": "OFI",
                "description": "Observation should not carry fleetwide NC relevance.",
                "objective_evidence": "Interview note.",
                "def_code_id": "10101",
                "is_fleetwide_relevance": True,
                "clauses": [
                    {
                        "rule_book_type": "OTHER",
                        "clause_ref_text": "Bridge team improvement note",
                        "is_primary": True,
                    }
                ],
            },
            user,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "AUDIT_FINDING_VALIDATION")
        self.assertEqual(AuditFinding.objects.count(), 0)
        self.assertEqual(CAR.objects.count(), 0)

    def test_post_finding_rejects_other_clause_without_bounded_text(self) -> None:
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._post_finding(
            {
                "finding_type": "OBSERVATION",
                "observation_category": "OFI",
                "description": "Bridge checklist could be clearer.",
                "objective_evidence": "Observed during interview.",
                "def_code_id": "10101",
                "clauses": [{"rule_book_type": "OTHER", "clause_ref_text": "bad", "is_primary": True}],
            },
            user,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "AUDIT_FINDING_VALIDATION")
        self.assertEqual(AuditFinding.objects.count(), 0)
        self.assertEqual(CAR.objects.count(), 0)

    def test_submit_blocks_when_finding_has_no_objective_evidence(self) -> None:
        self._make_submit_ready()
        car = CAR.objects.create(car_number="AUDIT-2026-001", status="ALLOTTED")
        deficiency = Deficiency.objects.create(
            inspection=self.inspection,
            def_code_id="10101",
            def_code="10101",
            description="Fire door issue",
            car=car,
            created_by="auditor-1",
        )
        AuditFinding.objects.create(
            audit_detail_id=self.audit_detail.id,
            psc_deficiency_id=deficiency.id.hex,
            audit_classification="INTERNAL",
            finding_type="NC",
            nc_category="MINOR_NC",
            description="Fire door issue",
            objective_evidence="",
            created_by="auditor-1",
        )
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._submit(user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("findings", response.data["gates"])
        self.assertIn("objective_evidence", response.data["gates"]["findings"])

    def test_issue_circular_creates_draft_and_links_fleetwide_nc(self) -> None:
        conductor = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])
        create_response = self._post_finding(
            {
                "finding_type": "NC",
                "nc_category": "MAJOR_NC",
                "standard_code": "ISM",
                "description": "Fleetwide NC requires circular issue.",
                "objective_evidence": "Same condition sampled across sister vessels.",
                "def_code_id": "10101",
                "priority": "HIGH",
                "is_fleetwide_relevance": True,
                "clauses": [
                    {
                        "rule_book_type": "ISM",
                        "rule_clause_id": str(self.ism_clause.id),
                        "is_primary": True,
                    }
                ],
            },
            conductor,
        )
        finding_id = create_response.data["data"]["id"]
        dpa = make_user(role="DPA", process_ids=[AUDIT_P_007], vessel_ids=[str(self.vessel_id)])

        response = self._post_issue_circular(finding_id, dpa)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["status"], "DRAFT_CREATED")
        circular_id = response.data["data"]["circular_id"]
        self.assertEqual(str(AuditFinding.objects.get(id=finding_id).linked_circular_id), circular_id)
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM msc_data WHERE id = %s", [circular_id])
            self.assertEqual(cursor.fetchone()[0], 1)

        second_response = self._post_issue_circular(finding_id, dpa)
        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(second_response.data["data"]["status"], "ALREADY_LINKED")
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM msc_data")
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_issue_circular_requires_fleetwide_nc(self) -> None:
        conductor = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])
        create_response = self._post_finding(
            {
                "finding_type": "NC",
                "nc_category": "MINOR_NC",
                "standard_code": "ISM",
                "description": "Non-fleetwide NC.",
                "objective_evidence": "Single sampled condition.",
                "def_code_id": "10101",
                "clauses": [
                    {
                        "rule_book_type": "ISM",
                        "rule_clause_id": str(self.ism_clause.id),
                        "is_primary": True,
                    }
                ],
            },
            conductor,
        )
        dpa = make_user(role="DPA", process_ids=[AUDIT_P_007], vessel_ids=[str(self.vessel_id)])

        response = self._post_issue_circular(create_response.data["data"]["id"], dpa)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "AUDIT_CIRCULAR_LINK_VALIDATION")
        self.assertIsNone(AuditFinding.objects.get().linked_circular_id)

    def test_submit_blocks_with_structured_gate_failures(self) -> None:
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._submit(user)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "SUBMIT_GATES_FAILED")
        self.assertIn("closing_meeting", response.data["gates"])
        self.assertIn("scorecard", response.data["gates"])
        self.assertIn("summary_equipment", response.data["gates"])
        self.audit_detail.refresh_from_db()
        self.assertEqual(self.audit_detail.status, "IN_PROGRESS")

    def test_submit_blocks_when_scorecard_row_is_blank(self) -> None:
        self._make_submit_ready()
        AuditAreaSummary.objects.filter(area_code="AREA_14").update(status=None)
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._submit(user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("scorecard", response.data["gates"])
        self.audit_detail.refresh_from_db()
        self.assertEqual(self.audit_detail.status, "IN_PROGRESS")

    def test_submit_blocks_when_summary_is_too_short_or_equipment_empty(self) -> None:
        self._make_submit_ready()
        self.audit_detail.audit_summary = "Too short"
        self.audit_detail.equipment_tested = "   "
        self.audit_detail.save(update_fields=["audit_summary", "equipment_tested"])
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._submit(user)

        self.assertEqual(response.status_code, 400)
        self.assertIn("summary_equipment", response.data["gates"])
        self.assertIn("audit_summary", response.data["gates"]["summary_equipment"])
        self.assertIn("equipment_tested", response.data["gates"]["summary_equipment"])

    def test_submit_all_gates_pass_moves_to_report_finalized(self) -> None:
        self._make_submit_ready()
        user = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        response = self._submit(user)

        self.assertEqual(response.status_code, 200)
        self.audit_detail.refresh_from_db()
        self.assertEqual(self.audit_detail.status, "REPORT_FINALIZED")
        self.assertIsNotNone(self.audit_detail.updated_date)
        self.assertEqual(response.data["data"]["status"], "REPORT_FINALIZED")

    def test_acknowledge_requires_master_gate_and_report_finalized_status(self) -> None:
        self.audit_detail.status = "IN_PROGRESS"
        self.audit_detail.save(update_fields=["status"])
        conductor = make_user(process_ids=[AUDIT_P_003], vessel_ids=[str(self.vessel_id)])

        no_gate_response = self._acknowledge(conductor)

        self.assertEqual(no_gate_response.status_code, 403)

        master = make_user(
            role="MASTER",
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[AUDIT_P_017],
            vessel_ids=[str(self.vessel_id)],
        )
        master.vessel_id = str(self.vessel_id)
        wrong_status_response = self._acknowledge(master)

        self.assertEqual(wrong_status_response.status_code, 409)
        self.audit_detail.refresh_from_db()
        self.assertEqual(self.audit_detail.status, "IN_PROGRESS")

    def test_acknowledge_master_moves_report_finalized_to_vessel_acknowledged(self) -> None:
        self.audit_detail.status = "REPORT_FINALIZED"
        self.audit_detail.save(update_fields=["status"])
        master = make_user(
            role="MASTER",
            user_type="VESSEL",
            user_id="master-1",
            process_ids=[AUDIT_P_017],
            vessel_ids=[str(self.vessel_id)],
        )
        master.vessel_id = str(self.vessel_id)

        response = self._acknowledge(master)

        self.assertEqual(response.status_code, 200)
        self.audit_detail.refresh_from_db()
        self.assertEqual(self.audit_detail.status, "VESSEL_ACKNOWLEDGED")
        self.assertEqual(self.audit_detail.updated_by, "master-1")
        self.assertIsNotNone(self.audit_detail.updated_date)
        self.assertEqual(response.data["data"]["status"], "VESSEL_ACKNOWLEDGED")


if __name__ == "__main__":
    unittest.main()
