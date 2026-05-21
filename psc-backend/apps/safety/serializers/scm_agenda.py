from __future__ import annotations

from rest_framework import serializers


class SCMAgendaActionItemWriteSerializer(serializers.Serializer):
    enabled = serializers.BooleanField(default=False)
    title = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    assigned_crew_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    assigned_office_user_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, attrs):
        enabled = bool(attrs.get("enabled", False))
        if not enabled:
            return attrs

        title = str(attrs.get("title", "") or "").strip()
        description = str(attrs.get("description", "") or "").strip()
        assigned_crew_id = str(attrs.get("assigned_crew_id", "") or "").strip()
        assigned_office_user_id = str(attrs.get("assigned_office_user_id", "") or "").strip()

        if len(title) < 5:
            raise serializers.ValidationError({"title": "Action-item title must be at least 5 characters."})
        if len(description) < 20:
            raise serializers.ValidationError(
                {"description": "Action-item description must be at least 20 characters."}
            )
        if not assigned_crew_id and not assigned_office_user_id:
            raise serializers.ValidationError(
                {"assigned_crew_id": "Action item requires a crew or office owner."}
            )
        if attrs.get("due_date") in (None, ""):
            raise serializers.ValidationError({"due_date": "Action item requires a due date."})

        attrs["title"] = title
        attrs["description"] = description
        attrs["assigned_crew_id"] = assigned_crew_id or None
        attrs["assigned_office_user_id"] = assigned_office_user_id or None
        return attrs


class SCMAgendaRowWriteSerializer(serializers.Serializer):
    agenda_item_number = serializers.IntegerField(min_value=1, max_value=10)
    content = serializers.CharField(required=False, allow_blank=True)
    decision = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    linked_finding_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )
    linked_incident_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )
    action_item = SCMAgendaActionItemWriteSerializer(required=False)

    def validate(self, attrs):
        content = attrs.get("content")
        if content is not None:
            content = str(content).strip()
            if content and len(content) < 20:
                raise serializers.ValidationError(
                    {"content": "SCM section free text must be at least 20 characters."}
                )
            attrs["content"] = content

        if "decision" in attrs:
            decision = attrs.get("decision")
            attrs["decision"] = None if decision in (None, "") else str(decision).strip()
        return attrs


class SCMAgendaUpdateSerializer(serializers.Serializer):
    rows = SCMAgendaRowWriteSerializer(many=True)

    def validate_rows(self, value):
        seen: set[int] = set()
        for row in value:
            agenda_item_number = int(row["agenda_item_number"])
            if agenda_item_number in seen:
                raise serializers.ValidationError("Agenda rows must be unique per section.")
            seen.add(agenda_item_number)
        return value
