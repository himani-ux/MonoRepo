"""
Inspection report export views.

Source: BACKEND_STRUCTURE.md Section 10.3
Implements: PRD.md FEAT-RPT-002
"""

import io
import zipfile
from datetime import datetime

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.db import connection
from django.shortcuts import get_object_or_404

from apps.accounts.models import RoleCodes
from apps.car.evidence_links import attach_report_evidence_urls
from apps.car.follow_up_reports import attach_follow_up_reports
from apps.inspection.deficiency_models import CAR
from apps.car.serializers import CARDetailSerializer
from apps.car.reports import generate_car_pdf
from .models import Inspection
from .deficiency_models import Deficiency
from .reports import generate_deficiency_excel
from .permissions import HasVesselAccess, IsAuthenticated as PSCIsAuthenticated


def _lookup_vessel_names(vessel_ids):
    """Look up vessel names from VesselData using raw SQL (char(32) -> uniqueidentifier CAST)."""
    vessel_names = {}
    if vessel_ids:
        def to_uuid_str(vid):
            s = str(vid).replace('-', '')
            return f'{s[:8]}-{s[8:12]}-{s[12:16]}-{s[16:20]}-{s[20:]}'

        placeholders = ','.join(['CAST(%s AS uniqueidentifier)'] * len(vessel_ids))
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT id, vesselName FROM VesselData WHERE id IN ({placeholders})",
                    [to_uuid_str(vid) for vid in vessel_ids],
                )
                vessel_names = {str(row[0]).replace('-', '').lower(): row[1] for row in cursor.fetchall()}
        except Exception:
            vessel_names = {}
    return vessel_names


def _attach_vessel_name_to_car_data(car_data, vessel_name):
    """Populate vessel name fields expected by the CAR PDF generator."""
    vessel_name = str(vessel_name or '').strip()
    if not vessel_name:
        return car_data

    inspection = car_data.get('inspection') or {}
    inspection.setdefault('vessel', {})
    inspection['vessel']['name'] = inspection['vessel'].get('name') or vessel_name
    inspection['vessel_name'] = inspection.get('vessel_name') or vessel_name
    car_data['inspection'] = inspection

    car_data['vessel_name'] = car_data.get('vessel_name') or vessel_name
    car_data['vessel'] = car_data.get('vessel') or {}
    car_data['vessel']['name'] = car_data['vessel'].get('name') or vessel_name
    return car_data


