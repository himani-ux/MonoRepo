from __future__ import annotations

from rest_framework import serializers

from apps.safety.authentication.vessel_scope import user_has_vessel_access
from apps.safety.models import SOIInspection, SOIOfficerSetting
from apps.safety.serializers.vessel_display import VesselDisplayMixin
from apps.safety.services.checklist_version_resolver import ChecklistVersionResolutionError
from apps.safety.services.field_history_recorder import resolve_actor_id, resolve_actor_role

SECTION_12_ALREADY_COVERED_ERROR = (
    "Section 12 'Cross-cutting Safety & Culture' evaluated once per 3-month cycle "
    "(D-GAP-M23). This cycle already covered."
)
MAX_SOI_SELECTED_AREAS = 4


def _dedupe_preserve_order(values: list[object]) -> list[object]:
    seen: set[object] = set()
    ordered: list[object] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _validate_area_selection(
    *,
    repository,
    vessel_id: str,
    area_ids: list[int],
    section_12_included: bool,
    section12_cycle_enforcer=None,
    at_date=None,
    exclude_inspection_id: int | None = None,
) -> list[int]:
    normalized_area_ids = [int(area_id) for area_id in _dedupe_preserve_order(area_ids)]
    if not normalized_area_ids:
        raise serializers.ValidationError({"area_ids": "Pick at least one applicable area for the SOI."})
    if len(normalized_area_ids) > MAX_SOI_SELECTED_AREAS:
        raise serializers.ValidationError(
            {"area_ids": f"Select a maximum of {MAX_SOI_SELECTED_AREAS} areas for one SOI."}
        )

    available_areas = repository.list_available_areas(vessel_id=str(vessel_id))
    applicable_area_ids = {int(row["area_id"]) for row in available_areas}
    section_12_area_ids = {
        int(row["area_id"])
        for row in available_areas
        if bool(row.get("section_12_flag"))
    }
    invalid_area_ids = [area_id for area_id in normalized_area_ids if area_id not in applicable_area_ids]
    if invalid_area_ids:
        raise serializers.ValidationError(
            {
                "area_ids": (
                    "Selected area ids are not applicable for the vessel: "
                    + ", ".join(str(area_id) for area_id in invalid_area_ids)
                )
            }
        )

    selected_section_12_area_ids = [
        area_id for area_id in normalized_area_ids if area_id in section_12_area_ids
    ]
    if selected_section_12_area_ids and not section_12_included:
        raise serializers.ValidationError(
            {
                "section_12_included": (
                    "Cross-cutting Safety & Culture is reserved for Section 12. Set section_12_included to true "
                    "to carry it in this cycle."
                )
            }
        )
    if section_12_included and not selected_section_12_area_ids:
        raise serializers.ValidationError(
            {"section_12_included": "Section 12 requires the cross-cutting Safety & Culture area to be selected."}
        )
    if section_12_included and section12_cycle_enforcer is not None and at_date is not None:
        can_pick, _next_allowed_date = section12_cycle_enforcer.can_pick_section_12(
            vessel_id=str(vessel_id),
            at_date=at_date,
            exclude_inspection_id=exclude_inspection_id,
        )
        if not can_pick:
            raise serializers.ValidationError({"section_12_included": SECTION_12_ALREADY_COVERED_ERROR})
    return normalized_area_ids


def _validate_trainee_ids(trainee_crew_ids: list[str]) -> list[str]:
    normalized = [str(crew_id).strip() for crew_id in trainee_crew_ids if str(crew_id).strip()]
    if len(normalized) > 3:
        raise serializers.ValidationError({"trainee_crew_ids": "A maximum of 3 trainees may be assigned."})
    if len(set(normalized)) != len(normalized):
        raise serializers.ValidationError({"trainee_crew_ids": "Trainee crew ids must be unique."})
    return normalized


