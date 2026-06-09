from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date

from rest_framework import serializers

from apps.safety.authentication.vessel_scope import user_has_vessel_access
from apps.safety.models import SCMMeeting
from apps.safety.serializers.scm_attendance import SCMAttendanceRowWriteSerializer
from apps.safety.serializers.vessel_display import VesselDisplayMixin


SCM_SECTION_TEMPLATE: tuple[dict[str, object], ...] = (
    {"agenda_item_number": 1, "section_label": "Structured Review", "auto_populated": False},
    {"agenda_item_number": 2, "section_label": "Quality and Safety Practice", "auto_populated": False},
    {"agenda_item_number": 3, "section_label": "Security", "auto_populated": False},
    {"agenda_item_number": 4, "section_label": "Environment", "auto_populated": False},
    {"agenda_item_number": 5, "section_label": "Health", "auto_populated": False},
    {"agenda_item_number": 6, "section_label": "Crew Welfare", "auto_populated": False},
    {"agenda_item_number": 7, "section_label": "PSC Findings & Corrective Measures", "auto_populated": False},
    {"agenda_item_number": 8, "section_label": "Minutes of Meeting", "auto_populated": False},
    {"agenda_item_number": 9, "section_label": "Office Review", "auto_populated": False},
)

SCM_LEGACY_FIELD_TEMPLATE: dict[int, tuple[dict[str, object], ...]] = {
    1: (
        {"field_key": "previous_minutes_reviewed", "field_label": "Minutes of previous safety committee reviewed?", "field_type": "BOOLEAN", "required": True},
        {"field_key": "company_topics_discussed", "field_label": "Topics recommended by company discussed?", "field_type": "BOOLEAN", "required": True},
        {"field_key": "deficiencies_discussed", "field_label": "Safety/Deficiencies discussed?", "field_type": "BOOLEAN", "required": True},
        {"field_key": "near_misses_discussed", "field_label": "All near misses discussed?", "field_type": "BOOLEAN", "required": True},
        {"field_key": "near_miss_discussion_status", "field_label": "Near miss discussion status", "field_type": "TEXT", "required": False},
        {"field_key": "near_miss_not_discussed_reason", "field_label": "Reason if near miss not discussed", "field_type": "TEXT", "required": False},
        {"field_key": "immediate_actions_discussed", "field_label": "Immediate actions discussed?", "field_type": "BOOLEAN", "required": True},
        {"field_key": "major_incidents_discussed", "field_label": "Major incidents discussed?", "field_type": "BOOLEAN", "required": True},
        {"field_key": "emergency_drills_discussed", "field_label": "Emergency drills discussed?", "field_type": "BOOLEAN", "required": True},
    ),
    2: (
        {"field_key": "permit_to_work_compliance", "field_label": "Compliance with PTW (Permit To Work)", "field_type": "BOOLEAN", "required": True},
        {"field_key": "checklist_system_compliance", "field_label": "Compliance with Checklist system", "field_type": "BOOLEAN", "required": True},
        {"field_key": "alcohol_policy", "field_label": "Compliance with Drug & Alcohol policy", "field_type": "BOOLEAN", "required": True},
        {"field_key": "risk_assessment_management", "field_label": "Compliance with Risk assessment", "field_type": "BOOLEAN", "required": True},
        {"field_key": "rest_hours", "field_label": "Compliance with Rest hours", "field_type": "BOOLEAN", "required": True},
        {"field_key": "marpol_procedure_compliance", "field_label": "Compliance with MARPOL procedure", "field_type": "BOOLEAN", "required": False},
        {"field_key": "circular_discussion_status", "field_label": "Circular / safety alert / work instruction discussion status", "field_type": "TEXT", "required": False},
        {"field_key": "circular_not_discussed_reason", "field_label": "Reason if not discussed", "field_type": "TEXT", "required": False},
        {"field_key": "best_practices", "field_label": "Best practice recommendations", "field_type": "TEXT", "required": False},
    ),
    3: (
        {"field_key": "immediate_security_concerns", "field_label": "Review of immediate security concerns", "field_type": "TEXT", "required": True},
        {"field_key": "security_best_practices", "field_label": "Best practices", "field_type": "TEXT", "required": False},
        {"field_key": "cyber_security_notes", "field_label": "Cyber security notes", "field_type": "TEXT", "required": False},
    ),
    4: (
        {"field_key": "environment_best_practices", "field_label": "Best practices", "field_type": "TEXT", "required": False},
    ),
    5: (
        {"field_key": "health_review", "field_label": "Health review", "field_type": "TEXT", "required": True},
        {"field_key": "medical_certificates_healthy", "field_label": "Validity of Medical certificates", "field_type": "BOOLEAN", "required": True},
        {"field_key": "weekly_master_inspection", "field_label": "Weekly inspection by Master", "field_type": "BOOLEAN", "required": True},
        {"field_key": "mess_committee_meeting", "field_label": "Mess committee meeting for quality", "field_type": "BOOLEAN", "required": True},
        {"field_key": "health_best_practices", "field_label": "Best practices", "field_type": "TEXT", "required": False},
    ),
    6: (
        {"field_key": "crew_complaint_received", "field_label": "Any complaints received from crew?", "field_type": "BOOLEAN", "required": True},
        {"field_key": "matter_status_resolved", "field_label": "Matter status resolved", "field_type": "BOOLEAN", "required": False},
        {"field_key": "complaint_form_submitted", "field_label": "Scan copy of complaint form submitted to office", "field_type": "BOOLEAN", "required": False},
        {"field_key": "crew_best_practices", "field_label": "Best practices", "field_type": "TEXT", "required": False},
    ),
    7: tuple(
        [
            {
                "field_key": f"findings{index}",
                "field_label": f"Findings {index}",
                "field_type": "TEXT",
                "required": index == 1,
            }
            for index in range(1, 11)
        ]
        + [
            {
                "field_key": f"correctivemeasure{index}",
                "field_label": f"Corrective Measure {index}",
                "field_type": "TEXT",
                "required": index == 1,
            }
            for index in range(1, 11)
        ]
    ),
    8: (
        {"field_key": "miscellaneous_comments", "field_label": "Comments", "field_type": "TEXT", "required": True},
    ),
    9: (
        {"field_key": "officecomments", "field_label": "OFFICECOMMENTS", "field_type": "TEXT", "required": False, "office_only": True},
        {"field_key": "isreviewed", "field_label": "IsReviewed", "field_type": "BOOLEAN", "required": False, "office_only": True},
    ),
}


