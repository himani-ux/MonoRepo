from __future__ import annotations

from datetime import datetime, timedelta, timezone as dt_timezone
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from django.db import connection

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_near_miss_reference_tables


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.views.near_miss import NearMissListCreateView, NearMissRateLimitView


def build_user(*, role_name: str = "WIPER") -> SimpleNamespace:
    return SimpleNamespace(
        id="wiper-7",
        username="wiper-7",
        role_name=role_name,
        form_ids=["SAF_F_002"],
        process_ids=["SAF_P_001"],
        vessel_ids=["7"],
        is_global=False,
    )


def long_narrative(seed: int) -> str:
    return (
        f"Near miss {seed} involved unsecured stores shifting during rolling weather near frame {seed}, "
        "and the crew reported the exposure before it escalated into contact, injury, or equipment damage."
    )


class NearMissRateLimitTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_near_miss_reference_tables()
        self._recreate_wrh_ship_time_config()
        self.factory = APIRequestFactory()
        self.create_view = NearMissListCreateView.as_view()
        self.rate_limit_view = NearMissRateLimitView.as_view()

    def _recreate_wrh_ship_time_config(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS wrh_ship_time_config")
            cursor.execute(
                """
                CREATE TABLE wrh_ship_time_config (
                    vessel_id VARCHAR(64) PRIMARY KEY,
                    utc_offset_minutes INTEGER NOT NULL
                )
                """
            )
            cursor.execute(
                "INSERT INTO wrh_ship_time_config (vessel_id, utc_offset_minutes) VALUES ('7', 330)"
            )

    def _recreate_wrh_ship_time_config_effective_date(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS wrh_ship_time_config")
            cursor.execute(
                """
                CREATE TABLE wrh_ship_time_config (
                    id INTEGER PRIMARY KEY,
                    vessel_id VARCHAR(64) NOT NULL,
                    effective_date DATE NOT NULL,
                    tz_offset_minutes INTEGER NOT NULL
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO wrh_ship_time_config (id, vessel_id, effective_date, tz_offset_minutes)
                VALUES
                    (1, '7', '2026-04-01', 120),
                    (2, '7', '2026-04-28', 330)
                """
            )

    def _seed_submission(self, *, created_at: datetime, incident_number: str) -> None:
        near_miss = Incident.objects.create(
            incident_number=incident_number,
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="DRAFT",
            current_phase=1,
            narrative=long_narrative(0),
            near_miss_priority="LOW",
            reporter_id="wiper-7",
            reporter_name="Deck Wiper",
            reporter_rank="WIPER",
            created_by="wiper-7",
            updated_by="wiper-7",
            schema_version=1,
            reported_at=created_at,
        )
        Incident.objects.filter(pk=near_miss.pk).update(
            created_date=created_at,
            updated_date=created_at,
        )

    def _build_payload(self, *, narrative_seed: int, occurred_at: datetime | None = None) -> dict[str, object]:
        return {
            "vessel_id": "7",
            "vessel_code": "ABC",
            "incident_type_id": 1,
            "loss_type_primary_id": 1,
            "narrative": long_narrative(narrative_seed),
            "occurred_at": (occurred_at or datetime.now(dt_timezone.utc) - timedelta(minutes=10)).isoformat(),
            "near_miss_severity": "LOW",
            "near_miss_shell_tag": "Liveware",
            "near_miss_immediate_action": "Crew corrected the condition immediately.",
            "near_miss_suggestion": "Repeat the loose gear check before each watch.",
            "reporter_device_fingerprint": "device-wiper-7",
            "reporter_name": "Deck Wiper",
            "reporter_rank": "WIPER",
            "reporter_user_id": "wiper-7",
            "schema_version": 1,
        }

    def test_sixth_submission_in_same_vessel_local_day_is_rejected(self) -> None:
        base_time = datetime(2026, 4, 28, 6, 0, tzinfo=dt_timezone.utc)
        for index in range(5):
            self._seed_submission(
                created_at=base_time + timedelta(minutes=index),
                incident_number=f"DRAFT-ABC/2026/T{index + 1:03d}",
            )

        request = self.factory.post(
            "/api/safety/near-miss/",
            self._build_payload(narrative_seed=6, occurred_at=base_time - timedelta(minutes=10)),
            format="json",
        )
        force_authenticate(request, user=build_user())

        with patch("apps.safety.views.near_miss.timezone.now", return_value=base_time):
            response = self.create_view(request)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(
            response.data["detail"],
            "Rate-limit reached. Next submission allowed after 00:00 LT.",
        )
        self.assertEqual(response["Retry-After"], "45000")

    def test_submission_allowed_again_after_vessel_local_midnight_reset(self) -> None:
        current_time = datetime(2026, 4, 28, 6, 0, tzinfo=dt_timezone.utc)
        previous_local_day_utc = datetime(2026, 4, 27, 18, 10, tzinfo=dt_timezone.utc)
        for index in range(5):
            self._seed_submission(
                created_at=previous_local_day_utc + timedelta(minutes=index),
                incident_number=f"DRAFT-ABC/2026/T{index + 1:03d}",
            )

        request = self.factory.post(
            "/api/safety/near-miss/",
            self._build_payload(narrative_seed=7, occurred_at=current_time - timedelta(minutes=10)),
            format="json",
        )
        force_authenticate(request, user=build_user())

        with patch("apps.safety.views.near_miss.timezone.now", return_value=current_time):
            response = self.create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["record_type"], "NEAR_MISS")

    def test_rate_limit_status_endpoint_reports_remaining_capacity(self) -> None:
        base_time = datetime(2026, 4, 28, 6, 0, tzinfo=dt_timezone.utc)
        for index in range(2):
            self._seed_submission(
                created_at=base_time + timedelta(minutes=index),
                incident_number=f"DRAFT-ABC/2026/T{index + 1:03d}",
            )

        request = self.factory.get("/api/safety/near-miss/rate-limit/?vessel_id=7")
        force_authenticate(request, user=build_user())

        with patch("apps.safety.services.nm_rate_limiter.timezone.now", return_value=base_time):
            response = self.rate_limit_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["allowed"])
        self.assertEqual(response.data["limit"], 5)
        self.assertEqual(response.data["used"], 2)
        self.assertEqual(response.data["remaining"], 3)
        self.assertEqual(response.data["scope"], "vessel_local_day")

    def test_rate_limit_status_rejects_other_reporter_identity_for_non_dpa_fm(self) -> None:
        request = self.factory.get("/api/safety/near-miss/rate-limit/?crew_id=other-user&vessel_id=7")
        force_authenticate(request, user=build_user(role_name="MASTER"))

        response = self.rate_limit_view(request)

        self.assertEqual(response.status_code, 403)

    def test_rate_limit_uses_effective_date_timezone_config_when_present(self) -> None:
        self._recreate_wrh_ship_time_config_effective_date()
        limiter_time = datetime(2026, 4, 28, 6, 0, tzinfo=dt_timezone.utc)

        request = self.factory.get("/api/safety/near-miss/rate-limit/?vessel_id=7")
        force_authenticate(request, user=build_user())

        with patch("apps.safety.services.nm_rate_limiter.timezone.now", return_value=limiter_time):
            response = self.rate_limit_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["scope"], "vessel_local_day")
        self.assertEqual(response.data["remaining"], 5)
        self.assertEqual(
            response.data["reset_at"],
            datetime(2026, 4, 28, 18, 30, tzinfo=dt_timezone.utc),
        )
