from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0021_scm_lifecycle_signature"),
    ]

    operations = [
        migrations.AddField(
            model_name="scmmeeting",
            name="occasion",
            field=models.CharField(default="M", max_length=8),
        ),
        migrations.AddField(
            model_name="scmmeeting",
            name="ship_position",
            field=models.CharField(default="P", max_length=1),
        ),
        migrations.AddField(
            model_name="scmmeeting",
            name="ship_pos_from",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="scmmeeting",
            name="ship_pos_to",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="scmmeeting",
            name="comm_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="scmmeeting",
            name="comp_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="scmmeeting",
            constraint=models.CheckConstraint(
                condition=Q(ship_position__in=["S", "P"]),
                name="ck_vims_safety_scm_ship_position",
            ),
        ),
        migrations.CreateModel(
            name="SCMLegacyField",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("meeting_id", models.BigIntegerField()),
                ("agenda_item_number", models.IntegerField()),
                ("field_key", models.CharField(max_length=64)),
                ("field_label", models.CharField(max_length=160)),
                (
                    "field_type",
                    models.CharField(
                        choices=[
                            ("BOOLEAN", "Boolean"),
                            ("DATE", "Date"),
                            ("INTEGER", "Integer"),
                            ("TEXT", "Text"),
                        ],
                        default="TEXT",
                        max_length=16,
                    ),
                ),
                ("field_value", models.TextField(blank=True, null=True)),
                ("schema_version", models.IntegerField(default=1)),
            ],
            options={
                "db_table": "vims_safety_scm_legacy_field",
                "ordering": ("agenda_item_number", "id"),
            },
        ),
        migrations.AddConstraint(
            model_name="scmlegacyfield",
            constraint=models.UniqueConstraint(
                fields=("meeting_id", "agenda_item_number", "field_key"),
                name="uq_vims_safety_scm_legacy_field",
            ),
        ),
        migrations.AddConstraint(
            model_name="scmlegacyfield",
            constraint=models.CheckConstraint(
                condition=Q(agenda_item_number__gte=1) & Q(agenda_item_number__lte=10),
                name="ck_vims_safety_scm_legacy_section",
            ),
        ),
        migrations.AddConstraint(
            model_name="scmlegacyfield",
            constraint=models.CheckConstraint(
                condition=Q(field_type__in=["BOOLEAN", "DATE", "INTEGER", "TEXT"]),
                name="ck_vims_safety_scm_legacy_type",
            ),
        ),
        migrations.AddIndex(
            model_name="scmlegacyfield",
            index=models.Index(fields=("meeting_id", "agenda_item_number"), name="ix_safe_scml_meet_sec"),
        ),
    ]