class SOIInspectionAreaSerializer(serializers.Serializer):
    selection_id = serializers.CharField()
    inspection_id = serializers.CharField()
    area_id = serializers.IntegerField()
    area_name = serializers.CharField()
    section_12_flag = serializers.BooleanField()
    display_order = serializers.IntegerField()
    inspected = serializers.BooleanField()
    last_inspected_at = serializers.DateTimeField(allow_null=True)
    notes = serializers.CharField(allow_blank=True, allow_null=True)
    schema_version = serializers.IntegerField()


class SOITraineeSerializer(serializers.Serializer):
    inspection_id = serializers.CharField()
    crew_id = serializers.CharField()
    trainee_slot = serializers.IntegerField()
    schema_version = serializers.IntegerField()


class SOIChecklistVersionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    legacy_int_id = serializers.IntegerField()
    version_label = serializers.CharField()
    effective_from = serializers.DateField()
    effective_to = serializers.DateField(allow_null=True)
    source_description = serializers.CharField()
    active = serializers.BooleanField()


class SOIInspectionSerializer(VesselDisplayMixin, serializers.ModelSerializer):
    checklist_version = serializers.SerializerMethodField()
    selected_areas = serializers.SerializerMethodField()
    trainees = serializers.SerializerMethodField()
    vessel_code = serializers.SerializerMethodField()
    vessel_name = serializers.SerializerMethodField()
    vessel_display_name = serializers.SerializerMethodField()

    class Meta:
        model = SOIInspection
        fields = (
            "id",
            "vessel_id",
            "vessel_code",
            "vessel_name",
            "vessel_display_name",
            "inspection_reference",
            "cycle_label",
            "state",
            "planned_date",
            "safety_officer_crew_id",
            "safety_officer_department",
            "assistant_crew_id",
            "assistant_department",
            "master_crew_id",
            "checklist_unique_id",
            "checklist_generated_at",
            "checklist_format",
            "checklist_version",
            "fieldwork_started_at",
            "reported_at",
            "closed_at",
            "lost_paper_flag",
            "lost_paper_note",
            "section_12_included",
            "schema_version",
            "created_by",
            "created_date",
            "selected_areas",
            "trainees",
            "updated_by",
            "updated_date",
        )

    def get_checklist_version(self, obj):
        resolver = self.context["checklist_version_resolver"]
        try:
            version = resolver.get_version_for_inspection(obj)
        except ChecklistVersionResolutionError:
            return None
        return SOIChecklistVersionSerializer(version).data

    def get_selected_areas(self, obj):
        repository = self.context["soi_repository"]
        return SOIInspectionAreaSerializer(repository.list_selected_areas(obj.id), many=True).data

    def get_trainees(self, obj):
        repository = self.context["soi_repository"]
        return SOITraineeSerializer(repository.list_trainees(obj.id), many=True).data


