"""
Dashboard API endpoint.

Returns aggregated metrics for the master/office dashboard in a single request.
GET /api/psc/dashboard/?vessel_id=<uuid> (vessel_id optional, for office drill-down)
"""
from datetime import date, timedelta
from uuid import UUID

from django.db import DatabaseError, OperationalError, ProgrammingError
from django.db.models import Count, Exists, Max, Min, OuterRef, Q
from django.db.models.functions import TruncMonth
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import VesselData
from apps.car.models import CorrectiveAction, Evidence, EvidenceType
from apps.inspection.deficiency_models import CAR, CARStatus, Deficiency
from apps.inspection.models import Inspection
from apps.masters.models import PSCDefCode
from core.vessel_access import (
    apply_office_vessel_filter,
    get_office_user_identifiers,
    get_office_user_vessel_ids,
    has_global_office_vessel_access,
)


class DashboardView(APIView):
    """
    Aggregated dashboard metrics.

    Vessel users: scoped to their vessel_id.
    Office users (no vessel_id param): all assigned vessels.
    Office users (with vessel_id param): single vessel drill-down.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        vessel_id_param = request.query_params.get('vessel_id')

        today = date.today()
        one_year_ago = today - timedelta(days=365)
        three_years_ago = today - timedelta(days=365 * 3)

        inspections_qs = Inspection.objects.filter(is_deleted=False)
        cars_qs = CAR.objects.filter(is_deleted=False)
        defs_qs = Deficiency.objects.filter(is_deleted=False)
        actions_qs = CorrectiveAction.objects.filter(is_deleted=False)

        if getattr(user, 'user_type', None) == 'VESSEL':
            vid = getattr(user, 'vessel_id', None)
            if vid:
                inspections_qs = inspections_qs.filter(vessel_id=vid)
                defs_qs = defs_qs.filter(inspection__vessel_id=vid)
                cars_qs = cars_qs.filter(deficiency__inspection__vessel_id=vid)
                actions_qs = actions_qs.filter(car__deficiency__inspection__vessel_id=vid)
        else:
            if vessel_id_param:
                try:
                    vid = UUID(vessel_id_param)
                except (ValueError, AttributeError):
                    return Response(
                        {"error": "Invalid vessel_id parameter"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                inspections_qs = inspections_qs.filter(vessel_id=vid)
                defs_qs = defs_qs.filter(inspection__vessel_id=vid)
                cars_qs = cars_qs.filter(deficiency__inspection__vessel_id=vid)
                actions_qs = actions_qs.filter(car__deficiency__inspection__vessel_id=vid)
            else:
                inspections_qs = apply_office_vessel_filter(inspections_qs, user)
                defs_qs = apply_office_vessel_filter(
                    defs_qs, user, vessel_id_field="inspection__vessel_id"
                )
                cars_qs = apply_office_vessel_filter(
                    cars_qs, user, vessel_id_field="deficiency__inspection__vessel_id"
                )
                actions_qs = apply_office_vessel_filter(
                    actions_qs,
                    user,
                    vessel_id_field="car__deficiency__inspection__vessel_id",
                )

        inspections_by_type = list(
            inspections_qs
            .filter(inspection_date__gte=one_year_ago)
            .values("inspection_type")
            .annotate(count=Count("id"))
            .order_by("inspection_type")
        )
        total_inspections_12m = sum(item["count"] for item in inspections_by_type)

        open_cars_count = cars_qs.exclude(status=CARStatus.CLOSED).count()

        overdue_cars_count = (
            cars_qs.exclude(status=CARStatus.CLOSED)
            .filter(target_date__lt=today)
            .count()
        )

        detentions_count = (
            inspections_qs.filter(
                is_detention=True,
                inspection_date__gte=three_years_ago,
            ).count()
        )

        top_def_codes_raw = list(
            defs_qs.values("def_code_id")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        code_ids = [item["def_code_id"] for item in top_def_codes_raw]
        code_map = _get_def_code_name_map(code_ids)
        top_def_codes = [
            {
                "def_code": item["def_code_id"],
                "def_code_description": code_map.get(item["def_code_id"], ""),
                "count": item["count"],
            }
            for item in top_def_codes_raw
        ]

        pending_defs_count = (
            cars_qs.filter(
                status__in=[
                    CARStatus.PENDING_CE_REVIEW,
                    CARStatus.PENDING_MASTER_REVIEW,
                ]
            ).count()
        )

        has_before = Evidence.objects.filter(
            car=OuterRef("pk"),
            evidence_type=EvidenceType.BEFORE,
            is_deleted=False,
        )
        has_after = Evidence.objects.filter(
            car=OuterRef("pk"),
            evidence_type=EvidenceType.AFTER,
            is_deleted=False,
        )
        missing_evidence_count = (
            cars_qs.filter(status__in=[CARStatus.ALLOTTED, CARStatus.IN_PROGRESS])
            .filter(Q(~Exists(has_before)) | Q(~Exists(has_after)))
            .count()
        )

        overdue_actions_count = (
            actions_qs.filter(is_completed=False, due_date__lt=today).count()
        )

        car_status_distribution = list(
            cars_qs.values("status").annotate(count=Count("id")).order_by("status")
        )

        monthly_def_trend = list(
            defs_qs.filter(created_date__gte=one_year_ago)
            .annotate(month=TruncMonth("created_date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        for item in monthly_def_trend:
            if item["month"] is not None:
                item["month"] = item["month"].strftime("%Y-%m")

        repeat_deficiencies = _build_repeat_deficiencies(
            defs_qs=defs_qs,
            date_from=one_year_ago,
            date_to=today,
        )

        vessels = []
        if getattr(user, "user_type", None) == "OFFICE":
            vessels = _get_vessels_for_office_user(user)

        return Response(
            {
                "data": {
                    "inspections_by_type": inspections_by_type,
                    "total_inspections_12m": total_inspections_12m,
                    "open_cars_count": open_cars_count,
                    "overdue_cars_count": overdue_cars_count,
                    "detentions_count": detentions_count,
                    "top_def_codes": top_def_codes,
                    "pending_defs_count": pending_defs_count,
                    "missing_evidence_count": missing_evidence_count,
                    "overdue_actions_count": overdue_actions_count,
                    "car_status_distribution": car_status_distribution,
                    "monthly_def_trend": monthly_def_trend,
                    "repeat_deficiencies": repeat_deficiencies,
                    "vessels": vessels,
                }
            }
        )


def _build_repeat_deficiencies(*, defs_qs, date_from, date_to) -> list[dict]:
    repeat_base_qs = defs_qs.filter(
        inspection__inspection_date__gte=date_from,
        inspection__inspection_date__lte=date_to,
    ).exclude(Q(def_code_id__isnull=True) | Q(def_code_id=""))

    repeat_groups = list(
        repeat_base_qs.values("def_code_id")
        .annotate(
            repeat_count=Count("id"),
            range_from=Min("inspection__inspection_date"),
            range_to=Max("inspection__inspection_date"),
        )
        .filter(repeat_count__gte=2)
        .order_by("-repeat_count", "def_code_id")
    )
    if not repeat_groups:
        return []

    code_ids = [group["def_code_id"] for group in repeat_groups]
    code_map = _get_def_code_name_map(code_ids)

    vessel_rows = list(
        repeat_base_qs.filter(def_code_id__in=code_ids)
        .values("def_code_id", "inspection__vessel_id")
        .annotate(last_seen=Max("inspection__inspection_date"))
        .order_by("def_code_id", "-last_seen", "inspection__vessel_id")
    )
    vessel_details = _get_vessel_details(
        row["inspection__vessel_id"]
        for row in vessel_rows
    )

    vessels_by_code: dict[str, list[dict]] = {}
    for row in vessel_rows:
        def_code = row["def_code_id"]
        vessel_id = row["inspection__vessel_id"]
        vessel_key = str(vessel_id)
        vessel_meta = vessel_details.get(vessel_key, {})
        vessels_by_code.setdefault(def_code, []).append(
            {
                "vessel_id": vessel_key,
                "vessel_name": vessel_meta.get("vessel_name", ""),
                "vessel_code": vessel_meta.get("vessel_code", ""),
            }
        )

    for vessels in vessels_by_code.values():
        vessels.sort(
            key=lambda vessel: (
                vessel["vessel_name"] or vessel["vessel_code"] or vessel["vessel_id"]
            )
        )

    return [
        {
            "def_code": group["def_code_id"],
            "def_title": code_map.get(group["def_code_id"], ""),
            "repeat_count": group["repeat_count"],
            "classification": (
                "Systemic"
                if len(vessels_by_code.get(group["def_code_id"], [])) >= 2
                else "Recurring"
            ),
            "vessels": vessels_by_code.get(group["def_code_id"], []),
            "range_from": (
                group["range_from"].isoformat() if group["range_from"] is not None else None
            ),
            "range_to": (
                group["range_to"].isoformat() if group["range_to"] is not None else None
            ),
        }
        for group in repeat_groups
    ]


def _get_vessel_details(vessel_ids) -> dict[str, dict]:
    normalized_ids = sorted({str(vessel_id) for vessel_id in vessel_ids if vessel_id})
    if not normalized_ids:
        return {}

    placeholders = ",".join(["CAST(%s AS uniqueidentifier)"] * len(normalized_ids))
    try:
        qs = (
            VesselData.objects.filter(is_deleted=False)
            .extra(where=[f"id IN ({placeholders})"], params=normalized_ids)
        )
        return {
            str(vessel.id): {
                "vessel_name": vessel.vesselName,
                "vessel_code": vessel.vesselCode,
            }
            for vessel in qs
        }
    except (DatabaseError, OperationalError, ProgrammingError):
        return {}


def _get_def_code_name_map(code_ids) -> dict[str, str]:
    if not code_ids:
        return {}

    try:
        return {
            row.def_code: row.def_name
            for row in PSCDefCode.objects.filter(def_code__in=code_ids)
        }
    except (DatabaseError, OperationalError, ProgrammingError):
        return {}


def _get_vessels_for_office_user(user) -> list[dict]:
    """Return vessel list for the office user's dropdown."""
    if has_global_office_vessel_access(user):
        qs = VesselData.objects.filter(is_active=True, is_deleted=False)
    else:
        user_identifiers = get_office_user_identifiers(user)
        vessel_ids = get_office_user_vessel_ids(user_identifiers)
        if not vessel_ids:
            return []

        hyphenated = [str(vid) for vid in vessel_ids]
        placeholders = ",".join(["CAST(%s AS uniqueidentifier)"] * len(hyphenated))
        qs = (
            VesselData.objects.filter(is_active=True, is_deleted=False)
            .extra(where=[f"id IN ({placeholders})"], params=hyphenated)
        )

    return [
        {
            "id": str(v.id),
            "vessel_name": v.vesselName,
            "vessel_code": v.vesselCode,
        }
        for v in qs.order_by("vesselCode")
    ]