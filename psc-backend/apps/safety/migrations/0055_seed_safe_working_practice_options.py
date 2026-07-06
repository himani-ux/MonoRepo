from __future__ import annotations

from django.db import migrations


SAFE_WORKING_PRACTICE_OPTIONS = [
    "Health and hygiene",
    "Good housekeeping",
    "Fitness, health and hygiene",
    "Smoking",
    "Avoiding the effects of fatigue (tiredness)",
    "Working in hot or sunny climates and hot environments",
    "Working in cold climates and environments",
    "Risk from sharps",
    "Head protection",
    "Hearing protection",
    "Face and eye protection",
    "Respiratory protective equipment",
    "Hand and foot protection",
    "Protection from falls",
    "Body protection",
    "Protection against drowning",
    "Gas cylinders",
    "Pipelines",
    "Portable fire extinguishers",
    "Good manual-handling techniques",
    "Drainage",
    "Lighting",
    "Guarding of openings",
    "Watertight doors",
    "Stairways, ladders and portable ladders",
    "Shipboard vehicles",
    "Working on deck while ship is at sea",
    "Adverse weather",
    "General advice to seafarers",
    "Assessing exposure to noise",
    "Mitigation: hand-arm vibration",
    "Mitigation: whole-body vibration",
    "Permit to work systems",
    "Enclosed Space Entry",
    "Portable ladders",
    "Cradles and stages",
    "Bosun's chair",
    "Working from punts",
    "Scaffolding",
    "Hand tools",
    "Electrical equipment",
    "High or very low temperatures",
    "Controls",
    "Markings",
    "Warnings",
    "Portable power-operated tools and equipment",
    "Workshop and bench machines (fixed installations)",
    "Abrasive wheels",
    "Hydraulic/pneumatic/high-pressure jetting equipment",
    "Hydraulic jacks",
    "Use of mobile work equipment",
    "Carrying of seafarers on mobile work equipment",
    "Overturning of fork-lift trucks",
    "Self-propelled work equipment",
    "Remote-controlled self-propelled work equipment",
    "Drive units and power take-off shafts",
    "Ropes and wires",
    "Laundry equipment",
    "Lifting Plant",
    "Thorough examination of lifting equipment",
    "Reports, records and marking of lifting equipment",
    "Lifting operations",
    "Use of winches and cranes",
    "Use of derricks",
    "Use of derricks in union purchase",
    "Use of stoppers",
    "Overhaul of cargo gear",
    "Trucks and other vehicles/appliances",
    "Personnel-lifting equipment, lifts",
    "Maintenance and testing of lifts",
    "Work in machinery spaces",
    "Unmanned machinery spaces",
    "Maintenance of machinery",
    "Hydraulic and pneumatic equipment",
    "Storage batteries: general",
    "Storage batteries: lead acid",
    "Storage batteries: alkaline",
    "Carcinogens and mutagens",
    "Safety nets",
    "Use of Equipment",
    "Access for pilots",
    "Safe rigging of pilot ladder",
    "Safe access to small craft",
    "Slips, falls and tripping hazards",
    "Galley stoves, steam boilers and deep fat fryers",
    "Liquid petroleum gas appliances",
    "Deep fat frying",
    "Microwave ovens",
    "Catering equipment",
    "Knives, meat saws, choppers, etc.",
    "Refrigerated rooms and store rooms",
    "Painting",
]


def _unique_options() -> list[str]:
    seen: set[str] = set()
    unique_options: list[str] = []
    for option in SAFE_WORKING_PRACTICE_OPTIONS:
        if option in seen:
            continue
        seen.add(option)
        unique_options.append(option)
    return unique_options


def seed_safe_working_practice_options(apps, schema_editor):
    InjuryDropdownOption = apps.get_model("safety", "InjuryDropdownOption")
    field_key = "SAFE_WORKING_PRACTICE"
    active_options = _unique_options()
    for display_order, option_label in enumerate(active_options, start=1):
        InjuryDropdownOption.objects.update_or_create(
            field_key=field_key,
            option_label=option_label,
            defaults={
                "display_order": display_order,
                "active": True,
                "created_by": "migration",
                "updated_by": "migration",
            },
        )
    InjuryDropdownOption.objects.filter(field_key=field_key).exclude(
        option_label__in=active_options
    ).update(active=False, updated_by="migration")


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0054_alter_injurydropdownoption_field_key"),
    ]

    operations = [
        migrations.RunPython(seed_safe_working_practice_options, migrations.RunPython.noop),
    ]
