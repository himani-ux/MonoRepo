from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0045_incident_cause_factor_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="externalpartyinjury",
            name="injured_person_type",
            field=models.CharField(
                choices=[("CREW", "Crew"), ("NON_CREW", "Non-crew")],
                default="NON_CREW",
                max_length=16,
            ),
        ),
        migrations.AlterField(
            model_name="externalpartyinjury",
            name="party_name",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AlterField(
            model_name="externalpartyinjury",
            name="party_type",
            field=models.CharField(
                blank=True,
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
        migrations.AlterField(
            model_name="externalpartyinjury",
            name="company_name",
            field=models.CharField(blank=True, max_length=128),
        ),
        migrations.AlterField(
            model_name="externalpartyinjury",
            name="severity",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="crew_rank",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="crew_age",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="crew_activity_type",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="shore_assistance_required",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="vessel_location",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="onboard_location",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="last_port",
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="departure_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="vessel_condition",
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="what_happened_narrative",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="nature_of_injury",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="source_of_injury",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="affected_body_areas",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="first_aid_details",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="why_it_happened_analysis",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="regulation_or_procedure_breach",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="risk_assessment_carried_out",
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="toolbox_meeting_carried_out",
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="prevention_action_taken_required",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="ocimf_fatality",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="ocimf_permanent_total_disability",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="ocimf_permanent_partial_disability",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="ocimf_lost_workday_case",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="ocimf_restricted_workday_case",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="ocimf_medical_treatment_case",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="ocimf_first_aid_case",
            field=models.BooleanField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="cost_medicines_onboard",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="cost_doctor_visits",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="cost_repatriation",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="cost_evacuation",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="cost_off_hire",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="cost_vessel_delays",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="cost_man_hours_lost",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="cost_deviation",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="cost_miscellaneous",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="miscellaneous_expenses_reason",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="externalpartyinjury",
            name="total_estimated_cost",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
    ]
