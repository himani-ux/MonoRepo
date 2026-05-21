from __future__ import annotations

import unittest

from apps.safety.profile_permission_seed import (
    FORM,
    PROCESS,
    merge_permission_lists,
    target_permissions_for_profile,
)


class SafetyProfilePermissionSeedTests(unittest.TestCase):
    def test_merge_permission_lists_preserves_existing_order_and_appends_new_ids_once(self) -> None:
        merged = merge_permission_lists(
            '["PSC_F_001", "SAF_F_001"]',
            (FORM["INCIDENTS"], FORM["DASHBOARD"], FORM["INCIDENTS"]),
        )

        self.assertEqual(merged, ["PSC_F_001", "SAF_F_001", "SAF_F_015"])

    def test_master_profile_receives_safety_master_bundle(self) -> None:
        bundle = target_permissions_for_profile(work_side=True, profile_name="MASTER")

        self.assertIn(FORM["INCIDENTS"], bundle.form_ids)
        self.assertIn(FORM["SOI"], bundle.form_ids)
        self.assertIn(FORM["SOI_APPLICABILITY"], bundle.form_ids)
        self.assertIn(PROCESS["APPROVE_CLOSE"], bundle.process_ids)
        self.assertIn(PROCESS["SOI_APPROVE_CLOSURE"], bundle.process_ids)
        self.assertIn(PROCESS["SOI_APPLICABILITY_REQUEST"], bundle.process_ids)

    def test_acting_master_profile_is_not_mapped_to_master_authority(self) -> None:
        bundle = target_permissions_for_profile(work_side=True, profile_name="ACTING MASTER")

        self.assertEqual(bundle.form_ids, (FORM["NEAR_MISS"],))
        self.assertEqual(bundle.process_ids, (PROCESS["CREATE"],))

    def test_general_ship_crew_only_receives_near_miss_create_bundle(self) -> None:
        bundle = target_permissions_for_profile(work_side=True, profile_name="OILER")

        self.assertEqual(bundle.form_ids, (FORM["NEAR_MISS"],))
        self.assertEqual(bundle.process_ids, (PROCESS["CREATE"],))

    def test_seq_manager_receives_dpa_bundle(self) -> None:
        bundle = target_permissions_for_profile(work_side=False, profile_name="SEQ Manager")

        self.assertIn(FORM["ADMIN"], bundle.form_ids)
        self.assertIn(FORM["AUDITOR_EXPORT"], bundle.form_ids)
        self.assertIn(PROCESS["MSCAT_UPDATE"], bundle.process_ids)
        self.assertIn(PROCESS["SOI_TEMPLATE_UPDATE"], bundle.process_ids)
        self.assertIn(PROCESS["FLEET_CIRCULAR"], bundle.process_ids)

    def test_unmapped_office_profile_is_left_unchanged(self) -> None:
        bundle = target_permissions_for_profile(work_side=False, profile_name="Accounts")

        self.assertEqual(bundle.form_ids, ())
        self.assertEqual(bundle.process_ids, ())
