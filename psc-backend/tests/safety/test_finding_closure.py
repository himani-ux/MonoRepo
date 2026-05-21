from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
import uuid
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SOIFinding, SOIInspection, SOIOfficerSetting
from apps.safety.views.finding_closure import (
    SOIFindingApproveClosureView,
    SOIFindingPendingClosureView,
    SOIFindingReopenView,
)


def build_user(
    *,
    role_name: str,
    process_ids: list[str],
    user_id: str,
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_004"],
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class SOIFindingClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.pending_view = SOIFindingPendingClosureView.as_view()
        self.approve_view = SOIFindingApproveClosureView.as_view()
        self.reopen_view = SOIFindingReopenView.as_view()
        self.inspection_id = self._insert_inspection()
        self.finding_id = self._insert_finding(status="OPEN")

    def test_safety_officer_can_mark_finding_pending_closure(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/findings/{self.finding_id}/pending-closure/",
            {
                "typed_name": "Chief Officer Seven",
                "device_fingerprint": "tablet-co-7",
                "closure_note": "Rectified and ready for Master review.",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="CO", process_ids=["SAF_P_014"], user_id="co-7"),
        )

        response = self.pending_view(request, finding_id=self.finding_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "PENDING_CLOSURE")
        self.assertIsNotNone(response.data["pending_closure_signature"])
        finding = SOIFinding.objects.get(pk=self.finding_id)
        self.assertEqual(finding.status, SOIFinding.Status.PENDING_CLOSURE)
        self.assertIn("Rectified and ready for Master review.", finding.closure_note or "")

    def test_2e_without_master_toggle_cannot_mark_pending_closure(self) -> None:
        request = self.factory.post(
            f"/api/safety/soi/findings/{self.finding_id}/pending-closure/",
            {
                "typed_name": "Second Engineer Seven",
                "device_fingerprint": "tablet-2e-7",
                "closure_note": "Rectified and ready for Master review.",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="2/E", process_ids=["SAF_P_014"], user_id="2e-7"),
        )

        response = self.pending_view(request, finding_id=self.finding_id)

        self.assertEqual(response.status_code, 403)

    def test_master_can_approve_pending_closure_and_close_finding(self) -> None:
        finding = SOIFinding.objects.get(pk=self.finding_id)
        finding.status = SOIFinding.Status.PENDING_CLOSURE
        finding.save(update_fields=["status"])

        request = self.factory.post(
            f"/api/safety/soi/findings/{self.finding_id}/approve-closure/",
            {
                "decision": "APPROVE",
                "typed_name": "Master Seven",
                "device_fingerprint": "bridge-console-7",
                "closure_note": "Verified during deck round.",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="MASTER", process_ids=["SAF_P_015"], user_id="master-7"),
        )

        response = self.approve_view(request, finding_id=self.finding_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "CLOSED")
        self.assertEqual(response.data["master_approval_state"], "MASTER_APPROVED")
        self.assertIsNotNone(response.data["master_counter_signature"])
        self.assertIn("transition", response.data)
        finding.refresh_from_db()
        self.assertEqual(finding.status, SOIFinding.Status.CLOSED)
        self.assertEqual(finding.master_approved_by, "master-7")
        self.assertIsNotNone(finding.master_approved_at)
        self.assertIsNotNone(finding.closed_at)

    def test_master_rejection_requires_reason_and_returns_to_open(self) -> None:
        finding = SOIFinding.objects.get(pk=self.finding_id)
        finding.status = SOIFinding.Status.PENDING_CLOSURE
        finding.save(update_fields=["status"])

        bad_request = self.factory.post(
            f"/api/safety/soi/findings/{self.finding_id}/approve-closure/",
            {"decision": "REJECT"},
            format="json",
        )
        force_authenticate(
            bad_request,
            user=build_user(role_name="MASTER", process_ids=["SAF_P_015"], user_id="master-7"),
        )

        bad_response = self.approve_view(bad_request, finding_id=self.finding_id)

        self.assertEqual(bad_response.status_code, 400)
        self.assertIn("reason", bad_response.data)

        request = self.factory.post(
            f"/api/safety/soi/findings/{self.finding_id}/approve-closure/",
            {
                "decision": "REJECT",
                "reason": "Outstanding corrective evidence still missing.",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="MASTER", process_ids=["SAF_P_015"], user_id="master-7"),
        )

        response = self.approve_view(request, finding_id=self.finding_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "OPEN")
        self.assertIn("Outstanding corrective evidence still missing.", response.data["closure_note"])
        finding.refresh_from_db()
        self.assertEqual(finding.status, SOIFinding.Status.OPEN)

    def test_dpa_can_reopen_closed_finding_with_audit_reason(self) -> None:
        finding = SOIFinding.objects.get(pk=self.finding_id)
        finding.status = SOIFinding.Status.CLOSED
        finding.closed_at = datetime(2026, 5, 3, 10, 0, tzinfo=timezone.utc)
        finding.master_approved_at = datetime(2026, 5, 3, 9, 30, tzinfo=timezone.utc)
        finding.master_approved_by = "master-7"
        finding.save(update_fields=["status", "closed_at", "master_approved_at", "master_approved_by"])
        SOIInspection.objects.filter(pk=self.inspection_id).update(
            state=SOIInspection.State.CLOSED,
            closed_at=datetime(2026, 5, 3, 11, 0, tzinfo=timezone.utc),
        )

        request = self.factory.post(
            f"/api/safety/soi/findings/{self.finding_id}/reopen/",
            {"reason": "Closure evidence was incomplete during office safety review."},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="DPA", process_ids=["SAF_P_008"], user_id="dpa-1"),
        )

        response = self.reopen_view(request, finding_id=self.finding_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "OPEN")
        self.assertEqual(response.data["transition"]["transition"], "DPA_REOPENED_TO_OPEN")
        finding.refresh_from_db()
        self.assertEqual(finding.status, SOIFinding.Status.OPEN)
        self.assertIsNone(finding.closed_at)
        self.assertIsNone(finding.master_approved_at)
        self.assertIsNone(finding.master_approved_by)
        self.assertIn("Closure evidence was incomplete", finding.closure_note or "")
        inspection = SOIInspection.objects.get(pk=self.inspection_id)
        self.assertEqual(inspection.state, SOIInspection.State.REPORTED)
        self.assertIsNone(inspection.closed_at)

    def test_reopened_finding_can_be_resubmitted_and_master_closes_with_fresh_signature(self) -> None:
        finding = SOIFinding.objects.get(pk=self.finding_id)
        finding.status = SOIFinding.Status.CLOSED
        finding.closed_at = datetime(2026, 5, 3, 10, 0, tzinfo=timezone.utc)
        finding.master_approved_at = datetime(2026, 5, 3, 9, 30, tzinfo=timezone.utc)
        finding.master_approved_by = "master-7"
        finding.save(update_fields=["status", "closed_at", "master_approved_at", "master_approved_by"])

        reopen_request = self.factory.post(
            f"/api/safety/soi/findings/{self.finding_id}/reopen/",
            {"reason": "Office review asked vessel to refresh closure evidence."},
            format="json",
        )
        force_authenticate(
            reopen_request,
            user=build_user(role_name="DPA", process_ids=["SAF_P_008"], user_id="dpa-1"),
        )
        self.reopen_view(reopen_request, finding_id=self.finding_id)
        SOIOfficerSetting.objects.create(
            vessel_id="7",
            alternate_enabled=True,
            alternate_so_crew_id="2e-7",
            created_by="master-7",
        )

        pending_request = self.factory.post(
            f"/api/safety/soi/findings/{self.finding_id}/pending-closure/",
            {
                "typed_name": "Second Engineer Seven",
                "device_fingerprint": "tablet-2e-7",
                "closure_note": "Updated closure evidence attached.",
            },
            format="json",
        )
        force_authenticate(
            pending_request,
            user=build_user(role_name="2/E", process_ids=["SAF_P_014"], user_id="2e-7"),
        )
        pending_response = self.pending_view(pending_request, finding_id=self.finding_id)

        self.assertEqual(pending_response.status_code, 200)
        self.assertEqual(pending_response.data["status"], "PENDING_CLOSURE")
        self.assertIsNone(pending_response.data["master_counter_signature"])

        approve_request = self.factory.post(
            f"/api/safety/soi/findings/{self.finding_id}/approve-closure/",
            {
                "decision": "APPROVE",
                "typed_name": "Master Seven",
                "device_fingerprint": "bridge-console-7",
                "closure_note": "Fresh evidence verified.",
            },
            format="json",
        )
        force_authenticate(
            approve_request,
            user=build_user(role_name="MASTER", process_ids=["SAF_P_015"], user_id="master-7"),
        )
        approve_response = self.approve_view(approve_request, finding_id=self.finding_id)

        self.assertEqual(approve_response.status_code, 200)
        self.assertEqual(approve_response.data["status"], "CLOSED")
        self.assertIsNotNone(approve_response.data["master_counter_signature"])

    def _insert_inspection(self) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_inspection (
                    public_id,
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
                    checklist_generated_at,
                    checklist_format,
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(uuid.uuid4()),
                    "7",
                    "SOI/ABC/26/09",
                    "Q2/2026",
                    "DOWNLOADED",
                    date(2026, 5, 1),
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    "master-7",
                    "SOI-UID-009",
                    "2026-05-01 08:00:00",
                    "PDF",
                    False,
                    1,
                    False,
                    "co-7",
                ],
            )
            return int(cursor.lastrowid)

    def _insert_finding(self, *, status: str) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_finding (
                    public_id,
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
                    str(uuid.uuid4()),
                    self.inspection_id,
                    5,
                    3001,
                    "Forward station drain cover",
                    "Drain cover was repaired and verified by the deck team.",
                    "MED",
                    "MED",
                    status,
                    "co-7",
                    "2026-05-02 10:00:00",
                ],
            )
            return int(cursor.lastrowid)
