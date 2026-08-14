"""DPA failed-notification queue API views."""

from __future__ import annotations

from django.http import Http404
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inspection.audit.models import NotificationDeliveryLog
from apps.inspection.audit.permissions import (
    AUDIT_GATE_IDS,
    HasAnyAuditProcessPermission,
    is_office_user,
    normalized_audit_role,
)
from apps.inspection.audit.serializers.notification import (
    AuditNotificationDeliverySerializer,
    AuditNotificationOfflineSerializer,
)


FAILED_STATUS = "FAILED_PERMANENT"
RETRYABLE_CHANNELS = {"EMAIL", "SLACK"}
RESOLVED_OFFLINE_STATUS = "RESOLVED_OFFLINE"


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


def _is_dpa_user(user: object) -> bool:
    return is_office_user(user) and normalized_audit_role(user) == "DPA"


class AuditFailedNotificationListView(APIView):
    """GET /api/audit/dpa/notifications/failed/ for the DPA failed queue."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(*AUDIT_GATE_IDS)]

    def get(self, request):
        if not _is_dpa_user(request.user):
            return _forbidden("Failed notification resolution is DPA-only.")

        queryset = NotificationDeliveryLog.objects.filter(status=FAILED_STATUS).order_by(
            "last_attempted_at",
            "created_date",
            "id",
        )
        rows = AuditNotificationDeliverySerializer(list(queryset), many=True).data
        return Response({"data": {"count": len(rows), "results": rows}})


class AuditNotificationRetryView(APIView):
    """POST /api/audit/notifications/{id}/retry/ to requeue a failed transport row."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(*AUDIT_GATE_IDS)]

    def post(self, request, id):
        if not _is_dpa_user(request.user):
            return _forbidden("Manual notification retry is DPA-only.")

        delivery_log = _get_delivery_log(id)
        if delivery_log.status != FAILED_STATUS:
            return _bad_request({"status": "Only FAILED_PERMANENT rows can be retried manually."})
        if delivery_log.channel not in RETRYABLE_CHANNELS:
            return _bad_request({"channel": "Manual retry is available only for EMAIL or SLACK delivery rows."})

        with transaction.atomic():
            delivery_log.status = "QUEUED"
            delivery_log.attempt_count = 0
            delivery_log.first_attempted_at = None
            delivery_log.last_attempted_at = None
            delivery_log.last_error = None
            delivery_log.sent_at = None
            delivery_log.resolved_offline_reason = None
            delivery_log.save(
                update_fields=[
                    "status",
                    "attempt_count",
                    "first_attempted_at",
                    "last_attempted_at",
                    "last_error",
                    "sent_at",
                    "resolved_offline_reason",
                ]
            )

        return Response(
            {
                "data": AuditNotificationDeliverySerializer(delivery_log).data,
                "message": "Notification delivery row queued for manual retry.",
            }
        )


class AuditNotificationOfflineResolveView(APIView):
    """POST /api/audit/notifications/{id}/offline/ to resolve a failed row manually."""

    permission_classes = [IsAuthenticated, HasAnyAuditProcessPermission.requiring_any(*AUDIT_GATE_IDS)]

    def post(self, request, id):
        if not _is_dpa_user(request.user):
            return _forbidden("Offline notification resolution is DPA-only.")

        delivery_log = _get_delivery_log(id)
        if delivery_log.status != FAILED_STATUS:
            return _bad_request({"status": "Only FAILED_PERMANENT rows can be marked notified offline."})

        serializer = AuditNotificationOfflineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current = timezone.now()

        with transaction.atomic():
            delivery_log.status = RESOLVED_OFFLINE_STATUS
            delivery_log.resolved_offline_reason = serializer.validated_data["reason"]
            delivery_log.last_attempted_at = current
            if delivery_log.first_attempted_at is None:
                delivery_log.first_attempted_at = current
            delivery_log.save(
                update_fields=[
                    "status",
                    "resolved_offline_reason",
                    "first_attempted_at",
                    "last_attempted_at",
                ]
            )

        return Response(
            {
                "data": AuditNotificationDeliverySerializer(delivery_log).data,
                "message": "Notification delivery row resolved offline.",
            }
        )


def _get_delivery_log(id):
    try:
        return NotificationDeliveryLog.objects.get(id=id)
    except NotificationDeliveryLog.DoesNotExist as exc:
        raise Http404("Notification delivery row not found.") from exc


__all__ = [
    "AuditFailedNotificationListView",
    "AuditNotificationOfflineResolveView",
    "AuditNotificationRetryView",
]
