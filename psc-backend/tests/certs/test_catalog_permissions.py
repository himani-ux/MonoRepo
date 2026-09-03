from __future__ import annotations

import unittest
from types import SimpleNamespace

from apps.certs.permissions.certs_perms import IsCatalogWriter
from apps.certs.profile_permission_seed import FORM, PROCESS, target_permissions_for_profile


class CertsCatalogPermissionTests(unittest.TestCase):
    def test_marine_superintendent_can_write_catalog_with_catalog_edit_permission(self) -> None:
        request = SimpleNamespace(
            user=SimpleNamespace(
                role_name="Marine Superintendent",
                form_ids=["CERT_F_001"],
                process_ids=["CERT_P_008"],
            )
        )

        self.assertTrue(IsCatalogWriter().has_permission(request, view=None))

    def test_marine_superintendent_seed_includes_catalog_edit_without_bulk_action(self) -> None:
        bundle = target_permissions_for_profile(work_side=False, profile_name="Marine Superintendent")

        self.assertIn(FORM["CATALOG"], bundle.form_ids)
        self.assertIn(PROCESS["CATALOG_EDIT"], bundle.process_ids)
        self.assertNotIn(PROCESS["BULK_ACTION"], bundle.process_ids)

    def test_technical_superintendent_can_write_catalog_with_catalog_edit_permission(self) -> None:
        request = SimpleNamespace(
            user=SimpleNamespace(
                role_name="Technical Superintendent",
                form_ids=["CERT_F_001"],
                process_ids=["CERT_P_008"],
            )
        )

        self.assertTrue(IsCatalogWriter().has_permission(request, view=None))

    def test_technical_superintendent_with_generic_office_supt_role_can_write_catalog(self) -> None:
        request = SimpleNamespace(
            user=SimpleNamespace(
                role="OFFICE_SUPT",
                role_name="Technical Superintendent",
                form_ids=["CERT_F_001"],
                process_ids=["CERT_P_008"],
            )
        )

        self.assertTrue(IsCatalogWriter().has_permission(request, view=None))

    def test_generic_office_supt_without_writer_profile_cannot_write_catalog(self) -> None:
        request = SimpleNamespace(
            user=SimpleNamespace(
                role="OFFICE_SUPT",
                role_name="Senior Technical Superintendent",
                form_ids=["CERT_F_001"],
                process_ids=["CERT_P_008"],
            )
        )

        self.assertFalse(IsCatalogWriter().has_permission(request, view=None))

    def test_technical_superintendent_seed_includes_catalog_edit_without_bulk_action(self) -> None:
        bundle = target_permissions_for_profile(work_side=False, profile_name="Technical Superintendent")

        self.assertIn(FORM["CATALOG"], bundle.form_ids)
        self.assertIn(PROCESS["CATALOG_EDIT"], bundle.process_ids)
        self.assertNotIn(PROCESS["BULK_ACTION"], bundle.process_ids)

    def test_senior_technical_superintendent_seed_does_not_gain_catalog_edit(self) -> None:
        bundle = target_permissions_for_profile(work_side=False, profile_name="Senior Technical Superintendent")

        self.assertIn(FORM["CATALOG"], bundle.form_ids)
        self.assertNotIn(PROCESS["CATALOG_EDIT"], bundle.process_ids)
