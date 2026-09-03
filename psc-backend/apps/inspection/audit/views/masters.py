"""Gated operational Audit master-data APIs."""

from __future__ import annotations

import uuid

from django.db import connection, transaction
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import OfficeUser
from apps.inspection.audit.models import (
    AuditQualifyingBody,
    MasterAuditQualifiedAuditor,
    MasterExternalAuditOrg,
    MasterHodAssignment,
    VesselAuditRoDelegation,
)
from apps.inspection.audit.permissions import (
    AUDIT_P_001,
    AUDIT_P_003,
    AUDIT_P_009,
    AUDIT_P_013,
    AUDIT_P_016,
    AUDIT_P_019,
    AUDIT_P_020,
    HasAnyAuditProcessPermission,
    HasAuditProcessPermission,
    can_authorize_acting_hod,
)
from apps.inspection.audit.serializers.masters import (
    AuditQualifyingBodySerializer,
    ExternalAuditOrgSerializer,
    HodAssignmentSerializer,
    OfficeUserLookupSerializer,
    QualifiedAuditorSerializer,
    VesselRoDelegationSerializer,
)


def _actor_id(request) -> str:
    return str(getattr(request.user, "id", "") or getattr(request.user, "username", "") or "system")


def _forbidden(message: str) -> Response:
    return Response({"error": "FORBIDDEN", "message": message}, status=status.HTTP_403_FORBIDDEN)


def _normalized_identifier(value: object) -> str:
    return str(value or "").strip().casefold()


def _office_role_names_by_identifier(identifiers: set[str]) -> dict[str, str]:
    role_by_identifier: dict[str, str] = {}
    if not identifiers:
        return role_by_identifier

    sql_server = """
        SELECT TOP 1 mr.role_name
        FROM mapping_role_user mru
        INNER JOIN master_role mr
            ON mr.id = mru.role_id
           AND mr.is_active = 1
           AND mr.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(mru.userid) = LOWER(%s)
        ORDER BY mru.created_date DESC
    """
    sql_sqlite = """
        SELECT mr.role_name
        FROM mapping_role_user mru
        INNER JOIN master_role mr
            ON mr.id = mru.role_id
           AND mr.is_active = 1
           AND mr.is_deleted = 0
        WHERE mru.is_active = 1
          AND mru.is_deleted = 0
          AND LOWER(mru.userid) = LOWER(%s)
        ORDER BY mru.created_date DESC
        LIMIT 1
    """
    sql = sql_sqlite if connection.vendor == "sqlite" else sql_server

    for identifier in identifiers:
        with connection.cursor() as cursor:
            cursor.execute(sql, [identifier])
            row = cursor.fetchone()
        if row and row[0]:
            role_by_identifier[_normalized_identifier(identifier)] = str(row[0]).strip()

    return role_by_identifier


def _office_user_lookup_rows(search: str = "") -> list[dict[str, str | None]]:
    queryset = OfficeUser.objects.filter(is_active=True, is_deleted=False)
    search = str(search or "").strip()
    if search:
        queryset = queryset.filter(
            Q(employee_id__icontains=search)
            | Q(display_name__icontains=search)
            | Q(employee_name__icontains=search)
            | Q(username__icontains=search)
            | Q(employee_role__icontains=search)
            | Q(department__icontains=search)
        )

    users = list(
        queryset.values(
            "employee_id",
            "display_name",
            "employee_name",
            "username",
            "employee_role",
            "department",
        )
    )
    identifiers = {
        str(raw_identifier or "").strip()
        for user in users
        for raw_identifier in (user.get("employee_id"), user.get("username"))
        if str(raw_identifier or "").strip()
    }
    role_by_identifier = _office_role_names_by_identifier(identifiers)

    rows: list[dict[str, str | None]] = []
    for user in users:
        role_name = (
            role_by_identifier.get(_normalized_identifier(user.get("employee_id")))
            or role_by_identifier.get(_normalized_identifier(user.get("username")))
        )
        if not role_name:
            continue
        rows.append({**user, "role_name": role_name})

    return sorted(
        rows,
        key=lambda row: (
            str(row.get("display_name") or row.get("employee_name") or row.get("username") or row.get("employee_id") or "").casefold(),
            str(row.get("employee_id") or "").casefold(),
        ),
    )


