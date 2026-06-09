from django.db import migrations, models
from django.db.models import Q


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0034_near_miss_place_multiselect"),
    ]

    operations = [
        migrations.AlterField(
            model_name="scmmeeting",
            name="state",
            field=models.CharField(
                choices=[
                    ("DRAFT", "Draft"),
                    ("SUBMITTED", "Submitted"),
                    ("SIGNED_OFF", "Signed Off"),
                    ("REOPENED", "Reopened"),
                    ("CLOSED", "Closed"),
                ],
                default="DRAFT",
                max_length=24,
            ),
        ),
        migrations.RemoveConstraint(
            model_name="scmmeeting",
            name="ck_vims_safety_scm_meeting_state",
        ),
        migrations.AddConstraint(
            model_name="scmmeeting",
            constraint=models.CheckConstraint(
                condition=Q(state__in=["DRAFT", "SUBMITTED", "SIGNED_OFF", "REOPENED", "CLOSED"]),
                name="ck_vims_safety_scm_meeting_state",
            ),
        ),
    ]
