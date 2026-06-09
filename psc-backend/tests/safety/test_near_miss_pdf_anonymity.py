from __future__ import annotations

from datetime import datetime
from io import BytesIO
from types import SimpleNamespace
import unittest

from PyPDF2 import PdfReader

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django(root_urlconf="config.urls")

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog
from apps.safety.views.near_miss_pdf import NearMissPDFDownloadView


def build_user(*, role_name: str, user_id: str) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_002"],
        process_ids=["SAF_P_023"],
        vessel_ids=["7"],
        is_global=role_name in {"DPA", "FM"},
    )


class NearMissPdfAnonymityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django(root_urlconf="config.urls")

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.view = NearMissPDFDownloadView.as_view()
        self.near_miss = Incident.objects.create(
            incident_number="NM/2026/061",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            near_miss_priority="HIGH",
            occurred_at=datetime.fromisoformat("2026-04-28T06:10:00+00:00"),
            reported_at=datetime.fromisoformat("2026-04-28T06:35:00+00:00"),
            narrative=(
                "The lookout identified an unsecured paint drum near a cargo-walkway before "
                "it could shift into the passage during heavy rolling."
            ),
            reporter_id="crew-61",
            reporter_name="Crew Reporter",
            reporter_rank="AB",
            reporter_email="crew61@example.test",
            reporter_department="Deck",
            reporter_device_fingerprint="device-61",
            created_by="crew-61",
            updated_by="dpa-1",
            schema_version=1,
        )
        IncidentPhaseLog.objects.create(
            incident=self.near_miss,
            phase_from=1,
            phase_to=1,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            loop_back_reason="Near-miss triaged HIGH.",
            actor_user_id="dpa-1",
            actor_role_code="DPA",
            schema_version=1,
        )

    def _render_text(self, *, role_name: str, user_id: str) -> str:
        request = self.factory.get(f"/api/safety/near-miss/{self.near_miss.pk}/pdf/")
        force_authenticate(request, user=build_user(role_name=role_name, user_id=user_id))
        response = self.view(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

        reader = PdfReader(BytesIO(response.content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def test_master_viewer_receives_masked_reporter_identity_in_pdf(self) -> None:
        text = self._render_text(role_name="MASTER", user_id="master-7")

        self.assertIn("Anonymous Reporter", text)
        self.assertNotIn("Crew Reporter", text)
        self.assertNotIn("Reporter identity is masked for this viewer.", text)

    def test_dpa_viewer_receives_visible_reporter_identity_in_pdf(self) -> None:
        text = self._render_text(role_name="DPA", user_id="dpa-1")

        self.assertIn("Crew Reporter", text)
        self.assertNotIn("Anonymous Reporter", text)
