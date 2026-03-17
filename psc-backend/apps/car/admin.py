"""Django admin registration for CAR module."""

from django.contrib import admin

from .models import (
    CorrectiveAction,
    Evidence,
    CarClcMapping,
    ActivityHistory,
    AuditLog,
    PhysicalVerification,
)


@admin.register(CorrectiveAction)
class CorrectiveActionAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'action_type', 'is_completed', 'due_date')
    list_filter = ('action_type', 'is_completed')


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'evidence_type', 'file_name', 'uploaded_at')
    list_filter = ('evidence_type',)


@admin.register(CarClcMapping)
class CarClcMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'clc_item_id')


@admin.register(ActivityHistory)
class ActivityHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'entity_type', 'event_type', 'performed_by', 'performed_at')
    list_filter = ('entity_type', 'event_type')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'entity_type', 'action', 'field_name', 'performed_by', 'performed_at')
    list_filter = ('entity_type', 'action')


@admin.register(PhysicalVerification)
class PhysicalVerificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'status', 'scheduled_date', 'visit_date')
    list_filter = ('status',)
