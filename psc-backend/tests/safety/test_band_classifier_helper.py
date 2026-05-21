from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django


bootstrap_django()

from apps.safety.services.band_classifier import AdvisoryBandResult, classify_band


class BandClassifierHelperTests(unittest.TestCase):
    def test_returns_green_when_no_escalation_signals_are_present(self) -> None:
        result = classify_band(
            loss_type="MINOR_PROPERTY",
            injuries="NONE",
            pollution="NONE",
            damage="MINOR",
        )

        self.assertIsInstance(result, AdvisoryBandResult)
        self.assertEqual(result.band, "GREEN")
        self.assertIn("minor", result.rationale.lower())

    def test_returns_yellow_for_serious_but_non_catastrophic_signals(self) -> None:
        result = classify_band(
            loss_type="PERSONNEL_INJURY",
            injuries="MAJOR",
            pollution="NONE",
            damage="MODERATE",
        )

        self.assertEqual(result.band, "YELLOW")
        self.assertIn("major injury", result.rationale.lower())

    def test_returns_red_for_catastrophic_signals(self) -> None:
        result = classify_band(
            loss_type="POLLUTION",
            injuries="FATALITY",
            pollution="MAJOR",
            damage="SEVERE",
        )

        self.assertEqual(result.band, "RED")
        self.assertIn("fatality", result.rationale.lower())
