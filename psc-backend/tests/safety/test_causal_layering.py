from __future__ import annotations

import unittest

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_phase5_reference_tables,
    seed_phase5_reference_tables,
)


bootstrap_django()

from apps.safety.models import Incident, IncidentCauseTag, IncidentFact, MasterMscatTaxonomy


class CausalLayeringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_phase5_reference_tables()
        seed_phase5_reference_tables()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/PH5",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=5,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        self.fact = IncidentFact.objects.create(
            incident=self.incident,
            sequence_index=1,
            fact_text="Bridge team actions and system controls were reviewed against captured evidence.",
            source_evidence_id=101,
            confidence=IncidentFact.Confidence.HIGH,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        self.subcode = MasterMscatTaxonomy.objects.first()

    def test_immediate_intermediate_and_root_layers_persist(self) -> None:
        IncidentCauseTag.objects.create(
            incident=self.incident,
            source_fact=self.fact,
            mscat_subcode_id=self.subcode.subcode_id,
            causal_layer=IncidentCauseTag.CausalLayer.IMMEDIATE,
            analysis_tool=IncidentCauseTag.AnalysisTool.STEP,
            rationale="Immediate action captured from the fact base.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        IncidentCauseTag.objects.create(
            incident=self.incident,
            source_fact=self.fact,
            mscat_subcode_id=self.subcode.subcode_id,
            causal_layer=IncidentCauseTag.CausalLayer.INTERMEDIATE,
            analysis_tool=IncidentCauseTag.AnalysisTool.FACT_TREE,
            rationale="Intermediate condition linked from the same fact.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        IncidentCauseTag.objects.create(
            incident=self.incident,
            source_fact=self.fact,
            mscat_subcode_id=self.subcode.subcode_id,
            causal_layer=IncidentCauseTag.CausalLayer.ROOT,
            analysis_tool=IncidentCauseTag.AnalysisTool.BARRIER,
            rationale="Root cause retained with its layer tag.",
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )

        layers = list(
            self.incident.cause_tags.order_by("id").values_list("causal_layer", flat=True)
        )
        self.assertEqual(
            layers,
            [
                IncidentCauseTag.CausalLayer.IMMEDIATE,
                IncidentCauseTag.CausalLayer.INTERMEDIATE,
                IncidentCauseTag.CausalLayer.ROOT,
            ],
        )

    def test_multiple_root_causes_have_no_artificial_cap(self) -> None:
        rows = [
            IncidentCauseTag(
                incident=self.incident,
                source_fact=self.fact,
                mscat_subcode_id=self.subcode.subcode_id,
                causal_layer=IncidentCauseTag.CausalLayer.ROOT,
                analysis_tool=IncidentCauseTag.AnalysisTool.CHANGE,
                rationale=f"Root cause path {index}",
                created_by="master-7",
                updated_by="master-7",
                schema_version=1,
            )
            for index in range(1, 16)
        ]
        IncidentCauseTag.objects.bulk_create(rows)

        self.assertEqual(
            self.incident.cause_tags.filter(
                causal_layer=IncidentCauseTag.CausalLayer.ROOT
            ).count(),
            15,
        )
