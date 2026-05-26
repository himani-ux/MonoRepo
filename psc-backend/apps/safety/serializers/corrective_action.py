from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from apps.safety.models import CorrectiveAction, Incident, Recommendation, SCMAgendaItem
from apps.safety.identifiers import is_uuid_identifier
from apps.safety.services.ca_aging import CorrectiveActionAgingService
from apps.safety.services.purchase_fk_enforcer import PurchaseFKEnforcer, PurchaseFKEnforcerError


ALLOWED_STATUS_TRANSITIONS = {
    CorrectiveAction.Status.OPEN: {CorrectiveAction.Status.IN_PROGRESS},
    CorrectiveAction.Status.IN_PROGRESS: {CorrectiveAction.Status.PENDING_VERIFY},
    CorrectiveAction.Status.PENDING_VERIFY: {CorrectiveAction.Status.CLOSED, CorrectiveAction.Status.REOPENED},
    CorrectiveAction.Status.CLOSED: {CorrectiveAction.Status.REOPENED},
    CorrectiveAction.Status.REOPENED: {CorrectiveAction.Status.IN_PROGRESS, CorrectiveAction.Status.PENDING_VERIFY},
}


def _purchase_fk_enforcer(context) -> PurchaseFKEnforcer:
    return context.get("purchase_fk_enforcer") or context.get("purchase_guard") or PurchaseFKEnforcer()


def _aging_service(context) -> CorrectiveActionAgingService:
    return context.get("aging_service") or CorrectiveActionAgingService()


class CorrectiveActionSerializer(serializers.ModelSerializer):
    aging_bucket = serializers.SerializerMethodField()
    purchase_request = serializers.SerializerMethodField()
    recommendation_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = CorrectiveAction
        fields = (
            "id",
            "id",
            "source_table",
            "source_id",
            "recommendation_id",
            "title",
            "description",
            "assigned_crew_id",
            "assigned_office_user_id",
            "verifier_user_id",
            "due_date",
            "status",
            "purchase_req_id",
            "purchase_request",
            "physical_verification_done",
            "physical_verification_at",
            "physical_verification_by",
            "physical_verification_note",
            "aging_bucket",
            "closed_at",
            "closed_by",
        )
        read_only_fields = fields

    def get_aging_bucket(self, obj: CorrectiveAction) -> str:
        return _aging_service(self.context).aging_bucket(obj)

    def get_purchase_request(self, obj: CorrectiveAction) -> dict[str, object] | None:
        if not obj.purchase_req_id:
            return None
        requisition = _purchase_fk_enforcer(self.context).get_requisition(obj.purchase_req_id, raise_if_missing=False)
        if requisition is not None:
            return requisition
        return {
            "id": obj.purchase_req_id,
            "status": None,
            "is_archived": None,
        }


class CorrectiveActionWriteSerializer(serializers.ModelSerializer):
    recommendation_id = serializers.UUIDField(required=False, allow_null=True)
    source_id = serializers.CharField(required=False, allow_blank=False)

    class Meta:
        model = CorrectiveAction
        fields = (
            "source_table",
            "source_id",
            "recommendation_id",
            "title",
            "description",
            "assigned_crew_id",
            "assigned_office_user_id",
            "verifier_user_id",
            "due_date",
            "purchase_req_id",
        )

    def validate_recommendation_id(self, value):
        if value is None:
            return value
        if not Recommendation.objects.filter(pk=value, is_deleted=False).exists():
            raise serializers.ValidationError("Recommendation must exist before linking a corrective action.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        source_table = str(attrs.get("source_table") or "").strip()
        source_id = attrs.get("source_id")
        if source_id in (None, ""):
            return attrs

        source_value = str(source_id).strip()
        if is_uuid_identifier(source_value):
            source_model = None
            if source_table == Incident._meta.db_table:
                source_model = Incident
            elif source_table == SCMAgendaItem._meta.db_table:
                source_model = SCMAgendaItem
            if source_model is not None:
                row = source_model.objects.filter(id=source_value, is_deleted=False).values("id").first()
                if row is None:
                    raise serializers.ValidationError({"source_id": "Source record does not exist."})
                attrs["source_id"] = row["id"]
                return attrs

        raise serializers.ValidationError({"source_id": "Source ID must be a valid Safety UUID."})
        return attrs

    def validate_purchase_req_id(self, value: int | None) -> int | None:
        if value in (None, ""):
            return None
        try:
            _purchase_fk_enforcer(self.context).ensure_linkable(int(value))
        except PurchaseFKEnforcerError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return int(value)

    def create(self, validated_data):
        recommendation_id = validated_data.pop("recommendation_id", None)
        actor_id = self.context.get("user_id", "system")
        if recommendation_id is not None:
            validated_data["recommendation"] = Recommendation.objects.get(pk=recommendation_id)
        action = CorrectiveAction.objects.create(
            status=CorrectiveAction.Status.OPEN,
            created_by=actor_id,
            updated_by=actor_id,
            updated_date=timezone.now(),
            schema_version=1,
            **validated_data,
        )
        _aging_service(self.context).sync_bucket(action)
        return action


class CorrectiveActionLinkPurchaseSerializer(serializers.Serializer):
    purchase_req_id = serializers.IntegerField(min_value=1)

    def validate_purchase_req_id(self, value: int) -> int:
        try:
            _purchase_fk_enforcer(self.context).ensure_linkable(value)
        except PurchaseFKEnforcerError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value


class CorrectiveActionTransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=CorrectiveAction.Status.choices)
    note = serializers.CharField(allow_blank=False)

    def validate(self, attrs):
        action: CorrectiveAction = self.context["action"]
        target_status = attrs["status"]
        if target_status == action.status:
            raise serializers.ValidationError({"status": "Corrective Action is already in the requested state."})
        allowed_targets = ALLOWED_STATUS_TRANSITIONS.get(action.status, set())
        if target_status not in allowed_targets:
            raise serializers.ValidationError(
                {"status": f"Illegal corrective-action transition from {action.status} to {target_status}."}
            )
        return attrs


class CorrectiveActionPhysicalVerifySerializer(serializers.Serializer):
    note = serializers.CharField(allow_blank=False)
