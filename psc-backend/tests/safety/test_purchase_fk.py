from __future__ import annotations

import unittest

from django.db import connection

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_purchase_requisition_table,
)


bootstrap_django()

from apps.safety.models import CorrectiveAction, Incident, Recommendation
from apps.safety.services.purchase_fk_enforcer import (
    PurchaseFKEnforcer,
    PurchaseFKEnforcerError,
)


class PurchaseForeignKeyEnforcerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_purchase_requisition_table()
        self.enforcer = PurchaseFKEnforcer()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/PFK1",
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
                [9001, "SUBMITTED", 0],
            )

    def test_archive_blocked_while_linked_corrective_action_is_open(self) -> None:
        CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=self.incident.pk,
            recommendation=self.recommendation,
            title="Replace failed guard",
            description="Immediate vessel corrective action.",
            verifier_user_id="dpa-1",
            due_date="2026-05-30",
            status=CorrectiveAction.Status.OPEN,
            purchase_req_id=9001,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        with self.assertRaises(PurchaseFKEnforcerError) as context:
            self.enforcer.ensure_archive_allowed(9001)

        self.assertIn("Requisition cannot be archived", str(context.exception))

    def test_archive_unblocks_once_linked_corrective_action_is_closed(self) -> None:
        CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=self.incident.pk,
            recommendation=self.recommendation,
            title="Replace failed guard",
            description="Immediate vessel corrective action.",
            verifier_user_id="dpa-1",
            due_date="2026-05-30",
            status=CorrectiveAction.Status.CLOSED,
            purchase_req_id=9001,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        self.enforcer.ensure_archive_allowed(9001)
