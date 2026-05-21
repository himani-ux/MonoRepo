from __future__ import annotations

import os
from unittest import TestCase
from unittest.mock import patch

from PIL import Image

from tests.safety.support import bootstrap_django


bootstrap_django()

from apps.safety.services import SOIChecklistGenerator


class SOIUniqueIdFormatFinalTests(TestCase):
    def test_generator_ignores_legacy_code128_override_and_emits_qr_png(self) -> None:
        with patch.dict(os.environ, {"VITE_SAFETY_QR_FORMAT": "code128"}, clear=False):
            generator = SOIChecklistGenerator()

        code_image = generator._build_code_image("SOI-9123456-20260506-0001")

        self.assertIsNotNone(code_image)
        qr_image = Image.open(code_image)
        self.assertEqual(qr_image.format, "PNG")
        self.assertEqual(qr_image.width, qr_image.height)

    def test_generator_ignores_legacy_plain_override_and_still_emits_qr_png(self) -> None:
        with patch.dict(os.environ, {"VITE_SAFETY_QR_FORMAT": "plain"}, clear=False):
            generator = SOIChecklistGenerator()

        code_image = generator._build_code_image("SOI-9123456-20260506-0002")

        self.assertIsNotNone(code_image)
        qr_image = Image.open(code_image)
        self.assertEqual(qr_image.format, "PNG")
        self.assertEqual(qr_image.width, qr_image.height)
