from __future__ import annotations

from django.db import DatabaseError, OperationalError, ProgrammingError, connection
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.safety.authentication.permissions import HasFormPermission
from apps.safety.authentication.vessel_scope import get_scoped_vessel_ids, user_has_vessel_access
from apps.safety.models.dashboard_rollup import SafetyDashboardRollup
from apps.safety.services.composite_score import CompositeScoreService
from apps.safety.services.dashboard_ca_aging import DashboardCorrectiveActionAgingService
from apps.safety.services.dashboard_soi_compliance import DashboardSOIComplianceService
from apps.safety.services.heinrich_ratio import HeinrichRatioService
from apps.safety.services.pareto_screener import ParetoScreenerService
from apps.safety.services.repeat_root_radar import RepeatRootRadarService


def _normalize_vessel_id(value: object) -> str | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    return normalized


def _get_office_user_identifiers(user) -> list[str]:
    raw_identifiers = [
        getattr(user, "login_id", None),
        getattr(user, "employee_id", None),
        getattr(user, "id", None),
        getattr(user, "username", None),
    ]
    identifiers: list[str] = []
    for value in raw_identifiers:
        normalized = str(value).strip() if value is not None else ""
        if normalized and normalized not in identifiers:
            identifiers.append(normalized)
    return identifiers


def _has_global_office_vessel_access(user) -> bool:
    explicit_scope = getattr(user, "has_global_vessel_access", None)
    if explicit_scope is True:
        return True
    role = str(getattr(user, "role", "") or "").strip().upper()
    if role in {"DPA", "FM", "FLEET MANAGER"}:
        return True
    try:
        from core.vessel_access import has_global_office_vessel_access
    except Exception:
        return False
    return has_global_office_vessel_access(user)


def _serialize_vessel_options(rows: list[dict[str, object]]) -> list[dict[str, str]]:
    return [
        {
            "id": str(row.get("id") or "").strip(),
            "vessel_code": str(row.get("vessel_code") or "").strip(),
            "vessel_name": str(row.get("vessel_name") or "").strip(),
        }
        for row in rows
        if str(row.get("id") or "").strip()
    ]


def _lookup_vessel_rows(vessel_ids: list[str]) -> list[dict[str, object]]:
    normalized_ids = [vessel_id for vessel_id in (_normalize_vessel_id(value) for value in vessel_ids) if vessel_id]
    if not normalized_ids:
        return []

    try:
        with connection.cursor() as cursor:
            if connection.vendor == "sqlite":
                placeholders = ",".join(["%s"] * len(normalized_ids))
                cursor.execute(
                    f"""
                    SELECT id, vesselCode, vesselName
                    FROM VesselData
                    WHERE id IN ({placeholders})
                      AND COALESCE(is_deleted, 0) = 0
                    ORDER BY vesselCode, vesselName, id
                    """,
                    normalized_ids,
                )
            else:
                placeholders = ",".join(["CAST(%s AS uniqueidentifier)"] * len(normalized_ids))
                cursor.execute(
                    f"""
                    SELECT id, vesselCode, vesselName
                    FROM VesselData
                    WHERE id IN ({placeholders})
                      AND is_active = 1
                      AND is_deleted = 0
                    ORDER BY vesselCode, vesselName, id
                    """,
                    normalized_ids,
                )
            return [
                {"id": row[0], "vessel_code": row[1], "vessel_name": row[2]}
                for row in cursor.fetchall()
            ]
    except (DatabaseError, OperationalError, ProgrammingError, ValueError):
        return []


