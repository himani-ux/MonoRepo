"""Serializers for the DPA scan-validation queue."""

from __future__ import annotations

from rest_framework import serializers

from apps.inspection.audit.models import AuditAttachment


ACCEPT_REASON_MIN_LENGTH = 50


class AuditScanValidationActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=("VALIDATE", "ACCEPT_WITH_REASON", "REJECT_RESCAN"))
    qr_payload = serializers.JSONField(required=False)
    reason = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)

    def validate(self, data):
        action = data["action"]
        reason = data.get("reason", "")
        if action == "ACCEPT_WITH_REASON" and len(reason.strip()) < ACCEPT_REASON_MIN_LENGTH:
            raise serializers.ValidationError(
                {"reason": f"Accept reason must be at least {ACCEPT_REASON_MIN_LENGTH} characters."}
            )
        return data


class AuditScanValidationQueueSerializer(serializers.Serializer):
    def to_representation(self, instance: AuditAttachment):
        return {
            "id": str(instance.id),
            "audit_detail_id": str(instance.audit_detail_id),
            "audit_finding_id": str(instance.audit_finding_id) if instance.audit_finding_id else None,
            "file_name": instance.file_name,
            "file_path": instance.file_path,
            "mime_type": instance.mime_type,
            "category": instance.category,
            "attachment_version": instance.attachment_version,
            "linked_pdf_generation_id": (
                str(instance.linked_pdf_generation_id) if instance.linked_pdf_generation_id else None
            ),
            "pdf_hash_validation_status": instance.pdf_hash_validation_status,
            "validated_at": instance.validated_at.isoformat() if instance.validated_at else None,
            "validator_message": instance.validator_message,
            "uploaded_by": instance.uploaded_by,
            "uploaded_at": instance.uploaded_at.isoformat() if instance.uploaded_at else None,
        }


__all__ = [
    "ACCEPT_REASON_MIN_LENGTH",
    "AuditScanValidationActionSerializer",
    "AuditScanValidationQueueSerializer",
]
