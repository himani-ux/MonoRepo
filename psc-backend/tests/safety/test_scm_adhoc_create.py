from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_scm_tables


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.views.scm import SCMListCreateView
from apps.safety.views.scm_adhoc import SCMCreateAdHocView


def build_user(
    *,
    role_name: str,
    process_ids: list[str] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_003"],
        process_ids=["SAF_P_001"] if process_ids is None else process_ids,
        vessel_ids=["7"],
        is_global=False,
    )


def build_sections() -> list[dict[str, object]]:
    return [
        {
            "agenda_item_number": index,
            "content": (
                f"Ad-Hoc section {index} discussion notes captured for a triggered meeting "
                "with enough detail to satisfy the SCM form expectations."
            ),
            "decision": f"Ad-Hoc decision outcome recorded for section {index}.",
        }
        for index in range(1, 11)
    ]


def build_payload() -> dict[str, object]:
    return {
        "vessel_id": "7",
        "vessel_code": "ABC",
        "meeting_type": "AD_HOC",
        "meeting_date": "2026-04-28",
        "meeting_time_local": "14:30:00",
        "location": "Singapore Anchorage",
        "voyage_no": "V2026-03",
        "chair_crew_id": "master-7",
        "ad_hoc_trigger_reason": (
            "RED-band incident follow-up requires a dedicated vessel discussion outside the monthly cycle."
        ),
        "sections": build_sections(),
    }


class SCMAdHocCreateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_scm_tables()
        self.factory = APIRequestFactory()
        self.list_create_view = SCMListCreateView.as_view()
        self.create_adhoc_view = SCMCreateAdHocView.as_view()

    def test_master_can_create_adhoc_scm_with_trigger_reason(self) -> None:
        request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(request, user=build_user(role_name="MASTER"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["meeting_type"], "AD_HOC")
        self.assertEqual(response.data["ad_hoc_trigger_reason"], build_payload()["ad_hoc_trigger_reason"])
        self.assertEqual(response.data["prepared_by_crew_id"], "master-7")
        self.assertEqual(len(response.data["sections"]), 10)

    def test_co_can_create_adhoc_scm_with_trigger_reason(self) -> None:
        request = self.factory.post("/api/safety/scm/", build_payload(), format="json")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["meeting_type"], "AD_HOC")
        self.assertEqual(response.data["prepared_by_crew_id"], "co-7")

    def test_adhoc_create_requires_trigger_reason(self) -> None:
        payload = build_payload()
        payload["ad_hoc_trigger_reason"] = ""
        request = self.factory.post("/api/safety/scm/", payload, format="json")
        force_authenticate(request, user=build_user(role_name="MASTER"))

        response = self.list_create_view(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("ad_hoc_trigger_reason", response.data)

    def test_master_can_load_adhoc_form_config(self) -> None:
        request = self.factory.get("/api/safety/scm/create-adhoc/?vessel_id=7")
        force_authenticate(request, user=build_user(role_name="MASTER"))

        response = self.create_adhoc_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meeting_type"], "AD_HOC")
        self.assertEqual(len(response.data["sections"]), 10)

    def test_co_can_load_adhoc_form_config(self) -> None:
        request = self.factory.get("/api/safety/scm/create-adhoc/?vessel_id=7")
        force_authenticate(request, user=build_user(role_name="CO", user_id="co-7"))

        response = self.create_adhoc_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meeting_type"], "AD_HOC")
