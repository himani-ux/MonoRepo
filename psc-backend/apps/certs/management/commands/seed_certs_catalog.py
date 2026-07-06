from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from apps.certs.catalog_workshop_seed import load_catalog_workshop_rows, seed_certs_catalog_rows


class Command(BaseCommand):
    help = "Seed the Phase 1.12 approved Certs catalog workshop CSV into vims_certs_catalog_row."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--input", required=True, help="Path to the approved Phase 1.12 catalog workshop CSV.")
        parser.add_argument("--apply", action="store_true", help="Persist rows and create audit entries.")
        parser.add_argument("--approved-by", help="Approver name(s), required with --apply.")
        parser.add_argument("--approval-ref", help="Workshop approval reference, required with --apply.")

    def handle(self, *args, **options):
        apply_changes = bool(options["apply"])
        approved_by = (options.get("approved_by") or "").strip()
        approval_ref = (options.get("approval_ref") or "").strip()
        if apply_changes and (not approved_by or not approval_ref):
            raise CommandError("--apply requires --approved-by and --approval-ref.")

        rows = load_catalog_workshop_rows(options["input"])
        actor_id = _actor_id(approved_by) if apply_changes else "seed_certs_catalog_dry_run"
        effective_ref = approval_ref if apply_changes else "DPA/Tech Sup'tt approval not supplied - dry run only"

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    IF OBJECT_ID(N'dbo.vims_certs_catalog_row', N'U') IS NULL
                    BEGIN
                        THROW 51000, 'dbo.vims_certs_catalog_row does not exist. Run certs migrations first.', 1;
                    END
                    IF OBJECT_ID(N'dbo.vims_certs_audit_log', N'U') IS NULL
                    BEGIN
                        THROW 51000, 'dbo.vims_certs_audit_log does not exist. Run certs migrations first.', 1;
                    END
                    """
                )
                result = seed_certs_catalog_rows(
                    cursor,
                    rows,
                    actor_id=actor_id,
                    approval_ref=effective_ref,
                    dry_run=not apply_changes,
                )

        if apply_changes:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Seeded {result.created_count} approved catalog row(s); "
                    f"skipped {result.skipped_count} existing row(s)."
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                "Dry run only. "
                f"Would create {result.would_create_count} catalog row(s) and skip "
                f"{result.would_skip_count} existing row(s). "
                "Re-run with --apply --approved-by <name> --approval-ref <ref> only after DPA + Tech Sup'tt approval."
            )
        )


def _actor_id(approved_by: str) -> str:
    normalized = "_".join(approved_by.lower().split())
    return f"seed_certs_catalog:{normalized}"[:64]
