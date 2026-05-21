from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident
from apps.safety.serializers.near_miss import NearMissSerializer


def build_viewer(role_name: str, *, user_id: str = "viewer-1") -> SimpleNamespace:
    return SimpleNamespace(role_name=role_name, id=user_id)


class NearMissAnonymitySerializerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.near_miss = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="DRAFT",
            current_phase=1,
            schema_version=1,
            narrative=(
                "A bosun noticed a loose ladder securing pin during routine rounds and "
                "reported it before anyone used the ladder in rough weather conditions."
            ),
            near_miss_priority="LOW",
            reporter_id="reporter-7",
            reporter_name="Crew Reporter",
            reporter_rank="BOSUN",
            reporter_email="reporter@example.test",
            reporter_department="Deck",
            reporter_device_fingerprint="device-7",
            created_by="reporter-7",
            updated_by="reporter-7",
        )

    def _serialize(self, viewer: SimpleNamespace) -> dict[str, object]:
        serializer = NearMissSerializer(
            instance=self.near_miss,
            context={"request": SimpleNamespace(user=viewer)},
        )
        return serializer.data

    def test_master_receives_masked_reporter_fields(self) -> None:
        data = self._serialize(build_viewer("MASTER"))

        self.assertEqual(data["reporter_name"], "Anonymous Reporter")
        self.assertIsNone(data["reporter_user_id"])
        self.assertIsNone(data["reporter_rank"])
        self.assertIsNone(data["reporter_email"])
        self.assertIsNone(data["reporter_department"])
        self.assertIsNone(data["reporter_device_fingerprint"])

    def test_dpa_and_fm_receive_full_identity(self) -> None:
        for role_name in ("DPA", "FM"):
            data = self._serialize(build_viewer(role_name))

            self.assertEqual(data["reporter_name"], "Crew Reporter")
            self.assertEqual(data["reporter_user_id"], "reporter-7")
            self.assertEqual(data["reporter_rank"], "BOSUN")
            self.assertEqual(data["reporter_email"], "reporter@example.test")

    def test_reporter_self_receives_full_identity(self) -> None:
        data = self._serialize(build_viewer("BOSUN", user_id="reporter-7"))

        self.assertEqual(data["reporter_name"], "Crew Reporter")
        self.assertEqual(data["reporter_user_id"], "reporter-7")
        self.assertEqual(data["reporter_rank"], "BOSUN")
