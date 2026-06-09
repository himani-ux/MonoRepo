"""
Inspection views per BACKEND_STRUCTURE.md Section 10.3.

Endpoints:
- GET /api/psc/inspections/ - List with filters
- POST /api/psc/inspections/ - Create new
- GET /api/psc/inspections/{id}/ - Detail
- PUT /api/psc/inspections/{id}/ - Update
- DELETE /api/psc/inspections/{id}/ - Soft delete
- POST /api/psc/inspections/{id}/submit/ - Submit for review
- POST /api/psc/inspections/{id}/pic-review/ - PIC review
- POST /api/psc/inspections/{id}/dpa-close/ - DPA close
- POST /api/psc/inspections/{id}/upload-report/ - Upload report
"""

import os
import uuid

from django.conf import settings
from django.db import transaction
from django.db.models.expressions import RawSQL
from django.http import FileResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from apps.car.follow_up_reports import is_valid_follow_up_report_token
from .models import Inspection, InspectionReport, InspectionStatus
from .deficiency_models import Deficiency, CAR
from .serializers import (
    InspectionListSerializer,
    InspectionDetailSerializer,
    InspectionCreateSerializer,
    InspectionUpdateSerializer,
    InspectionSubmitSerializer,
    InspectionPICReviewSerializer,
    InspectionDPACloseSerializer,
    InspectionReportUploadSerializer,
    InspectionReportSerializer,
)
from .permissions import (
    HasVesselAccess,
    CanCreateInspection,
    CanEditInspection,
    CanDeleteInspection,
    CanSubmitInspection,
    CanPICReview,
    CanDPAClose,
)
from apps.accounts.models import RoleCodes
from apps.car.models import ActivityHistory, AuditLog
from apps.notifications.signals import notify_inspection_dpa_closed
from core.db_utils import vessel_name_annotation, vessel_code_annotation, imo_number_annotation


def create_inspection_audit_log(
    *,
    inspection_id,
    action,
    user,
    request,
    field_name=None,
    old_value=None,
    new_value=None,
    is_office_edit_assist=False,
):
    """Create a field-level audit log entry for inspection edits."""
    user_id = str(user.id) if hasattr(user, 'id') else str(user)
    user_role = getattr(user, 'role', None)

    AuditLog.objects.create(
        entity_type='INSPECTION',
        entity_id=inspection_id,
        action=action,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        performed_by=user_id,
        performed_by_role=user_role,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        is_office_edit_assist=is_office_edit_assist,
    )


def create_inspection_activity(*, inspection, event_type, event_description, user):
    """Create an inspection activity history event."""
    user_name = getattr(user, 'display_name', '') or getattr(
        user,
        'username',
        str(user.id),
    )
    ActivityHistory.objects.create(
        entity_type='INSPECTION',
        entity_id=inspection.id,
        vessel_id=inspection.vessel_id,
        event_type=event_type,
        event_description=event_description,
        performed_by=str(user.id),
        performed_by_name=user_name,
    )


