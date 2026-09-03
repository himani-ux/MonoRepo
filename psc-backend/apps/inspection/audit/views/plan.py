"""Audit plan register API views."""

import logging
import uuid

from django.db import connection, transaction
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import MasterAuditPlan
from apps.inspection.audit.permissions import (
    AUDIT_GATE_IDS,
    AUDIT_P_001,
    AUDIT_P_002,
    AUDIT_P_005,
    AUDIT_P_006,
    HasAnyAuditProcessPermission,
    audit_process_ids_for_request,
    is_office_user,
    is_vessel_user,
    normalized_audit_role,
)
from apps.inspection.audit.serializers.plan import (
    AuditPlanCancelSerializer,
    AuditPlanExtensionDecisionSerializer,
    AuditPlanExtensionRequestSerializer,
    AuditPlanFlagNotificationSerializer,
    AuditPlanResponseSerializer,
    AuditPlanSerializer,
)
from apps.inspection.audit.services.additional_audit import create_additional_audit_plan
from apps.inspection.audit.services.cancellation import cancel_audit_plan
from apps.inspection.audit.services.extension import (
    AuditPlanWorkflowError,
    decide_plan_extension,
    record_flag_notification,
    request_plan_extension,
)
from apps.inspection.audit.services.notification_dispatcher import dispatch_audit_notification
from apps.inspection.audit.services.vessels import audit_vessel_label_map


logger = logging.getLogger(__name__)


