from __future__ import annotations

import unittest
from datetime import timedelta

import django
from django.apps import apps
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import connection


def bootstrap_django() -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="safety-phase-0-2-auth-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "rest_framework",
                "apps.safety",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
        )

    if not apps.ready:
        django.setup()

    existing_tables = set(connection.introspection.table_names())
    if "auth_user" not in existing_tables:
        call_command("migrate", run_syncdb=True, verbosity=0)


bootstrap_django()

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import AccessToken

from apps.safety.authentication.backends import SafetyJWTAuthentication
from apps.safety.authentication.permissions import HasFormPermission, HasProcessPermission


class SafetyJwtAuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(
            username="safety.auth",
            password="not-used-in-token-test",
        )
        cls.factory = APIRequestFactory()

    def test_valid_jwt_carries_safety_permission_claims(self) -> None:
        token = AccessToken.for_user(self.user)
        token["form_ids"] = ["SAF_F_001", "SAF_F_004"]
        token["process_ids"] = ["SAF_P_003", "SAF_P_004"]

        request = self.factory.get("/api/safety/incidents/")
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {str(token)}"

        authenticated_user, validated_token = SafetyJWTAuthentication().authenticate(request)
        request.user = authenticated_user
        request.auth = validated_token

        self.assertEqual(validated_token["form_ids"], ["SAF_F_001", "SAF_F_004"])
        self.assertEqual(validated_token["process_ids"], ["SAF_P_003", "SAF_P_004"])
        self.assertTrue(HasFormPermission("SAF_F_001").has_permission(request, None))
        self.assertTrue(HasProcessPermission("SAF_P_003").has_permission(request, None))

    def test_expired_jwt_is_rejected(self) -> None:
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=timedelta(seconds=-1))

        request = self.factory.get("/api/safety/incidents/")
        request.META["HTTP_AUTHORIZATION"] = f"Bearer {str(token)}"

        with self.assertRaises(AuthenticationFailed):
            SafetyJWTAuthentication().authenticate(request)
