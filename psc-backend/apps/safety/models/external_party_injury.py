from __future__ import annotations

from django.db import models

from .base import PublicIdMixin


class ExternalPartyInjury(PublicIdMixin):
    class PartyType(models.TextChoices):
        PILOT = "PILOT", "Pilot"
        SHIPYARD = "SHIPYARD", "Shipyard"
        STEVEDORE = "STEVEDORE", "Stevedore"
        CONTRACTOR = "CONTRACTOR", "Contractor"
        PASSENGER = "PASSENGER", "Passenger"
        PORT_AGENT = "PORT_AGENT", "Port Agent"
        OTHER = "OTHER", "Other"

    incident = models.OneToOneField(
        "safety.Incident",
        db_column="incident_id",
        db_constraint=False,
        on_delete=models.DO_NOTHING,
        related_name="external_party_injury",
    )
    party_name = models.CharField(max_length=128)
    party_type = models.CharField(max_length=32, choices=PartyType.choices)
    company_name = models.CharField(max_length=128)
    severity = models.CharField(max_length=64)
    notes = models.TextField(null=True, blank=True)
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_external_party_injury"
        ordering = ("incident_id", "id")
