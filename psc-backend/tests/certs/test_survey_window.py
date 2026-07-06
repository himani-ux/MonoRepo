from __future__ import annotations

import os
import unittest
from datetime import date

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings_test")
django.setup()

from apps.certs.services.survey_window import compute_window


class CertSurveyWindowTests(unittest.TestCase):
    def test_renewal_window_uses_anniversary_plus_cadence_and_closes_on_due_date(self) -> None:
        window_open, window_close, next_due_date = compute_window(
            {
                "anniversary_date": date(2026, 1, 1),
                "cadence_months": 60,
                "validity_type": "full",
                "type": "certificate",
            }
        )

        self.assertEqual(window_open, date(2030, 10, 1))
        self.assertEqual(window_close, date(2031, 1, 1))
        self.assertEqual(next_due_date, date(2031, 1, 1))

    def test_annual_survey_window_uses_two_month_range_around_due_date(self) -> None:
        window_open, window_close, next_due_date = compute_window(
            {
                "anniversary_date": "2026-05-31",
                "cadence_months": 12,
                "relationship_type": "survey_of",
                "catalog_display_name": "Class Annual Survey",
            }
        )

        self.assertEqual(window_open, date(2027, 3, 31))
        self.assertEqual(window_close, date(2027, 7, 31))
        self.assertEqual(next_due_date, date(2027, 5, 31))

    def test_custom_day_cadence_has_due_day_only_window(self) -> None:
        window_open, window_close, next_due_date = compute_window(
            {
                "anniversary_date": "2026-01-01",
                "cadence_months": None,
                "cadence_custom_days": 45,
            }
        )

        self.assertEqual(window_open, date(2026, 2, 15))
        self.assertEqual(window_close, date(2026, 2, 15))
        self.assertEqual(next_due_date, date(2026, 2, 15))

    def test_permanent_or_unanchored_rows_have_no_computed_window(self) -> None:
        self.assertEqual(
            compute_window({"anniversary_date": "2026-01-01", "validity_type": "permanent"}),
            (None, None, None),
        )
        self.assertEqual(
            compute_window({"cadence_months": 12, "validity_type": "full"}),
            (None, None, None),
        )


if __name__ == "__main__":
    unittest.main()
