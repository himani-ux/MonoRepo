from __future__ import annotations

import uuid

from django.db import models


class SafetyCaseStudy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legacy_int_id = models.BigIntegerField(unique=True, editable=False)
    slug = models.SlugField(max_length=64, unique=True)
    title = models.CharField(max_length=128)
    event_type = models.CharField(max_length=128)
    loss_summary = models.CharField(max_length=256)
    incident_date = models.DateField()
    immediate_cause_codes = models.CharField(max_length=128)
    basic_cause_codes = models.CharField(max_length=128)
    narrative = models.TextField()
    recommendations = models.TextField()
    source_label = models.CharField(max_length=128, default="DNV worked solution")
    active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_by = models.CharField(max_length=128, default="seed_case_studies")
    created_date = models.DateTimeField(null=True, blank=True)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "master_safety_case_study"
        managed = False
        ordering = ("display_order", "title")
