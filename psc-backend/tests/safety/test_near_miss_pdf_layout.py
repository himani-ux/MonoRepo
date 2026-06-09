from __future__ import annotations

from datetime import datetime
from io import BytesIO
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PyPDF2 import PdfReader

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.services.pdf_renderer import NearMissLightweightPdfRenderer


class NearMissPdfLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()

    def test_renderer_outputs_lightweight_one_to_two_page_template_without_cause_tree_sections(self) -> None:
        near_miss = Incident.objects.create(
            incident_number="NM/2026/042",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="CLOSED",
            current_phase=1,
            incident_type_id=1,
            loss_type_primary_id=1,
            near_miss_priority="HIGH",
            near_miss_severity="MED",
            near_miss_place="AT_PORT",
            near_miss_shell_tag="Safety",
            near_miss_category_tags='["Safety","Operational"]',
            near_miss_incident_type_ids="[1,2]",
            near_miss_mscat_subcode_id="10.01",
            near_miss_mscat_subcode_ids='["10.01","10.02"]',
            occurred_at=datetime.fromisoformat("2026-04-28T09:20:00+00:00"),
            reported_at=datetime.fromisoformat("2026-04-28T09:35:00+00:00"),
            narrative=(
                "A loose staging pin was found on the access ladder before personnel stepped "
                "onto it during rolling conditions, and the area was secured before use."
            ),
            near_miss_immediate_action="The ladder was isolated and tagged until the staging pin was re-secured.",
            near_miss_suggestion="Add a staging pin verification to the deck access checklist.",
            near_miss_root_cause_detail="Pin verification was not included in the pre-use check.",
            near_miss_corrective_action="Checklist updated and bosun briefed the deck team.",
            near_miss_weather_voyage_details="Rolling conditions during port stay.",
            near_miss_equipment_details="Portable staging ladder and securing pin.",
            near_miss_lessons_learned="Verify removable securing pins before exposed work.",
            reporter_id="crew-42",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            reporter_department="Deck",
            closure_reason=(
                "Master and DPA correspondence confirmed the ladder was isolated, the pin was "
                "re-secured, and the local barrier remained effective."
            ),
            created_by="crew-42",
            updated_by="dpa-1",
            schema_version=1,
        )
        IncidentPhaseLog.objects.create(
            incident=near_miss,
            phase_from=1,
            phase_to=1,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            loop_back_reason="Office comment: Near-miss office comments accepted as HIGH.",
            actor_user_id="dpa-1",
            actor_role_code="DPA",
            schema_version=1,
        )
        SafetyFieldHistory.objects.create(
            parent_table=near_miss._meta.db_table,
            parent_id=near_miss.pk,
            field_name="near_miss_rework_resubmission",
            old_value=None,
            new_value={
                "comment": "Updated category, immediate cause, and equipment details after office request.",
                "submitted_by": "crew-42",
                "submitted_role": "REPORTER",
            },
            change_reason="Updated category, immediate cause, and equipment details after office request.",
            actor_user_id="crew-42",
            actor_role_code="REPORTER",
            schema_version=1,
        )
        SafetyFieldHistory.objects.create(
            parent_table=near_miss._meta.db_table,
            parent_id=near_miss.pk,
            field_name="near_miss_vessel_review_signature",
            old_value=None,
            new_value={
                "device_fingerprint": "device-review-42",
                "signed_at": "2026-04-28T09:50:00+00:00",
                "signed_by": "master-7",
                "signed_role": "MASTER",
                "typed_name": "Master Seven",
            },
            change_reason="Near-miss vessel review completed.",
            actor_user_id="master-7",
            actor_role_code="MASTER",
            schema_version=1,
        )
        SafetyFieldHistory.objects.create(
            parent_table=near_miss._meta.db_table,
            parent_id=near_miss.pk,
            field_name="near_miss_closure_signature",
            old_value=None,
            new_value={
                "device_fingerprint": "device-master-42",
                "signed_at": "2026-04-28T10:05:00+00:00",
                "signed_by": "master-7",
                "signed_role": "MASTER",
                "typed_name": "Master Seven",
            },
            change_reason="Near-miss closure completed.",
            actor_user_id="master-7",
            actor_role_code="MASTER",
            schema_version=1,
        )
        SafetyFieldHistory.objects.create(
            parent_table=near_miss._meta.db_table,
            parent_id=near_miss.pk,
            field_name="near_miss_fleet_learning",
            old_value=None,
            new_value="Fleet learning: repeat access-equipment pin checks before exposed work.",
            change_reason="Near-miss fleet learning recorded.",
            actor_user_id="dpa-1",
            actor_role_code="DPA",
            schema_version=1,
        )

        with patch(
            "apps.safety.services.pdf_renderer.resolve_vessel_display",
            return_value={"vessel_code": "ARY", "vessel_name": "MV Arya", "vessel_display_name": "MV Arya"},
        ):
            result = NearMissLightweightPdfRenderer().render_near_miss_pdf(
                incident_id=near_miss.pk,
                viewer_user=SimpleNamespace(role_name="DPA", id="dpa-1"),
                persist=False,
            )

        self.assertTrue(result.content.startswith(b"%PDF"))
        reader = PdfReader(BytesIO(result.content))
        self.assertGreaterEqual(len(reader.pages), 1)
        self.assertLessEqual(len(reader.pages), 2)

        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("Near Miss Report", text)
        self.assertNotIn("FEAT-SAF", text)
        self.assertNotIn("D-GAP", text)
        self.assertNotIn("Document Control", text)
        self.assertIn("What Happened", text)
        self.assertIn("SSOT Summary", text)
        self.assertIn("Preventive Measures", text)
        self.assertIn("Immediate Action", text)
        self.assertIn("High-risk and Learning Details", text)
        self.assertIn("Office Comments and Rework", text)
        self.assertIn("Fleet Learning", text)
        self.assertIn("Closure", text)
        self.assertIn("Signatures", text)
        self.assertIn("Vessel review signature", text)
        self.assertIn("Office review signature", text)
        self.assertIn("Reported by", text)
        self.assertIn("Reporter's rank", text)
        self.assertIn("28 Apr 2026", text)
        self.assertNotIn("Triage signature", text)
        self.assertNotIn("2026-04-28T09:20:00+00:00", text)
        self.assertIn("NM/2026/042", text)
        self.assertIn("MV Arya", text)
        self.assertIn("MED", text)
        self.assertIn("At Port", text)
        self.assertIn("Safety, Operational", text)
        self.assertIn("Near-miss type", text)
        self.assertIn("Possible loss type", text)
        self.assertIn("Immediate cause", text)
        self.assertIn("Crew Reporter", text)
        self.assertIn("staging pin verification", text)
        self.assertIn("Pin verification was not included", text)
        self.assertIn("Checklist updated and bosun briefed", text)
        self.assertIn("Rolling conditions during port stay", text)
        self.assertIn("Portable staging ladder", text)
        self.assertIn("Verify removable securing pins", text)
        self.assertIn("Near-miss office comments accepted as HIGH", text)
        self.assertNotIn("Office comment: Near-miss", text)
        self.assertIn("Updated category, immediate cause", text)
        self.assertIn("repeat access-equipment pin checks", text)
        self.assertIn("barrier remained effective", text)
        self.assertNotIn("Root-Cause Analysis", text)
        self.assertNotIn("Causal-Factor Enumeration", text)
        self.assertNotIn("cause-tree", text.lower())

    def test_renderer_omits_high_risk_learning_section_when_details_are_empty(self) -> None:
        near_miss = Incident.objects.create(
            incident_number="NM/2026/043",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            incident_type_id=1,
            loss_type_primary_id=1,
            near_miss_priority="LOW",
            near_miss_severity="LOW",
            near_miss_place="AT_SEA",
            near_miss_shell_tag="Safety",
            near_miss_category_tags='["Safety"]',
            occurred_at=datetime.fromisoformat("2026-04-28T09:20:00+00:00"),
            reported_at=datetime.fromisoformat("2026-04-28T09:35:00+00:00"),
            narrative=(
                "A toolbox was left near the walkway and was moved before it could create "
                "a trip hazard during routine rounds."
            ),
            near_miss_immediate_action="Toolbox removed from the walkway.",
            near_miss_suggestion="Remind crew to keep walkways clear.",
            reporter_id="crew-43",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            created_by="crew-43",
            updated_by="pic-1",
            schema_version=1,
        )

        with patch(
            "apps.safety.services.pdf_renderer.resolve_vessel_display",
            return_value={"vessel_code": "ARY", "vessel_name": "MV Arya", "vessel_display_name": "MV Arya"},
        ):
            result = NearMissLightweightPdfRenderer().render_near_miss_pdf(
                incident_id=near_miss.pk,
                viewer_user=SimpleNamespace(role_name="DPA", id="dpa-1"),
                persist=False,
            )

        reader = PdfReader(BytesIO(result.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        self.assertIn("SSOT Summary", text)
        self.assertNotIn("High-risk and Learning Details", text)
        self.assertNotIn("Root cause detail", text)
        self.assertNotIn("Corrective action", text)
        self.assertNotIn("Weather / voyage details", text)
        self.assertNotIn("Equipment details", text)
        self.assertNotIn("Lessons learned", text)
