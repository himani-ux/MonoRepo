from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import django
from django.apps import apps


def bootstrap_django() -> None:
    from django.conf import settings

    os.environ.pop("DJANGO_SETTINGS_MODULE", None)
    if not settings.configured:
        settings.configure(
            SECRET_KEY="audit-auth-permission-test-secret-key",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "apps.accounts",
                "apps.masters",
                "apps.inspection",
                "apps.car",
                "apps.notifications",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
            DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        )

    if not apps.ready:
        django.setup()


bootstrap_django()

from apps.accounts.backends import PSCAuthenticationBackend  # noqa: E402
from apps.accounts.models import RoleCodes  # noqa: E402
from apps.accounts.utils import resolve_current_vessel_permission_snapshot  # noqa: E402
from apps.inspection.audit.permissions import AUDIT_P_008, AUDIT_P_013, AUDIT_P_017  # noqa: E402


class AuditAuthPermissionDefaultTests(unittest.TestCase):
    @patch("apps.accounts.utils.get_profile_permissions")
    def test_master_snapshot_merges_audit_defaults_when_profile_lacks_them(self, profile_permissions):
        profile_permissions.return_value = (["SAF_F_003"], ["SAF_P_004"])

        snapshot = resolve_current_vessel_permission_snapshot(
            user_type="VESSEL",
            role=RoleCodes.VESSEL_MASTER,
            rank="MASTER",
            full_name="Vessel Master",
        )

        self.assertEqual(snapshot["role_name"], "MASTER")
        self.assertEqual(snapshot["safety_role_name"], "MASTER")
        self.assertIn("SAF_P_004", snapshot["process_ids"])
        self.assertIn(AUDIT_P_008, snapshot["process_ids"])
        self.assertIn(AUDIT_P_013, snapshot["process_ids"])
        self.assertIn(AUDIT_P_017, snapshot["process_ids"])

    def test_acting_master_resolves_to_vessel_master_role(self):
        backend = PSCAuthenticationBackend()

        self.assertEqual(backend._determine_vessel_role("ACTING MASTER"), RoleCodes.VESSEL_MASTER)
