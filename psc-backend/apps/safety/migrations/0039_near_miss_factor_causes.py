from __future__ import annotations

import uuid

from django.db import migrations, models


CAUSE_OPTIONS = {
    ("HUMAN", "IMMEDIATE"): [
        "Failure to check/calibrate tools prior to use or use of defective equipment",
        "Malicious act",
        "Failure to intervene with a subordinate",
        "Failure to intervene with a peer",
        "Failure to intervene with a senior",
        "Rushing to complete task (actual pressure from other party)",
        "Rushing to complete task (perceived pressure from other party)",
        "Rushing to complete task (self-induced pressure)",
        "Fatigue due to type of task or duration",
        "Fatigue due to lack of rest",
        "Conflicts due to nationalities involved",
        "Horseplay",
        "Non-compliance with procedures, permits, PMS, or safe working practices",
        "Deliberately bypassing a safety device",
        "Safety alarm ignored",
        "Failure to secure",
        "Failure to use proper PPE",
        "Incorrect position for task",
        "Failure to warn / communicate",
        "Incorrect lifting or manual handling",
        "Failure to restrict access to unauthorized personnel",
        "Operating equipment without authority",
        "Lack of two-man verification check",
        "Other",
        "Not Applicable",
    ],
    ("VESSEL", "IMMEDIATE"): [
        "PMS routines not followed",
        "Defective equipment not properly taken out of service or quarantined",
        "Ineffective isolation of equipment",
        "Wrong tool for job / Inadequate tools",
        "Correct tool not available on board / Inadequate tools",
        "Defective tools / Defective material / Inadequate tools",
        "Inadequate information from manufacturer",
        "Inadequate or excessive illumination",
        "Excessive wear and tear (not related to maintenance)",
        "Ropes, wires breaking or jamming",
        "Missing safety device",
        "Failed safety device",
        "Non-operational safety alarm",
        "Inadequate or inoperative guards, barriers, warning signs, or safety devices",
        "Accidental release of pressure (fluids or gases)",
        "Critical equipment failure",
        "Inadequate or restricted space",
        "Defective ladders / stairs",
        "Other",
        "Not Applicable",
    ],
    ("MANAGEMENT", "IMMEDIATE"): [
        "Inadequate ventilation and/or unsafe atmosphere",
        "Inadequate preparation / testing of work area",
        "Incorrect navigation or ship handling",
        "Incorrect cargo / bunkers line setting",
        "Incorrect cargo lashing or stowage",
        "Outdated charts or other navigational publications",
        "Poor housekeeping",
        "Inadequate instructions provided",
        "Lack of inadequate toolbox talk",
        "Inadequate firewalls",
        "Failure of BTM",
        "Other",
        "Not Applicable",
    ],
    ("OTHER", "IMMEDIATE"): [
        "Influence of drug, alcohol, or prescription medicine",
        "Inadequate port or berthing facilities",
        "Inadequate aids to navigation",
        "Exposure to chemicals (cargo, cleaning agents, fuel, additives, etc.)",
        "Wet, slippery, uneven, or defective surfaces",
        "Excessive environmental factors - Hot temperature",
        "Excessive environmental factors - Cold temperature",
        "Excessive environmental factors - Noise",
        "Excessive environmental factors - Vessel movement / adverse weather conditions",
        "Poor quality bunkers or lube oil",
        "Other",
        "Not Applicable",
    ],
    ("HUMAN", "ROOT"): [
        "Lack of knowledge",
        "Lack of skills",
        "Inadequate training",
        "Inadequate refresher training frequency",
        "Inadequate familiarization",
        "Inadequate / insufficient resources",
        "Limited physical capabilities",
        "Disturbed mental state, stress, confusion, or panic",
        "Improper behaviour / performance tolerated or rewarded",
        "Routine / repetitious work",
        "Too high workload",
        "Overconfidence",
        "Lack of situational awareness",
        "Poor risk awareness / perception of risk",
        "Lack of motivation / morale",
        "Ergonomic issue with MMI (Man Machine Interface)",
        "Language problem",
        "Inadequate experience",
        "Other",
        "Not Applicable",
    ],
    ("VESSEL", "ROOT"): [
        "Lack of spares / tools - Inadequate maintenance program",
        "Incorrect type of maintenance - Inadequate maintenance program",
        "Inappropriate procurement due to inappropriate transportation by supplier",
        "Inappropriate procurement due to poor quality of supplier",
        "Inappropriate procurement due to inappropriate storage by supplier",
        "Design or engineering defect",
        "Latent defect",
        "Other",
        "Not Applicable",
    ],
    ("MANAGEMENT", "ROOT"): [
        "Shore management failure (ISM)",
        "Shipboard management failure (SMS)",
        "Inadequate or incorrect procedures",
        "Lack of proper supervision / leadership",
        "Inadequate checklists",
        "Inadequate audit process",
        "Inadequate contingency plans",
        "Failure in MOC process",
        "High turnover of personnel",
        "Inadequate resources",
        "Hiring and selection policy",
        "Communication failure - Due to language issues",
        "Communication failure - Due to poor delivery of instructions",
        "Communication failure - Conflicting orders",
        "Poor work planning",
        "Inadequate Master / Pilot exchange",
        "Over-reliance on pilot",
        "Other",
        "Not Applicable",
    ],
    ("OTHER", "ROOT"): [
        "Geographical constraints",
        "External Factors - Pilots",
        "External Factors - Shore mooring crew",
        "External Factors - Terminal personnel",
        "External Factors - Local authorities",
        "External Factors - Other personnel not under control of shipboard management",
        "External Factors - Contractors",
        "Unlawful act",
        "Other",
        "Not Applicable",
    ],
}


