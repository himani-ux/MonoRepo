"""
Dashboard API endpoint.

Returns aggregated metrics for the master/office dashboard in a single request.
GET /api/psc/dashboard/?vessel_id=<uuid>  (vessel_id optional, for office drill-down)
"""

from datetime import date, timedelta
from uuid import UUID

from django.db.models import Count, Q, Exists, OuterRef
from django.db.models.functions import TruncMonth

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import VesselData
from apps.inspection.models import Inspection
from apps.inspection.deficiency_models import CAR, CARStatus, Deficiency, DefStatus
from apps.car.models import CorrectiveAction, Evidence, EvidenceType
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

        # ── Build base querysets with vessel scoping ──────────────
        inspections_qs = Inspection.objects.filter(is_deleted=False)
        cars_qs = CAR.objects.filter(is_deleted=False)
        defs_qs = Deficiency.objects.filter(is_deleted=False)
        actions_qs = CorrectiveAction.objects.filter(is_deleted=False)

        if getattr(user, 'user_type', None) == 'VESSEL':
            # Vessel user — scope to their vessel
            vid = getattr(user, 'vessel_id', None)
            if vid:
                inspections_qs = inspections_qs.filter(vessel_id=vid)
                defs_qs = defs_qs.filter(inspection__vessel_id=vid)
                cars_qs = cars_qs.filter(deficiency__inspection__vessel_id=vid)
                actions_qs = actions_qs.filter(car__deficiency__inspection__vessel_id=vid)
        else:
            # Office user
            if vessel_id_param:
                # Drill-down to specific vessel
                try:
                    vid = UUID(vessel_id_param)
                except (ValueError, AttributeError):
                    return Response(
                        {'error': 'Invalid vessel_id parameter'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                inspections_qs = inspections_qs.filter(vessel_id=vid)
                defs_qs = defs_qs.filter(inspection__vessel_id=vid)
                cars_qs = cars_qs.filter(deficiency__inspection__vessel_id=vid)
                actions_qs = actions_qs.filter(car__deficiency__inspection__vessel_id=vid)
            else:
                # Apply office vessel filter (DPA sees all, others see assigned)
                inspections_qs = apply_office_vessel_filter(inspections_qs, user)
                defs_qs = apply_office_vessel_filter(
                    defs_qs, user, vessel_id_field='inspection__vessel_id'
                )
                cars_qs = apply_office_vessel_filter(
                    cars_qs, user, vessel_id_field='deficiency__inspection__vessel_id'
                )
                actions_qs = apply_office_vessel_filter(
                    actions_qs, user, vessel_id_field='car__deficiency__inspection__vessel_id'
                )

        # ── 1. Inspections by type (12 months) ───────────────────
        inspections_by_type = list(
            inspections_qs
            .filter(inspection_date__gte=one_year_ago)
            .values('inspection_type')
            .annotate(count=Count('id'))
            .order_by('inspection_type')
        )
        total_inspections_12m = sum(item['count'] for item in inspections_by_type)

        # ── 2. Open CARs count ───────────────────────────────────
        open_cars_count = cars_qs.exclude(status=CARStatus.CLOSED).count()

        # ── 3. Overdue CARs count ────────────────────────────────
        overdue_cars_count = (
            cars_qs
            .exclude(status=CARStatus.CLOSED)
            .filter(target_date__lt=today)
            .count()
        )

        # ── 4. Detentions (3 years) ──────────────────────────────
        detentions_count = (
            inspections_qs
            .filter(is_detention=True, inspection_date__gte=three_years_ago)
            .count()
        )

        # ── 5. Top 10 deficiency codes ───────────────────────────
        top_def_codes_raw = list(
            defs_qs
            .values('def_code_id')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        # Bulk lookup descriptions from master table
        code_ids = [item['def_code_id'] for item in top_def_codes_raw]
        code_map = {}
        if code_ids:
            code_map = {
                dc.def_code: dc.def_name
                for dc in PSCDefCode.objects.filter(def_code__in=code_ids)
            }
        top_def_codes = [
            {
                'def_code': item['def_code_id'],
                'def_code_description': code_map.get(item['def_code_id'], ''),
                'count': item['count'],
            }
            for item in top_def_codes_raw
        ]

        # ── 6. Pending review CARs ────────────────────────────────
        pending_defs_count = (
            cars_qs
            .filter(status__in=[
                CARStatus.PENDING_CE_REVIEW,
                CARStatus.PENDING_MASTER_REVIEW,
            ])
            .count()
        )

        # ── 7. CARs missing evidence ─────────────────────────────
        has_before = Evidence.objects.filter(
            car=OuterRef('pk'),
            evidence_type=EvidenceType.BEFORE,
            is_deleted=False,
        )
        has_after = Evidence.objects.filter(
            car=OuterRef('pk'),
            evidence_type=EvidenceType.AFTER,
            is_deleted=False,
        )
        missing_evidence_count = (
            cars_qs
            .filter(status__in=[CARStatus.ALLOTTED, CARStatus.IN_PROGRESS])
            .filter(Q(~Exists(has_before)) | Q(~Exists(has_after)))
            .count()
        )

        # ── 8. Overdue actions count ─────────────────────────────
        overdue_actions_count = (
            actions_qs
            .filter(is_completed=False, due_date__lt=today)
            .count()
        )

        # ── 9. CAR status distribution ───────────────────────────
        car_status_distribution = list(
            cars_qs
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )

        # ── 10. Monthly DEF trend (12 months) ────────────────────
        monthly_def_trend = list(
            defs_qs
            .filter(created_date__gte=one_year_ago)
            .annotate(month=TruncMonth('created_date'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        # Format dates for JSON serialization
        for item in monthly_def_trend:
            item['month'] = item['month'].strftime('%Y-%m')

        # ── 11. Vessels list (office users only) ──────────────────
        vessels = []
        if getattr(user, 'user_type', None) == 'OFFICE':
            vessels = _get_vessels_for_office_user(user)

        return Response({
            'data': {
                'inspections_by_type': inspections_by_type,
                'total_inspections_12m': total_inspections_12m,
                'open_cars_count': open_cars_count,
                'overdue_cars_count': overdue_cars_count,
                'detentions_count': detentions_count,
                'top_def_codes': top_def_codes,
                'pending_defs_count': pending_defs_count,
                'missing_evidence_count': missing_evidence_count,
                'overdue_actions_count': overdue_actions_count,
                'car_status_distribution': car_status_distribution,
                'monthly_def_trend': monthly_def_trend,
                'vessels': vessels,
            }
        })


def _get_vessels_for_office_user(user) -> list[dict]:
    """Return vessel list for the office user's dropdown."""
    if has_global_office_vessel_access(user):
        # Global PIC/DPA sees all active vessels.
        qs = VesselData.objects.filter(is_active=True, is_deleted=False)
    else:
        user_identifiers = get_office_user_identifiers(user)
        vessel_ids = get_office_user_vessel_ids(user_identifiers)
        if not vessel_ids:
            return []
        # VesselData uses native uniqueidentifier — mssql-django's id__in
        # sends char(32) which SQL Server can't convert.  Use extra() with CAST.
        hyphenated = [str(vid) for vid in vessel_ids]
        placeholders = ','.join(['CAST(%s AS uniqueidentifier)'] * len(hyphenated))
        qs = (
            VesselData.objects
            .filter(is_active=True, is_deleted=False)
            .extra(where=[f'id IN ({placeholders})'], params=hyphenated)
        )

    return [
        {
            'id': str(v.id),
            'vessel_name': v.vesselName,
            'vessel_code': v.vesselCode,
        }
        for v in qs.order_by('vesselCode')
    ]