class SOIInspectionCreateSerializer(serializers.Serializer):
    vessel_id = serializers.CharField(max_length=64)
    inspection_reference = serializers.CharField(required=False, allow_blank=True, max_length=32)
    cycle_label = serializers.CharField(max_length=16)
    planned_date = serializers.DateField()
    safety_officer_crew_id = serializers.CharField(required=False, allow_blank=True, max_length=64)
    assistant_crew_id = serializers.CharField(max_length=64)
    trainee_crew_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    area_ids = serializers.ListField(child=serializers.IntegerField(min_value=1))
    section_12_included = serializers.BooleanField(required=False, default=False)
    schema_version = serializers.IntegerField(required=False, default=1)

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user_has_vessel_access(user, attrs.get("vessel_id")):
            raise serializers.ValidationError({"vessel_id": "You are not assigned to this vessel."})

        repository = self.context["soi_repository"]
        attrs["area_ids"] = _validate_area_selection(
            repository=repository,
            vessel_id=str(attrs["vessel_id"]),
            area_ids=list(attrs.get("area_ids") or []),
            section_12_included=bool(attrs.get("section_12_included", False)),
            section12_cycle_enforcer=self.context["section12_cycle_enforcer"],
            at_date=attrs["planned_date"],
        )
        validator = self.context["assistant_validator"]
        safety_officer = validator.resolve_safety_officer(
            vessel_id=str(attrs["vessel_id"]),
            actor_id=resolve_actor_id(user),
            actor_role=resolve_actor_role(user),
            requested_safety_officer_crew_id=attrs.get("safety_officer_crew_id"),
            active_on=attrs["planned_date"],
        )
        attrs["safety_officer_crew_id"] = str(safety_officer["crew_id"])
        assignments = validator.resolve_assignments(
            vessel_id=str(attrs["vessel_id"]),
            safety_officer_crew_id=str(attrs["safety_officer_crew_id"]),
            assistant_crew_id=str(attrs["assistant_crew_id"]),
            active_on=attrs["planned_date"],
        )
        attrs["safety_officer_department"] = assignments["safety_officer_department"]
        attrs["assistant_department"] = assignments["assistant_department"]
        attrs["trainee_crew_ids"] = validator.validate_trainees(
            vessel_id=str(attrs["vessel_id"]),
            trainee_crew_ids=_validate_trainee_ids(list(attrs.get("trainee_crew_ids") or [])),
            safety_officer_crew_id=str(attrs["safety_officer_crew_id"]),
            assistant_crew_id=str(attrs["assistant_crew_id"]),
            active_on=attrs["planned_date"],
        )
        if not str(attrs.get("inspection_reference") or "").strip():
            attrs["inspection_reference"] = self._generate_reference(
                vessel_id=str(attrs["vessel_id"]),
                planned_date=attrs["planned_date"],
            )
        resolver = self.context["checklist_version_resolver"]
        try:
            attrs["resolved_checklist_version"] = resolver.get_active_version()
        except ChecklistVersionResolutionError as exc:
            raise serializers.ValidationError({"checklist_version": str(exc)}) from exc
        return attrs

    def _generate_reference(self, *, vessel_id: str, planned_date) -> str:
        repository = self.context["soi_repository"]
        year_suffix = str(planned_date.year)[-2:]
        vessel_code = repository.resolve_vessel_reference_code(vessel_id=str(vessel_id))
        prefix = f"SOI/{vessel_code}/{year_suffix}/"
        existing_references = set(
            repository.inspection_model.objects.filter(
                inspection_reference__startswith=prefix,
                is_deleted=False,
            ).values_list("inspection_reference", flat=True)
        )
        sequence = (
            repository.inspection_model.objects.filter(
                vessel_id=str(vessel_id),
                planned_date__year=planned_date.year,
                is_deleted=False,
            ).count()
            + 1
        )
        reference = f"{prefix}{sequence:03d}"
        while reference in existing_references:
            sequence += 1
            reference = f"{prefix}{sequence:03d}"
        return reference

    def create(self, validated_data):
        repository = self.context["soi_repository"]
        area_ids = list(validated_data.pop("area_ids", []))
        trainee_crew_ids = list(validated_data.pop("trainee_crew_ids", []))
        validated_data.pop("resolved_checklist_version", None)
        return repository.create_planned_inspection(
            inspection_payload=validated_data,
            area_ids=area_ids,
            trainee_crew_ids=trainee_crew_ids,
        )


class SOIApplicabilitySerializer(serializers.Serializer):
    map_id = serializers.CharField(allow_null=True)
    area_id = serializers.IntegerField()
    area_name = serializers.CharField()
    section_12_flag = serializers.BooleanField()
    applicable = serializers.BooleanField()
    last_inspected_at = serializers.DateTimeField(allow_null=True)
    due_at = serializers.DateTimeField(allow_null=True)
    schema_version = serializers.IntegerField()


class SOIApplicabilityRequestResultSerializer(serializers.Serializer):
    request_id = serializers.CharField()
    status = serializers.CharField()
    vessel_id = serializers.CharField()
    area_id = serializers.IntegerField()
    area_name = serializers.CharField(allow_null=True)
    current_applicable = serializers.BooleanField()
    requested_applicable = serializers.BooleanField()
    reason = serializers.CharField()
    master_requested_by = serializers.CharField()
    master_requested_at = serializers.DateTimeField(allow_null=True)


