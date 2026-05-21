from __future__ import annotations
from types import SimpleNamespace
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from apps.safety.models import SOIFinding, SafetyFieldHistory
from apps.safety.services.finding_closure import FindingClosureService
from apps.safety.services.field_history_recorder import parse_history_value


def build_user(role_name: str, user_id: str):
    return SimpleNamespace(id=user_id, username=user_id, role_name=role_name)


class SOIFindingSignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_soi_tables()
        self.service = FindingClosureService()
        self._seed_inspection()

    def test_pending_and_master_signature_payloads_are_recorded_append_only(self) -> None:
        finding = SOIFinding.objects.create(
            inspection_id=1,
            area_id=5,
            item_id=3001,
            title="Ventilation guard replaced",
            description="Guard was replaced and is ready for closure.",
            severity="LOW",
            priority="LOW",
            status=SOIFinding.Status.OPEN,
            created_by="co-7",
        )

        self.service.mark_pending_closure(
            finding=finding,
            user=build_user("CO", "co-7"),
            typed_name="Chief Officer Seven",
            device_fingerprint="tablet-co-7",
            closure_note="Rectified onboard.",
        )
        self.service.approve_closure(
            finding=finding,
            user=build_user("MASTER", "master-7"),
            typed_name="Master Seven",
            device_fingerprint="bridge-console-7",
            closure_note="Confirmed during inspection round.",
        )

        pending_row = SafetyFieldHistory.objects.get(field_name="soi_pending_closure_signature")
        pending_payload = parse_history_value(pending_row.new_value)
        self.assertEqual(pending_payload["typed_name"], "Chief Officer Seven")
        self.assertEqual(pending_payload["device_fingerprint"], "tablet-co-7")
        self.assertTrue(pending_payload["signed_at"])

        master_row = SafetyFieldHistory.objects.get(field_name="soi_master_counter_signature")
        master_payload = parse_history_value(master_row.new_value)
        self.assertEqual(master_payload["typed_name"], "Master Seven")
        self.assertEqual(master_payload["device_fingerprint"], "bridge-console-7")
        self.assertTrue(master_payload["signed_at"])

        approval_state_row = SafetyFieldHistory.objects.get(field_name="master_approval_state")
        self.assertEqual(approval_state_row.new_value, "MASTER_APPROVED")

    def _seed_inspection(self) -> None:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO vims_safety_soi_inspection (
                    id,
                    vessel_id,
                    inspection_reference,
                    cycle_label,
                    state,
                    planned_date,
                    safety_officer_crew_id,
                    safety_officer_department,
                    assistant_crew_id,
                    assistant_department,
                    master_crew_id,
                    checklist_unique_id,
                    checklist_generated_at,
                    checklist_format,
                    section_12_included,
                    schema_version,
                    is_deleted,
                    created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    1,
                    "7",
                    "SOI/ABC/26/10",
                    "Q2/2026",
                    "DOWNLOADED",
                    "2026-05-01",
                    "co-7",
                    "DECK",
                    "2e-7",
                    "ENGINE",
                    "master-7",
                    "SOI-UID-010",
                    "2026-05-01 08:00:00",
                    "PDF",
                    False,
                    1,
                    False,
                    "co-7",
                ],
            )
