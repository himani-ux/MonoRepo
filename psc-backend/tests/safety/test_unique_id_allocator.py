from __future__ import annotations

from datetime import date
import unittest

from tests.safety.support import bootstrap_django, recreate_soi_tables


bootstrap_django()

from apps.safety.models import SOIInspection
from apps.safety.services.unique_id_allocator import UniqueIdAllocator


class UniqueIdAllocatorTests(unittest.TestCase):
    def setUp(self) -> None:
        recreate_soi_tables()

    def test_allocator_formats_unique_id_and_reuses_existing_value(self) -> None:
        tokens = iter(["AB12", "CD34"])
        allocator = UniqueIdAllocator(token_factory=lambda: next(tokens))
        first = self._create_inspection(reference="SOI/ABC/26/01")
        second = self._create_inspection(reference="SOI/ABC/26/02")

        first_unique_id = allocator.allocate(first.id)
        repeated_unique_id = allocator.allocate(first.id)
        second_unique_id = allocator.allocate(second.id)

        self.assertEqual(first_unique_id, "SOI-0000007-20260501-0001")
        self.assertEqual(repeated_unique_id, first_unique_id)
        self.assertEqual(second_unique_id, "SOI-0000007-20260501-0002")

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.checklist_unique_id, first_unique_id)
        self.assertEqual(second.checklist_unique_id, second_unique_id)

    def _create_inspection(self, *, reference: str) -> SOIInspection:
        return SOIInspection.objects.create(
            vessel_id="7",
            inspection_reference=reference,
            cycle_label="Q2/2026",
            planned_date=date(2026, 5, 1),
            safety_officer_crew_id="co-7",
            safety_officer_department="DECK",
            assistant_crew_id="2e-7",
            assistant_department="ENGINE",
            created_by="co-7",
        )