class SOIApplicabilityApprovalResultSerializer(serializers.Serializer):
    request_id = serializers.CharField()
    status = serializers.CharField()
    decision = serializers.CharField()
    vessel_id = serializers.CharField()
    area_id = serializers.IntegerField()
    area_name = serializers.CharField(allow_null=True)
    current_applicable = serializers.BooleanField()
    applicable = serializers.BooleanField()
    requested_applicable = serializers.BooleanField()
    reason = serializers.CharField()
    dpa_approved_by = serializers.CharField()
    dpa_approved_at = serializers.DateTimeField(allow_null=True)
    map_id = serializers.CharField(allow_null=True)


class SOIPendingApplicabilityRequestSerializer(serializers.Serializer):
    request_id = serializers.CharField()
    vessel_id = serializers.CharField()
    area_id = serializers.IntegerField()
    area_name = serializers.CharField()
    section_12_flag = serializers.BooleanField()
    old_applicable = serializers.BooleanField()
    new_applicable = serializers.BooleanField()
    reason = serializers.CharField()
    master_requested_by = serializers.CharField()
    master_requested_at = serializers.DateTimeField()
    master_signature = serializers.CharField()


class SOIApplicabilityRequestPayloadSerializer(serializers.Serializer):
    area_id = serializers.IntegerField(min_value=1)
    new_applicable = serializers.BooleanField(required=False, default=False)
    reason = serializers.CharField()
    master_signature = serializers.CharField()

    def validate(self, attrs):
        reason = str(attrs.get("reason") or "").strip()
        if len(reason) < 100:
            raise serializers.ValidationError({"reason": "Applicability request reason must be at least 100 characters."})

        master_signature = str(attrs.get("master_signature") or "").strip()
        if not master_signature:
            raise serializers.ValidationError({"master_signature": "Master signature is required."})

        attrs["reason"] = reason
        attrs["master_signature"] = master_signature
        return attrs

    def save(self, **kwargs):
        repository = self.context["soi_repository"]
        actor_id = self.context["actor_id"]
        vessel_id = self.context["vessel_id"]
        try:
            return repository.create_applicability_request(
                vessel_id=str(vessel_id),
                area_id=int(self.validated_data["area_id"]),
                new_applicable=bool(self.validated_data.get("new_applicable", False)),
                actor_id=actor_id,
                reason=self.validated_data["reason"],
                master_signature=self.validated_data["master_signature"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"non_field_errors": [str(exc)]}) from exc


class SOIApplicabilityApprovalPayloadSerializer(serializers.Serializer):
    area_id = serializers.IntegerField(min_value=1)
    dpa_decision = serializers.ChoiceField(choices=["APPROVED", "REJECTED"])
    reason = serializers.CharField()
    dpa_signature = serializers.CharField()

    def validate(self, attrs):
        reason = str(attrs.get("reason") or "").strip()
        if not reason:
            raise serializers.ValidationError({"reason": "DPA decision note is required."})

        dpa_signature = str(attrs.get("dpa_signature") or "").strip()
        if not dpa_signature:
            raise serializers.ValidationError({"dpa_signature": "DPA signature is required."})

        attrs["reason"] = reason
        attrs["dpa_signature"] = dpa_signature
        return attrs

    def save(self, **kwargs):
        repository = self.context["soi_repository"]
        actor_id = self.context["actor_id"]
        vessel_id = self.context["vessel_id"]
        try:
            return repository.decide_applicability_request(
                vessel_id=str(vessel_id),
                area_id=int(self.validated_data["area_id"]),
                actor_id=actor_id,
                dpa_signature=self.validated_data["dpa_signature"],
                dpa_decision=self.validated_data["dpa_decision"],
                decision_note=self.validated_data["reason"],
            )
        except ValueError as exc:
            raise serializers.ValidationError({"non_field_errors": [str(exc)]}) from exc


