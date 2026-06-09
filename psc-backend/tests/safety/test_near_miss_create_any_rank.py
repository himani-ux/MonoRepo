from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_near_miss_reference_tables


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.near_miss import NearMissListCreateView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    user_id: str = "user-1",
    user_type: str = "VESSEL",
    vessel_id: str = "7",
    vessel_code: str = "ABC",
    full_name: str | None = None,
    rank: str | None = None,
    email: str | None = None,
    department: str | None = None,
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        full_name=full_name,
        rank=rank,
        email=email,
        department=department,
        user_type=user_type,
        role_name=role_name,
        form_ids=["SAF_F_002"],
        process_ids=["SAF_P_001"] if process_ids is None else process_ids,
        vessel_id=vessel_id,
        vessel_code=vessel_code,
        vessel_ids=[vessel_id],
        is_global=False,
    )


def build_payload(*, narrative: str) -> dict[str, object]:
    return {
        "vessel_id": "7",
        "vessel_code": "ABC",
        "incident_type_id": 1,
        "loss_type_primary_id": 1,
        "narrative": narrative,
        "occurred_at": (timezone.now() - timedelta(minutes=10)).isoformat(),
        "near_miss_severity": "MED",
        "near_miss_shell_tag": "Liveware",
        "near_miss_mscat_subcode_id": "10.01",
        "near_miss_immediate_action": "The unsecured item was moved away from the work path.",
        "near_miss_suggestion": "Add a pre-watch loose gear check during rolling weather.",
        "reporter_device_fingerprint": "device-wiper-7",
        "reporter_name": "Deck Wiper",
        "reporter_rank": "WIPER",
        "reporter_user_id": "wiper-7",
        "schema_version": 1,
    }


class NearMissCreateAnyRankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_near_miss_reference_tables()
        self.factory = APIRequestFactory()
        self.view = NearMissListCreateView.as_view()

    def test_wiper_can_create_near_miss_with_create_permission(self) -> None:
        request = self.factory.post(
            "/api/safety/near-miss/",
            build_payload(
                narrative=(
                    "Crew member observed an unsecured paint drum on the aft deck during "
                    "heavy rolling and reported the exposure before it struck personnel."
                )
            ),
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="WIPER", process_ids=["SAF_P_001"], user_id="wiper-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["record_type"], "NEAR_MISS")
        self.assertEqual(response.data["state"], "PENDING_VESSEL_REVIEW")
        self.assertEqual(response.data["reporter_name"], "wiper-7")

    def test_vessel_user_create_uses_authenticated_vessel_context(self) -> None:
        request = self.factory.post(
            "/api/safety/near-miss/",
            {
                "incident_type_id": 1,
                "loss_type_primary_id": 1,
                "narrative": (
                    "Crew member observed a loose portable pump bracket near the starboard "
                    "manifold and reported it before vibration could cause contact injury "
                    "or equipment damage during cargo watch."
                ),
                "occurred_at": (timezone.now() - timedelta(minutes=10)).isoformat(),
                "near_miss_severity": "LOW",
                "near_miss_shell_tag": "Hardware",
                "near_miss_immediate_action": "The bracket was isolated and marked for inspection.",
                "near_miss_suggestion": "Add bracket checks to the pre-cargo watch walk-around.",
                "reporter_device_fingerprint": "device-wiper-ef90",
                "reporter_name": "Deck Wiper",
                "reporter_rank": "WIPER",
                "reporter_user_id": "wiper-ef90",
                "schema_version": 1,
            },
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(
                role_name="WIPER",
                process_ids=["SAF_P_001"],
                user_id="wiper-ef90",
                vessel_id="EF9029C2-A192-EF11-A9F2-933342524037",
                vessel_code="MVX",
            ),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["vessel_id"], "EF9029C2-A192-EF11-A9F2-933342524037")
        self.assertTrue(str(response.data["incident_number"]).startswith("DRAFT-MVX/"))

    def test_create_accepts_place_and_up_to_three_near_miss_classifiers(self) -> None:
        payload = build_payload(
            narrative=(
                "Crew member observed loose securing around a portable pump and reported "
                "the exposure before the item could shift into the access path during sea passage."
            )
        )
        payload.update(
            {
                "near_miss_place": "AT_SEA",
                "near_miss_category_tags": ["Safety", "Operational", "Environment"],
                "near_miss_incident_type_ids": [1, 2, 3],
                "near_miss_mscat_subcode_ids": ["10.01", "10.02", "10.03"],
            }
        )
        request = self.factory.post("/api/safety/near-miss/", payload, format="json")
        force_authenticate(
            request,
            user=build_user(role_name="WIPER", process_ids=["SAF_P_001"], user_id="wiper-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["near_miss_place"], "AT_SEA")
        self.assertEqual(response.data["near_miss_shell_tag"], "Safety")
        self.assertEqual(response.data["near_miss_category_tags"], ["Safety", "Operational", "Environment"])
        self.assertEqual(str(response.data["incident_type_id"]), "1")
        self.assertEqual(response.data["near_miss_incident_type_ids"], [1, 2, 3])
        self.assertEqual(response.data["near_miss_mscat_subcode_id"], "10.01")
        self.assertEqual(response.data["near_miss_mscat_subcode_ids"], ["10.01", "10.02", "10.03"])

    def test_create_rejects_more_than_three_near_miss_classifiers(self) -> None:
        payload = build_payload(
            narrative=(
                "Crew member observed loose securing around a portable pump and reported "
                "the exposure before the item could shift into the access path during sea passage."
            )
        )
        payload["near_miss_category_tags"] = ["Safety", "Operational", "Environment", "Training"]
        request = self.factory.post("/api/safety/near-miss/", payload, format="json")
        force_authenticate(
            request,
            user=build_user(role_name="WIPER", process_ids=["SAF_P_001"], user_id="wiper-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("near_miss_category_tags", response.data)

    def test_missing_create_permission_is_rejected(self) -> None:
        request = self.factory.post(
            "/api/safety/near-miss/",
            build_payload(
                narrative=(
                    "Crew member observed an unsecured paint drum on the aft deck during "
                    "heavy rolling and reported the exposure before it struck personnel."
                )
            ),
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="WIPER", process_ids=[], user_id="wiper-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 403)

    def test_narrative_shorter_than_100_characters_is_rejected(self) -> None:
        request = self.factory.post(
            "/api/safety/near-miss/",
            build_payload(narrative="Too short to satisfy the minimum near-miss detail rule."),
            format="json",
        )
        force_authenticate(
            request,
            user=build_user(role_name="WIPER", process_ids=["SAF_P_001"], user_id="wiper-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("narrative", response.data)

    def test_reporter_device_fingerprint_is_required(self) -> None:
        payload = build_payload(
            narrative=(
                "Crew member observed an unsecured paint drum on the aft deck during "
                "heavy rolling and reported the exposure before it struck personnel."
            )
        )
        payload.pop("reporter_device_fingerprint")
        request = self.factory.post("/api/safety/near-miss/", payload, format="json")
        force_authenticate(
            request,
            user=build_user(role_name="WIPER", process_ids=["SAF_P_001"], user_id="wiper-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("reporter_device_fingerprint", response.data)

    def test_occurred_at_is_required(self) -> None:
        payload = build_payload(
            narrative=(
                "Crew member observed a portable ladder standing unsecured near the "
                "work site and reported the exposure before it could fall into the "
                "access route during deck rounds."
            )
        )
        payload.pop("occurred_at")
        request = self.factory.post("/api/safety/near-miss/", payload, format="json")
        force_authenticate(
            request,
            user=build_user(role_name="WIPER", process_ids=["SAF_P_001"], user_id="wiper-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("occurred_at", response.data)

    def test_create_ignores_reporter_supplied_priority_until_dpa_triage(self) -> None:
        payload = build_payload(
            narrative=(
                "Crew member observed an unsecured paint drum on the aft deck during "
                "heavy rolling and reported the exposure before it struck personnel."
            )
        )
        payload["near_miss_priority"] = "HIGH"
        request = self.factory.post("/api/safety/near-miss/", payload, format="json")
        force_authenticate(
            request,
            user=build_user(role_name="WIPER", process_ids=["SAF_P_001"], user_id="wiper-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.data["near_miss_priority"])

    def test_create_uses_authenticated_reporter_identity_not_client_supplied_identity(self) -> None:
        payload = build_payload(
            narrative=(
                "Crew member observed a loose lashing point near the bunker station and reported "
                "the exposure before the watch team could be placed in the line of fire."
            )
        )
        payload.update(
            {
                "reporter_name": "Spoofed Reporter",
                "reporter_rank": "MASTER",
                "reporter_user_id": "spoofed-user",
                "reporter_email": "spoofed@example.test",
                "reporter_department": "Office",
            }
        )
        request = self.factory.post("/api/safety/near-miss/", payload, format="json")
        force_authenticate(
            request,
            user=build_user(
                role_name="WIPER",
                process_ids=["SAF_P_001"],
                user_id="wiper-auth",
                full_name="Authenticated Wiper",
                rank="WIPER",
                email="wiper@example.test",
                department="Deck",
            ),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["reporter_name"], "Authenticated Wiper")
        self.assertEqual(response.data["reporter_rank"], "WIPER")
        self.assertEqual(response.data["reporter_user_id"], "wiper-auth")
        self.assertEqual(response.data["reporter_email"], "wiper@example.test")
        self.assertEqual(response.data["reporter_department"], "Deck")

    def test_future_occurred_at_is_rejected_when_reported_at_is_omitted(self) -> None:
        payload = build_payload(
            narrative=(
                "Crew member observed a portable light cable stretched across the access route "
                "and reported the exposure before anyone tripped during the night watch."
            )
        )
        payload["occurred_at"] = (timezone.now() + timedelta(minutes=5)).isoformat()
        payload.pop("reported_at", None)
        request = self.factory.post("/api/safety/near-miss/", payload, format="json")
        force_authenticate(
            request,
            user=build_user(role_name="WIPER", process_ids=["SAF_P_001"], user_id="wiper-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("occurred_at", response.data)

    def test_occurred_at_after_reported_at_is_rejected(self) -> None:
        reported_at = timezone.now() - timedelta(hours=1)
        payload = build_payload(
            narrative=(
                "Crew member observed a temporary hose crossing near the manifold "
                "and reported the trip exposure before the cargo watch changed over."
            )
        )
        payload["reported_at"] = reported_at.isoformat()
        payload["occurred_at"] = (reported_at + timedelta(minutes=5)).isoformat()
        request = self.factory.post("/api/safety/near-miss/", payload, format="json")
        force_authenticate(
            request,
            user=build_user(role_name="WIPER", process_ids=["SAF_P_001"], user_id="wiper-7"),
        )

        response = self.view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["occurred_at"][0], "Occurred time cannot be after reported time.")