class DeficiencyExcelExportView(APIView):
    """
    GET /api/psc/inspections/export-excel/

    Export deficiencies to Excel with inspection and CAR context.
    Supports same filters as InspectionListView.

    Source: BACKEND_STRUCTURE.md Section 10.3
    Implements: PRD.md FEAT-RPT-002
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        # Build inspection queryset with filters (same as InspectionListView)
        queryset = Inspection.objects.filter(is_deleted=False)

        # Vessel access control
        if user.user_type == 'VESSEL':
            queryset = queryset.filter(vessel_id=user.vessel_id)
        else:
            from core.vessel_access import apply_office_vessel_filter
            queryset = apply_office_vessel_filter(queryset, user, 'vessel_id')

        # Apply filters
        filters = {}
        vessel_id = request.query_params.get('vessel_id')
        if vessel_id:
            queryset = queryset.filter(vessel_id=vessel_id)
            filters['vessel_id'] = vessel_id

        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            filters['status'] = status_filter

        inspection_type = request.query_params.get('inspection_type')
        if inspection_type:
            queryset = queryset.filter(inspection_type=inspection_type)
            filters['inspection_type'] = inspection_type

        date_from = request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(inspection_date__gte=date_from)
            filters['date_from'] = date_from

        date_to = request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(inspection_date__lte=date_to)
            filters['date_to'] = date_to

        # Get deficiencies for matching inspections
        inspection_ids = queryset.values_list('id', flat=True)
        deficiencies = Deficiency.objects.filter(
            inspection_id__in=inspection_ids,
            is_deleted=False,
        ).select_related(
            'inspection',
            'car',
        )

        # Crew members can only export their assigned deficiencies
        if user.user_type == 'VESSEL' and user.role == 'VESSEL_CREW':
            from django.db.models import Q
            deficiencies = deficiencies.filter(
                Q(assigned_crew_id=user.crew_id) |
                Q(assigned_crew_id=user.id)
            )

        deficiencies = deficiencies.order_by(
            'inspection__inspection_date',
            'inspection__id',
            'sequence_no',
        )

        # Build vessel name lookup for export
        vessel_ids = set(d.inspection.vessel_id for d in deficiencies if d.inspection and d.inspection.vessel_id)
        vessel_names = _lookup_vessel_names(vessel_ids)

        # Annotate CAR data for the export
        deficiency_data = []
        for deficiency in deficiencies:
            inspection = deficiency.inspection
            car = deficiency.car

            car_data = {}
            if car:
                # Count evidence and actions
                evidence_count = car.evidence.filter(is_deleted=False).count() if hasattr(car, 'evidence') else 0
                actions_count = car.corrective_actions.filter(is_deleted=False).count() if hasattr(car, 'corrective_actions') else 0

                car_data = {
                    'car_number': car.car_number,
                    'status': car.status,
                    'status_display': car.get_status_display(),
                    'root_cause_summary': car.root_cause_summary,
                    'target_date': str(car.target_date) if car.target_date else None,
                    'evidence_count': evidence_count,
                    'actions_count': actions_count,
                }

            deficiency_data.append({
                'def_code': deficiency.def_code,
                'description': deficiency.description,
                'action_code': deficiency.action_code,
                'target_date': str(deficiency.target_date) if deficiency.target_date else None,
                'is_cleared': deficiency.is_cleared,
                'cleared_date': str(deficiency.cleared_date) if deficiency.cleared_date else None,
                'inspection': {
                    'vessel_name': vessel_names.get(str(inspection.vessel_id).replace('-', '').lower(), str(inspection.vessel_id)),
                    'inspection_type': inspection.inspection_type,
                    'inspection_date': str(inspection.inspection_date),
                    'port_place': inspection.port_place,
                    'is_detention': inspection.is_detention,
                },
                'car': car_data,
            })

        filters['total_count'] = len(deficiency_data)

        # Generate Excel
        excel_bytes = generate_deficiency_excel(deficiency_data, filters)

        # Return as file download
        filename = f"Deficiency_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        response = HttpResponse(
            excel_bytes,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class BulkCARExportView(APIView):
    """
    GET /api/psc/inspections/{inspection_id}/cars/export-pdf/

    Download all CAR PDFs for an inspection as a ZIP file.
    If only one CAR exists, returns the PDF directly.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, inspection_id, *args, **kwargs):
        inspection = get_object_or_404(Inspection, id=inspection_id, is_deleted=False)
        audience = (request.query_params.get('audience') or 'internal').strip().lower()
        if audience not in {'internal', 'external'}:
            return Response(
                {
                    'error': 'VALIDATION_ERROR',
                    'message': "Invalid audience. Use 'internal' or 'external'.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Vessel access check
        access_permission = HasVesselAccess()
        if not access_permission.has_object_permission(request, self, inspection):
            return Response(
                {'error': access_permission.message},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get all CARs linked to this inspection's deficiencies
        cars = CAR.objects.filter(
            deficiency__inspection_id=inspection_id,
            is_deleted=False,
        ).select_related(
            'deficiency__inspection'
        ).prefetch_related(
            'corrective_actions',
            'evidence',
            'clc_mappings',
            'physical_verifications',
        )

        if not cars.exists():
            return Response(
                {'error': 'No CARs found for this inspection.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        car_list = list(cars)
        vessel_name = ''
        if inspection.vessel_id:
            vessel_name = _lookup_vessel_names({inspection.vessel_id}).get(
                str(inspection.vessel_id).replace('-', '').lower(),
                '',
            )
        if not vessel_name and request.user.user_type == 'VESSEL':
            vessel_name = str(getattr(request.user, 'vessel_name', '') or '').strip()

        # Single CAR — return PDF directly (no zip overhead)
        if len(car_list) == 1:
            car = car_list[0]
            serializer = CARDetailSerializer(car, context={'request': request})
            car_data = attach_report_evidence_urls(
                request,
                car_id=car.id,
                car_data=serializer.data,
            )
            car_data = attach_follow_up_reports(car_data, request=request)
            car_data = _attach_vessel_name_to_car_data(car_data, vessel_name)
            pdf_bytes = generate_car_pdf(car_data, audience=audience)
            car_number = car_data.get('car_number', 'CAR')
            audience_suffix = 'External' if audience == 'external' else 'Internal'
            filename = (
                f"{car_number.replace('-', '_')}_Report_{audience_suffix}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response

        # Multiple CARs — generate ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for car in car_list:
                serializer = CARDetailSerializer(car, context={'request': request})
                car_data = attach_report_evidence_urls(
                    request,
                    car_id=car.id,
                    car_data=serializer.data,
                )
                car_data = attach_follow_up_reports(car_data, request=request)
                car_data = _attach_vessel_name_to_car_data(car_data, vessel_name)
                pdf_bytes = generate_car_pdf(car_data, audience=audience)
                car_number = car_data.get('car_number', 'CAR')
                audience_suffix = 'External' if audience == 'external' else 'Internal'
                zf.writestr(
                    f"{car_number.replace('-', '_')}_Report_{audience_suffix}.pdf",
                    pdf_bytes,
                )

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audience_suffix = 'External' if audience == 'external' else 'Internal'
        filename = f"CARs_Inspection_{audience_suffix}_{timestamp}.zip"

        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
