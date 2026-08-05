from __future__ import annotations

from datetime import datetime
from io import BytesIO
import unittest

from PyPDF2 import PdfReader

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.services.pdf_renderer import IncidentPdfRenderer


class IncidentPdfSignatureBandTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()

    def test_signature_rows_are_not_risk_band_specific(self) -> None:
        cases = [
            Incident.RiskBand.GREEN,
            Incident.RiskBand.YELLOW,
            Incident.RiskBand.RED,
        ]

        for index, band in enumerate(cases, start=1):
            with self.subTest(risk_band=band):
                incident = Incident.objects.create(
                    incident_number=f"KSM-INC-2026-00{index}",
                    vessel_id="7",
                    state="APPROVED",
                    current_phase=8,
                    risk_band=band,
                    imo_classifier=Incident.ImoClassifier.MI,
                    reported_at=datetime.fromisoformat("2026-04-27T10:00:00+00:00"),
                    reporter_id="rep-7",
                    reporter_name="Reporter Seven",
                    reporter_device_fingerprint="device-reporter-7",
                    created_by="rep-7",
                    updated_by="rep-7",
                    schema_version=1,
                )
                incident.dpa_accepted_by = "pic-or-dpa-7"
                incident.dpa_accepted_at = datetime.fromisoformat("2026-04-28T08:00:00+00:00")
                incident.save(
                    update_fields=[
                        "dpa_accepted_by",
                        "dpa_accepted_at",
                    ]
                )

                result = IncidentPdfRenderer().render_incident_pdf(
                    incident_id=incident.pk,
                    viewer_user=None,
                    persist=False,
                )
                text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(result.content)).pages)

                for label in [
                    "Reporter signature",
                    "PIC / DPA office",
                ]:
                    self.assertIn(label, text)
                for label in ["Master signature", "HOD signature", "PIC closer signature", "FM signature"]:
                    self.assertNotIn(label, text)