class SOICrewSnapshotSerializer(serializers.Serializer):
    crew_id = serializers.CharField()
    vessel_id = serializers.CharField()
    department = serializers.CharField()
    rank = serializers.CharField()
    crew_name = serializers.CharField(required=False, allow_blank=True)


class SOICreateConfigSerializer(serializers.Serializer):
    areas = SOIApplicabilitySerializer(many=True)
    assistant_candidates = SOICrewSnapshotSerializer(many=True)
    checklist_version = SOIChecklistVersionSerializer(allow_null=True)
    max_trainees = serializers.IntegerField()
    responsible_candidates = SOICrewSnapshotSerializer(many=True)
    section_12_status = serializers.DictField()
    safety_officer = SOICrewSnapshotSerializer(allow_null=True)
    trainee_candidates = SOICrewSnapshotSerializer(many=True)


class SOIOfficerSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SOIOfficerSetting
        fields = (
            "id",
            "id",
            "vessel_id",
            "alternate_enabled",
            "alternate_so_crew_id",
            "reason",
            "enabled_by",
            "enabled_at",
            "disabled_by",
            "disabled_at",
            "schema_version",
            "updated_by",
            "updated_date",
        )
        read_only_fields = (
            "id",
            "vessel_id",
            "enabled_by",
            "enabled_at",
            "disabled_by",
            "disabled_at",
            "schema_version",
            "updated_by",
            "updated_date",
        )


class SOIOfficerSettingUpdateSerializer(serializers.Serializer):
    alternate_enabled = serializers.BooleanField()
    alternate_so_crew_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=64)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        if attrs["alternate_enabled"] and not str(attrs.get("alternate_so_crew_id") or "").strip():
            raise serializers.ValidationError(
                {"alternate_so_crew_id": "Select the active 2/E before enabling alternate Safety Officer."}
            )
        return attrs


class SOISection12StatusSerializer(serializers.Serializer):
    vessel_id = serializers.CharField()
    cycle_label = serializers.CharField()
    cycle_start = serializers.DateField()
    cycle_end = serializers.DateField()
    covered_this_cycle = serializers.BooleanField()
    prompt_required = serializers.BooleanField()
    next_allowed_date = serializers.DateField(allow_null=True)
    covered_by_inspection_id = serializers.CharField(allow_null=True)
    covered_by_inspection_reference = serializers.CharField(allow_null=True)
    covered_planned_date = serializers.DateField(allow_null=True)


class SOIComplianceAreaSerializer(serializers.Serializer):
    area_id = serializers.IntegerField()
    area_name = serializers.CharField(allow_null=True)
    section_12_flag = serializers.BooleanField()
    status = serializers.CharField()
    last_inspected_at = serializers.DateTimeField(allow_null=True)
    due_at = serializers.DateTimeField(allow_null=True)
    days_since_last_inspection = serializers.IntegerField(allow_null=True)
    days_until_due = serializers.IntegerField(allow_null=True)
    days_overdue = serializers.IntegerField(allow_null=True)


class SOIComplianceSerializer(serializers.Serializer):
    label = serializers.CharField()
    vessel_id = serializers.CharField()
    calculated_at = serializers.DateTimeField()
    status = serializers.CharField()
    compliance_percent = serializers.IntegerField(allow_null=True)
    display_value = serializers.CharField()
    applicable_area_count = serializers.IntegerField()
    inspected_area_count = serializers.IntegerField()
    amber_area_count = serializers.IntegerField()
    overdue_area_count = serializers.IntegerField()
    areas = SOIComplianceAreaSerializer(many=True)


class SOICrewRotationCrewSerializer(serializers.Serializer):
    crew_id = serializers.CharField()
    inspections_accompanied = serializers.IntegerField()


