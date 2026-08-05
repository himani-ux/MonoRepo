from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0057_remove_recommendation_tier_cardinality"),
    ]

    operations = [
        migrations.AddField(
            model_name="incident",
            name="activity_type",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="incident_type_other",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="permit_issued",
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="risk_assessment_carried_out",
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="toolbox_meeting_carried_out",
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name="incident",
            name="vessel_location_detail",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddConstraint(
            model_name="incident",
            constraint=models.CheckConstraint(
                condition=Q(risk_assessment_carried_out__isnull=True)
                | Q(risk_assessment_carried_out__in=("YES", "NO", "NA")),
                name="ck_vims_safety_incident_risk_assessment",
            ),
        ),
        migrations.AddConstraint(
            model_name="incident",
            constraint=models.CheckConstraint(
                condition=Q(toolbox_meeting_carried_out__isnull=True)
                | Q(toolbox_meeting_carried_out__in=("YES", "NO", "NA")),
                name="ck_vims_safety_incident_toolbox_meeting",
            ),
        ),
        migrations.AddConstraint(
            model_name="incident",
            constraint=models.CheckConstraint(
                condition=Q(permit_issued__isnull=True) | Q(permit_issued__in=("YES", "NO", "NA")),
                name="ck_vims_safety_incident_permit_issued",
            ),
        ),
    ]