def _forbidden(message: str) -> Response:
    return Response(
        {
            "error": "FORBIDDEN",
            "message": message,
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def _bad_request(errors: dict[str, str]) -> Response:
    return Response(errors, status=status.HTTP_400_BAD_REQUEST)


def _user_id(user: object) -> str:
    return str(getattr(user, "id", "") or getattr(user, "username", "") or "system")


def _user_vessel_uuid(user: object) -> uuid.UUID | None:
    vessel_id = getattr(user, "vessel_id", None)
    if vessel_id in (None, ""):
        return None
    try:
        return uuid.UUID(str(vessel_id))
    except (TypeError, ValueError, AttributeError):
        return None


def _is_dpa_user(user: object) -> bool:
    return normalized_audit_role(user) == "DPA"


def _plan_queryset():
    return MasterAuditPlan.objects.order_by("planned_window_end", "planned_window_start", "id")


def _plan_status_filter(request) -> str | None:
    status_filter = request.query_params.get("status")
    return status_filter.strip().upper() if status_filter else None


def _plan_additional_filter(request) -> bool | None:
    additional_filter = request.query_params.get("is_additional")
    if additional_filter is None:
        return None
    return additional_filter.strip().lower() in {"1", "true", "yes"}


def _apply_plan_list_filters(queryset, *, status_filter: str | None, additional_filter: bool | None):
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if additional_filter is not None:
        queryset = queryset.filter(is_additional=additional_filter)
    return queryset


def _sql_server_vessel_plan_rows(
    *,
    vessel_uuid: uuid.UUID,
    status_filter: str | None,
    additional_filter: bool | None,
) -> list[MasterAuditPlan]:
    where_clauses = [
        "target_vessel_id = CAST(%s AS uniqueidentifier)",
        "is_deleted = 0",
    ]
    params: list[object] = [str(vessel_uuid)]
    if status_filter:
        where_clauses.append("status = %s")
        params.append(status_filter)
    if additional_filter is not None:
        where_clauses.append("is_additional = %s")
        params.append(1 if additional_filter else 0)

    return list(
        MasterAuditPlan.objects.raw(
            f"""
            SELECT *
            FROM dbo.master_audit_plan
            WHERE {' AND '.join(where_clauses)}
            ORDER BY planned_window_end, planned_window_start, id
            """,
            params,
        )
    )


def _serialize_plan(plan: MasterAuditPlan):
    return AuditPlanResponseSerializer(
        plan,
        context={"vessel_label_map": audit_vessel_label_map([plan.target_vessel_id])},
    ).data


def _serialize_plans(plans: list[MasterAuditPlan]):
    return AuditPlanResponseSerializer(
        plans,
        many=True,
        context={"vessel_label_map": audit_vessel_label_map([plan.target_vessel_id for plan in plans])},
    ).data


def _plan_by_id(plan_id) -> MasterAuditPlan:
    plan_uuid = uuid.UUID(str(plan_id))
    if connection.vendor == "microsoft":
        rows = list(
            MasterAuditPlan.objects.raw(
                """
                SELECT *
                FROM dbo.master_audit_plan
                WHERE id = CAST(%s AS uniqueidentifier)
                  AND is_deleted = 0
                """,
                [str(plan_uuid)],
            )
        )
        if rows:
            return rows[0]
        raise MasterAuditPlan.DoesNotExist
    return MasterAuditPlan.objects.get(id=plan_uuid)


class AuditPlanListCreateView(APIView):
    """GET/POST /api/audit/plans/ for the Phase 8.1 plan register."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(*AUDIT_GATE_IDS)]

    def get(self, request):
        status_filter = _plan_status_filter(request)
        additional_filter = _plan_additional_filter(request)

        if is_vessel_user(request.user):
            vessel_uuid = _user_vessel_uuid(request.user)
            if vessel_uuid is None:
                plans = []
            elif connection.vendor == "microsoft":
                plans = _sql_server_vessel_plan_rows(
                    vessel_uuid=vessel_uuid,
                    status_filter=status_filter,
                    additional_filter=additional_filter,
                )
            else:
                queryset = _apply_plan_list_filters(
                    _plan_queryset().filter(target_vessel_id=vessel_uuid),
                    status_filter=status_filter,
                    additional_filter=additional_filter,
                )
                plans = list(queryset)
        elif not is_office_user(request.user):
            return _forbidden("Audit plan register is available only to office users or vessel users.")
        else:
            queryset = _apply_plan_list_filters(
                _plan_queryset(),
                status_filter=status_filter,
                additional_filter=additional_filter,
            )
            plans = list(queryset)

        rows = _serialize_plans(plans)
        return Response({"data": {"count": len(rows), "results": rows}})

    def post(self, request):
        if AUDIT_P_001 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to create audit plan entries.")
        if not is_office_user(request.user):
            return _forbidden("Audit plan creation is restricted to office users.")

        serializer = AuditPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            plan = serializer.save(created_by=_user_id(request.user))
            if plan.status == "CONFIRMED":
                _dispatch_plan_notification_after_commit(plan, "AUDIT_SCHEDULED")
        return Response(
            {
                "data": _serialize_plan(plan),
                "message": "Audit plan entry created successfully",
            },
            status=status.HTTP_201_CREATED,
        )


class AuditPlanDetailView(APIView):
    """GET/PATCH /api/audit/plans/{id}/ for Phase 8.1 plan detail/edit."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(*AUDIT_GATE_IDS)]

    def get(self, request, id):
        if not is_office_user(request.user):
            return _forbidden("Audit plan register is restricted to office users.")
        return Response({"data": _serialize_plan(self._get_plan(id))})

    def patch(self, request, id):
        if not is_office_user(request.user):
            return _forbidden("Audit plan updates are restricted to office users.")
        request_process_ids = audit_process_ids_for_request(request)
        if AUDIT_P_001 not in request_process_ids and AUDIT_P_002 not in request_process_ids:
            return _forbidden("You do not have permission to update audit plan entries.")

        plan = self._get_plan(id)
        previous_status = plan.status
        if plan.status == "CANCELLED":
            return _bad_request({"status": "Cancelled plan entries are read-only."})
        serializer = AuditPlanSerializer(
            plan,
            data=request.data,
            partial=True,
            context={"instance": plan},
        )
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            updated_plan = serializer.save(
                updated_by=_user_id(request.user),
                updated_date=timezone.now(),
            )
            if previous_status != "CONFIRMED" and updated_plan.status == "CONFIRMED":
                _dispatch_plan_notification_after_commit(updated_plan, "AUDIT_SCHEDULED")
        return Response({"data": _serialize_plan(updated_plan)})

    def _get_plan(self, id):
        try:
            return _plan_by_id(id)
        except MasterAuditPlan.DoesNotExist as exc:
            raise Http404("Audit plan not found.") from exc


class AuditPlanExtensionRequestView(APIView):
    """POST /api/audit/plans/{id}/extension/ for OPM F 713 requests."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(*AUDIT_GATE_IDS)]

    def post(self, request, id):
        if AUDIT_P_001 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to request audit extensions.")
        if not is_office_user(request.user):
            return _forbidden("Audit extension requests are restricted to office users.")

        serializer = AuditPlanExtensionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            plan = request_plan_extension(
                _get_plan(id),
                reason=serializer.validated_data["extension_requested_reason"],
                proposed_new_target_date=serializer.validated_data["proposed_new_target_date"],
                actor=_user_id(request.user),
            )
        except AuditPlanWorkflowError as exc:
            return _bad_request(exc.errors)
        return Response({"data": _serialize_plan(plan)})


class AuditPlanExtensionDecideView(APIView):
    """POST /api/audit/plans/{id}/extension/decide/ for DPA extension decisions."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(*AUDIT_GATE_IDS)]

    def post(self, request, id):
        if AUDIT_P_005 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to decide audit extensions.")
        if not is_office_user(request.user) or not _is_dpa_user(request.user):
            return _forbidden("Audit extension decisions are DPA-only.")

        serializer = AuditPlanExtensionDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                result = decide_plan_extension(
                    _get_plan(id),
                    decision=serializer.validated_data["decision"],
                    reason=serializer.validated_data["extension_approved_reason"],
                    actor=_user_id(request.user),
                )
                if result.approved:
                    _dispatch_plan_notification(result.plan, "AUDIT_EXTENSION_APPROVED")
        except AuditPlanWorkflowError as exc:
            return _bad_request(exc.errors)
        return Response(
            {
                "data": _serialize_plan(result.plan),
                "approved": result.approved,
            }
        )


class AuditPlanFlagNotifyView(APIView):
    """POST /api/audit/plans/{id}/flag-notify/ for extension flag notification capture."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(*AUDIT_GATE_IDS)]

    def post(self, request, id):
        if AUDIT_P_005 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to record flag notifications.")
        if not is_office_user(request.user) or not _is_dpa_user(request.user):
            return _forbidden("Flag notification capture is DPA-only.")

        serializer = AuditPlanFlagNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            plan = record_flag_notification(
                _get_plan(id),
                notification_date=serializer.validated_data["flag_notification_date"],
                notification_ref=serializer.validated_data["flag_notification_ref"],
                attachment=serializer.validated_data["flag_notification_attachment"],
                actor=_user_id(request.user),
            )
        except AuditPlanWorkflowError as exc:
            return _bad_request(exc.errors)
        return Response({"data": _serialize_plan(plan)})


class AuditPlanCancelView(APIView):
    """POST /api/audit/plans/{id}/cancel/ for DPA cancellation."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(*AUDIT_GATE_IDS)]

    def post(self, request, id):
        if AUDIT_P_006 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to cancel audit plan entries.")
        if not is_office_user(request.user) or not _is_dpa_user(request.user):
            return _forbidden("Audit cancellation is DPA-only.")

        serializer = AuditPlanCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                original_plan = _get_plan(id)
                was_cancelled = original_plan.status == "CANCELLED"
                plan, replacement = cancel_audit_plan(
                    original_plan,
                    cancellation_reason=serializer.validated_data["cancellation_reason"],
                    next_planned_date=serializer.validated_data["next_planned_date"],
                    actor=_user_id(request.user),
                    today=serializer.validated_data.get("today"),
                )
                if not was_cancelled:
                    _dispatch_plan_notification(plan, "AUDIT_CANCELLED")
        except AuditPlanWorkflowError as exc:
            return _bad_request(exc.errors)
        return Response(
            {
                "data": _serialize_plan(plan),
                "replacement_plan": _serialize_plan(replacement),
            }
        )


class AuditPlanAdditionalView(APIView):
    """POST /api/audit/plans/additional/ for DPA additional audits."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(*AUDIT_GATE_IDS)]

    def post(self, request):
        if AUDIT_P_001 not in audit_process_ids_for_request(request):
            return _forbidden("You do not have permission to create additional audits.")
        if not is_office_user(request.user) or not _is_dpa_user(request.user):
            return _forbidden("Additional audit creation is DPA-only.")

        try:
            plan = create_additional_audit_plan(data=request.data, actor=_user_id(request.user))
        except AuditPlanWorkflowError as exc:
            return _bad_request(exc.errors)
        return Response(
            {
                "data": _serialize_plan(plan),
                "message": "Additional audit plan entry created successfully",
            },
            status=status.HTTP_201_CREATED,
        )


def _get_plan(id):
    try:
        return _plan_by_id(id)
    except MasterAuditPlan.DoesNotExist as exc:
        raise Http404("Audit plan not found.") from exc


def _dispatch_plan_notification(plan: MasterAuditPlan, notification_type: str) -> None:
    titles = {
        "AUDIT_SCHEDULED": "Audit scheduled",
        "AUDIT_CANCELLED": "Audit cancelled",
        "AUDIT_EXTENSION_APPROVED": "Audit extension approved",
    }
    messages = {
        "AUDIT_SCHEDULED": "Internal audit plan has been confirmed.",
        "AUDIT_CANCELLED": "Internal audit plan has been cancelled by DPA.",
        "AUDIT_EXTENSION_APPROVED": "Internal audit plan extension has been approved by DPA.",
    }
    dispatch_audit_notification(
        notification_type=notification_type,
        title=titles[notification_type],
        message=messages[notification_type],
        entity_type="AUDIT_PLAN",
        entity_id=plan.id,
        vessel_id=plan.target_vessel_id,
        office_dept=plan.target_office_dept,
    )


def _dispatch_plan_notification_after_commit(plan: MasterAuditPlan, notification_type: str) -> None:
    def dispatch() -> None:
        try:
            _dispatch_plan_notification(plan, notification_type)
        except Exception:
            logger.exception(
                "Audit plan notification dispatch failed after plan save. plan_id=%s notification_type=%s",
                plan.id,
                notification_type,
            )

    transaction.on_commit(dispatch)
