from __future__ import annotations

import importlib
import unittest

from django.apps import apps as django_apps

from tests.safety.support import bootstrap_django, recreate_taxonomy_reference_tables


bootstrap_django()

from apps.safety.models import SafetyCaseStudy


case_study_migration = importlib.import_module("apps.safety.migrations.0008_case_study_library")


class CaseStudySeedTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_taxonomy_reference_tables()

    def test_seed_case_studies_loads_two_expected_rows_idempotently(self) -> None:
        case_study_migration.seed_case_studies(django_apps, schema_editor=None)
        case_study_migration.seed_case_studies(django_apps, schema_editor=None)

        self.assertEqual(SafetyCaseStudy.objects.count(), 2)
        self.assertEqual(
            list(
                SafetyCaseStudy.objects.order_by("display_order").values_list(
                    "slug",
                    flat=True,
                )
            ),
            ["navigator", "sinkfast"],
        )
