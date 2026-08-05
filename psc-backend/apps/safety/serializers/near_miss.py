from __future__ import annotations

import json

from django.utils import timezone
from rest_framework import serializers

from apps.safety.authentication.anonymity import AnonymityMixin
from apps.safety.authentication.vessel_scope import user_has_vessel_access
from apps.safety.models import (
    Incident,
    IncidentPhaseLog,
    NearMissCauseOption,
    NearMissCategory,
    MasterLossType,
    MasterMscatTaxonomy,
    MasterSafetyIncidentType,
    NearMissGuidancePrompt,
    NearMissKpiTarget,
    SafetyFieldHistory,
)
from apps.safety.identifiers import is_uuid_identifier
from apps.safety.serializers.vessel_display import VesselDisplayMixin
from apps.safety.services.field_history_recorder import parse_history_value


def _is_vessel_user(user) -> bool:
    if user is None:
        return False
    user_type = str(getattr(user, "user_type", "") or "").strip().upper()
    if user_type == "VESSEL":
        return True
    work_side = getattr(user, "work_side", None)
    return work_side in (1, True, "1", "SHIP", "VESSEL")


LEGACY_SHELL_TAGS = {"Software", "Hardware", "Environment", "Liveware", "Liveware-Liveware"}
NEAR_MISS_OTHER_CATEGORY = "Other"
NEAR_MISS_OTHER_PREFIX = "Other:"
NEAR_MISS_OTHER_SPECIFY_MAX_LENGTH = 200

NEAR_MISS_PLACES = {
    "AT_ANCHOR",
    "AT_SEA",
    "AT_PORT",
}


def resolve_near_miss_category(value: object) -> str | None:
    normalized = str(value or "").strip()
    if not normalized:
        return None
    if normalized.startswith(NEAR_MISS_OTHER_PREFIX):
        specified = normalized[len(NEAR_MISS_OTHER_PREFIX):].strip()
        if len(specified) > NEAR_MISS_OTHER_SPECIFY_MAX_LENGTH:
            return None
        if specified and NearMissCategory.objects.filter(category_name__iexact=NEAR_MISS_OTHER_CATEGORY, active=True).exists():
            return f"{NEAR_MISS_OTHER_PREFIX} {specified}"
    category = NearMissCategory.objects.filter(category_name__iexact=normalized, active=True).first()
    return category.category_name if category is not None else None


class NearMissJsonListField(serializers.ListField):
    def to_representation(self, value):
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return value
        try:
            parsed = json.loads(value)
        except (TypeError, ValueError):
            return []
        return parsed if isinstance(parsed, list) else []


def _json_dump_list(values: list[object]) -> str:
    return json.dumps(values, separators=(",", ":"))


