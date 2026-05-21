from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_master_notification_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import EvidenceDeadlineTask, Incident
from apps.safety.views.incident_phase2 import IncidentPhase2SubmitView, IncidentPhase2UpdateView
from apps.safety.views.incident_phase3 import IncidentPhase3DeadlineTaskView


def build_user(
    *,
    role_name: str = "MASTER",
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_002"],
        vessel_ids=["7"],
        is_global=False,
    )


class EvidenceDeadlineTaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_master_notification_table()
        self.factory = APIRequestFactory()
        self.update_view = IncidentPhase2UpdateView.as_view()
        self.submit_view = IncidentPhase2SubmitView.as_view()
        self.task_view = IncidentPhase3DeadlineTaskView.as_view()

    def test_phase2_submit_creates_default_deadline_tasks(self) -> None:
        occurred_at = datetime(2026, 4, 27, 6, 0, tzinfo=timezone.utc)
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="SUBMITTED",
            current_phase=2,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
            narrative="Narrative " + ("details " * 30),
            first_hour_checklist_done=True,
            reporter_id="master-7",
            occurred_at=occurred_at,
            latitude="12.345678",
            longitude="103.456789",
        )

        update_request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/phase-2/",
            {
                "risk_band": Incident.RiskBand.RED,
                "imo_classifier": Incident.ImoClassifier.MI,
                "pic_user_id": "pic-9",
            },
            format="json",
        )
        force_authenticate(update_request, user=build_user())
        update_response = self.update_view(update_request, id=incident.pk)
        self.assertEqual(update_response.status_code, 200)

        submit_request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-2/submit/",
            {},
            format="json",
        )
        force_authenticate(submit_request, user=build_user())
        submit_response = self.submit_view(submit_request, id=incident.pk)
        self.assertEqual(submit_response.status_code, 200)

        tasks = {
            task.task_code: task
            for task in EvidenceDeadlineTask.objects.filter(incident_id=incident.pk)
        }
        self.assertEqual(set(tasks), {"VDR_CAPTURE", "ECDIS_SNAPSHOT", "AIS_REQUEST", "PHOTO_WALKAROUND", "FORMAL_STATEMENTS"})
        self.assertEqual(tasks["VDR_CAPTURE"].due_at, occurred_at + tasks["VDR_CAPTURE"].due_within)
        self.assertEqual(tasks["ECDIS_SNAPSHOT"].due_at, occurred_at + tasks["ECDIS_SNAPSHOT"].due_within)
        self.assertEqual(tasks["AIS_REQUEST"].due_at, occurred_at + tasks["AIS_REQUEST"].due_within)
        self.assertEqual(tasks["PHOTO_WALKAROUND"].due_at, occurred_at + tasks["PHOTO_WALKAROUND"].due_within)
        self.assertEqual(tasks["FORMAL_STATEMENTS"].due_at, occurred_at + tasks["FORMAL_STATEMENTS"].due_within)
        self.assertEqual(tasks["VDR_CAPTURE"].severity, EvidenceDeadlineTask.Severity.HARD_ALARM)

    def test_phase3_deadline_task_can_be_completed_with_justification(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/TASK-1",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        task = EvidenceDeadlineTask.objects.create(
            incident=incident,
            task_code="AIS_REQUEST",
            title="Request AIS shore-side record",
            due_at=datetime(2026, 4, 28, 6, 0, tzinfo=timezone.utc),
            status=EvidenceDeadlineTask.Status.PENDING,
            severity=EvidenceDeadlineTask.Severity.ALERT,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/evidence/deadline-tasks/{task.pk}/",
            {"status": "COMPLETED", "justification": "AIS requested from port agent."},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.task_view(request, id=incident.pk, task_id=task.pk)

        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, EvidenceDeadlineTask.Status.COMPLETED)
        self.assertEqual(task.justification, "AIS requested from port agent.")
        self.assertIsNotNone(task.completed_at)
