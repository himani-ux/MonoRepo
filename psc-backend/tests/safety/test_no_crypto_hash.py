from __future__ import annotations

from pathlib import Path
import unittest


class NoCryptoHashTests(unittest.TestCase):
    def test_field_history_resolution_uses_no_hashlib(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        targets = [
            repo_root / "apps" / "safety" / "models" / "field_history.py",
            repo_root / "apps" / "safety" / "services" / "field_history_recorder.py",
            repo_root / "apps" / "safety" / "migrations" / "0010_field_history_shape.py",
        ]

        for path in targets:
            with self.subTest(path=str(path)):
                self.assertNotIn("hashlib", path.read_text(encoding="utf-8"))
