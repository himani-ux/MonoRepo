from __future__ import annotations

from datetime import date, datetime
from io import BytesIO
import json
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

    def test_renderer_exports_draft_meeting_without_master_signoff(self) -> None:
        meeting = SCMMeeting.objects.create(
            vessel_id="7",
            scm_number="ABC-29-Apr-2026",
            meeting_type=SCMMeeting.MeetingType.REGULAR,
            meeting_date=date(2026, 4, 29),
            meeting_time_local="10:00:00",
            location="At Sea",
            chair_crew_id="master-7",
            prepared_by_crew_id="co-7",
            state=SCMMeeting.State.DRAFT,
            created_by="co-7",
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
        self.assertEqual(result.meeting_id, meeting.pk)

    def test_renderer_preserves_locked_legacy_section_order(self) -> None:
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
            "Quality and Safety Practice",
            "Security",
            "Environment",
            "Health",
            "Crew Welfare",
            "PSC Findings & Corrective Measures",
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
                    present=False,
                    absence_reason="Shore medical appointment.",
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
                    agenda_item_number=1,
                    field_key="near_miss_discussion_status",
                    field_label="Near miss discussion status",
                    field_type=SCMLegacyField.FieldType.TEXT,
                    field_value=json.dumps(
                        [
                            {
                                "reference": "NM/ABC/2026/001",
                                "title": "Loose ladder pin observed near deck access.",
                                "status": "DISCUSSED",
                                "reason": "",
                            },
                            {
                                "reference": "NM/ABC/2026/002",
                                "title": "Near miss pending crew availability.",
                                "status": "NOT_DISCUSSED",
                                "reason": "Responsible crew member was on watch.",
                            },
                        ]
                    ),
                ),
                SCMLegacyField(
                    meeting_id=meeting.id,
                    agenda_item_number=2,
                    field_key="circular_discussion_status",
                    field_label="Circular / safety alert / work instruction discussion status",
                    field_type=SCMLegacyField.FieldType.TEXT,
                    field_value=json.dumps(
                        [
                            {
                                "srNo": "KSM/Circular/Technical/2026-0008",
                                "title": "Fleet alert reviewed by committee.",
                                "status": "DISCUSSED",
                                "reason": "",
                            }
                        ]
                    ),
                ),
                SCMLegacyField(
                    meeting_id=meeting.id,
                    agenda_item_number=2,
                    field_key="circular_not_discussed_reason",
                    field_label="Reason if not discussed",
                    field_type=SCMLegacyField.FieldType.TEXT,
                    field_value="",
                ),
                SCMLegacyField(
                    meeting_id=meeting.id,
                    agenda_item_number=7,
                    field_key="findings1",
                    field_label="Findings 1",
                    field_type=SCMLegacyField.FieldType.TEXT,
                    field_value="Finding 1 observation.",
                ),
                SCMLegacyField(
                    meeting_id=meeting.id,
                    agenda_item_number=7,
                    field_key="correctivemeasure1",
                    field_label="Corrective Measure 1",
                    field_type=SCMLegacyField.FieldType.TEXT,
                    field_value="Corrective measure 1.",
                ),
                SCMLegacyField(
                    meeting_id=meeting.id,
                    agenda_item_number=7,
                    field_key="findings2",
                    field_label="Findings 2",
                    field_type=SCMLegacyField.FieldType.TEXT,
                    field_value="Finding 2 observation.",
                ),
                SCMLegacyField(
                    meeting_id=meeting.id,
                    agenda_item_number=7,
                    field_key="correctivemeasure2",
                    field_label="Corrective Measure 2",
                    field_type=SCMLegacyField.FieldType.TEXT,
                    field_value="Corrective measure 2.",
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
                "2. Quality and Safety Practice",
                "3. Security",
                "4. Environment",
                "5. Health",
                "6. Crew Welfare",
                "7. PSC Findings & Corrective Measures",
                "8. Minutes of Meeting",
                "9. Office Review",
            ],
        )

        reader = PdfReader(BytesIO(result.content))
        page_texts = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(page_texts)
        self.assertIn("Safety Committee Meeting Minutes", text)
        self.assertIn("Attendance and WRH Snapshot", text)
        self.assertIn("Closed Items Since Last SCM", text)
        self.assertIn("Safety Committee Meeting Record", text)
        self.assertIn("Safety Committee Meeting Record", text)
        self.assertNotIn("Document Control", text)
        self.assertNotIn("SSOT", text)
        self.assertNotIn("D-PDF", text)
        self.assertIn("SOI Feed, Actions, Comments", text)
        self.assertNotIn("Digital Signatures", text)
        self.assertNotIn("Digital Signature Status", text)
        self.assertIn("Signatures", text)
        self.assertIn("Master Signature", text)
        self.assertIn("Chief Officer Signature", text)
        self.assertIn("Name / Date", text)
        self.assertIn("Remarks", text)
        self.assertIn("Chief Officer One", text)
        self.assertIn("Bosun Two", text)
        self.assertIn("Absent - Reason", text)
        self.assertIn("Shore medical", text)
        self.assertIn("appointment.", text)
        self.assertNotIn("Master Seven", text)
        self.assertIn("Chief Officer", text)
        self.assertNotIn("Attendee Signatures", text)
        self.assertNotIn("2 of 2 captured", text)
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
        self.assertIn("Recommendation /", text)
        self.assertIn("Suggestions", text)
        self.assertIn("Decision recorded for Structured Review.", text)
        self.assertIn("Decision recorded for Quality and Safety Practice.", text)
        self.assertIn("Decision recorded for Security.", text)
        self.assertIn("Decision recorded for Environment.", text)
        self.assertIn("Decision recorded for Health.", text)
        self.assertIn("Decision recorded for Crew Welfare.", text)
        self.assertIn("NM/ABC/2026/001", text)
        self.assertIn("Loose ladder pin observed near deck", text)
        self.assertIn("access.", text)
        self.assertIn("NM/ABC/2026/002", text)
        self.assertIn("Responsible crew member was on", text)
        self.assertIn("watch.", text)
        self.assertNotIn("Quality & Safety topic 1", text)
        self.assertNotIn("Quality & Safety topic 2", text)
        self.assertNotIn("Quality & Safety topic 3", text)
        self.assertIn("Reference", text)
        self.assertIn("KSM/Circular/Techni", text)
        self.assertIn("cal/2026-0008", text)
        self.assertIn("Fleet alert reviewed by committee.", text)
        self.assertNotIn("circular_discussion_status", text)
        self.assertNotIn('"status"', text)
        self.assertIn("Finding 1 observation", text)
        self.assertIn("Finding 2 observation", text)
        self.assertNotIn("Findings 10", text)
        self.assertNotIn("Safety Observations for the Month", text)
        self.assertLess(text.index("Closed Items Since Last SCM"), text.index("Safety Committee Meeting Record"))
        self.assertLess(text.index("Safety Committee Meeting Record"), text.index("SOI Feed, Actions, Comments, Signatures"))
        self.assertLess(text.index("SOI Feed, Actions, Comments, Signatures"), text.index("1. Structured Review"))
        self.assertIn("66.7%", text)
        self.assertNotIn("SOI/ABC/26/004", text)
        self.assertNotIn("SOI/ABC/26/003", text)
        self.assertNotIn("Fire door self-closing device weak.", text)
        self.assertNotIn("Deck lighting guard missing.", text)
        self.assertNotIn("8. Safety Observations for the Month", text)
        self.assertIn("7. PSC Findings & Corrective Measures", text)
        self.assertIn("Finding 1 observation.", text)
        self.assertIn("Corrective measure 1.", text)
        self.assertNotIn("TBD", text)
        self.assertIn("8. Minutes of Meeting", text)
        self.assertNotIn("Decision recorded for Minutes of Meeting.", text)
        self.assertNotIn("Decision / Action", text)
        self.assertIn("9. Office Comments and Review", text)
        self.assertIn("Office Comments", text)
        self.assertNotIn("SOI Sign-Off Gate", text)
        self.assertIn("Review", text)
        self.assertIn("Closure Timestamp", text)
        for title in [result.section_titles[index] for index in (0, 1, 2, 3, 4, 5)]:
            self.assertIn(title, text)
        self.assertIn("9. Office Comments and Review", text)
