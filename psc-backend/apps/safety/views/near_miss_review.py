from __future__ import annotations

import json

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasAnyProcessPermission
from apps.safety.models import (
    Incident,
    IncidentPhaseLog,
    MasterLossType,
    MasterMscatTaxonomy,
    MasterSafetyIncidentType,
    NearMissCauseOption,
    SafetyFieldHistory,
)
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.serializers import NearMissSerializer, PhaseLogSerializer
from apps.safety.serializers.near_miss import NEAR_MISS_OTHER_CATEGORY, NEAR_MISS_OTHER_PREFIX, resolve_near_miss_category
from apps.safety.services import NotificationWriter, capture_model_state, record_field_changes
from apps.safety.services.near_miss_numbering import formalize_near_miss_number_for_office
from apps.safety.services.signature_chain import SignatureChainService
from apps.safety.views.near_miss import NearMissViewMixin, _is_master_user, _normalized_role, _resolve_actor_id


VESSEL_REVIEW_ROLES = {
    "MASTER",
    "CAPTAIN",
    "CO",
    "CE",
    "HOD",
    "CHIEF OFFICER",
    "CHIEF ENGINEER",
    "HEAD OF DEPARTMENT",
}
HOD_REVIEW_FIELD = "near_miss_hod_review_signature"
VESSEL_REVIEW_FIELD = "near_miss_vessel_review_signature"
REWORK_RESUBMISSION_FIELD = "near_miss_rework_resubmission"

ENGINE_HOD_ROLES = {"CE", "CHIEF ENGINEER"}
DECK_HOD_ROLES = {"CO", "CHIEF OFFICER"}
MASTER_ROLES = {"MASTER", "CAPTAIN"}


class NearMissReviewActionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=("SUBMIT_TO_OFFICE", "SEND_BACK"))
    comment = serializers.CharField(allow_blank=True, required=False, trim_whitespace=True)
    typed_name = serializers.CharField(allow_blank=False, trim_whitespace=True)
    device_fingerprint = serializers.CharField(allow_blank=False, trim_whitespace=True)

    def validate(self, attrs):
        decision = str(attrs["decision"]).strip().upper()
        comment = str(attrs.get("comment") or "").strip()
        if decision == "SEND_BACK" and not comment:
            raise serializers.ValidationError({"comment": "Rework requires reviewer comments."})
        attrs["decision"] = decision
        attrs["comment"] = comment
        return attrs


