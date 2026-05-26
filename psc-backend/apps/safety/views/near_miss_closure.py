from __future__ import annotations

from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from apps.safety.authentication.anonymity import MASKED_NULL_FIELDS, can_see_reporter
from apps.safety.authentication.permissions import HasAnyProcessPermission, HasProcessPermission
from apps.safety.models import Incident, IncidentPhaseLog, SafetyFieldHistory
from apps.safety.identifiers import get_by_id_or_pk
from apps.safety.serializers import FieldHistorySerializer, NearMissListSerializer, NearMissSerializer, PhaseLogSerializer
from apps.safety.services import FleetAlertIssuer, capture_model_state, record_field_changes
from apps.safety.services.field_history_recorder import resolve_actor_id
from apps.safety.services.self_report_guard import check_self_report_conflict
from apps.safety.views.near_miss import NearMissViewMixin, _normalized_role


NEAR_MISS_AUDIT_RESTRICTED_FIELDS = frozenset(
    {
        "reporter_id",
        "reporter_name",
        "reporter_rank",
        "reporter_email",
        "reporter_department",
        "reporter_device_fingerprint",
        *MASKED_NULL_FIELDS,
    }
)

HIGH_PRIORITY_CLOSE_ROLES = {"DPA", "FM", "FLEET MANAGER"}
LOW_PRIORITY_CLOSE_ROLES = {
    "MASTER",
    "CAPTAIN",
    "DPA",
    "FM",
    "FLEET MANAGER",
    "PIC",
    "OFFICE_PIC",
    "OFFICE_SSQE",
    "OFFICE_SUPT",
}


def _filtered_field_history_queryset(near_miss: Incident, *, user):
    queryset = SafetyFieldHistory.objects.filter(
        parent_table=near_miss._meta.db_table,
        parent_id=near_miss.pk,
    ).order_by("changed_at", "id")
    if can_see_reporter(user, near_miss):
        return queryset
    return queryset.exclude(field_name__in=NEAR_MISS_AUDIT_RESTRICTED_FIELDS)


def build_near_miss_pdf_payload(near_miss: Incident, *, user) -> dict[str, object]:
    return NearMissSerializer(near_miss, context={"user": user}).data


def build_near_miss_search_payload(near_miss: Incident, *, user) -> dict[str, object]:
    return NearMissListSerializer(near_miss, context={"user": user}).data


class NearMissClosureActionSerializer(serializers.Serializer):
    closure_reason = serializers.CharField(allow_blank=False)
    near_miss_suggestion = serializers.CharField(required=False, allow_blank=True)
    preventive_measure_due_date = serializers.DateField(required=False, allow_null=True)
    preventive_measure_owner = serializers.CharField(required=False, allow_blank=True)
    preventive_measure_status = serializers.ChoiceField(
        choices=("OPEN", "IN_PROGRESS", "CLOSED"),
        required=False,
        allow_blank=True,
    )
    typed_name = serializers.CharField()
    device_fingerprint = serializers.CharField()
    conflict_acknowledged = serializers.BooleanField(required=False, default=False)
    conflict_approver_role = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        incident: Incident = self.context["incident"]
        user = self.context["user"]

        typed_name = (attrs.get("typed_name") or "").strip()
        device_fingerprint = (attrs.get("device_fingerprint") or "").strip()
        if len(typed_name) < 3:
            raise serializers.ValidationError(
                {"typed_name": "Near-miss closure signature requires the typed full name."}
            )
        if not device_fingerprint:
            raise serializers.ValidationError(
                {"device_fingerprint": "Near-miss closure signature requires a device fingerprint."}
            )

        if incident.record_type != Incident.RecordType.NEAR_MISS:
            raise serializers.ValidationError("Near-miss closure is only available for near-miss records.")
        if incident.state == "CLOSED":
            raise serializers.ValidationError("Near-miss record is already closed.")
        if incident.state == "SUPERSEDED" or incident.superseded_by_id:
            raise serializers.ValidationError(
                "Superseded near-miss records must continue in the incident workflow instead of closing here."
            )
        if incident.state != "TRIAGED":
            raise serializers.ValidationError("Near-miss record must be triaged before closure.")

        conflict = check_self_report_conflict(
            incident.reporter_id,
            {"pic_user_id": resolve_actor_id(user), "reporter_rank": incident.reporter_rank},
            user=user,
            reporter_rank=incident.reporter_rank,
        )
        if conflict.conflict_detected:
            if not attrs.get("conflict_acknowledged"):
                raise serializers.ValidationError(
                    {
                        "conflict_acknowledged": [
                            "Acknowledge the self-report conflict before closing the near miss."
                        ],
                        "conflict_approver_role": [
                            f"Conflict detected - assign {conflict.required_approver_role} as the different approver."
                        ],
                    }
                )
            if attrs.get("conflict_approver_role") != conflict.required_approver_role:
                raise serializers.ValidationError(
                    {
                        "conflict_approver_role": [
                            f"Conflict detected - assign {conflict.required_approver_role} as the different approver."
                        ]
                    }
                )
        attrs["self_report_conflict"] = {
            "conflict_detected": conflict.conflict_detected,
            "required_approver_role": conflict.required_approver_role,
        }
        return attrs


