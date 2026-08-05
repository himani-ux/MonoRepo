from __future__ import annotations

from django.db import models

from .base import PublicIdMixin


class IncidentWeatherOption(PublicIdMixin):
    class FieldKey(models.TextChoices):
        VISIBILITY = "VISIBILITY", "Visibility"
        PRECIPITATION = "PRECIPITATION", "Precipitation"
        SEA_STATE = "SEA_STATE", "Sea State"
        WIND_SCALE = "WIND_SCALE", "Wind Scale"
        WIND_DIRECTION = "WIND_DIRECTION", "Wind Direction"
        LIGHTING_SOURCE = "LIGHTING_SOURCE", "Source of Lighting"
        CURRENT_DIRECTION = "CURRENT_DIRECTION", "Current Direction"
        ICE_CONDITION_ONBOARD = "ICE_CONDITION_ONBOARD", "Ice condition on-board"
        ICE_CONDITION_AT_SEA = "ICE_CONDITION_AT_SEA", "Ice condition at sea"
        LIGHT_CONDITION = "LIGHT_CONDITION", "Light condition"

    field_key = models.CharField(max_length=32, choices=FieldKey.choices, db_index=True)
    option_label = models.CharField(max_length=128)
    display_order = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=128, default="system")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_incident_weather_option"
        ordering = ("field_key", "display_order", "option_label")
        constraints = [
            models.UniqueConstraint(
                fields=("field_key", "option_label"),
                name="uq_inc_weather_option_field_label",
            ),
        ]
        indexes = [
            models.Index(fields=("active", "field_key", "display_order"), name="ix_inc_weather_option_lookup"),
        ]
