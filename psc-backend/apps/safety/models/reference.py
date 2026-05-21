from __future__ import annotations

import uuid

from django.db import models


class MasterMscatTaxonomy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legacy_int_id = models.BigIntegerField(unique=True, editable=False)
    category_id = models.IntegerField()
    category_name = models.CharField(max_length=128)
    subcode_id = models.CharField(max_length=16, unique=True)
    subcode_description = models.TextField()
    cause_type = models.CharField(max_length=32)
    active = models.BooleanField(default=True)
    seeded_version = models.CharField(max_length=16, default="v1.0-Round21")
    schema_version = models.PositiveIntegerField(default=1)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "master_mscat_taxonomy"
        managed = False
        ordering = ("category_id", "subcode_id")


class MasterImmediateCause(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legacy_int_id = models.BigIntegerField(unique=True, editable=False)
    category_id = models.IntegerField()
    category_name = models.CharField(max_length=128)
    subcode_id = models.CharField(max_length=16)
    subcode_description = models.TextField()
    cause_type = models.CharField(max_length=32)
    active = models.BooleanField(default=True)
    seeded_version = models.CharField(max_length=16, default="v1.0")
    schema_version = models.PositiveIntegerField(default=1)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "master_immediate_causes"
        managed = False
        ordering = ("category_id", "subcode_id")


class MasterLossType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legacy_int_id = models.BigIntegerField(unique=True, editable=False)
    loss_type_id = models.IntegerField(unique=True)
    loss_type_name = models.CharField(max_length=64)
    description = models.CharField(max_length=128)
    active = models.BooleanField(default=True)
    seeded_version = models.CharField(max_length=16, default="v1.0")

    class Meta:
        db_table = "master_loss_types"
        managed = False
        ordering = ("loss_type_id",)


class MasterSoiArea(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legacy_int_id = models.BigIntegerField(unique=True, editable=False)
    area_id = models.IntegerField(unique=True)
    area_name = models.CharField(max_length=128)
    section_12_flag = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)
    seeded_version = models.CharField(
        max_length=128,
        default="v1.0 (SQE S 608 - SSQE Rev 02 baseline + Section 12)",
    )

    class Meta:
        db_table = "master_soi_area"
        managed = False
        ordering = ("display_order", "area_id")


class MasterSoiAreaItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legacy_int_id = models.BigIntegerField(unique=True, editable=False)
    area_id = models.IntegerField()
    area_name = models.CharField(max_length=128)
    subsection_id = models.IntegerField()
    subsection_name = models.CharField(max_length=128)
    item_number = models.CharField(max_length=16)
    description = models.TextField()
    tier = models.CharField(max_length=16)
    active = models.BooleanField(default=True)
    seeded_version = models.CharField(max_length=16, default="v1.0")
    schema_version = models.PositiveIntegerField(default=1)
    updated_by = models.CharField(max_length=128, null=True, blank=True)
    updated_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "master_soi_area_item"
        managed = False
        ordering = ("area_id", "subsection_id", "item_number", "id")


class MasterSafetyIncidentType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legacy_int_id = models.BigIntegerField(unique=True, editable=False)
    type_code = models.CharField(max_length=64, unique=True)
    type_name = models.CharField(max_length=128)
    imo_reportable = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_safety_incident_type"
        managed = False
        ordering = ("type_code",)


class MasterSafetyBiasGuard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legacy_int_id = models.BigIntegerField(unique=True, editable=False)
    guard_code = models.CharField(max_length=32, unique=True)
    guard_name = models.CharField(max_length=128)
    family = models.CharField(max_length=16)
    description = models.TextField()
    bit_position = models.PositiveSmallIntegerField()
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "master_safety_bias_guard"
        managed = False
        ordering = ("bit_position", "id")
