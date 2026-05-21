from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace
import uuid
import unittest

from tests.safety.support import (
    bootstrap_django,
    recreate_scm_tables,
    recreate_soi_tables,
)


bootstrap_django()

from django.db import connection
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SCMMeeting, SOIInspection
from apps.safety.views.scm_soi_feed import SCMSoIAutoFeedMeetingView, SOIOpenFindingsVesselView


def build_user(
    *,
    role_name: str = "CO",
    process_ids: list[str] | None = None,
    user_id: str = "co-7",
    vessel_id: str | None = None,
    vessel_ids: list[str] | None = None,
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_003"],
        process_ids=["SAF_P_002"] if process_ids is None else process_ids,
        vessel_id=vessel_id,
        vessel_ids=["7"] if vessel_ids is None else vessel_ids,
        is_global=False,
    )


def aware(year: int, month: int, day: int, hour: int, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


class SCMSoIAutoFeedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_scm_tables()
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.meeting_view = SCMSoIAutoFeedMeetingView.as_view()
        self.vessel_view = SOIOpenFindingsVesselView.as_view()

    def test_meeting_route_splits_new_and_carried_forward_findings(self) -> None:
        self._create_signed_off_meeting(
            meeting_date=date(2026, 4, 1),
            signed_off_at=aware(2026, 4, 1, 10, 0),
            meeting_type=SCMMeeting.MeetingType.REGULAR,
        )
        current_meeting = self._create_meeting(meeting_date=date(2026, 4, 28))
        self._insert_vessel_area_map(area_id=1, last_inspected_at=aware(2026, 4, 10, 8, 0))
        self._insert_vessel_area_map(area_id=2, last_inspected_at=None)

        inspection_id = self._insert_soi_inspection(
            inspection_reference="SOI/ABC/26/01",
            checklist_unique_id="SOI-UID-001",
            reported_at=aware(2026, 4, 10, 8, 0),
        )
        new_finding_id = self._insert_soi_finding(
            inspection_id=inspection_id,
            title="Fresh mooring winch guard finding",
            status="OPEN",
            created_date=aware(2026, 4, 10, 8, 30),
        )
        self._insert_soi_finding(
            inspection_id=inspection_id,
            title="Older open finding before cutoff",
            status="OPEN",
            created_date=aware(2026, 3, 20, 8, 30),
        )
        carried_finding_id = self._insert_soi_finding(
            inspection_id=inspection_id,
            title="Repeated enclosed-space permit finding",
            status="CARRIED_FORWARD",
            created_date=aware(2026, 3, 25, 8, 30),
            carried_forward_count=2,
        )

        request = self.factory.get(f"/api/safety/scm/{current_meeting.id}/auto-feed/")
        force_authenticate(request, user=build_user(role_name="DPA", process_ids=[]))

        response = self.meeting_view(request, id=current_meeting.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meeting_id"], current_meeting.id)
        self.assertEqual(response.data["summary"]["new_count"], 1)
        self.assertEqual(response.data["summary"]["carried_forward_count"], 1)
        self.assertEqual(response.data["summary"]["total_count"], 2)
        self.assertEqual(response.data["section8"]["answer"], "YES")
        self.assertEqual(response.data["section8"]["inspection_count"], 1)
        self.assertEqual(response.data["section8"]["applicable_area_count"], 2)
        self.assertEqual(response.data["section8"]["inspected_area_count"], 1)
        self.assertEqual(response.data["section8"]["coverage_percent"], 50.0)

        self.assertEqual(
            [item["finding_id"] for item in response.data["new_findings"]],
            [new_finding_id],
        )
        self.assertEqual(
            [item["finding_id"] for item in response.data["carried_forward_findings"]],
            [carried_finding_id],
        )

        new_item = response.data["new_findings"][0]
        self.assertEqual(new_item["inspection_reference"], "SOI/ABC/26/01")
        inspection_public_id = SOIInspection.objects.get(pk=inspection_id).public_id
        self.assertEqual(new_item["source_route"], f"/safety/soi/{inspection_public_id}/findings")
        self.assertEqual(new_item["checklist_unique_id"], "SOI-UID-001")

    def test_vessel_route_supports_create_screen_feed_from_latest_signed_off_cutoff(self) -> None:
        self._create_signed_off_meeting(
            meeting_date=date(2026, 4, 1),
            signed_off_at=aware(2026, 4, 1, 10, 0),
            meeting_type=SCMMeeting.MeetingType.REGULAR,
        )
        latest_cutoff = self._create_signed_off_meeting(
            meeting_date=date(2026, 4, 15),
            signed_off_at=aware(2026, 4, 15, 14, 0),
            meeting_type=SCMMeeting.MeetingType.AD_HOC,
            scm_number="ABC-15-Apr-2026",
        )
        inspection_id = self._insert_soi_inspection(
            inspection_reference="SOI/ABC/26/02",
            checklist_unique_id="SOI-UID-002",
            reported_at=aware(2026, 4, 20, 9, 0),
        )
        self._insert_soi_finding(
            inspection_id=inspection_id,
            title="Fire-station hose pressure finding",
            status="OPEN",
            created_date=aware(2026, 4, 20, 9, 15),
        )
        old_inspection_id = self._insert_soi_inspection(
            inspection_reference="SOI/ABC/26/00",
            checklist_unique_id="SOI-UID-000",
            reported_at=aware(2026, 4, 10, 9, 0),
        )
        self._insert_soi_finding(
            inspection_id=old_inspection_id,
            title="Old housekeeping finding before the latest cut-off",
            status="OPEN",
            created_date=aware(2026, 4, 10, 9, 15),
        )

        request = self.factory.get("/api/safety/soi/open-findings/?vessel_id=7")
        force_authenticate(request, user=build_user(role_name="CO", process_ids=[]))

        response = self.vessel_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["meeting_id"])
        self.assertEqual(response.data["cutoff"]["meeting_id"], latest_cutoff.id)
        self.assertEqual(response.data["cutoff"]["meeting_type"], "AD_HOC")
        self.assertEqual(response.data["summary"]["new_count"], 1)
        self.assertEqual(response.data["summary"]["carried_forward_count"], 0)
        self.assertEqual(
            [item["inspection_reference"] for item in response.data["new_findings"]],
            ["SOI/ABC/26/02"],
        )

    def test_vessel_route_defaults_to_uuid_scoped_vessel_when_query_is_omitted(self) -> None:
        vessel_id = "EF9029C2-A192-EF11-A9F2-933342524037"
        latest_cutoff = self._create_signed_off_meeting(
            meeting_date=date(2026, 4, 15),
            signed_off_at=aware(2026, 4, 15, 14, 0),
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            scm_number="ARAYA-15-Apr-2026",
            vessel_id=vessel_id,
        )
        inspection_id = self._insert_soi_inspection(
            inspection_reference="SOI/ARAYA/26/02",
            checklist_unique_id="SOI-ARAYA-002",
            reported_at=aware(2026, 4, 20, 9, 0),
            vessel_id=vessel_id,
        )
        self._insert_soi_finding(
            inspection_id=inspection_id,
            title="Araya bridge checklist gap",
            status="OPEN",
            created_date=aware(2026, 4, 20, 9, 15),
        )

        request = self.factory.get("/api/safety/soi/open-findings/")
        force_authenticate(
            request,
            user=build_user(
                role_name="CO",
                process_ids=[],
                vessel_id=vessel_id,
                vessel_ids=[],
            ),
        )

        response = self.vessel_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["vessel_id"], vessel_id)
        self.assertEqual(response.data["cutoff"]["meeting_id"], latest_cutoff.id)
        self.assertEqual(response.data["summary"]["new_count"], 1)
        self.assertEqual(
            [item["inspection_reference"] for item in response.data["new_findings"]],
            ["SOI/ARAYA/26/02"],
        )

    def test_patch_updates_finding_outcomes_and_refreshes_split_payload(self) -> None:
        meeting = self._create_meeting(meeting_date=date(2026, 4, 28))
        inspection_id = self._insert_soi_inspection(
            inspection_reference="SOI/ABC/26/03",
            checklist_unique_id="SOI-UID-003",
            reported_at=aware(2026, 4, 25, 11, 0),
        )
        new_finding_id = self._insert_soi_finding(
            inspection_id=inspection_id,
            title="Loose storage securing",
            status="OPEN",
            created_date=aware(2026, 4, 25, 11, 10),
        )
        carried_finding_id = self._insert_soi_finding(
            inspection_id=inspection_id,
            title="Repeated toolbox-talk attendance gap",
            status="CARRIED_FORWARD",
            created_date=aware(2026, 4, 24, 10, 0),
            carried_forward_count=1,
        )

        request = self.factory.patch(
            f"/api/safety/scm/{meeting.id}/auto-feed/",
            {
                "outcomes": [
                    {
                        "finding_id": new_finding_id,
                        "next_status": "CARRIED_FORWARD",
                        "decision_note": "Carry forward for the next monthly review.",
                    },
                    {
                        "finding_id": carried_finding_id,
                        "next_status": "CLOSED",
                        "decision_note": "Closed during SCM after Master review of evidence.",
                    },
                ]
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER", user_id="master-7"))

        response = self.meeting_view(request, id=meeting.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            sorted(response.data["updated_finding_ids"]),
            sorted([new_finding_id, carried_finding_id]),
        )

        carried_row = self._fetch_finding_row(new_finding_id)
        self.assertEqual(carried_row["status"], "CARRIED_FORWARD")
        self.assertEqual(carried_row["carried_forward_count"], 1)
        self.assertIsNone(carried_row["closed_at"])
        self.assertIn("Carry forward", carried_row["closure_note"])

        closed_row = self._fetch_finding_row(carried_finding_id)
        self.assertEqual(closed_row["status"], "CLOSED")
        self.assertIsNotNone(closed_row["closed_at"])
        self.assertIn("Closed during SCM", closed_row["closure_note"])

        self.assertEqual(response.data["summary"]["new_count"], 0)
        self.assertEqual(response.data["summary"]["carried_forward_count"], 1)
        self.assertEqual(response.data["summary"]["total_count"], 1)

    def _create_meeting(
        self,
        *,
        meeting_date: date,
        meeting_type: str = SCMMeeting.MeetingType.REGULAR,
        scm_number: str | None = None,
        vessel_id: str = "7",
    ) -> SCMMeeting:
        return SCMMeeting.objects.create(
            vessel_id=vessel_id,
            scm_number=scm_number or f"ABC-{meeting_date.strftime('%d-%b-%Y')}",
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            meeting_time_local=datetime.strptime("10:00:00", "%H:%M:%S").time(),
            location="Singapore Anchorage",
            voyage_no="V2026-03",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            ad_hoc_trigger_reason=(
                "Ad-Hoc trigger reason captured for the Step 3.8 vessel feed."
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
        vessel_id: str = "7",
    ) -> SCMMeeting:
        meeting = self._create_meeting(
            meeting_date=meeting_date,
            meeting_type=meeting_type,
            scm_number=scm_number,
            vessel_id=vessel_id,
        )
        meeting.state = SCMMeeting.State.SIGNED_OFF
        meeting.master_signed_off_at = signed_off_at
        meeting.master_signed_off_by = "master-7"
        meeting.save(update_fields=["state", "master_signed_off_at", "master_signed_off_by"])
        return meeting

    def _insert_vessel_area_map(self, *, area_id: int, last_inspected_at) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_vessel_area_map (
                    public_id,
                    vessel_id,
                    area_id,
                    applicable,
                    last_inspected_at,
                    due_at,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(uuid.uuid4()),
                    "7",
                    area_id,
                    True,
                    last_inspected_at,
                    None,
                    1,
                ],
            )

    def _insert_soi_inspection(
        self,
        *,
        inspection_reference: str,
        checklist_unique_id: str,
        reported_at,
        vessel_id: str = "7",
    ) -> int:
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
                    reported_at,
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(uuid.uuid4()),
                    vessel_id,
                    inspection_reference,
                    "Q2/2026",
                    "REPORTED",
                    "2026-04-18",
                    "so-7",
                    "DECK",
                    "asst-7",
                    "ENGINE",
                    "master-7",
                    checklist_unique_id,
                    reported_at,
                    False,
                    1,
                    False,
                    "so-7",
                ],
            )
            return int(cursor.lastrowid)

    def _insert_soi_finding(
        self,
        *,
        inspection_id: int,
        title: str,
        status: str,
        created_date,
        carried_forward_count: int = 0,
    ) -> int:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_finding (
                    public_id,
                    inspection_id,
                    area_id,
                    title,
                    description,
                    severity,
                    priority,
                    status,
                    carried_forward_count,
                    schema_version,
                    is_deleted,
                    created_by,
                    created_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(uuid.uuid4()),
                    inspection_id,
                    1,
                    title,
                    f"{title} description.",
                    "MED",
                    "MED",
                    status,
                    carried_forward_count,
                    1,
                    False,
                    "so-7",
                    created_date,
                ],
            )
            return int(cursor.lastrowid)

    def _fetch_finding_row(self, finding_id: int) -> dict[str, object]:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    status,
                    carried_forward_count,
                    closed_at,
                    closure_note
                FROM vims_safety_soi_finding
                WHERE id = %s
                """,
                [finding_id],
            )
            row = cursor.fetchone()
        return {
            "status": row[0],
            "carried_forward_count": row[1],
            "closed_at": row[2],
            "closure_note": row[3],
        }
