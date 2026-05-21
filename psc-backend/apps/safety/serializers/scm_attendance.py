from __future__ import annotations

from rest_framework import serializers

from apps.safety.models import SCMAttendance


class SCMAttendanceSerializer(serializers.ModelSerializer):
    wrh_flag = serializers.SerializerMethodField()

    class Meta:
        model = SCMAttendance
        fields = (
            "crew_id",
            "rank_name",
            "display_name",
            "present",
            "absence_reason",
            "wrh_data_available",
            "wrh_rest_hours_24h",
            "wrh_rest_hours_7d",
            "wrh_non_compliance_flag",
            "wrh_flag",
            "remarks",
            "schema_version",
        )

    def get_wrh_flag(self, obj: SCMAttendance) -> str:
        if not obj.wrh_data_available:
            return "RED"
        if obj.wrh_non_compliance_flag:
            return "YELLOW"
        return "GREEN"


class SCMAttendanceRowWriteSerializer(serializers.Serializer):
    crew_id = serializers.CharField()
    rank_name = serializers.CharField()
    display_name = serializers.CharField()
    present = serializers.BooleanField(required=False, default=True)
    absence_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    remarks = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    schema_version = serializers.IntegerField(required=False, default=1)

    def validate(self, attrs):
        attrs["crew_id"] = str(attrs["crew_id"]).strip()
        attrs["rank_name"] = str(attrs["rank_name"]).strip()
        attrs["display_name"] = str(attrs["display_name"]).strip()
        attrs["absence_reason"] = str(attrs.get("absence_reason") or "").strip() or None
        attrs["remarks"] = str(attrs.get("remarks") or "").strip() or None

        if not attrs["crew_id"]:
            raise serializers.ValidationError({"crew_id": "Attendance rows require a crew ID."})
        if not attrs["rank_name"]:
            raise serializers.ValidationError({"rank_name": "Attendance rows require a rank name."})
        if not attrs["display_name"]:
            raise serializers.ValidationError({"display_name": "Attendance rows require a display name."})
        if not attrs["present"] and not attrs["absence_reason"]:
            raise serializers.ValidationError(
                {"absence_reason": "Absent attendees require an absence reason."}
            )
        return attrs


class SCMAttendanceBulkWriteSerializer(serializers.Serializer):
    rows = SCMAttendanceRowWriteSerializer(many=True)
