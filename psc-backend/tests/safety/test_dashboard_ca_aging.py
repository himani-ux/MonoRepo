from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_scm_tables


bootstrap_django(root_urlconf="config.urls")

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import CorrectiveAction, Incident, Recommendation
from apps.safety.services.dashboard_ca_aging import DashboardCorrectiveActionAgingService
from apps.safety.views.dashboard import DashboardCAAgingView


def build_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="dpa-1",
        username="dpa-1",
        role_name="DPA",
        form_ids=["SAF_F_015"],
        process_ids=[],
        vessel_ids=["7"],
        is_global=False,
    )


class DashboardCAAgingViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django(root_urlconf="config.urls")

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_scm_tables()
        self.factory = APIRequestFactory()
        self.view = DashboardCAAgingView.as_view()
        self.service = DashboardCorrectiveActionAgingService()

        self.vessel_7_incident = Incident.objects.create(
            incident_number="INC/2026/CAA-7",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=6,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        self.vessel_9_incident = Incident.objects.create(
            incident_number="INC/2026/CAA-9",
            vessel_id="9",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=6,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        self.recommendation_7 = Recommendation.objects.create(
            incident=self.vessel_7_incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Vessel 7 corrective action",
            description="Bridge-side corrective action.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        self.recommendation_9 = Recommendation.objects.create(
            incident=self.vessel_9_incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Vessel 9 corrective action",
            description="Engine-side corrective action.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

        self._create_action(self.recommendation_7, age_days=10, status=CorrectiveAction.Status.OPEN)
        self._create_action(self.recommendation_7, age_days=20, status=CorrectiveAction.Status.IN_PROGRESS)
        self._create_action(self.recommendation_7, age_days=40, status=CorrectiveAction.Status.PENDING_VERIFY)
        self._create_action(self.recommendation_7, age_days=60, status=CorrectiveAction.Status.REOPENED)
        self._create_action(self.recommendation_7, age_days=90, status=CorrectiveAction.Status.CLOSED)
        self._create_action(self.recommendation_9, age_days=12, status=CorrectiveAction.Status.OPEN)

    def _create_action(
        self,
        recommendation: Recommendation,
        *,
        age_days: int,
        status: str,
    ) -> CorrectiveAction:
        action = CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=recommendation.incident_id,
            recommendation=recommendation,
            title=f"CA {age_days}",
            description="Dashboard aging fixture.",
            status=status,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        created_at = timezone.now() - timedelta(days=age_days)
        CorrectiveAction.objects.filter(pk=action.pk).update(created_date=created_at)
        action.refresh_from_db()
        return action

    def test_service_builds_bucket_counts_without_resetting_reopened_age(self) -> None:
        payload = self.service.build_panel(vessel_id="7")

        bucket_counts = {entry["bucket"]: entry["count"] for entry in payload["buckets"]}
        self.assertEqual(payload["label"], "CA Aging Pipeline")
        self.assertEqual(payload["open_action_count"], 4)
        self.assertEqual(bucket_counts["0-15"], 1)
        self.assertEqual(bucket_counts["15-30"], 1)
        self.assertEqual(bucket_counts["30-45"], 1)
        self.assertEqual(bucket_counts["45+"], 1)
        self.assertGreaterEqual(payload["oldest_age_days"], 60)

    def test_view_defaults_to_authenticated_vessel_scope(self) -> None:
        request = self.factory.get("/api/safety/dashboard/ca-aging/")
        force_authenticate(request, user=build_user())

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["scope_type"], "VESSEL")
        self.assertEqual(response.data["scope_id"], "7")
        self.assertEqual(response.data["open_action_count"], 4)
