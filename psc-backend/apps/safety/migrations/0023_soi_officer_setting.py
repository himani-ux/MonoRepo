from django.db import migrations, models
from django.db.models.functions import Now


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0022_scm_legacy_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="SOIOfficerSetting",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("vessel_id", models.CharField(max_length=64, unique=True)),
                ("alternate_enabled", models.BooleanField(db_default=False, default=False)),
                ("alternate_so_crew_id", models.CharField(blank=True, max_length=64, null=True)),
                ("reason", models.TextField(blank=True, null=True)),
                ("enabled_by", models.CharField(blank=True, max_length=128, null=True)),
                ("enabled_at", models.DateTimeField(blank=True, null=True)),
                ("disabled_by", models.CharField(blank=True, max_length=128, null=True)),
                ("disabled_at", models.DateTimeField(blank=True, null=True)),
                ("schema_version", models.IntegerField(db_default=1, default=1)),
                ("created_by", models.CharField(blank=True, max_length=128, null=True)),
                ("created_date", models.DateTimeField(auto_now_add=True, db_default=Now())),
                ("updated_by", models.CharField(blank=True, max_length=128, null=True)),
                ("updated_date", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "vims_safety_soi_officer_setting",
            },
        ),
        migrations.AddIndex(
            model_name="soiofficersetting",
            index=models.Index(fields=["vessel_id", "alternate_enabled"], name="ix_safe_sois_vsl_enabled"),
        ),
    ]
