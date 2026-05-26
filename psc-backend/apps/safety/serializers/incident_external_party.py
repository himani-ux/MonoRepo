from __future__ import annotations

from rest_framework import serializers

from apps.safety.models import ExternalPartyInjury


class ExternalPartyInjurySerializer(serializers.ModelSerializer):
    incident_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = ExternalPartyInjury
        fields = (
            "id",
            "id",
            "incident_id",
            "party_name",
            "party_type",
            "company_name",
            "severity",
            "notes",
            "schema_version",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )
        read_only_fields = (
            "id",
            "id",
            "incident_id",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )

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
