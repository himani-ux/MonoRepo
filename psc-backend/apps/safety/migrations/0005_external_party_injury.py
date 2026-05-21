from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0004_recommendation_verification"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExternalPartyInjury",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("party_name", models.CharField(max_length=128)),
                (
                    "party_type",
                    models.CharField(
                        choices=[
                            ("PILOT", "Pilot"),
                            ("SHIPYARD", "Shipyard"),
                            ("STEVEDORE", "Stevedore"),
                            ("CONTRACTOR", "Contractor"),
                            ("PASSENGER", "Passenger"),
                            ("PORT_AGENT", "Port Agent"),
                            ("OTHER", "Other"),
                        ],
                        max_length=32,
                    ),
                ),
                ("company_name", models.CharField(max_length=128)),
                ("severity", models.CharField(max_length=64)),
                ("notes", models.TextField(blank=True, null=True)),
                ("schema_version", models.PositiveIntegerField(default=1)),
                ("created_by", models.CharField(max_length=128)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("updated_by", models.CharField(blank=True, max_length=128, null=True)),
                ("updated_date", models.DateTimeField(blank=True, null=True)),
                (
                    "incident",
                    models.OneToOneField(
                        db_column="incident_id",
                        db_constraint=False,
                        on_delete=models.deletion.DO_NOTHING,
                        related_name="external_party_injury",
                        to="safety.VimsSafetyIncident",
                    ),
                ),
            ],
            options={
                "db_table": "vims_safety_external_party_injury",
                "ordering": ("incident_id", "id"),
            },
        ),
    ]
