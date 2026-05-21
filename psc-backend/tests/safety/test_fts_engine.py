from __future__ import annotations

import unittest

from tests.safety.support import bootstrap_django


bootstrap_django()

from apps.safety.services.fts_engine import SafetyFtsEngine


class SafetyFtsEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = SafetyFtsEngine()

    def test_build_sql_server_contains_query_uses_prefix_terms(self) -> None:
        self.assertEqual(
            self.engine.build_sql_server_contains_query("hydraulic manifold"),
            '"hydraulic*" AND "manifold*"',
        )

    def test_build_sql_server_contains_query_preserves_code_like_tokens(self) -> None:
        self.assertEqual(
            self.engine.build_sql_server_contains_query("M-220 5.2"),
            '"M-220*" AND "5.2*"',
        )

    def test_description_similarity_flags_same_issue_despite_reordered_words(self) -> None:
        first = "Hydraulic manifold guard left open after maintenance."
        second = "After maintenance, the hydraulic manifold guard was left open."

        self.assertTrue(self.engine.descriptions_are_similar(first, second))
        self.assertGreaterEqual(self.engine.description_similarity(first, second), 0.45)

    def test_description_similarity_rejects_unrelated_findings(self) -> None:
        first = "Hydraulic manifold guard left open after maintenance."
        second = "Galley refrigerator temperature log missing for the weekly review."

        self.assertFalse(self.engine.descriptions_are_similar(first, second))
        self.assertLess(self.engine.description_similarity(first, second), 0.45)
