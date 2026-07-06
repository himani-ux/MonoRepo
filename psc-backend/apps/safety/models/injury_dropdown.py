from __future__ import annotations

from django.db import models

from .base import PublicIdMixin


class InjuryDropdownOption(PublicIdMixin):
    class FieldKey(models.TextChoices):
        NATURE_OF_INJURY = "NATURE_OF_INJURY", "Nature of Injury"
        SOURCE_OF_INJURY = "SOURCE_OF_INJURY", "Source of Injury"
        AFFECTED_BODY_AREA = "AFFECTED_BODY_AREA", "Affected Areas of the Body"
        TYPE_OF_ACTIVITY = "TYPE_OF_ACTIVITY", "Type of Activity"
        SAFE_WORKING_PRACTICE = "SAFE_WORKING_PRACTICE", "Code of Safe Working Practices"

    field_key = models.CharField(max_length=32, choices=FieldKey.choices, db_index=True)
    option_label = models.CharField(max_length=255)
    display_order = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=128, default="system")
    created_date = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "vims_safety_injury_dropdown_option"
        ordering = ("field_key", "display_order", "option_label")
        constraints = [
            models.UniqueConstraint(
                fields=("field_key", "option_label"),
                name="uq_injury_dropdown_field_label",
            ),
        ]
        indexes = [
            models.Index(fields=("active", "field_key", "display_order"), name="ix_injury_dropdown_lookup"),
        ]
