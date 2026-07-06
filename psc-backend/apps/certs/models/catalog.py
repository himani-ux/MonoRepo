from __future__ import annotations

from django.db import models


class CatalogSection(models.Model):
    section_id = models.IntegerField(primary_key=True)
    section_code = models.CharField(max_length=32, unique=True)
    display_name = models.CharField(max_length=128)
    sort_order = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField()
    created_by = models.CharField(max_length=64)

    class Meta:
        db_table = "vims_certs_catalog_section"
        managed = False
        ordering = ("sort_order", "section_id")


class CatalogRow(models.Model):
    catalog_id = models.UUIDField(primary_key=True, editable=False)
    canonical_code = models.CharField(max_length=64, unique=True)
    section = models.ForeignKey(CatalogSection, db_column="section_id", on_delete=models.DO_NOTHING)
    display_name = models.CharField(max_length=256)
    short_name = models.CharField(max_length=64, null=True, blank=True)
    print_section_label = models.CharField(max_length=128)
    validity_type = models.CharField(max_length=16)
    cadence_months = models.SmallIntegerField(null=True, blank=True)
    cadence_custom_days = models.IntegerField(null=True, blank=True)
    issuing_authority_type = models.CharField(max_length=16)
    is_class_tracked = models.BooleanField(default=False)
    submission_scope = models.CharField(max_length=32)
    parent = models.ForeignKey("self", db_column="parent_id", null=True, blank=True, on_delete=models.DO_NOTHING)
    relationship_type_default = models.CharField(max_length=32, null=True, blank=True)
    applicable_ship_types = models.CharField(max_length=256, default='["all"]')
    mandatory_for_all_vessels = models.BooleanField(default=True)
    applicability_mode = models.CharField(max_length=24, default="all_matching_type")
    specific_vessel_ids = models.TextField(null=True, blank=True)
    parent_supports_dynamic_children = models.BooleanField(default=False)
    age_gate_max_years = models.SmallIntegerField(null=True, blank=True)
    retain_all_versions = models.BooleanField(default=False)
    linked_pms_component_id = models.CharField(max_length=64, null=True, blank=True)
    alert_lead_overrides = models.TextField(null=True, blank=True)
    regulatory_anchor = models.CharField(max_length=256, null=True, blank=True)
    legacy_remarks = models.TextField(null=True, blank=True)
    print_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField()
    created_by = models.CharField(max_length=64)
    updated_at = models.DateTimeField()
    updated_by = models.CharField(max_length=64)

    class Meta:
        db_table = "vims_certs_catalog_row"
        managed = False
        ordering = ("section__sort_order", "print_order", "display_name")
