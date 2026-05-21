from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_scm_tables


bootstrap_django()

from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SCMAgendaItem, SCMMeeting
from apps.safety.views.scm_agenda import SCMAgendaView
from apps.safety.views.scm_attendance import SCMAttendanceListCreateView


def aware(year: int, month: int, day: int, hour: int = 0, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


def build_user(*, role_name: str, process_ids: list[str]):
    return SimpleNamespace(
        id=f"{role_name.lower()}-7",
        username=f"{role_name.lower()}-7",
        role_name=role_name,
        form_ids=["SAF_F_003"],
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class SCMStateImmutableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_scm_tables()
        self.factory = APIRequestFactory()
        self.agenda_view = SCMAgendaView.as_view()
        self.attendance_view = SCMAttendanceListCreateView.as_view()
        self.meeting = self._create_signed_off_meeting()

    def test_signed_off_meeting_rejects_agenda_patch(self) -> None:
        request = self.factory.patch(
            f"/api/safety/scm/{self.meeting.id}/agenda/",
            {
                "rows": [
                    {
                        "agenda_item_number": 1,
                        "content": "Updated content that should be rejected because the meeting is already signed off.",
                    }
                ]
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="CO", process_ids=["SAF_P_002"]))

        response = self.agenda_view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["state"][0],
            "Signed-off SCM meetings are read-only in the handover workspace.",
        )

    def test_signed_off_meeting_rejects_attendance_write(self) -> None:
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/attendance/",
            {
                "rows": [
                    {
                        "crew_id": "crew-1",
                        "rank_name": "Chief Officer",
                        "display_name": "Chief Officer",
                        "present": True,
                    }
                ]
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER", process_ids=["SAF_P_001"]))

        response = self.attendance_view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["state"][0],
            "Signed-off SCM meetings are read-only in the handover workspace.",
        )

    def test_office_user_cannot_write_attendance_even_with_process_permission(self) -> None:
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/attendance/",
            {
                "rows": [
                    {
                        "crew_id": "crew-1",
                        "rank_name": "Chief Officer",
                        "display_name": "Chief Officer",
                        "present": True,
                    }
                ]
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="OFFICE_PIC", process_ids=["SAF_P_001"]))

        response = self.attendance_view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 403)

    def test_office_user_cannot_read_attendance_editor_payload(self) -> None:
        request = self.factory.get(f"/api/safety/scm/{self.meeting.id}/attendance/")
        force_authenticate(request, user=build_user(role_name="OFFICE_PIC", process_ids=[]))

        response = self.attendance_view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 403)

    def _create_signed_off_meeting(self) -> SCMMeeting:
        meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="ABC-01-Apr-2026",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=date(2026, 4, 1),
            meeting_time_local="10:00:00",
            location="Singapore Anchorage",
            voyage_no="V2026-02",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            state=SCMMeeting.State.SIGNED_OFF,
            master_signed_off_at=aware(2026, 4, 1, 11, 0),
            master_signed_off_by="master-7",
            schema_version=1,
            created_by="co-7",
            updated_by="master-7",
            updated_date=aware(2026, 4, 1, 11, 0),
        )
        SCMAgendaItem.objects.create(
            meeting_id=meeting.id,
            agenda_item_number=1,
            section_label="Section 1",
            auto_populated=False,
            content="Agenda content already captured before the meeting was signed off.",
            decision="Keep as-is.",
            schema_version=1,
        )
        return meeting
