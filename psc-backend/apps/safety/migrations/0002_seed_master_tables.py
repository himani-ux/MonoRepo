from __future__ import annotations

from django.db import migrations
from django.core.management.base import CommandError

from apps.safety.management.commands.seed_master_safety import SEED_TABLE_SPECS, seed_master_safety


def seed_master_tables(apps, schema_editor) -> None:
    existing_tables = set(schema_editor.connection.introspection.table_names())
    required_tables = {spec.table_name for spec in SEED_TABLE_SPECS}
    if not required_tables.issubset(existing_tables):
        return

    try:
        seed_master_safety(using=schema_editor.connection.alias)
    except CommandError:
        # Some checkouts omit the optional seed-data payloads. Keep schema migration
        # unblocked; reference data can be loaded later when the files are available.
        return


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_master_tables, migrations.RunPython.noop),
    ]