def _list_available_vessels(*, user) -> list[dict[str, str]]:
    direct_vessel_id = _normalize_vessel_id(getattr(user, "vessel_id", None))
    direct_vessel_name = str(getattr(user, "vessel_name", "") or "").strip()
    direct_vessel_code = str(getattr(user, "vessel_code", "") or "").strip()
    if direct_vessel_id and (direct_vessel_name or direct_vessel_code):
        return [
            {
                "id": direct_vessel_id,
                "vessel_code": direct_vessel_code,
                "vessel_name": direct_vessel_name or f"Vessel {direct_vessel_id}",
            }
        ]

    explicit_vessel_ids = getattr(user, "vessel_ids", None) or []
    if explicit_vessel_ids:
        rows = _lookup_vessel_rows([str(value) for value in explicit_vessel_ids])
        row_map = {str(vessel.get("id")): vessel for vessel in rows}
        options: list[dict[str, str]] = []
        for vessel_id in [vessel_id for vessel_id in (_normalize_vessel_id(value) for value in explicit_vessel_ids) if vessel_id]:
            vessel = row_map.get(vessel_id)
            if vessel is None:
                options.append(
                    {
                        "id": vessel_id,
                        "vessel_code": vessel_id,
                        "vessel_name": f"Vessel {vessel_id}",
                    }
                )
                continue
            options.append(
                {
                    "id": str(vessel.get("id") or "").strip(),
                    "vessel_code": str(vessel.get("vessel_code") or "").strip(),
                    "vessel_name": str(vessel.get("vessel_name") or "").strip(),
                }
            )
        return options

    if direct_vessel_id:
        rows = _lookup_vessel_rows([direct_vessel_id])
        if rows:
            return _serialize_vessel_options(rows)
        return [
            {
                "id": direct_vessel_id,
                "vessel_code": direct_vessel_id,
                "vessel_name": f"Vessel {direct_vessel_id}",
            }
        ]

    if getattr(user, "user_type", None) != "OFFICE":
        return []

    office_identifiers = _get_office_user_identifiers(user)
    if _has_global_office_vessel_access(user):
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, vesselCode, vesselName
                    FROM VesselData
                    WHERE COALESCE(is_deleted, 0) = 0
                    ORDER BY vesselCode, vesselName, id
                    """
                )
                return _serialize_vessel_options(
                    [
                        {"id": row[0], "vessel_code": row[1], "vessel_name": row[2]}
                        for row in cursor.fetchall()
                    ]
                )
        except (DatabaseError, OperationalError, ProgrammingError):
            return []

    if not office_identifiers:
        return []

    try:
        assigned_vessel_ids: list[str] = []
        with connection.cursor() as cursor:
            for identifier in office_identifiers:
                cursor.execute(
                    """
                    SELECT VesselId
                    FROM master_RoleByVessel
                    WHERE IsActive = 1
                      AND COALESCE(is_deleted, 0) = 0
                      AND LOWER(UserId) = LOWER(%s)
                    """,
                    [identifier],
                )
                assigned_vessel_ids.extend(
                    [
                        vessel_id
                        for vessel_id in (
                            _normalize_vessel_id(row[0]) for row in cursor.fetchall()
                        )
                        if vessel_id
                    ]
                )
    except (DatabaseError, OperationalError, ProgrammingError):
        return []

    if not assigned_vessel_ids:
        return []

    return _serialize_vessel_options(_lookup_vessel_rows(assigned_vessel_ids))


class DashboardPermissionMixin:
    form_permission_class = HasFormPermission.requiring("SAF_F_015")

    @staticmethod
    def resolve_vessel_id(*, request, explicit_vessel_id: str | None = None) -> str | None:
        if explicit_vessel_id not in (None, ""):
            if not user_has_vessel_access(request.user, explicit_vessel_id):
                raise PermissionDenied("You are not assigned to this vessel.")
            return str(explicit_vessel_id)
        if _has_global_office_vessel_access(request.user):
            return None
        vessel_ids = sorted(get_scoped_vessel_ids(request.user))
        if vessel_ids:
            return str(vessel_ids[0])
        raise PermissionDenied("No vessel scope is assigned to this user.")

    def get_permissions(self):
        return [self.form_permission_class()]


class DashboardCompositeView(DashboardPermissionMixin, generics.GenericAPIView):
    service_class = CompositeScoreService

    def get_service(self) -> CompositeScoreService:
        return self.service_class()

    def get(self, request, *args, **kwargs):
        requested_period = str(
            request.query_params.get("period") or SafetyDashboardRollup.PeriodCode.YEARS_3
        ).strip().upper()
        vessel_id = self.resolve_vessel_id(
            request=request,
            explicit_vessel_id=request.query_params.get("vessel_id"),
        )
        service = self.get_service()
        scope = service.resolve_scope(vessel_id=vessel_id, user=request.user)
        payload = service.build_rollup(scope=scope, period_code=requested_period)
        payload["available_vessels"] = _list_available_vessels(user=request.user)
        return Response(payload)


class DashboardHeinrichView(DashboardPermissionMixin, generics.GenericAPIView):
    service_class = HeinrichRatioService

    def get_service(self) -> HeinrichRatioService:
        return self.service_class()

    def get(self, request, *args, **kwargs):
        vessel_id = self.resolve_vessel_id(
            request=request,
            explicit_vessel_id=request.query_params.get("vessel_id"),
        )
        payload = self.get_service().build_panel(vessel_id=vessel_id)
        return Response(payload)


class DashboardRepeatRootCauseView(DashboardPermissionMixin, generics.GenericAPIView):
    service_class = RepeatRootRadarService

    def get_service(self) -> RepeatRootRadarService:
        return self.service_class()

    def get(self, request, *args, **kwargs):
        vessel_id = self.resolve_vessel_id(
            request=request,
            explicit_vessel_id=request.query_params.get("vessel_id"),
        )
        payload = self.get_service().build_panel(vessel_id=vessel_id)

        scope = str(request.query_params.get("scope") or "").strip().lower()
        if scope == "fleet":
            return Response(
                {
                    "items": payload["fleet"],
                    "scope": "fleet",
                    "window_end": payload["window_end"],
                    "window_start": payload["window_start"],
                }
            )
        if scope == "vessel":
            return Response(
                {
                    "items": payload["vessel"],
                    "scope": "vessel",
                    "vessel_id": vessel_id or "",
                    "window_end": payload["window_end"],
                    "window_start": payload["window_start"],
                }
            )
        return Response(payload)


class DashboardParetoView(DashboardPermissionMixin, generics.GenericAPIView):
    service_class = ParetoScreenerService

    def get_service(self) -> ParetoScreenerService:
        return self.service_class()

    def get(self, request, *args, **kwargs):
        vessel_id = self.resolve_vessel_id(
            request=request,
            explicit_vessel_id=request.query_params.get("vessel_id"),
        )
        requested_top_n = request.query_params.get("top_n")
        try:
            top_n = int(requested_top_n) if requested_top_n not in (None, "") else None
        except (TypeError, ValueError):
            top_n = None
        payload = self.get_service().build_panel(vessel_id=vessel_id, top_n=top_n)
        return Response(payload)


class DashboardSOIComplianceView(DashboardPermissionMixin, generics.GenericAPIView):
    service_class = DashboardSOIComplianceService

    def get_service(self) -> DashboardSOIComplianceService:
        return self.service_class()

    def get(self, request, *args, **kwargs):
        vessel_id = self.resolve_vessel_id(
            request=request,
            explicit_vessel_id=request.query_params.get("vessel_id"),
        )
        payload = self.get_service().build_panel(vessel_id=vessel_id)
        return Response(payload)


class DashboardCAAgingView(DashboardPermissionMixin, generics.GenericAPIView):
    service_class = DashboardCorrectiveActionAgingService

    def get_service(self) -> DashboardCorrectiveActionAgingService:
        return self.service_class()

    def get(self, request, *args, **kwargs):
        vessel_id = self.resolve_vessel_id(
            request=request,
            explicit_vessel_id=request.query_params.get("vessel_id"),
        )
        payload = self.get_service().build_panel(vessel_id=vessel_id)
        return Response(payload)
