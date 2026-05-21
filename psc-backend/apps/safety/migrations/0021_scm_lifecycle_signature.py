from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0020_near_miss_lightweight_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="scmmeeting",
            name="attendance_warnings_acknowledged_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="scmmeeting",
            name="attendance_warnings_acknowledged_by",
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.CreateModel(
            name="SCMSignature",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("meeting_id", models.BigIntegerField()),
                (
                    "signer_role",
                    models.CharField(
                        choices=[("MASTER", "Master"), ("CO", "Chief Officer"), ("ATTENDEE", "Attendee")],
                        max_length=16,
                    ),
                ),
                ("signer_crew_id", models.CharField(max_length=64)),
                ("display_name", models.CharField(max_length=128)),
                ("typed_name", models.CharField(max_length=128)),
                ("device_fingerprint", models.CharField(max_length=128)),
                ("signed_at", models.DateTimeField()),
                ("created_by", models.CharField(max_length=128)),
                ("schema_version", models.IntegerField(default=1)),
            ],
            options={
                "db_table": "vims_safety_scm_signature",
                "indexes": [
                    models.Index(fields=["meeting_id"], name="ix_safe_scms_meet"),
                    models.Index(fields=["signer_role"], name="ix_safe_scms_role"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("meeting_id", "signer_role", "signer_crew_id"),
                        name="uq_vims_safety_scm_signature",
                    )
                ],
            },
        ),
    ]
