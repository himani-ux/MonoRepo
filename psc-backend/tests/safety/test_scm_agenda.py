from __future__ import annotations

from datetime import date
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_scm_tables


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import CorrectiveAction, Incident, SCMAgendaItem, SCMMeeting
from apps.safety.views.scm_agenda import SCMAgendaView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    user_id: str = "co-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_003"],
        process_ids=["SAF_P_002"] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


def build_sections() -> list[dict[str, object]]:
    labels = (
        "Structured Review",
        "Quality and Safety Practice",
        "Security",
        "Environment",
        "Health",
        "Crew Welfare",
        "PSC Findings & Corrective Measures",
        "Minutes of Meeting",
        "Office Review",
    )
    return [
        {
            "agenda_item_number": index,
            "section_label": label,
            "content": (
                f"Section {index} discussion notes captured for the agenda route "
                "with enough detail to satisfy the legacy SCM expectations."
            ),
            "decision": f"Decision outcome recorded for section {index}.",
        }
        for index, label in enumerate(labels, start=1)
    ]


class SCMAgendaViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_scm_tables()
        self.factory = APIRequestFactory()
        self.view = SCMAgendaView.as_view()

    def test_get_returns_rows_and_carried_forward_open_actions(self) -> None:
        prior_meeting = self._create_meeting(scm_number="ABC-01-Apr-2026", meeting_date=date(2026, 4, 1))
        prior_row = SCMAgendaItem.objects.get(meeting_id=prior_meeting.id, agenda_item_number=2)
        CorrectiveAction.objects.create(
            source_table="vims_safety_scm_agenda",
            source_id=prior_row.id,
            title="Outstanding lifeboat release gear follow-up",
            description="Open action item carried forward from the previous SCM.",
            assigned_crew_id="chief-officer-7",
            due_date=date(2026, 5, 10),
            status=CorrectiveAction.Status.OPEN,
            created_by="co-7",
            updated_by="co-7",
        )

        current_meeting = self._create_meeting(scm_number="ABC-28-Apr-2026", meeting_date=date(2026, 4, 28))

        request = self.factory.get(f"/api/safety/scm/{current_meeting.id}/agenda/")
        force_authenticate(request, user=build_user(role_name="CO", process_ids=[]))

        response = self.view(request, id=current_meeting.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meeting_id"], current_meeting.id)
        self.assertEqual(len(response.data["rows"]), 9)
        self.assertEqual(response.data["summary"]["carried_forward_count"], 1)
        self.assertEqual(response.data["summary"]["current_action_item_count"], 0)
        self.assertEqual(len(response.data["carried_forward_items"]), 1)
        self.assertEqual(
            response.data["carried_forward_items"][0]["display_status"],
            "CARRIED_FORWARD",
        )
        self.assertEqual(
            response.data["carried_forward_items"][0]["source_scm_number"],
            "ABC-01-Apr-2026",
        )

    def test_office_user_can_read_agenda_payload_without_editor_authority(self) -> None:
        meeting = self._create_meeting(scm_number="ABC-28-Apr-2026", meeting_date=date(2026, 4, 28))

        request = self.factory.get(f"/api/safety/scm/{meeting.id}/agenda/")
        force_authenticate(
            request,
            user=build_user(role_name="OFFICE_PIC", process_ids=[], user_id="office-pic"),
        )

        response = self.view(request, id=meeting.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meeting_id"], meeting.id)
        self.assertEqual(len(response.data["rows"]), 9)

    def test_patch_updates_rows_and_promotes_action_item_to_corrective_action(self) -> None:
        meeting = self._create_meeting(scm_number="ABC-28-Apr-2026", meeting_date=date(2026, 4, 28))

        request = self.factory.patch(
            f"/api/safety/scm/{meeting.id}/agenda/",
            {
                "rows": [
                    {
                        "agenda_item_number": 2,
                        "content": (
                            "Outstanding item review captured with enough detail to remain part "
                            "of the fixed SCM agenda surface."
                        ),
                        "decision": "Create a tracked action item with owner and due date.",
                        "action_item": {
                            "enabled": True,
                            "title": "Close lifeboat release gear gap",
                            "description": "Assign and track the corrective action from the SCM agenda surface.",
                            "assigned_crew_id": "chief-officer-7",
                            "due_date": "2026-05-10",
                        },
                    }
                ]
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.view(request, id=meeting.id)

        self.assertEqual(response.status_code, 200)
        row = next(item for item in response.data["rows"] if item["agenda_item_number"] == 2)
        self.assertEqual(
            row["decision"],
            "Create a tracked action item with owner and due date.",
        )
        self.assertIsNotNone(row["action_item"])
        self.assertEqual(row["action_item"]["display_status"], "OPEN")
        self.assertEqual(row["action_item"]["assigned_crew_id"], "chief-officer-7")

        agenda_row = SCMAgendaItem.objects.get(meeting_id=meeting.id, agenda_item_number=2)
        action = CorrectiveAction.objects.get(
            source_table="vims_safety_scm_agenda",
            source_id=agenda_row.id,
            is_deleted=False,
        )
        self.assertEqual(action.title, "Close lifeboat release gear gap")
        self.assertEqual(action.status, CorrectiveAction.Status.OPEN)
        self.assertEqual(action.assigned_crew_id, "chief-officer-7")
        self.assertEqual(action.created_by, "co-7")

    def test_patch_updates_existing_linked_action_without_creating_duplicate(self) -> None:
        meeting = self._create_meeting(scm_number="ABC-28-Apr-2026", meeting_date=date(2026, 4, 28))
        agenda_row = SCMAgendaItem.objects.get(meeting_id=meeting.id, agenda_item_number=8)
        CorrectiveAction.objects.create(
            source_table="vims_safety_scm_agenda",
            source_id=agenda_row.id,
            title="Initial action title",
            description="Initial action description tied to the SCM agenda row.",
            assigned_crew_id="chief-officer-7",
            due_date=date(2026, 5, 10),
            status=CorrectiveAction.Status.OPEN,
            created_by="co-7",
            updated_by="co-7",
        )

        request = self.factory.patch(
            f"/api/safety/scm/{meeting.id}/agenda/",
            {
                "rows": [
                    {
                        "agenda_item_number": 8,
                        "decision": "Updated decision after further review.",
                        "action_item": {
                            "enabled": True,
                            "title": "Updated action title",
                            "description": "Updated action description after further SCM review.",
                            "assigned_crew_id": "chief-engineer-7",
                            "due_date": "2026-05-20",
                        },
                    }
                ]
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER", user_id="master-7"))

        response = self.view(request, id=meeting.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            CorrectiveAction.objects.filter(
                source_table="vims_safety_scm_agenda",
                source_id=agenda_row.id,
                is_deleted=False,
            ).count(),
            1,
        )
        action = CorrectiveAction.objects.get(
            source_table="vims_safety_scm_agenda",
            source_id=agenda_row.id,
            is_deleted=False,
        )
        self.assertEqual(action.title, "Updated action title")
        self.assertEqual(action.assigned_crew_id, "chief-engineer-7")
        self.assertEqual(str(action.due_date), "2026-05-20")
        self.assertEqual(action.updated_by, "master-7")

    def test_patch_validates_structured_linked_incident_scope(self) -> None:
        meeting = self._create_meeting(scm_number="ABC-28-Apr-2026", meeting_date=date(2026, 4, 28))
        in_scope = Incident.objects.create(
            vessel_id="7",
            incident_number="INC-7",
            schema_version=1,
            created_by="co-7",
        )
        out_of_scope = Incident.objects.create(
            vessel_id="8",
            incident_number="INC-8",
            schema_version=1,
            created_by="co-8",
        )

        valid_request = self.factory.patch(
            f"/api/safety/scm/{meeting.id}/agenda/",
            {"rows": [{"agenda_item_number": 1, "linked_incident_ids": [str(in_scope.id)]}]},
            format="json",
        )
        force_authenticate(valid_request, user=build_user(role_name="CO", user_id="co-7"))
        valid_response = self.view(valid_request, id=meeting.id)

        invalid_request = self.factory.patch(
            f"/api/safety/scm/{meeting.id}/agenda/",
            {"rows": [{"agenda_item_number": 1, "linked_incident_ids": [str(out_of_scope.id)]}]},
            format="json",
        )
        force_authenticate(invalid_request, user=build_user(role_name="CO", user_id="co-7"))
        invalid_response = self.view(invalid_request, id=meeting.id)

        self.assertEqual(valid_response.status_code, 200)
        row = next(item for item in valid_response.data["rows"] if item["agenda_item_number"] == 1)
        self.assertEqual(row["linked_incident_ids"], [str(in_scope.id)])
        self.assertEqual(invalid_response.status_code, 400)
        self.assertIn("linked_incident_ids", invalid_response.data)

    def test_office_user_cannot_patch_agenda_even_with_process_permission(self) -> None:
        meeting = self._create_meeting(scm_number="ABC-28-Apr-2026", meeting_date=date(2026, 4, 28))

        request = self.factory.patch(
            f"/api/safety/scm/{meeting.id}/agenda/",
            {
                "rows": [
                    {
                        "agenda_item_number": 1,
                        "content": "Office-side edit attempt should remain outside the formal SCM workflow.",
                    }
                ]
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="OFFICE_PIC", process_ids=["SAF_P_002"], user_id="office-pic"),
        )

        response = self.view(request, id=meeting.id)

        self.assertEqual(response.status_code, 403)

    def _create_meeting(self, *, scm_number: str, meeting_date: date) -> SCMMeeting:
        meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number=scm_number,
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=meeting_date,
            meeting_time_local="10:00:00",
            location="Singapore Anchorage",
            voyage_no="V2026-03",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            state=SCMMeeting.State.DRAFT,
            schema_version=1,
            created_by="co-7",
            updated_by="co-7",
        )
        SCMAgendaItem.objects.bulk_create(
            [
                SCMAgendaItem(
                    meeting_id=meeting.id,
                    agenda_item_number=int(section["agenda_item_number"]),
                    section_label=str(section["section_label"]),
                    auto_populated=False,
                    content=str(section["content"]),
                    decision=str(section["decision"]),
                    schema_version=1,
                )
                for section in build_sections()
            ]
        )
        return meeting
