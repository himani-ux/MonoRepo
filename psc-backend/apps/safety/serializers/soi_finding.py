from __future__ import annotations

from django.db import connection
from rest_framework import serializers

from apps.safety.models import SOIFinding, SOIInspection, SafetyFieldHistory
from apps.safety.services.field_history_recorder import history_value_as_text, parse_history_value
from apps.safety.services.repeat_finding_detector import RepeatFindingDetector
from apps.safety.services.high_severity_nudge import HighSeverityNudgeService
from apps.safety.services.high_severity_photo_validator import HighSeverityPhotoValidator
from apps.safety.services.life_threat_detector import LifeThreatDetector


def _dedupe_area_ids(area_ids: list[int]) -> list[int]:
    seen: set[int] = set()
    ordered: list[int] = []
    for raw_area_id in area_ids:
        area_id = int(raw_area_id)
        if area_id in seen:
            continue
        seen.add(area_id)
        ordered.append(area_id)
    return ordered


class SOIFindingSerializer(serializers.ModelSerializer):
    inspection_public_id = serializers.SerializerMethodField()
    incident_linked_id = serializers.SerializerMethodField()
    incident_linked_number = serializers.SerializerMethodField()
    incident_worthy_reason = serializers.SerializerMethodField()
    is_repeat = serializers.SerializerMethodField()
    master_approval_state = serializers.SerializerMethodField()
    master_counter_signature = serializers.SerializerMethodField()
    life_threat_escalation_target = serializers.SerializerMethodField()
    pending_closure_signature = serializers.SerializerMethodField()
    repeat_badge_text = serializers.SerializerMethodField()
    repeat_occurrence_count = serializers.SerializerMethodField()

    class Meta:
        model = SOIFinding
        fields = (
            "id",
            "public_id",
            "inspection_id",
            "inspection_public_id",
            "area_id",
            "item_id",
            "title",
            "description",
            "severity",
            "priority",
            "mscat_category_id",
            "mscat_subcode_id",
            "shell_tag",
            "assigned_crew_id",
            "due_date",
            "proposed_action",
            "status",
            "carried_forward_count",
            "photo_attachment_path",
            "incident_linked_id",
            "incident_linked_number",
            "incident_worthy_reason",
            "life_threat_escalation_target",
            "is_repeat",
            "repeat_occurrence_count",
            "repeat_badge_text",
            "pending_closure_signature",
            "master_counter_signature",
            "master_approval_state",
            "master_approved_at",
            "master_approved_by",
            "closed_at",
            "closure_note",
            "schema_version",
            "created_by",
            "created_date",
            "updated_by",
            "updated_date",
        )

    def get_inspection_public_id(self, instance: SOIFinding) -> str | None:
        inspection = getattr(instance, "inspection", None)
        if inspection is not None:
            return str(inspection.public_id)
        row = SOIInspection.objects.filter(pk=instance.inspection_id, is_deleted=False).values("public_id").first()
        return str(row["public_id"]) if row else None

    def _history_value(self, instance: SOIFinding, field_name: str) -> str | None:
        if SafetyFieldHistory._meta.db_table not in connection.introspection.table_names():
            return None
        row = (
            SafetyFieldHistory.objects.filter(
                parent_table=instance._meta.db_table,
                parent_id=instance.pk,
                field_name=field_name,
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        return history_value_as_text(row.new_value) if row is not None else None

    def _history_json(self, instance: SOIFinding, field_name: str) -> dict[str, object] | None:
        if SafetyFieldHistory._meta.db_table not in connection.introspection.table_names():
            return None
        row = (
            SafetyFieldHistory.objects.filter(
                parent_table=instance._meta.db_table,
                parent_id=instance.pk,
                field_name=field_name,
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if row is None:
            return None
        payload = parse_history_value(row.new_value)
        if not isinstance(payload, dict):
            return None
        return payload

    def _repeat_result(self, instance: SOIFinding):
        cache = getattr(self, "_repeat_cache", None)
        if cache is None:
            cache = {}
            self._repeat_cache = cache
        if instance.pk not in cache:
            detector = self.context.get("repeat_finding_detector") or RepeatFindingDetector()
            cache[instance.pk] = detector.detect(instance)
        return cache[instance.pk]

    def _signature_payload(self, instance: SOIFinding, field_name: str) -> dict[str, object] | None:
        payload = self._history_json(instance, field_name)
        if payload is None:
            return None
        typed_name = str(payload.get("typed_name") or "").strip()
        signed_at = str(payload.get("signed_at") or "").strip()
        device_fingerprint = str(payload.get("device_fingerprint") or "").strip()
        if not typed_name or not signed_at or not device_fingerprint:
            return None
        return {
            "signer_display_name": typed_name,
            "signed_at": signed_at,
            "device_fingerprint_last8": device_fingerprint[-8:],
        }

    def get_incident_linked_id(self, instance: SOIFinding) -> int | None:
        raw = self._history_value(instance, "incident_linked_id")
        return int(raw) if raw and str(raw).isdigit() else None

    def get_incident_linked_number(self, instance: SOIFinding) -> str | None:
        return self._history_value(instance, "incident_linked_number")

    def get_incident_worthy_reason(self, instance: SOIFinding) -> str | None:
        return self._history_value(instance, "incident_worthy_reason")

    def get_life_threat_escalation_target(self, instance: SOIFinding) -> str | None:
        return self._history_value(instance, "life_threat_escalation_target")

    def get_is_repeat(self, instance: SOIFinding) -> bool:
        return bool(self._repeat_result(instance).is_repeat)

    def get_repeat_occurrence_count(self, instance: SOIFinding) -> int:
        return int(self._repeat_result(instance).occurrence_count)

    def get_repeat_badge_text(self, instance: SOIFinding) -> str | None:
        return self._repeat_result(instance).badge_text

    def get_pending_closure_signature(self, instance: SOIFinding) -> dict[str, object] | None:
        return self._signature_payload(instance, "soi_pending_closure_signature")

    def get_master_counter_signature(self, instance: SOIFinding) -> dict[str, object] | None:
        if instance.status not in {SOIFinding.Status.MASTER_APPROVED, SOIFinding.Status.CLOSED}:
            return None
        if not instance.master_approved_at or not instance.master_approved_by:
            return None
        return self._signature_payload(instance, "soi_master_counter_signature")

    def get_master_approval_state(self, instance: SOIFinding) -> str | None:
        if instance.status not in {SOIFinding.Status.MASTER_APPROVED, SOIFinding.Status.CLOSED}:
            return None
        return self._history_value(instance, "master_approval_state") or (
            "MASTER_APPROVED" if instance.master_approved_at and instance.master_approved_by else None
        )


class SOIFindingCreateSerializer(serializers.Serializer):
    INCIDENT_WORTHY_CHOICES = ("CREATE_INCIDENT", "KEEP_SOI_ONLY")
    LIFE_THREAT_TARGET_CHOICES = ("INCIDENT", "NEAR_MISS")

    checklist_unique_id = serializers.CharField(max_length=32)
    area_id = serializers.IntegerField(min_value=1)
    item_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(max_length=256)
    description = serializers.CharField()
    severity = serializers.ChoiceField(choices=SOIFinding.Severity.values)
    priority = serializers.ChoiceField(choices=SOIFinding.Priority.values)
    mscat_category_id = serializers.IntegerField(required=False, allow_null=True)
    mscat_subcode_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=16)
    shell_tag = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=32)
    assigned_crew_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=64)
    due_date = serializers.DateField(required=False, allow_null=True)
    proposed_action = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    photo_attachment_path = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=512)
    incident_worthy_action = serializers.ChoiceField(
        choices=INCIDENT_WORTHY_CHOICES,
        required=False,
        allow_null=True,
    )
    incident_worthy_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    life_threat_escalation_target = serializers.ChoiceField(
        choices=LIFE_THREAT_TARGET_CHOICES,
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        inspection: SOIInspection = self.context["inspection"]
        repository = self.context["finding_repository"]
        soi_repository = self.context["soi_repository"]
        area_id = int(attrs["area_id"])

        if inspection.state == SOIInspection.State.CLOSED:
            raise serializers.ValidationError(
                {"inspection_id": "Closed SOI inspections are read-only."}
            )

        if not inspection.checklist_unique_id or inspection.checklist_generated_at is None:
            raise serializers.ValidationError(
                {"inspection_id": "SOI findings can only be registered after the paper checklist has been generated."}
            )
        checklist_unique_id = str(attrs.get("checklist_unique_id") or "").strip()
        if checklist_unique_id != str(inspection.checklist_unique_id):
            raise serializers.ValidationError(
                {"checklist_unique_id": "Checklist unique ID must match the downloaded SOI paper packet."}
            )

        if area_id not in repository.selected_area_ids(inspection.id):
            raise serializers.ValidationError(
                {"area_id": "SOI findings may only be registered against areas selected on the paper checklist."}
            )
        item_id = attrs.get("item_id")
        if item_id not in (None, ""):
            legacy_item_id = soi_repository.resolve_checklist_item_legacy_id(item_id=item_id, area_id=area_id)
            if legacy_item_id is None:
                raise serializers.ValidationError(
                    {"item_id": "Checklist item must exist in master_soi_area_item and belong to the selected SOI area."}
                )
            attrs["item_id"] = legacy_item_id
        else:
            attrs["item_id"] = None

        photo_validator = self.context.get("high_severity_photo_validator") or HighSeverityPhotoValidator()
        photo_validator.validate(
            severity=str(attrs["severity"]).strip().upper(),
            photo_attachment_path=attrs.get("photo_attachment_path"),
        )

        life_threat_detector = self.context.get("life_threat_detector") or LifeThreatDetector()
        life_threat_result = life_threat_detector.scan(
            severity=str(attrs["severity"]).strip().upper(),
            title=str(attrs.get("title") or ""),
            description=str(attrs.get("description") or ""),
        )
        is_high_severity = str(attrs["severity"]).strip().upper() == SOIFinding.Severity.HIGH
        incident_worthy_action = str(attrs.get("incident_worthy_action") or "").strip().upper() or None
        incident_worthy_reason = str(attrs.get("incident_worthy_reason") or "").strip() or None
        life_threat_escalation_target = str(attrs.get("life_threat_escalation_target") or "").strip().upper() or None

        errors: dict[str, str] = {}
        if life_threat_result.detected:
            if life_threat_escalation_target not in self.LIFE_THREAT_TARGET_CHOICES:
                errors["life_threat_escalation_target"] = (
                    "Life-threat findings must escalate through Incident or Near Miss before save can continue."
                )
        elif is_high_severity:
            if incident_worthy_action not in self.INCIDENT_WORTHY_CHOICES:
                errors["incident_worthy_action"] = (
                    "HIGH-severity findings must record the incident-worthy prompt outcome."
                )
            elif incident_worthy_action == "KEEP_SOI_ONLY" and not incident_worthy_reason:
                errors["incident_worthy_reason"] = (
                    "Reason is required when keeping a HIGH-severity finding in SOI only."
                )

        if errors:
            raise serializers.ValidationError(errors)

        self._incident_worthy_action = incident_worthy_action
        self._incident_worthy_reason = incident_worthy_reason
        self._life_threat_escalation_target = life_threat_escalation_target
        self._life_threat_result = life_threat_result
        assigned = attrs.get("assigned_crew_id")
        attrs["assigned_crew_id"] = None if assigned in (None, "") else str(assigned).strip()
        attrs.pop("checklist_unique_id", None)
        return attrs

    def create(self, validated_data):
        repository = self.context["finding_repository"]
        inspection: SOIInspection = self.context["inspection"]
        actor_id = self.context["actor_id"]
        incident_worthy_action = validated_data.pop("incident_worthy_action", None)
        incident_worthy_reason = validated_data.pop("incident_worthy_reason", None)
        life_threat_escalation_target = validated_data.pop("life_threat_escalation_target", None)
        return repository.create_finding(
            inspection=inspection,
            payload=validated_data,
            actor_id=actor_id,
        )

    def save(self, **kwargs):
        finding = super().save(**kwargs)
        nudge_service = self.context.get("high_severity_nudge_service") or HighSeverityNudgeService()
        self.nudge_result = nudge_service.resolve(
            finding=finding,
            inspection=self.context["inspection"],
            user=self.context.get("actor_user"),
            incident_worthy_action=getattr(self, "_incident_worthy_action", None),
            incident_worthy_reason=getattr(self, "_incident_worthy_reason", None),
            life_threat_escalation_target=getattr(self, "_life_threat_escalation_target", None),
            life_threat_result=getattr(self, "_life_threat_result", LifeThreatDetector().scan()),
        )
        return finding


class SOIFindingSubmitSerializer(serializers.Serializer):
    submitted_area_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=1,
    )

    def validate_submitted_area_ids(self, value):
        return _dedupe_area_ids(list(value or []))

    def save(self, **kwargs):
        repository = self.context["finding_repository"]
        inspection: SOIInspection = self.context["inspection"]
        actor_id = self.context["actor_id"]
        return repository.submit_areas(
            inspection=inspection,
            submitted_area_ids=list(self.validated_data["submitted_area_ids"]),
            actor_id=actor_id,
        )


