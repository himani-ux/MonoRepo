from __future__ import annotations

import unittest
from unittest.mock import patch

from apps.help_assistant.services import HelpChunk, fallback_answer, lexical_search


class HelpAssistantLocalRetrievalTests(unittest.TestCase):
    def test_lexical_search_prefers_module_context_and_related_terms(self) -> None:
        inspection_chunk = HelpChunk(
            id="inspection-1",
            title="Create Inspection",
            module="inspection",
            source_path="Docs/modules/frontend/inspection-workflow.md",
            text=(
                "Open the inspections screen and create a new inspection. "
                "Submit the inspection report after adding deficiencies and required evidence."
            ),
        )
        circular_chunk = HelpChunk(
            id="circular-1",
            title="Circular Publishing",
            module="circular",
            source_path="Docs/modules/frontend/circular-workflow.md",
            text="Create a circular, attach the PDF, and publish it to selected vessels.",
        )

        with patch(
            "apps.help_assistant.services.load_help_chunks",
            return_value=[circular_chunk, inspection_chunk],
        ):
            results = lexical_search(
                "How do I submit an inspection defect report?",
                {"module": "inspection", "route": "/inspections/new"},
            )

        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].chunk.id, "inspection-1")

    def test_fallback_answer_builds_multi_line_answer_with_sources(self) -> None:
        chunk = HelpChunk(
            id="car-1",
            title="CAR Workflow",
            module="car",
            source_path="Docs/modules/backend/car.md",
            text=(
                "The PIC reviews the corrective action evidence before submitting the CAR. "
                "The DPA can return the CAR for rework when evidence is missing or incomplete. "
                "After approval, the CAR is closed and the audit trail is retained."
            ),
        )

        answer = fallback_answer(
            "Why can a CAR be returned for rework?",
            chunks=[type("Retrieved", (), {"chunk": chunk, "score": 1.0})()],
        )

        self.assertIn("Based on the current VIMS Help documents", answer)
        self.assertIn("rework", answer.lower())
        self.assertIn("Sources:", answer)
        self.assertIn("CAR Workflow", answer)


if __name__ == "__main__":
    unittest.main()