def _blank_legacy_fields(section_number: int) -> dict[str, object]:
    return {str(field["field_key"]): None for field in SCM_LEGACY_FIELD_TEMPLATE.get(section_number, ())}


def _legacy_field_meta(section_number: int) -> list[dict[str, object]]:
    return [dict(field) for field in SCM_LEGACY_FIELD_TEMPLATE.get(section_number, ())]


def _coerce_bool(value: object) -> bool | str | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"na", "n/a", "not applicable", "not_applicable"}:
        return "N/A"
    return normalized in {"1", "true", "yes", "y"}


def _coerce_legacy_value(value: object, field_type: str) -> object:
    if value in (None, ""):
        return None
    if field_type == "BOOLEAN":
        return _coerce_bool(value)
    if field_type == "INTEGER":
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return str(value).strip()


def legacy_value_for_storage(value: object, field_type: str) -> str | None:
    normalized = _coerce_legacy_value(value, field_type)
    if normalized is None:
        return None
    if field_type == "BOOLEAN":
        if normalized == "N/A":
            return "N/A"
        return "true" if normalized else "false"
    return str(normalized)


def normalize_legacy_fields(section_number: int, value: object) -> dict[str, object]:
    if isinstance(value, list):
        value = {
            str(row.get("field_key")): row.get("field_value")
            for row in value
            if isinstance(row, Mapping) and row.get("field_key")
        }
    if not isinstance(value, Mapping):
        value = {}

    normalized: dict[str, object] = {}
    for field in SCM_LEGACY_FIELD_TEMPLATE.get(section_number, ()):
        field_key = str(field["field_key"])
        normalized[field_key] = _coerce_legacy_value(value.get(field_key), str(field["field_type"]))
    return normalized


