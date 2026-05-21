from __future__ import annotations

import uuid

from django.db import migrations, models


PUBLIC_ID_MODELS = (
    "incident",
    "incidentphaselog",
    "safetyfieldhistory",
    "incidentfact",
    "incidentphase5assessment",
    "incidentcausetag",
    "incidentsafeguardfailure",
    "incidentbiasguardresponse",
    "incidentblameoverride",
    "safetydashboardrollup",
    "incidentevidence",
    "evidenceitem",
    "chainofcustody",
    "witnessinterview",
    "evidencedeadlinetask",
    "externalpartyinjury",
    "recommendation",
    "correctiveaction",
    "recommendationverification",
    "scmmeeting",
    "scmattendance",
    "scmsignature",
    "scmagendaitem",
    "scmlegacyfield",
    "soiinspection",
    "soiofficersetting",
    "soiapplicabilitylog",
    "soivesselareamap",
    "soifinding",
    "soiinspectionarea",
    "soitrainee",
)


def backfill_public_ids(apps, schema_editor):
    for model_name in PUBLIC_ID_MODELS:
        model = apps.get_model("safety", model_name)
        queryset = model.objects.filter(public_id__isnull=True).only("pk")
        for row in queryset.iterator(chunk_size=500):
            model.objects.filter(pk=row.pk, public_id__isnull=True).update(public_id=uuid.uuid4())


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0028_phase_log_signature_valid"),
    ]

    operations = [
        *[
            migrations.AddField(
                model_name=model_name,
                name="public_id",
                field=models.UUIDField(editable=False, null=True),
            )
            for model_name in PUBLIC_ID_MODELS
        ],
        migrations.RunPython(backfill_public_ids, migrations.RunPython.noop),
        *[
            migrations.AlterField(
                model_name=model_name,
                name="public_id",
                field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True),
            )
            for model_name in PUBLIC_ID_MODELS
        ],
    ]
