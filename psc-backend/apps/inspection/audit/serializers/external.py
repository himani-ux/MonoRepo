"""Serializers for external-audit close-out APIs."""

from rest_framework import serializers


CERTIFICATE_IMPACTS = ("NONE", "CERT_VALID", "RENEWAL_AT_RISK", "SUSPENDED", "WITHDRAWN")


class ExternalAuditCloseoutSerializer(serializers.Serializer):
    certificate_impact = serializers.ChoiceField(choices=CERTIFICATE_IMPACTS)
    is_cycle_resetting = serializers.BooleanField(required=False, default=False)
    cycle_reset_reason = serializers.CharField(required=False, allow_blank=True)
    typed_cert_number = serializers.CharField(required=False, allow_blank=True)
    flag_notified_to = serializers.CharField(required=False, allow_blank=True, max_length=200)
    flag_notification_ref = serializers.CharField(required=False, allow_blank=True, max_length=200)


class ExternalCertLinkEditSerializer(serializers.Serializer):
    linked_cert_ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=True)
    reason = serializers.CharField()

