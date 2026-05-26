from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django


bootstrap_django()

from apps.safety.serializers.scm import SCM_SECTION_TEMPLATE


class SCMSectionTemplateTests(unittest.TestCase):
    def test_legacy_template_keeps_expected_section_order(self) -> None:
        labels = [section["section_label"] for section in SCM_SECTION_TEMPLATE]

        self.assertEqual(
            labels,
            [
                "Structured Review",
                "Quality and Safety Practice",
                "Security",
                "Environment",
                "Health",
                "Crew Welfare",
                "PSC Findings & Corrective Measures",
                "Minutes of Meeting",
                "Office Review",
            ],
        )

    def test_legacy_template_contains_expected_sections(self) -> None:
        self.assertEqual(len(SCM_SECTION_TEMPLATE), 9)
        self.assertEqual(
            [section["agenda_item_number"] for section in SCM_SECTION_TEMPLATE],
            list(range(1, 10)),
        )
