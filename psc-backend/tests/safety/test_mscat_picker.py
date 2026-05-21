from __future__ import annotations

import unittest

from tests.safety.support import (
    bootstrap_django,
    recreate_phase5_reference_tables,
    seed_phase5_reference_tables,
)


bootstrap_django()

from apps.safety.models import MasterMscatTaxonomy
from apps.safety.services.mscat_search import MscatSearchService


class MscatPickerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        bootstrap_django()

    def setUp(self) -> None:
        recreate_phase5_reference_tables()
        seed_phase5_reference_tables()
        self.service = MscatSearchService()

    def test_search_returns_orientation_hits_and_round_21_design_moc_entry(self) -> None:
        self.assertEqual(MasterMscatTaxonomy.objects.count(), 174)

        orientation_results = self.service.search("orientation")
        self.assertGreater(len(orientation_results), 0)
        self.assertTrue(
            any("orientation" in row.subcode_description.lower() for row in orientation_results),
        )

        design_results = self.service.search("10.15")
        self.assertTrue(any(row.subcode_id.startswith("10.15") for row in design_results))