def seed_near_miss_cause_options(apps, schema_editor):
    NearMissCauseOption = apps.get_model("safety", "NearMissCauseOption")
    for (factor, cause_stage), option_texts in CAUSE_OPTIONS.items():
        for display_order, option_text in enumerate(option_texts, start=1):
            if option_text == "Other":
                suffix = "OTHER"
            elif option_text == "Not Applicable":
                suffix = "NA"
            else:
                suffix = f"{display_order:03d}"
            option_code = f"{factor}_{cause_stage}_{suffix}"
            NearMissCauseOption.objects.update_or_create(
                factor=factor,
                cause_stage=cause_stage,
                option_code=option_code,
                defaults={
                    "option_text": option_text,
                    "display_order": display_order,
                    "active": True,
                    "updated_by": "migration",
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ("safety", "0038_incident_multiple_loss_types"),
    ]

    operations = [
        migrations.CreateModel(
            name="NearMissCauseOption",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "factor",
                    models.CharField(
                        choices=[
                            ("HUMAN", "Human Factors"),
                            ("VESSEL", "Vessel Factors"),
                            ("MANAGEMENT", "Management Factors"),
                            ("OTHER", "Other Factors"),
                        ],
                        db_index=True,
                        max_length=16,
                    ),
                ),
                (
                    "cause_stage",
                    models.CharField(
                        choices=[("IMMEDIATE", "Immediate Cause"), ("ROOT", "Root Cause")],
                        db_index=True,
                        max_length=16,
                    ),
                ),
                ("option_code", models.CharField(db_index=True, max_length=64)),
                ("option_text", models.TextField()),
                ("display_order", models.PositiveSmallIntegerField(default=0)),
                ("active", models.BooleanField(default=True)),
                ("created_by", models.CharField(default="system", max_length=128)),
                ("created_date", models.DateTimeField(auto_now_add=True)),
                ("updated_by", models.CharField(blank=True, max_length=128, null=True)),
                ("updated_date", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "db_table": "vims_safety_near_miss_cause_option",
                "ordering": ("factor", "cause_stage", "display_order", "option_text"),
            },
        ),
        migrations.AddField(
            model_name="incident",
            name="near_miss_factor_causes",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddConstraint(
            model_name="nearmisscauseoption",
            constraint=models.UniqueConstraint(
                fields=("factor", "cause_stage", "option_code"),
                name="uq_nm_cause_option_factor_stage_code",
            ),
        ),
        migrations.AddIndex(
            model_name="nearmisscauseoption",
            index=models.Index(fields=("active", "factor", "cause_stage"), name="ix_nm_cause_option_lookup"),
        ),
        migrations.RunPython(seed_near_miss_cause_options, migrations.RunPython.noop),
    ]
