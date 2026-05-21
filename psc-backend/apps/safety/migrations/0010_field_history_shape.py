from __future__ import annotations

import json

from django.db import migrations, models


def _normalize_legacy_history_value(value):
    if value is None:
        return None
    if isinstance(value, (dict, list, bool, int, float)):
        return value

    text = str(value)
    stripped = text.strip()
    if (
        (stripped.startswith("{") and stripped.endswith("}"))
        or (stripped.startswith("[") and stripped.endswith("]"))
    ):
        try:
            return json.loads(stripped)
        except (TypeError, ValueError, json.JSONDecodeError):
            return text
    return text


def normalize_legacy_field_history_values(apps, schema_editor):
    FieldHistory = apps.get_model("safety", "VimsSafetyFieldHistory")

    for row in FieldHistory.objects.all().iterator():
        update_fields: list[str] = []
        for field_name in ("old_value", "new_value"):
            raw_value = getattr(row, field_name)
            normalized = _normalize_legacy_history_value(raw_value)
            serialized = None if normalized is None else json.dumps(normalized, sort_keys=True, default=str)
            if raw_value != serialized:
                setattr(row, field_name, serialized)
                update_fields.append(field_name)
        if update_fields:
            row.save(update_fields=update_fields)


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0009_tighten_incident_enums"),
    ]

    operations = [
        migrations.RunPython(normalize_legacy_field_history_values, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="vimssafetyfieldhistory",
            name="old_value",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="vimssafetyfieldhistory",
            name="new_value",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
