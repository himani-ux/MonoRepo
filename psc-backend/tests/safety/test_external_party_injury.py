from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import ExternalPartyInjury, Incident
from apps.safety.views.incident_external_party import IncidentExternalPartyInjuryView


def build_user(*, role_name: str, process_ids: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        id="master-1",
        username="master-1",
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class ExternalPartyInjuryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = IncidentExternalPartyInjuryView.as_view()

    def _incident(self) -> Incident:
        return Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T012",
            vessel_id="7",
            state="DRAFT",
            current_phase=1,
            created_by="master-1",
            updated_by="master-1",
            schema_version=1,
        )

    def test_post_creates_external_party_injury_record(self) -> None:
        incident = self._incident()
        request = self.factory.post(
            f"/api/safety/incidents/{incident.pk}/external-party/",
            {
                "party_name": "Pilot John",
                "party_type": "PILOT",
                "company_name": "Harbor Ops",
                "severity": "LOST_TIME",
                "notes": "Escort-ladder slip during berthing.",
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="MASTER", process_ids=["SAF_P_001"]))

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 201)
        record = ExternalPartyInjury.objects.get(incident=incident)
        self.assertEqual(record.party_type, ExternalPartyInjury.PartyType.PILOT)
        self.assertEqual(record.company_name, "Harbor Ops")

    def test_patch_updates_existing_external_party_injury_record(self) -> None:
        incident = self._incident()
        ExternalPartyInjury.objects.create(
            incident=incident,
            party_name="Contractor A",
            party_type=ExternalPartyInjury.PartyType.CONTRACTOR,
            company_name="Yard Team",
            severity="MEDICAL_TREATMENT",
            notes="Initial note.",
            created_by="master-1",
            updated_by="master-1",
            schema_version=1,
        )
        request = self.factory.patch(
            f"/api/safety/incidents/{incident.pk}/external-party/",
            {
                "severity": "LOST_TIME",
                "notes": "Updated after shore clinic review.",
            },
            format="json",
        )
        force_authenticate(request, user=build_user(role_name="DPA", process_ids=["SAF_P_001"]))

        response = self.view(request, id=incident.pk)

        self.assertEqual(response.status_code, 200)
        record = ExternalPartyInjury.objects.get(incident=incident)
        self.assertEqual(record.severity, "LOST_TIME")
        self.assertEqual(record.notes, "Updated after shore clinic review.")
