from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.certs.permissions import HasAuditorAccessReadPermission, IsAuditorAccessWriter
from apps.certs.serializers.auditor import (
    AuditorAccessCreateSerializer,
    AuditorAccessExpirySerializer,
    serialize_auditor_grant,
    serialize_auditor_tracked_item,
    serialize_auditor_vessel,
)
from apps.certs.services.audit_log import record_audit_event, resolve_actor_id
from apps.certs.services.auditor_access_repository import AuditorAccessRepository, is_grant_expired, parse_scope
from apps.certs.services.auditor_token import (
    AuditorTokenInvalid,
    build_session_token,
    build_signup_path,
    generate_raw_token,
    hash_token,
    verify_session_token,
)


repository = AuditorAccessRepository()
TERMINAL_EXPIRED_DETAIL = "Access expired — contact the DPA"


@dataclass(frozen=True)
class SystemActor:
    user_id: str = "external-auditor-signup"
    role: str = "SYSTEM"


class AuditorAccessListCreateView(generics.GenericAPIView):
    def get_permissions(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return [IsAuthenticated(), HasAuditorAccessReadPermission()]
        return [IsAuthenticated(), IsAuditorAccessWriter()]

    def get(self, request, *args, **kwargs):
        return Response({"results": [serialize_auditor_grant(row) for row in repository.list_grants()]})

    def post(self, request, *args, **kwargs):
        serializer = AuditorAccessCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_signup_token = generate_raw_token()
        signup_token_hash = hash_token(raw_signup_token)
        with transaction.atomic():
            row = repository.create_grant(
                auditor_name=serializer.validated_data["auditorName"],
                auditor_email=serializer.validated_data["auditorEmail"],
                scope=serializer.validated_data["scope"],
                expiry_at=serializer.validated_data["expiryAt"],
                granted_by=resolve_actor_id(request.user),
                signup_token_hash=signup_token_hash,
            )
            serialized = serialize_auditor_grant(row)
            record_audit_event(
                actor=request.user,
                action="grant_auditor_access",
                entity_type="external_auditor_access",
                entity_id=serialized["id"],
                before=None,
                after=_grant_audit_payload(serialized),
                reason="External auditor access granted.",
                metadata={"source": "api.certs.auditor_access"},
            )
        serialized["signupUrl"] = build_signup_path(raw_signup_token)
        return Response(serialized, status=status.HTTP_201_CREATED)


class AuditorAccessDetailView(generics.GenericAPIView):
    def get_permissions(self):
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            return [IsAuthenticated(), HasAuditorAccessReadPermission()]
        return [IsAuthenticated(), IsAuditorAccessWriter()]

    def get(self, request, grant_id: str, *args, **kwargs):
        row = repository.get_grant(str(grant_id))
        if row is None:
            return Response({"detail": "Auditor access grant not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialize_auditor_grant(row))

    def patch(self, request, grant_id: str, *args, **kwargs):
        serializer = AuditorAccessExpirySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        before = repository.get_grant(str(grant_id))
        if before is None:
            return Response({"detail": "Auditor access grant not found."}, status=status.HTTP_404_NOT_FOUND)
        expiry_at = serializer.validated_data["expiryAt"]
        revoked_via_expiry_edit = _is_past_or_now(expiry_at)
        with transaction.atomic():
            after = repository.update_expiry(
                str(grant_id),
                expiry_at=expiry_at,
                revoked_via_expiry_edit=revoked_via_expiry_edit,
            )
            if after is None:
                return Response({"detail": "Auditor access grant not found."}, status=status.HTTP_404_NOT_FOUND)
            serialized_before = serialize_auditor_grant(before)
            serialized_after = serialize_auditor_grant(after)
            record_audit_event(
                actor=request.user,
                action="edit_auditor_access",
                entity_type="external_auditor_access",
                entity_id=serialized_after["id"],
                before=_grant_audit_payload(serialized_before),
                after=_grant_audit_payload(serialized_after),
                reason="External auditor access expiry edited.",
                metadata={"source": "api.certs.auditor_access", "revokedViaExpiryEdit": revoked_via_expiry_edit},
            )
        return Response(serialized_after)


class AuditorSignupView(generics.GenericAPIView):
    authentication_classes: list = []
    permission_classes: list = []

    def post(self, request, token: str, *args, **kwargs):
        row = repository.get_grant_by_signup_token_hash(hash_token(token))
        if row is None:
            return Response({"detail": TERMINAL_EXPIRED_DETAIL}, status=status.HTTP_410_GONE)
        if row.get("signup_token_used_at") is not None or is_grant_expired(row):
            return Response({"detail": TERMINAL_EXPIRED_DETAIL}, status=status.HTTP_410_GONE)

        raw_secret = generate_raw_token()
        token_secret_hash = hash_token(raw_secret)
        with transaction.atomic():
            updated = repository.mark_signup_used(str(row["grant_id"]), token_secret_hash=token_secret_hash)
            if updated is None:
                return Response({"detail": TERMINAL_EXPIRED_DETAIL}, status=status.HTTP_410_GONE)
            serialized = serialize_auditor_grant(updated)
            record_audit_event(
                actor=SystemActor(),
                action="signup_token_used",
                entity_type="external_auditor_access",
                entity_id=serialized["id"],
                before=_grant_audit_payload(serialize_auditor_grant(row)),
                after=_grant_audit_payload(serialized),
                reason="External auditor signup token used.",
                metadata={"source": "api.auditor.signup"},
            )
        return Response(
            {
                "sessionToken": build_session_token(grant_id=serialized["id"], raw_secret=raw_secret),
                "grant": serialized,
            }
        )


class AuditorVesselListView(generics.GenericAPIView):
    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request, grant_token: str, *args, **kwargs):
        grant, error = _grant_from_token(grant_token)
        if error:
            return error
        repository.touch_last_accessed(str(grant["grant_id"]))
        vessels = repository.list_scoped_vessels(parse_scope(grant.get("scope_json")))
        return Response({"results": [serialize_auditor_vessel(row) for row in vessels]})


class AuditorVesselCertListView(generics.GenericAPIView):
    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request, grant_token: str, imo: str, *args, **kwargs):
        grant, error = _grant_from_token(grant_token)
        if error:
            return error
        repository.touch_last_accessed(str(grant["grant_id"]))
        rows = repository.list_scoped_certs(parse_scope(grant.get("scope_json")), imo=str(imo))
        return Response({"results": [serialize_auditor_tracked_item(row) for row in rows]})


class AuditorCertDetailView(generics.GenericAPIView):
    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request, grant_token: str, cert_id: str, *args, **kwargs):
        grant, error = _grant_from_token(grant_token)
        if error:
            return error
        repository.touch_last_accessed(str(grant["grant_id"]))
        row = repository.get_scoped_cert(parse_scope(grant.get("scope_json")), str(cert_id))
        if row is None:
            return Response({"detail": "Certificate not found in auditor scope."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serialize_auditor_tracked_item(row))


class AuditorPrintView(generics.GenericAPIView):
    authentication_classes: list = []
    permission_classes: list = []

    def post(self, request, grant_token: str, *args, **kwargs):
        grant, error = _grant_from_token(grant_token)
        if error:
            return error
        repository.touch_last_accessed(str(grant["grant_id"]))
        scope = parse_scope(grant.get("scope_json"))
        watermark_text = _auditor_watermark_text(grant, scope)
        return Response(
            {
                "watermarkApplied": "AUDIT_COPY",
                "watermarkRecipient": grant.get("auditor_name"),
                "watermarkText": watermark_text,
                "scope": scope,
            }
        )


def _grant_from_token(grant_token: str) -> tuple[dict[str, Any] | None, Response | None]:
    try:
        grant_id, token_secret_hash = verify_session_token(grant_token)
    except AuditorTokenInvalid:
        return None, Response({"detail": TERMINAL_EXPIRED_DETAIL}, status=status.HTTP_410_GONE)
    grant = repository.get_grant(str(grant_id))
    if grant is None or is_grant_expired(grant):
        return None, Response({"detail": TERMINAL_EXPIRED_DETAIL}, status=status.HTTP_410_GONE)
    if str(grant.get("token_secret_hash") or "") != token_secret_hash:
        return None, Response({"detail": TERMINAL_EXPIRED_DETAIL}, status=status.HTTP_410_GONE)
    return grant, None


def _is_past_or_now(value) -> bool:
    now = timezone.now()
    if timezone.is_naive(value):
        now = now.replace(tzinfo=None)
    return value <= now


def _grant_audit_payload(serialized: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": serialized.get("id"),
        "auditorName": serialized.get("auditorName"),
        "auditorEmail": serialized.get("auditorEmail"),
        "scope": serialized.get("scope"),
        "expiryAt": serialized.get("expiryAt"),
        "grantedBy": serialized.get("grantedBy"),
        "grantedAt": serialized.get("grantedAt"),
        "signupTokenUsedAt": serialized.get("signupTokenUsedAt"),
        "lastAccessedAt": serialized.get("lastAccessedAt"),
        "revokedViaExpiryEdit": serialized.get("revokedViaExpiryEdit"),
    }


def _auditor_watermark_text(grant: dict[str, Any], scope: dict[str, list[str]]) -> str:
    vessels = repository.list_scoped_vessels(scope)
    vessel_name = vessels[0].get("name") if len(vessels) == 1 else "SCOPED VESSELS"
    return "\n".join(
        [
            f"AUDIT COPY — {vessel_name}",
            str(grant.get("auditor_name") or "External Auditor"),
            f"Access expires {_format_expiry(grant.get('expiry_at'))}",
        ]
    )


def _format_expiry(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d-%b-%Y")
    return str(value or "")
