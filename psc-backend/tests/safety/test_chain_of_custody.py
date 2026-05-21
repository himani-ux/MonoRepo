from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.views.incident_phase3 import IncidentPhase3ChainOfCustodyView


def build_user(user_id: str = "dpa-1", role_name: str = "DPA"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=["SAF_P_002"],
        vessel_ids=["7"],
        is_global=False,
    )


class ChainOfCustodyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = IncidentPhase3ChainOfCustodyView.as_view()

    def test_chain_of_custody_transfer_is_audit_logged(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        create_request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/chain-of-custody/",
            {
                "description": "Burnt relay recovered from engine control room.",
                "collection_timestamp": "2026-04-27T08:30:00+00:00",
                "collector_name": "Chief Engineer",
                "collector_signature": "CE-signature",
                "storage_location": "Evidence locker bag #44",
                "witness_signature": "Master-signature",
                "current_holder": "Chief Engineer",
            },
            format="json",
        )
        force_authenticate(create_request, user=build_user())

        create_response = self.view(create_request, id=incident.pk)
        self.assertEqual(create_response.status_code, 201)
        chain_id = create_response.data["id"]

        transfer_request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/chain-of-custody/",
            {
                "chain_of_custody_id": chain_id,
                "handover_timestamp": "2026-04-27T10:00:00+00:00",
                "handover_from": "Chief Engineer",
                "handover_to": "DPA",
            },
            format="json",
        )
        force_authenticate(transfer_request, user=build_user())

        transfer_response = self.view(transfer_request, id=incident.pk)

        self.assertEqual(transfer_response.status_code, 200)
        self.assertEqual(len(transfer_response.data["handover_log"]), 1)
        self.assertEqual(transfer_response.data["current_holder"], "DPA")
        self.assertEqual(
            SafetyFieldHistory.objects.filter(
                parent_table="vims_safety_chain_of_custody",
                field_name="handover_log",
            ).count(),
            1,
        )

        incident.refresh_from_db()
        self.assertTrue(incident.chain_of_custody_ok)

    def test_chain_of_custody_requires_witness_signature(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/001",
            vessel_id="7",
            state="IN_PROGRESS",
            current_phase=3,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/chain-of-custody/",
            {
                "description": "Burnt relay recovered from engine control room.",
                "collection_timestamp": "2026-04-27T08:30:00+00:00",
                "collector_name": "Chief Engineer",
                "collector_signature": "CE-signature",
                "storage_location": "Evidence locker bag #44",
            },
            format="json",
        )
        force_authenticate(request, user=build_user())

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 400)
        self.assertIn("witness_signature", response.data)
