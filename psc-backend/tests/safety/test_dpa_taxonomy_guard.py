from __future__ import annotations

from types import SimpleNamespace
import unittest

from rest_framework.test import APIRequestFactory

from apps.safety.authentication.permissions import HasDpaTaxonomyWritePermission


class DpaTaxonomyGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.permission = HasDpaTaxonomyWritePermission()

    def test_safe_methods_are_allowed_for_non_dpa_user(self) -> None:
        request = self.factory.get("/api/safety/admin/taxonomy/")
        request.user = SimpleNamespace(role_name="MASTER")

        self.assertTrue(self.permission.has_permission(request, view=None))

    def test_dpa_can_write_taxonomy(self) -> None:
        request = self.factory.patch("/api/safety/admin/taxonomy/1/", {"active": False}, format="json")
        request.user = SimpleNamespace(role_name="DPA")

        self.assertTrue(self.permission.has_permission(request, view=None))

    def test_non_dpa_cannot_write_taxonomy(self) -> None:
        request = self.factory.patch("/api/safety/admin/taxonomy/1/", {"active": False}, format="json")
        request.user = SimpleNamespace(role_name="FM")

        self.assertFalse(self.permission.has_permission(request, view=None))
