from __future__ import annotations

import unittest
from types import SimpleNamespace

from rest_framework import serializers

from apps.safety.authentication.anonymity import (
    ANONYMITY_PLACEHOLDER,
    AnonymityMixin,
    can_see_reporter,
)


class DummyNearMissSerializer(AnonymityMixin, serializers.Serializer):
    record_type = serializers.CharField()
    reporter_user_id = serializers.IntegerField(allow_null=True)
    reporter_name = serializers.CharField(allow_null=True)
    reporter_rank = serializers.CharField(allow_null=True)
    reporter_email = serializers.CharField(allow_null=True)
    created_by = serializers.IntegerField(allow_null=True)
    updated_by = serializers.IntegerField(allow_null=True)


def build_record():
    return {
        "record_type": "NEAR_MISS",
        "reporter_user_id": 44,
        "reporter_name": "Crew Reporter",
        "reporter_rank": "AB",
        "reporter_email": "crew@example.test",
        "created_by": 44,
        "updated_by": 98,
    }


class SafetyAnonymityTests(unittest.TestCase):
    def test_can_see_reporter_for_dpa_fm_and_self(self) -> None:
        record = build_record()

        self.assertTrue(can_see_reporter(SimpleNamespace(role_name="DPA", id=1), record))
        self.assertTrue(can_see_reporter(SimpleNamespace(role_name="FM", id=1), record))
        self.assertTrue(can_see_reporter(SimpleNamespace(role_name="MASTER", id=44), record))
        self.assertFalse(can_see_reporter(SimpleNamespace(role_name="MASTER", id=45), record))

    def test_near_miss_scrubs_reporter_pii_for_master_hod_and_co(self) -> None:
        for role_name in ("MASTER", "HOD", "CO"):
            serializer = DummyNearMissSerializer(
                instance=build_record(),
                context={"request": SimpleNamespace(user=SimpleNamespace(role_name=role_name, id=77))},
            )

            data = serializer.data

            self.assertEqual(data["reporter_name"], ANONYMITY_PLACEHOLDER)
            self.assertIsNone(data["reporter_user_id"])
            self.assertIsNone(data["reporter_rank"])
            self.assertIsNone(data["reporter_email"])
            self.assertIsNone(data["created_by"])
            self.assertIsNone(data["updated_by"])

    def test_near_miss_preserves_reporter_pii_for_dpa_fm_and_self(self) -> None:
        viewers = (
            SimpleNamespace(role_name="DPA", id=1),
            SimpleNamespace(role_name="FM", id=1),
            SimpleNamespace(role_name="MASTER", id=44),
        )

        for viewer in viewers:
            serializer = DummyNearMissSerializer(
                instance=build_record(),
                context={"request": SimpleNamespace(user=viewer)},
            )

            data = serializer.data

            self.assertEqual(data["reporter_name"], "Crew Reporter")
            self.assertEqual(data["reporter_user_id"], 44)
            self.assertEqual(data["reporter_rank"], "AB")
            self.assertEqual(data["reporter_email"], "crew@example.test")
            self.assertEqual(data["created_by"], 44)
            self.assertEqual(data["updated_by"], 98)