def _normalize_vessel_id(value):
    """Normalize vessel identifiers for robust equality checks."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return str(uuid.UUID(text))
    except (ValueError, TypeError, AttributeError):
        return text.lower()


class InspectionListView(generics.ListAPIView):
    """
    GET /api/psc/inspections/

    List inspections with filters.
    Per BACKEND_STRUCTURE.md Section 10.3
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InspectionListSerializer

    def get_permissions(self):
        """Use create permissions for POST while keeping list access for authenticated users."""
        if self.request.method == 'POST':
            return [IsAuthenticated(), CanCreateInspection()]
        return [permission() for permission in self.permission_classes]

    def get_serializer_class(self):
        """Use create serializer for POST and list serializer for GET."""
        if self.request.method == 'POST':
            return InspectionCreateSerializer
        return InspectionListSerializer

    def get_queryset(self):
        """
        Get inspections filtered by user access and query params.
        Returns base queryset WITHOUT RawSQL annotations (safe for count).
        """
        queryset = Inspection.objects.filter(is_deleted=False)

        user = self.request.user

        # Filter by vessel access
        if user.user_type == 'VESSEL':
            # Vessel users can only see their own vessel
            queryset = queryset.filter(vessel_id=user.vessel_id)
            # VESSEL_CREW can only see inspections with deficiencies assigned to them
            if user.role == RoleCodes.VESSEL_CREW:
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(deficiencies__assigned_crew_id=user.crew_id) |
                    Q(deficiencies__assigned_crew_id=user.id)
                ).distinct()
        else:
            from core.vessel_access import apply_office_vessel_filter
            queryset = apply_office_vessel_filter(queryset, user, 'vessel_id')

        # Apply query param filters
        vessel_id = self.request.query_params.get('vessel_id')
        if vessel_id:
            queryset = queryset.filter(vessel_id=vessel_id)

        # Computed status filter (OPEN/CLOSED incorporating def_reported)
        status_filter = self.request.query_params.get('status')
        if status_filter in ('OPEN', 'CLOSED'):
            from django.db.models import Q
            queryset = queryset.annotate(
                _open_def_count=RawSQL(
                    "(SELECT COUNT(*) FROM psc_deficiency d "
                    "WHERE d.inspection_id = psc_inspection.id AND d.is_deleted = 0 "
                    "AND (d.action_code_id IS NULL OR d.action_code_id != 10))",
                    [],
                ),
                _total_def_count=RawSQL(
                    "(SELECT COUNT(*) FROM psc_deficiency d "
                    "WHERE d.inspection_id = psc_inspection.id AND d.is_deleted = 0)",
                    [],
                ),
            )
            if status_filter == 'OPEN':
                # OPEN: def_reported IS NULL (legacy)
                # OR def_reported=YES AND (no defs yet OR has open defs)
                queryset = queryset.filter(
                    Q(def_reported__isnull=True) |
                    Q(def_reported='YES', _total_def_count=0) |
                    Q(def_reported='YES', _open_def_count__gt=0)
                )
            else:
                # CLOSED: def_reported=NO
                # OR def_reported=YES AND total defs > 0 AND open defs = 0
                queryset = queryset.filter(
                    Q(def_reported='NO') |
                    Q(def_reported='YES', _total_def_count__gt=0, _open_def_count=0)
                )

        inspection_type = self.request.query_params.get('inspection_type')
        if inspection_type:
            queryset = queryset.filter(inspection_type=inspection_type)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(inspection_date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(inspection_date__lte=date_to)

        return queryset.order_by('-inspection_date', '-created_date')

    def list(self, request, *args, **kwargs):
        """Return paginated list with standard response format."""
        queryset = self.get_queryset()

        # Pagination — count on base queryset (no RawSQL annotations)
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 100)

        total_count = queryset.count()
        total_pages = (total_count + page_size - 1) // page_size

        start = (page - 1) * page_size
        end = start + page_size

        # Annotate with vessel name/code and report count AFTER slicing.
        # All annotations use scalar RawSQL subqueries to avoid SQL Server
        # GROUP BY conflicts (SQL Server can't have subqueries in GROUP BY).
        paginated_queryset = queryset[start:end]
        annotated_ids = [obj.id for obj in paginated_queryset]
        annotated_queryset = Inspection.objects.filter(
            id__in=annotated_ids
        ).annotate(
            vessel_name=vessel_name_annotation(),
            vessel_code=vessel_code_annotation(),
            report_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_inspection_report r "
                "WHERE r.inspection_id = psc_inspection.id AND r.is_deleted = 0)",
                [],
            ),
            deficiency_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_deficiency d "
                "WHERE d.inspection_id = psc_inspection.id AND d.is_deleted = 0)",
                [],
            ),
            open_deficiency_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_deficiency d "
                "WHERE d.inspection_id = psc_inspection.id AND d.is_deleted = 0 "
                "AND (d.action_code_id IS NULL OR d.action_code_id != 10))",
                [],
            ),
            closed_deficiency_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_deficiency d "
                "WHERE d.inspection_id = psc_inspection.id AND d.is_deleted = 0 "
                "AND d.action_code_id = 10)",
                [],
            ),
        ).order_by('-inspection_date', '-created_date')

        serializer = self.get_serializer(annotated_queryset, many=True)

        return Response({
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
            }
        })

    def post(self, request, *args, **kwargs):
        """
        POST /api/psc/inspections/

        Create new inspection on the contract endpoint. `/create/` remains as a
        compatibility alias.
        """
        payload = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if request.user.user_type == 'VESSEL':
            if not _normalize_vessel_id(request.user.vessel_id):
                return Response({
                    'error': 'FORBIDDEN',
                    'message': 'Your account is not mapped to a vessel.'
                }, status=status.HTTP_403_FORBIDDEN)
            payload['vessel_id'] = request.user.vessel_id

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)

        inspection = serializer.save()

        return Response({
            'data': InspectionDetailSerializer(inspection).data,
            'message': 'Inspection created successfully'
        }, status=status.HTTP_201_CREATED)


