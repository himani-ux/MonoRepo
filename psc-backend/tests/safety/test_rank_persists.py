from __future__ import annotations

from pathlib import Path
import re
import unittest


FORBIDDEN_PATTERNS = (
    re.compile(r"Acting-(DPA|CO|CE|FM|Master|SO|HOD)\b"),
    re.compile(r"\bacting_(master|dpa|co|ce|so|hod|fm)\b", re.IGNORECASE),
)

CODE_SUFFIXES = {".py", ".ts", ".tsx"}
CODE_ROOTS = ("apps/safety", "src")


class RankPersistsTests(unittest.TestCase):
    def test_no_acting_role_constants_exist_in_workspace_code(self) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        matches: list[str] = []

        for relative_root in CODE_ROOTS:
            root = repo_root / relative_root
            for path in root.rglob("*"):
                if path.suffix not in CODE_SUFFIXES or not path.is_file():
                    continue
                content = path.read_text(encoding="utf-8", errors="ignore")
                for pattern in FORBIDDEN_PATTERNS:
                    if pattern.search(content):
                        matches.append(str(path.relative_to(repo_root)))
                        break

        self.assertEqual(matches, [])