class NearMissClosureView(NearMissViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)
    serializer_class = NearMissClosureActionSerializer
    close_permission_class = HasAnyProcessPermission.requiring_any("SAF_P_004", "SAF_P_006")
    fleet_alert_issuer_class = FleetAlertIssuer

    def get_permissions(self):
        permissions = [self.form_permission_class()]
        if self.request.method == "POST":
            permissions.append(self.close_permission_class())
        return permissions

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get_near_miss(self) -> Incident:
        near_miss = get_by_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])
        if near_miss.record_type != Incident.RecordType.NEAR_MISS:
            raise ValidationError("Near-miss closure is only available for near-miss records.")
        return near_miss

    def get_object(self):
        return self.get_near_miss()

    def _build_summary_payload(self, near_miss: Incident) -> dict[str, object]:
        phase_logs = IncidentPhaseLog.objects.filter(incident_id=near_miss.pk).order_by("occurred_at", "id")
        field_history = _filtered_field_history_queryset(near_miss, user=self.request.user)
        latest_phase_log = phase_logs.last()
        latest_field_change = field_history.last()
        return {
            "near_miss": NearMissSerializer(near_miss, context=self.get_serializer_context()).data,
            "audit_summary": {
                "phase_log_count": phase_logs.count(),
                "field_history_count": field_history.count(),
                "latest_phase_log": (
                    PhaseLogSerializer(latest_phase_log).data if latest_phase_log is not None else None
                ),
                "latest_field_change": (
                    FieldHistorySerializer(latest_field_change).data if latest_field_change is not None else None
                ),
            },
            "visibility_rule": (
                "Reporter identity remains masked for non-DPA/FM viewers across the near-miss summary and audit exits."
            ),
        }

    def _has_process_permission(self, process_id: str) -> bool:
        permission = HasProcessPermission.requiring(process_id)()
        return permission.has_permission(self.request, self)

    def _validate_close_contract(self, near_miss: Incident) -> None:
        actor_role = _normalized_role(self.request.user)
        if near_miss.near_miss_priority == "HIGH":
            fleet_alert_issuer = self.fleet_alert_issuer_class()
            fleet_alert_status = fleet_alert_issuer.build_status(near_miss, user=self.request.user)
            if actor_role not in HIGH_PRIORITY_CLOSE_ROLES:
                raise PermissionDenied("HIGH-priority near-miss closure is restricted to DPA or FM.")
            if not self._has_process_permission("SAF_P_004"):
                raise PermissionDenied("HIGH-priority near-miss closure requires SAF_P_004 approval authority.")
            preventive_fields_complete = all(
                (
                    (self.request.data.get("preventive_measure_owner") or "").strip(),
                    self.request.data.get("preventive_measure_due_date"),
                    self.request.data.get("preventive_measure_status"),
                )
            )
            if (
                not (near_miss.near_miss_suggestion or "").strip()
                or near_miss.facts.count() < 1
                or not fleet_alert_status.issued
                or fleet_alert_status.sla_status not in {"ISSUED_ON_TIME", "ISSUED_LATE_WITH_EXTENSION"}
                or not fleet_alert_issuer.get_fleet_learning_text(near_miss)
                or not preventive_fields_complete
            ):
                raise ValidationError(
                    {
                        "detail": (
                            "HIGH-priority near-miss requires full investigation "
                            "(causal analysis, preventive measures, fleet learning, fleet alert within 1 week) (D-GAP-R22)."
                        )
                    }
                )
            return

        if near_miss.near_miss_priority == "LOW":
            if actor_role not in LOW_PRIORITY_CLOSE_ROLES:
                raise PermissionDenied("LOW-priority near-miss closure is restricted to Master, PIC, DPA, or FM authority.")
            if not (self._has_process_permission("SAF_P_004") or self._has_process_permission("SAF_P_006")):
                raise PermissionDenied("LOW-priority near-miss closure requires SAF_P_004 or SAF_P_006 authority.")
            if len((near_miss.closure_reason or "").strip()) == 0 and len((self.request.data.get("closure_reason") or "").strip()) == 0:
                raise ValidationError(
                    {
                        "closure_reason": [
                            "LOW-priority near-miss closure requires Master/DPA correspondence note (D-GAP-R22)."
                        ]
                    }
                )
            return

        raise ValidationError("Near-miss priority must be LOW or HIGH before closure.")

    def get(self, request, *args, **kwargs):
        near_miss = self.get_near_miss()
        if near_miss.state != "CLOSED":
            raise ValidationError("Near-miss closure summary is only available after the record is closed.")
        return Response(self._build_summary_payload(near_miss), status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        near_miss = self.get_near_miss()
        serializer = self.get_serializer(data=request.data, context={"incident": near_miss, "user": request.user})
        serializer.is_valid(raise_exception=True)
        old_state = capture_model_state(
            near_miss,
            field_names=(
                "state",
                "closed_at",
                "closure_reason",
                "near_miss_suggestion",
                "updated_by",
                "updated_date",
            ),
        )
        preventive_measures = (serializer.validated_data.get("near_miss_suggestion") or "").strip()
        if preventive_measures:
            near_miss.near_miss_suggestion = preventive_measures
        self._validate_close_contract(near_miss)

        closed_at = timezone.now()
        actor_id = resolve_actor_id(request.user)
        actor_role = _normalized_role(request.user) or "SYSTEM"

        near_miss.state = "CLOSED"
        near_miss.closed_at = closed_at
        near_miss.closure_reason = serializer.validated_data["closure_reason"]
        near_miss.updated_by = actor_id
        near_miss.updated_date = closed_at
        near_miss.save(
            update_fields=(
                "state",
                "closed_at",
                "closure_reason",
                "near_miss_suggestion",
                "updated_by",
                "updated_date",
            )
        )
        record_field_changes(
            near_miss,
            old_state,
            user=request.user,
            field_names=(
                "state",
                "closed_at",
                "closure_reason",
                "near_miss_suggestion",
                "updated_by",
                "updated_date",
            ),
            change_reason="Near-miss closure completed.",
        )
        SafetyFieldHistory.objects.create(
            parent_table=near_miss._meta.db_table,
            parent_id=near_miss.pk,
            field_name="near_miss_closure_signature",
            old_value=None,
            new_value={
                "device_fingerprint": serializer.validated_data["device_fingerprint"],
                "signed_at": closed_at.isoformat(),
                "signed_by": actor_id,
                "signed_role": actor_role,
                "typed_name": serializer.validated_data["typed_name"].strip(),
            },
            change_reason="Near-miss closure completed.",
            actor_user_id=actor_id,
            actor_role_code=actor_role,
            schema_version=near_miss.schema_version or 1,
        )
        if near_miss.near_miss_priority == "HIGH":
            SafetyFieldHistory.objects.create(
                parent_table=near_miss._meta.db_table,
                parent_id=near_miss.pk,
                field_name="near_miss_preventive_measures",
                old_value=None,
                new_value={
                    "description": near_miss.near_miss_suggestion,
                    "due_date": (
                        serializer.validated_data.get("preventive_measure_due_date").isoformat()
                        if serializer.validated_data.get("preventive_measure_due_date")
                        else None
                    ),
                    "owner": serializer.validated_data.get("preventive_measure_owner") or "",
                    "status": serializer.validated_data.get("preventive_measure_status") or "OPEN",
                },
                change_reason="Near-miss structured preventive measures recorded.",
                actor_user_id=actor_id,
                actor_role_code=actor_role,
                schema_version=near_miss.schema_version or 1,
            )
        IncidentPhaseLog.objects.create(
            incident=near_miss,
            phase_from=near_miss.current_phase,
            phase_to=near_miss.current_phase,
            transition_type=IncidentPhaseLog.TransitionType.CLOSE,
            actor_user_id=actor_id,
            actor_role_code=actor_role,
            device_fingerprint=serializer.validated_data["device_fingerprint"],
            schema_version=near_miss.schema_version or 1,
        )
        return Response(self._build_summary_payload(near_miss), status=status.HTTP_200_OK)


class NearMissAuditView(NearMissViewMixin, generics.GenericAPIView):
    lookup_url_kwarg = "id"
    queryset = Incident.objects.filter(is_deleted=False)

    def get_permissions(self):
        return [self.form_permission_class()]

    def get_queryset(self):
        return self._apply_filters(super().get_queryset())

    def get(self, request, *args, **kwargs):
        near_miss = get_by_id_or_pk(self.get_queryset(), self.kwargs[self.lookup_url_kwarg])
        if near_miss.record_type != Incident.RecordType.NEAR_MISS:
            raise ValidationError("Near-miss audit is only available for near-miss records.")

        phase_logs = IncidentPhaseLog.objects.filter(incident_id=near_miss.pk).order_by("occurred_at", "id")
        field_history = _filtered_field_history_queryset(near_miss, user=request.user)
        return Response(
            {
                "phase_log": PhaseLogSerializer(phase_logs, many=True).data,
                "field_history": FieldHistorySerializer(field_history, many=True).data,
            }
        )
