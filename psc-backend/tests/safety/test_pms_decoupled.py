from __future__ import annotations

from pathlib import Path
import re
import unittest

from django.apps import apps
from django.db.models import ForeignKey

from tests.safety.support import bootstrap_django


bootstrap_django()


class PMSDecoupledTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[2]
    source_roots = ("apps", "src", "config", "tests/safety")
    source_suffixes = {".py", ".ts", ".tsx", ".js", ".jsx"}
    forbidden_table_token = "pm" + "s_"
    forbidden_import = "apps" + ".pms"

    def iter_source_files(self):
        for root_name in self.source_roots:
            root = self.repo_root / root_name
            for path in root.rglob("*"):
                if path.is_file() and path.suffix in self.source_suffixes:
                    yield path

    def test_source_tree_contains_no_pms_identifiers(self) -> None:
        identifier_pattern = re.compile(rf"\b{re.escape(self.forbidden_table_token)}[a-z0-9_]*\b")
        offenders: list[str] = []

        for path in self.iter_source_files():
            content = path.read_text(encoding="utf-8")
            if identifier_pattern.search(content):
                offenders.append(str(path.relative_to(self.repo_root)))

        self.assertEqual(
            offenders,
            [],
            msg=f"Safety source tree must not contain PMS-shaped identifiers: {offenders}",
        )

    def test_source_tree_contains_no_apps_pms_imports(self) -> None:
        import_pattern = re.compile(
            rf"^\s*(?:from|import)\s+{re.escape(self.forbidden_import)}(?:\b|[.\s])",
            re.MULTILINE,
        )
        offenders: list[str] = []

        for path in self.iter_source_files():
            content = path.read_text(encoding="utf-8")
            if import_pattern.search(content):
                offenders.append(str(path.relative_to(self.repo_root)))

        self.assertEqual(
            offenders,
            [],
            msg=f"Safety source tree must not import PMS modules: {offenders}",
        )

    def test_safety_models_expose_no_pms_fk_or_columns(self) -> None:
        offenders: list[str] = []

        for model in apps.get_app_config("safety").get_models():
            if self.forbidden_table_token in model._meta.db_table.lower():
                offenders.append(f"{model.__name__}:table:{model._meta.db_table}")

            for field in model._meta.get_fields():
                if getattr(field, "auto_created", False) and not getattr(field, "concrete", False):
                    continue

                column_name = getattr(field, "column", None)
                attname = getattr(field, "attname", None)

                if column_name and self.forbidden_table_token in column_name.lower():
                    offenders.append(f"{model.__name__}:column:{column_name}")
                if attname and self.forbidden_table_token in attname.lower():
                    offenders.append(f"{model.__name__}:attname:{attname}")

                if isinstance(field, ForeignKey):
                    related_model = getattr(field, "related_model", None)
                    related_module = getattr(related_model, "__module__", "")
                    if related_module.startswith(self.forbidden_import):
                        offenders.append(
                            f"{model.__name__}:fk:{field.name}->{related_model.__module__}.{related_model.__name__}"
                        )

        self.assertEqual(
            offenders,
            [],
            msg=f"Safety models must remain PMS-decoupled: {offenders}",
        )