def _uuid_text_or_none(value: object) -> str | None:
    if not value:
        return None
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError):
        return None


def _create_sql_server_qualified_auditor(validated_data, actor_id: str) -> MasterAuditQualifiedAuditor:
    auditor_id = uuid.uuid4()
    created_date = timezone.now()
    certificate_attachment_id = _uuid_text_or_none(validated_data.get("certificate_attachment_id"))

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO dbo.master_audit_qualified_auditor (
                id,
                user_id,
                qualification_text,
                qualification_date,
                expiry_date,
                scope_standards_csv,
                qualifying_body,
                certificate_attachment_id,
                auditor_scope,
                qualified_for_seq,
                is_active,
                created_by,
                created_date
            )
            VALUES (
                CAST(%s AS uniqueidentifier),
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                CAST(%s AS uniqueidentifier),
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            [
                str(auditor_id),
                validated_data["user_id"],
                validated_data["qualification_text"],
                validated_data["qualification_date"],
                validated_data["expiry_date"],
                validated_data["scope_standards_csv"],
                validated_data.get("qualifying_body") or None,
                certificate_attachment_id,
                validated_data["auditor_scope"],
                bool(validated_data.get("qualified_for_seq", False)),
                bool(validated_data.get("is_active", True)),
                actor_id,
                created_date,
            ],
        )

    return _fetch_sql_server_qualified_auditor(auditor_id)


def _fetch_sql_server_qualified_auditor(auditor_id) -> MasterAuditQualifiedAuditor:
    rows = list(
        MasterAuditQualifiedAuditor.objects.raw(
            """
            SELECT *
            FROM dbo.master_audit_qualified_auditor
            WHERE id = CAST(%s AS uniqueidentifier)
            """,
            [str(auditor_id)],
        )
    )
    if not rows:
        raise MasterAuditQualifiedAuditor.DoesNotExist("Qualified auditor was saved but could not be reloaded.")
    return rows[0]


