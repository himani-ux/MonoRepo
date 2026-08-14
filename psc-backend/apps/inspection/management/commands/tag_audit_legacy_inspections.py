from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime

from apps.inspection.audit.services.legacy_tagging import tag_legacy_audit_inspections


class Command(BaseCommand):
    help = (
        "Discover pre-deploy AUDIT/RS psc_inspection rows and optionally tag "
        "them in audit_legacy_inspection_tag."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--database",
            default="default",
            help="Database alias to inspect. Defaults to 'default'.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write missing tags to audit_legacy_inspection_tag. Omit for no-write probe.",
        )
        parser.add_argument(
            "--deploy-date",
            default=None,
            help="Optional ISO datetime cutoff; only rows with created_date before it are tagged.",
        )
        parser.add_argument(
            "--tagged-by",
            default="migration",
            help="Value for audit_legacy_inspection_tag.tagged_by when --apply is used.",
        )

    def handle(self, *args, **options):
        deploy_date = None
        if options["deploy_date"]:
            deploy_date = parse_datetime(options["deploy_date"])
            if deploy_date is None:
                raise CommandError("--deploy-date must be an ISO datetime.")

        try:
            result = tag_legacy_audit_inspections(
                using=options["database"],
                apply=options["apply"],
                deploy_date=deploy_date,
                tagged_by=options["tagged_by"],
            )
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        mode = "apply" if options["apply"] else "dry-run"
        self.stdout.write(
            "LEGACY_TAGGING "
            f"mode={mode} discovered={result.discovered} "
            f"already_tagged={result.already_tagged} inserted={result.inserted}"
        )
