from __future__ import annotations

from rest_framework import serializers


class IncidentReopenSerializer(serializers.Serializer):
    reason = serializers.CharField(allow_blank=False, trim_whitespace=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        for forbidden_key in attrs:
            key = forbidden_key.lower()
            if "acting" in key or "deputy" in key:
                raise serializers.ValidationError(
                    {
                        forbidden_key: (
                            "Acting-role / deputy-chain concepts not supported "
                            "(D-GAP-A3 / A4)."
                        )
                    }
                )
        return attrs