def _update_sql_server_qualified_auditor(
    auditor_id,
    validated_data,
    actor_id: str,
) -> MasterAuditQualifiedAuditor:
    allowed_fields = {
        "user_id",
        "qualification_text",
        "qualification_date",
        "expiry_date",
        "scope_standards_csv",
        "qualifying_body",
        "certificate_attachment_id",
        "auditor_scope",
        "qualified_for_seq",
        "is_active",
    }
    update_data = {key: value for key, value in validated_data.items() if key in allowed_fields}
    update_data["updated_by"] = actor_id
    update_data["updated_date"] = timezone.now()

    assignments = []
    params = []
    for field_name, value in update_data.items():
        if field_name == "certificate_attachment_id":
            assignments.append("certificate_attachment_id = CAST(%s AS uniqueidentifier)")
            params.append(_uuid_text_or_none(value))
            continue
        assignments.append(f"{field_name} = %s")
        params.append(value)

    params.append(str(auditor_id))
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            UPDATE dbo.master_audit_qualified_auditor
            SET {", ".join(assignments)}
            WHERE id = CAST(%s AS uniqueidentifier)
            """,
            params,
        )

    return _fetch_sql_server_qualified_auditor(auditor_id)


class _MasterListCreateView(APIView):
    serializer_class = None
    model = None
    process_id = None
    active_field = None

    def get_queryset(self):
        queryset = self.model.objects.all().order_by("id")
        include_inactive = str(self.request.query_params.get("include_inactive", "false")).lower() in {
            "1",
            "true",
            "yes",
        }
        if self.active_field and not include_inactive:
            queryset = queryset.filter(**{self.active_field: True})
        return queryset

    def get(self, request):
        rows = self.serializer_class(self.get_queryset(), many=True).data
        return Response({"data": {"count": len(rows), "results": rows}})

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            instance = serializer.save(created_by=_actor_id(request))
        return Response({"data": self.serializer_class(instance).data}, status=status.HTTP_201_CREATED)


class _MasterDetailView(APIView):
    serializer_class = None
    model = None
    process_id = None
    active_field = None

    def _get_instance(self, id):
        try:
            return self.model.objects.get(id=id)
        except self.model.DoesNotExist as exc:
            raise Http404("Audit master record not found.") from exc

    def get(self, request, id):
        return Response({"data": self.serializer_class(self._get_instance(id)).data})

    def patch(self, request, id):
        instance = self._get_instance(id)
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        update_fields = list(serializer.validated_data)
        if hasattr(instance, "updated_by"):
            serializer.validated_data["updated_by"] = _actor_id(request)
            serializer.validated_data["updated_date"] = timezone.now()
            update_fields.extend(["updated_by", "updated_date"])
        serializer.save()
        return Response({"data": self.serializer_class(instance).data})


class OfficeUserLookupView(APIView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_009)]

    def get(self, request):
        rows = OfficeUserLookupSerializer(
            _office_user_lookup_rows(request.query_params.get("q", "")),
            many=True,
        ).data
        return Response({"data": {"count": len(rows), "results": rows}})


class QualifiedAuditorListCreateView(_MasterListCreateView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_009)]
    serializer_class = QualifiedAuditorSerializer
    model = MasterAuditQualifiedAuditor
    process_id = AUDIT_P_009
    active_field = "is_active"

    def get_queryset(self):
        queryset = super().get_queryset()
        standards = self.request.query_params.get("standards") or self.request.query_params.get("audit_standards_csv")
        if standards:
            standards_filter = Q()
            for standard in [part.strip().upper() for part in standards.split(",") if part.strip()]:
                standards_filter |= Q(scope_standards_csv__icontains=standard)
            queryset = queryset.filter(standards_filter)
        if str(self.request.query_params.get("eligible", "")).lower() in {"1", "true", "yes"}:
            queryset = queryset.filter(expiry_date__gte=timezone.localdate())
        if str(self.request.query_params.get("target_office_dept", "")).strip().upper() == "SEQ":
            queryset = queryset.filter(qualified_for_seq=True)
        return queryset

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            if connection.vendor == "sqlite":
                instance = serializer.save(created_by=_actor_id(request))
            else:
                instance = _create_sql_server_qualified_auditor(serializer.validated_data, _actor_id(request))
        return Response({"data": self.serializer_class(instance).data}, status=status.HTTP_201_CREATED)


class QualifiedAuditorDetailView(_MasterDetailView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_009)]
    serializer_class = QualifiedAuditorSerializer
    model = MasterAuditQualifiedAuditor
    process_id = AUDIT_P_009

    def _get_instance(self, id):
        if connection.vendor == "sqlite":
            return super()._get_instance(id)
        try:
            return _fetch_sql_server_qualified_auditor(id)
        except self.model.DoesNotExist as exc:
            raise Http404("Audit master record not found.") from exc

    def patch(self, request, id):
        if connection.vendor == "sqlite":
            return super().patch(request, id)

        instance = self._get_instance(id)
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            instance = _update_sql_server_qualified_auditor(
                id,
                serializer.validated_data,
                _actor_id(request),
            )
        return Response({"data": self.serializer_class(instance).data})


class AuditQualifyingBodyListCreateView(_MasterListCreateView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_009)]
    serializer_class = AuditQualifyingBodySerializer
    model = AuditQualifyingBody
    process_id = AUDIT_P_009
    active_field = "is_active"

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False).order_by("body_name")


class AuditQualifyingBodyDetailView(_MasterDetailView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_009)]
    serializer_class = AuditQualifyingBodySerializer
    model = AuditQualifyingBody
    process_id = AUDIT_P_009

    def _get_instance(self, id):
        try:
            return self.model.objects.get(id=id, is_deleted=False)
        except self.model.DoesNotExist as exc:
            raise Http404("Audit qualifying body not found.") from exc


class ExternalAuditOrgListCreateView(_MasterListCreateView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_019)]
    serializer_class = ExternalAuditOrgSerializer
    model = MasterExternalAuditOrg
    process_id = AUDIT_P_019
    active_field = "is_active"

    def get_permissions(self):
        if self.request.method == "GET":
            return [
                IsAuthenticated(),
                HasAnyAuditProcessPermission.requiring_any(AUDIT_P_001, AUDIT_P_003, AUDIT_P_013, AUDIT_P_019)(),
            ]
        return super().get_permissions()


class ExternalAuditOrgDetailView(_MasterDetailView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_019)]
    serializer_class = ExternalAuditOrgSerializer
    model = MasterExternalAuditOrg
    process_id = AUDIT_P_019


class VesselRoDelegationListCreateView(_MasterListCreateView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_020)]
    serializer_class = VesselRoDelegationSerializer
    model = VesselAuditRoDelegation
    process_id = AUDIT_P_020

    def get_queryset(self):
        queryset = super().get_queryset()
        vessel_id = self.request.query_params.get("target_vessel_id")
        standard_code = self.request.query_params.get("standard_code")
        if vessel_id:
            queryset = queryset.filter(target_vessel_id=vessel_id)
        if standard_code:
            queryset = queryset.filter(standard_code=standard_code.strip().upper())
        return queryset


class VesselRoDelegationDetailView(_MasterDetailView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_020)]
    serializer_class = VesselRoDelegationSerializer
    model = VesselAuditRoDelegation
    process_id = AUDIT_P_020


class HodCoverageListCreateView(_MasterListCreateView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_016)]
    serializer_class = HodAssignmentSerializer
    model = MasterHodAssignment
    process_id = AUDIT_P_016

    def get_queryset(self):
        queryset = super().get_queryset().order_by("dept", "-effective_from", "-created_date")
        dept = self.request.query_params.get("dept")
        include_expired = str(self.request.query_params.get("include_expired", "false")).lower() in {
            "1",
            "true",
            "yes",
        }
        if dept:
            queryset = queryset.filter(dept=dept.strip().upper())
        if not include_expired:
            today = timezone.localdate()
            queryset = queryset.filter(Q(effective_to__isnull=True) | Q(effective_to__gte=today))
        return queryset

    def post(self, request):
        payload = request.data.copy()
        payload["is_acting"] = True
        serializer = self.serializer_class(data=payload)
        serializer.is_valid(raise_exception=True)
        if not can_authorize_acting_hod(request.user, serializer.validated_data.get("user_id")):
            return _forbidden("DPA/Fleet Manager cannot assign themselves as Acting HoD.")
        with transaction.atomic():
            instance = serializer.save(created_by=_actor_id(request))
        return Response({"data": self.serializer_class(instance).data}, status=status.HTTP_201_CREATED)


class HodCoverageExpireView(APIView):
    permission_classes = [IsAuthenticated, HasAuditProcessPermission.requiring(AUDIT_P_016)]

    def post(self, request, id):
        try:
            assignment = MasterHodAssignment.objects.get(id=id, is_acting=True)
        except MasterHodAssignment.DoesNotExist as exc:
            raise Http404("Acting HoD assignment not found.") from exc
        if not can_authorize_acting_hod(request.user, assignment.user_id):
            return _forbidden("DPA/Fleet Manager cannot close their own Acting HoD assignment.")
        today = timezone.localdate()
        if assignment.effective_to is None or assignment.effective_to > today:
            assignment.effective_to = today
            assignment.save(update_fields=["effective_to"])
        return Response({"data": HodAssignmentSerializer(assignment).data})