def build_legacy_section_content(section_number: int, fields: Mapping[str, object]) -> str:
    parts: list[str] = []
    for field in SCM_LEGACY_FIELD_TEMPLATE.get(section_number, ()):
        field_key = str(field["field_key"])
        value = fields.get(field_key)
        if value in (None, ""):
            continue
        if field["field_type"] == "BOOLEAN":
            value = "N/A" if value == "N/A" else ("Yes" if value is True else "No")
        parts.append(f"{field['field_label']}: {value}")
    return "\n".join(parts)


def validate_required_legacy_fields(sections: Iterable[Mapping[str, object]]) -> list[str]:
    errors: list[str] = []
    for section in sections:
        try:
            section_number = int(section.get("agenda_item_number"))
        except (TypeError, ValueError):
            continue
        if section_number == 9:
            continue
        legacy_fields = section.get("legacy_fields")
        if not isinstance(legacy_fields, Mapping):
            legacy_fields = {}
        for field in SCM_LEGACY_FIELD_TEMPLATE.get(section_number, ()):
            if not field.get("required"):
                continue
            value = legacy_fields.get(str(field["field_key"]))
            if value in (None, ""):
                errors.append(f"Section {section_number} requires {field['field_label']}.")
    return errors


def build_default_scm_sections() -> list[dict[str, object]]:
    return [
        {
            **template_row,
            "content": "",
            "decision": None,
            "legacy_field_meta": _legacy_field_meta(int(template_row["agenda_item_number"])),
            "legacy_fields": _blank_legacy_fields(int(template_row["agenda_item_number"])),
            "schema_version": 1,
        }
        for template_row in SCM_SECTION_TEMPLATE
    ]


def normalize_scm_sections(value: object) -> list[dict[str, object]]:
    template_map = {
        int(section["agenda_item_number"]): section
        for section in build_default_scm_sections()
    }
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, dict)):
        return list(template_map.values())

    provided_map: dict[int, dict[str, object]] = {}
    for row in value:
        if not isinstance(row, dict):
            continue
        agenda_item_number = row.get("agenda_item_number")
        try:
            agenda_item_number = int(agenda_item_number)
        except (TypeError, ValueError):
            continue
        if agenda_item_number not in template_map:
            continue
        base_row = dict(template_map[agenda_item_number])
        legacy_fields = normalize_legacy_fields(agenda_item_number, row.get("legacy_fields"))
        base_row["legacy_fields"] = legacy_fields
        base_row["content"] = str(row.get("content", "") or "") or build_legacy_section_content(
            agenda_item_number,
            legacy_fields,
        )
        base_row["decision"] = row.get("decision")
        provided_map[agenda_item_number] = base_row

    return [
        provided_map.get(section_number, dict(template_row))
        for section_number, template_row in sorted(template_map.items())
    ]


def _select_display_section_row(
    agenda_map: Mapping[int, object],
    *,
    section_number: int,
    legacy_source_number: int,
) -> object | None:
    current_row = agenda_map.get(section_number)
    legacy_row = agenda_map.get(legacy_source_number)
    if current_row is None:
        return legacy_row
    current_label = str(getattr(current_row, "section_label", "") or "").strip().lower()
    if section_number == 2 and current_label == "reserved":
        return legacy_row or current_row
    return current_row


def _has_nonblank_legacy_values(values: Mapping[str, object]) -> bool:
    return any(value not in (None, "") and str(value).strip() for value in values.values())


class SCMSectionSerializer(serializers.Serializer):
    agenda_item_number = serializers.IntegerField(min_value=1, max_value=9)
    section_label = serializers.CharField(required=False)
    auto_populated = serializers.BooleanField(required=False, default=False)
    content = serializers.CharField(allow_blank=True, required=False)
    decision = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    legacy_fields = serializers.DictField(required=False)
    schema_version = serializers.IntegerField(required=False, default=1)

    def validate(self, attrs):
        template_row = next(
            (
                row
                for row in SCM_SECTION_TEMPLATE
                if int(row["agenda_item_number"]) == attrs["agenda_item_number"]
            ),
            None,
        )
        if template_row is None:
            raise serializers.ValidationError("Unknown SCM section.")

        section_label = attrs.get("section_label")
        if section_label not in (None, "", template_row["section_label"]):
            raise serializers.ValidationError(
                {"section_label": "SCM sections must follow the locked legacy order."}
            )

        attrs["section_label"] = str(template_row["section_label"])
        attrs["auto_populated"] = bool(template_row["auto_populated"])
        attrs["legacy_fields"] = normalize_legacy_fields(
            attrs["agenda_item_number"],
            attrs.get("legacy_fields"),
        )

        content = str(attrs.get("content", "") or "").strip()
        if content and len(content) < 20:
            raise serializers.ValidationError(
                {"content": "SCM section free text must be at least 20 characters."}
            )
        return attrs


