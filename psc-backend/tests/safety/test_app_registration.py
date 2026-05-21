from __future__ import annotations

import unittest

import django
from django.apps import apps

from apps.safety.routing import SafetyRouter


def bootstrap_django() -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="safety-phase-0-1-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "rest_framework",
                "apps.safety",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            DATABASE_ROUTERS=["apps.safety.routing.SafetyRouter"],
            USE_TZ=True,
        )

    if not apps.ready:
        django.setup()


class _SafetyModelMeta:
    app_label = "safety"


class _OtherModelMeta:
    app_label = "reporting"


class DummySafetyModel:
    _meta = _SafetyModelMeta()


class DummyOtherModel:
    _meta = _OtherModelMeta()


class SafetyAppRegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def test_apps_safety_resolves_via_django_app_registry(self) -> None:
        app_config = apps.get_app_config("safety")

        self.assertEqual(app_config.name, "apps.safety")
        self.assertEqual(app_config.label, "safety")

    def test_safety_router_uses_only_default_alias(self) -> None:
        router = SafetyRouter()

        self.assertEqual(router.db_for_read(DummySafetyModel), "default")
        self.assertEqual(router.db_for_write(DummySafetyModel), "default")
        self.assertTrue(router.allow_migrate("default", "safety"))
        self.assertFalse(router.allow_migrate("analytics", "safety"))
        self.assertIsNone(router.db_for_read(DummyOtherModel))
        self.assertIsNone(router.db_for_write(DummyOtherModel))
        self.assertIsNone(router.allow_migrate("default", "reporting"))
