from __future__ import annotations

import json
import math
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.db import connection
from django.http import HttpResponseRedirect
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.certs.services.magic_link import MagicLinkExpired, MagicLinkInvalid, verify_magic_link_token


def _table_name(table_name: str) -> str:
    if connection.vendor == "microsoft":
        return f"dbo.{table_name}"
    return table_name


def _recipient_candidates(user) -> list[str]:
    values = [
        getattr(user, "user_id", None),
        getattr(user, "id", None),
        getattr(user, "employee_id", None),
        getattr(user, "crew_id", None),
        getattr(user, "login_id", None),
    ]
    return [str(value) for value in dict.fromkeys(values) if value not in (None, "")]


def _json_value(raw: object, fallback):
    if raw in (None, ""):
        return fallback
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(str(raw))
    except json.JSONDecodeError:
        return fallback


def _row_dict(cursor, row) -> dict[str, object]:
    columns = [column[0] for column in cursor.description]
    return dict(zip(columns, row))


def _redirect_with_ack_status(path: str | None, status_value: str) -> str:
    safe_path = path if path and path.startswith("/") and not path.startswith("//") else "/notifications?module=certs"
    parts = urlsplit(safe_path)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["ack"] = status_value
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


class CertNotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        recipients = _recipient_candidates(request.user)
        if not recipients:
            return Response(
                {"error": "INVALID_USER", "message": "Unable to determine notification recipient."},
                status=status.HTTP_403_FORBIDDEN,
            )

        placeholders = ", ".join(["%s"] * len(recipients))
        params: list[object] = list(recipients)
        where_parts = [f"mn.recipient_ref IN ({placeholders})", "UPPER(mn.module_code) = 'CERTS'"]

        is_read = request.query_params.get("is_read")
        if is_read is not None:
            if is_read.lower() in ("true", "1"):
                where_parts.append("meta.ack_at IS NOT NULL")
            else:
                where_parts.append("meta.ack_at IS NULL")

        page = max(1, int(request.query_params.get("page", 1)))
        page_size = min(max(1, int(request.query_params.get("page_size", 20))), 100)
        offset = (page - 1) * page_size

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {_table_name("master_notification")} mn
                JOIN {_table_name("vims_certs_notification_meta")} meta
                  ON meta.master_notification_id = mn.id
                WHERE {" AND ".join(where_parts)}
                """,
                params,
            )
            total_count = int(cursor.fetchone()[0] or 0)
            cursor.execute(
                f"""
                SELECT
                    meta.notification_id,
                    meta.master_notification_id,
                    meta.trigger_event,
                    meta.cert_row_id,
                    meta.vessel_id,
                    meta.recipients_json,
                    meta.channels_json,
                    meta.sent_at,
                    meta.delivery_status_json,
                    meta.ack_user_id,
                    meta.ack_at,
                    meta.ack_channel,
                    meta.escalation_level,
                    mn.recipient_ref,
                    mn.notification_kind,
                    mn.title,
                    mn.message,
                    mn.payload_json,
                    mn.created_at
                FROM {_table_name("master_notification")} mn
                JOIN {_table_name("vims_certs_notification_meta")} meta
                  ON meta.master_notification_id = mn.id
                WHERE {" AND ".join(where_parts)}
                ORDER BY meta.sent_at DESC
                OFFSET %s ROWS FETCH NEXT %s ROWS ONLY
                """,
                [*params, offset, page_size],
            )
            rows = [_row_dict(cursor, row) for row in cursor.fetchall()]

        total_pages = max(1, math.ceil(total_count / page_size))

        return Response(
            {
                "data": [self._serialize_row(row) for row in rows],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                },
            }
        )

    def _serialize_row(self, row: dict[str, object]) -> dict[str, object]:
        ack_at = row.get("ack_at")
        sent_at = row.get("sent_at") or row.get("created_at")
        channels = _json_value(row.get("channels_json"), [])
        side = ""
        if channels and isinstance(channels[0], dict):
            side = str(channels[0].get("side") or "").lower()
        recipient_type = "CREW" if side == "vessel" else "OFFICE"
        return {
            "id": str(row.get("notification_id")),
            "masterNotificationId": row.get("master_notification_id"),
            "triggerEvent": row.get("trigger_event"),
            "certRowId": str(row.get("cert_row_id")) if row.get("cert_row_id") else None,
            "vesselId": str(row.get("vessel_id")) if row.get("vessel_id") else None,
            "recipients": _json_value(row.get("recipients_json"), []),
            "channels": channels,
            "deliveryStatus": _json_value(row.get("delivery_status_json"), []),
            "ackUserId": row.get("ack_user_id"),
            "ackAt": ack_at,
            "ackChannel": row.get("ack_channel"),
            "escalationLevel": row.get("escalation_level"),
            "recipient_type": recipient_type,
            "recipient_id": row.get("recipient_ref"),
            "vessel_id": str(row.get("vessel_id")) if row.get("vessel_id") else None,
            "notification_type": "CERT_ALERT",
            "title": row.get("title"),
            "message": row.get("message"),
            "entity_type": "tracked_item",
            "entity_id": str(row.get("cert_row_id")) if row.get("cert_row_id") else None,
            "is_read": ack_at is not None,
            "read_at": ack_at,
            "created_date": sent_at,
        }


class CertNotificationAckView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id, *args, **kwargs):
        recipients = _recipient_candidates(request.user)
        if not recipients:
            return Response(
                {"error": "INVALID_USER", "message": "Unable to determine notification recipient."},
                status=status.HTTP_403_FORBIDDEN,
            )

        placeholders = ", ".join(["%s"] * len(recipients))
        params: list[object] = [str(getattr(request.user, "user_id", request.user.id)), timezone.now(), str(notification_id)]
        params.extend(recipients)
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {_table_name("vims_certs_notification_meta")}
                SET ack_user_id = %s, ack_at = %s, ack_channel = 'in_app'
                WHERE notification_id = %s
                  AND ack_at IS NULL
                  AND master_notification_id IN (
                      SELECT id FROM {_table_name("master_notification")}
                      WHERE recipient_ref IN ({placeholders})
                        AND UPPER(module_code) = 'CERTS'
                  )
                """,
                params,
            )
            updated = cursor.rowcount

        return Response({"data": {"marked_count": max(updated, 0)}})


class CertNotificationMagicAckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, token, *args, **kwargs):
        try:
            payload = verify_magic_link_token(token)
        except MagicLinkExpired:
            return Response(
                {"error": "MAGIC_LINK_EXPIRED", "message": "This acknowledgement link has expired."},
                status=status.HTTP_410_GONE,
            )
        except MagicLinkInvalid:
            return Response(
                {"error": "MAGIC_LINK_INVALID", "message": "This acknowledgement link is invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        row = self._get_notification_row(
            notification_id=payload.notification_id,
            recipient_id=payload.recipient_id,
        )
        if row is None:
            return Response(
                {"error": "MAGIC_LINK_INVALID", "message": "This acknowledgement link is invalid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if row.get("ack_at") is not None:
            return Response(
                {"error": "MAGIC_LINK_ALREADY_USED", "message": "This acknowledgement link was already used."},
                status=status.HTTP_409_CONFLICT,
            )

        ack_at = timezone.now()
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                UPDATE {_table_name("vims_certs_notification_meta")}
                SET ack_user_id = %s, ack_at = %s, ack_channel = 'magic_link'
                WHERE notification_id = %s
                  AND ack_at IS NULL
                  AND master_notification_id IN (
                      SELECT id FROM {_table_name("master_notification")}
                      WHERE recipient_ref = %s
                        AND UPPER(module_code) = 'CERTS'
                  )
                """,
                [payload.recipient_id, ack_at, payload.notification_id, payload.recipient_id],
            )
            updated = cursor.rowcount

        if updated <= 0:
            return Response(
                {"error": "MAGIC_LINK_ALREADY_USED", "message": "This acknowledgement link was already used."},
                status=status.HTTP_409_CONFLICT,
            )

        redirect_path = self._redirect_path(row)
        return HttpResponseRedirect(_redirect_with_ack_status(redirect_path, "success"))

    def _get_notification_row(self, *, notification_id: str, recipient_id: str) -> dict[str, object] | None:
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    meta.notification_id,
                    meta.ack_at,
                    mn.recipient_ref,
                    mn.payload_json
                FROM {_table_name("vims_certs_notification_meta")} meta
                JOIN {_table_name("master_notification")} mn
                  ON meta.master_notification_id = mn.id
                WHERE meta.notification_id = %s
                  AND mn.recipient_ref = %s
                  AND UPPER(mn.module_code) = 'CERTS'
                """,
                [notification_id, recipient_id],
            )
            row = cursor.fetchone()
            if not row:
                return None
            return _row_dict(cursor, row)

    def _redirect_path(self, row: dict[str, object]) -> str | None:
        payload = _json_value(row.get("payload_json"), {})
        if not isinstance(payload, dict):
            return None
        return payload.get("returnPath") or payload.get("redirectPath")
