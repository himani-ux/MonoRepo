from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4
import unittest

from tests.safety.support import bootstrap_django, recreate_incident_table, recreate_soi_tables


bootstrap_django(root_urlconf="config.urls")

from django.db import connection
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.safety.models import (
    CorrectiveAction,
    Incident,
    Recommendation,
    SCMAgendaItem,
    SCMMeeting,
    SafetyDashboardRollup,
    SOIFinding,
    SOIInspection,
)
from apps.safety.services.composite_score import CompositeScoreService, RollupScope
from apps.safety.views.dashboard import DashboardCompositeView, _list_available_vessels


def aware(year: int, month: int, day: int, hour: int = 0, minute: int = 0):
    return timezone.make_aware(datetime(year, month, day, hour, minute))


def build_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="master-7",
        username="master-7",
        role_name="MASTER",
        form_ids=["SAF_F_015"],
        process_ids=[],
        vessel_ids=["7"],
        is_global=False,
    )


class CompositeScoreServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django(root_urlconf="config.urls")

    def setUp(self) -> None:
        recreate_incident_table()
        recreate_soi_tables()
        self._recreate_dashboard_support_tables()
        self.current_at = aware(2026, 4, 30, 12, 0)
        self.service = CompositeScoreService(now_func=lambda: self.current_at)
        self.factory = APIRequestFactory()
        self.view = DashboardCompositeView.as_view()

        self.incident = Incident.objects.create(
            incident_number="INC/2026/071",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=6,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        closed_incident = Incident.objects.create(
            incident_number="INC/2026/072",
            vessel_id="7",
            record_type=Incident.RecordType.INCIDENT,
            state="CLOSED",
            current_phase=9,
            closed_at=self.current_at - timedelta(days=1),
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        open_near_miss = Incident.objects.create(
            incident_number="NM/2026/073",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="OFFICE_COMMENTS_COMPLETED",
            current_phase=1,
            created_by="crew-7",
            updated_by="dpa-1",
            schema_version=1,
        )
        closed_near_miss = Incident.objects.create(
            incident_number="NM/2026/074",
            vessel_id="7",
            record_type=Incident.RecordType.NEAR_MISS,
            state="CLOSED",
            current_phase=1,
            closed_at=self.current_at,
            created_by="crew-7",
            updated_by="dpa-1",
            schema_version=1,
        )
        other_vessel_incident = Incident.objects.create(
            incident_number="INC/2026/075",
            vessel_id="9",
            record_type=Incident.RecordType.INCIDENT,
            state="UNDER_REVIEW",
            current_phase=6,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        Incident.objects.filter(
            pk__in=[
                self.incident.pk,
                closed_incident.pk,
                open_near_miss.pk,
                closed_near_miss.pk,
                other_vessel_incident.pk,
            ]
        ).update(created_date=self.current_at)

        recommendation = Recommendation.objects.create(
            incident=self.incident,
            tier=Recommendation.Tier.CORRECTIVE,
            title="Replace failed guard",
            description="Correct the guard at the source.",
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        open_action = CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=self.incident.pk,
            recommendation=recommendation,
            title="Overdue corrective action",
            description="Waiting on vessel execution.",
            due_date=(self.current_at - timedelta(days=3)).date(),
            status=CorrectiveAction.Status.OPEN,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        closed_action = CorrectiveAction.objects.create(
            source_table="vims_safety_incident",
            source_id=closed_incident.pk,
            recommendation=recommendation,
            title="Closed corrective action",
            description="Already resolved.",
            due_date=(self.current_at - timedelta(days=1)).date(),
            status=CorrectiveAction.Status.CLOSED,
            closed_at=self.current_at,
            created_by="dpa-1",
            updated_by="dpa-1",
            schema_version=1,
        )
        CorrectiveAction.objects.filter(pk__in=[open_action.pk, closed_action.pk]).update(
            created_date=self.current_at
        )

        self.inspection = SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference="SOI/ABC/26/71",
            cycle_label="Q2/2026",
            state=SOIInspection.State.REPORTED,
            planned_date=self.current_at.date(),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            created_by="co-7",
            updated_by="co-7",
            schema_version=1,
        )
        SOIFinding.objects.create(
            inspection_id=self.inspection.id,
            area_id=3,
            title="Open bridge finding",
            description="Open vessel finding should count.",
            severity=SOIFinding.Severity.MED,
            priority=SOIFinding.Priority.MED,
            status=SOIFinding.Status.OPEN,
            created_date=self.current_at,
            created_by="co-7",
            schema_version=1,
        )
        SOIFinding.objects.create(
            inspection_id=self.inspection.id,
            area_id=8,
            title="Closed finding",
            description="Closed finding should not count.",
            severity=SOIFinding.Severity.LOW,
            priority=SOIFinding.Priority.LOW,
            status=SOIFinding.Status.CLOSED,
            created_date=self.current_at,
            created_by="co-7",
            schema_version=1,
        )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO master_soi_area (
                    area_id,
                    area_name,
                    section_12_flag,
                    display_order,
                    active,
                    seeded_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [3, "Navigating Bridge & Monkey Island", False, 3, True, "v1.0"],
            )
            cursor.execute(
                """
                INSERT INTO master_soi_area (
                    area_id,
                    area_name,
                    section_12_flag,
                    display_order,
                    active,
                    seeded_version
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [8, "Engine Control Room + Machinery Flat", False, 8, True, "v1.0"],
            )
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_vessel_area_map (
                    id,
                    vessel_id,
                    area_id,
                    applicable,
                    last_inspected_at,
                    due_at,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(uuid4()),
                    "7",
                    3,
                    True,
                    self.current_at - timedelta(days=30),
                    self.current_at + timedelta(days=60),
                    1,
                ],
            )
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_vessel_area_map (
                    id,
                    vessel_id,
                    area_id,
                    applicable,
                    last_inspected_at,
                    due_at,
                    schema_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    str(uuid4()),
                    "7",
                    8,
                    True,
                    self.current_at - timedelta(days=95),
                    self.current_at - timedelta(days=5),
                    1,
                ],
            )

    def test_build_rollup_returns_core_counts_and_composite_score(self) -> None:
        payload = self.service.build_rollup(
            scope=RollupScope(scope_type=SafetyDashboardRollup.ScopeType.VESSEL, scope_id="7"),
            period_code=SafetyDashboardRollup.PeriodCode.YEARS_3,
            as_of=self.current_at,
        )

        self.assertEqual(payload["metrics"]["open_incidents"], 1)
        self.assertEqual(payload["metrics"]["total_incidents"], 2)
        self.assertEqual(payload["metrics"]["open_near_misses"], 1)
        self.assertEqual(payload["metrics"]["total_near_misses"], 2)
        self.assertEqual(payload["metrics"]["open_findings"], 1)
        self.assertEqual(payload["metrics"]["total_findings"], 2)
        self.assertEqual(payload["metrics"]["overdue_corrective_actions"], 1)
        self.assertEqual(payload["metrics"]["total_corrective_actions"], 2)
        self.assertEqual(payload["metrics"]["soi_compliance_percent"], 50)
        self.assertEqual(payload["metrics"]["soi_compliance_label"], "SOI Compliance %")
        self.assertEqual(payload["composite_score"], 75)
        self.assertEqual(payload["score_status"], "AMBER")

    def test_dashboard_view_defaults_non_global_user_to_own_vessel(self) -> None:
        request = self.factory.get("/api/safety/dashboard/composite/?period=3y")
        force_authenticate(request, user=build_user())

        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["scope_type"], "VESSEL")
        self.assertEqual(response.data["scope_id"], "7")
        self.assertEqual(response.data["composite_score"], 75)
        self.assertEqual(
            response.data["available_vessels"],
            [
                {
                    "id": "7",
                    "vessel_code": "7",
                    "vessel_name": "Vessel 7",
                }
            ],
        )

    def test_available_vessels_uses_current_vessel_snapshot_when_present(self) -> None:
        vessels = _list_available_vessels(
            user=SimpleNamespace(
                user_type="VESSEL",
                vessel_id="7",
                vessel_code="MV07",
                vessel_name="MV Example",
            )
        )

        self.assertEqual(
            vessels,
            [
                {
                    "id": "7",
                    "vessel_code": "MV07",
                    "vessel_name": "MV Example",
                }
            ],
        )

    def _recreate_dashboard_support_tables(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys = OFF")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_dashboard_rollup")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_agenda")
            cursor.execute("DROP TABLE IF EXISTS vims_safety_scm_meeting")
            cursor.execute("PRAGMA foreign_keys = ON")

        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(SCMMeeting)
            schema_editor.create_model(SCMAgendaItem)
            schema_editor.create_model(SafetyDashboardRollup)
