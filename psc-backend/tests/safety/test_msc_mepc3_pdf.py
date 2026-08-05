from __future__ import annotations

from datetime import datetime
from io import BytesIO
from types import SimpleNamespace
import unittest

from PyPDF2 import PdfReader

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_mscmepc3_support_tables


bootstrap_django()

from django.db import connection
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import EvidenceItem, Incident, IncidentCauseTag, IncidentEvidence, IncidentFact, Recommendation
from apps.safety.services.pdf_renderer import MscMepc3Circ4PdfRenderer
from apps.safety.views.msc_mepc3_export import MscMepc3ExportView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    form_ids: list[str] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=f"{role_name.lower()}-1",
        username=f"{role_name.lower()}-1",
        role_name=role_name,
        form_ids=form_ids if form_ids is not None else ["SAF_F_001"],
        process_ids=process_ids if process_ids is not None else ["SAF_P_023"],
        vessel_ids=["SFD"],
        is_global=True,
    )


class MscMepc3PdfTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_mscmepc3_support_tables()
        self.factory = APIRequestFactory()
        self.view = MscMepc3ExportView.as_view()

    def test_renderer_maps_five_appendices_from_incident_vessel_and_reporting_sources(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_safety_incident_type (id, legacy_int_id, type_code, type_name)
                VALUES (%s, %s, %s, %s)
                """,
                ["00000000000000000000000000000001", 1, "COLLISION", "Collision / Contact"],
            )
            cursor.execute(
                """
                INSERT INTO master_loss_types (id, legacy_int_id, loss_type_id, loss_type_name)
                VALUES (%s, %s, %s, %s)
                """,
                ["00000000000000000000000000000002", 1, 3, "Environmental"],
            )
            cursor.execute(
                """
                INSERT INTO VesselData (
                    id,
                    vesselCode,
                    vesselName,
                    imoNumber,
                    flags,
                    ClassificationSociety,
                    grt,
                    nrt,
                    deadweight,
                    LastPortofcall,
                    ShipOwner,
                    ShipManagement,
                    is_deleted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
                """,
                [
                    "2FBE4CC4-0723-EF11-BE3C-30D042027DCF",
                    "SFD",
                    "SF DARIKA",
                    "9502752",
                    "Thai",
                    "KR",
                    22402,
                    12019,
                    35265,
                    "BANGKOK",
                    "SF DARIKA Co., Ltd",
                    "Kaizen Ship Management Co., Ltd",
                ],
            )
            cursor.execute(
                """
                INSERT INTO NoonReport (
                    id,
                    auto_id,
                    VesselID,
                    ReportDate,
                    VoyageNo,
                    VoyCondition,
                    Lattitude1,
                    Lattitude2,
                    Lattitude3,
                    Longitude1,
                    Longitud2,
                    Longitud3,
                    WeatherRemarks,
                    WindForce,
                    SeaState,
                    CurrentStrength,
                    TotalCargoWeight
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    "row-11560",
                    11560,
                    "SFD",
                    datetime.fromisoformat("2026-04-27T10:00:00+00:00"),
                    "VOY-778",
                    "AT SEA",
                    12,
                    30,
                    "N",
                    98,
                    45,
                    "E",
                    "Moderate swell and passing rain.",
                    5,
                    4,
                    1.5,
                    22150,
                ],
            )

        incident = Incident.objects.create(
            incident_number="KSM-INC-2026-0055",
            vessel_id="SFD",
            state="CLOSED",
            current_phase=9,
            risk_band=Incident.RiskBand.YELLOW,
            imo_classifier=Incident.ImoClassifier.MC,
            incident_type_id=1,
            loss_type_primary_id=3,
            investigation_depth=Incident.InvestigationDepth.DEEP,
            occurred_at=datetime.fromisoformat("2026-04-27T10:15:00+00:00"),
            reported_at=datetime.fromisoformat("2026-04-27T11:30:00+00:00"),
            position_source="AUTO_FROM_DAILY_REPORT",
            narrative="Contact with floating object during heavy-weather passage.",
            marine_docs_checklist_done=True,
            chain_of_custody_ok=True,
            cargo_evidence_applicable=True,
            health_fatigue_applicable=False,
            causal_layering_complete=True,
            alarp_attested=True,
            bias_guard_attestations="RECENCY,CONFIRMATION",
            reporter_id="rep-55",
            reporter_name="Reporter Fifty Five",
            reporter_rank="Chief Officer",
            reporter_department="Deck",
            dpa_notified_at=datetime.fromisoformat("2026-04-27T12:00:00+00:00"),
            office_notified_at=datetime.fromisoformat("2026-04-27T12:05:00+00:00"),
            dpa_accepted_by="dpa-55",
            closed_at=datetime.fromisoformat("2026-04-28T08:00:00+00:00"),
            created_by="rep-55",
            updated_by="dpa-55",
            schema_version=1,
        )
        evidence_tab = IncidentEvidence.objects.create(
            incident=incident,
            tab_code=IncidentEvidence.TabCode.POSITION,
            summary="Bridge log, weather observation, and obstruction sighting notes.",
            entry_count=1,
            created_by="rep-55",
            schema_version=1,
        )
        evidence_item = EvidenceItem.objects.create(
            incident=incident,
            evidence_tab=evidence_tab,
            item_type=EvidenceItem.ItemType.MATRIX,
            title="Bridge weather observation",
            description="Noon report weather block and bridge notes for the same watch.",
            source_label="Noon report",
            finding="Heavy-weather context confirmed.",
            created_by="rep-55",
            schema_version=1,
        )
        first_fact = IncidentFact.objects.create(
            incident=incident,
            sequence_index=1,
            fact_text="The vessel altered course after a floating obstruction was sighted on the starboard bow.",
            fact_timestamp=datetime.fromisoformat("2026-04-27T10:12:00+00:00"),
            source_evidence_id=evidence_item.pk,
            created_by="rep-55",
            schema_version=1,
        )
        IncidentCauseTag.objects.create(
            incident=incident,
            source_fact=first_fact,
            mscat_subcode_id="M-220",
            causal_layer=IncidentCauseTag.CausalLayer.ROOT,
            analysis_tool=IncidentCauseTag.AnalysisTool.STEP,
            rationale="Bridge lookout and prevailing weather conditions reduced reaction margin.",
            created_by="dpa-55",
            schema_version=1,
        )
        Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.PREVENTIVE,
            title="Review heavy-weather obstruction lookout briefing.",
            description="Add a fleet reminder to bridge team departure briefings.",
            rationale="The same navigation window exists on sister vessels.",
            created_by="dpa-55",
            schema_version=1,
        )

        result = MscMepc3Circ4PdfRenderer().render_export_pdf(
            incident_id=incident.pk,
            viewer_user=None,
            persist=False,
        )

        self.assertTrue(result.content.startswith(b"%PDF"))
        self.assertEqual(result.incident_id, incident.pk)
        self.assertEqual(
            result.appendix_titles,
            [
                "Appendix 1. Generic Information",
                "Appendix 2. Ship Particulars",
                "Appendix 3. Casualty Analysis",
                "Appendix 4. Supplementary Conditions",
                "Appendix 5. Standardized Field Values",
            ],
        )

        reader = PdfReader(BytesIO(result.content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)

        self.assertIn("MSC-MEPC.3/Circ.4 Regulatory Export", text)
        self.assertIn("Appendix 1. Generic Information", text)
        self.assertIn("Appendix 2. Ship Particulars", text)
        self.assertIn("Appendix 3. Casualty Analysis", text)
        self.assertIn("Appendix 4. Supplementary Conditions", text)
        self.assertIn("Appendix 5. Standardized Field Values", text)
        self.assertIn("SF DARIKA", text)
        self.assertIn("9502752", text)
        self.assertIn("Thai", text)
        self.assertIn("NoonReport:11560", text)
        self.assertIn("Moderate swell and passing rain.", text)
        self.assertIn("Collision / Contact", text)
        self.assertIn("Environmental", text)
        self.assertNotIn("First-hour checklist", text)
        self.assertIn("Field 29 - Current strength", text)

    def test_backend_export_is_dpa_only_even_with_export_permission(self) -> None:
        incident = self._create_exportable_incident()

        dpa_request = self.factory.get(f"/api/safety/export/msc-mepc-3/{incident.pk}/")
        force_authenticate(dpa_request, user=build_user(role_name="DPA"))
        dpa_response = self.view(dpa_request, id=incident.pk)
        self.assertEqual(dpa_response.status_code, 200)

        fm_request = self.factory.get(f"/api/safety/export/msc-mepc-3/{incident.pk}/")
        force_authenticate(fm_request, user=build_user(role_name="FM", process_ids=["SAF_P_023"]))
        fm_response = self.view(fm_request, id=incident.pk)
        self.assertEqual(fm_response.status_code, 403)

        no_permission_request = self.factory.get(f"/api/safety/export/msc-mepc-3/{incident.pk}/")
        force_authenticate(no_permission_request, user=build_user(role_name="DPA", process_ids=[]))
        no_permission_response = self.view(no_permission_request, id=incident.pk)
        self.assertEqual(no_permission_response.status_code, 403)

    def test_renderer_rejects_missing_or_non_applicable_imo_classifier(self) -> None:
        for classifier in (None, Incident.ImoClassifier.NOT_APPLICABLE):
            with self.subTest(classifier=classifier):
                incident = self._create_exportable_incident(imo_classifier=classifier)
                with self.assertRaises(ValidationError) as context:
                    MscMepc3Circ4PdfRenderer().render_export_pdf(
                        incident_id=incident.pk,
                        viewer_user=None,
                        persist=False,
                    )
                self.assertIn("requires an applicable IMO classifier", str(context.exception))

    def test_renderer_allows_applicable_incident_before_phase_seven_acceptance(self) -> None:
        incident = self._create_exportable_incident(
            current_phase=6,
            state="IN_PROGRESS",
        )

        result = MscMepc3Circ4PdfRenderer().render_export_pdf(
            incident_id=incident.pk,
            viewer_user=None,
            persist=False,
        )

        self.assertTrue(result.content.startswith(b"%PDF"))
        self.assertEqual(result.incident_id, incident.pk)

    def _create_exportable_incident(
        self,
        *,
        current_phase: int = 9,
        imo_classifier: str | None = Incident.ImoClassifier.MI,
        state: str = "CLOSED",
    ) -> Incident:
        return Incident.objects.create(
            incident_number=f"KSM-INC-2026-MSC-{Incident.objects.count() + 1}",
            vessel_id="SFD",
            state=state,
            current_phase=current_phase,
            risk_band=Incident.RiskBand.YELLOW,
            imo_classifier=imo_classifier,
            occurred_at=datetime.fromisoformat("2026-04-27T10:15:00+00:00"),
            reported_at=datetime.fromisoformat("2026-04-27T11:30:00+00:00"),
            narrative="Regulatory export permission fixture.",
            marine_docs_checklist_done=True,
            chain_of_custody_ok=True,
            causal_layering_complete=True,
            alarp_attested=True,
            reporter_id="rep-msc",
            reporter_name="Reporter MSC",
            created_by="rep-msc",
            updated_by="dpa-msc",
            schema_version=1,
        )
