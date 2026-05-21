from __future__ import annotations

from rest_framework import serializers


class IncidentDraftSerializer(serializers.Serializer):
    draft_note = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
