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


def build_user(*, role_name: str, user_id: str, profile_id: str | None = None):
    return SimpleNamespace(
        id=user_id,
        is_authenticated=True,
        login_id=user_id,
        profile_id=profile_id,
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
            state=SCMMeeting.State.DRAFT,
            created_by="co-7",
        )

    def test_dpa_can_add_audited_office_comment_and_close_meeting(self) -> None:
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/office-comment/",
            {"office_comment": "Follow up trend with vessel team."},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="DPA", user_id="dpa-1"))

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 200)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.state, SCMMeeting.State.CLOSED)
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
                agenda_item_number=9,
                field_key="officecomments",
            ).field_value,
            "Follow up trend with vessel team.",
        )
        self.assertEqual(
            SCMLegacyField.objects.get(
                meeting_id=self.meeting.id,
                agenda_item_number=9,
                field_key="isreviewed",
            ).field_value,
            "true",
        )

    def test_marine_superintendent_profile_can_add_office_comment(self) -> None:
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/office-comment/",
            {"office_comment": "Marine superintendent review completed."},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(
                role_name="MARINE SUPERINTENDENT",
                user_id="marine-supt-1",
                profile_id="407EF017-0F1C-EF11-A9F1-F348983BAE6B",
            ),
        )

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 200)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.state, SCMMeeting.State.CLOSED)
        self.assertEqual(self.meeting.office_comment, "Marine superintendent review completed.")
        self.assertEqual(self.meeting.office_comment_by, "marine-supt-1")

    def test_ship_user_cannot_add_office_comment(self) -> None:
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/office-comment/",
            {"office_comment": "Not an office oversight comment."},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER", user_id="master-7"))

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 403)

    def test_office_comment_cannot_be_added_twice_after_closure(self) -> None:
        self.meeting.office_comment = "Already reviewed."
        self.meeting.office_comment_at = timezone.now()
        self.meeting.office_comment_by = "dpa-1"
        self.meeting.state = SCMMeeting.State.CLOSED
        self.meeting.save(update_fields=("office_comment", "office_comment_at", "office_comment_by", "state"))
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/office-comment/",
            {"office_comment": "Second office review."},
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="DPA", user_id="dpa-1"))

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 400)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.office_comment, "Already reviewed.")
