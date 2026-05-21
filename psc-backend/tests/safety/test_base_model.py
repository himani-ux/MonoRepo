from __future__ import annotations

import unittest

import django
from django.apps import apps
from django.db import models


def bootstrap_django() -> None:
    from django.conf import settings

    if not settings.configured:
        settings.configure(
            SECRET_KEY="safety-phase-0-2-model-test-secret-key-1234567890",
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "apps.safety",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=True,
        )

    if not apps.ready:
        django.setup()


bootstrap_django()

from apps.safety.models import BaseSafetyRecord


class ConcreteSafetyRecord(BaseSafetyRecord):
    title = models.CharField(max_length=64)

    class Meta:
        app_label = "safety"


class BaseSafetyRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def test_base_model_is_abstract(self) -> None:
        self.assertTrue(BaseSafetyRecord._meta.abstract)
        self.assertFalse(ConcreteSafetyRecord._meta.abstract)

    def test_is_deleted_defaults_to_false(self) -> None:
        record = ConcreteSafetyRecord(
            title="Near miss",
            vessel_id="7",
            state="DRAFT",
            created_by="crew-7",
            schema_version=1,
        )

        self.assertFalse(record.is_deleted)
        self.assertFalse(record.is_archived)
        self.assertIsNone(record.archived_at)

    def test_schema_version_is_required(self) -> None:
        field = ConcreteSafetyRecord._meta.get_field("schema_version")

        self.assertFalse(field.blank)
        self.assertFalse(field.null)

    def test_created_by_is_required_text_field(self) -> None:
        field = ConcreteSafetyRecord._meta.get_field("created_by")

        self.assertIsInstance(field, models.CharField)
        self.assertFalse(field.blank)
        self.assertFalse(field.null)
