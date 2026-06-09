from __future__ import annotations

from datetime import date, datetime, timezone as dt_timezone
from types import SimpleNamespace
import uuid
import unittest

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_scm_tables,
    recreate_soi_tables,
)


bootstrap_django()

from django.db import connection
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import CorrectiveAction, Incident, SCMMeeting, SOIInspection
from apps.safety.views.scm_closed_since import (
    SCMClosedSinceLastMeetingView,
    SCMClosedSinceLastVesselView,
)


def build_user(
    *,
    role_name: str = "DPA",
    user_id: str = "dpa-7",
    vessel_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_003"],
        process_ids=[],
        vessel_ids=["7"] if vessel_ids is None else vessel_ids,
        is_global=False,
    )


def aware(year: int, month: int, day: int, hour: int, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


class ClosedSinceLastSCMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_scm_tables()
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.meeting_view = SCMClosedSinceLastMeetingView.as_view()
        self.vessel_view = SCMClosedSinceLastVesselView.as_view()

    def test_meeting_route_aggregates_closed_items_since_prior_signoff(self) -> None:
        prior_meeting = self._create_signed_off_meeting(
            meeting_date=date(2026, 4, 1),
            signed_off_at=aware(2026, 4, 1, 10, 0),
            meeting_type=SCMMeeting.MeetingType.REGULAR,
        )
        current_meeting = self._create_meeting(meeting_date=date(2026, 4, 28))

        closed_incident = self._create_incident(
            incident_number="INC-001",
            record_type=Incident.RecordType.INCIDENT,
            state="CLOSED",
            closed_at=aware(2026, 4, 10, 9, 0),
        )
        self._create_incident(
            incident_number="INC-000",
            record_type=Incident.RecordType.INCIDENT,
            state="CLOSED",
            closed_at=aware(2026, 3, 20, 9, 0),
        )
        closed_near_miss = self._create_incident(
            incident_number="NM-001",
            record_type=Incident.RecordType.NEAR_MISS,
            state="CLOSED",
            closed_at=aware(2026, 4, 11, 12, 0),
            near_miss_priority="LOW",
        )
        self._create_incident(
            incident_number="NM-OFFICE-COMMENTS-COMPLETED",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            closed_at=None,
            near_miss_priority="HIGH",
        )
        self._create_corrective_action(
            source_id=closed_incident.id,
            closed_at=aware(2026, 4, 12, 15, 0),
        )
        inspection_id = self._insert_soi_inspection(
            inspection_reference="SOI/ABC/26/01",
            checklist_unique_id="SOI-UID-001",
            closed_at=aware(2026, 4, 19, 8, 0),
        )
        self._insert_soi_finding(
            inspection_id=inspection_id,
            title="Closed lifeboat drill follow-up",
            status="CLOSED",
            closed_at=aware(2026, 4, 20, 8, 30),
        )
        self._insert_soi_finding(
            inspection_id=inspection_id,
            title="Pending closure finding",
            status="PENDING_CLOSURE",
            closed_at=None,
        )
        self._insert_soi_inspection(
            vessel_id="99",
            inspection_reference="SOI/XYZ/26/01",
            checklist_unique_id="SOI-UID-999",
            closed_at=aware(2026, 4, 19, 8, 0),
        )

        request = self.factory.get(f"/api/safety/scm/{current_meeting.id}/closed-since-last/")
        force_authenticate(request, user=build_user())

        response = self.meeting_view(request, id=current_meeting.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meeting_id"], current_meeting.id)
        self.assertEqual(response.data["cutoff"]["meeting_id"], prior_meeting.id)
        self.assertEqual(
            datetime.fromisoformat(response.data["cutoff"]["closed_at"]).astimezone(dt_timezone.utc),
            prior_meeting.master_signed_off_at.astimezone(dt_timezone.utc),
        )
        self.assertEqual(response.data["summary"]["incident_count"], 1)
        self.assertEqual(response.data["summary"]["near_miss_count"], 1)
        self.assertEqual(response.data["summary"]["soi_finding_count"], 1)
        self.assertEqual(response.data["summary"]["corrective_action_count"], 1)
        self.assertEqual(response.data["summary"]["total_count"], 4)

        references = {item["reference"] for item in response.data["items"]}
        self.assertIn("INC-001", references)
        self.assertIn("NM-001", references)
        self.assertIn("SOI/ABC/26/01", references)
        self.assertNotIn("INC-000", references)
        self.assertNotIn("NM-OFFICE-COMMENTS-COMPLETED", references)
        self.assertTrue(all(item["status"] == "CLOSED" for item in response.data["items"]))
        self.assertIsNone(response.data["empty_message"])
        self.assertEqual(
            {item["item_type"] for item in response.data["items"]},
            {"INCIDENT", "NEAR_MISS", "SOI_FINDING", "CORRECTIVE_ACTION"},
        )
        soi_item = next(item for item in response.data["items"] if item["item_type"] == "SOI_FINDING")
        self.assertEqual(soi_item["unique_id"], "SOI-UID-001")
        inspection_id = SOIInspection.objects.get(pk=inspection_id).id.hex
        self.assertEqual(soi_item["source_route"], f"/safety/soi/{inspection_id}/findings")
        ca_item = next(item for item in response.data["items"] if item["item_type"] == "CORRECTIVE_ACTION")
        self.assertEqual(
            ca_item["source_route"],
            f"/safety/incidents/{closed_incident.id}/corrective-actions",
        )
        near_miss_item = next(item for item in response.data["items"] if item["item_type"] == "NEAR_MISS")
        self.assertEqual(near_miss_item["source_id"], closed_near_miss.id)

    def test_vessel_route_anchors_on_latest_signed_off_meeting_regardless_of_type(self) -> None:
        self._create_signed_off_meeting(
            meeting_date=date(2026, 4, 1),
            signed_off_at=aware(2026, 4, 1, 10, 0),
            meeting_type=SCMMeeting.MeetingType.REGULAR,
        )
        latest_cutoff = self._create_signed_off_meeting(
            meeting_date=date(2026, 4, 15),
            signed_off_at=aware(2026, 4, 15, 16, 0),
            meeting_type=SCMMeeting.MeetingType.AD_HOC,
            scm_number="ABC-15-Apr-2026",
        )
        self._create_incident(
            incident_number="INC-BEFORE-ADHOC",
            record_type=Incident.RecordType.INCIDENT,
            state="CLOSED",
            closed_at=aware(2026, 4, 10, 9, 0),
        )
        self._create_incident(
            incident_number="INC-AFTER-ADHOC",
            record_type=Incident.RecordType.INCIDENT,
            state="CLOSED",
            closed_at=aware(2026, 4, 20, 9, 0),
        )

        request = self.factory.get("/api/safety/scm/closed-since-last/?vessel_id=7")
        force_authenticate(request, user=build_user())

        response = self.vessel_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["meeting_id"])
        self.assertEqual(response.data["cutoff"]["meeting_id"], latest_cutoff.id)
        self.assertEqual(response.data["cutoff"]["meeting_type"], "AD_HOC")
        self.assertEqual(response.data["summary"]["incident_count"], 1)
        self.assertEqual(response.data["summary"]["total_count"], 1)
        self.assertEqual([item["reference"] for item in response.data["items"]], ["INC-AFTER-ADHOC"])

    def test_returns_empty_payload_when_no_prior_signed_off_meeting_exists(self) -> None:
        request = self.factory.get("/api/safety/scm/closed-since-last/?vessel_id=7")
        force_authenticate(request, user=build_user())

        response = self.vessel_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["cutoff"])
        self.assertEqual(response.data["summary"]["total_count"], 0)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(response.data["empty_message"], "Nothing closed since last SCM.")

    def _create_meeting(
        self,
        *,
        meeting_date: date,
        meeting_type: str = SCMMeeting.MeetingType.REGULAR,
        scm_number: str | None = None,
    ) -> SCMMeeting:
        return SCMMeeting.objects.create(
            vessel_id="7",
            scm_number=scm_number or f"ABC-{meeting_date.strftime('%d-%b-%Y')}",
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            meeting_time_local=datetime.strptime("10:00:00", "%H:%M:%S").time(),
            location="Singapore Anchorage",
            voyage_no="V2026-03",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            ad_hoc_trigger_reason=(
                "Ad-Hoc trigger reason captured for Step 3.4 cutoff anchoring."
                if meeting_type == SCMMeeting.MeetingType.AD_HOC
                else None
            ),
            state=SCMMeeting.State.DRAFT,
            created_by="co-7",
            updated_by="co-7",
        )

    def _create_signed_off_meeting(
        self,
        *,
        meeting_date: date,
        signed_off_at,
        meeting_type: str,
        scm_number: str | None = None,
    ) -> SCMMeeting:
        meeting = self._create_meeting(
            meeting_date=meeting_date,
            meeting_type=meeting_type,
            scm_number=scm_number,
        )
        meeting.state = SCMMeeting.State.SIGNED_OFF
        meeting.master_signed_off_at = signed_off_at
        meeting.master_signed_off_by = "master-7"
        meeting.save(update_fields=["state", "master_signed_off_at", "master_signed_off_by"])
        return meeting

    def _create_incident(
        self,
        *,
        incident_number: str,
        record_type: str,
        state: str,
        closed_at,
        near_miss_priority: str | None = None,
    ) -> Incident:
        return Incident.objects.create(
            vessel_id="7",
            state=state,
            created_by="system",
            updated_by="system",
            schema_version=1,
            incident_number=incident_number,
            record_type=record_type,
            current_phase=9 if state == "CLOSED" and record_type == Incident.RecordType.INCIDENT else 1,
            near_miss_priority=near_miss_priority,
            narrative=f"{incident_number} narrative for closed-since-last testing.",
            closed_at=closed_at,
        )

    def _create_corrective_action(self, *, source_id: int, closed_at) -> CorrectiveAction:
        return CorrectiveAction.objects.create(
            source_table=Incident._meta.db_table,
            source_id=source_id,
            recommendation=None,
            title="Closed corrective action",
            description="Action completed for summary-block verification.",
            status=CorrectiveAction.Status.CLOSED,
            closed_at=closed_at,
            closed_by="dpa-7",
            created_by="dpa-7",
            updated_by="dpa-7",
        )

    def _insert_soi_inspection(
        self,
        *,
        inspection_reference: str,
        checklist_unique_id: str,
        closed_at,
        vessel_id: str = "7",
    ) -> int:
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
                    closed_at,
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    inspection_id,
                    vessel_id,
                    inspection_reference,
                    "Q2/2026",
                    "CLOSED",
                    "2026-04-18",
                    "so-7",
                    "DECK",
                    "asst-7",
                    "ENGINE",
                    "master-7",
                    checklist_unique_id,
                    closed_at,
                    False,
                    1,
                    False,
                    "so-7",
                ],
            )
            return inspection_id

    def _insert_soi_finding(
        self,
        *,
        inspection_id: int,
        title: str,
        status: str,
        closed_at,
    ) -> int:
        finding_id = uuid.uuid4().hex
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_finding (
                    id,
                    inspection_id,
                    area_id,
                    title,
                    description,
                    severity,
                    priority,
                    status,
                    closed_at,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    finding_id,
                    inspection_id,
                    1,
                    title,
                    f"{title} description.",
                    "MED",
                    "MED",
                    status,
                    closed_at,
                    1,
                    False,
                    "so-7",
                ],
            )
            return finding_id