class InspectionCreateView(generics.CreateAPIView):
    """
    POST /api/psc/inspections/

    Create new inspection.
    Per BACKEND_STRUCTURE.md Section 10.3
    """
    permission_classes = [IsAuthenticated, CanCreateInspection]
    serializer_class = InspectionCreateSerializer

    def create(self, request, *args, **kwargs):
        payload = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        if request.user.user_type == 'VESSEL':
            if not _normalize_vessel_id(request.user.vessel_id):
                return Response({
                    'error': 'FORBIDDEN',
                    'message': 'Your account is not mapped to a vessel.'
                }, status=status.HTTP_403_FORBIDDEN)
            payload['vessel_id'] = request.user.vessel_id

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)

        inspection = serializer.save()

        return Response({
            'data': InspectionDetailSerializer(inspection).data,
            'message': 'Inspection created successfully'
        }, status=status.HTTP_201_CREATED)


class InspectionDetailView(generics.RetrieveAPIView):
    """
    GET /api/psc/inspections/{id}/

    Get inspection detail.
    Per BACKEND_STRUCTURE.md Section 10.3
    """
    permission_classes = [IsAuthenticated, HasVesselAccess]
    serializer_class = InspectionDetailSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Inspection.objects.filter(is_deleted=False).annotate(
            vessel_name=vessel_name_annotation(),
            vessel_code=vessel_code_annotation(),
            imo_number=imo_number_annotation(),
            deficiency_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_deficiency d "
                "WHERE d.inspection_id = psc_inspection.id AND d.is_deleted = 0)",
                [],
            ),
            open_deficiency_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_deficiency d "
                "WHERE d.inspection_id = psc_inspection.id AND d.is_deleted = 0 "
                "AND (d.action_code_id IS NULL OR d.action_code_id != 10))",
                [],
            ),
            closed_deficiency_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_deficiency d "
                "WHERE d.inspection_id = psc_inspection.id AND d.is_deleted = 0 "
                "AND d.action_code_id = 10)",
                [],
            ),
        )

    def retrieve(self, request, *args, **kwargs):
        """Return detail with standard response format."""
        instance = self.get_object()
        # VESSEL_CREW can only view inspections with deficiencies assigned to them
        if (request.user.user_type == 'VESSEL'
                and request.user.role == RoleCodes.VESSEL_CREW):
            from django.db.models import Q
            has_assignment = instance.deficiencies.filter(
                Q(assigned_crew_id=request.user.crew_id) |
                Q(assigned_crew_id=request.user.id),
                is_deleted=False,
            ).exists()
            if not has_assignment:
                return Response({
                    'error': 'FORBIDDEN',
                    'message': 'You can only view inspections assigned to you.'
                }, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance)
        return Response({
            'data': serializer.data
        })


class InspectionUpdateView(generics.UpdateAPIView):
    """
    PUT /api/psc/inspections/{id}/

    Update inspection.
    Per BACKEND_STRUCTURE.md Section 10.3
    """
    permission_classes = [IsAuthenticated, HasVesselAccess, CanEditInspection]
    serializer_class = InspectionUpdateSerializer
    lookup_field = 'id'

    def get_queryset(self):
        return Inspection.objects.filter(is_deleted=False)

    def update(self, request, *args, **kwargs):
        """Update inspection with standard response format."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        changed_fields = []
        for field_name, new_value in serializer.validated_data.items():
            old_value = getattr(instance, field_name)
            if old_value != new_value:
                changed_fields.append((field_name, old_value, new_value))

        is_office_edit_assist = request.user.user_type == 'OFFICE'
        is_post_submit_edit = instance.status != InspectionStatus.DRAFT
        if is_post_submit_edit:
            serializer.validated_data['revision_no'] = instance.revision_no + 1

        inspection = serializer.save()

        if changed_fields:
            changed_field_names = ','.join(field_name for field_name, _, _ in changed_fields)
            create_inspection_audit_log(
                inspection_id=inspection.id,
                action='UPDATE',
                field_name='MULTI_FIELD_UPDATE',
                old_value=None,
                new_value=changed_field_names,
                user=request.user,
                request=request,
                is_office_edit_assist=is_office_edit_assist,
            )

        # Record detention remark in activity history if provided
        detention_reason = request.data.get('detention_reason', '').strip()
        if inspection.is_detention and detention_reason:
            user = request.user
            user_name = getattr(user, 'display_name', None) or getattr(user, 'username', str(user.id))
            ActivityHistory.objects.create(
                entity_type='INSPECTION',
                entity_id=str(inspection.id),
                vessel_id=str(inspection.vessel_id) if inspection.vessel_id else None,
                event_type='DETENTION_REMARK',
                event_description=f'Detention remark: {detention_reason}',
                performed_by=str(user.id),
                performed_by_name=user_name,
            )

        return Response({
            'data': InspectionDetailSerializer(inspection).data,
            'message': 'Inspection updated successfully'
        })


class InspectionDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/psc/inspections/{id}/

    Soft delete inspection.
    Per BACKEND_STRUCTURE.md Section 10.3
    """
    permission_classes = [IsAuthenticated, HasVesselAccess, CanDeleteInspection]
    lookup_field = 'id'

    def get_queryset(self):
        return Inspection.objects.filter(is_deleted=False)

    def destroy(self, request, *args, **kwargs):
        """Soft delete inspection."""
        instance = self.get_object()
        updated_by = str(request.user.id)

        with transaction.atomic():
            related_deficiencies = Deficiency.objects.filter(
                inspection=instance,
                is_deleted=False,
            )
            related_car_ids = list(
                related_deficiencies.exclude(car_id__isnull=True).values_list('car_id', flat=True)
            )

            related_deficiencies.update(
                is_deleted=True,
                updated_by=updated_by,
            )

            if related_car_ids:
                CAR.objects.filter(
                    id__in=related_car_ids,
                    is_deleted=False,
                ).update(
                    is_deleted=True,
                    updated_by=updated_by,
                )

            instance.is_deleted = True
            instance.updated_by = updated_by
            instance.sync_version += 1
            instance.save(update_fields=['is_deleted', 'updated_by', 'sync_version', 'updated_date'])

        return Response({
            'message': 'Inspection deleted successfully'
        }, status=status.HTTP_200_OK)


