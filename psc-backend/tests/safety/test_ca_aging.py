from __future__ import annotations

from datetime import timedelta
import unittest

from django.utils import timezone

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import CorrectiveAction, Incident, Recommendation
from apps.safety.services.ca_aging import CorrectiveActionAgingService


class CorrectiveActionAgingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.service = CorrectiveActionAgingService()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/CAA1",
            vessel_id="7",
            state="UNDER_REVIEW",
            current_phase=6,
            risk_band=Incident.RiskBand.YELLOW,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        self.recommendation = Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Replace failed control",
            description="Immediate vessel corrective action.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )

    def _create_action(self, *, age_days: int, status: str = CorrectiveAction.Status.OPEN) -> CorrectiveAction:
        action = CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=self.incident.pk,
            recommendation=self.recommendation,
            title="Replace failed control",
            description="Immediate vessel corrective action.",
            verifier_user_id="dpa-1",
            due_date="2026-05-30",
            status=status,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        created_at = timezone.now() - timedelta(days=age_days)
        CorrectiveAction.objects.filter(pk=action.pk).update(created_date=created_at)
        action.refresh_from_db()
        return action

    def test_sync_bucket_uses_creation_date_thresholds(self) -> None:
        expectations = {
            5: "0-15",
            16: "15-30",
            31: "30-45",
            60: "45+",
        }

        for age_days, expected_bucket in expectations.items():
            action = self._create_action(age_days=age_days)
            bucket = self.service.sync_bucket(action)
            action.refresh_from_db()
            self.assertEqual(bucket, expected_bucket)
            self.assertEqual(action.aging_bucket, expected_bucket)

    def test_reopened_action_keeps_original_clock(self) -> None:
        action = self._create_action(age_days=48, status=CorrectiveAction.Status.REOPENED)

        bucket = self.service.sync_bucket(action)

        self.assertEqual(bucket, "45+")
