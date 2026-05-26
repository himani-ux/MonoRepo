from __future__ import annotations
from datetime import date, datetime
from types import SimpleNamespace
import uuid
import unittest

from tests.safety.support import bootstrap_django, recreate_scm_tables, recreate_soi_tables


bootstrap_django()

from django.db import connection
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import SCMAgendaItem, SCMAttendance, SCMLegacyField, SCMMeeting, SCMSignature, SafetyFieldHistory
from apps.safety.serializers.scm import SCM_LEGACY_FIELD_TEMPLATE
from apps.safety.services.field_history_recorder import parse_history_value
from apps.safety.services.scm_state_machine import SCMStateMachine
from apps.safety.views.scm_signoff import SCMSignOffView


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


def build_signature_payload() -> dict[str, str]:
    return {
        "typed_name": "Master Seven",
        "device_fingerprint": "device-master-7",
    }


class SCMSignoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_scm_tables()
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.view = SCMSignOffView.as_view()
        self.meeting = self._create_meeting()
        self._insert_area(area_id=3, area_name="Navigating Bridge & Monkey Island")
        self._insert_area_map(
            vessel_id="7",
            area_id=3,
            last_inspected_at="2026-04-28 09:00:00",
            due_at="2026-07-27 09:00:00",
            applicable=True,
        )

    def test_master_signoff_captures_hybrid_signature_and_audit_row(self) -> None:
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/sign-off/",
            build_signature_payload(),
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["state"], SCMMeeting.State.SIGNED_OFF)
        self.assertEqual(response.data["master_signed_off_by"], "master-7")
        self.assertEqual(response.data["signature"]["typed_name"], "Master Seven")
        self.assertEqual(response.data["signature"]["device_fingerprint"], "device-master-7")
        self.assertTrue(response.data["signature"]["signed_at"])
        self.assertEqual(response.data["pdf"]["status"], "generated")
        self.assertEqual(response.data["pdf"]["download_path"], f"/api/safety/scm/{self.meeting.id}/pdf/")
        self.assertTrue(response.data["pdf"]["file_name"].endswith("-scm-legacy.pdf"))

        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.state, SCMMeeting.State.SIGNED_OFF)
        self.assertTrue(self.meeting.pdf_export_path)
        audit_row = SafetyFieldHistory.objects.get(
            parent_table=self.meeting._meta.db_table,
            parent_id=self.meeting.pk,
            field_name="scm_signoff_signature",
        )
        payload = parse_history_value(audit_row.new_value)
        self.assertEqual(payload["typed_name"], "Master Seven")
        self.assertEqual(payload["device_fingerprint"], "device-master-7")
        self.assertEqual(payload["signed_by"], "master-7")
        self.assertEqual(payload["signed_role"], "MASTER")
        self.assertTrue(payload["signed_at"])
        export_row = SafetyFieldHistory.objects.get(
            parent_table=self.meeting._meta.db_table,
            parent_id=self.meeting.pk,
            field_name="scm_pdf_export",
        )
        export_payload = parse_history_value(export_row.new_value)
        self.assertEqual(export_payload["download_path"], f"/api/safety/scm/{self.meeting.id}/pdf/")

    def test_signature_payload_is_required_after_preflight_clears(self) -> None:
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/sign-off/",
            {"typed_name": "", "device_fingerprint": ""},
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("typed_name", response.data)
        self.assertIn("device_fingerprint", response.data)

    def test_signature_device_fingerprint_is_compacted_to_fit_storage(self) -> None:
        long_fingerprint = "Windows|Chrome|user-agent|" + ("x" * 220)

        signature = SCMStateMachine().record_signature(
            self.meeting,
            signer_role=SCMSignature.SignerRole.CO,
            signer_crew_id="co-7",
            display_name="Chief Officer Seven",
            typed_name="Chief Officer Seven",
            device_fingerprint=long_fingerprint,
            signed_at=None,
            user=build_user(role_name="CO", user_id="co-7"),
        )

        self.assertLessEqual(len(signature.device_fingerprint), 128)
        self.assertTrue(signature.device_fingerprint.startswith("sha256:"))

    def test_signoff_blocks_when_agenda_decisions_are_missing(self) -> None:
        SCMAgendaItem.objects.filter(meeting_id=self.meeting.id, agenda_item_number=1).update(decision=None)
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/sign-off/",
            build_signature_payload(),
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 422)
        self.assertIn("agenda", response.data["errors"])

    def test_signoff_blocks_when_meeting_is_not_finalized(self) -> None:
        self.meeting.state = SCMMeeting.State.DRAFT
        self.meeting.save(update_fields=("state",))
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/sign-off/",
            build_signature_payload(),
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 422)
        self.assertIn("state", response.data["errors"])

    def test_signoff_blocks_until_required_co_and_attendee_signatures_exist(self) -> None:
        SCMSignature.objects.filter(meeting_id=self.meeting.id).delete()
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/sign-off/",
            build_signature_payload(),
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 422)
        self.assertIn("signatures", response.data["errors"])

    def test_signoff_blocks_until_master_acknowledges_attendance_warnings(self) -> None:
        SCMAttendance.objects.filter(meeting_id=self.meeting.id, crew_id="co-7").update(
            wrh_non_compliance_flag=True
        )
        request = self.factory.post(
            f"/api/safety/scm/{self.meeting.id}/sign-off/",
            build_signature_payload(),
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=self.meeting.id)

        self.assertEqual(response.status_code, 422)
        self.assertIn("attendance_acknowledged", response.data["errors"])

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
                    content=f"Section {index} notes captured with enough detail for SCM sign-off testing.",
                    decision=f"Decision for section {index}.",
                    schema_version=1,
                )
                for index in range(1, 11)
            ]
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
        SCMSignature.objects.create(
            meeting_id=meeting.id,
            signer_role=SCMSignature.SignerRole.CO,
            signer_crew_id="co-7",
            display_name="Chief Officer Seven",
            typed_name="Chief Officer Seven",
            device_fingerprint="device-co-7",
            signed_at=datetime.fromisoformat("2026-04-28T09:45:00+00:00"),
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
        last_inspected_at: str | None,
        due_at: str | None,
        applicable: bool,
    ) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_vessel_area_map (
                    id,
                    vessel_id,
                    area_id,
                    applicable,
                    last_inspected_at,
                    due_at,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [uuid.uuid4().hex, vessel_id, area_id, applicable, last_inspected_at, due_at, 1],
            )
