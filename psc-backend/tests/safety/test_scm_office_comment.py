from __future__ import annotations

from datetime import date
from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_scm_tables


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SCMLegacyField, SCMMeeting, SafetyFieldHistory
from apps.safety.views.scm_office_comment import SCMOfficeCommentView


def build_user(*, role_name: str, user_id: str):
    return SimpleNamespace(
        id=user_id,
        is_authenticated=True,
        username=user_id,
        role_name=role_name,
        safety_role_name=role_name,
        form_ids=["SAF_F_003"],
        process_ids=[],
        vessel_ids=["7"],
        is_global=role_name in {"DPA", "FM"},
    )


class SCMOfficeCommentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_scm_tables()
        self.factory = APIRequestFactory()
        self.view = SCMOfficeCommentView.as_view()
        self.meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="ABC-28-Apr-2026",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=date(2026, 4, 28),
            meeting_time_local="10:00:00",
            location="Singapore Anchorage",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            state=SCMMeeting.State.SIGNED_OFF,
            master_signed_off_at=timezone.now(),
            master_signed_off_by="master-7",
            created_by="co-7",
        )

    def test_dpa_can_add_audited_office_comment_without_changing_scm_state(self) -> None:
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/office-comment/",
            {"office_comment": "Follow up trend with vessel team."},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="DPA", user_id="dpa-1"))

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 200)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.state, SCMMeeting.State.SIGNED_OFF)
        self.assertEqual(self.meeting.office_comment, "Follow up trend with vessel team.")
        self.assertEqual(self.meeting.office_comment_by, "dpa-1")
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                parent_table=SCMMeeting._meta.db_table,
                parent_id=self.meeting.id,
                field_name="office_comment",
            ).exists()
        )
        self.assertEqual(
            SCMLegacyField.objects.get(
                meeting_id=self.meeting.id,
                agenda_item_number=10,
                field_key="officecomments",
            ).field_value,
            "Follow up trend with vessel team.",
        )
        self.assertEqual(
            SCMLegacyField.objects.get(
                meeting_id=self.meeting.id,
                agenda_item_number=10,
                field_key="isreviewed",
            ).field_value,
            "true",
        )

    def test_ship_user_cannot_add_office_comment(self) -> None:
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/office-comment/",
            {"office_comment": "Not an office oversight comment."},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER", user_id="master-7"))

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 403)

    def test_office_comment_requires_master_signoff(self) -> None:
        unsigned_meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="ABC-29-Apr-2026",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=date(2026, 4, 29),
            meeting_time_local="10:00:00",
            location="Singapore Anchorage",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            state=SCMMeeting.State.SUBMITTED,
            created_by="co-7",
        )
        request = self.factory.post(
            f"/api/safety/scm/{unsigned_meeting.id}/office-comment/",
            {"office_comment": "Office review before sign-off."},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="DPA", user_id="dpa-1"))

        response = self.view(request, id=unsigned_meeting.id)

        self.assertEqual(response.status_code, 400)
        unsigned_meeting.refresh_from_db()
        self.assertIsNone(unsigned_meeting.office_comment)