class SCMMeetingSerializer(VesselDisplayMixin, serializers.ModelSerializer):
    cadence_warning = serializers.SerializerMethodField()
    occasion = serializers.SerializerMethodField()
    ship_position = serializers.SerializerMethodField()
    ship_pos_from = serializers.SerializerMethodField()
    ship_pos_to = serializers.SerializerMethodField()
    comm_time = serializers.SerializerMethodField()
    comp_time = serializers.SerializerMethodField()
    is_reviewed = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    vessel_code = serializers.SerializerMethodField()
    vessel_name = serializers.SerializerMethodField()
    vessel_display_name = serializers.SerializerMethodField()

    class Meta:
        model = SCMMeeting
        fields = (
            "id",
            "id",
            "vessel_id",
            "vessel_code",
            "vessel_name",
            "vessel_display_name",
            "scm_number",
            "meeting_type",
            "meeting_date",
            "meeting_time_local",
            "location",
            "latitude",
            "longitude",
            "voyage_no",
            "occasion",
            "ship_position",
            "ship_pos_from",
            "ship_pos_to",
            "comm_time",
            "comp_time",
            "chair_crew_id",
            "prepared_by_crew_id",
            "ad_hoc_trigger_reason",
            "state",
            "cadence_warning",
            "sections",
            "master_signed_off_at",
            "master_signed_off_by",
            "attendance_warnings_acknowledged_at",
            "attendance_warnings_acknowledged_by",
            "office_comment",
            "office_comment_by",
            "office_comment_at",
            "is_reviewed",
            "schema_version",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )

    def get_cadence_warning(self, obj: SCMMeeting):
        repository = self.context.get("scm_repository")
        if repository is None:
            return None
        meeting_date = obj.meeting_date
        if isinstance(meeting_date, date):
            return repository.build_cadence_warning(
                vessel_id=str(obj.vessel_id),
                meeting_date=meeting_date,
            )
        return repository.build_cadence_warning(vessel_id=str(obj.vessel_id))

    def get_sections(self, obj: SCMMeeting) -> list[dict[str, object]]:
        agenda_rows = getattr(obj, "_agenda_rows", None)
        if agenda_rows is None:
            repository = self.context.get("scm_repository")
            if repository is None:
                return build_default_scm_sections()
            agenda_rows = list(repository.list_sections(obj.id))

        if not agenda_rows:
            return build_default_scm_sections()

        legacy_fields = getattr(obj, "_legacy_fields", None)
        if legacy_fields is None and (repository := self.context.get("scm_repository")) is not None:
            legacy_fields = list(repository.list_legacy_fields(obj.id))
        legacy_map: dict[int, dict[str, object]] = {}
        for field in legacy_fields or []:
            section_number = int(field.agenda_item_number)
            field_type = str(field.field_type)
            legacy_map.setdefault(section_number, {})[field.field_key] = _coerce_legacy_value(
                field.field_value,
                field_type,
            )

        agenda_map = {int(row.agenda_item_number): row for row in agenda_rows}
        legacy_source_map = {1: 1, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 10}
        rows = []
        for template_row in build_default_scm_sections():
            section_number = int(template_row["agenda_item_number"])
            legacy_source_number = legacy_source_map.get(section_number, section_number)
            row = _select_display_section_row(
                agenda_map,
                section_number=section_number,
                legacy_source_number=legacy_source_number,
            )
            current_legacy_fields = legacy_map.get(section_number, {})
            legacy_source_fields = legacy_map.get(legacy_source_number, {})
            selected_legacy_fields = (
                current_legacy_fields
                if _has_nonblank_legacy_values(current_legacy_fields)
                else legacy_source_fields
            )
            rows.append(
                {
                    "agenda_item_number": section_number,
                    "section_label": str(template_row["section_label"]),
                    "auto_populated": bool(getattr(row, "auto_populated", template_row.get("auto_populated", False))) if row is not None else bool(template_row.get("auto_populated", False)),
                    "content": getattr(row, "content", None) if row is not None else "",
                    "decision": getattr(row, "decision", None) if row is not None else None,
                    "legacy_field_meta": _legacy_field_meta(section_number),
                    "legacy_fields": {
                        **_blank_legacy_fields(section_number),
                        **selected_legacy_fields,
                    },
                    "schema_version": getattr(row, "schema_version", 1) if row is not None else 1,
                }
            )
        return rows

    def get_is_reviewed(self, obj: SCMMeeting) -> bool:
        return obj.office_comment_at is not None

    def get_occasion(self, obj: SCMMeeting) -> str:
        return str(obj.__dict__.get("occasion") or "M")

    def get_ship_position(self, obj: SCMMeeting) -> str:
        return str(obj.__dict__.get("ship_position") or "P")

    def get_ship_pos_from(self, obj: SCMMeeting) -> str | None:
        return obj.__dict__.get("ship_pos_from")

    def get_ship_pos_to(self, obj: SCMMeeting) -> str | None:
        return obj.__dict__.get("ship_pos_to")

    def get_comm_time(self, obj: SCMMeeting) -> str | None:
        value = obj.__dict__.get("comm_time")
        return str(value) if value not in (None, "") else None

    def get_comp_time(self, obj: SCMMeeting) -> str | None:
        value = obj.__dict__.get("comp_time")
        return str(value) if value not in (None, "") else None


