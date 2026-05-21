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
from apps.safety.views.corrective_action import CorrectiveActionListCreateView


def build_user(*, user_id: str = "dpa-1"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name="DPA",
        form_ids=["SAF_F_001"],
        process_ids=[],
        vessel_ids=["7"],
        is_global=False,
    )


class CorrectiveActionPurchaseStatusLiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_purchase_requisition_table()
        self.factory = APIRequestFactory()
        self.list_view = CorrectiveActionListCreateView.as_view()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/CASL1",
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

    def test_corrective_action_list_returns_live_purchase_status(self) -> None:
        CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=self.incident.pk,
            recommendation=self.recommendation,
            title="Replace failed guard",
            description="Immediate vessel corrective action.",
            verifier_user_id="dpa-1",
            due_date="2026-05-30",
            status=CorrectiveAction.Status.OPEN,
            purchase_req_id=9101,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE pur_requisition SET status = %s, is_archived = %s WHERE id = %s",
                ["APPROVED", 0, 9101],
            )

        request = self.factory.get("/api/safety/corrective-actions/?incident_id=%s" % self.incident.pk)
        force_authenticate(request, user=build_user())
        response = self.list_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["purchase_req_id"], 9101)
        self.assertEqual(response.data[0]["purchase_request"]["status"], "APPROVED")
        self.assertFalse(response.data[0]["purchase_request"]["is_archived"])