class InspectionSubmitView(APIView):
    """
    POST /api/psc/inspections/{id}/submit/

    Submit inspection for review.
    Per BACKEND_STRUCTURE.md Section 10.3
    """
    permission_classes = [IsAuthenticated, HasVesselAccess, CanSubmitInspection]

    def get_object(self):
        inspection_id = self.kwargs.get('id')
        try:
            inspection = Inspection.objects.get(id=inspection_id, is_deleted=False)
            self.check_object_permissions(self.request, inspection)
            return inspection
        except Inspection.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        """Submit inspection."""
        inspection = self.get_object()
        if not inspection:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Inspection not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = InspectionSubmitSerializer(
            data={},
            context={'inspection': inspection, 'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # Update status
        inspection.status = InspectionStatus.SUBMITTED
        inspection.updated_by = str(request.user.id)
        inspection.sync_version += 1
        inspection.save()

        create_inspection_activity(
            inspection=inspection,
            event_type='INSPECTION_SUBMITTED',
            event_description='Inspection submitted for office review',
            user=request.user,
        )

        return Response({
            'data': {'id': str(inspection.id), 'status': inspection.status},
            'message': 'Inspection submitted successfully'
        })


class InspectionPICReviewView(APIView):
    """
    POST /api/psc/inspections/{id}/pic-review/

    PIC reviews inspection.
    Per BACKEND_STRUCTURE.md Section 10.3
    """
    permission_classes = [IsAuthenticated, CanPICReview]

    def get_object(self):
        inspection_id = self.kwargs.get('id')
        try:
            inspection = Inspection.objects.get(id=inspection_id, is_deleted=False)
            self.check_object_permissions(self.request, inspection)
            return inspection
        except Inspection.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        """PIC review inspection."""
        inspection = self.get_object()
        if not inspection:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Inspection not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = InspectionPICReviewSerializer(
            data=request.data,
            context={'inspection': inspection, 'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # Update status and review info
        inspection.status = InspectionStatus.PIC_REVIEWED
        inspection.pic_comment = serializer.validated_data['comment']
        inspection.pic_reviewed_by = str(request.user.id)
        inspection.pic_reviewed_at = timezone.now()
        inspection.updated_by = str(request.user.id)
        inspection.sync_version += 1
        inspection.save()

        create_inspection_activity(
            inspection=inspection,
            event_type='INSPECTION_PIC_REVIEWED',
            event_description='Inspection reviewed by PIC',
            user=request.user,
        )

        return Response({
            'data': {'id': str(inspection.id), 'status': inspection.status},
            'message': 'Inspection reviewed successfully'
        })


class InspectionDPACloseView(APIView):
    """
    POST /api/psc/inspections/{id}/dpa-close/

    DPA closes inspection.
    Per BACKEND_STRUCTURE.md Section 10.3
    """
    permission_classes = [IsAuthenticated, CanDPAClose]

    def get_object(self):
        inspection_id = self.kwargs.get('id')
        try:
            inspection = Inspection.objects.get(id=inspection_id, is_deleted=False)
            self.check_object_permissions(self.request, inspection)
            return inspection
        except Inspection.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        """DPA close inspection."""
        inspection = self.get_object()
        if not inspection:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Inspection not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = InspectionDPACloseSerializer(
            data=request.data,
            context={'inspection': inspection, 'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # Update status and close info
        inspection.status = InspectionStatus.DPA_CLOSED
        inspection.dpa_comment = serializer.validated_data['comment']
        inspection.dpa_closed_by = str(request.user.id)
        inspection.dpa_closed_at = timezone.now()
        inspection.updated_by = str(request.user.id)
        inspection.sync_version += 1
        inspection.save()

        create_inspection_activity(
            inspection=inspection,
            event_type='INSPECTION_DPA_CLOSED',
            event_description='Inspection closed by DPA',
            user=request.user,
        )
        if inspection.vessel_id:
            notify_inspection_dpa_closed(inspection, str(inspection.vessel_id))

        return Response({
            'data': {'id': str(inspection.id), 'status': inspection.status},
            'message': 'Inspection closed successfully'
        })


class InspectionUploadReportView(APIView):
    """
    POST /api/psc/inspections/{id}/upload-report/

    Upload inspection report file.
    Per BACKEND_STRUCTURE.md Section 10.3
    """
    permission_classes = [IsAuthenticated, HasVesselAccess]
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self):
        inspection_id = self.kwargs.get('id')
        try:
            inspection = Inspection.objects.get(id=inspection_id, is_deleted=False)
            self.check_object_permissions(self.request, inspection)
            return inspection
        except Inspection.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        """Upload report file."""
        inspection = self.get_object()
        if not inspection:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Inspection not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = InspectionReportUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uploaded_file = serializer.validated_data['file']
        description = serializer.validated_data.get('description', '')

        # Generate file path
        # Pattern: /psc/{vessel_id}/inspections/{inspection_id}/{filename}
        file_ext = os.path.splitext(uploaded_file.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        relative_path = f"psc/{inspection.vessel_id}/inspections/{inspection.id}/{unique_filename}"

        # Full path for storage.
        # Prefer UPLOAD_BASE_PATH from core/settings.py and keep PSC_UPLOAD_PATH as compatibility fallback.
        upload_base = (
            getattr(settings, 'UPLOAD_BASE_PATH', None)
            or getattr(settings, 'PSC_UPLOAD_PATH', None)
            or (settings.BASE_DIR / 'uploads')
        )
        full_path = os.path.join(str(upload_base), relative_path)

        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Save file
        with open(full_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Create report record
        report = InspectionReport.objects.create(
            inspection=inspection,
            file_name=uploaded_file.name,
            file_path=relative_path,
            file_size=uploaded_file.size,
            mime_type=uploaded_file.content_type,
            description=description,
            uploaded_by=str(request.user.id),
        )

        return Response({
            'data': InspectionReportSerializer(report).data,
            'message': 'Report uploaded successfully'
        }, status=status.HTTP_201_CREATED)


class InspectionReportViewFileView(APIView):
    """
    GET /api/psc/inspections/reports/{report_id}/view/

    Inline file view for inspection report attachments. Exported PDFs use a
    signed report_token so the file link works outside an authenticated session.
    """
    permission_classes = [AllowAny]

    def get(self, request, report_id, *args, **kwargs):
        try:
            report = InspectionReport.objects.select_related('inspection').get(
                id=report_id,
                is_deleted=False,
            )
        except InspectionReport.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Inspection report not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        is_authenticated = bool(getattr(request.user, 'is_authenticated', False))
        report_token = request.query_params.get('report_token')
        has_valid_report_token = is_valid_follow_up_report_token(
            report_token,
            report_id=report.id,
            inspection_id=report.inspection_id,
        )
        if not is_authenticated and not has_valid_report_token:
            return Response({
                'error': 'AUTHENTICATION_REQUIRED',
                'message': 'Authentication or a valid report link is required.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        file_path = report.file_path or ''
        if not file_path:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Inspection report file path is missing.'
            }, status=status.HTTP_404_NOT_FOUND)

        if os.path.isabs(file_path):
            absolute_path = file_path
        else:
            upload_base = (
                getattr(settings, 'UPLOAD_BASE_PATH', None)
                or getattr(settings, 'PSC_UPLOAD_PATH', None)
                or (settings.BASE_DIR / 'uploads')
            )
            absolute_path = os.path.join(str(upload_base), file_path.lstrip('/'))

        if not os.path.exists(absolute_path):
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Inspection report file not found on disk.'
            }, status=status.HTTP_404_NOT_FOUND)

        content_type = report.mime_type or 'application/octet-stream'
        response = FileResponse(open(absolute_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(report.file_name)}"'
        return response
