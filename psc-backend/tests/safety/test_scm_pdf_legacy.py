from __future__ import annotations

from datetime import date, datetime
from io import BytesIO
import unittest
from unittest.mock import patch

from PyPDF2 import PdfReader

from tests.safety.support import bootstrap_django, recreate_scm_tables


bootstrap_django()

from apps.safety.models import SCMAgendaItem, SCMAttendance, SCMLegacyField, SCMMeeting, SCMSignature, SafetyFieldHistory
from apps.safety.services.pdf_renderer import SCMLegacyPdfRenderer


class FakeSoiFeedService:
    def fetch_for_meeting(self, meeting):
        return {
            "section8": {
                "answer": "YES",
                "inspection_count": 2,
                "coverage_percent": 66.7,
                "summary_text": "Yes - 2 SOI inspection(s) recorded since the prior SCM covering 66.7% of applicable areas.",
            },
            "new_findings": [
                {
                    "inspection_reference": "SOI/ABC/26/004",
                    "title": "Fire door self-closing device weak.",
                    "severity": "MEDIUM",
                    "status": "OPEN",
                    "proposed_action": "Repair self-closing device and verify closure.",
                    "carried_forward_count": 0,
                }
            ],
            "carried_forward_findings": [
                {
                    "inspection_reference": "SOI/ABC/26/003",
                    "title": "Deck lighting guard missing.",
                    "severity": "LOW",
                    "status": "CARRIED_FORWARD",
                    "proposed_action": "Fit replacement guard.",
                    "carried_forward_count": 1,
                }
            ],
        }


class SCMLegacyPdfTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_scm_tables()

    def test_renderer_preserves_locked_legacy_ten_section_order(self) -> None:
        meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="ABC-30-Apr-2026",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=date(2026, 4, 30),
            meeting_time_local="10:00:00",
            location="At Sea",
            voyage_no="VOY-600",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            office_comment="Office review noted for audit completeness.",
            state=SCMMeeting.State.SIGNED_OFF,
            master_signed_off_at=datetime.fromisoformat("2026-04-30T10:45:00+00:00"),
            master_signed_off_by="master-7",
            created_by="co-7",
            updated_by="master-7",
            schema_version=1,
        )
        agenda_labels = [
            "Structured Review",
            "Reserved",
            "Safety Practice",
            "Security",
            "Environment",
            "Health",
            "Crew Welfare",
            "Findings & Corrective Measures",
            "Minutes of Meeting",
            "Office Review",
        ]
        SCMAgendaItem.objects.bulk_create(
            [
                SCMAgendaItem(
                    meeting_id=meeting.id,
                    agenda_item_number=index,
                    section_label=label,
                    auto_populated=False,
                    content=f"{label} notes captured with enough detail for the SCM PDF verification surface.",
                    decision=f"Decision recorded for {label}.",
                    schema_version=1,
                )
                for index, label in enumerate(agenda_labels, start=1)
            ]
        )
        SCMAttendance.objects.bulk_create(
            [
                SCMAttendance(
                    meeting_id=meeting.id,
                    crew_id="crew-1",
                    rank_name="Chief Officer",
                    display_name="Chief Officer One",
                    present=True,
                    wrh_data_available=True,
                    wrh_rest_hours_24h=10.5,
                    wrh_rest_hours_7d=79.0,
                    wrh_non_compliance_flag=False,
                    remarks="Fit for duty.",
                    schema_version=1,
                ),
                SCMAttendance(
                    meeting_id=meeting.id,
                    crew_id="crew-2",
                    rank_name="Bosun",
                    display_name="Bosun Two",
                    present=True,
                    wrh_data_available=False,
                    wrh_rest_hours_24h=None,
                    wrh_rest_hours_7d=None,
                    wrh_non_compliance_flag=False,
                    remarks="WRH data unavailable in workspace test.",
                    schema_version=1,
                ),
            ]
        )
        SCMLegacyField.objects.bulk_create(
            [
                SCMLegacyField(
                    meeting_id=meeting.id,
                    agenda_item_number=1,
                    field_key="previous_minutes_reviewed",
                    field_label="Minutes of previous safety committee reviewed?",
                    field_type=SCMLegacyField.FieldType.BOOLEAN,
                    field_value="true",
                ),
                SCMLegacyField(
                    meeting_id=meeting.id,
                    agenda_item_number=8,
                    field_key="findings10",
                    field_label="Findings 10",
                    field_type=SCMLegacyField.FieldType.TEXT,
                    field_value="Finding 10 observation.",
                ),
                SCMLegacyField(
                    meeting_id=meeting.id,
                    agenda_item_number=8,
                    field_key="correctivemeasure10",
                    field_label="Corrective Measure 10",
                    field_type=SCMLegacyField.FieldType.TEXT,
                    field_value="Corrective measure 10.",
                ),
            ]
        )
        SCMSignature.objects.bulk_create(
            [
                SCMSignature(
                    meeting_id=meeting.id,
                    signer_role=SCMSignature.SignerRole.MASTER,
                    signer_crew_id="master-7",
                    display_name="Master Seven",
                    typed_name="Master Seven",
                    device_fingerprint="device-master-7",
                    signed_at=datetime.fromisoformat("2026-04-30T10:45:00+00:00"),
                    created_by="master-7",
                    schema_version=1,
                ),
                SCMSignature(
                    meeting_id=meeting.id,
                    signer_role=SCMSignature.SignerRole.CO,
                    signer_crew_id="co-7",
                    display_name="Chief Officer One",
                    typed_name="Chief Officer One",
                    device_fingerprint="device-co-7",
                    signed_at=datetime.fromisoformat("2026-04-30T10:20:00+00:00"),
                    created_by="co-7",
                    schema_version=1,
                ),
                SCMSignature(
                    meeting_id=meeting.id,
                    signer_role=SCMSignature.SignerRole.ATTENDEE,
                    signer_crew_id="crew-1",
                    display_name="Chief Officer One",
                    typed_name="Chief Officer One",
                    device_fingerprint="device-attendee-1",
                    signed_at=datetime.fromisoformat("2026-04-30T10:25:00+00:00"),
                    created_by="co-7",
                    schema_version=1,
                ),
                SCMSignature(
                    meeting_id=meeting.id,
                    signer_role=SCMSignature.SignerRole.ATTENDEE,
                    signer_crew_id="crew-2",
                    display_name="Bosun Two",
                    typed_name="Bosun Two",
                    device_fingerprint="device-attendee-2",
                    signed_at=datetime.fromisoformat("2026-04-30T10:26:00+00:00"),
                    created_by="co-7",
                    schema_version=1,
                ),
            ]
        )
        SafetyFieldHistory.objects.create(
            parent_table=meeting._meta.db_table,
            parent_id=meeting.pk,
            field_name="scm_signoff_signature",
            old_value=None,
            new_value={
                "typed_name": "Master Seven",
                "device_fingerprint": "device-master-7",
                "signed_at": "2026-04-30T10:45:00+00:00",
                "signed_by": "master-7",
                "signed_role": "MASTER",
            },
            change_reason="SCM sign-off completed.",
            actor_user_id="master-7",
            actor_role_code="MASTER",
            schema_version=1,
        )

        with patch(
            "apps.safety.services.pdf_renderer.resolve_vessel_display",
            return_value={"vessel_display_name": "MV Test Vessel"},
        ):
            result = SCMLegacyPdfRenderer(soi_feed_service_class=FakeSoiFeedService).render_scm_pdf(
                meeting_id=meeting.pk,
                viewer_user=None,
                persist=False,
            )

        self.assertTrue(result.content.startswith(b"%PDF"))
        self.assertEqual(
            result.section_titles,
            [
                "1. Structured Review",
                "2. Reserved",
                "3. Safety Practice",
                "4. Security",
                "5. Environment",
                "6. Health",
                "7. Crew Welfare",
                "8. Findings & Corrective Measures",
                "9. Minutes of Meeting",
                "10. Office Review",
            ],
        )

        reader = PdfReader(BytesIO(result.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("Safety Committee Meeting Minutes", text)
        self.assertIn("Legacy SCM PDF structure preserved", text)
        self.assertIn("Attendance and WRH Snapshot", text)
        self.assertIn("Closed Items Since Last SCM", text)
        self.assertIn("Document Control and SSOT Alignment", text)
        self.assertIn("Legacy 10-Section SCM Record", text)
        self.assertIn("SOI Feed, Actions, Comments", text)
        self.assertIn("Digital Signatures", text)
        self.assertIn("Chief Officer One", text)
        self.assertIn("Bosun Two", text)
        self.assertIn("Master Seven", text)
        self.assertIn("Chief Officer", text)
        self.assertIn("Attendee Signatures", text)
        self.assertIn("2 of 2 captured", text)
        self.assertNotIn("Device fingerprint", text)
        self.assertIn("SCM No", text)
        self.assertIn("Vessel", text)
        self.assertIn("MV Test Vessel", text)
        self.assertIn("MEETING DATE", text)
        self.assertIn("OCCASION", text)
        self.assertIn("M - Monthly", text)
        self.assertIn("SHIP POSITION", text)
        self.assertIn("P - Port", text)
        self.assertIn("Minutes of previous safety committee reviewed?", text)
        self.assertIn("Safety Observations for the Month", text)
        self.assertIn("SOI/ABC/26/004", text)
        self.assertIn("SOI/ABC/26/003", text)
        self.assertIn("66.7%", text)
        self.assertIn("Fire door self-closing device weak.", text)
        self.assertIn("8. Findings and Corrective Measures", text)
        self.assertIn("Finding 10 observation.", text)
        self.assertIn("Corrective measure 10.", text)
        self.assertIn("Owner", text)
        self.assertIn("Due Date", text)
        self.assertIn("9. Minutes of Meeting", text)
        self.assertIn("10. Office Comments and Review", text)
        self.assertIn("Office Comments", text)
        self.assertIn("SOI Sign-Off Gate", text)
        self.assertIn("Closure Timestamp", text)
        for title in [result.section_titles[index] for index in (0, 2, 3, 4, 5, 6)]:
            self.assertIn(title, text)
        self.assertIn("10. Office Comments and Review", text)
