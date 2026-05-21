from __future__ import annotations

import unittest

from django.db import IntegrityError

from tests.safety.support import bootstrap_django, recreate_incident_table


bootstrap_django()

from apps.safety.models import Incident, IncidentPhaseLog


class PhaseLogShapeFinalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_incident_table()
        self.incident = Incident.objects.create(
            incident_number="ABC/2026/PHASELOG",
            vessel_id="7",
            state="DRAFT",
            current_phase=1,
            created_by="master-7",
            schema_version=1,
        )

    def test_phase_to_must_stay_within_nine_phase_workflow(self) -> None:
        with self.assertRaises(IntegrityError):
            IncidentPhaseLog.objects.create(
                incident=self.incident,
                phase_from=9,
                phase_to=10,
                transition_type=IncidentPhaseLog.TransitionType.CLOSE,
                actor_user_id="dpa-1",
                actor_role_code="DPA",
                schema_version=1,
            )

    def test_phase_from_must_be_null_or_a_documented_phase_number(self) -> None:
        with self.assertRaises(IntegrityError):
            IncidentPhaseLog.objects.create(
                incident=self.incident,
                phase_from=0,
                phase_to=3,
                transition_type=IncidentPhaseLog.TransitionType.REWORK,
                loop_back_reason="Need more evidence from the bridge team.",
                actor_user_id="dpa-1",
                actor_role_code="DPA",
                schema_version=1,
            )

    def test_loop_back_requires_non_empty_reason(self) -> None:
        with self.assertRaises(IntegrityError):
            IncidentPhaseLog.objects.create(
                incident=self.incident,
                phase_from=5,
                phase_to=3,
                transition_type=IncidentPhaseLog.TransitionType.LOOP_BACK,
                loop_back_reason="",
                actor_user_id="dpa-1",
                actor_role_code="DPA",
                schema_version=1,
            )

    def test_phase_log_signature_valid_defaults_true(self) -> None:
        phase_log = IncidentPhaseLog.objects.create(
            incident=self.incident,
            phase_from=1,
            phase_to=2,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            actor_user_id="master-7",
            actor_role_code="MASTER",
            device_fingerprint="bridge-review-7",
            schema_version=1,
        )

        self.assertTrue(phase_log.signature_valid)
