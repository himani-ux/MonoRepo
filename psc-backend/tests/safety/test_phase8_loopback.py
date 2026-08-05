from __future__ import annotations

import importlib
from types import SimpleNamespace
import unittest

from django.apps import apps as django_apps
from django.db import connection

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


VESSEL_UUID = "11111111-1111-1111-1111-111111111111"
MASTER_RANK_UUID = "22222222-2222-2222-2222-222222222222"
CHIEF_ENGINEER_RANK_UUID = "33333333-3333-3333-3333-333333333333"


def recreate_phase8_crew_reference_tables() -> None:
    with connection.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS Crew_Onboarding_History")
        cursor.execute("DROP TABLE IF EXISTS HRM501")
        cursor.execute("DROP TABLE IF EXISTS master_applied_rank")
        cursor.execute(
            """
            CREATE TABLE master_applied_rank (
                id VARCHAR(36) PRIMARY KEY,
                rank_name VARCHAR(128) NULL,
                is_active BOOLEAN NULL DEFAULT 1,
                is_deleted BOOLEAN NULL DEFAULT 0
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE HRM501 (
                id VARCHAR(36) PRIMARY KEY,
                CrewID VARCHAR(16) NOT NULL,
                first_name VARCHAR(128) NULL,
                surname VARCHAR(128) NULL,
                rank_name VARCHAR(36) NULL,
                is_active BOOLEAN NULL DEFAULT 1,
                is_deleted BOOLEAN NULL DEFAULT 0
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE Crew_Onboarding_History (
                id VARCHAR(36) PRIMARY KEY,
                CrewID VARCHAR(16) NOT NULL,
                Vessel VARCHAR(36) NULL,
                SignOnDate DATETIME NULL,
                SignOffDate DATETIME NULL,
                is_active BOOLEAN NULL DEFAULT 1,
                is_deleted BOOLEAN NULL DEFAULT 0,
                created_date DATETIME NULL
            )
            """
        )
        cursor.executemany(
            "INSERT INTO master_applied_rank (id, rank_name, is_active, is_deleted) VALUES (%s, %s, %s, %s)",
            [
                (MASTER_RANK_UUID, "MASTER", 1, 0),
                (CHIEF_ENGINEER_RANK_UUID, "CHIEF ENGINEER", 1, 0),
            ],
        )
        cursor.executemany(
            """
            INSERT INTO HRM501 (id, CrewID, first_name, surname, rank_name, is_active, is_deleted)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            [
                ("44444444-4444-4444-4444-444444444444", "KSM0001", "Master", "Current", MASTER_RANK_UUID, 1, 0),
                (
                    "55555555-5555-5555-5555-555555555555",
                    "KSM0002",
                    "Chief",
                    "Engineer",
                    CHIEF_ENGINEER_RANK_UUID,
                    1,
                    0,
                ),
            ],
        )
        cursor.executemany(
            """
            INSERT INTO Crew_Onboarding_History (
                id, CrewID, Vessel, SignOnDate, SignOffDate, is_active, is_deleted, created_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    "66666666-6666-6666-6666-666666666666",
                    "KSM0001",
                    VESSEL_UUID,
                    "2026-01-01 00:00:00",
                    None,
                    1,
                    0,
                    "2026-01-01 00:00:00",
                ),
                (
                    "77777777-7777-7777-7777-777777777777",
                    "KSM0002",
                    VESSEL_UUID,
                    "2026-01-02 00:00:00",
                    None,
                    1,
                    0,
                    "2026-01-02 00:00:00",
                ),
            ],
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

    def test_workspace_auto_fills_current_vessel_master_and_chief_engineer(self) -> None:
        recreate_phase8_crew_reference_tables()
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8CREW1",
            vessel_id=VESSEL_UUID,
            state="IN_PROGRESS",
            current_phase=7,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            created_by="master-1",
            updated_by="master-1",
            schema_version=1,
        )

        payload = build_phase8_workspace_payload(incident)

        self.assertEqual(payload["loss_evaluation"]["name_of_master"], "Master Current")
        self.assertEqual(payload["loss_evaluation"]["name_of_chief_engineer"], "Chief Engineer")

    def test_workspace_preserves_saved_loss_evaluation_officer_names(self) -> None:
        recreate_phase8_crew_reference_tables()
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8CREW2",
            vessel_id=VESSEL_UUID,
            state="IN_PROGRESS",
            current_phase=7,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            created_by="master-1",
            updated_by="master-1",
            schema_version=1,
        )
        IncidentLossEvaluation.objects.create(
            incident=incident,
            name_of_master="Manual Master",
            name_of_chief_engineer="Manual Chief Engineer",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        payload = build_phase8_workspace_payload(incident)

        self.assertEqual(payload["loss_evaluation"]["name_of_master"], "Manual Master")
        self.assertEqual(payload["loss_evaluation"]["name_of_chief_engineer"], "Manual Chief Engineer")

    def test_ship_user_can_fill_loss_evaluation_before_office_approval(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8SHIP1",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=7,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            created_by="master-1",
            updated_by="master-1",
            schema_version=1,
        )

        get_request = self.factory.get(f"/api/safety/incidents/{incident.pk}/phase-8/")
        ship_user = build_user(role_name="MASTER", user_id="master-1", process_ids=[])
        force_authenticate(get_request, user=ship_user)

        get_response = self.workspace_view(get_request, id=incident.pk)

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.data["current_phase"], 7)

        patch_request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/phase-8/",
            {
                "report_type": "INCIDENT",
                "consequence": "MAJOR",
                "likelihood": "POSSIBLE",
                "risk_level": "HIGH",
                "name_of_master": "Master One",
                "estimated_cost_delay": "75.00",
                "total_estimated_cost": "75.00",
            },
            format="json",
        )
        force_authenticate(patch_request, user=ship_user)

        patch_response = self.workspace_view(patch_request, id=incident.pk)

        self.assertEqual(patch_response.status_code, 200)
        self.assertTrue(patch_response.data["has_loss_evaluation"])
        self.assertEqual(patch_response.data["report_type"], "INCIDENT")
        self.assertEqual(patch_response.data["loss_evaluation"]["name_of_master"], "Master One")
        self.assertEqual(patch_response.data["loss_evaluation"]["total_estimated_cost"], "75.00")

    def test_user_can_choose_injury_loss_evaluation_without_injury_record(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/P8TYPE1",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=7,
            risk_band=Incident.RiskBand.YELLOW,
            pic_user_id="pic-1",
            created_by="master-1",
            updated_by="master-1",
            schema_version=1,
        )

        request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/phase-8/",
            {
                "report_type": "INJURY",
                "consequence": "SEVERE",
                "likelihood": "UNLIKELY",
                "risk_level": "HIGH",
                "safe_working_practice": "Working on deck while ship is at sea",
                "injury_total_estimated_cost": "125.00",
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="MASTER", user_id="master-1", process_ids=[]),
        )

        response = self.workspace_view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["report_type"], "INJURY")
        self.assertEqual(response.data["loss_evaluation"]["report_type"], "INJURY")
        self.assertEqual(
            response.data["loss_evaluation"]["safe_working_practice"],
            "Working on deck while ship is at sea",
        )

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

    def test_phase_eight_close_endpoint_rejects_closure(self) -> None:
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

        self.assertEqual(response.status_code, 400)
        incident.refresh_from_db()
        self.assertEqual(incident.current_phase, 8)
        self.assertEqual(incident.state, "APPROVED")
        self.assertIn("Incident close is handled in Phase 6 Office Review.", str(response.data))

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
                "report_type": "INCIDENT",
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
        self.assertEqual(response.data["report_type"], "INCIDENT")
        self.assertEqual(response.data["loss_evaluation"]["report_type"], "INCIDENT")
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
