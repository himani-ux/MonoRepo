from __future__ import annotations

from types import SimpleNamespace
import unittest

from django.utils import timezone

from tests.safety.support import (
    bootstrap_django,
    recreate_incident_table,
    recreate_scm_tables,
    recreate_soi_tables,
)


bootstrap_django()

from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import Incident
from apps.safety.views.search import SafetyCrossRecordSearchView


def build_user(*, role_name: str = "DPA", user_id: str = "dpa-1"):
    return SimpleNamespace(
        id=user_id,
        username=user_id,
        role_name=role_name,
        form_ids=["SAF_F_005"],
        process_ids=[],
        vessel_ids=["7"],
        is_global=role_name in {"DPA", "FM"},
    )


class ArchiveOptInSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_incident_table()
        recreate_scm_tables()
        recreate_soi_tables()
        self.factory = APIRequestFactory()
        self.view = SafetyCrossRecordSearchView.as_view()
        self.current_at = timezone.now()
        self.active_incident = Incident.objects.create(
            incident_number="INC/2026/310",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=3,
            narrative="Manifold leak remains under active investigation.",
            occurred_at=self.current_at,
            created_by="master-7",
            updated_by="master-7",
            schema_version=1,
        )
        self.archived_incident = Incident.objects.create(
            incident_number="INC/2023/099",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="CLOSED",
            current_phase=9,
            narrative="Archived manifold case retained inside the soft-archive window.",
            occurred_at=self.current_at,
            is_archived=True,
            archived_at=self.current_at,
            created_by="dpa-7",
            updated_by="dpa-7",
            schema_version=1,
        )

    def test_search_excludes_archived_records_by_default(self) -> None:
        request = self.factory.get("/api/safety/search/?q=manifold")
        force_authenticate(request, user=build_user())

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["include_archived"])
        references = [row["reference"] for row in response.data["groups"]["INCIDENT"]]
        self.assertIn(self.active_incident.incident_number, references)
        self.assertNotIn(self.archived_incident.incident_number, references)

    def test_search_includes_archived_records_when_opted_in(self) -> None:
        request = self.factory.get("/api/safety/search/?q=manifold&include_archived=true")
        force_authenticate(request, user=build_user())

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["include_archived"])
        references = [row["reference"] for row in response.data["groups"]["INCIDENT"]]
        self.assertIn(self.active_incident.incident_number, references)
        self.assertIn(self.archived_incident.incident_number, references)
        archived_rows = {
            row["reference"]: row["archived"]
            for row in response.data["groups"]["INCIDENT"]
        }
        self.assertFalse(archived_rows[self.active_incident.incident_number])
        self.assertTrue(archived_rows[self.archived_incident.incident_number])
