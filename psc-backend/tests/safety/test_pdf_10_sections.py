from __future__ import annotations

from datetime import datetime
from io import BytesIO
import unittest

from PyPDF2 import PdfReader

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import (
    CorrectiveAction,
    EvidenceItem,
    Incident,
    IncidentCauseTag,
    IncidentEvidence,
    IncidentFact,
    Recommendation,
    RecommendationVerification,
)
from apps.safety.services.pdf_renderer import IncidentPdfRenderer


class IncidentPdfTenSectionTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()

    def test_renderer_outputs_all_ten_section_titles(self) -> None:
        incident = Incident.objects.create(
            incident_number="KSM-INC-2026-0042",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.YELLOW,
            imo_classifier=Incident.ImoClassifier.MC,
            occurred_at=datetime.fromisoformat("2026-04-27T10:15:00+00:00"),
            reported_at=datetime.fromisoformat("2026-04-27T11:30:00+00:00"),
            reporter_id="rep-7",
            reporter_name="Reporter Seven",
            reporter_rank="Chief Officer",
            reporter_device_fingerprint="device-reporter-7",
            narrative="Engine-room slip while inspecting purifier platform. Containment established and review started.",
            pic_user_id="pic-7",
            dpa_accepted_by="dpa-7",
            dpa_accepted_at=datetime.fromisoformat("2026-04-28T08:00:00+00:00"),
            created_by="rep-7",
            updated_by="dpa-7",
            schema_version=1,
        )
        evidence_tab = IncidentEvidence.objects.create(
            incident=incident,
            tab_code=IncidentEvidence.TabCode.PEOPLE,
            summary="Witness notes and bridge call log captured.",
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
            source_fact=fact,
            mscat_subcode_id="M-101",
            causal_layer=IncidentCauseTag.CausalLayer.ROOT,
            analysis_tool=IncidentCauseTag.AnalysisTool.STEP,
            rationale="Permit controls did not cover the oily ladder condition.",
            created_by="dpa-7",
            schema_version=1,
        )
        recommendation = Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.LESSONS_LEARNT,
            title="Fleet ladder-condition alert",
            description="Issue a ladder housekeeping lesson to all vessels.",
            rationale="The same purifier ladder layout exists fleet-wide.",
            created_by="dpa-7",
            schema_version=1,
        )
        corrective_action = CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=incident.pk,
            recommendation=recommendation,
            title="Replace anti-slip edge strip",
            description="Fit a new anti-slip strip and inspect adjacent access points.",
            status=CorrectiveAction.Status.IN_PROGRESS,
            created_by="dpa-7",
            schema_version=1,
        )
        RecommendationVerification.objects.create(
            recommendation=recommendation,
            is_effective=False,
            residual_risk="MEDIUM",
            verified_by="dpa-7",
            notes="Awaiting vessel close-out confirmation.",
        )

        result = IncidentPdfRenderer().render_incident_pdf(incident_id=incident.pk, viewer_user=None, persist=False)

        self.assertTrue(result.content.startswith(b"%PDF"))
        self.assertEqual(result.section_titles, [
            "1. Cover and Classification",
            "2. Investigator / Team Credentials",
            "3. Evidence Collected",
            "4. Causes Identified",
            "5. Contributing Factors",
            "6. Actions and Timeline",
            "7. Lessons Learned",
            "8. Fleet Notification Plan",
            "9. Signatures",
            "10. Appendices",
        ])

        reader = PdfReader(BytesIO(result.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for title in result.section_titles:
            self.assertIn(title, text)
        self.assertIn("KSM-INC-2026-0042", text)
        self.assertIn("Fleet ladder-condition alert", text)
        self.assertIn("Replace anti-slip edge strip", text)
        self.assertIn("27 Apr 2026, 10:15", text)
        self.assertIn("Prepared by", text)
        self.assertNotIn("Step 6.1", text)
        self.assertNotIn("internal 10-section contract", text)
        self.assertNotIn("Narrative owner", text)
