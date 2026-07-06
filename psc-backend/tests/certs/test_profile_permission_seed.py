from __future__ import annotations

import unittest

from apps.certs.profile_permission_seed import (
    FORM,
    PROCESS,
    merge_permission_lists,
    target_permissions_for_profile,
)


class CertProfilePermissionSeedTests(unittest.TestCase):
    def test_merge_permission_lists_preserves_existing_order_and_appends_new_ids_once(self) -> None:
        merged = merge_permission_lists(
            '["PSC_F_001", "CERT_F_001"]',
            (FORM["CATALOG"], FORM["TRACKED_ITEMS"], FORM["CATALOG"]),
        )

        self.assertEqual(merged, ["PSC_F_001", "CERT_F_001", "CERT_F_002"])

    def test_dpa_profile_receives_full_certs_bundle(self) -> None:
        bundle = target_permissions_for_profile(work_side=False, profile_name="SEQ Manager")

        self.assertEqual(bundle.form_ids, tuple(FORM.values()))
        self.assertEqual(bundle.process_ids, tuple(PROCESS.values()))

    def test_system_admin_profiles_receive_full_certs_bundle(self) -> None:
        for profile_name in ("admin", "Super Admin"):
            with self.subTest(profile_name=profile_name):
                bundle = target_permissions_for_profile(work_side=False, profile_name=profile_name)

                self.assertEqual(bundle.form_ids, tuple(FORM.values()))
                self.assertEqual(bundle.process_ids, tuple(PROCESS.values()))

    def test_fleet_manager_receives_read_plus_fm_action_bundle(self) -> None:
        bundle = target_permissions_for_profile(work_side=False, profile_name="Fleet Manager")

        self.assertIn(FORM["ONBOARDING"], bundle.form_ids)
        self.assertIn(FORM["AUDIT_LOG"], bundle.form_ids)
        self.assertNotIn(FORM["NOTIFICATION_CONFIG"], bundle.form_ids)
        self.assertIn(PROCESS["SUBMIT"], bundle.process_ids)
        self.assertIn(PROCESS["EXPORT_BUNDLE"], bundle.process_ids)
        self.assertNotIn(PROCESS["PROVISION_AUDITOR"], bundle.process_ids)

    def test_marine_superintendent_receives_reconciliation_and_auditor_provisioning(self) -> None:
        bundle = target_permissions_for_profile(work_side=False, profile_name="Marine Superintendent")

        self.assertIn(FORM["RECONCILIATION"], bundle.form_ids)
        self.assertIn(FORM["AUDITOR_ACCESS"], bundle.form_ids)
        self.assertIn(PROCESS["PROVISION_AUDITOR"], bundle.process_ids)
        self.assertIn(PROCESS["ROLLBACK"], bundle.process_ids)

    def test_technical_manager_is_read_mostly_with_print_action_only(self) -> None:
        bundle = target_permissions_for_profile(work_side=False, profile_name="Technical Manager")

        self.assertIn(FORM["TRACKED_ITEMS"], bundle.form_ids)
        self.assertIn(FORM["PRINT_EXPORT"], bundle.form_ids)
        self.assertEqual(bundle.process_ids, (PROCESS["PRINT"],))

    def test_master_receives_own_vessel_write_approval_print_and_bundle(self) -> None:
        bundle = target_permissions_for_profile(work_side=True, profile_name="MASTER")

        self.assertIn(FORM["TRACKED_ITEMS"], bundle.form_ids)
        self.assertIn(FORM["PRINT_EXPORT"], bundle.form_ids)
        self.assertIn(PROCESS["CREATE"], bundle.process_ids)
        self.assertIn(PROCESS["APPROVE"], bundle.process_ids)
        self.assertIn(PROCESS["REJECT"], bundle.process_ids)
        self.assertIn(PROCESS["EXPORT_BUNDLE"], bundle.process_ids)

    def test_acting_master_profile_is_not_mapped_to_master_authority(self) -> None:
        bundle = target_permissions_for_profile(work_side=True, profile_name="ACTING MASTER")

        self.assertEqual(bundle.form_ids, (FORM["TRACKED_ITEMS"],))
        self.assertEqual(bundle.process_ids, ())

    def test_ship_submitter_profiles_receive_create_and_submit_only(self) -> None:
        for profile_name in ("CHIEF OFFICER", "CHIEF ENGINEER", "SECOND ENGINEER"):
            with self.subTest(profile_name=profile_name):
                bundle = target_permissions_for_profile(work_side=True, profile_name=profile_name)

                self.assertEqual(bundle.form_ids, (FORM["TRACKED_ITEMS"],))
                self.assertEqual(bundle.process_ids, (PROCESS["CREATE"], PROCESS["SUBMIT"]))

    def test_unmapped_office_profile_is_left_unchanged(self) -> None:
        bundle = target_permissions_for_profile(work_side=False, profile_name="Accounts")

        self.assertEqual(bundle.form_ids, ())
        self.assertEqual(bundle.process_ids, ())
