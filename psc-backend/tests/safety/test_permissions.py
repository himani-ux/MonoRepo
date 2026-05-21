from __future__ import annotations

import unittest
from types import SimpleNamespace

from apps.safety.authentication.permissions import HasFormPermission, HasProcessPermission


class SafetyPermissionTests(unittest.TestCase):
    def test_form_permission_passes_with_matching_form_id(self) -> None:
        request = SimpleNamespace(
            user=SimpleNamespace(form_ids=["SAF_F_001", "SAF_F_004"]),
            auth=None,
        )

        self.assertTrue(HasFormPermission("SAF_F_001").has_permission(request, None))

    def test_form_permission_rejects_without_matching_form_id(self) -> None:
        request = SimpleNamespace(
            user=SimpleNamespace(form_ids="SAF_F_002, SAF_F_004"),
            auth=None,
        )

        self.assertFalse(HasFormPermission("SAF_F_001").has_permission(request, None))

    def test_process_permission_reads_ids_from_auth_payload(self) -> None:
        request = SimpleNamespace(
            user=SimpleNamespace(process_ids=None),
            auth={"process_ids": ["SAF_P_003", "SAF_P_004"]},
        )

        self.assertTrue(HasProcessPermission("SAF_P_003").has_permission(request, None))
        self.assertFalse(HasProcessPermission("SAF_P_009").has_permission(request, None))

