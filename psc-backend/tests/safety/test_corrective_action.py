from __future__ import annotations

from types import SimpleNamespace
import unittest

from django.db import connection

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_purchase_requisition_table,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import CorrectiveAction, Incident, Recommendation
from apps.safety.views.corrective_action import (
    CorrectiveActionDetailView,
    CorrectiveActionLinkPurchaseView,
    CorrectiveActionListCreateView,
    CorrectiveActionPhysicalVerifyView,
    CorrectiveActionTransitionView,
)


def build_user(*, process_ids: list[str], user_id: str = "dpa-1", role_name: str = "DPA"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class CorrectiveActionApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_purchase_requisition_table()
        self.factory = APIRequestFactory()
        self.list_view = CorrectiveActionListCreateView.as_view()
        self.detail_view = CorrectiveActionDetailView.as_view()
        self.transition_view = CorrectiveActionTransitionView.as_view()
        self.link_view = CorrectiveActionLinkPurchaseView.as_view()
        self.verify_view = CorrectiveActionPhysicalVerifyView.as_view()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/CA1",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.YELLOW,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        self.recommendation = Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Replace failed guard",
            description="Immediate vessel corrective action.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO pur_requisition (id, status, is_archived) VALUES (%s, %s, %s)",
                [9101, "SUBMITTED", 0],
            )
            cursor.execute(
                "INSERT INTO pur_requisition (id, status, is_archived) VALUES (%s, %s, %s)",
                [9102, "CLOSED", 1],
            )

    def test_create_endpoint_accepts_active_purchase_requisition(self) -> None:
        request = self.factory.post(
            "/api/safety/corrective-actions/",
            {
                "source_table": "vims_safety_incident",
                "source_id": self.incident.pk,
                "recommendation_id": self.recommendation.pk,
                "title": "Replace failed guard",
                "description": "Immediate vessel corrective action.",
                "assigned_crew_id": "bosun-4",
                "verifier_user_id": "dpa-1",
                "due_date": "2026-05-30",
                "purchase_req_id": 9101,
            },
            format="json",
        )
        force_authenticate(request, user=build_user(process_ids=["SAF_P_020"]))

        response = self.list_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], CorrectiveAction.Status.OPEN)
        self.assertEqual(response.data["purchase_req_id"], 9101)
        self.assertEqual(response.data["aging_bucket"], "0-15")

    def test_detail_endpoint_rejects_corrective_action_for_unassigned_vessel(self) -> None:
        other_incident = Incident.objects.create(
            incident_number="ABC/2026/CA-OTHER",
            vessel_id="99",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.YELLOW,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        other_recommendation = Recommendation.objects.create(
            incident=other_incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Other vessel recommendation",
            description="Corrective action from a different vessel.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        action = CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=other_incident.pk,
            recommendation=other_recommendation,
            title="Other vessel action",
            description="Should be hidden from vessel 7 scoped user.",
            verifier_user_id="dpa-1",
            due_date="2026-05-30",
            status=CorrectiveAction.Status.OPEN,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.get(f"/api/safety/corrective-actions/{action.pk}/")
        force_authenticate(request, user=build_user(process_ids=["SAF_P_020"], role_name="PIC"))

        response = self.detail_view(request, id=action.pk)

        self.assertEqual(response.status_code, 404)

    def test_link_endpoint_rejects_archived_requisition(self) -> None:
        action = CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=self.incident.pk,
            recommendation=self.recommendation,
            title="Replace failed guard",
            description="Immediate vessel corrective action.",
            verifier_user_id="dpa-1",
            due_date="2026-05-30",
            status=CorrectiveAction.Status.OPEN,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/corrective-actions/{action.pk}/link-pr/",
            {"purchase_req_id": 9102},
            format="json",
        )
        force_authenticate(request, user=build_user(process_ids=["SAF_P_021"]))

        response = self.link_view(request, id=action.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("purchase_req_id", response.data)

    def test_transition_and_physical_verification_endpoints_update_action(self) -> None:
        action = CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=self.incident.pk,
            recommendation=self.recommendation,
            title="Replace failed guard",
            description="Immediate vessel corrective action.",
            verifier_user_id="dpa-1",
            due_date="2026-05-30",
            status=CorrectiveAction.Status.OPEN,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/corrective-actions/{action.pk}/transition/",
            {"status": CorrectiveAction.Status.IN_PROGRESS, "note": "Parts ordered."},
            format="json",
        )
        force_authenticate(request, user=build_user(process_ids=["SAF_P_020"]))
        response = self.transition_view(request, id=action.pk)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post(
            f"/api/safety/corrective-actions/{action.pk}/transition/",
            {"status": CorrectiveAction.Status.PENDING_VERIFY, "note": "Work completed on board."},
            format="json",
        )
        force_authenticate(request, user=build_user(process_ids=["SAF_P_020"]))
        response = self.transition_view(request, id=action.pk)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post(
            f"/api/safety/corrective-actions/{action.pk}/verify/",
            {"note": "Physical verification confirms the guard is back in service."},
            format="json",
        )
        force_authenticate(request, user=build_user(process_ids=["SAF_P_022"], user_id="fm-1"))
        response = self.verify_view(request, id=action.pk)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post(
            f"/api/safety/corrective-actions/{action.pk}/transition/",
            {"status": CorrectiveAction.Status.CLOSED, "note": "CA closed after verification."},
            format="json",
        )
        force_authenticate(request, user=build_user(process_ids=["SAF_P_020"]))
        response = self.transition_view(request, id=action.pk)

        self.assertEqual(response.status_code, 200)
        action.refresh_from_db()
        self.assertEqual(action.status, CorrectiveAction.Status.CLOSED)
        self.assertTrue(action.physical_verification_done)
        self.assertIsNotNone(action.closed_at)
        self.assertEqual(action.closed_by, "dpa-1")
