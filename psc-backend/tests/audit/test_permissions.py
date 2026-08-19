from __future__ import annotations

import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import patch

from apps.inspection.audit.permissions import (
    AUDIT_GATE_IDS,
    AUDIT_P_001,
    AUDIT_P_002,
    AUDIT_P_003,
    AUDIT_P_004,
    AUDIT_P_005,
    AUDIT_P_006,
    AUDIT_P_007,
    AUDIT_P_008,
    AUDIT_P_009,
    AUDIT_P_010,
    AUDIT_P_011,
    AUDIT_P_012,
    AUDIT_P_013,
    AUDIT_P_014,
    AUDIT_P_016,
    AUDIT_P_017,
    AUDIT_P_018,
    AUDIT_P_019,
    AUDIT_P_020,
    CanUseAuditCarWorkflow,
    HasAuditProcessPermission,
    audit_assignment_process_ids_for_user,
    audit_car_workflow_required_gates,
    audit_effective_process_ids_for_user,
    can_authorize_acting_hod,
    default_audit_gates_for_designation,
    has_audit_process_id,
    request_has_audit_detail_process_id,
    user_can_access_audit_detail,
    user_has_vessel_scope,
)


def make_user(**overrides):
    data = {
        "id": "user-1",
        "role": "OFFICE_SSQE",
        "user_type": "OFFICE",
        "process_ids": [],
        "is_authenticated": True,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def make_request(user, *, action="START_PIC_REVIEW", process_ids=None, auth=None):
    if process_ids is not None:
        user.process_ids = process_ids
    return SimpleNamespace(user=user, auth=auth, data={"action": action})


class AuditPermissionTests(unittest.TestCase):
    def test_gate_family_matches_rbac_without_p015(self) -> None:
        self.assertEqual(
            AUDIT_GATE_IDS,
            (
                AUDIT_P_001,
                AUDIT_P_002,
                AUDIT_P_003,
                AUDIT_P_004,
                AUDIT_P_005,
                AUDIT_P_006,
                AUDIT_P_007,
                AUDIT_P_008,
                AUDIT_P_009,
                AUDIT_P_010,
                AUDIT_P_011,
                AUDIT_P_012,
                AUDIT_P_013,
                AUDIT_P_014,
                AUDIT_P_016,
                AUDIT_P_017,
                AUDIT_P_018,
                AUDIT_P_019,
                AUDIT_P_020,
            ),
        )
        self.assertNotIn("AUDIT_P_015", AUDIT_GATE_IDS)

    def test_default_role_designation_mapping_matches_rbac(self) -> None:
        self.assertEqual(
            default_audit_gates_for_designation("OFFICE_SSQE"),
            frozenset(
                {
                    AUDIT_P_001,
                    AUDIT_P_005,
                    AUDIT_P_006,
                    AUDIT_P_009,
                    AUDIT_P_010,
                    AUDIT_P_011,
                    AUDIT_P_012,
                    AUDIT_P_019,
                    AUDIT_P_020,
                }
            ),
        )
        self.assertEqual(
            default_audit_gates_for_designation("DPA"),
            frozenset({AUDIT_P_001, AUDIT_P_005, AUDIT_P_006, AUDIT_P_007, AUDIT_P_013, AUDIT_P_014, AUDIT_P_016, AUDIT_P_018}),
        )
        self.assertEqual(default_audit_gates_for_designation("Lead Auditor"), frozenset())
        self.assertEqual(default_audit_gates_for_designation("Conductor"), frozenset())
        self.assertEqual(default_audit_gates_for_designation("Office Supt"), frozenset({AUDIT_P_004, AUDIT_P_007}))
        self.assertEqual(default_audit_gates_for_designation("Fleet Manager"), frozenset({AUDIT_P_016}))
        self.assertEqual(default_audit_gates_for_designation("Master"), frozenset({AUDIT_P_008, AUDIT_P_017}))
        self.assertEqual(default_audit_gates_for_designation("HoD"), frozenset())

    def test_process_permission_reads_user_auth_and_json_claims(self) -> None:
        permission = HasAuditProcessPermission.requiring(AUDIT_P_004)()

        self.assertTrue(permission.has_permission(make_request(make_user(process_ids=[AUDIT_P_004])), None))
        self.assertTrue(permission.has_permission(make_request(make_user(process_ids='["AUDIT_P_004"]')), None))
        self.assertTrue(
            permission.has_permission(
                make_request(
                    make_user(process_ids=[]),
                    auth={"process_ids": "AUDIT_P_004,PSC_P_004"},
                ),
                None,
            )
        )
        self.assertFalse(permission.has_permission(make_request(make_user(process_ids=[AUDIT_P_003])), None))

    def test_documented_role_defaults_grant_audit_gates_when_profile_seed_missing(self) -> None:
        user = make_user(role="DPA", process_ids=[])

        self.assertTrue(has_audit_process_id(user, AUDIT_P_018))
        self.assertTrue(HasAuditProcessPermission.requiring(AUDIT_P_018)().has_permission(make_request(user), None))
        self.assertTrue(HasAuditProcessPermission.requiring(AUDIT_P_014)().has_permission(make_request(user), None))

        seq_user = make_user(role="OFFICE_SSQE", role_name="SEQ MANAGER", process_ids=[])
        self.assertTrue(HasAuditProcessPermission.requiring(AUDIT_P_009)().has_permission(make_request(seq_user), None))
        self.assertFalse(HasAuditProcessPermission.requiring(AUDIT_P_014)().has_permission(make_request(seq_user), None))

        unmapped_user = make_user(role="PHYSICAL_VERIFIER", role_name="PHYSICAL_VERIFIER", process_ids=[])
        self.assertFalse(has_audit_process_id(unmapped_user, AUDIT_P_018))
        self.assertFalse(HasAuditProcessPermission.requiring(AUDIT_P_018)().has_permission(make_request(unmapped_user), None))

    def test_per_audit_assignments_grant_only_assigned_record_gates(self) -> None:
        assigned_audit = SimpleNamespace(
            auditee_type="VESSEL",
            vessel_id=uuid.uuid4().hex,
            lead_auditor_user_id="lead-1",
            conductor_user_id="cond-1",
        )
        other_audit = SimpleNamespace(
            auditee_type="VESSEL",
            vessel_id=uuid.uuid4().hex,
            lead_auditor_user_id="lead-2",
            conductor_user_id="cond-2",
        )
        lead = make_user(id="lead-1", role="Lead Auditor", process_ids=[])
        conductor = make_user(id="cond-1", role="Conductor", process_ids=[])

        self.assertEqual(audit_assignment_process_ids_for_user(lead, assigned_audit), {AUDIT_P_002, AUDIT_P_003, AUDIT_P_004})
        self.assertEqual(audit_assignment_process_ids_for_user(conductor, assigned_audit), {AUDIT_P_003})
        self.assertEqual(audit_assignment_process_ids_for_user(lead, other_audit), set())
        self.assertEqual(audit_assignment_process_ids_for_user(conductor, other_audit), set())
        self.assertFalse(has_audit_process_id(lead, AUDIT_P_003))
        self.assertFalse(has_audit_process_id(conductor, AUDIT_P_003))
        self.assertTrue(user_can_access_audit_detail(lead, assigned_audit))
        self.assertFalse(user_can_access_audit_detail(lead, other_audit))
        self.assertTrue(request_has_audit_detail_process_id(make_request(conductor), assigned_audit, AUDIT_P_003))

    def test_office_hod_gate_comes_from_active_assignment_not_static_label(self) -> None:
        office_audit = SimpleNamespace(
            auditee_type="OFFICE_DEPT",
            auditee_office_dept="TECH",
            vessel_id=None,
            lead_auditor_user_id="lead-1",
            conductor_user_id="cond-1",
        )
        hod = make_user(id="hod-1", role="HoD", process_ids=[])

        self.assertFalse(has_audit_process_id(hod, AUDIT_P_008))
        with patch("apps.inspection.audit.permissions._active_hod_user_id_for_dept", return_value="hod-1"):
            self.assertEqual(audit_assignment_process_ids_for_user(hod, office_audit), {AUDIT_P_008})
            self.assertIn(AUDIT_P_008, audit_effective_process_ids_for_user(hod, office_audit))
            self.assertTrue(user_can_access_audit_detail(hod, office_audit))

    def test_audit_car_workflow_action_gates(self) -> None:
        self.assertEqual(audit_car_workflow_required_gates("START_PIC_REVIEW"), (AUDIT_P_004,))
        self.assertEqual(audit_car_workflow_required_gates("SUBMIT_TO_LEAD_AUDITOR"), (AUDIT_P_004,))
        self.assertEqual(audit_car_workflow_required_gates("LEAD_AUDITOR_CLOSE"), (AUDIT_P_004,))
        self.assertEqual(audit_car_workflow_required_gates("AWAIT_EXTERNAL_CLOSE_OUT"), (AUDIT_P_004,))
        self.assertEqual(audit_car_workflow_required_gates("CONFIRM_EXTERNAL_CLOSE"), (AUDIT_P_013,))
        self.assertEqual(audit_car_workflow_required_gates("REQUEST_REWORK"), (AUDIT_P_004, AUDIT_P_013))

        permission = CanUseAuditCarWorkflow()
        self.assertTrue(permission.has_permission(make_request(make_user(process_ids=[AUDIT_P_004])), None))
        self.assertFalse(permission.has_permission(make_request(make_user(process_ids=[AUDIT_P_003])), None))
        self.assertTrue(
            permission.has_permission(
                make_request(
                    make_user(role="DPA", process_ids=[AUDIT_P_013]),
                    action="CONFIRM_EXTERNAL_CLOSE",
                ),
                None,
            )
        )
        self.assertFalse(
            permission.has_permission(
                make_request(
                    make_user(role="OFFICE_PIC", process_ids=[AUDIT_P_004]),
                    action="CONFIRM_EXTERNAL_CLOSE",
                ),
                None,
            )
        )

    def test_vessel_scope_and_office_audit_visibility(self) -> None:
        vessel_id = uuid.uuid4()
        other_vessel_id = uuid.uuid4()
        office_user = make_user(process_ids=[AUDIT_P_001], vessel_ids=[str(vessel_id)])
        vessel_user = make_user(
            role="VESSEL_MASTER",
            user_type="VESSEL",
            vessel_id=str(vessel_id),
            process_ids=[AUDIT_P_017],
        )

        vessel_audit = SimpleNamespace(auditee_type="VESSEL", vessel_id=vessel_id.hex)
        other_vessel_audit = SimpleNamespace(auditee_type="VESSEL", vessel_id=other_vessel_id.hex)
        office_audit = SimpleNamespace(auditee_type="OFFICE_DEPT", vessel_id=None)

        self.assertTrue(user_has_vessel_scope(office_user, vessel_id.hex))
        self.assertFalse(user_has_vessel_scope(office_user, other_vessel_id.hex))
        self.assertTrue(user_has_vessel_scope(vessel_user, vessel_id.hex))
        self.assertFalse(user_has_vessel_scope(vessel_user, other_vessel_id.hex))
        self.assertTrue(user_can_access_audit_detail(office_user, vessel_audit))
        self.assertFalse(user_can_access_audit_detail(office_user, other_vessel_audit))
        self.assertTrue(user_can_access_audit_detail(office_user, office_audit))
        self.assertFalse(user_can_access_audit_detail(vessel_user, office_audit))

    def test_acting_hod_authorisation_requires_dpa_or_fm_and_blocks_self_acting(self) -> None:
        dpa = make_user(id="dpa-1", role="DPA", process_ids=[AUDIT_P_016])
        fm = make_user(id="fm-1", role="FM", process_ids=[AUDIT_P_016])
        seq = make_user(id="seq-1", role="OFFICE_SSQE", process_ids=[AUDIT_P_016])

        self.assertTrue(can_authorize_acting_hod(dpa, "hod-1"))
        self.assertTrue(can_authorize_acting_hod(fm, "hod-1"))
        self.assertFalse(can_authorize_acting_hod(seq, "hod-1"))
        self.assertFalse(can_authorize_acting_hod(dpa, "dpa-1"))
        self.assertTrue(can_authorize_acting_hod(make_user(role="DPA", process_ids=[]), "hod-1"))
        self.assertFalse(can_authorize_acting_hod(make_user(role="PHYSICAL_VERIFIER", process_ids=[]), "hod-1"))


if __name__ == "__main__":
    unittest.main()
