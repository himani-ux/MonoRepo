from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django(root_urlconf="config.urls")

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, IncidentPhaseLog
from apps.safety.services.pdf_preview_generator import PdfPreviewGenerator
from apps.safety.views.incident_pdf import IncidentPDFDownloadView
from apps.safety.views.incident_phase7 import IncidentPhase7AcceptView


def build_user(*, role_name: str, user_id: str, process_ids: list[str]) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_001"],
        process_ids=process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


class IncidentPdfEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django(root_urlconf="config.urls")

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.accept_view = IncidentPhase7AcceptView.as_view()
        self.download_view = IncidentPDFDownloadView.as_view()

    def test_phase_seven_accept_generates_and_persists_pdf_export(self) -> None:
        incident = Incident.objects.create(
            incident_number="KSM-INC-2026-0099",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=7,
            risk_band=Incident.RiskBand.YELLOW,
            reporter_id="rep-7",
            reporter_name="Reporter Seven",
            reporter_device_fingerprint="device-reporter-7",
            reported_at=datetime.fromisoformat("2026-04-27T10:00:00+00:00"),
            narrative="Phase 7 acceptance path should emit the formal report export.",
            created_by="rep-7",
            updated_by="rep-7",
            schema_version=1,
        )
        IncidentPhaseLog.objects.create(
            incident=incident,
            phase_from=1,
            phase_to=2,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            actor_user_id="master-7",
            actor_role_code="MASTER",
            schema_version=1,
        )
        IncidentPhaseLog.objects.create(
            incident=incident,
            phase_from=5,
            phase_to=6,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            actor_user_id="hod-7",
            actor_role_code="HOD",
            schema_version=1,
        )

        original_export_root = os.environ.get("SAFETY_EXPORT_ROOT")
        export_root = Path("test-output") / "pdf-e2e"
        shutil.rmtree(export_root, ignore_errors=True)
        export_root.mkdir(parents=True, exist_ok=True)
        os.environ["SAFETY_EXPORT_ROOT"] = str(export_root)
        try:
            accept_request = self.factory.post(
                f"/api/safety/incidents/{incident.pk}/phase-7/accept/",
                {"typed_name": "DPA Reviewer", "device_fingerprint": "device-dpa-7"},
                format="json",
            )
            force_authenticate(
                accept_request,
                user=build_user(role_name="DPA", user_id="dpa-7", process_ids=["SAF_P_004"]),
            )

            accept_response = self.accept_view(accept_request, id=incident.pk)

            self.assertEqual(accept_response.status_code, 200)
            incident.refresh_from_db()
            self.assertEqual(incident.current_phase, 8)
            pdf_export = accept_response.data["pdf_export"]
            export_path = Path(pdf_export["export_path"])
            self.assertTrue(export_path.exists())
            self.assertIn(export_root.resolve(), export_path.parents)

            preview = PdfPreviewGenerator().build_preview(incident)
            self.assertTrue(preview["available"])
            self.assertEqual(preview["download_path"], f"/api/safety/incidents/{incident.pk}/pdf/")

            download_request = self.factory.get(f"/api/safety/incidents/{incident.pk}/pdf/")
            force_authenticate(
                download_request,
                user=build_user(role_name="DPA", user_id="dpa-7", process_ids=["SAF_P_023"]),
            )
            download_response = self.download_view(download_request, id=incident.pk)

            self.assertEqual(download_response.status_code, 200)
            self.assertEqual(download_response["Content-Type"], "application/pdf")
            self.assertEqual(download_response["X-Safety-Export-Path"], str(export_path))
        finally:
            shutil.rmtree(export_root, ignore_errors=True)
            if original_export_root is None:
                os.environ.pop("SAFETY_EXPORT_ROOT", None)
            else:
                os.environ["SAFETY_EXPORT_ROOT"] = original_export_root