class SOICrewRotationCoverageSerializer(serializers.Serializer):
    vessel_id = serializers.CharField()
    window_days = serializers.IntegerField()
    window_start = serializers.DateTimeField()
    window_end = serializers.DateTimeField()
    total_active_crew = serializers.IntegerField()
    accompanied_crew_count = serializers.IntegerField()
    coverage_percent = serializers.IntegerField(allow_null=True)
    display_value = serializers.CharField()
    crew = SOICrewRotationCrewSerializer(many=True)


class SOIFindingSummarySerializer(serializers.Serializer):
    total_count = serializers.IntegerField()
    open_count = serializers.IntegerField()
    master_approved_count = serializers.IntegerField()
    pending_closure_count = serializers.IntegerField()
    closed_count = serializers.IntegerField()
    carried_forward_count = serializers.IntegerField()


class SOIDigitalSignatureSnapshotSerializer(serializers.Serializer):
    signer_display_name = serializers.CharField()
    signed_at = serializers.DateTimeField()
    device_fingerprint_last8 = serializers.CharField()


class SOICloseSnapshotSerializer(serializers.Serializer):
    inspection_id = serializers.CharField()
    vessel_id = serializers.CharField()
    inspection_reference = serializers.CharField()
    checklist_unique_id = serializers.CharField(allow_null=True)
    planned_date = serializers.DateField()
    state = serializers.CharField()
    closed_at = serializers.DateTimeField(allow_null=True)
    selected_areas = SOIInspectionAreaSerializer(many=True)
    trainees = SOITraineeSerializer(many=True)
    finding_summary = SOIFindingSummarySerializer()
    crew_rotation = SOICrewRotationCoverageSerializer()
    signature = SOIDigitalSignatureSnapshotSerializer(allow_null=True)


class SOIClosePayloadSerializer(serializers.Serializer):
    typed_name = serializers.CharField(allow_blank=False, trim_whitespace=True)
    device_fingerprint = serializers.CharField(allow_blank=False, trim_whitespace=True)


class SOIDownloadQuerySerializer(serializers.Serializer):
    format = serializers.CharField(required=False, default="PDF")

    def validate_format(self, value):
        normalized = str(value or "").strip().upper()
        if normalized not in {"PDF", "XLSX"}:
            raise serializers.ValidationError("SOI checklist downloads only support PDF or XLSX.")
        return normalized


class SOIReprintRequestSerializer(serializers.Serializer):
    format = serializers.CharField(required=False, default="PDF")
    reason = serializers.CharField(allow_blank=True)

    def validate_format(self, value):
        normalized = str(value or "").strip().upper()
        if normalized not in {"PDF", "XLSX"}:
            raise serializers.ValidationError("SOI checklist downloads only support PDF or XLSX.")
        return normalized

    def validate_reason(self, value):
        normalized = str(value).strip()
        if not normalized:
            raise serializers.ValidationError("Lost-paper recovery requires a reason.")
        return normalized


class SOIPickAreasSerializer(serializers.Serializer):
    inspection_id = serializers.CharField()
    vessel_id = serializers.CharField()
    section_12_included = serializers.BooleanField()
    section_12_status = SOISection12StatusSerializer()
    available_areas = SOIApplicabilitySerializer(many=True)
    selected_areas = SOIInspectionAreaSerializer(many=True)


class SOIPickAreasUpdateSerializer(serializers.Serializer):
    area_ids = serializers.ListField(child=serializers.IntegerField(min_value=1))
    section_12_included = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        inspection = self.context["inspection"]
        attrs["area_ids"] = _validate_area_selection(
            repository=self.context["soi_repository"],
            vessel_id=str(inspection.vessel_id),
            area_ids=list(attrs.get("area_ids") or []),
            section_12_included=bool(attrs.get("section_12_included", False)),
            section12_cycle_enforcer=self.context["section12_cycle_enforcer"],
            at_date=inspection.planned_date,
            exclude_inspection_id=inspection.id,
        )
        return attrs

    def save(self, **kwargs):
        repository = self.context["soi_repository"]
        inspection_id = kwargs["inspection_id"]
        return repository.replace_selected_areas(
            inspection_id=inspection_id,
            area_ids=list(self.validated_data["area_ids"]),
            section_12_included=bool(self.validated_data.get("section_12_included", False)),
        )