class _BaseSOIFindingActionSerializer(serializers.Serializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)
        for key in self.initial_data:
            lowered = str(key).lower()
            if "acting" in lowered or "deputy" in lowered:
                raise serializers.ValidationError(
                    {
                        key: "Acting-role / deputy-chain concepts not supported (D-GAP-A3 / A4)."
                    }
                )
        return attrs


class SOIFindingPendingClosureSerializer(_BaseSOIFindingActionSerializer):
    typed_name = serializers.CharField(allow_blank=False, trim_whitespace=True)
    device_fingerprint = serializers.CharField(allow_blank=False, trim_whitespace=True)
    closure_note = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class SOIFindingApprovalSerializer(_BaseSOIFindingActionSerializer):
    decision = serializers.ChoiceField(choices=("APPROVE", "REJECT"))
    typed_name = serializers.CharField(required=False, allow_blank=True, allow_null=True, trim_whitespace=True)
    device_fingerprint = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        trim_whitespace=True,
    )
    closure_note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        decision = str(attrs["decision"]).strip().upper()
        if decision == "APPROVE":
            if not str(attrs.get("typed_name") or "").strip():
                raise serializers.ValidationError(
                    {"typed_name": "Master typed name is required for digital counter-signature."}
                )
            if not str(attrs.get("device_fingerprint") or "").strip():
                raise serializers.ValidationError(
                    {"device_fingerprint": "Device fingerprint is required for digital counter-signature."}
                )
        else:
            if not str(attrs.get("reason") or "").strip():
                raise serializers.ValidationError(
                    {"reason": "Master rejection requires a written reason."}
                )
        return attrs


class SOIFindingReopenSerializer(_BaseSOIFindingActionSerializer):
    reason = serializers.CharField(allow_blank=False, trim_whitespace=True)