class NearMissSerializer(AnonymityMixin, VesselDisplayMixin, serializers.ModelSerializer):
    near_miss_category_tags = NearMissJsonListField(child=serializers.CharField(), required=False)
    near_miss_incident_type_ids = NearMissJsonListField(child=serializers.CharField(), required=False)
    near_miss_mscat_subcode_ids = NearMissJsonListField(child=serializers.CharField(), required=False)
    near_miss_factor_causes = NearMissJsonListField(child=serializers.DictField(), required=False)
    vessel_code = serializers.SerializerMethodField()
    vessel_name = serializers.SerializerMethodField()
    vessel_display_name = serializers.SerializerMethodField()
    rework_summary = serializers.SerializerMethodField()
    vessel_review_summary = serializers.SerializerMethodField()
    evidence_attachments = serializers.SerializerMethodField()
    reporter_user_id = serializers.CharField(
        source="reporter_id",
        allow_null=True,
        required=False,
    )

    class Meta:
        model = Incident
        fields = (
            "id",
            "id",
            "incident_number",
            "vessel_id",
            "vessel_code",
            "vessel_name",
            "vessel_display_name",
            "record_type",
            "state",
            "current_phase",
            "occurred_at",
            "reported_at",
            "incident_type_id",
            "loss_type_primary_id",
            "narrative",
            "near_miss_priority",
            "near_miss_severity",
            "near_miss_place",
            "near_miss_shell_tag",
            "near_miss_category_tags",
            "near_miss_incident_type_ids",
            "near_miss_mscat_category_id",
            "near_miss_mscat_subcode_id",
            "near_miss_mscat_subcode_ids",
            "near_miss_factor_causes",
            "near_miss_immediate_action",
            "near_miss_suggestion",
            "near_miss_root_cause_detail",
            "near_miss_corrective_action",
            "near_miss_weather_voyage_details",
            "near_miss_equipment_details",
            "near_miss_lessons_learned",
            "reporter_user_id",
            "reporter_name",
            "reporter_rank",
            "reporter_email",
            "reporter_department",
            "reporter_device_fingerprint",
            "schema_version",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
            "rework_summary",
            "vessel_review_summary",
            "evidence_attachments",
        )
        read_only_fields = (
            "id",
            "incident_number",
            "record_type",
            "state",
            "current_phase",
            "created_date",
            "updated_date",
        )

    def get_rework_summary(self, obj: Incident) -> dict[str, object] | None:
        phase_log = (
            IncidentPhaseLog.objects.filter(
                incident=obj,
                transition_type=IncidentPhaseLog.TransitionType.REWORK,
            )
            .order_by("-occurred_at", "-id")
            .first()
        )
        if phase_log is None:
            return None
        comment = str(phase_log.loop_back_reason or "").strip()
        if not comment:
            return None
        return {
            "comment": comment,
            "requested_at": phase_log.occurred_at,
            "requested_by": phase_log.actor_user_id,
            "requested_by_role": phase_log.actor_role_code,
        }

    def get_vessel_review_summary(self, obj: Incident) -> dict[str, object] | None:
        history_row = (
            SafetyFieldHistory.objects.filter(
                parent_table=obj._meta.db_table,
                parent_id=obj.pk,
                field_name="near_miss_vessel_review_signature",
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if history_row is None:
            return None

        comment = str(history_row.change_reason or "").strip()
        payload = parse_history_value(history_row.new_value)
        if not isinstance(payload, dict):
            payload = {}
        decision = str(payload.get("decision") or "").strip()
        fallback = f"Near-miss vessel review decision: {decision}.".strip()
        if not comment or comment == fallback:
            return None

        return {
            "comment": comment,
            "decision": decision or None,
            "reviewed_at": payload.get("signed_at") or history_row.changed_at,
            "reviewed_by": payload.get("signed_by") or history_row.actor_user_id,
            "reviewed_by_role": payload.get("signed_role") or history_row.actor_role_code,
            "typed_name": payload.get("typed_name"),
        }

    def get_evidence_attachments(self, obj: Incident) -> list[dict[str, object]]:
        attachments: list[dict[str, object]] = []
        for evidence in obj.evidence_items.order_by("id"):
            metadata = evidence.metadata_json or {}
            attachment_path = str(metadata.get("attachment_path") or "").strip()
            content_type = str(metadata.get("content_type") or "").strip()
            if not attachment_path or not content_type.startswith("image/"):
                continue
            attachments.append(
                {
                    "id": str(evidence.id),
                    "title": evidence.title or "Near miss image",
                    "description": evidence.description or "",
                    "file_name": metadata.get("original_name") or metadata.get("file_name") or "near-miss-image",
                    "content_type": content_type,
                    "byte_size": metadata.get("byte_size"),
                    "uploaded_at": metadata.get("uploaded_at") or metadata.get("recorded_at"),
                    "high_severity_required": bool(metadata.get("high_severity_required")),
                    "preview_url": f"/api/safety/near-miss/{obj.id}/analysis/evidence/{evidence.id}/photo/",
                }
            )
        return attachments


class NearMissListSerializer(NearMissSerializer):
    class Meta(NearMissSerializer.Meta):
        fields = (
            "id",
            "id",
            "incident_number",
            "vessel_id",
            "vessel_code",
            "vessel_name",
            "vessel_display_name",
            "record_type",
            "state",
            "occurred_at",
            "reported_at",
            "incident_type_id",
            "loss_type_primary_id",
            "near_miss_priority",
            "near_miss_severity",
            "reporter_name",
            "schema_version",
        )


class NearMissCreateSerializer(NearMissSerializer):
    incident_type_id = serializers.CharField(required=True, allow_blank=False, allow_null=False)
    vessel_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta(NearMissSerializer.Meta):
        fields = NearMissSerializer.Meta.fields
        read_only_fields = tuple(
            field_name
            for field_name in NearMissSerializer.Meta.read_only_fields + ("near_miss_priority",)
            if field_name != "vessel_code"
        )
        extra_kwargs = {
            "schema_version": {"required": False},
            "record_type": {"required": False},
            "state": {"required": False},
            "current_phase": {"required": False},
            "created_by": {"required": False},
            "updated_by": {"required": False},
            "reported_at": {"required": False},
            "vessel_id": {"required": False, "allow_blank": True},
        }

    def validate_narrative(self, value: str) -> str:
        if len(value.strip()) < 100:
            raise serializers.ValidationError(
                "Near-miss description must be at least 100 characters (D-GAP-M38)."
            )
        return value

    def validate_near_miss_severity(self, value: str | None) -> str:
        normalized = str(value or "").strip().upper()
        if normalized not in {"HIGH", "MED", "LOW"}:
            raise serializers.ValidationError("Select a severity level before submitting.")
        return normalized

    def validate_near_miss_place(self, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = str(value).strip().upper()
        if normalized not in NEAR_MISS_PLACES:
            raise serializers.ValidationError("Select a valid place.")
        return normalized

    def validate_near_miss_category_tags(self, value: list[str] | None) -> list[str]:
        return self._validate_limited_list(
            value or [],
            field_name="near_miss_category_tags",
            item_validator=self._validate_category_tag,
        )

    def validate_near_miss_incident_type_ids(self, value: list[object] | None) -> list[str]:
        return self._validate_limited_list(
            value or [],
            field_name="near_miss_incident_type_ids",
            item_validator=lambda item: str(item).strip(),
        )

    def validate_near_miss_mscat_subcode_ids(self, value: list[object] | None) -> list[str]:
        return self._validate_limited_list(
            value or [],
            field_name="near_miss_mscat_subcode_ids",
            item_validator=lambda item: str(item).strip(),
        )

    def validate_near_miss_factor_causes(self, value: list[dict] | None) -> list[dict]:
        return self._validate_factor_causes(value or [])

    def validate_near_miss_shell_tag(self, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = self._validate_category_tag(value)
        return normalized

    def _validate_category_tag(self, value: object) -> str:
        normalized = resolve_near_miss_category(value)
        if normalized is None:
            raise serializers.ValidationError("Category must match the Safety SSOT values.")
        return normalized

    def _shell_tag_for_category(self, value: str | None) -> str | None:
        normalized = str(value or "").strip()
        if not normalized:
            return None
        if normalized.startswith(NEAR_MISS_OTHER_PREFIX):
            return NEAR_MISS_OTHER_CATEGORY
        return normalized[:32]

    def _validate_limited_list(self, value: list[object], *, field_name: str, item_validator) -> list[str]:
        if not isinstance(value, list):
            raise serializers.ValidationError("Expected a list.")
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            normalized = item_validator(item)
            if not normalized or normalized in seen:
                continue
            cleaned.append(normalized)
            seen.add(normalized)
        if len(cleaned) > 3:
            raise serializers.ValidationError("Select up to 3 values only.")
        return cleaned

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if _is_vessel_user(user):
            vessel_id = str(getattr(user, "vessel_id", "") or "").strip()
            vessel_code = str(getattr(user, "vessel_code", "") or "").strip()
            if not vessel_id:
                raise serializers.ValidationError(
                    {"vessel_id": "Authenticated vessel user is missing vessel assignment."}
                )
            attrs["vessel_id"] = vessel_id
            if vessel_code:
                attrs["vessel_code"] = vessel_code

        if not attrs.get("vessel_id"):
            raise serializers.ValidationError({"vessel_id": "This field is required."})
        if not user_has_vessel_access(user, attrs.get("vessel_id")):
            raise serializers.ValidationError({"vessel_id": "You are not assigned to this vessel."})
        if not str(attrs.get("reporter_device_fingerprint") or "").strip():
            raise serializers.ValidationError(
                {"reporter_device_fingerprint": "Digital signature requires device fingerprint (D-GAP-D1)."}
            )
        if not attrs.get("near_miss_severity"):
            raise serializers.ValidationError({"near_miss_severity": "Select a severity level before submitting."})
        incident_type_values = attrs.get("near_miss_incident_type_ids") or []
        if incident_type_values:
            attrs["incident_type_id"] = incident_type_values[0]
        if not attrs.get("incident_type_id"):
            raise serializers.ValidationError({"incident_type_id": "This field is required."})
        if not attrs.get("loss_type_primary_id"):
            raise serializers.ValidationError({"loss_type_primary_id": "This field is required."})
        resolved_incident_types = self._resolve_incident_types([attrs["incident_type_id"], *incident_type_values])
        if not resolved_incident_types:
            raise serializers.ValidationError({"incident_type_id": "Select a valid Safety incident type."})
        attrs["incident_type_id"] = resolved_incident_types[0]
        attrs["near_miss_incident_type_ids"] = _json_dump_list(resolved_incident_types[:3])
        if not MasterLossType.objects.filter(loss_type_id=attrs["loss_type_primary_id"], active=True).exists():
            raise serializers.ValidationError({"loss_type_primary_id": "Select a valid Safety loss type."})

        category_tags = attrs.get("near_miss_category_tags") or []
        if category_tags:
            attrs["near_miss_shell_tag"] = self._shell_tag_for_category(category_tags[0])
        if category_tags:
            attrs["near_miss_category_tags"] = _json_dump_list(category_tags[:3])

        factor_causes = attrs.get("near_miss_factor_causes") or []
        if not factor_causes:
            raise serializers.ValidationError(
                {"near_miss_factor_causes": "Select immediate and root causes for every factor."}
            )
        attrs["near_miss_factor_causes"] = _json_dump_list(factor_causes)
        attrs["near_miss_mscat_subcode_id"] = None
        attrs["near_miss_mscat_category_id"] = None
        attrs["near_miss_mscat_subcode_ids"] = _json_dump_list([])

        occurred_at = attrs.get("occurred_at")
        reported_at = attrs.get("reported_at")
        effective_reported_at = reported_at or timezone.now()
        if occurred_at is None:
            raise serializers.ValidationError({"occurred_at": "Occurred time is required."})
        if occurred_at > timezone.now():
            raise serializers.ValidationError({"occurred_at": "Occurred time cannot be in the future."})
        if occurred_at > effective_reported_at:
            raise serializers.ValidationError(
                {"occurred_at": "Occurred time cannot be after reported time."}
            )
        return attrs

    def _resolve_incident_types(self, values: list[object]) -> list[int]:
        resolved: list[int] = []
        seen: set[int] = set()
        for value in values:
            incident_type = self._resolve_incident_type(value)
            legacy_id = getattr(incident_type, "legacy_int_id", None)
            if legacy_id is not None and legacy_id not in seen:
                resolved.append(int(legacy_id))
                seen.add(int(legacy_id))
        return resolved[:3]

    def _resolve_mscat_subcodes(self, values: list[object]) -> list[MasterMscatTaxonomy]:
        subcodes: list[str] = []
        seen: set[str] = set()
        for value in values:
            subcode = str(value or "").strip()
            if subcode and subcode not in seen:
                subcodes.append(subcode)
                seen.add(subcode)
        if not subcodes:
            return []
        rows = MasterMscatTaxonomy.objects.filter(subcode_id__in=subcodes[:3], active=True)
        row_by_subcode = {row.subcode_id: row for row in rows}
        missing = [subcode for subcode in subcodes[:3] if subcode not in row_by_subcode]
        if missing:
            raise serializers.ValidationError({"near_miss_mscat_subcode_ids": "Select valid immediate causes."})
        return [row_by_subcode[subcode] for subcode in subcodes[:3]]

    def _validate_factor_causes(self, rows: list[dict]) -> list[dict]:
        if not isinstance(rows, list):
            raise serializers.ValidationError("Expected a list.")
        required_factors = {choice[0] for choice in NearMissCauseOption.Factor.choices}
        allowed_factors = set(required_factors)
        cleaned_by_factor: dict[str, dict] = {}
        option_ids: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                raise serializers.ValidationError("Each factor cause row must be an object.")
            factor = str(row.get("factor") or "").strip().upper()
            if factor not in allowed_factors:
                raise serializers.ValidationError("Select a valid near-miss factor.")
            cleaned = {"factor": factor}
            for stage in ("immediate", "root"):
                option_id = str(row.get(f"{stage}_option_id") or "").strip()
                if not option_id:
                    raise serializers.ValidationError({f"{stage}_option_id": "Select a cause or Not Applicable."})
                other_text = str(row.get(f"{stage}_other_text") or "").strip()
                cleaned[f"{stage}_option_id"] = option_id
                cleaned[f"{stage}_other_text"] = other_text
                option_ids.add(option_id)
            cleaned_by_factor[factor] = cleaned
        missing_factors = sorted(required_factors - set(cleaned_by_factor))
        if missing_factors:
            raise serializers.ValidationError({"near_miss_factor_causes": "Select immediate and root causes for every factor."})
        options = NearMissCauseOption.objects.filter(id__in=option_ids, active=True)
        option_by_id = {str(option.id): option for option in options}
        if len(option_by_id) != len(option_ids):
            raise serializers.ValidationError({"near_miss_factor_causes": "Select valid near-miss cause options."})
        for factor, cleaned in cleaned_by_factor.items():
            for stage, cause_stage in (
                ("immediate", NearMissCauseOption.CauseStage.IMMEDIATE),
                ("root", NearMissCauseOption.CauseStage.ROOT),
            ):
                option = option_by_id[cleaned[f"{stage}_option_id"]]
                if option.factor != factor or option.cause_stage != cause_stage:
                    raise serializers.ValidationError({"near_miss_factor_causes": "Cause option does not match its factor/type."})
                cleaned[f"{stage}_option_text"] = option.option_text
                if option.option_text.strip().lower() in {"other", "others"} and not cleaned[f"{stage}_other_text"]:
                    raise serializers.ValidationError({"near_miss_factor_causes": "Specify the cause when Other is selected."})
                if option.option_text.strip().lower() not in {"other", "others"}:
                    cleaned[f"{stage}_other_text"] = ""
        return [cleaned_by_factor[factor] for factor in sorted(cleaned_by_factor)]

    def _resolve_incident_type(self, value: object) -> MasterSafetyIncidentType | None:
        raw_value = str(value or "").strip()
        if not raw_value:
            return None
        if is_uuid_identifier(raw_value):
            return MasterSafetyIncidentType.objects.filter(id=raw_value, active=True).first()
        if raw_value.isdigit():
            return MasterSafetyIncidentType.objects.filter(legacy_int_id=int(raw_value), active=True).first()
        return None

    def create(self, validated_data):
        repository = self.context["incident_repository"]
        validated_data["record_type"] = Incident.RecordType.NEAR_MISS
        validated_data.setdefault("state", Incident.State.PENDING_VESSEL_REVIEW)
        validated_data.setdefault("current_phase", 1)
        validated_data.setdefault("reported_at", timezone.now())
        validated_data.pop("near_miss_priority", None)
        return repository.create(validated_data)


class NearMissCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NearMissCategory
        fields = (
            "id",
            "category_name",
            "display_order",
            "active",
        )
        read_only_fields = fields


class NearMissGuidancePromptSerializer(serializers.ModelSerializer):
    class Meta:
        model = NearMissGuidancePrompt
        fields = (
            "id",
            "category_tag",
            "incident_type_id",
            "prompt_text",
            "display_order",
            "active",
        )
        read_only_fields = ("id",)

    def validate_category_tag(self, value: str | None) -> str | None:
        if value in (None, ""):
            return None
        normalized = resolve_near_miss_category(value)
        if normalized is None:
            raise serializers.ValidationError("Category must match the Safety SSOT values.")
        return normalized


class NearMissCauseOptionSerializer(serializers.ModelSerializer):
    factor_label = serializers.CharField(source="get_factor_display", read_only=True)
    cause_stage_label = serializers.CharField(source="get_cause_stage_display", read_only=True)

    class Meta:
        model = NearMissCauseOption
        fields = (
            "id",
            "factor",
            "factor_label",
            "cause_stage",
            "cause_stage_label",
            "option_code",
            "option_text",
            "display_order",
            "active",
        )
        read_only_fields = fields


class NearMissKpiTargetSerializer(serializers.ModelSerializer):
    actual_count = serializers.IntegerField(read_only=True, required=False)
    variance = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = NearMissKpiTarget
        fields = (
            "id",
            "vessel_id",
            "year",
            "month",
            "target_count",
            "actual_count",
            "variance",
            "active",
        )
        read_only_fields = ("id", "actual_count", "variance")

    def validate_vessel_id(self, value: str) -> str:
        value = str(value or "").strip()
        if not value:
            raise serializers.ValidationError("Vessel is required.")
        return value


class NearMissCategoryReclassifySerializer(serializers.Serializer):
    near_miss_shell_tag = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    near_miss_mscat_subcode_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    reason = serializers.CharField(allow_blank=False, trim_whitespace=True)

    def validate(self, attrs):
        if "near_miss_shell_tag" not in attrs and "near_miss_mscat_subcode_id" not in attrs:
            raise serializers.ValidationError("Select a category or root cause to reclassify.")
        if "near_miss_shell_tag" in attrs:
            normalized = resolve_near_miss_category(attrs["near_miss_shell_tag"])
            if normalized is None:
                raise serializers.ValidationError({"near_miss_shell_tag": "Category must match the Safety SSOT values."})
            attrs["near_miss_category_tag"] = normalized
            attrs["near_miss_shell_tag"] = (
                NEAR_MISS_OTHER_CATEGORY if normalized.startswith(NEAR_MISS_OTHER_PREFIX) else normalized
            )

        subcode = str(attrs.get("near_miss_mscat_subcode_id") or "").strip()
        if subcode:
            mscat = MasterMscatTaxonomy.objects.filter(subcode_id=subcode, active=True).first()
            if mscat is None:
                raise serializers.ValidationError({"near_miss_mscat_subcode_id": "Select a valid root cause."})
            attrs["near_miss_mscat_subcode_id"] = mscat.subcode_id
            attrs["near_miss_mscat_category_id"] = mscat.category_id
        elif "near_miss_mscat_subcode_id" in attrs:
            attrs["near_miss_mscat_subcode_id"] = None
            attrs["near_miss_mscat_category_id"] = None
        return attrs