class SCMMeetingDetailSerializer(SCMMeetingSerializer):
    def get_cadence_warning(self, obj: SCMMeeting):
        return None

    def get_sections(self, obj: SCMMeeting) -> list[dict[str, object]]:
        return []


class SCMMeetingListSerializer(VesselDisplayMixin, serializers.ModelSerializer):
    cadence_warning = serializers.SerializerMethodField()
    section_count = serializers.IntegerField(read_only=True)
    sections = serializers.SerializerMethodField()
    vessel_code = serializers.SerializerMethodField()
    vessel_name = serializers.SerializerMethodField()
    vessel_display_name = serializers.SerializerMethodField()

    class Meta:
        model = SCMMeeting
        fields = (
            "id",
            "vessel_id",
            "vessel_code",
            "vessel_name",
            "vessel_display_name",
            "scm_number",
            "meeting_type",
            "meeting_date",
            "chair_crew_id",
            "state",
            "cadence_warning",
            "sections",
            "section_count",
            "master_signed_off_at",
            "office_comment_at",
            "created_date",
            "updated_date",
        )

    def get_cadence_warning(self, obj: SCMMeeting):
        meeting_date = obj.meeting_date
        if obj.meeting_type != SCMMeeting.MeetingType.REGULAR or not isinstance(meeting_date, date):
            return None
        return getattr(obj, "_cadence_warning", None)

    def get_sections(self, obj: SCMMeeting) -> list[dict[str, object]]:
        count = int(getattr(obj, "section_count", 0) or 0)
        return [{} for _ in range(count)]


