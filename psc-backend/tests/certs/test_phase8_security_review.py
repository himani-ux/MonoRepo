from __future__ import annotations

import re
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[3]


class Phase8SecurityReviewGateTests(unittest.TestCase):
    def test_audit_grant_regime_keeps_app_role_append_only_and_jobs_role_scoped(self) -> None:
        migration_source = (
            REPO_ROOT
            / "psc-backend"
            / "apps"
            / "certs"
            / "migrations"
            / "0001_initial.py"
        ).read_text(encoding="utf-8")
        bootstrap_sql = (
            REPO_ROOT
            / "psc-backend"
            / "apps"
            / "certs"
            / "sql"
            / "phase0_03_role_separation.sql"
        ).read_text(encoding="utf-8")

        append_only_block = re.search(
            r"append_only_tables\s*=\s*\{(?P<body>.*?)\}",
            migration_source,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(append_only_block)
        append_only_body = append_only_block.group("body")
        self.assertIn('"vims_certs_audit_log"', append_only_body)
        self.assertIn('"vims_certs_approval_event"', append_only_body)
        self.assertIn('"vims_certs_cert_change_log"', append_only_body)
        self.assertIn('_grant(cursor, "GRANT SELECT, INSERT", table_name, "vims_app")', migration_source)
        self.assertIn(
            '_grant(cursor, "GRANT UPDATE (retention_tier, archived_at)", "vims_certs_audit_log", "vims_jobs")',
            migration_source,
        )
        self.assertIn('_grant(cursor, "GRANT DELETE", "vims_certs_audit_log", "vims_jobs")', migration_source)
        self.assertNotRegex(bootstrap_sql, r"(?im)^\s*GRANT\s+")

    def test_static_platform_maintenance_page_exists_for_phase9_cutover(self) -> None:
        maintenance_page = REPO_ROOT / "psc-frontend" / "public" / "maintenance.html"
        nginx_conf = REPO_ROOT / "psc-frontend" / "nginx.conf"

        self.assertTrue(maintenance_page.exists(), "Static maintenance page is missing.")
        page_text = maintenance_page.read_text(encoding="utf-8")
        self.assertIn("VIMS is under scheduled maintenance.", page_text)
        self.assertIn("Estimated return:", page_text)

        nginx_text = nginx_conf.read_text(encoding="utf-8")
        self.assertIn("location = /maintenance.html", nginx_text)
        self.assertIn("try_files /maintenance.html =503", nginx_text)


if __name__ == "__main__":
    unittest.main()
