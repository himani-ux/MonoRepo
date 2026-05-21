from __future__ import annotations
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.services.field_history_recorder import parse_history_value
from apps.safety.services.signature_chain import SignatureChainService


def build_user():
    return SimpleNamespace(id="dpa-1", username="dpa-1", role_name="DPA")


class HybridDigitalSignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.service = SignatureChainService()

    def test_signature_audit_row_stores_typed_name_timestamp_and_device_fingerprint(self) -> None:
        incident = Incident.objects.create(
            incident_number="ABC/2026/SIGN1",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=7,
            risk_band=Incident.RiskBand.YELLOW,
            reporter_id="rep-1",
            reporter_name="Reporter One",
            reporter_device_fingerprint="rep-device",
            reported_at="2026-04-27T10:00:00Z",
            created_by="rep-1",
            updated_by="rep-1",
            schema_version=1,
        )

        self.service.stamp_phase7_signature(
            incident,
            role_code=SignatureChainService.DPA,
            typed_name="DPA Reviewer",
            device_fingerprint="device-dpa-1",
            user=build_user(),
        )

        audit_row = SafetyFieldHistory.objects.get(field_name="phase7_signature_dpa")
        payload = parse_history_value(audit_row.new_value)
        self.assertEqual(payload["typed_name"], "DPA Reviewer")
        self.assertEqual(payload["device_fingerprint"], "device-dpa-1")
        self.assertTrue(payload["signed_at"])
