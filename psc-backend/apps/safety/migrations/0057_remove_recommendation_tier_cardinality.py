from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0056_incident_loss_evaluation_report_type"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "IF EXISTS ("
                        "SELECT 1 FROM sys.indexes "
                        "WHERE name = 'uq_vims_safety_recommendation_incident_tier_active' "
                        "AND object_id = OBJECT_ID('vims_safety_recommendation')"
                        ") "
                        "DROP INDEX [uq_vims_safety_recommendation_incident_tier_active] "
                        "ON [vims_safety_recommendation];"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.RemoveConstraint(
                    model_name="recommendation",
                    name="uq_vims_safety_recommendation_incident_tier_active",
                ),
            ],
        ),
    ]
