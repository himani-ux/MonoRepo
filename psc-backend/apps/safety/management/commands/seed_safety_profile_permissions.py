from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from apps.accounts.models import MscProfile
from apps.safety.profile_permission_seed import (
    merge_permission_lists,
    serialize_permission_list,
    target_permissions_for_profile,
)


class Command(BaseCommand):
    help = "Append Safety SAF_F_* and SAF_P_* permissions into active msc_profiles rows."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persist the computed Safety permissions into msc_profiles.",
        )

    def handle(self, *args, **options):
        apply_changes = bool(options["apply"])
        profiles = list(
            MscProfile.objects.filter(is_active=True, is_deleted=False)
            .order_by("work_side", "profile_name", "-created_on")
        )

        updates: list[tuple[MscProfile, str, str]] = []
        for profile in profiles:
            bundle = target_permissions_for_profile(
                work_side=bool(profile.work_side),
                profile_name=profile.profile_name,
            )
            if not bundle.form_ids and not bundle.process_ids:
                continue

            merged_forms = merge_permission_lists(profile.form_ids, bundle.form_ids)
            merged_processes = merge_permission_lists(profile.process_ids, bundle.process_ids)
            serialized_forms = serialize_permission_list(merged_forms)
            serialized_processes = serialize_permission_list(merged_processes)

            if serialized_forms == (profile.form_ids or "") and serialized_processes == (profile.process_ids or ""):
                continue

            updates.append((profile, serialized_forms, serialized_processes))

        if not updates:
            self.stdout.write(self.style.SUCCESS("No msc_profiles updates are required."))
            return

        for profile, serialized_forms, serialized_processes in updates:
            scope = "SHIP" if profile.work_side else "OFFICE"
            self.stdout.write(
                f"{scope:<6} {profile.profile_name}: "
                f"forms -> {serialized_forms} | processes -> {serialized_processes}"
            )

        if not apply_changes:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run only. Re-run with --apply to update {len(updates)} msc_profiles row(s)."
                )
            )
            return

        with transaction.atomic():
            sql = (
                "UPDATE msc_profiles "
                "SET form_ids = %s, process_ids = %s "
                "WHERE id = CAST(%s AS uniqueidentifier)"
            )
            for profile, serialized_forms, serialized_processes in updates:
                with connection.cursor() as cursor:
                    cursor.execute(
                        sql,
                        [serialized_forms, serialized_processes, str(profile.pk)],
                    )
                    if cursor.rowcount != 1:
                        raise RuntimeError(
                            f"Expected to update exactly one msc_profiles row for {profile.profile_name}, "
                            f"updated {cursor.rowcount}."
                        )

        self.stdout.write(self.style.SUCCESS(f"Updated {len(updates)} msc_profiles row(s)."))
