from __future__ import annotations

from datetime import date, datetime, timedelta
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_scm_tables, recreate_soi_tables


bootstrap_django()

from django.db import connection
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SCMAgendaItem, SCMAttendance, SCMLegacyField, SCMMeeting, SCMSignature
from apps.safety.serializers.scm import SCM_LEGACY_FIELD_TEMPLATE
from apps.safety.views.scm_signoff import SCMSignOffPreflightView, SCMSignOffView


def aware(year: int, month: int, day: int, hour: int = 0, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


def build_user(
    *,
    role_name: str = "MASTER",
    process_ids: list[str] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_003"],
        process_ids=["SAF_P_004"] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class SCMOverdueSOIBlockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_scm_tables()
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.preflight_view = SCMSignOffPreflightView.as_view()
        self.signoff_view = SCMSignOffView.as_view()
        self.meeting = self._create_meeting()
        self.current_at = timezone.now().replace(microsecond=0)
        self.overdue_due_at = self.current_at - timedelta(days=5)
        self.last_inspected_at = self.overdue_due_at - timedelta(days=90)
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_area_map(
            vessel_id="7",
            area_id=3,
            last_inspected_at=self.last_inspected_at,
            due_at=self.overdue_due_at,
            applicable=True,
        )

    def test_preflight_reports_overdue_areas_and_current_workspace_booleans(self) -> None:
        request = self.factory.get(f"/api/safety/scm/{self.meeting.id}/preflight/")
        force_authenticate(request, user=build_user(process_ids=[]))

        response = self.preflight_view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meeting_id"], self.meeting.id)
        self.assertEqual(response.data["meeting_state"], SCMMeeting.State.SUBMITTED)
        self.assertEqual(response.data["agenda_complete"], True)
        self.assertEqual(response.data["attendance_acknowledged"], True)
        self.assertEqual(len(response.data["overdue_soi_areas"]), 1)
        self.assertEqual(response.data["overdue_soi_areas"][0]["message"], "Area 3 overdue by 5 days")

    def test_overdue_soi_blocks_signoff_until_area_is_cleared(self) -> None:
        blocked_request = self.factory.post(f"/api/safety/scm/{self.meeting.id}/sign-off/", {}, format="json")
        force_authenticate(blocked_request, user=build_user())

        blocked_response = self.signoff_view(blocked_request, id=self.meeting.id)

        self.assertEqual(blocked_response.status_code, 422)
        self.assertEqual(
            blocked_response.data["errors"]["soi_overdue"],
            ["Area 3 overdue by 5 days"],
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE vims_safety_soi_vessel_area_map
                SET last_inspected_at = %s,
                    due_at = %s
                WHERE vessel_id = %s AND area_id = %s
                """,
                [self.current_at - timedelta(days=1), self.current_at + timedelta(days=90), "7", 3],
            )

        success_request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/sign-off/",
            {
                "typed_name": "Master Seven",
                "device_fingerprint": "device-master-7",
            },
            format="json",
        )
        force_authenticate(success_request, user=build_user())

        success_response = self.signoff_view(success_request, id=self.meeting.id)

        self.assertEqual(success_response.status_code, 200)
        self.assertEqual(success_response.data["state"], SCMMeeting.State.SIGNED_OFF)
        self.assertEqual(success_response.data["master_signed_off_by"], "master-7")
        self.assertIsNotNone(success_response.data["master_signed_off_at"])
        self.assertEqual(success_response.data["signature"]["typed_name"], "Master Seven")

        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.state, SCMMeeting.State.SIGNED_OFF)
        self.assertEqual(self.meeting.master_signed_off_by, "master-7")
        self.assertIsNotNone(self.meeting.master_signed_off_at)

    def test_non_master_is_rejected_even_with_process_id(self) -> None:
        request = self.factory.get(f"/api/safety/scm/{self.meeting.id}/preflight/")
        force_authenticate(request, user=build_user(role_name="CO"))

        response = self.preflight_view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 403)

    def _create_meeting(self) -> SCMMeeting:
        meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="ABC-28-Apr-2026",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=date(2026, 4, 28),
            meeting_time_local="10:00:00",
            location="Singapore Anchorage",
            voyage_no="V2026-03",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            state=SCMMeeting.State.SUBMITTED,
            schema_version=1,
            created_by="co-7",
            updated_by="co-7",
        )
        SCMAgendaItem.objects.bulk_create(
            [
                SCMAgendaItem(
                    meeting_id=meeting.id,
                    agenda_item_number=index,
                    section_label=f"Section {index}",
                    auto_populated=False,
                    content=(
                        f"Section {index} notes captured with enough detail for the sign-off preflight test surface."
                    ),
                    decision=f"Decision for section {index}.",
                    schema_version=1,
                )
                for index in range(1, 11)
            ]
        )
        SCMAttendance.objects.create(
            meeting_id=meeting.id,
            crew_id="co-7",
            rank_name="Chief Officer",
            display_name="Chief Officer Seven",
            present=True,
            wrh_data_available=True,
            wrh_non_compliance_flag=False,
            schema_version=1,
        )
        SCMLegacyField.objects.bulk_create(
            [
                SCMLegacyField(
                    meeting_id=meeting.id,
                    agenda_item_number=section_number,
                    field_key=str(field["field_key"]),
                    field_label=str(field["field_label"]),
                    field_type=str(field["field_type"]),
                    field_value="true" if field["field_type"] == "BOOLEAN" else f"{field['field_label']} recorded.",
                    schema_version=1,
                )
                for section_number, fields in SCM_LEGACY_FIELD_TEMPLATE.items()
                if section_number != 10
                for field in fields
                if field.get("required")
            ]
        )
        SCMSignature.objects.create(
            meeting_id=meeting.id,
            signer_role=SCMSignature.SignerRole.CO,
            signer_crew_id="co-7",
            display_name="Chief Officer Seven",
            typed_name="Chief Officer Seven",
            device_fingerprint="device-co-7",
            signed_at=aware(2026, 4, 28, 9, 45),
            created_by="co-7",
            schema_version=1,
        )
        return meeting

    def _insert_area(self, *, area_id: int, area_name: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_soi_area (
                    area_id,
                    area_name,
                    section_12_flag,
                    display_order,
                    active,
                    seeded_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [area_id, area_name, False, area_id, True, "v1.0"],
            )

    def _insert_area_map(
        self,
        *,
        vessel_id: str,
        area_id: int,
        last_inspected_at,
        due_at,
        applicable: bool,
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_vessel_area_map (
                    vessel_id,
                    area_id,
                    applicable,
                    last_inspected_at,
                    due_at,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [vessel_id, area_id, applicable, last_inspected_at, due_at, 1],
            )