class SOITraineePayloadSerializer(serializers.Serializer):
    inspection_id = serializers.CharField()
    trainees = SOITraineeSerializer(many=True)


class SOITraineeUpdateSerializer(serializers.Serializer):
    trainee_crew_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )

    def validate(self, attrs):
        inspection = self.context["inspection"]
        validator = self.context["assistant_validator"]
        attrs["trainee_crew_ids"] = validator.validate_trainees(
            vessel_id=str(inspection.vessel_id),
            trainee_crew_ids=_validate_trainee_ids(list(attrs.get("trainee_crew_ids") or [])),
            safety_officer_crew_id=str(inspection.safety_officer_crew_id),
            assistant_crew_id=str(inspection.assistant_crew_id),
            active_on=inspection.planned_date,
        )
        return attrs

    def save(self, **kwargs):
        repository = self.context["soi_repository"]
        inspection_id = kwargs["inspection_id"]
        return repository.replace_trainees(
            inspection_id=inspection_id,
            trainee_crew_ids=list(self.validated_data.get("trainee_crew_ids") or []),
        )


class SOIApplicabilityUpdateSerializer(serializers.Serializer):
    vessel_id = serializers.CharField()
    area_id = serializers.IntegerField(min_value=1)
    applicable = serializers.BooleanField(required=False)
    reason = serializers.CharField()
    master_signature = serializers.CharField(required=False, allow_blank=True)
    dpa_approved_by = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    dpa_signature = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    dpa_decision = serializers.ChoiceField(
        choices=["APPROVED", "REJECTED"],
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        reason = str(attrs.get("reason") or "").strip()
        if not reason:
            raise serializers.ValidationError({"reason": "Applicability changes require a reason."})

        normalized_decision = attrs.get("dpa_decision")
        if normalized_decision not in (None, ""):
            dpa_signature = str(attrs.get("dpa_signature") or "").strip()
            if not dpa_signature:
                raise serializers.ValidationError({"dpa_signature": "DPA signature is required."})
            attrs["dpa_signature"] = dpa_signature
        else:
            if "applicable" not in attrs:
                raise serializers.ValidationError({"applicable": "Applicability request must include the requested state."})
            master_signature = str(attrs.get("master_signature") or "").strip()
            if not master_signature:
                raise serializers.ValidationError({"master_signature": "Master signature is required."})
            if len(reason) < 100:
                raise serializers.ValidationError({"reason": "Applicability request reason must be at least 100 characters."})
            attrs["master_signature"] = master_signature

        attrs["reason"] = reason
        return attrs

    def save(self, **kwargs):
        repository = self.context["soi_repository"]
        actor_id = self.context["actor_id"]
        payload = dict(self.validated_data)
        dpa_decision = payload.get("dpa_decision")
        if dpa_decision not in (None, ""):
            try:
                return repository.decide_applicability_request(
                    vessel_id=str(payload["vessel_id"]),
                    area_id=int(payload["area_id"]),
                    actor_id=actor_id,
                    dpa_signature=str(payload.get("dpa_signature") or ""),
                    dpa_decision=str(dpa_decision),
                    decision_note=str(payload["reason"]),
                )
            except ValueError as exc:
                raise serializers.ValidationError({"non_field_errors": [str(exc)]}) from exc

        try:
            return repository.create_applicability_request(
                vessel_id=str(payload["vessel_id"]),
                area_id=int(payload["area_id"]),
                new_applicable=bool(payload["applicable"]),
                actor_id=actor_id,
                reason=str(payload["reason"]),
                master_signature=str(payload.get("master_signature") or ""),
            )
        except ValueError as exc:
            raise serializers.ValidationError({"non_field_errors": [str(exc)]}) from exc
