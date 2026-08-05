from __future__ import annotations

from django.db import migrations


INCIDENT_TYPE_ROWS = (
    ("INC_COLLISION", "Collision"),
    ("INC_GROUNDING", "Grounding"),
    ("INC_STRANDING", "Stranding"),
    ("INC_TOUCHED_BOTTOM_BERTH_ANCHORAGE", "Touched bottom at berth / anchorage"),
    ("INC_TOUCHED_BOTTOM_RIVERS_CANALS", "Touched bottom in rivers / canals"),
    ("INC_ALLISION_JETTY_BERTH_LOCKS", "Allision with Jetty / Berth / Locks"),
    ("INC_ALLISION_OTHER_VESSELS", "Allision with other Vessels"),
    ("INC_ALLISION_ICE", "Allision with ice"),
    ("INC_ALLISION_NAV_AIDS_BUOYS_OBJECTS", "Allision with Navigation Aids / Buoys / Other objects"),
    ("INC_FOUNDERING", "Foundering"),
    ("INC_CAPSIZING_LOSS_STABILITY", "Capsizing / Loss of Stability"),
    ("INC_FLOODING", "Flooding"),
    ("INC_EXPLOSION", "Explosion"),
    ("INC_FIRE", "Fire"),
    ("INC_CARGO_DAMAGE", "Cargo Damage"),
    ("INC_HULL_STRUCTURAL_FAILURE", "Hull / Structural Failure"),
    ("INC_FOULING_PIPELINE_SUBMARINE_CABLE", "The fouling or damaging by a vessel of a pipeline or submarine cable"),
    (
        "INC_FOULING_AID_TO_NAVIGATION",
        "The fouling or damaging by a vessel of an aid to navigation other than allision",
    ),
    (
        "INC_FOULING_PORT_TERMINAL_INSTALLATION",
        "The fouling or damaging by a vessel of a port/terminal installation",
    ),
    (
        "INC_EQUIPMENT_FAILURE_ELECTRICAL_POWER",
        "Failure of ship's equipment resulting in loss of vessel's electrical power",
    ),
    ("INC_EQUIPMENT_FAILURE_PROPULSION", "Failure of ship's equipment resulting in loss of propulsion"),
    (
        "INC_EQUIPMENT_FAILURE_STEERING",
        "Failure of ship's equipment resulting in loss of steering capabilities",
    ),
    (
        "INC_EQUIPMENT_FAILURE_CARGO_DELAY",
        "Failure of ship's equipment resulting in a delay of cargo operation of more than 6 hours",
    ),
    (
        "INC_EQUIPMENT_FAILURE_UNSEAWORTHY",
        "Failure of ship's equipment rendering the vessel in any other way unseaworthy",
    ),
    (
        "INC_EQUIPMENT_OR_HULL_CARGO_DAMAGE",
        "Failure of ship's equipment or hull resulting in cargo damage",
    ),
    ("INC_CREW_INJURY", "Crew Injury"),
    ("INC_POLLUTION", "Pollution"),
    ("INC_LOCAL_REGULATION_BREACH", "Breach of Local Regulations"),
    ("INC_STOWAWAY", "Stowaway Incident"),
    ("INC_SECURITY", "Security Incident"),
    ("INC_CYBER_SECURITY_BREACH", "Breach of Cyber Security"),
    ("INC_OTHER", "Other"),
)


def replace_incident_type_master_list(apps, schema_editor):
    MasterSafetyIncidentType = apps.get_model("safety", "MasterSafetyIncidentType")
    active_codes = {code for code, _name in INCIDENT_TYPE_ROWS}

    MasterSafetyIncidentType.objects.exclude(type_code__in=active_codes).update(active=False)

    next_legacy_int_id = (
        MasterSafetyIncidentType.objects.order_by("-legacy_int_id")
        .values_list("legacy_int_id", flat=True)
        .first()
        or 0
    ) + 1

    for type_code, type_name in INCIDENT_TYPE_ROWS:
        row = MasterSafetyIncidentType.objects.filter(type_code=type_code).first()
        defaults = {
            "type_name": type_name,
            "imo_reportable": True,
            "description": "Current incident type from CR-031.",
            "active": True,
        }
        if row is not None:
            for field_name, field_value in defaults.items():
                setattr(row, field_name, field_value)
            row.save(update_fields=tuple(defaults.keys()))
            continue

        MasterSafetyIncidentType.objects.create(
            legacy_int_id=next_legacy_int_id,
            type_code=type_code,
            **defaults,
        )
        next_legacy_int_id += 1


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0050_incident_reporting_context_fields"),
    ]

    operations = [
        migrations.RunPython(replace_incident_type_master_list, migrations.RunPython.noop),
    ]
