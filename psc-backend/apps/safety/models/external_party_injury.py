from __future__ import annotations

from django.db import models

from .base import PublicIdMixin


class ExternalPartyInjury(PublicIdMixin):
    class InjuredPersonType(models.TextChoices):
        CREW = "CREW", "Crew"
        NON_CREW = "NON_CREW", "Non-crew"

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
    injured_person_type = models.CharField(
        max_length=16,
        choices=InjuredPersonType.choices,
        default=InjuredPersonType.NON_CREW,
    )
    party_name = models.CharField(max_length=128, blank=True)
    party_type = models.CharField(max_length=32, choices=PartyType.choices, blank=True)
    company_name = models.CharField(max_length=128, blank=True)
    severity = models.CharField(max_length=64, blank=True)
    crew_rank = models.CharField(max_length=128, null=True, blank=True)
    crew_age = models.PositiveSmallIntegerField(null=True, blank=True)
    crew_activity_type = models.CharField(max_length=128, null=True, blank=True)
    shore_assistance_required = models.BooleanField(null=True, blank=True)
    vessel_location = models.CharField(max_length=128, null=True, blank=True)
    onboard_location = models.CharField(max_length=128, null=True, blank=True)
    last_port = models.CharField(max_length=128, null=True, blank=True)
    departure_date = models.DateField(null=True, blank=True)
    vessel_condition = models.CharField(max_length=16, null=True, blank=True)
    what_happened_narrative = models.TextField(null=True, blank=True)
    nature_of_injury = models.CharField(max_length=255, null=True, blank=True)
    source_of_injury = models.CharField(max_length=255, null=True, blank=True)
    affected_body_areas = models.CharField(max_length=255, null=True, blank=True)
    first_aid_details = models.TextField(null=True, blank=True)
    why_it_happened_analysis = models.TextField(null=True, blank=True)
    regulation_or_procedure_breach = models.TextField(null=True, blank=True)
    risk_assessment_carried_out = models.CharField(max_length=8, null=True, blank=True)
    toolbox_meeting_carried_out = models.CharField(max_length=8, null=True, blank=True)
    prevention_action_taken_required = models.TextField(null=True, blank=True)
    ocimf_fatality = models.BooleanField(null=True, blank=True)
    ocimf_permanent_total_disability = models.BooleanField(null=True, blank=True)
    ocimf_permanent_partial_disability = models.BooleanField(null=True, blank=True)
    ocimf_lost_workday_case = models.BooleanField(null=True, blank=True)
    ocimf_restricted_workday_case = models.BooleanField(null=True, blank=True)
    ocimf_medical_treatment_case = models.BooleanField(null=True, blank=True)
    ocimf_first_aid_case = models.BooleanField(null=True, blank=True)
    cost_medicines_onboard = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_doctor_visits = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_repatriation = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_evacuation = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_off_hire = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_vessel_delays = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_man_hours_lost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_deviation = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_miscellaneous = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    miscellaneous_expenses_reason = models.TextField(null=True, blank=True)
    total_estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    schema_version = models.PositiveIntegerField(default=1)
    created_by = models.CharField(max_length=128)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_external_party_injury"
        ordering = ("incident_id", "id")
