from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
import unittest

from PyPDF2 import PdfReader
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from django.db import connection

from apps.safety.models import (
    CorrectiveAction,
    EvidenceItem,
    ExternalPartyInjury,
    Incident,
    IncidentCauseTag,
    IncidentEvidence,
    IncidentFact,
    IncidentLossEvaluation,
    IncidentWeatherOption,
    Recommendation,
    RecommendationVerification,
    WitnessInterview,
)
from apps.safety.services.pdf_renderer import IncidentPdfRenderer
from apps.safety.services.pdf_templates.incident_10_section import (
    IncidentPdfContext,
    IncidentPdfDetailBlock,
    IncidentTenSectionTemplate,
)


class IncidentPdfSectionTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()

    def test_pdf_report_title_style_is_centered_and_bold(self) -> None:
        template = IncidentTenSectionTemplate()

        self.assertEqual(template.title_style.alignment, TA_CENTER)
        self.assertEqual(template.title_style.fontName, "Helvetica-Bold")

    def test_summary_table_odd_rows_do_not_render_filler_not_recorded(self) -> None:
        template = IncidentTenSectionTemplate()

        rows = template._paired_summary_rows([("Generated at", "01 Jul 2026, 05:28")])

        self.assertEqual(
            [cell.getPlainText() for cell in rows[0]],
            ["Generated at", "01 Jul 2026, 05:28", "", ""],
        )

    def test_full_width_detail_block_uses_single_column_without_filler_label(self) -> None:
        template = IncidentTenSectionTemplate()
        comment = (
            "Closure comment with  two spaces and no separate field label. "
            + "This sentence is intentionally repeated to exceed the generic chunk threshold. " * 20
            + "\nTyped second line remains part of the same comment block."
        )

        story = template._build_detail_blocks(
            [
                IncidentPdfDetailBlock(
                    "Office comments/ lesson learnt",
                    [("", comment)],
                )
            ]
        )

        table = story[0]
        self.assertEqual(table._colWidths, [170 * mm])
        self.assertEqual(len(table._cellvalues), 2)
        self.assertEqual(table._cellvalues[0][0].getPlainText(), "Office comments/ lesson learnt")
        self.assertIn("with &#160;two spaces", template._format_plain_text_preserving_spacing(comment))
        content_text = table._cellvalues[1][0].getPlainText()
        self.assertIn("Closure comment with", content_text)
        self.assertIn("two spaces and no separate field label.", content_text)
        self.assertIn("Typed second line remains part of the same comment block.", content_text)

    def test_renderer_outputs_incident_report_without_duplicate_sections(self) -> None:
        incident = Incident.objects.create(
            incident_number="KSM-INC-2026-0042",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.YELLOW,
            imo_classifier=Incident.ImoClassifier.MC,
            occurred_at=datetime.fromisoformat("2026-04-27T10:15:00+00:00"),
            reported_at=datetime.fromisoformat("2026-04-27T11:30:00+00:00"),
            vessel_location="In Port",
            vessel_location_detail="Singapore",
            reporter_id="rep-7",
            reporter_name="Reporter Seven",
            reporter_rank="Chief Officer",
            reporter_device_fingerprint="device-reporter-7",
            narrative="Engine-room slip while inspecting purifier platform. Containment established and review started.",
            pic_user_id="pic-7",
            dpa_accepted_by="dpa-7",
            dpa_accepted_at=datetime.fromisoformat("2026-04-28T08:00:00+00:00"),
            office_comment="Office reviewed and accepted with loss evaluation pending.",
            closure_reason="DPA accepted the corrective actions and closed the incident after final review.",
            created_by="rep-7",
            updated_by="dpa-7",
            schema_version=1,
        )
        evidence_tab = IncidentEvidence.objects.create(
            incident=incident,
            tab_code=IncidentEvidence.TabCode.PEOPLE,
            summary="Witness statements and bridge call log captured.",
            entry_count=2,
            created_by="rep-7",
            schema_version=1,
        )
        evidence_item = EvidenceItem.objects.create(
            incident=incident,
            evidence_tab=evidence_tab,
            item_type=EvidenceItem.ItemType.MATRIX,
            title="Purifier platform condition",
            description="Oil residue observed on ladder edge.",
            source_label="Photo set A",
            finding="Slip hazard confirmed.",
            pro_evidence="Crew statements and deck log support the timing.",
            comments="Retain for appendix.",
            metadata_json={"attachment_path": "vessels/7/incidents/KSM-INC-2026-0042/phase-3/photo-set-a.jpg"},
            created_by="rep-7",
            schema_version=1,
        )
        fact = IncidentFact.objects.create(
            incident=incident,
            sequence_index=1,
            fact_text="Purifier platform inspection started before the morning toolbox talk concluded.",
            fact_timestamp=datetime.fromisoformat("2026-04-27T10:10:00+00:00"),
            source_evidence_id=evidence_item.pk,
            created_by="rep-7",
            schema_version=1,
        )
        IncidentCauseTag.objects.create(
            incident=incident,
            cause_factor="MANAGEMENT",
            source_fact=fact,
            mscat_subcode_id="M-101",
            causal_layer=IncidentCauseTag.CausalLayer.ROOT,
            analysis_tool=IncidentCauseTag.AnalysisTool.STEP,
            rationale="Permit controls did not cover the oily ladder condition.",
            created_by="dpa-7",
            schema_version=1,
        )
        second_fact = IncidentFact.objects.create(
            incident=incident,
            sequence_index=2,
            fact_text="A housekeeping check was delayed until after the task began.",
            fact_timestamp=datetime.fromisoformat("2026-04-27T10:12:00+00:00"),
            source_evidence_id=evidence_item.pk,
            created_by="rep-7",
            schema_version=1,
        )
        IncidentCauseTag.objects.create(
            incident=incident,
            source_fact=second_fact,
            mscat_subcode_id="M-102",
            causal_layer=IncidentCauseTag.CausalLayer.ROOT,
            analysis_tool=IncidentCauseTag.AnalysisTool.STEP,
            rationale="The area was not rechecked before work started.",
            created_by="dpa-7",
            schema_version=1,
        )
        lessons_recommendation = Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.LESSONS_LEARNT,
            title="Fleet ladder-condition alert",
            description="Issue a ladder housekeeping lesson to all vessels.",
            rationale="The same purifier ladder layout exists fleet-wide.",
            created_by="dpa-7",
            schema_version=1,
        )
        corrective_recommendation = Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Replace anti-slip strip",
            description="Fit a new anti-slip strip.",
            created_by="dpa-7",
            schema_version=1,
        )
        preventive_recommendation = Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.PREVENTIVE,
            title="Improve housekeeping inspection",
            description="Add housekeeping verification before purifier work.",
            created_by="dpa-7",
            schema_version=1,
        )
        corrective_action = CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=incident.pk,
            recommendation=corrective_recommendation,
            title="Replace anti-slip edge strip",
            description="Fit a new anti-slip strip and inspect adjacent access points.",
            due_date=date(2026, 5, 10),
            status=CorrectiveAction.Status.IN_PROGRESS,
            physical_verification_note="Vessel later confirmed the strip was fitted.",
            closed_at=datetime.fromisoformat("2026-05-12T08:30:00+00:00"),
            created_by="dpa-7",
            schema_version=1,
        )
        CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=incident.pk,
            recommendation=preventive_recommendation,
            title="Add housekeeping verification",
            description="Add a pre-job housekeeping verification before purifier platform work.",
            due_date=date(2026, 5, 15),
            status=CorrectiveAction.Status.OPEN,
            physical_verification_note="Preventive verification is intentionally not printed.",
            created_by="dpa-7",
            schema_version=1,
        )
        RecommendationVerification.objects.create(
            recommendation=corrective_recommendation,
            is_effective=False,
            residual_risk="MEDIUM",
            verified_by="dpa-7",
            notes="Awaiting vessel close-out confirmation.",
        )

        renderer = IncidentPdfRenderer()
        context = renderer._build_context(incident)
        actions_by_heading = {block.heading: block for block in context.action_blocks}
        self.assertEqual(
            actions_by_heading["Corrective Actions"].rows,
            [
                (
                    "",
                    "Fit a new anti-slip strip and inspect adjacent access points.\nDue Date: 2026-05-10",
                )
            ],
        )
        self.assertEqual(
            actions_by_heading["Preventive Actions"].rows,
            [
                (
                    "",
                    "Add a pre-job housekeeping verification before purifier platform work.\nDue Date: 2026-05-15",
                )
            ],
        )

        result = renderer.render_incident_pdf(incident_id=incident.pk, viewer_user=None, persist=False)

        self.assertTrue(result.content.startswith(b"%PDF"))
        self.assertEqual(result.section_titles, [
            "Summary",
            "Reporter Details",
            "Injury Details",
            "Root Cause Analysis",
            "Corrective and Preventive Actions",
            "Evidence (Documents)",
            "Lessons Learned",
            "Signature",
            "Estimated Cost",
        ])

        reader = PdfReader(BytesIO(result.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertLess(text.index("Incident Report"), text.index("Summary"))
        for title in [
            "Summary",
            "Reporter Details",
            "Root Cause Analysis",
            "Evidence (Documents)",
            "Corrective and Preventive Actions",
            "Lessons Learned",
        ]:
            self.assertIn(title, text)
        self.assertIn("KSM-INC-2026-0042", text)
        self.assertIn("Root Cause Analysis", text)
        self.assertNotIn("Attachments", text)
        self.assertNotIn("Attachment 1", text)
        self.assertNotIn("Document 1", text)
        self.assertNotIn("Evidence item - Purifier platform condition", text)
        self.assertNotIn("Slip hazard confirmed.", text)
        self.assertNotIn("Crew statements and deck log support the timing.", text)
        self.assertNotIn("Retain for appendix.", text)
        self.assertIn("Purifier platform condition", text)
        self.assertIn("photo-set-a.jpg", text)
        self.assertIn("Vessel location", text)
        self.assertIn("In Port - Singapore", text)
        self.assertNotIn("Specific vessel", text)
        self.assertNotIn("Fleet ladder-condition alert", text)
        self.assertNotIn("Corrective action - Replace anti-slip edge strip", text)
        self.assertIn("Corrective Actions", text)
        self.assertIn("Preventive Actions", text)
        self.assertNotIn("Corrective action", text)
        self.assertLess(
            text.index("Corrective Actions\nFit a new anti-slip strip"),
            text.index("Preventive Actions\nAdd a pre-job housekeeping verification"),
        )
        self.assertLess(
            text.index("Preventive Actions\nAdd a pre-job housekeeping verification"),
            text.index("Evidence (Documents)"),
        )
        self.assertIn("Fit a new anti-slip strip and inspect adjacent access points.", text)
        self.assertIn("Due Date:", text)
        self.assertNotIn("Due date:", text)
        self.assertIn("2026-05-10", text)
        self.assertIn("Add a pre-job housekeeping verification before purifier platform", text)
        self.assertIn("work.", text)
        self.assertIn("2026-05-15", text)
        self.assertNotIn("Status:", text)
        self.assertNotIn("In Progress", text)
        self.assertNotIn("Physical verification note", text)
        self.assertNotIn("Vessel later confirmed the strip was fitted.", text)
        self.assertNotIn("Preventive verification is intentionally not printed.", text)
        self.assertNotIn("Closed at:", text)
        self.assertNotIn("12 May 2026", text)
        self.assertNotIn("Verification 1", text)
        self.assertNotIn("Awaiting vessel close-out confirmation.", text)
        self.assertIn("27 Apr 2026", text)
        self.assertLess(text.index("Summary"), text.index("Engine-room slip while inspecting purifier platform"))
        self.assertLess(text.index("Engine-room slip while inspecting purifier platform"), text.index("Root Cause Analysis"))
        self.assertEqual(text.count("Root Cause Analysis"), 1)
        self.assertNotIn("Cause 1", text)
        self.assertNotIn("Cause 2", text)
        self.assertIn("Cause factor", text)
        self.assertIn("Management", text)
        self.assertIn("Cause", text)
        self.assertNotIn("Cause option", text)
        self.assertNotIn("Management Factor", text)
        self.assertNotIn("Vessel Factor", text)
        self.assertNotIn("Human Factor", text)
        self.assertIn("Reason", text)
        self.assertNotIn("Rationale:", text)
        self.assertNotIn("Other detail", text)
        self.assertNotIn("Source fact", text)
        self.assertNotIn("M-SCAT category", text)
        self.assertEqual(text.count("Issue a ladder housekeeping lesson to all vessels."), 1)
        self.assertNotIn("The same purifier ladder layout exists fleet-wide.", text)
        self.assertIn("Office comments/ lesson learnt", text)
        self.assertIn("Office reviewed and accepted with loss evaluation pending.", text)
        self.assertNotIn("\nComment\n", text)
        self.assertNotIn("Closure reason", text)
        self.assertNotIn("DPA accepted the corrective actions and closed the incident after final review.", text)
        self.assertLess(text.index("Lessons Learned"), text.index("Office comments/ lesson learnt"))
        self.assertLess(text.index("Office comments/ lesson learnt"), text.index("Signature"))
        self.assertNotIn("Master signature", text)
        self.assertNotIn("HOD signature", text)
        self.assertIn("PIC / DPA office", text)
        self.assertNotIn("Recommendation - Fleet ladder-condition alert", text)
        self.assertNotIn("Prepared by", text)
        self.assertNotIn("8. Office Review and Fleet Alert", text)
        self.assertNotIn("10. Attachments and Appendix", text)
        self.assertNotIn("Step 6.1", text)
        self.assertNotIn("internal 10-section contract", text)
        self.assertNotIn("Narrative owner", text)

    def test_pdf_title_switches_to_injury_report_when_injury_is_recorded(self) -> None:
        incident = self._create_exportable_incident("KSM-INC-2026-INJURY")
        incident.shore_assistance_required = True
        incident.vessel_location = "At sea"
        incident.onboard_location = "Main deck"
        incident.last_port = "Incident Legacy Last Port"
        incident.departure_date = "2026-06-03"
        incident.vessel_condition = "LOADED"
        incident.save(
            update_fields=[
                "shore_assistance_required",
                "vessel_location",
                "onboard_location",
                "last_port",
                "departure_date",
                "vessel_condition",
            ]
        )
        ExternalPartyInjury.objects.create(
            incident=incident,
            injured_person_type=ExternalPartyInjury.InjuredPersonType.CREW,
            crew_rank="Chief Officer",
            crew_activity_type="Hot work",
            what_happened_narrative="Crew member cut hand while preparing hot work shielding.",
            nature_of_injury="Cuts / Lacerations",
            source_of_injury="Sharp edge",
            affected_body_areas="Right hand",
            last_port="Injury Legacy Last Port",
            first_aid_details="Wound cleaned and dressed onboard.",
            why_it_happened_analysis="Sharp edge was not identified during pre-job inspection.",
            risk_assessment_carried_out="YES",
            toolbox_meeting_carried_out="NO",
            prevention_action_taken_required="Deburr edge and refresh hot work preparation checklist.",
            ocimf_first_aid_case=True,
            cost_medicines_onboard=Decimal("123.45"),
            cost_doctor_visits=Decimal("50.00"),
            total_estimated_cost=Decimal("173.45"),
            created_by="rep-7",
            schema_version=1,
        )

        result = IncidentPdfRenderer().render_incident_pdf(incident_id=incident.pk, viewer_user=None, persist=False)

        text = self._extract_pdf_text(result.content)
        self.assertIn("Injury Report", text)
        self.assertLess(text.index("Injury Report"), text.index("Summary"))
        self.assertRegex(text, r"Describe What\s+happened\?")
        self.assertIn("Incident report title regression check.", text)
        self.assertLess(text.index("Reporter Details"), text.index("Describe What"))
        self.assertLess(text.index("Describe What"), text.index("Injury Details"))
        self.assertLess(text.index("Reporter Details"), text.index("Incident report title regression check."))
        self.assertLess(text.index("Incident report title regression check."), text.index("Injury Details"))
        self.assertIn("Injury details", text)
        self.assertIn("Type of activity", text)
        self.assertIn("Hot work", text)
        self.assertIn("Shore assistance", text)
        self.assertIn("At sea", text)
        self.assertIn("Main deck", text)
        self.assertNotIn("Last port", text)
        self.assertNotIn("Incident Legacy Last Port", text)
        self.assertNotIn("Injury Legacy Last Port", text)
        self.assertIn("Loaded", text)
        self.assertNotIn("Crew member cut hand while preparing hot work shielding.", text)
        self.assertIn("Cuts / Lacerations", text)
        self.assertIn("Right hand", text)
        self.assertIn("Injury investigation", text)
        self.assertIn("Sharp edge was not identified during pre-job inspection.", text)
        self.assertIn("OCIMF injury reporting", text)
        self.assertIn("Estimated injury costs", text)
        self.assertIn("Total estimated cost", text)
        self.assertIn("173.45", text)
        self.assertNotIn("Formal Incident Report", text)

    def test_pdf_title_stays_incident_report_without_injury_record(self) -> None:
        incident = self._create_exportable_incident("KSM-INC-2026-NO-INJURY")

        result = IncidentPdfRenderer().render_incident_pdf(incident_id=incident.pk, viewer_user=None, persist=False)

        text = self._extract_pdf_text(result.content)
        self.assertIn("Incident Report", text)
        self.assertLess(text.index("Incident Report"), text.index("Summary"))
        self.assertNotIn("Injury Report", text)

    def test_pdf_selected_sections_filter_report_content(self) -> None:
        incident = self._create_exportable_incident("KSM-INC-2026-FILTERED")
        ExternalPartyInjury.objects.create(
            incident=incident,
            injured_person_type=ExternalPartyInjury.InjuredPersonType.CREW,
            crew_rank="Chief Officer",
            crew_activity_type="Hot work",
            what_happened_narrative="Crew member cut hand while preparing hot work shielding.",
            total_estimated_cost=Decimal("173.45"),
            created_by="rep-7",
            schema_version=1,
        )

        result = IncidentPdfRenderer().render_incident_pdf(
            incident_id=incident.pk,
            viewer_user=None,
            persist=False,
            included_sections=["summary", "injury_details"],
        )

        text = self._extract_pdf_text(result.content)
        self.assertEqual(result.section_titles, ["Summary", "Injury Details"])
        self.assertIn("Injury Report", text)
        self.assertIn("Summary", text)
        self.assertIn("Injury Details", text)
        self.assertNotIn("Crew member cut hand while preparing hot work shielding.", text)
        self.assertNotIn("Reporter Details", text)
        self.assertNotIn("Estimated Cost", text)
        self.assertNotIn("Total estimated cost", text)
        self.assertNotIn("Root Cause Analysis", text)
        self.assertNotIn("Evidence (Documents)", text)

    def test_pdf_estimated_cost_prints_loss_evaluation(self) -> None:
        incident = self._create_exportable_incident("KSM-INC-2026-LOSS-EVAL")
        IncidentLossEvaluation.objects.create(
            incident=incident,
            report_type=IncidentLossEvaluation.ReportType.INCIDENT,
            consequence=IncidentLossEvaluation.Consequence.MAJOR,
            likelihood=IncidentLossEvaluation.Likelihood.POSSIBLE,
            risk_level=IncidentLossEvaluation.RiskLevel.HIGH,
            name_of_master="Master One",
            name_of_chief_engineer="Chief Engineer One",
            repair_type=IncidentLossEvaluation.RepairType.TEMPORARY,
            repair_details="Temporary repair completed onboard.",
            delay_to_vessel="Six hours alongside.",
            estimated_cost_off_hire=Decimal("100.00"),
            estimated_cost_delay=Decimal("50.00"),
            total_estimated_cost=Decimal("150.00"),
            created_by="dpa-7",
            schema_version=1,
        )

        result = IncidentPdfRenderer().render_incident_pdf(
            incident_id=incident.pk,
            viewer_user=None,
            persist=False,
            included_sections=["estimated_cost"],
        )

        text = self._extract_pdf_text(result.content)
        self.assertEqual(result.section_titles, ["Estimated Cost"])
        self.assertIn("Risk Assessment", text)
        self.assertIn("Major", text)
        self.assertIn("Possible", text)
        self.assertIn("High", text)
        self.assertIn("Details", text)
        self.assertNotIn("Other Details", text)
        self.assertIn("Master One", text)
        self.assertIn("Temporary repair completed onboard.", text)
        self.assertIn("Cost Evaluation", text)
        self.assertIn("Estimated Costs", text)
        self.assertNotIn("Loss Evaluation -", text)
        self.assertIn("150.00", text)

    def test_pdf_loss_evaluation_uses_saved_report_type_over_injury_presence(self) -> None:
        incident = self._create_exportable_incident("KSM-INC-2026-LOSS-TYPE")
        ExternalPartyInjury.objects.create(
            incident=incident,
            injured_person_type=ExternalPartyInjury.InjuredPersonType.CREW,
            created_by="rep-7",
            schema_version=1,
        )
        IncidentLossEvaluation.objects.create(
            incident=incident,
            report_type=IncidentLossEvaluation.ReportType.INCIDENT,
            consequence=IncidentLossEvaluation.Consequence.MAJOR,
            likelihood=IncidentLossEvaluation.Likelihood.POSSIBLE,
            risk_level=IncidentLossEvaluation.RiskLevel.HIGH,
            repair_type=IncidentLossEvaluation.RepairType.PERMANENT,
            repair_details="Permanent repair completed after inspection.",
            safe_working_practice="Working on deck while ship is at sea",
            injury_total_estimated_cost=Decimal("25.00"),
            total_estimated_cost=Decimal("250.00"),
            created_by="dpa-7",
            schema_version=1,
        )

        result = IncidentPdfRenderer().render_incident_pdf(
            incident_id=incident.pk,
            viewer_user=None,
            persist=False,
            included_sections=["estimated_cost"],
        )

        text = self._extract_pdf_text(result.content)
        self.assertIn("Permanent repair completed after inspection.", text)
        self.assertIn("250.00", text)
        self.assertNotIn("Code of Safe Working Practices", text)
        self.assertNotIn("Working on deck while ship is at sea", text)

    def test_pdf_evidence_documents_group_attachments_and_notes_cleanly(self) -> None:
        incident = self._create_exportable_incident("KSM-INC-2026-EVIDENCE")
        evidence_tab = IncidentEvidence.objects.create(
            incident=incident,
            tab_code=IncidentEvidence.TabCode.PEOPLE,
            summary="Attachment evidence captured.",
            entry_count=1,
            created_by="rep-7",
            schema_version=1,
        )
        EvidenceItem.objects.create(
            incident=incident,
            evidence_tab=evidence_tab,
            item_type=EvidenceItem.ItemType.MATRIX,
            title="Initial root cause entry",
            description="Root cause was entered before evidence upload.",
            created_by="rep-7",
            schema_version=1,
        )
        first_attachment_path = "vessels/7/incidents/KSM-INC-2026-EVIDENCE/phase-4/photo-set-a.jpg"
        EvidenceItem.objects.create(
            incident=incident,
            evidence_tab=evidence_tab,
            item_type=EvidenceItem.ItemType.MATRIX,
            title="Purifier platform condition",
            description="Oil residue observed on ladder edge.",
            finding="Legacy finding should not print in the simplified PDF evidence card.",
            pro_evidence="Legacy pro evidence should not print.",
            con_evidence="Legacy con evidence should not print.",
            comments="Legacy comment should not print.",
            metadata_json={
                "attachment_path": first_attachment_path,
                "file_name": "photo-set-a.jpg",
                "attachments": [
                    {
                        "attachment_path": first_attachment_path,
                        "original_name": "photo-set-a.jpg",
                    },
                    {
                        "attachment_path": first_attachment_path,
                        "file_name": "photo-set-a.jpg",
                    },
                ],
            },
            created_by="rep-7",
            schema_version=1,
        )
        second_attachment_path = "vessels/7/incidents/KSM-INC-2026-EVIDENCE/phase-4/134002466654279729-b51281dcf51a495b85189966cc146bc2.jpg"
        EvidenceItem.objects.create(
            incident=incident,
            evidence_tab=evidence_tab,
            item_type=EvidenceItem.ItemType.MATRIX,
            title="134002466654279729-b51281dcf51a495b85189966cc146bc2.jpg",
            metadata_json={
                "attachment_path": second_attachment_path,
                "original_name": "134002466654279729.jpg",
            },
            created_by="rep-7",
            schema_version=1,
        )

        renderer = IncidentPdfRenderer()
        context = renderer._build_context(incident, included_sections=["evidence_documents"])
        headings = [block.heading for block in context.evidence_blocks]
        self.assertCountEqual(headings, ["Purifier platform condition", "Evidence document"])
        purifier_block = next(block for block in context.evidence_blocks if block.heading == "Purifier platform condition")
        generated_title_block = next(block for block in context.evidence_blocks if block.heading == "Evidence document")
        document_blocks = [purifier_block, generated_title_block]
        row_labels = [label for block in document_blocks for label, _ in block.rows]
        self.assertFalse(any(label.startswith("Attachment ") for label in row_labels))
        self.assertFalse(any(label.startswith("Title ") for label in row_labels))
        self.assertFalse(any(label.startswith("Description ") for label in row_labels))
        self.assertEqual(purifier_block.rows[0], ("Description", "Oil residue observed on ladder edge."))
        self.assertEqual(purifier_block.rows[1][0], "File")
        self.assertEqual(generated_title_block.rows[0][0], "File")
        self.assertEqual(
            sum(value.count("PDF_LINK::") for block in document_blocks for _, value in block.rows),
            2,
        )
        attachment_link_rows = [value for block in document_blocks for label, value in block.rows if label == "File"]
        self.assertTrue(all("/phase-4/evidence/attachments/?path=" in value for value in attachment_link_rows))
        self.assertTrue(any("::photo-set-a.jpg" in value for value in attachment_link_rows))
        self.assertTrue(any("::134002466654279729.jpg" in value for value in attachment_link_rows))

        result = renderer.render_incident_pdf(
            incident_id=incident.pk,
            viewer_user=None,
            persist=False,
            included_sections=["evidence_documents"],
        )

        text = self._extract_pdf_text(result.content)
        self.assertIn("Evidence (Documents)", text)
        self.assertNotIn("Document 1", text)
        self.assertNotIn("Document 2", text)
        self.assertNotIn("Attachment 1", text)
        self.assertNotIn("Attachment 2", text)
        self.assertNotIn("Title 1", text)
        self.assertNotIn("Description 1", text)
        self.assertNotIn("Attachments", text)
        self.assertNotIn("Evidence notes", text)
        self.assertIn("Purifier platform condition", text)
        self.assertIn("Oil residue observed on ladder edge.", text)
        self.assertIn("photo-set-a.jpg", text)
        self.assertIn("134002466654279729.jpg", text)
        self.assertNotIn("Initial root cause entry", text)
        self.assertNotIn("Root cause was entered before evidence upload.", text)
        self.assertNotIn("Evidence item -", text)
        self.assertNotIn("134002466654279729-b51281dcf51a495b85189966cc146bc2.jpg", text)
        self.assertNotIn("Legacy finding should not print", text)
        self.assertNotIn("Legacy pro evidence should not print", text)
        self.assertNotIn("Legacy con evidence should not print", text)
        self.assertNotIn("Legacy comment should not print", text)

    def test_pdf_evidence_section_suppresses_saved_witness_statement_text(self) -> None:
        incident = self._create_exportable_incident("KSM-INC-2026-WITNESS")
        first_interview = WitnessInterview.objects.create(
            incident=incident,
            witness_name="AB Witness",
            interview_type=WitnessInterview.InterviewType.INFORMAL,
            meeting_notes="Witness saw water on the deck before the slip.",
            conclusion_notes="Witness statement closed after read-back.",
            reason_formal_impossible="Simplified witness note recorded from Phase 4.",
            witness_signature="data:image/png;base64,YXR0YWNoZWQtc3RhdGVtZW50",
            created_by="rep-7",
            schema_version=1,
        )
        WitnessInterview.objects.create(
            incident=incident,
            witness_name="Bosun Witness",
            interview_type=WitnessInterview.InterviewType.INFORMAL,
            meeting_notes="Bosun saw the deck cleaned after the incident.",
            conclusion_notes="Follow-up remark added by office.",
            reason_formal_impossible="Simplified witness note recorded from Phase 4.",
            created_by="rep-7",
            schema_version=1,
        )

        renderer = IncidentPdfRenderer()
        context = renderer._build_context(incident, included_sections=["evidence_documents"])

        blocks_by_heading = {block.heading: block for block in context.evidence_blocks}
        self.assertEqual(
            set(blocks_by_heading),
            {"Witness Statement - AB Witness", "Witness Statement - Bosun Witness"},
        )
        self.assertEqual(
            blocks_by_heading["Witness Statement - AB Witness"].rows,
            [
                (
                    "Witness statement attachment",
                    (
                        "PDF_LINK::"
                        f"/api/safety/incidents/{incident.id}/phase-4/interviews/{first_interview.id}/statement-attachment/"
                        "::Witness statement attachment"
                    ),
                ),
                ("Remark", "Witness statement closed after read-back."),
            ],
        )

        result = renderer.render_incident_pdf(
            incident_id=incident.pk,
            viewer_user=None,
            persist=False,
            included_sections=["evidence_documents"],
        )

        text = self._extract_pdf_text(result.content)
        self.assertIn("Evidence (Documents)", text)
        self.assertIn("Witness Statement", text)
        self.assertIn("AB Witness", text)
        self.assertNotIn("What the witness said", text)
        self.assertNotIn("Witness saw water on the deck before the slip.", text)
        self.assertIn("Witness statement attachment", text)
        self.assertNotIn("Attached", text)
        self.assertIn("Remark", text)
        self.assertIn("Witness statement closed after read-back.", text)
        self.assertIn("Witness Statement - Bosun Witness", text)
        self.assertNotIn("Bosun saw the deck cleaned after the incident.", text)
        self.assertIn("Follow-up remark added by office.", text)
        self.assertNotIn("Witness name", text)
        self.assertNotIn("Witness 1 name", text)
        self.assertNotIn("What witness 1 said", text)
        self.assertNotIn("Remark 1", text)
        self.assertNotIn("Interview type", text)
        self.assertNotIn("Reason formal impossible", text)

    def test_pdf_weather_condition_prints_option_label_not_uuid(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS vims_safety_incident_weather_option")
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(IncidentWeatherOption)

        visibility = IncidentWeatherOption.objects.create(
            field_key=IncidentWeatherOption.FieldKey.VISIBILITY,
            option_label="Good: More than 5 nautical miles",
            display_order=1,
            created_by="test",
        )
        incident = self._create_exportable_incident("KSM-INC-2026-WEATHER")
        incident.weather_visibility_id = visibility.pk
        incident.save(update_fields=["weather_visibility_id"])

        result = IncidentPdfRenderer().render_incident_pdf(incident_id=incident.pk, viewer_user=None, persist=False)

        text = self._extract_pdf_text(result.content)
        self.assertIn("Weather Condition", text)
        self.assertIn("Good: More than 5 nautical miles", text)
        self.assertNotIn(str(visibility.pk), text)

    def test_pdf_detail_block_headings_are_not_orphaned_at_page_end(self) -> None:
        context = self._long_detail_context()

        content = IncidentTenSectionTemplate().render(context)

        page_texts = self._extract_pdf_page_texts(content)
        for page_text in page_texts:
            self.assertFalse(
                page_text.rstrip().endswith("Injury Details\nInjury details"),
                page_text,
            )
        self.assertTrue(
            any(
                "Injury Details\nInjury details\nLabel 1" in page_text
                or "Injury details\nLabel 1" in page_text
                for page_text in page_texts
            )
        )

    @staticmethod
    def _extract_pdf_text(content: bytes) -> str:
        return "\n".join(IncidentPdfSectionTests._extract_pdf_page_texts(content))

    @staticmethod
    def _extract_pdf_page_texts(content: bytes) -> list[str]:
        reader = PdfReader(BytesIO(content))
        return [page.extract_text() or "" for page in reader.pages]

    @staticmethod
    def _long_detail_context():
        return IncidentPdfContext(
            incident_id=1,
            incident_number="TEST/2026/001",
            vessel_id="VESSEL",
            current_phase=8,
            risk_band="YELLOW",
            imo_classifier="MI",
            occurred_at="1",
            reported_at="1",
            narrative=" ".join(["Long narrative sentence."] * 120),
            generated_at="now",
            cover_band_hex="#FFFFFF",
            investigator_rows=[],
            evidence_rows=[],
            cause_rows=[],
            causal_factor_points=[],
            action_rows=[],
            lessons_text="",
            notification_rows=[],
            signature_rows=[],
            appendix_rows=[],
            report_title="Injury Report",
            classification_rows=[
                ("Incident number", "TEST/2026/001"),
                ("Vessel", "VESSEL"),
                ("Status", "APPROVED"),
                ("Risk band", "YELLOW"),
                ("Generated at", "now"),
            ],
            summary_blocks=[
                IncidentPdfDetailBlock(
                    "Weather Condition",
                    [
                        ("Visibility", "Poor"),
                        ("Precipitation", "Rain"),
                        ("Sea State", "Moderate"),
                        ("Wind Scale", "4"),
                        ("Wind Direction", "E"),
                        ("Source of Lighting", "Darkness"),
                        ("Current Direction", "SE"),
                        ("Current Strength", "8"),
                        ("Temperature", "-3"),
                        ("Light condition", "Full dark"),
                    ],
                )
            ],
            injury_detail_blocks=[
                IncidentPdfDetailBlock(
                    "Injury details",
                    [(f"Label {index}", "Value text " * 5) for index in range(1, 25)],
                )
            ],
            included_section_keys=["summary", "injury_details"],
        )

    @staticmethod
    def _create_exportable_incident(incident_number: str) -> Incident:
        return Incident.objects.create(
            incident_number=incident_number,
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.GREEN,
            imo_classifier=Incident.ImoClassifier.MC,
            occurred_at=datetime.fromisoformat("2026-04-27T10:15:00+00:00"),
            reported_at=datetime.fromisoformat("2026-04-27T11:30:00+00:00"),
            reporter_id="rep-7",
            reporter_name="Reporter Seven",
            reporter_rank="Chief Officer",
            narrative="Incident report title regression check.",
            created_by="rep-7",
            updated_by="rep-7",
            schema_version=1,
        )
