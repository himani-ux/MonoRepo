from __future__ import annotations

import importlib
from types import SimpleNamespace
import unittest

from django.apps import apps as django_apps

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import (
    ExternalPartyInjury,
    Incident,
    IncidentLossEvaluation,
    IncidentPhaseLog,
    InjuryDropdownOption,
    Recommendation,
)
from apps.safety.serializers.incident_phase8 import build_phase8_workspace_payload
from apps.safety.views.incident_phase8 import IncidentPhase8CloseView, IncidentPhase8VerifyView, IncidentPhase8WorkspaceView


def build_user(*, role_name: str, user_id: str, process_ids: list[str]):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class Phase8LoopbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.close_view = IncidentPhase8CloseView.as_view()
        self.verify_view = IncidentPhase8VerifyView.as_view()
        self.workspace_view = IncidentPhase8WorkspaceView.as_view()

    def test_workspace_view_allows_scoped_office_user_to_read_red_incident(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8R1",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.RED,
            pic_user_id="pic-1",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.get(f"/api/safety/incidents/{incident.pk}/phase-6/")
        force_authenticate(
            request,
            user=build_user(role_name="OFFICE_PIC", user_id="office-pic-1", process_ids=[]),
        )

        response = self.workspace_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["incident_id"], incident.pk)
        self.assertEqual(response.data["phase_title"], "Loss Evaluation")
        self.assertEqual(response.data["report_type"], "INCIDENT")
        self.assertFalse(response.data["has_loss_evaluation"])

    def test_ineffective_verification_loops_back_to_phase_six(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8L1",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        recommendation = Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Correct guardrail gap",
            description="Ship a corrective action.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-8/verify/",
            {
                "recommendation_id": recommendation.pk,
                "is_effective": False,
                "residual_risk": "MEDIUM",
                "notes": "Control failed on vessel follow-up; new recommendation required.",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="DPA", user_id="dpa-1", process_ids=["SAF_P_004"]),
        )

        response = self.verify_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 6)
        latest_log = IncidentPhaseLog.objects.order_by("-id").first()
        self.assertIsNotNone(latest_log)
        self.assertEqual(latest_log.transition_type, IncidentPhaseLog.TransitionType.REWORK)
        self.assertEqual(latest_log.phase_from, 8)
        self.assertEqual(latest_log.phase_to, 6)

    def test_dpa_can_record_effectiveness_without_process_permission(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8D1",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        recommendation = Recommendation.objects.create(
            incident=incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Verify corrective action",
            description="Verification without process permission.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-8/verify/",
            {
                "recommendation_id": recommendation.pk,
                "is_effective": True,
                "residual_risk": "LOW",
                "notes": "DPA verified the corrective action.",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="DPA", user_id="dpa-1", process_ids=[]),
        )

        response = self.verify_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["looped_back"])

    def test_pic_can_close_red_incident_after_loss_evaluation_is_saved(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8PIC-R",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.RED,
            pic_user_id="pic-1",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        IncidentLossEvaluation.objects.create(
            incident=incident,
            consequence=IncidentLossEvaluation.Consequence.MAJOR,
            likelihood=IncidentLossEvaluation.Likelihood.POSSIBLE,
            risk_level=IncidentLossEvaluation.RiskLevel.HIGH,
            name_of_master="Master One",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/phase-8/close/",
            {"closure_reason": "Loss evaluation complete."},
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="OFFICE_PIC", user_id="pic-1", process_ids=["SAF_P_006"]),
        )

        response = self.close_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 9)
        self.assertEqual(incident.state, "CLOSED")

    def test_workspace_saves_incident_loss_evaluation(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8LOSS1",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/phase-8/",
            {
                "consequence": "MAJOR",
                "likelihood": "POSSIBLE",
                "risk_level": "HIGH",
                "name_of_master": "Master One",
                "name_of_chief_engineer": "Chief Engineer One",
                "repair_type": "TEMPORARY",
                "repair_details": "Temporary repair completed onboard.",
                "estimated_cost_off_hire": "100.00",
                "estimated_cost_delay": "50.00",
                "total_estimated_cost": "150.00",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="DPA", user_id="dpa-1", process_ids=[]),
        )

        response = self.workspace_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["has_loss_evaluation"])
        self.assertTrue(response.data["ready_for_close"])
        self.assertEqual(response.data["loss_evaluation"]["repair_type"], "TEMPORARY")
        self.assertEqual(response.data["loss_evaluation"]["total_estimated_cost"], "150.00")

    def test_workspace_uses_injury_report_field_set_when_injury_exists(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8INJ1",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        ExternalPartyInjury.objects.create(
            incident=incident,
            injured_person_type=ExternalPartyInjury.InjuredPersonType.CREW,
            created_by="dpa-1",
            schema_version=1,
        )
        IncidentLossEvaluation.objects.create(
            incident=incident,
            consequence=IncidentLossEvaluation.Consequence.SEVERE,
            likelihood=IncidentLossEvaluation.Likelihood.UNLIKELY,
            risk_level=IncidentLossEvaluation.RiskLevel.HIGH,
            safe_working_practice="Code A",
            cost_medicines_onboard="25.00",
            injury_total_estimated_cost="25.00",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        payload = build_phase8_workspace_payload(incident)

        self.assertEqual(payload["report_type"], "INJURY")
        self.assertTrue(payload["has_loss_evaluation"])
        self.assertEqual(payload["loss_evaluation"]["safe_working_practice"], "Code A")
        self.assertEqual(payload["loss_evaluation"]["injury_total_estimated_cost"], "25.00")

    def test_workspace_uses_seeded_safe_working_practice_dropdown_options(self) -> None:
        migration = importlib.import_module(
            "apps.safety.migrations.0055_seed_safe_working_practice_options"
        )
        InjuryDropdownOption.objects.create(
            field_key=InjuryDropdownOption.FieldKey.SAFE_WORKING_PRACTICE,
            option_label="Code A",
            display_order=1,
            active=True,
            created_by="test",
        )
        migration.seed_safe_working_practice_options(django_apps, None)
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8INJ2",
            vessel_id="7",
            state="APPROVED",
            current_phase=8,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        ExternalPartyInjury.objects.create(
            incident=incident,
            injured_person_type=ExternalPartyInjury.InjuredPersonType.CREW,
            created_by="dpa-1",
            schema_version=1,
        )

        options = build_phase8_workspace_payload(incident)["choices"]["safe_working_practice"]
        labels = [option["label"] for option in options]

        self.assertEqual(labels[:3], ["Health and hygiene", "Good housekeeping", "Fitness, health and hygiene"])
        self.assertIn("Painting", labels)
        self.assertNotIn("Code A", labels)
        self.assertEqual(labels.count("Health and hygiene"), 1)
        self.assertEqual(labels.count("Lighting"), 1)
        self.assertEqual(labels.count("Electrical equipment"), 1)