class SCMMeetingCreateSerializer(serializers.ModelSerializer):
    attendance_rows = SCMAttendanceRowWriteSerializer(many=True, required=False)
    sections = SCMSectionSerializer(many=True, required=False)
    ad_hoc_trigger_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    vessel_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    _NULL_DECIMAL_VALUES = {"", "null", "none", "undefined"}

    class Meta:
        model = SCMMeeting
        fields = (
            "id",
            "id",
            "vessel_id",
            "vessel_code",
            "meeting_type",
            "meeting_date",
            "meeting_time_local",
            "location",
            "latitude",
            "longitude",
            "voyage_no",
            "occasion",
            "ship_position",
            "ship_pos_from",
            "ship_pos_to",
            "comm_time",
            "comp_time",
            "chair_crew_id",
            "prepared_by_crew_id",
            "ad_hoc_trigger_reason",
            "attendance_rows",
            "sections",
            "schema_version",
        )
        extra_kwargs = {
            "meeting_type": {"required": False},
            "chair_crew_id": {"required": False},
            "prepared_by_crew_id": {"required": False},
            "schema_version": {"required": False},
            "occasion": {"required": False},
            "ship_position": {"required": False},
            "comm_time": {"required": False},
            "comp_time": {"required": False},
        }

    def to_internal_value(self, data):
        if hasattr(data, "copy"):
            data = data.copy()
            for field_name in ("latitude", "longitude"):
                value = data.get(field_name)
                if isinstance(value, str) and value.strip().lower() in self._NULL_DECIMAL_VALUES:
                    data[field_name] = None
        return super().to_internal_value(data)

    def validate(self, attrs):
        meeting_type = str(attrs.get("meeting_type") or SCMMeeting.MeetingType.REGULAR).strip().upper()
        if meeting_type not in {SCMMeeting.MeetingType.REGULAR, SCMMeeting.MeetingType.AD_HOC}:
            raise serializers.ValidationError({"meeting_type": "Unknown SCM meeting type."})

        attrs["meeting_type"] = meeting_type
        trigger_reason = str(attrs.get("ad_hoc_trigger_reason") or "").strip()
        if meeting_type == SCMMeeting.MeetingType.AD_HOC:
            if not trigger_reason:
                raise serializers.ValidationError(
                    {"ad_hoc_trigger_reason": "Ad-Hoc SCM requires a trigger reason."}
                )
            attrs["ad_hoc_trigger_reason"] = trigger_reason
        else:
            attrs["ad_hoc_trigger_reason"] = None

        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user_has_vessel_access(user, attrs.get("vessel_id")):
            raise serializers.ValidationError({"vessel_id": "You are not assigned to this vessel."})

        location = str(attrs.get("location") or "").strip()
        latitude = attrs.get("latitude")
        longitude = attrs.get("longitude")
        if not location and (latitude is None or longitude is None):
            raise serializers.ValidationError(
                {"location": "SCM requires a location or at-sea latitude and longitude."}
            )
        attrs["location"] = location or None
        attrs["occasion"] = str(attrs.get("occasion") or "M").strip().upper() or "M"
        ship_position = str(attrs.get("ship_position") or ("S" if not location else "P")).strip().upper()
        if ship_position not in {"S", "P"}:
            raise serializers.ValidationError({"ship_position": "ShipPosition must be S or P."})
        attrs["ship_position"] = ship_position
        if attrs.get("comm_time") is None:
            attrs["comm_time"] = attrs.get("meeting_time_local")
        if attrs.get("meeting_time_local") is None and attrs.get("comm_time") is not None:
            attrs["meeting_time_local"] = attrs["comm_time"]

        attrs["sections"] = normalize_scm_sections(attrs.get("sections"))
        return attrs

    def create(self, validated_data):
        repository = self.context["scm_repository"]
        attendance_rows = validated_data.pop("attendance_rows", None)
        sections = validated_data.pop("sections", None)
        payload = dict(validated_data)
        if attendance_rows is not None:
            payload["attendance_rows"] = attendance_rows
        if sections is not None:
            payload["sections"] = sections
        return repository.create(payload)

    def update(self, instance, validated_data):
        repository = self.context["scm_repository"]
        request = self.context.get("request")
        actor_id = "system"
        user = getattr(request, "user", None)
        if user is not None:
            for attr_name in ("username", "employee_id", "crew_id", "user_id", "id"):
                value = getattr(user, attr_name, None)
                if value not in (None, ""):
                    actor_id = str(value)
                    break
        return repository.update_meeting(
            meeting=instance,
            payload=validated_data,
            actor_id=actor_id,
        )


class SCMSignOffSerializer(serializers.Serializer):
    typed_name = serializers.CharField()
    device_fingerprint = serializers.CharField()


class SCMSubmitSerializer(serializers.Serializer):
    typed_name = serializers.CharField(required=False, allow_blank=True)
    device_fingerprint = serializers.CharField(required=False, allow_blank=True)


class SCMAttendanceAcknowledgementSerializer(serializers.Serializer):
    acknowledged = serializers.BooleanField()


class SCMSignatureSerializer(serializers.Serializer):
    signer_role = serializers.ChoiceField(choices=("CO", "ATTENDEE"))
    signer_crew_id = serializers.CharField()
    typed_name = serializers.CharField()
    device_fingerprint = serializers.CharField()


class SCMOfficeCommentSerializer(serializers.Serializer):
    office_comment = serializers.CharField(allow_blank=False)
    is_reviewed = serializers.BooleanField(required=False, default=True)
