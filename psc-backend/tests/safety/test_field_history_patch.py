from __future__ import annotations

from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident, SafetyFieldHistory
from apps.safety.views.incident import IncidentDetailView


def build_user(
    *,
    role_name: str = "MASTER",
    form_ids: list[str] | None = None,
    process_ids: list[str] | None = None,
    vessel_ids: list[str] | None = None,
    user_id: str = "master-7",
):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=form_ids or ["SAF_F_001"],
        process_ids=process_ids or ["SAF_P_001"],
        vessel_ids=vessel_ids or ["7"],
        is_global=False,
    )


class FieldHistoryPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.factory = APIRequestFactory()
        self.detail_view = IncidentDetailView.as_view()

    def test_patch_writes_one_field_history_row_per_changed_field(self) -> None:
        incident = Incident.objects.create(
            incident_number="DRAFT-ABC/2026/T001",
            vessel_id="7",
            state="DRAFT",
            created_by="master-7",
            schema_version=1,
            narrative="Before update",
            risk_band=Incident.RiskBand.GREEN,
        )

        patch_request = self.factory.patch(
            f"/api/safety/incidents/{incident.id}/",
            {
                "narrative": "After update",
                "risk_band": Incident.RiskBand.RED,
            },
            format="json",
        )
        force_authenticate(patch_request, user=build_user())

        response = self.detail_view(patch_request, id=incident.id)

        self.assertEqual(response.status_code, 200)
        rows = list(
            SafetyFieldHistory.objects.order_by("field_name").values(
                "parent_table",
                "parent_id",
                "field_name",
                "old_value",
                "new_value",
            )
        )
        self.assertEqual(
            rows,
            [
                {
                    "parent_table": "vims_safety_incident",
                    "parent_id": incident.id,
                    "field_name": "narrative",
                    "old_value": "Before update",
                    "new_value": "After update",
                },
                {
                    "parent_table": "vims_safety_incident",
                    "parent_id": incident.id,
                    "field_name": "risk_band",
                    "old_value": "GREEN",
                    "new_value": "RED",
                },
            ],
        )
