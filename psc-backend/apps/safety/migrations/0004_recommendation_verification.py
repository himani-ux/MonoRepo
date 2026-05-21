from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0003_seed_permission_ids"),
    ]

    operations = [
        migrations.CreateModel(
            name="RecommendationVerification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_effective", models.BooleanField()),
                ("residual_risk", models.CharField(max_length=32)),
                ("verified_at", models.DateTimeField(auto_now_add=True)),
                ("verified_by", models.CharField(max_length=64)),
                ("notes", models.TextField(blank=True, null=True)),
                (
                    "recommendation",
                    models.ForeignKey(
                        db_column="recommendation_id",
                        on_delete=models.deletion.CASCADE,
                        related_name="verifications",
                        to="safety.VimsSafetyRecommendation",
                    ),
                ),
            ],
            options={
                "db_table": "vims_safety_recommendation_verification",
                "ordering": ("verified_at", "id"),
            },
        ),
        migrations.AddIndex(
            model_name="recommendationverification",
            index=models.Index(
                fields=["recommendation", "verified_at"],
                name="ix_vims_safety_recommendation_verification_rec",
            ),
        ),
        migrations.AddIndex(
            model_name="recommendationverification",
            index=models.Index(
                fields=["is_effective"],
                name="ix_vims_safety_recommendation_verification_effective",
            ),
        ),
    ]
