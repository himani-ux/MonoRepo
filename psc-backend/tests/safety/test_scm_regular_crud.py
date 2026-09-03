from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_scm_tables


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate
from django.utils import timezone

from apps.safety.models import SCMAgendaItem, SCMAttendance, SCMLegacyField, SCMMeeting, SCMSignature
from apps.safety.repositories import SCMRepository
from apps.safety.views.scm import SCMDetailView, SCMListCreateView, SCMSubmitView
from apps.safety.views.scm_attendance import SCMAttendanceListCreateView
from apps.safety.views.scm_signature import SCMSignatureView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    user_id: str = "co-7",
):
    return SimpleNamespace(
        id=user_id,
        is_authenticated=True,
        username=user_id,
        role_name=role_name,
        safety_role_name=role_name,
        form_ids=["SAF_F_003"],
        process_ids=["SAF_P_001"] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


def build_sections() -> list[dict[str, object]]:
    return [
        {
            "agenda_item_number": index,
            "content": (
                f"Section {index} discussion notes captured for the handover workspace "
                "with enough detail to satisfy the SCM form expectations."
            ),
            "decision": f"Decision outcome recorded for section {index}.",
        }
        for index in range(1, 10)
    ]


def build_payload() -> dict[str, object]:
    return {
        "attendance_rows": [
            {
                "crew_id": "co-7",
                "display_name": "Chief Officer Seven",
                "present": True,
                "rank_name": "CO",
            },
            {
                "absence_reason": "Engine watch handover overlap",
                "crew_id": "ce-7",
                "display_name": "Chief Engineer Seven",
                "present": False,
                "rank_name": "CE",
                "remarks": "Joining after watch change.",
            },
        ],
        "vessel_id": "7",
        "vessel_code": "ABC",
        "meeting_date": "2026-04-28",
        "meeting_time_local": "10:00:00",
        "location": "Singapore Anchorage",
        "voyage_no": "V2026-03",
        "chair_crew_id": "master-7",
        "sections": build_sections(),
    }


class CountingWRHFetcher:
    def __init__(self) -> None:
        self.fetch_24h_count = 0
        self.fetch_many_count = 0

    def fetch_timezone_offset(self, *, vessel_id, meeting_date):
        return 330

    def fetch_24h_and_7d(self, *, crew_id, meeting_date, vessel_id):
        self.fetch_24h_count += 1
        return {
            "timezone_offset_minutes": 330,
            "warning_codes": [],
            "warnings": [],
            "wrh_data_available": True,
            "wrh_flag": "GREEN",
            "wrh_rest_hours_24h": "12.00",
            "wrh_rest_hours_7d": "77.00",
            "wrh_non_compliance_flag": False,
        }

    def fetch_many_24h_and_7d(self, *, crew_ids, meeting_date, vessel_id):
        self.fetch_many_count += 1
        return {
            str(crew_id): {
                "timezone_offset_minutes": 330,
                "warning_codes": [],
                "warnings": [],
                "wrh_data_available": True,
                "wrh_flag": "GREEN",
                "wrh_rest_hours_24h": "12.00",
                "wrh_rest_hours_7d": "77.00",
                "wrh_non_compliance_flag": False,
            }
            for crew_id in crew_ids
        }


class MissingShipTimeWRHFetcher(CountingWRHFetcher):
    def fetch_timezone_offset(self, *, vessel_id, meeting_date):
        return None

    def fetch_many_24h_and_7d(self, *, crew_ids, meeting_date, vessel_id):
        self.fetch_many_count += 1
        return {
            str(crew_id): {
                "timezone_offset_minutes": None,
                "warning_codes": ["missing_timezone"],
                "warnings": ["WRH ship-time configuration unavailable for this vessel/date."],
                "wrh_data_available": True,
                "wrh_flag": "GREEN",
                "wrh_non_compliance_flag": False,
                "wrh_rest_hours_24h": "12.00",
                "wrh_rest_hours_7d": "77.00",
            }
            for crew_id in crew_ids
        }


class MissingCrewWRHFetcher(CountingWRHFetcher):
    def fetch_many_24h_and_7d(self, *, crew_ids, meeting_date, vessel_id):
        self.fetch_many_count += 1
        return {
            str(crew_id): {
                "timezone_offset_minutes": 330,
                "warning_codes": ["missing_data"] if str(crew_id) == "ce-7" else [],
                "warnings": ["WRH data unavailable for the requested crew/date."] if str(crew_id) == "ce-7" else [],
                "wrh_data_available": str(crew_id) != "ce-7",
                "wrh_flag": "RED" if str(crew_id) == "ce-7" else "GREEN",
                "wrh_non_compliance_flag": False,
                "wrh_rest_hours_24h": None if str(crew_id) == "ce-7" else "12.00",
                "wrh_rest_hours_7d": None if str(crew_id) == "ce-7" else "77.00",
            }
            for crew_id in crew_ids
        }


class FastSCMRepository(SCMRepository):
    wrh_fetcher = CountingWRHFetcher()

    def __init__(self, **kwargs):
        super().__init__(wrh_snapshot_fetcher=self.__class__.wrh_fetcher, **kwargs)


class FastSCMListCreateView(SCMListCreateView):
    repository_class = FastSCMRepository


class FastSCMDetailView(SCMDetailView):
    repository_class = FastSCMRepository


def build_legacy_sections() -> list[dict[str, object]]:
    sections = build_sections()
    legacy_fields: dict[int, dict[str, object]] = {
        1: {
            "previous_minutes_reviewed": True,
            "company_topics_discussed": True,
            "deficiencies_discussed": True,
            "near_misses_discussed": True,
            "immediate_actions_discussed": True,
            "major_incidents_discussed": "N/A",
            "emergency_drills_discussed": True,
        },
        2: {
            "permit_to_work_compliance": True,
            "checklist_system_compliance": True,
            "five_minute_safety_meeting_compliance": True,
            "risk_assessment_management": True,
            "alcohol_policy": True,
            "rest_hours": True,
            "best_practices": "Deck team shared enclosed-space preparation practice.",
            "quality_safety_topic_1": "Mooring safety",
            "quality_safety_topic_2": "Lifting gear",
            "quality_safety_topic_3": "Hot work watch",
        },
        3: {
            "immediate_security_concerns": "No immediate security concerns were raised.",
            "security_best_practices": "Gangway watch handover reinforced.",
            "cyber_security_notes": "USB media control discussed.",
            "latest_circular_safety_alert": "Latest safety alert reviewed.",
            "seq_message": "SEQ reminder discussed.",
        },
        4: {
            "kpi_review": "Environmental KPI trend reviewed.",
            "environment_best_practices": "Garbage segregation practice reinforced.",
        },
        5: {
            "health_review": "Crew health status reviewed.",
            "medical_certificates_healthy": True,
            "weekly_master_inspection": True,
            "mess_committee_meeting": True,
            "health_best_practices": "Hydration checks reinforced.",
        },
        6: {
            "crew_complaint_received": False,
            "matter_status_resolved": True,
            "complaint_form_submitted": True,
            "crew_best_practices": "Crew welfare feedback captured.",
        },
        7: {
            **{f"findings{index}": f"Finding {index} observation." for index in range(1, 11)},
            **{f"correctivemeasure{index}": f"Corrective measure {index}." for index in range(1, 11)},
        },
        8: {
            "miscellaneous_comments": "Miscellaneous safety comments captured.",
        },
        9: {},
    }
    for section in sections:
        section["content"] = ""
        if section["agenda_item_number"] == 9:
            section["decision"] = ""
        section["legacy_fields"] = legacy_fields.get(section["agenda_item_number"], {})
    return sections


class SCMRegularCrudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_scm_tables()
        FastSCMRepository.wrh_fetcher = CountingWRHFetcher()
        self.factory = APIRequestFactory()
        self.list_create_view = FastSCMListCreateView.as_view()
        self.detail_view = SCMDetailView.as_view()
        self.submit_view = SCMSubmitView.as_view()
        self.attendance_view = SCMAttendanceListCreateView.as_view()
        self.signature_view = SCMSignatureView.as_view()

    def test_co_can_create_regular_scm_and_read_it_back(self) -> None:
        create_request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))

        create_response = self.list_create_view(create_request)

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(create_response.data["state"], "DRAFT")
        meeting = SCMMeeting.objects.get(pk=create_response.data["id"])
        self.assertEqual(meeting.meeting_type, "REGULAR")
        self.assertEqual(meeting.prepared_by_crew_id, "co-7")

        detail_request = self.factory.get(f"/api/safety/scm/{create_response.data['id']}/")
        force_authenticate(detail_request, user=build_user(role_name="MASTER", process_ids=[], user_id="master-7"))

        detail_response = self.detail_view(detail_request, id=create_response.data["id"])

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(str(detail_response.data["id"]), str(create_response.data["id"]))
        self.assertEqual(detail_response.data["scm_number"], "ABC-28-Apr-2026")
        self.assertEqual(detail_response.data["sections"], [])
        self.assertEqual(
            SCMAgendaItem.objects.get(meeting_id=meeting.id, agenda_item_number=1).agenda_item_number,
            1,
        )

    def test_master_can_create_regular_scm_with_create_process_id(self) -> None:
        request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(request, user=build_user(role_name="MASTER", user_id="master-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        meeting = SCMMeeting.objects.get(pk=response.data["id"])
        self.assertEqual(meeting.meeting_type, "REGULAR")
        self.assertEqual(meeting.prepared_by_crew_id, "master-7")

    def test_co_can_edit_full_meeting_until_office_review(self) -> None:
        create_request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))
        create_response = self.list_create_view(create_request)
        self.assertEqual(create_response.status_code, 201)

        payload = build_payload()
        payload["location"] = "Edited Singapore Anchorage"
        payload["sections"][0]["content"] = "Edited structured review notes with enough content for validation."
        patch_request = self.factory.patch(
            f"/api/safety/scm/{create_response.data['id']}/",
            payload,
            format="json",
        )
        force_authenticate(
            patch_request,
            user=build_user(role_name="CO", process_ids=["SAF_P_002"], user_id="co-7"),
        )

        response = self.detail_view(patch_request, id=create_response.data["id"])

        self.assertEqual(response.status_code, 200)
        meeting = SCMMeeting.objects.get(pk=create_response.data["id"])
        self.assertEqual(meeting.location, "Edited Singapore Anchorage")
        self.assertEqual(
            SCMAgendaItem.objects.get(meeting_id=meeting.id, agenda_item_number=1).content,
            "Edited structured review notes with enough content for validation.",
        )

    def test_signed_off_meeting_can_be_edited_before_office_review(self) -> None:
        create_request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))
        create_response = self.list_create_view(create_request)
        meeting = SCMMeeting.objects.get(pk=create_response.data["id"])
        meeting.state = SCMMeeting.State.SIGNED_OFF
        meeting.master_signed_off_at = timezone.now()
        meeting.master_signed_off_by = "master-7"
        meeting.save(update_fields=("state", "master_signed_off_at", "master_signed_off_by"))

        payload = build_payload()
        payload["voyage_no"] = "V2026-EDIT"
        patch_request = self.factory.patch(
            f"/api/safety/scm/{meeting.id}/",
            payload,
            format="json",
        )
        force_authenticate(
            patch_request,
            user=build_user(role_name="MASTER", process_ids=["SAF_P_002"], user_id="master-7"),
        )

        response = self.detail_view(patch_request, id=meeting.id)

        self.assertEqual(response.status_code, 200)
        meeting.refresh_from_db()
        self.assertEqual(meeting.voyage_no, "V2026-EDIT")

    def test_office_review_locks_full_meeting_edit(self) -> None:
        create_request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))
        create_response = self.list_create_view(create_request)
        meeting = SCMMeeting.objects.get(pk=create_response.data["id"])
        meeting.office_comment = "Office reviewed."
        meeting.office_comment_at = timezone.now()
        meeting.office_comment_by = "dpa-1"
        meeting.save(update_fields=("office_comment", "office_comment_at", "office_comment_by"))

        patch_request = self.factory.patch(
            f"/api/safety/scm/{meeting.id}/",
            build_payload(),
            format="json",
        )
        force_authenticate(
            patch_request,
            user=build_user(role_name="CO", process_ids=["SAF_P_002"], user_id="co-7"),
        )

        response = self.detail_view(patch_request, id=meeting.id)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["state"][0], "SCM meetings cannot be edited after office review is recorded.")

    def test_master_created_regular_targets_actual_co_for_co_signature(self) -> None:
        create_request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(create_request, user=build_user(role_name="MASTER", user_id="master-7"))
        create_response = self.list_create_view(create_request)
        self.assertEqual(create_response.status_code, 201)

        attendance_request = self.factory.get(f"/api/safety/scm/{create_response.data['id']}/attendance/")
        force_authenticate(
            attendance_request,
            user=build_user(role_name="MASTER", process_ids=["SAF_P_002"], user_id="master-7"),
        )
        attendance_response = self.attendance_view(attendance_request, id=create_response.data["id"])

        self.assertEqual(attendance_response.status_code, 200)
        self.assertEqual(attendance_response.data["co_signature"]["signer_crew_id"], "co-7")

        signature_request = self.factory.post(
            f"/api/safety/scm/{create_response.data['id']}/signatures/",
            {
                "signer_role": "CO",
                "signer_crew_id": "co-7",
                "typed_name": "Chief Officer Seven",
                "device_fingerprint": "device-co-7",
            },
            format="json",
        )
        force_authenticate(
            signature_request,
            user=build_user(role_name="CO", process_ids=["SAF_P_002"], user_id="co-7"),
        )

        signature_response = self.signature_view(signature_request, id=create_response.data["id"])

        self.assertEqual(signature_response.status_code, 200)
        signature = SCMSignature.objects.get(
            meeting_id=create_response.data["id"],
            signer_role=SCMSignature.SignerRole.CO,
        )
        self.assertEqual(signature.signer_crew_id, "co-7")

    def test_regular_create_persists_attendance_rows_in_same_request(self) -> None:
        request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        attendance_rows = list(
            SCMAttendance.objects.filter(meeting_id=response.data["id"]).order_by("crew_id")
        )
        self.assertEqual(len(attendance_rows), 2)
        self.assertEqual(attendance_rows[0].crew_id, "ce-7")
        self.assertFalse(attendance_rows[0].present)
        self.assertEqual(attendance_rows[0].absence_reason, "Engine watch handover overlap")
        self.assertEqual(attendance_rows[1].crew_id, "co-7")
        self.assertTrue(attendance_rows[1].present)

    def test_regular_create_blocks_when_ship_time_is_not_configured(self) -> None:
        FastSCMRepository.wrh_fetcher = MissingShipTimeWRHFetcher()
        request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 400)
        readiness = response.data["wrh_host_readiness"]
        self.assertFalse(readiness["ready"])
        self.assertTrue(readiness["missing_ship_time"])
        self.assertIn("SCM cannot be hosted until ship time is configured for this vessel/date.", readiness["warnings"])
        self.assertEqual(SCMMeeting.objects.count(), 0)

    def test_regular_create_blocks_when_any_attendee_wrh_data_is_missing(self) -> None:
        FastSCMRepository.wrh_fetcher = MissingCrewWRHFetcher()
        request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 400)
        readiness = response.data["wrh_host_readiness"]
        self.assertFalse(readiness["ready"])
        self.assertFalse(readiness["missing_ship_time"])
        self.assertIn("WRH data is unavailable for Chief Engineer Seven.", readiness["warnings"])
        self.assertEqual(readiness["blocking_crew"][0]["crew_id"], "ce-7")
        self.assertEqual(SCMMeeting.objects.count(), 0)

    def test_create_and_edit_batch_wrh_lookup(self) -> None:
        FastSCMRepository.wrh_fetcher = CountingWRHFetcher()
        list_create_view = FastSCMListCreateView.as_view()
        detail_view = FastSCMDetailView.as_view()

        create_request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))

        create_response = list_create_view(create_request)

        self.assertEqual(create_response.status_code, 201)
        self.assertEqual(FastSCMRepository.wrh_fetcher.fetch_24h_count, 0)
        self.assertEqual(FastSCMRepository.wrh_fetcher.fetch_many_count, 2)
        self.assertTrue(
            all(
                row.wrh_data_available
                for row in SCMAttendance.objects.filter(meeting_id=create_response.data["id"])
            )
        )

        payload = build_payload()
        payload["location"] = "Edited no-WRH save location"
        for attendance_row in payload["attendance_rows"]:
            attendance_row["wrh_data_available"] = False
            attendance_row["wrh_rest_hours_24h"] = None
            attendance_row["wrh_rest_hours_7d"] = None
            attendance_row["warning_codes"] = ["missing_data"]
        patch_request = self.factory.patch(
            f"/api/safety/scm/{create_response.data['id']}/",
            payload,
            format="json",
        )
        force_authenticate(
            patch_request,
            user=build_user(role_name="CO", process_ids=["SAF_P_002"], user_id="co-7"),
        )

        patch_response = detail_view(patch_request, id=create_response.data["id"])

        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(FastSCMRepository.wrh_fetcher.fetch_24h_count, 0)
        self.assertEqual(FastSCMRepository.wrh_fetcher.fetch_many_count, 3)
        self.assertTrue(
            all(
                row.wrh_data_available
                for row in SCMAttendance.objects.filter(meeting_id=create_response.data["id"])
            )
        )

    def test_regular_create_derives_chair_and_preparer_from_authenticated_scope(self) -> None:
        payload = build_payload()
        payload["prepared_by_crew_id"] = "spoofed-co"
        payload["chair_crew_id"] = "spoofed-master"
        request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        meeting = SCMMeeting.objects.get(pk=response.data["id"])
        self.assertEqual(meeting.prepared_by_crew_id, "co-7")
        self.assertEqual(meeting.chair_crew_id, "master-7")

    def test_regular_create_requires_location_or_coordinates(self) -> None:
        payload = build_payload()
        payload["location"] = ""
        request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("location", response.data)

    def test_regular_create_accepts_at_sea_coordinates_without_location(self) -> None:
        payload = build_payload()
        payload["meeting_date"] = "2026-04-29"
        payload["location"] = ""
        payload["latitude"] = "1.290270"
        payload["longitude"] = "103.851959"
        request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        meeting = SCMMeeting.objects.get(pk=response.data["id"])
        self.assertIsNone(meeting.location)
        self.assertEqual(str(meeting.latitude), "1.290270")
        self.assertEqual(str(meeting.longitude), "103.851959")

    def test_regular_create_invalid_coordinate_explains_decimal_degrees_format(self) -> None:
        payload = build_payload()
        payload["latitude"] = "north"
        request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            str(response.data["latitude"][0]),
            "Latitude must be in decimal degrees, e.g. 1.290270. "
            "Use a minus sign for south; do not enter N/S letters.",
        )

    def test_create_accepts_structured_legacy_payload_and_renders_section_one(self) -> None:
        payload = build_payload()
        payload.update(
            {
                "occasion": "M",
                "ship_position": "P",
                "ship_pos_from": "Singapore",
                "ship_pos_to": "Fujairah",
                "comm_time": "10:00:00",
                "comp_time": "11:00:00",
                "sections": build_legacy_sections(),
            }
        )
        request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        meeting = SCMMeeting.objects.get(pk=response.data["id"])
        self.assertEqual(meeting.occasion, "M")
        self.assertEqual(meeting.ship_position, "P")
        self.assertEqual(
            SCMLegacyField.objects.get(
                meeting_id=response.data["id"],
                agenda_item_number=1,
                field_key="previous_minutes_reviewed",
            ).field_value,
            "true",
        )
        self.assertEqual(
            SCMLegacyField.objects.get(
                meeting_id=response.data["id"],
                agenda_item_number=1,
                field_key="major_incidents_discussed",
            ).field_value,
            "N/A",
        )

    def test_findings_section_persists_ten_findings_and_corrective_measure_pairs(self) -> None:
        payload = build_payload()
        payload["meeting_date"] = "2026-05-02"
        payload["sections"] = build_legacy_sections()
        request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        section_seven_fields = SCMLegacyField.objects.filter(
            meeting_id=response.data["id"],
            agenda_item_number=7,
        )
        self.assertEqual(section_seven_fields.count(), 20)
        self.assertEqual(
            section_seven_fields.get(field_key="findings10").field_value,
            "Finding 10 observation.",
        )
        self.assertEqual(
            section_seven_fields.get(field_key="correctivemeasure10").field_value,
            "Corrective measure 10.",
        )

    def test_minutes_section_allows_long_text(self) -> None:
        payload = build_payload()
        payload["meeting_date"] = "2026-05-04"
        sections = build_legacy_sections()
        long_minutes = ("Long minutes note with operational detail. " * 300).strip()
        sections[7]["legacy_fields"]["miscellaneous_comments"] = long_minutes
        payload["sections"] = sections
        request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            SCMLegacyField.objects.get(
                meeting_id=response.data["id"],
                agenda_item_number=8,
                field_key="miscellaneous_comments",
            ).field_value,
            long_minutes,
        )
        self.assertIn(
            long_minutes,
            SCMAgendaItem.objects.get(meeting_id=response.data["id"], agenda_item_number=8).content,
        )

    def test_office_review_is_not_required_for_vessel_create(self) -> None:
        payload = build_payload()
        payload["meeting_date"] = "2026-05-03"
        sections = build_legacy_sections()
        sections[8]["legacy_fields"] = {}
        sections[8]["content"] = ""
        sections[8]["decision"] = ""
        payload["sections"] = sections
        request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        meeting = SCMMeeting.objects.get(pk=response.data["id"])
        self.assertIsNone(meeting.office_comment)
        self.assertIsNone(meeting.office_comment_at)

    def test_scm_create_rate_limit_blocks_fourth_creation_for_vessel_day(self) -> None:
        statuses = []
        for index, meeting_date in enumerate(
            ["2026-04-28", "2026-04-29", "2026-04-30", "2026-05-01"], start=1
        ):
            payload = build_payload()
            payload["meeting_date"] = meeting_date
            payload["voyage_no"] = f"V2026-{index:02d}"
            request = self.factory.post("/api/safety/scm/", payload, format="json")
            force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))
            response = self.list_create_view(request)
            statuses.append(response.status_code)
            if response.status_code == 201:
                SCMMeeting.objects.filter(pk=response.data["id"]).update(state=SCMMeeting.State.SUBMITTED)

        self.assertEqual(statuses[:3], [201, 201, 201])
        self.assertEqual(statuses[3], 429)

    def test_co_can_finalize_regular_scm_and_capture_co_signature(self) -> None:
        payload = build_payload()
        payload["sections"] = build_legacy_sections()
        create_request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))
        create_response = self.list_create_view(create_request)
        self.assertEqual(create_response.status_code, 201)

        submit_request = self.factory.post(
            f"/api/safety/scm/{create_response.data['id']}/submit/",
            {"typed_name": "Chief Officer Seven", "device_fingerprint": "device-co-7"},
            format="json",
        )
        force_authenticate(
            submit_request,
            user=build_user(role_name="CO", process_ids=["SAF_P_002"], user_id="co-7"),
        )

        submit_response = self.submit_view(submit_request, id=create_response.data["id"])

        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(submit_response.data["state"], SCMMeeting.State.SUBMITTED)
        signature = SCMSignature.objects.get(meeting_id=create_response.data["id"], signer_role="CO")
        self.assertEqual(signature.signer_crew_id, "co-7")
        self.assertEqual(signature.typed_name, "Chief Officer Seven")

    def test_finalize_accepts_findings_legacy_fields_without_extra_decision(self) -> None:
        payload = build_payload()
        sections = build_legacy_sections()
        sections[6]["decision"] = ""
        payload["sections"] = sections
        create_request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))
        create_response = self.list_create_view(create_request)
        self.assertEqual(create_response.status_code, 201)

        submit_request = self.factory.post(
            f"/api/safety/scm/{create_response.data['id']}/submit/",
            {"typed_name": "Chief Officer Seven", "device_fingerprint": "device-co-7"},
            format="json",
        )
        force_authenticate(
            submit_request,
            user=build_user(role_name="CO", process_ids=["SAF_P_002"], user_id="co-7"),
        )

        submit_response = self.submit_view(submit_request, id=create_response.data["id"])

        self.assertEqual(submit_response.status_code, 200)
        self.assertEqual(submit_response.data["state"], SCMMeeting.State.SUBMITTED)

    def test_finalize_blocks_when_attendance_is_missing(self) -> None:
        payload = build_payload()
        payload["sections"] = build_legacy_sections()
        create_request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))
        create_response = self.list_create_view(create_request)
        self.assertEqual(create_response.status_code, 201)
        SCMAttendance.objects.filter(meeting_id=create_response.data["id"]).delete()

        submit_request = self.factory.post(
            f"/api/safety/scm/{create_response.data['id']}/submit/",
            {"typed_name": "Chief Officer Seven", "device_fingerprint": "device-co-7"},
            format="json",
        )
        force_authenticate(
            submit_request,
            user=build_user(role_name="CO", process_ids=["SAF_P_002"], user_id="co-7"),
        )

        submit_response = self.submit_view(submit_request, id=create_response.data["id"])

        self.assertEqual(submit_response.status_code, 422)
        self.assertIn("attendance", submit_response.data["errors"])

    def test_co_can_capture_present_attendee_signature(self) -> None:
        create_request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))
        create_response = self.list_create_view(create_request)
        request = self.factory.post(
            f"/api/safety/scm/{create_response.data['id']}/signatures/",
            {
                "signer_role": "ATTENDEE",
                "signer_crew_id": "co-7",
                "typed_name": "Chief Officer Seven",
                "device_fingerprint": "device-attendee-co",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="CO", process_ids=["SAF_P_002"], user_id="co-7"),
        )

        response = self.signature_view(request, id=create_response.data["id"])

        self.assertEqual(response.status_code, 200)
        signature = SCMSignature.objects.get(
            meeting_id=create_response.data["id"],
            signer_role=SCMSignature.SignerRole.ATTENDEE,
            signer_crew_id="co-7",
        )
        self.assertEqual(signature.display_name, "Chief Officer Seven")

        attendance_request = self.factory.get(f"/api/safety/scm/{create_response.data['id']}/attendance/")
        force_authenticate(
            attendance_request,
            user=build_user(role_name="CO", process_ids=["SAF_P_002"], user_id="co-7"),
        )
        attendance_response = self.attendance_view(attendance_request, id=create_response.data["id"])

        self.assertEqual(attendance_response.status_code, 200)
        signed_row = next(row for row in attendance_response.data["rows"] if row["crew_id"] == "co-7")
        self.assertEqual(signed_row["signature"]["status"], "SIGNED")
        self.assertEqual(signed_row["signature"]["typed_name"], "Chief Officer Seven")

    def test_master_can_finalize_regular_scm(self) -> None:
        payload = build_payload()
        payload["sections"] = build_legacy_sections()
        create_request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(create_request, user=build_user(role_name="CO", user_id="co-7"))
        create_response = self.list_create_view(create_request)
        request = self.factory.post(
            f"/api/safety/scm/{create_response.data['id']}/submit/",
            {"typed_name": "Master Seven", "device_fingerprint": "device-master-7"},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="MASTER", process_ids=["SAF_P_002"], user_id="master-7"),
        )

        response = self.submit_view(request, id=create_response.data["id"])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["state"], SCMMeeting.State.SUBMITTED)
        self.assertFalse(
            SCMSignature.objects.filter(
                meeting_id=create_response.data["id"],
                signer_role=SCMSignature.SignerRole.CO,
            ).exists()
        )