class NearMissReworkSubmitSerializer(serializers.Serializer):
    comment = serializers.CharField(allow_blank=False, trim_whitespace=True)
    incident_type_id = serializers.IntegerField(required=True)
    loss_type_primary_id = serializers.IntegerField(required=True)
    narrative = serializers.CharField(allow_blank=False, trim_whitespace=True)
    near_miss_immediate_action = serializers.CharField(allow_blank=False, trim_whitespace=True)
    near_miss_place = serializers.ChoiceField(choices=("AT_ANCHOR", "AT_SEA", "AT_PORT"), required=False, allow_null=True)
    near_miss_category_tags = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True, max_length=3)
    near_miss_incident_type_ids = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=True, max_length=3)
    near_miss_mscat_subcode_ids = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True, max_length=3)
    near_miss_factor_causes = serializers.ListField(child=serializers.DictField(), required=True, allow_empty=False)
    near_miss_severity = serializers.ChoiceField(choices=("HIGH", "MED", "LOW"))
    near_miss_shell_tag = serializers.CharField(required=False, allow_blank=True, allow_null=True, trim_whitespace=True)
    near_miss_suggestion = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    near_miss_root_cause_detail = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    near_miss_corrective_action = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    near_miss_weather_voyage_details = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    near_miss_equipment_details = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    near_miss_lessons_learned = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    occurred_at = serializers.DateTimeField(required=True)
    reporter_device_fingerprint = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)

    def validate_narrative(self, value: str) -> str:
        if len(value.strip()) < 100:
            raise serializers.ValidationError(
                "Near-miss description must be at least 100 characters (D-GAP-M38)."
            )
        return value

    def validate(self, attrs):
        incident_type_ids = self._clean_int_list(
            [attrs["incident_type_id"], *(attrs.get("near_miss_incident_type_ids") or [])]
        )
        incident_types = MasterSafetyIncidentType.objects.filter(
            legacy_int_id__in=incident_type_ids,
            active=True,
        )
        active_type_ids = {row.legacy_int_id for row in incident_types}
        missing_types = [type_id for type_id in incident_type_ids if type_id not in active_type_ids]
        if missing_types:
            raise serializers.ValidationError({"incident_type_id": "Select a valid Safety incident type."})
        attrs["incident_type_id"] = incident_type_ids[0]
        attrs["near_miss_incident_type_ids"] = incident_type_ids[:3]

        if not MasterLossType.objects.filter(loss_type_id=attrs["loss_type_primary_id"], active=True).exists():
            raise serializers.ValidationError({"loss_type_primary_id": "Select a valid Safety loss type."})

        category_tags = self._clean_text_list(attrs.get("near_miss_category_tags") or [])
        shell_tag = str(attrs.get("near_miss_shell_tag") or "").strip()
        if shell_tag and shell_tag not in category_tags:
            category_tags.insert(0, shell_tag)
        normalized_category_tags = []
        for tag in category_tags:
            normalized = resolve_near_miss_category(tag)
            if normalized is None:
                raise serializers.ValidationError({"near_miss_category_tags": "Category must match the Safety SSOT values."})
            normalized_category_tags.append(normalized)
        category_tags = normalized_category_tags
        attrs["near_miss_category_tags"] = category_tags[:3]
        first_category = attrs["near_miss_category_tags"][0] if attrs["near_miss_category_tags"] else None
        attrs["near_miss_shell_tag"] = (
            NEAR_MISS_OTHER_CATEGORY
            if first_category and first_category.startswith(NEAR_MISS_OTHER_PREFIX)
            else first_category
        )

        attrs["near_miss_factor_causes"] = self._validate_factor_causes(attrs.get("near_miss_factor_causes") or [])
        attrs["near_miss_mscat_subcode_id"] = None
        attrs["near_miss_mscat_category_id"] = None
        attrs["near_miss_mscat_subcode_ids"] = []

        occurred_at = attrs["occurred_at"]
        if occurred_at > timezone.now():
            raise serializers.ValidationError({"occurred_at": "Occurred time cannot be in the future."})
        return attrs

    def _clean_int_list(self, values: list[object]) -> list[int]:
        cleaned: list[int] = []
        seen: set[int] = set()
        for value in values:
            try:
                normalized = int(value)
            except (TypeError, ValueError):
                continue
            if normalized > 0 and normalized not in seen:
                cleaned.append(normalized)
                seen.add(normalized)
        if not cleaned:
            raise serializers.ValidationError({"incident_type_id": "This field is required."})
        return cleaned[:3]

    def _clean_text_list(self, values: list[object]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized = str(value or "").strip()
            if normalized and normalized not in seen:
                cleaned.append(normalized)
                seen.add(normalized)
        return cleaned[:3]

    def _validate_factor_causes(self, rows: list[dict]) -> list[dict]:
        required_factors = {choice[0] for choice in NearMissCauseOption.Factor.choices}
        cleaned_by_factor: dict[str, dict] = {}
        option_ids: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                raise serializers.ValidationError({"near_miss_factor_causes": "Each cause row must be an object."})
            factor = str(row.get("factor") or "").strip().upper()
            if factor not in required_factors:
                raise serializers.ValidationError({"near_miss_factor_causes": "Select a valid near-miss factor."})
            cleaned = {"factor": factor}
            for stage in ("immediate", "root"):
                option_id = str(row.get(f"{stage}_option_id") or "").strip()
                if not option_id:
                    raise serializers.ValidationError({"near_miss_factor_causes": "Select immediate and root causes for every factor."})
                cleaned[f"{stage}_option_id"] = option_id
                cleaned[f"{stage}_other_text"] = str(row.get(f"{stage}_other_text") or "").strip()
                option_ids.add(option_id)
            cleaned_by_factor[factor] = cleaned
        if set(cleaned_by_factor) != required_factors:
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
                if option.option_text.strip().lower() in {"other", "others"}:
                    if not cleaned[f"{stage}_other_text"]:
                        raise serializers.ValidationError({"near_miss_factor_causes": "Specify the cause when Other is selected."})
                else:
                    cleaned[f"{stage}_other_text"] = ""
        return [cleaned_by_factor[factor] for factor in sorted(cleaned_by_factor)]


class NearMissReviewView(NearMissViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = NearMissReviewActionSerializer
    review_permission_class = HasAnyProcessPermission.requiring_any("SAF_P_002", "SAF_P_006")
    notification_writer_class = NotificationWriter
    signature_service_class = SignatureChainService

    def get_permissions(self):
        return [self.form_permission_class(), self.review_permission_class()]

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_notification_writer(self) -> NotificationWriter:
        return self.notification_writer_class()

    def get_signature_service(self) -> SignatureChainService:
        return self.signature_service_class()

    def get_near_miss(self) -> Incident:
        near_miss = get_by_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])
        if near_miss.record_type != Incident.RecordType.NEAR_MISS:
            raise ValidationError("Vessel review is only available for near-miss records.")
        if near_miss.state in {Incident.State.CLOSED, Incident.State.SUPERSEDED}:
            raise ValidationError("Closed or superseded near misses cannot be reviewed.")
        return near_miss

    def _enforce_vessel_reviewer_role(self) -> None:
        if _normalized_role(self.request.user) not in VESSEL_REVIEW_ROLES:
            raise PermissionDenied("Near-miss vessel review is restricted to Master, HOD, CO, or CE.")

    def _department_route(self, near_miss: Incident) -> str:
        department = str(near_miss.reporter_department or "").strip().upper()
        if "ENGINE" in department or department in {"TECHNICAL", "ELECTRICAL"}:
            return "ENGINE"
        if "DECK" in department or "MARINE" in department:
            return "DECK"

        text = " ".join(
            value
            for value in (
                near_miss.near_miss_shell_tag,
                near_miss.narrative,
                near_miss.near_miss_immediate_action,
                near_miss.near_miss_suggestion,
            )
            if value
        ).lower()
        if any(marker in text for marker in ("engine", "machinery", "generator", "purifier", "boiler", "pump", "compressor")):
            return "ENGINE"
        if any(marker in text for marker in ("deck", "mooring", "cargo", "navigation", "bridge", "anchor", "gangway")):
            return "DECK"
        return "GENERAL"

    def _has_hod_review(self, near_miss: Incident) -> bool:
        queryset = SafetyFieldHistory.objects.filter(
            parent_table=near_miss._meta.db_table,
            parent_id=near_miss.pk,
            field_name=HOD_REVIEW_FIELD,
        )
        latest_rework_resubmission = (
            SafetyFieldHistory.objects.filter(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name=REWORK_RESUBMISSION_FIELD,
            )
            .order_by("-changed_at", "-id")
            .first()
        )
        if latest_rework_resubmission is not None:
            queryset = queryset.filter(changed_at__gt=latest_rework_resubmission.changed_at)
        return queryset.exists()

    def _record_review_signature(
        self,
        *,
        near_miss: Incident,
        signature,
        actor_id: str,
        actor_role: str,
        decision: str,
        comment: str,
        field_name: str,
    ) -> None:
        SafetyFieldHistory.objects.create(
            parent_table=near_miss._meta.db_table,
            parent_id=near_miss.pk,
            field_name=field_name,
            old_value=None,
            new_value={
                "typed_name": signature.typed_name,
                "signed_at": signature.signed_at.isoformat(),
                "device_fingerprint": signature.device_fingerprint,
                "signed_by": actor_id,
                "signed_role": actor_role,
                "decision": decision,
            },
            change_reason=comment or f"Near-miss vessel review decision: {decision}.",
            actor_user_id=actor_id,
            actor_role_code=actor_role,
            schema_version=near_miss.schema_version or 1,
        )

    def _handle_hod_review(self, *, near_miss, signature, actor_id, actor_role, decision, comment):
        route = self._department_route(near_miss)
        if decision != "SUBMIT_TO_OFFICE":
            return None

        if route == "ENGINE" and actor_role in ENGINE_HOD_ROLES:
            next_required_review = "MASTER"
        elif route == "DECK" and actor_role in DECK_HOD_ROLES:
            next_required_review = "MASTER"
        else:
            return None

        self._record_review_signature(
            near_miss=near_miss,
            signature=signature,
            actor_id=actor_id,
            actor_role=actor_role,
            decision=decision,
            comment=comment,
            field_name=HOD_REVIEW_FIELD,
        )
        phase_log = IncidentPhaseLog.objects.create(
            incident=near_miss,
            phase_from=near_miss.current_phase,
            phase_to=near_miss.current_phase,
            transition_type=IncidentPhaseLog.TransitionType.FORWARD,
            loop_back_reason=comment or f"{route} HOD review completed; awaiting Master review.",
            actor_user_id=actor_id,
            actor_role_code=actor_role,
            device_fingerprint=signature.device_fingerprint,
            signature_valid=True,
            schema_version=near_miss.schema_version or 1,
        )
        self.get_notification_writer().dispatch_notification(
            record_id=near_miss.pk,
            recipients=["MASTER"],
            kind="NEAR_MISS_HOD_REVIEW_COMPLETE",
            title="Near miss ready for Master review",
            message=f"{route} HOD reviewed near miss {near_miss.incident_number}. Master review is required before office comments.",
            payload={"near_miss_id": near_miss.pk, "state": near_miss.state, "route": route},
            send_slack=True,
        )
        payload = NearMissSerializer(near_miss, context=self.get_serializer_context()).data
        payload["review_phase_log"] = PhaseLogSerializer(phase_log).data
        payload["review_signature"] = {
            "typed_name": signature.typed_name,
            "signed_at": signature.signed_at,
            "device_fingerprint": signature.device_fingerprint,
            "signed_by": actor_id,
            "signed_role": actor_role,
        }
        payload["next_required_review"] = next_required_review
        payload["review_route"] = route
        return Response(payload, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        near_miss = self.get_near_miss()
        self._enforce_vessel_reviewer_role()
        if near_miss.state != Incident.State.PENDING_VESSEL_REVIEW:
            raise ValidationError("Near miss is not awaiting vessel-side review.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        actor_id = _resolve_actor_id(request.user)
        actor_role = _normalized_role(request.user) or "VESSEL_REVIEWER"
        decision = serializer.validated_data["decision"]
        comment = serializer.validated_data["comment"]
        signature = self.get_signature_service().validate_payload(
            typed_name=serializer.validated_data["typed_name"],
            device_fingerprint=serializer.validated_data["device_fingerprint"],
        )
        hod_response = self._handle_hod_review(
            near_miss=near_miss,
            signature=signature,
            actor_id=actor_id,
            actor_role=actor_role,
            decision=decision,
            comment=comment,
        )
        if hod_response is not None:
            return hod_response

        route = self._department_route(near_miss)
        if decision == "SUBMIT_TO_OFFICE":
            if route in {"ENGINE", "DECK"} and actor_role not in MASTER_ROLES:
                required = "Chief Engineer" if route == "ENGINE" else "Chief Officer"
                raise ValidationError(f"{route.title()} near miss requires {required} review, then Master review.")
            if route in {"ENGINE", "DECK"} and not self._has_hod_review(near_miss):
                required = "Chief Engineer" if route == "ENGINE" else "Chief Officer"
                raise ValidationError(f"{route.title()} near miss requires {required} review before Master submits to office.")
            if route == "GENERAL" and actor_role not in MASTER_ROLES:
                raise ValidationError("General near miss requires Master review before office comments.")

        next_state = (
            Incident.State.READY_FOR_OFFICE_COMMENTS
            if decision == "SUBMIT_TO_OFFICE"
            else Incident.State.REWORK_REQUIRED
        )
        with transaction.atomic():
            old_state = capture_model_state(
                near_miss,
                field_names=("incident_number", "state", "updated_by", "updated_date"),
            )
            near_miss.state = next_state
            near_miss.updated_by = actor_id
            near_miss.updated_date = timezone.now()
            update_fields = ["state", "updated_by", "updated_date"]
            if formalize_near_miss_number_for_office(
                near_miss,
                repository=self.get_incident_repository(),
            ):
                update_fields.append("incident_number")
            near_miss.save(update_fields=tuple(update_fields))
            record_field_changes(
                near_miss,
                old_state,
                user=request.user,
                field_names=tuple(update_fields),
                change_reason=comment or f"Near-miss vessel review decision: {decision}.",
            )
            phase_log = IncidentPhaseLog.objects.create(
                incident=near_miss,
                phase_from=near_miss.current_phase,
                phase_to=near_miss.current_phase,
                transition_type=(
                    IncidentPhaseLog.TransitionType.REWORK
                    if decision == "SEND_BACK"
                    else IncidentPhaseLog.TransitionType.FORWARD
                ),
                loop_back_reason=comment or f"Near-miss vessel review decision: {decision}.",
                actor_user_id=actor_id,
                actor_role_code=actor_role,
                device_fingerprint=signature.device_fingerprint,
                signature_valid=True,
                schema_version=near_miss.schema_version or 1,
            )
            self._record_review_signature(
                near_miss=near_miss,
                signature=signature,
                actor_id=actor_id,
                actor_role=actor_role,
                decision=decision,
                comment=comment,
                field_name=VESSEL_REVIEW_FIELD,
            )
        if decision == "SEND_BACK":
            self.get_notification_writer().dispatch_notification(
                record_id=near_miss.pk,
                recipients=["MASTER"],
                kind="NEAR_MISS_REWORK_REQUIRED",
                title="Near miss sent back for rework",
                message=comment,
                payload={
                    "near_miss_id": near_miss.pk,
                    "incident_number": near_miss.incident_number,
                    "state": near_miss.state,
                },
                send_slack=True,
            )
        else:
            self.get_notification_writer().dispatch_notification(
                record_id=near_miss.pk,
                recipients=["DPA", "PIC", "SAFETY_CHANNEL"],
                kind="NEAR_MISS_READY_FOR_OFFICE_COMMENTS",
                title="Near miss ready for office comments",
                message=f"Near miss {near_miss.incident_number} completed vessel review.",
                payload={
                    "near_miss_id": near_miss.pk,
                    "incident_number": near_miss.incident_number,
                    "state": near_miss.state,
                },
                send_slack=True,
            )

        payload = NearMissSerializer(near_miss, context=self.get_serializer_context()).data
        payload["review_phase_log"] = PhaseLogSerializer(phase_log).data
        payload["review_signature"] = {
            "typed_name": signature.typed_name,
            "signed_at": signature.signed_at,
            "device_fingerprint": signature.device_fingerprint,
            "signed_by": actor_id,
            "signed_role": actor_role,
        }
        return Response(payload, status=status.HTTP_200_OK)


class NearMissReworkSubmitView(NearMissViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = NearMissReworkSubmitSerializer
    rework_permission_class = NearMissViewMixin.process_permission_class.requiring("SAF_P_001")
    rework_update_fields = (
        "incident_type_id",
        "loss_type_primary_id",
        "narrative",
        "near_miss_priority",
        "near_miss_immediate_action",
        "near_miss_place",
        "near_miss_category_tags",
        "near_miss_incident_type_ids",
        "near_miss_mscat_category_id",
        "near_miss_mscat_subcode_id",
        "near_miss_mscat_subcode_ids",
        "near_miss_factor_causes",
        "near_miss_severity",
        "near_miss_shell_tag",
        "near_miss_suggestion",
        "near_miss_root_cause_detail",
        "near_miss_corrective_action",
        "near_miss_weather_voyage_details",
        "near_miss_equipment_details",
        "near_miss_lessons_learned",
        "occurred_at",
        "reporter_device_fingerprint",
    )

    def get_permissions(self):
        return [self.form_permission_class(), self.rework_permission_class()]

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def post(self, request, *args, **kwargs):
        near_miss = get_by_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])
        if near_miss.record_type != Incident.RecordType.NEAR_MISS:
            raise ValidationError("Rework is only available for near-miss records.")
        if near_miss.state not in {Incident.State.REWORK_REQUIRED, Incident.State.REJECTED}:
            raise ValidationError("Near miss is not awaiting reporter rework.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor_id = _resolve_actor_id(request.user)
        actor_role = _normalized_role(request.user) or "REPORTER"
        with transaction.atomic():
            old_state = capture_model_state(
                near_miss,
                field_names=(
                    *self.rework_update_fields,
                    "incident_number",
                    "state",
                    "updated_by",
                    "updated_date",
                ),
            )
            self._apply_rework_updates(near_miss, serializer.validated_data)
            near_miss.state = (
                Incident.State.READY_FOR_OFFICE_COMMENTS
                if _is_master_user(request.user)
                else Incident.State.PENDING_VESSEL_REVIEW
            )
            near_miss.updated_by = actor_id
            near_miss.updated_date = timezone.now()
            update_fields = [*self.rework_update_fields, "state", "updated_by", "updated_date"]
            if formalize_near_miss_number_for_office(
                near_miss,
                repository=self.get_incident_repository(),
            ):
                update_fields.append("incident_number")
            near_miss.save(update_fields=tuple(update_fields))
            record_field_changes(
                near_miss,
                old_state,
                user=request.user,
                field_names=tuple(update_fields),
                change_reason=serializer.validated_data["comment"],
            )
            SafetyFieldHistory.objects.create(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name=REWORK_RESUBMISSION_FIELD,
                old_value=None,
                new_value={
                    "comment": serializer.validated_data["comment"],
                    "submitted_by": actor_id,
                    "submitted_role": actor_role,
                },
                change_reason=serializer.validated_data["comment"],
                actor_user_id=actor_id,
                actor_role_code=actor_role,
                schema_version=near_miss.schema_version or 1,
            )
            phase_log = IncidentPhaseLog.objects.create(
                incident=near_miss,
                phase_from=near_miss.current_phase,
                phase_to=near_miss.current_phase,
                transition_type=IncidentPhaseLog.TransitionType.REWORK,
                loop_back_reason=serializer.validated_data["comment"],
                actor_user_id=actor_id,
                actor_role_code=actor_role,
                device_fingerprint=getattr(near_miss, "reporter_device_fingerprint", None),
                schema_version=near_miss.schema_version or 1,
            )
        payload = NearMissSerializer(near_miss, context=self.get_serializer_context()).data
        payload["rework_phase_log"] = PhaseLogSerializer(phase_log).data
        return Response(payload, status=status.HTTP_200_OK)

    def _apply_rework_updates(self, near_miss: Incident, data: dict[str, object]) -> None:
        for field_name in self.rework_update_fields:
            if field_name == "near_miss_priority":
                severity_priority = {
                    "HIGH": "HIGH",
                    "MED": "MEDIUM",
                    "LOW": "LOW",
                }.get(str(data.get("near_miss_severity") or "").strip().upper())
                setattr(near_miss, field_name, severity_priority)
                continue
            if field_name in {
                "near_miss_category_tags",
                "near_miss_incident_type_ids",
                "near_miss_mscat_subcode_ids",
                "near_miss_factor_causes",
            }:
                setattr(near_miss, field_name, json.dumps(data.get(field_name) or [], separators=(",", ":")))
            else:
                setattr(near_miss, field_name, data.get(field_name))
