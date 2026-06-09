from __future__ import annotations

from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, NearMissGuidancePrompt, NearMissKpiTarget, SafetyFieldHistory
from apps.safety.views.near_miss_config import (
    NearMissCategoryReclassifyView,
    NearMissGuidancePromptView,
    NearMissKpiTargetView,
)


def dpa_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="dpa-1",
        username="dpa-1",
        role_name="DPA",
        form_ids=["SAF_F_002"],
        process_ids=["SAF_P_002", "SAF_P_006"],
        vessel_ids=["7"],
        is_global=True,
    )


class NearMissConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.near_miss = Incident.objects.create(
            incident_number="NM/ARYA/2026/001",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state=Incident.State.READY_FOR_OFFICE_COMMENTS,
            current_phase=1,
            occurred_at=timezone.now(),
            reported_at=timezone.now(),
            narrative="Crew observed a near miss and gave enough detail for the safety office to classify the report.",
            near_miss_shell_tag="Safety",
            created_by="crew-7",
            updated_by="crew-7",
            schema_version=1,
        )

    def test_guidance_prompt_endpoint_returns_active_prompts(self) -> None:
        NearMissGuidancePrompt.objects.create(
            category_tag="Safety",
            prompt_text="Describe what almost happened.",
            display_order=1,
            created_by="test",
        )
        request = self.factory.get("/api/safety/near-miss/guidance-prompts/?category_tag=Safety")
        force_authenticate(request, user=dpa_user())

        response = NearMissGuidancePromptView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        rows = response.data["results"] if isinstance(response.data, dict) and "results" in response.data else response.data
        self.assertEqual(rows[0]["prompt_text"], "Describe what almost happened.")

    def test_kpi_target_endpoint_returns_actual_count_and_variance(self) -> None:
        now = timezone.localdate()
        NearMissKpiTarget.objects.create(
            vessel_id="7",
            year=now.year,
            month=now.month,
            target_count=3,
            created_by="test",
        )
        request = self.factory.get(
            f"/api/safety/near-miss/kpi-target/?vessel_id=7&year={now.year}&month={now.month}"
        )
        force_authenticate(request, user=dpa_user())

        response = NearMissKpiTargetView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["target_count"], 3)
        self.assertEqual(response.data["actual_count"], 1)
        self.assertEqual(response.data["variance"], -2)

    def test_reclassification_updates_category_and_audit_history(self) -> None:
        request = self.factory.patch(
            f"/api/safety/near-miss/{self.near_miss.pk}/reclassify/",
            {
                "near_miss_shell_tag": "Operational",
                "reason": "DPA corrected category after review.",
            },
            format="json",
        )
        force_authenticate(request, user=dpa_user())

        response = NearMissCategoryReclassifyView.as_view()(request, id=self.near_miss.pk)

        self.assertEqual(response.status_code, 200)
        self.near_miss.refresh_from_db()
        self.assertEqual(self.near_miss.near_miss_shell_tag, "Operational")
        self.assertTrue(
            SafetyFieldHistory.objects.filter(
                parent_id=self.near_miss.pk,
                field_name="near_miss_shell_tag",
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()
