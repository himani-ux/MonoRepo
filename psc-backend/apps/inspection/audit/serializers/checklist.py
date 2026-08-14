"""Serializers for Audit checklist master reads."""

from __future__ import annotations

from rest_framework import serializers

from apps.inspection.audit.services.checklist import AuditChecklistBundle


class AuditChecklistResponseSerializer(serializers.Serializer):
    def to_representation(self, instance: AuditChecklistBundle):
        checklist = instance.checklist
        return {
            "audit_id": str(instance.audit_detail.id),
            "selected": checklist is not None,
            "ship_type_filter": instance.ship_type_filter,
            "item_filter_applied": instance.item_filter_applied,
            "checklist": None
            if checklist is None
            else {
                "id": str(checklist.id),
                "checklist_code": checklist.checklist_code,
                "name": checklist.name,
                "auditee_type": checklist.auditee_type,
                "scope_dept": checklist.scope_dept,
                "ship_type_scope": checklist.ship_type_scope,
                "source_form_ref": checklist.source_form_ref,
                "code_version": checklist.code_version,
            },
            "items": [
                {
                    "id": str(item.id),
                    "location_code": item.location_code or "",
                    "item_code": item.item_code,
                    "question": item.question,
                    "guideline": item.guideline or "",
                    "regulation_ref": item.regulation_ref or "",
                    "ksm_sms_ref": item.ksm_sms_ref or "",
                    "ship_type": item.ship_type or "",
                    "sequence_no": item.sequence_no,
                }
                for item in instance.items
            ],
        }
