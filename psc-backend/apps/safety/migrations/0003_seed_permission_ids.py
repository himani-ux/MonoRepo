from __future__ import annotations

from django.db import migrations


FORM_LABELS = {
    1: "SAFETY_INCIDENT",
    2: "SAFETY_NEAR_MISS",
    3: "SAFETY_SCM",
    4: "SAFETY_SOI",
    17: "SAFETY_AUDIT",
    18: "SAFETY_REFERENCE_DATA",
    20: "SAFETY_EXPORT",
}

PROCESS_LABELS = {
    1: "SAFETY_CREATE",
    2: "SAFETY_SUBMIT",
    3: "SAFETY_SEND_BACK",
    4: "SAFETY_APPROVE_CLOSE",
    5: "SAFETY_FM_APPROVE",
    6: "SAFETY_BLAME_OVERRIDE",
    7: "SAFETY_EXPORT_PDF",
    8: "SAFETY_REOPEN",
    9: "SAFETY_FLEET_ALERT",
    10: "SAFETY_SOI_APPLICABILITY_REQUEST",
    11: "SAFETY_SOI_DOWNLOAD",
    12: "SAFETY_SCM_AD_HOC_CREATE",
    13: "SAFETY_SOI_REGISTER_FINDING",
    14: "SAFETY_SOI_PENDING_CLOSURE",
    15: "SAFETY_SOI_APPROVE_CLOSURE",
    16: "SAFETY_SOI_APPLICABILITY_APPROVE",
    17: "SAFETY_SOI_APPLICABILITY_REJECT",
    18: "SAFETY_MSCAT_UPDATE",
    19: "SAFETY_SOI_ITEM_UPDATE",
    20: "SAFETY_CA_CREATE",
    21: "SAFETY_CA_LINK_PURCHASE",
    22: "SAFETY_CA_VERIFY",
    23: "SAFETY_EXPORT_RECORD",
    24: "SAFETY_ADMIN",
}

PERMISSIONS = tuple(
    [
        (f"SAF_F_{index:03d}", FORM_LABELS.get(index, f"SAFETY_FORM_{index:03d}"), "form")
        for index in range(1, 21)
    ]
    + [
        (
            f"SAF_P_{index:03d}",
            PROCESS_LABELS.get(index, f"SAFETY_PROCESS_{index:03d}"),
            "process",
        )
        for index in range(1, 25)
    ]
)


def seed_permission_catalog(apps, schema_editor) -> None:
    existing_tables = set(schema_editor.connection.introspection.table_names())
    if "msc_profiles_catalog" not in existing_tables:
        return

    with schema_editor.connection.cursor() as cursor:
        for code, label, kind in PERMISSIONS:
            cursor.execute(
                "SELECT 1 FROM msc_profiles_catalog WHERE code = %s",
                [code],
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO msc_profiles_catalog (code, label, kind) VALUES (%s, %s, %s)",
                    [code, label, kind],
                )


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0002_seed_master_tables"),
    ]

    operations = [
        migrations.RunPython(seed_permission_catalog, migrations.RunPython.noop),
    ]
