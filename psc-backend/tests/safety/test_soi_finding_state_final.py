from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
import uuid
import unittest

from tests.safety.support import bootstrap_django, recreate_scm_tables, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SafetyFieldHistory, SOIFinding
from apps.safety.services.finding_closure import FindingClosureService
from apps.safety.views.scm_soi_feed import SOIOpenFindingsVesselView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    user_id: str,
    form_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_004"] if form_ids is None else form_ids,
        process_ids=[] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


def aware(year: int, month: int, day: int, hour: int, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


class SOIFindingStateFinalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_scm_tables()
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.closure_service = FindingClosureService()
        self.open_findings_view = SOIOpenFindingsVesselView.as_view()
        self.inspection_id = self._insert_inspection()

    def test_carried_forward_finding_can_move_back_to_pending_closure(self) -> None:
        finding = self._create_finding(status=SOIFinding.Status.CARRIED_FORWARD, title="Repeated permit lapse")

        result = self.closure_service.mark_pending_closure(
            finding=finding,
            user=build_user(role_name="CO", process_ids=["SAF_P_014"], user_id="co-7"),
            typed_name="Chief Officer Seven",
            device_fingerprint="tablet-co-7",
            closure_note="Evidence pack refreshed after repeat review.",
        )

        finding.refresh_from_db()
        self.assertEqual(result["status"], "PENDING_CLOSURE")
        self.assertEqual(finding.status, SOIFinding.Status.PENDING_CLOSURE)
        self.assertIn("Evidence pack refreshed", finding.closure_note or "")

    def test_second_engineer_alternate_can_move_open_finding_to_pending_closure(self) -> None:
        finding = self._create_finding(status=SOIFinding.Status.OPEN, title="Engine room guard renewed")

        result = self.closure_service.mark_pending_closure(
            finding=finding,
            user=build_user(role_name="SECOND ENGINEER", process_ids=["SAF_P_014"], user_id="2e-7"),
            typed_name="Second Engineer Seven",
            device_fingerprint="tablet-2e-7",
            closure_note="Corrective evidence checked by alternate Safety Officer.",
        )

        finding.refresh_from_db()
        self.assertEqual(result["status"], "PENDING_CLOSURE")
        self.assertEqual(finding.status, SOIFinding.Status.PENDING_CLOSURE)
        self.assertEqual(finding.updated_by, "2e-7")

    def test_approval_records_master_approved_transition_before_close(self) -> None:
        finding = self._create_finding(status=SOIFinding.Status.OPEN, title="Drain cover rectified")
        self.closure_service.mark_pending_closure(
            finding=finding,
            user=build_user(role_name="CO", process_ids=["SAF_P_014"], user_id="co-7"),
            typed_name="Chief Officer Seven",
            device_fingerprint="tablet-co-7",
            closure_note="Ready for Master review.",
        )

        result = self.closure_service.approve_closure(
            finding=finding,
            user=build_user(role_name="MASTER", process_ids=["SAF_P_015"], user_id="master-7"),
            typed_name="Master Seven",
            device_fingerprint="bridge-console-7",
            closure_note="Verified during deck round.",
        )

        finding.refresh_from_db()
        status_rows = list(
            SafetyFieldHistory.objects.filter(
                parent_table=finding._meta.db_table,
                parent_id=finding.pk,
                field_name="status",
            ).order_by("changed_at", "id")
        )

        self.assertEqual(result["status"], "CLOSED")
        self.assertEqual(finding.status, SOIFinding.Status.CLOSED)
        expected_transitions = [
            ("OPEN", "PENDING_CLOSURE"),
            ("PENDING_CLOSURE", "MASTER_APPROVED"),
            ("MASTER_APPROVED", "CLOSED"),
        ]
        actual_transitions = [(row.old_value, row.new_value) for row in status_rows]
        self.assertEqual(
            sorted(actual_transitions, key=expected_transitions.index),
            [
                ("OPEN", "PENDING_CLOSURE"),
                ("PENDING_CLOSURE", "MASTER_APPROVED"),
                ("MASTER_APPROVED", "CLOSED"),
            ],
        )

    def test_master_approved_rows_do_not_surface_as_open_scm_findings(self) -> None:
        excluded_id = self._insert_finding_row(
            title="Awaiting close after Master approval",
            status="MASTER_APPROVED",
            created_date=aware(2026, 5, 5, 8, 30),
        )
        included_id = self._insert_finding_row(
            title="Fresh open galley observation",
            status="OPEN",
            created_date=aware(2026, 5, 5, 9, 0),
        )

        request = self.factory.get("/api/safety/soi/open-findings/?vessel_id=7")
        force_authenticate(
            request,
            user=build_user(role_name="CO", user_id="co-7", form_ids=["SAF_F_003"]),
        )

        response = self.open_findings_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["summary"]["new_count"], 1)
        self.assertEqual(
            [item["finding_id"] for item in response.data["new_findings"]],
            [included_id],
        )
        self.assertNotIn(excluded_id, [item["finding_id"] for item in response.data["new_findings"]])

    def _create_finding(self, *, status: str, title: str) -> SOIFinding:
        return SOIFinding.objects.create(
            inspection_id=self.inspection_id,
            area_id=5,
            item_id=3001,
            title=title,
            description=f"{title} description.",
            severity="MED",
            priority="MED",
            status=status,
            created_by="co-7",
        )

    def _insert_inspection(self) -> str:
        inspection_id = uuid.uuid4().hex
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_inspection (
                    id,
                    vessel_id,
                    inspection_reference,
                    cycle_label,
                    state,
                    planned_date,
                    safety_officer_crew_id,
                    safety_officer_department,
                    assistant_crew_id,
                    assistant_department,
                    master_crew_id,
                    checklist_unique_id,
                    reported_at,
                    checklist_generated_at,
                    checklist_format,
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    inspection_id,
                    "7",
                    "SOI/ABC/26/11",
                    "Q2/2026",
                    "REPORTED",
                    date(2026, 5, 5),
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    "master-7",
                    "SOI-UID-011",
                    aware(2026, 5, 5, 7, 30),
                    aware(2026, 5, 4, 16, 0),
                    "PDF",
                    False,
                    1,
                    False,
                    "co-7",
                ],
            )
            return inspection_id

    def _insert_finding_row(self, *, title: str, status: str, created_date) -> str:
        finding_id = uuid.uuid4().hex
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_finding (
                    id,
                    inspection_id,
                    area_id,
                    item_id,
                    title,
                    description,
                    severity,
                    priority,
                    status,
                    created_by,
                    created_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    finding_id,
                    self.inspection_id,
                    5,
                    3001,
                    title,
                    f"{title} description.",
                    "MED",
                    "MED",
                    status,
                    "co-7",
                    created_date,
                ],
            )
            return finding_id
