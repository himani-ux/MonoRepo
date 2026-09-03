from pathlib import Path
import unittest


class AuditDemoSeedContractTests(unittest.TestCase):
    def test_demo_seed_uses_ssot_finding_type_enums(self):
        repo_root = Path(__file__).resolve().parents[3]
        seed_path = repo_root / "outputs" / "seed_audit_demo_data_20260817.py"
        source = seed_path.read_text(encoding="utf-8")

        self.assertIn(
            '(IDS["finding_nc"], IDS["def_nc"], "NC", "MAJOR_NC"',
            source,
        )
        self.assertIn(
            '(IDS["finding_obs"], IDS["def_obs"], "OBSERVATION", None, "IMPROVEMENT_SUGGESTION"',
            source,
        )
        self.assertNotIn('"OBS", None, "IMPROVEMENT"', source)


if __name__ == "__main__":
    unittest.main()
