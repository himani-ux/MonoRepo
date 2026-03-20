"""
CAR views per BACKEND_STRUCTURE.md Sections 10.5-10.8.

Endpoints:
- GET /api/psc/cars/ - List CARs with filters
- GET /api/psc/cars/{id}/ - CAR detail
- PUT /api/psc/cars/{id}/ - Update CAR
- POST /api/psc/cars/{id}/submit/ - Submit for PIC review
- POST /api/psc/cars/{id}/pic-accept/ - PIC accept
- POST /api/psc/cars/{id}/rework/ - Request rework
- POST /api/psc/cars/{id}/dpa-close/ - DPA close
- POST /api/psc/cars/{id}/reopen/ - Reopen (DPA only)
- POST /api/psc/cars/{car_id}/evidence/ - Upload evidence
- DELETE /api/psc/evidence/{id}/ - Delete evidence
- POST /api/psc/cars/{car_id}/actions/ - Add corrective action
- PUT /api/psc/actions/{id}/ - Update corrective action
- POST /api/psc/actions/{id}/complete/ - Complete corrective action
- POST /api/psc/cars/{car_id}/physical-verification/ - Create PV
- PUT /api/psc/physical-verifications/{id}/ - Update PV
- POST /api/psc/physical-verifications/{id}/close/ - Close PV
"""

import json
import os
import uuid
import logging
from datetime import date
import uuid
from core.vessel_access import apply_office_vessel_filter
from django.conf import settings
from django.db.models import Q
from django.db.models.expressions import RawSQL
from django.utils import timezone
from django.http import FileResponse
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from apps.accounts.models import RoleCodes, MasterAppliedRank
from core.db_utils import car_vessel_name_annotation, car_vessel_code_annotation
from apps.inspection.deficiency_models import CAR, CARStatus, Deficiency
from .models import (
    CorrectiveAction,
    Evidence,
    CarClcMapping,
    ActivityHistory,
    PhysicalVerification,
    PVStatus,
    AuditLog,
)
from .serializers import (
    CARListSerializer,
    CARDetailSerializer,
    CARUpdateSerializer,
    CARSubmitSerializer,
    CARPICAcceptSerializer,
    CARReworkSerializer,
    CARDPACloseSerializer,
    CARReopenSerializer,
    CorrectiveActionSerializer,
    CorrectiveActionCreateSerializer,
    CorrectiveActionUpdateSerializer,
    CorrectiveActionCompleteSerializer,
    EvidenceSerializer,
    EvidenceUploadSerializer,
    PhysicalVerificationSerializer,
    PhysicalVerificationCreateSerializer,
    PhysicalVerificationCloseSerializer,
)
from .permissions import (
    CanEditCAR,
    CanSubmitCAR,
    CanPICAcceptCAR,
    CanRequestRework,
    CanDPACloseCAR,
    CanReopenCAR,
    CanUploadEvidence,
    CanDeleteEvidence,
    CanManageAction,
    CanCompleteAction,
    CanCreatePV,
    CanClosePV,
)
from .evidence_links import is_valid_report_evidence_token
from apps.notifications.signals import (
    notify_car_submitted,
    notify_car_submitted_to_dpa,
    notify_car_pic_accepted,
    notify_car_rework_requested,
    notify_car_reopened,
    notify_car_dpa_closed,
    notify_physical_verification_created,
)

logger = logging.getLogger(__name__)


def _compact_uuid_text(value):
    """Return UUID in 32-char compact form when possible."""
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return uuid.UUID(raw).hex
    except (ValueError, TypeError, AttributeError):
        return raw.replace('-', '')


def _resolve_rank_label(rank_value):
    """Resolve rank text from UUID rank id or plain-text fallback."""
    from apps.accounts.utils import get_rank_name_by_id

    rank_name = get_rank_name_by_id(rank_value)
    if rank_name:
        return rank_name
    raw_rank = str(rank_value or "").strip()
    return raw_rank or None


def _hydrate_deficiency_owner_fields(deficiency):
    """
    Backfill owner metadata for legacy deficiencies where owner fields are null.
    Keeps behavior non-destructive and only updates missing values.
    """
    if not deficiency or not deficiency.assigned_crew_id:
        return
    if deficiency.owner_name and deficiency.owner_rank:
        return

    from apps.accounts.models import HRM501

    try:
        owner = HRM501.objects.filter(
            CrewID=str(deficiency.assigned_crew_id),
            is_deleted=False,
        ).order_by("-is_active").first()
    except Exception:
        # Test SQLite and degraded environments may not include unmanaged HRM tables.
        return
    if not owner:
        return

    update_fields = []
    if not deficiency.owner_name:
        deficiency.owner_name = owner.full_name or str(deficiency.assigned_crew_id)
        update_fields.append("owner_name")
    if not deficiency.owner_rank:
        deficiency.owner_rank = _resolve_rank_label(owner.rank_name)
        update_fields.append("owner_rank")

    if update_fields:
        deficiency.save(update_fields=update_fields)


# =============================================================================
# HELPER: Create activity history record
# =============================================================================

def create_activity(entity_type, entity_id, vessel_id, event_type, description, user, metadata=None):
    """Create an activity history record."""
    user_id = str(user.id) if hasattr(user, 'id') else str(user)
    user_name = getattr(user, 'display_name', '') or getattr(user, 'username', str(user))

    ActivityHistory.objects.create(
        entity_type=entity_type,
        entity_id=entity_id,
        vessel_id=vessel_id,
        event_type=event_type,
        event_description=description,
        performed_by=user_id,
        performed_by_name=user_name,
        metadata=json.dumps(metadata) if metadata else None,
    )


def create_audit_log(entity_type, entity_id, action, user, field_name=None,
                     old_value=None, new_value=None, request=None, is_edit_assist=False):
    """Create an audit log record."""
    user_id = str(user.id) if hasattr(user, 'id') else str(user)
    user_role = getattr(user, 'role', None)

    AuditLog.objects.create(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        performed_by=user_id,
        performed_by_role=user_role,
        ip_address=request.META.get('REMOTE_ADDR') if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else None,
        is_office_edit_assist=is_edit_assist,
    )


def _get_vessel_id_from_car(car):
    """Get vessel_id from a CAR by traversing deficiency -> inspection."""
    try:
        return car.deficiency.inspection.vessel_id
    except (Deficiency.DoesNotExist, AttributeError):
        return None


# =============================================================================
# CAR VIEWS
# =============================================================================

class CARListView(generics.ListAPIView):
    """
    GET /api/psc/cars/

    List CARs with filters.
    Per BACKEND_STRUCTURE.md Section 10.5
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CARListSerializer

    def get_queryset(self):
        """
        Get CARs filtered by user access and query params.
        Returns base queryset WITHOUT RawSQL annotations (safe for count).
        """
        print("=== ✅ FIXED get_queryset CALLED ===")
        print(f"user.user_type: {self.request.user.user_type}")
        print(f"user.vessel_id: {self.request.user.vessel_id}")
        print(f"user.vessel_code: {self.request.user.vessel_code}")
        print(f"user.crew_id: {self.request.user.crew_id}")
        print(f"vessel_id param: {self.request.query_params.get('vessel_id')}")
        queryset = CAR.objects.filter(is_deleted=False)
        
        # Prefetch related data
        queryset = queryset.select_related('deficiency__inspection')
        
        user = self.request.user
        
        # Filter by vessel access
        # Crew users (most specific) FIRST
        print("Filtering by crew:", user.crew_id)
        if user.role == RoleCodes.VESSEL_CREW:
            from apps.inspection.deficiency_models import Deficiency
            from django.db.models import Q

            # Show CARs if user is either the owner OR the reviewer.
            # Owner can be stored as CrewID or UUID (legacy/mixed data),
            # reviewer is typically stored as UUID.
            user_id = str(getattr(user, 'id', '') or '')
            user_id_compact = _compact_uuid_text(user_id) or ''
            user_crew_id = str(getattr(user, 'crew_id', '') or '')
            matching_defs = Deficiency.objects.filter(
                Q(assigned_crew_id=user_crew_id) |
                Q(assigned_crew_id=user_id) |
                Q(assigned_crew_id=user_id_compact) |
                Q(reviewer_crew_id=user_crew_id) |
                Q(reviewer_crew_id=user_id) |
                Q(reviewer_crew_id=user_id_compact)
            )

            print("Total matching deficiencies:", matching_defs.count())
            print("CAR linked count:", matching_defs.filter(car__isnull=False).count())

            queryset = queryset.filter(
                deficiency__in=matching_defs
            )

        elif user.user_type == 'VESSEL':
            queryset = queryset.filter(
                deficiency__inspection__vessel_id=user.vessel_id
            )

        else:
            if user.user_type == 'OFFICE' and user.role in RoleCodes.PIC_REVIEWERS:
                # Keep existing vessel-scoped access, but always include PIC inbox items
                # so role-forwarded CARs are visible even when vessel assignment differs.
                scoped_queryset = apply_office_vessel_filter(
                    queryset,
                    user,
                    'deficiency__inspection__vessel_id'
                )
                pic_inbox_queryset = queryset.filter(
                    status__in=[CARStatus.SUBMITTED_TO_PIC, CARStatus.PIC_REVIEW]
                )
                queryset = (scoped_queryset | pic_inbox_queryset).distinct()
            elif user.user_type == 'OFFICE' and user.role == RoleCodes.DPA:
                # DPA inbox starts only after PIC submits to DPA.
                queryset = queryset.filter(
                    status__in=[CARStatus.SUBMITTED_TO_DPA, CARStatus.CLOSED]
                )
            else:
                queryset = apply_office_vessel_filter(
                    queryset,
                    user,
                    'deficiency__inspection__vessel_id'
                )
        # Apply query param filters
        vessel_id = self.request.query_params.get('vessel_id')
        if vessel_id:
            try:
                # Validate UUID format first
                uuid.UUID(vessel_id)
                queryset = queryset.filter(
                    deficiency__inspection__vessel_id=vessel_id
                )
            except (ValueError, AttributeError):
                # Invalid UUID - skip this filter
                logger.warning(f"Invalid vessel_id query parameter: {vessel_id}")
                pass
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        source_filter = self.request.query_params.get('source')
        if source_filter:
            queryset = queryset.filter(
                deficiency__inspection__inspection_type=source_filter
            )
        
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(
                deficiency__inspection__inspection_date__gte=date_from
            )
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(
                deficiency__inspection__inspection_date__lte=date_to
            )
        
        overdue = self.request.query_params.get('overdue')
        if overdue is not None:
            overdue_value = overdue.strip().lower()
            if overdue_value in ('1', 'true', 'yes'):
                queryset = queryset.filter(
                    target_date__lt=date.today()
                ).exclude(
                    status=CARStatus.CLOSED
                )
            elif overdue_value in ('0', 'false', 'no'):
                queryset = queryset.filter(
                    Q(target_date__gte=date.today()) |
                    Q(target_date__isnull=True) |
                    Q(status=CARStatus.CLOSED)
                )
        
        pv_due = self.request.query_params.get('pv_due')
        if pv_due is not None:
            pv_due_value = pv_due.strip().lower()
            if pv_due_value in ('1', 'true', 'yes'):
                queryset = queryset.filter(
                    status=CARStatus.CLOSED,
                    physical_verifications__status=PVStatus.OPEN,
                    physical_verifications__is_deleted=False,
                ).distinct()
        
        car_number = self.request.query_params.get('car_number')
        if car_number:
            queryset = queryset.filter(car_number__icontains=car_number)
        
        return queryset.order_by('-created_date')

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

        # Annotate with vessel name/code and counts AFTER slicing.
        # All annotations use scalar RawSQL subqueries to avoid SQL Server
        # GROUP BY conflicts (SQL Server can't have subqueries in GROUP BY).
        paginated_queryset = queryset[start:end]
        annotated_ids = [obj.id for obj in paginated_queryset]
        annotated_queryset = CAR.objects.filter(
            id__in=annotated_ids
        ).select_related(
            'deficiency__inspection'
        ).annotate(
            vessel_name=car_vessel_name_annotation(),
            vessel_code=car_vessel_code_annotation(),
            action_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_corrective_action a "
                "WHERE a.car_id = psc_car.id AND a.is_deleted = 0)",
                [],
            ),
            completed_action_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_corrective_action a "
                "WHERE a.car_id = psc_car.id AND a.is_deleted = 0 AND a.is_completed = 1)",
                [],
            ),
            before_evidence_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_evidence e "
                "WHERE e.car_id = psc_car.id AND e.is_deleted = 0 AND e.evidence_type = 'BEFORE')",
                [],
            ),
            after_evidence_count=RawSQL(
                "(SELECT COUNT(*) FROM psc_evidence e "
                "WHERE e.car_id = psc_car.id AND e.is_deleted = 0 AND e.evidence_type = 'AFTER')",
                [],
            ),
            pv_due=RawSQL(
                "CASE WHEN psc_car.status = 'CLOSED' "
                "AND EXISTS (SELECT 1 FROM psc_physical_verification pv "
                "WHERE pv.car_id = psc_car.id AND pv.is_deleted = 0 AND pv.status = 'OPEN') "
                "THEN 1 ELSE 0 END",
                [],
            ),
        ).order_by('-created_date')

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






class CARDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            car = CAR.objects.select_related(
                'deficiency__inspection'
            ).prefetch_related(
                'corrective_actions',
                'evidence',
                'clc_mappings',
                'physical_verifications',
            ).annotate(
                vessel_name=car_vessel_name_annotation(),
            ).get(id=id, is_deleted=False)

        except CAR.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        if request.user.user_type == 'VESSEL':
            car_vessel_id = getattr(
                car.deficiency.inspection,
                'vessel_id',
                None
            )

            if not car_vessel_id:
                return Response({'error': 'NO_VESSEL'}, status=403)

            if uuid.UUID(str(car_vessel_id)) != uuid.UUID(str(request.user.vessel_id)):
                return Response({
                    'error': 'VESSEL_MISMATCH'
                }, status=403)

        serializer = CARDetailSerializer(car, context={'request': request})
        return Response({'data': serializer.data})







class CARUpdateView(APIView):
    """
    PUT /api/psc/cars/{id}/

    Update CAR (root cause, CLC codes, target date).
    Per BACKEND_STRUCTURE.md Section 10.5
    """
    permission_classes = [IsAuthenticated, CanEditCAR]

    def get_object(self):
        car_id = self.kwargs.get('id')
        try:
            car = CAR.objects.get(id=car_id, is_deleted=False)
            self.check_object_permissions(self.request, car)
            return car
        except CAR.DoesNotExist:
            return None

    def put(self, request, *args, **kwargs):
        car = self.get_object()
        if not car:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)
     

        serializer = CARUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        is_office = request.user.user_type == 'OFFICE'

        # Track changes for audit log
        if 'root_cause_summary' in data:
            old_val = car.root_cause_summary
            car.root_cause_summary = data['root_cause_summary']
            if old_val != data['root_cause_summary']:
                create_audit_log(
                    'CAR', car.id, 'UPDATE', request.user,
                    field_name='root_cause_summary',
                    old_value=old_val,
                    new_value=data['root_cause_summary'],
                    request=request,
                    is_edit_assist=is_office,
                )

        if 'target_date' in data:
            old_val = car.target_date
            car.target_date = data['target_date']
            if old_val != data['target_date']:
                create_audit_log(
                    'CAR', car.id, 'UPDATE', request.user,
                    field_name='target_date',
                    old_value=old_val,
                    new_value=data['target_date'],
                    request=request,
                    is_edit_assist=is_office,
                )

        # Handle CLC items
        if 'clc_item_ids' in data:
            # Remove existing mappings
            CarClcMapping.objects.filter(car=car).delete()
            # Create new mappings
            custom_text = data.get('custom_cause_text', '')
            for clc_id in data['clc_item_ids']:
                CarClcMapping.objects.create(
                    car=car,
                    clc_item_id=clc_id,
                    custom_cause_text=custom_text,
                    created_by=str(request.user.id),
                )

        car.updated_by = str(request.user.id)
        car.sync_version += 1
        car.save()

        # Auto-start: ALLOTTED -> IN_PROGRESS on content edit
        from apps.inspection.workflow import auto_start_if_allotted
        auto_start_if_allotted(car)

        # Return updated detail
        car.refresh_from_db()
        detail_serializer = CARDetailSerializer(car, context={'request': request})
        return Response({
            'data': detail_serializer.data,
            'message': 'CAR updated successfully'
        })


class CARSubmitView(APIView):
    """
    POST /api/psc/cars/{id}/submit/

    Submit CAR for PIC review.
    Per BACKEND_STRUCTURE.md Section 10.5
    """
    permission_classes = [IsAuthenticated, CanSubmitCAR]

    def get_object(self):
        car_id = self.kwargs.get('id')
        try:
            car = CAR.objects.get(id=car_id, is_deleted=False)
            self.check_object_permissions(self.request, car)
            return car
        except CAR.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        car = self.get_object()
        if not car:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate submission preconditions
        serializer = CARSubmitSerializer(
            data={},
            context={'car': car, 'request': request}
        )
        serializer.is_valid(raise_exception=True)

        # Update status
        car.status = CARStatus.SUBMITTED_TO_PIC
        car.updated_by = str(request.user.id)
        car.sync_version += 1
        car.save()

        # Create activity and notification
        vessel_id = _get_vessel_id_from_car(car)
        if vessel_id:
            create_activity(
                'CAR', car.id, vessel_id, 'CAR_SUBMITTED',
                f'CAR {car.car_number} submitted for review',
                request.user
            )
            notify_car_submitted(car, vessel_id)

        return Response({
            'data': {'id': str(car.id), 'status': car.status},
            'message': 'CAR submitted successfully'
        })


class CARPICAcceptView(APIView):
    """
    POST /api/psc/cars/{id}/pic-accept/

    PIC accepts CAR.
    Per BACKEND_STRUCTURE.md Section 10.5
    """
    permission_classes = [IsAuthenticated, CanPICAcceptCAR]

    def get_object(self):
        car_id = self.kwargs.get('id')
        try:
            car = CAR.objects.get(id=car_id, is_deleted=False)
            self.check_object_permissions(self.request, car)
            return car
        except CAR.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        car = self.get_object()
        if not car:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CARPICAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update status and PIC fields
        car.status = CARStatus.PIC_REVIEW
        car.pic_comment = serializer.validated_data['comment']
        car.pic_accepted_by = str(request.user.id)
        car.pic_accepted_at = timezone.now()
        car.updated_by = str(request.user.id)
        car.sync_version += 1
        car.save()

        # Create activity and notification
        vessel_id = _get_vessel_id_from_car(car)
        if vessel_id:
            create_activity(
                'CAR', car.id, vessel_id, 'CAR_PIC_ACCEPTED',
                f'CAR {car.car_number} accepted by PIC',
                request.user
            )
            notify_car_pic_accepted(car, vessel_id)

        return Response({
            'data': {'id': str(car.id), 'status': car.status},
            'message': 'CAR accepted successfully'
        })


class CARReworkView(APIView):
    """
    POST /api/psc/cars/{id}/rework/

    Request rework on CAR.
    Per BACKEND_STRUCTURE.md Section 10.5
    REWORK_REQUESTED auto-transitions to DRAFT.
    """
    permission_classes = [IsAuthenticated, CanRequestRework]

    def get_object(self):
        car_id = self.kwargs.get('id')
        try:
            car = CAR.objects.get(id=car_id, is_deleted=False)
            self.check_object_permissions(self.request, car)
            return car
        except CAR.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        car = self.get_object()
        if not car:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CARReworkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Record rework and auto-transition to DRAFT
        old_status = car.status
        car.rework_reason = serializer.validated_data['reason']
        car.rework_requested_by = str(request.user.id)
        car.rework_requested_at = timezone.now()
        car.rework_count += 1
        car.status = CARStatus.ALLOTTED  # Auto-transition: REWORK_REQUESTED -> DRAFT
        car.updated_by = str(request.user.id)
        car.sync_version += 1
        car.save()

        # Create activity and notification
        vessel_id = _get_vessel_id_from_car(car)
        if vessel_id:
            create_activity(
                'CAR', car.id, vessel_id, 'CAR_REWORK_REQUESTED',
                f'Rework requested on CAR {car.car_number}: {serializer.validated_data["reason"][:100]}',
                request.user
            )
            notify_car_rework_requested(car, vessel_id)

        # Create audit log for rework state transition
        create_audit_log(
            'CAR', car.id, 'UPDATE', request.user,
            field_name='status',
            old_value=old_status,
            new_value=CARStatus.ALLOTTED,
            request=request,
        )

        return Response({
            'data': {'id': str(car.id), 'status': car.status},
            'message': 'Rework requested successfully'
        })


class CARDPACloseView(APIView):
    """
    POST /api/psc/cars/{id}/dpa-close/

    DPA closes CAR.
    Per BACKEND_STRUCTURE.md Section 10.5
    """
    permission_classes = [IsAuthenticated, CanDPACloseCAR]

    def get_object(self):
        car_id = self.kwargs.get('id')
        try:
            car = CAR.objects.get(id=car_id, is_deleted=False)
            self.check_object_permissions(self.request, car)
            return car
        except CAR.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        car = self.get_object()
        if not car:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CARDPACloseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Update status and DPA fields
        car.status = CARStatus.CLOSED
        car.dpa_comment = serializer.validated_data['comment']
        car.dpa_closed_by = str(request.user.id)
        car.dpa_closed_at = timezone.now()
        car.updated_by = str(request.user.id)
        car.sync_version += 1
        car.save()

        # Create activity and notification
        vessel_id = _get_vessel_id_from_car(car)
        if vessel_id:
            create_activity(
                'CAR', car.id, vessel_id, 'CAR_DPA_CLOSED',
                f'CAR {car.car_number} closed by DPA',
                request.user
            )
            notify_car_dpa_closed(car, vessel_id)

        return Response({
            'data': {'id': str(car.id), 'status': car.status},
            'message': 'CAR closed successfully'
        })


class CARReopenView(APIView):
    """
    POST /api/psc/cars/{id}/reopen/

    Reopen a DPA-closed CAR. DPA only.
    Triggers rework flow (status -> DRAFT, rework_count++).
    """
    permission_classes = [IsAuthenticated, CanReopenCAR]

    def get_object(self):
        car_id = self.kwargs.get('id')
        try:
            car = CAR.objects.get(id=car_id, is_deleted=False)
            self.check_object_permissions(self.request, car)
            return car
        except CAR.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        car = self.get_object()
        if not car:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CARReopenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Reopen -> DRAFT per PRD FEAT-CAR-008 (same as rework, vessel can edit & resubmit)
        old_status = car.status
        car.rework_reason = serializer.validated_data['reason']
        car.rework_requested_by = str(request.user.id)
        car.rework_requested_at = timezone.now()
        car.rework_count += 1
        car.status = CARStatus.ALLOTTED
        # Clear DPA close fields
        car.dpa_comment = None
        car.dpa_closed_by = None
        car.dpa_closed_at = None
        car.updated_by = str(request.user.id)
        car.sync_version += 1
        car.save()

        # Create activity and notify vessel
        vessel_id = _get_vessel_id_from_car(car)
        if vessel_id:
            create_activity(
                'CAR', car.id, vessel_id, 'CAR_REOPENED',
                f'CAR {car.car_number} reopened by DPA: {serializer.validated_data["reason"][:100]}',
                request.user
            )
            notify_car_reopened(car, vessel_id)

        # Create audit log per PRD FEAT-CAR-008
        create_audit_log(
            'CAR', car.id, 'UPDATE', request.user,
            field_name='status',
            old_value=old_status,
            new_value=CARStatus.ALLOTTED,
            request=request,
        )

        return Response({
            'data': {'id': str(car.id), 'status': car.status},
            'message': 'CAR reopened successfully'
        })


# =============================================================================
# UNIFIED WORKFLOW VIEWS
# =============================================================================

class CARWorkflowView(APIView):
    """
    POST /api/psc/cars/{id}/workflow/

    Unified workflow endpoint for all 12 named transitions.
    Body: { action: string, comment?: string }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        try:
            car = CAR.objects.select_related('deficiency__inspection').get(
                id=id, is_deleted=False
            )
        except CAR.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        from .serializers import CARWorkflowTransitionSerializer
        serializer = CARWorkflowTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        comment = serializer.validated_data.get('comment', '')

        # Heal legacy deficiencies missing denormalized owner metadata so
        # routing/visibility works consistently in workflow transitions.
        _hydrate_deficiency_owner_fields(getattr(car, "deficiency", None))

        from apps.inspection.workflow import (
            validate_workflow_transition, ACTION_LABELS, WorkflowAction,
        )

        transition, error = validate_workflow_transition(car, action, request.user, comment)
        if error:
            return Response({
                'error': 'WORKFLOW_ERROR',
                'message': error,
            }, status=status.HTTP_400_BAD_REQUEST)

        # Content validation gate for SUBMIT_TO_PIC
        if action == WorkflowAction.SUBMIT_TO_PIC:
            from .validators import validate_car_submission
            submission_errors = validate_car_submission(car)
            if submission_errors:
                return Response({
                    'error': 'VALIDATION_ERROR',
                    'message': 'CAR does not meet submission requirements.',
                    'validation_errors': submission_errors,
                }, status=status.HTTP_400_BAD_REQUEST)

        # Execute transition
        old_status = car.status
        target_status = transition['target']

        car.status = target_status
        car.last_action = action
        car.last_action_by = str(request.user.id)
        car.last_action_at = timezone.now()
        car.last_action_comment = comment if comment else None
        car.updated_by = str(request.user.id)
        car.sync_version += 1

        auto_created_pv = None
        should_auto_create_pv = False

        # Special handling for specific actions
        if action == WorkflowAction.CLOSE_CAR:
            car.dpa_comment = comment
            car.dpa_closed_by = str(request.user.id)
            car.dpa_closed_at = timezone.now()
            car.verification_pending = True

            if not PhysicalVerification.objects.filter(
                car=car,
                status=PVStatus.OPEN,
                is_deleted=False,
            ).exists():
                should_auto_create_pv = True

        elif action == WorkflowAction.REOPEN_CAR:
            car.rework_reason = comment
            car.rework_requested_by = str(request.user.id)
            car.rework_requested_at = timezone.now()
            car.rework_count += 1
            car.dpa_comment = None
            car.dpa_closed_by = None
            car.dpa_closed_at = None
            car.verification_pending = False

        elif action == WorkflowAction.REQUEST_REWORK:
            car.rework_reason = comment
            car.rework_requested_by = str(request.user.id)
            car.rework_requested_at = timezone.now()
            car.rework_count += 1

        elif action == WorkflowAction.START_PIC_REVIEW:
            car.pic_comment = comment if comment else None
            car.pic_accepted_by = str(request.user.id)
            car.pic_accepted_at = timezone.now()

        car.save()

        # Auto-assign reviewer when transitioning to PENDING_CE_REVIEW (MARK_COMPLETED action)
        # This makes CAR visible to the reviewer (CE) in their list
        if target_status == CARStatus.PENDING_CE_REVIEW and car.deficiency:
            from apps.inspection.workflow import determine_reviewer, classify_rank, RANK_OTHER
            from apps.accounts.utils import get_rank_name_by_id

            deficiency = car.deficiency
            
            # Only auto-assign if no reviewer is already set
            if not deficiency.reviewer_crew_id:
                owner_rank_for_routing = deficiency.owner_rank
                # Fallback to actor rank when owner rank is absent/non-informative.
                if (
                    (not owner_rank_for_routing or classify_rank(owner_rank_for_routing) == RANK_OTHER)
                    and getattr(request.user, 'rank', None)
                ):
                    owner_rank_for_routing = request.user.rank

                reviewer_crew, reviewer_rank_cat = determine_reviewer(
                    owner_rank_for_routing,
                    str(deficiency.inspection.vessel_id),
                )
                if reviewer_crew:
                    deficiency.reviewer_crew_id = _compact_uuid_text(reviewer_crew.id)
                    deficiency.reviewer_rank = get_rank_name_by_id(reviewer_crew.rank_name)
                    deficiency.reviewer_name = reviewer_crew.full_name
                    deficiency.save(update_fields=['reviewer_crew_id', 'reviewer_rank', 'reviewer_name'])
                    
                    logger.info(
                        f"Auto-assigned reviewer to CAR {car.car_number}: "
                        f"{reviewer_crew.full_name} ({reviewer_rank_cat})"
                    )

        if should_auto_create_pv:
            auto_created_pv = PhysicalVerification.objects.create(
                car=car,
                status=PVStatus.OPEN,
                created_by=str(request.user.id),
            )

        # Create activity
        vessel_id = _get_vessel_id_from_car(car)
        action_label = ACTION_LABELS.get(action, action)
        if vessel_id:
            create_activity(
                'CAR', car.id, vessel_id,
                f'CAR_WORKFLOW_{action}',
                f'CAR {car.car_number}: {action_label} ({old_status} → {target_status})'
                + (f' — {comment[:100]}' if comment else ''),
                request.user,
                metadata={'action': action, 'old_status': old_status, 'new_status': target_status},
            )

        # Create audit log
        create_audit_log(
            'CAR', car.id, 'WORKFLOW', request.user,
            field_name='status',
            old_value=old_status,
            new_value=target_status,
            request=request,
        )

        if auto_created_pv and vessel_id:
            try:
                notify_physical_verification_created(auto_created_pv, car, vessel_id)
            except Exception:
                logger.exception(
                    "Failed to send physical verification created notification",
                    extra={
                        'car_id': str(car.id),
                        'car_number': getattr(car, 'car_number', None),
                        'physical_verification_id': str(auto_created_pv.id),
                        'vessel_id': str(vessel_id),
                    },
                )

        # Trigger notifications based on action
        self._send_notifications(action, car, vessel_id)

        return Response({
            'data': {'id': str(car.id), 'status': car.status, 'action': action},
            'message': f'{action_label} completed successfully',
        })

    def _send_notifications(self, action, car, vessel_id):
        """Send appropriate notifications based on the workflow action."""
        from apps.inspection.workflow import WorkflowAction
        if not vessel_id:
            return
        try:
            if action == WorkflowAction.SUBMIT_TO_PIC:
                notify_car_submitted(car, vessel_id)
            elif action == WorkflowAction.SUBMIT_TO_DPA:
                notify_car_submitted_to_dpa(car, vessel_id)
            elif action == WorkflowAction.START_PIC_REVIEW:
                notify_car_pic_accepted(car, vessel_id)
            elif action in (WorkflowAction.REQUEST_REWORK, WorkflowAction.RETURN_FOR_REWORK):
                notify_car_rework_requested(car, vessel_id)
            elif action == WorkflowAction.CLOSE_CAR:
                notify_car_dpa_closed(car, vessel_id)
            elif action == WorkflowAction.REOPEN_CAR:
                notify_car_reopened(car, vessel_id)
        except Exception:
            # Notifications are best-effort, but errors must be visible in logs.
            logger.exception(
                "Failed to send CAR workflow notification",
                extra={
                    'action': action,
                    'car_id': str(car.id),
                    'car_number': getattr(car, 'car_number', None),
                    'vessel_id': str(vessel_id),
                },
            )


class CARAvailableActionsView(APIView):
    """
    GET /api/psc/cars/{id}/available-actions/

    Returns the list of workflow actions available to the current user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, id, *args, **kwargs):
        try:
            car = CAR.objects.select_related('deficiency__inspection').get(
                id=id, is_deleted=False
            )
        except CAR.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        from apps.inspection.workflow import get_available_actions, WorkflowAction
        from .validators import validate_car_submission
        actions = get_available_actions(car, request.user)

        # Omit SUBMIT_TO_PIC if content validation fails
        filtered = [
            a for a in actions
            if a['action'] != WorkflowAction.SUBMIT_TO_PIC or not validate_car_submission(car)
        ]

        return Response({
            'data': filtered,
        })


# =============================================================================
# EVIDENCE VIEWS
# =============================================================================

class EvidenceUploadView(APIView):
    """
    POST /api/psc/cars/{car_id}/evidence/

    Upload evidence file.
    Per BACKEND_STRUCTURE.md Section 10.7
    """
    permission_classes = [IsAuthenticated, CanUploadEvidence]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, car_id, *args, **kwargs):
        # Get CAR
        try:
            car = CAR.objects.select_related('deficiency__inspection').get(
                id=car_id, is_deleted=False
            )
        except CAR.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, car)

        serializer = EvidenceUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        uploaded_file = data['file']
        evidence_type = data['evidence_type']
        description = data['description']
        client_id = data.get('client_id')

        # Generate file path
        vessel_id = _get_vessel_id_from_car(car)
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        short_uuid = str(uuid.uuid4())[:4]
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        safe_filename = f"{evidence_type.lower()}_{timestamp}_{short_uuid}{file_ext}"
        relative_path = f"psc/{vessel_id}/cars/{car.id}/{safe_filename}"

        # Full path for storage
        upload_base = getattr(settings, 'UPLOAD_BASE_PATH', 'uploads')
        print(f"upload_base:{upload_base}")
        full_path = os.path.join(upload_base, relative_path)

        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Save file
        with open(full_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        # Create evidence record
        evidence = Evidence.objects.create(
            car=car,
            evidence_type=evidence_type,
            file_name=uploaded_file.name,
            file_path=relative_path,
            file_size=uploaded_file.size,
            mime_type=uploaded_file.content_type,
            description=description,
            uploaded_by=str(request.user.id),
            client_id=client_id,
        )

        # Create activity
        if vessel_id:
            create_activity(
                'EVIDENCE', evidence.id, vessel_id, 'EVIDENCE_UPLOADED',
                f'{evidence_type} evidence uploaded for CAR {car.car_number}',
                request.user
            )

        return Response({
            'data': EvidenceSerializer(evidence).data,
            'message': 'Evidence uploaded successfully'
        }, status=status.HTTP_201_CREATED)


class EvidenceDeleteView(APIView):
    """
    DELETE /api/psc/evidence/{id}/

    Soft delete evidence.
    Per BACKEND_STRUCTURE.md Section 10.7
    """
    permission_classes = [IsAuthenticated, CanDeleteEvidence]

    def delete(self, request, id, *args, **kwargs):
        try:
            evidence = Evidence.objects.select_related('car').get(
                id=id, is_deleted=False
            )
        except Evidence.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Evidence not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Soft delete
        evidence.is_deleted = True
        evidence.save()

        # Create activity
        vessel_id = _get_vessel_id_from_car(evidence.car)
        if vessel_id:
            create_activity(
                'EVIDENCE', evidence.id, vessel_id, 'EVIDENCE_DELETED',
                f'{evidence.evidence_type} evidence deleted from CAR {evidence.car.car_number}',
                request.user
            )

        return Response({
            'message': 'Evidence deleted successfully'
        })


class EvidenceViewFileView(APIView):
    """
    GET /api/psc/evidence/{id}/view/

    Authenticated inline file view for evidence attachments.
    """
    permission_classes = [AllowAny]

    def get(self, request, id, *args, **kwargs):
        try:
            evidence = Evidence.objects.select_related('car').get(
                id=id, is_deleted=False
            )
        except Evidence.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Evidence not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        is_authenticated = bool(getattr(request.user, 'is_authenticated', False))
        report_token = request.query_params.get('report_token')
        has_valid_report_token = is_valid_report_evidence_token(
            report_token,
            evidence_id=evidence.id,
            car_id=evidence.car_id,
        )
        if not is_authenticated and not has_valid_report_token:
            return Response({
                'error': 'AUTHENTICATION_REQUIRED',
                'message': 'Authentication or a valid report link is required.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        file_path = evidence.file_path or ''
        if not file_path:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Evidence file path is missing.'
            }, status=status.HTTP_404_NOT_FOUND)

        if os.path.isabs(file_path):
            absolute_path = file_path
        else:
            upload_base = getattr(settings, 'UPLOAD_BASE_PATH', settings.BASE_DIR / 'uploads')
            absolute_path = os.path.join(str(upload_base), file_path.lstrip('/'))

        if not os.path.exists(absolute_path):
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Evidence file not found on disk.'
            }, status=status.HTTP_404_NOT_FOUND)

        content_type = evidence.mime_type or 'application/octet-stream'
        response = FileResponse(open(absolute_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{evidence.file_name}"'
        return response


# =============================================================================
# CORRECTIVE ACTION VIEWS
# =============================================================================

class CorrectiveActionCreateView(APIView):
    """
    POST /api/psc/cars/{car_id}/actions/

    Add corrective action to CAR.
    Per BACKEND_STRUCTURE.md Section 10.6
    """
    permission_classes = [IsAuthenticated, CanManageAction]

    def post(self, request, car_id, *args, **kwargs):
        # Get CAR
        try:
            car = CAR.objects.select_related('deficiency__inspection').get(
                id=car_id, is_deleted=False
            )
        except CAR.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Vessel users can only add actions to editable CARs.
        # Office users can add actions at any editable status (edit-assist).
        is_office = request.user.user_type == 'OFFICE'
        vessel_allowed = [CARStatus.ALLOTTED, CARStatus.IN_PROGRESS,
                          CARStatus.PENDING_CE_REVIEW, CARStatus.PENDING_MASTER_REVIEW,
                          CARStatus.RETURNED_FOR_REWORK]
        office_allowed = [CARStatus.ALLOTTED, CARStatus.IN_PROGRESS,
                          CARStatus.PENDING_CE_REVIEW, CARStatus.PENDING_MASTER_REVIEW,
                          CARStatus.RETURNED_FOR_REWORK,
                          CARStatus.SUBMITTED_TO_PIC, CARStatus.PIC_REVIEW]
        allowed_statuses = office_allowed if is_office else vessel_allowed
        if car.status not in allowed_statuses:
            return Response({
                'error': 'INVALID_STATE',
                'message': 'Actions cannot be added to this CAR in its current status.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = CorrectiveActionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Get next sequence number
        last_action = CorrectiveAction.objects.filter(
            car=car, is_deleted=False
        ).order_by('-sequence_no').first()
        next_seq = (last_action.sequence_no + 1) if last_action else 1

        action = CorrectiveAction.objects.create(
            car=car,
            action_type=data['action_type'],
            description=data['description'],
            owner_crew_id=data.get('owner_crew_id'),
            owner_user_id=data.get('owner_user_id'),
            due_date=data.get('due_date'),
            sequence_no=next_seq,
            client_id=data.get('client_id'),
            created_by=str(request.user.id),
        )

        return Response({
            'data': CorrectiveActionSerializer(action).data,
            'message': 'Corrective action added successfully'
        }, status=status.HTTP_201_CREATED)


class CorrectiveActionUpdateView(APIView):
    """
    PUT /api/psc/actions/{id}/

    Update corrective action.
    Per BACKEND_STRUCTURE.md Section 10.6
    """
    permission_classes = [IsAuthenticated, CanManageAction]

    def put(self, request, id, *args, **kwargs):
        try:
            action = CorrectiveAction.objects.select_related('car__deficiency__inspection').get(
                id=id, is_deleted=False
            )
        except CorrectiveAction.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Corrective action not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CorrectiveActionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        changed_fields = []

        if 'description' in data:
            if action.description != data['description']:
                changed_fields.append('description')
            action.description = data['description']
        if 'owner_crew_id' in data:
            if action.owner_crew_id != data['owner_crew_id']:
                changed_fields.append('owner_crew_id')
            action.owner_crew_id = data['owner_crew_id']
        if 'owner_user_id' in data:
            if action.owner_user_id != data['owner_user_id']:
                changed_fields.append('owner_user_id')
            action.owner_user_id = data['owner_user_id']
        if 'due_date' in data:
            if action.due_date != data['due_date']:
                changed_fields.append('due_date')
            action.due_date = data['due_date']

        action.updated_by = str(request.user.id)
        action.sync_version += 1
        action.save()

        if changed_fields:
            vessel_id = _get_vessel_id_from_car(action.car)
            if vessel_id:
                create_activity(
                    'ACTION',
                    action.id,
                    vessel_id,
                    'ACTION_UPDATED',
                    f'Corrective action updated for CAR {action.car.car_number}',
                    request.user,
                    metadata={'changed_fields': changed_fields},
                )

        return Response({
            'data': CorrectiveActionSerializer(action).data,
            'message': 'Corrective action updated successfully'
        })


class CorrectiveActionCompleteView(APIView):
    """
    POST /api/psc/actions/{id}/complete/

    Mark corrective action as completed.
    Per BACKEND_STRUCTURE.md Section 10.6
    """
    permission_classes = [IsAuthenticated, CanCompleteAction]

    def get_object(self):
        action_id = self.kwargs.get('id')
        try:
            action = CorrectiveAction.objects.select_related('car').get(
                id=action_id, is_deleted=False
            )
            self.check_object_permissions(self.request, action)
            return action
        except CorrectiveAction.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        action = self.get_object()
        if not action:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Corrective action not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        if action.is_completed:
            return Response({
                'error': 'VALIDATION_ERROR',
                'message': 'Action is already completed.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = CorrectiveActionCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action.is_completed = True
        action.completed_at = timezone.now()
        action.completion_remarks = serializer.validated_data.get('completion_remarks')
        action.updated_by = str(request.user.id)
        action.sync_version += 1
        action.save()

        # Create activity
        vessel_id = _get_vessel_id_from_car(action.car)
        if vessel_id:
            create_activity(
                'ACTION', action.id, vessel_id, 'ACTION_COMPLETED',
                f'Corrective action completed for CAR {action.car.car_number}',
                request.user
            )

        return Response({
            'data': CorrectiveActionSerializer(action).data,
            'message': 'Corrective action marked as completed'
        })


class CorrectiveActionDeleteView(APIView):
    """
    DELETE /api/psc/actions/{id}/delete/

    Soft-delete corrective action (only while CAR is in DRAFT/REWORK).
    """
    permission_classes = [IsAuthenticated, CanManageAction]

    def delete(self, request, id, *args, **kwargs):
        try:
            action = CorrectiveAction.objects.select_related('car').get(
                id=id, is_deleted=False
            )
        except CorrectiveAction.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Corrective action not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Only allow delete when CAR is in editable vessel-side statuses
        allowed = [CARStatus.ALLOTTED, CARStatus.IN_PROGRESS,
                   CARStatus.PENDING_CE_REVIEW, CARStatus.PENDING_MASTER_REVIEW,
                   CARStatus.RETURNED_FOR_REWORK, CARStatus.SUBMITTED_TO_PIC, CARStatus.PIC_REVIEW, CARStatus.RETURNED_FOR_REWORK, CARStatus.SUBMITTED_TO_DPA]
        if action.car.status not in allowed:
            return Response({
                'error': 'INVALID_STATE',
                'message': 'Actions can only be deleted when CAR is in Draft or Rework status.'
            }, status=status.HTTP_400_BAD_REQUEST)

        action.is_deleted = True
        action.updated_by = str(request.user.id)
        action.sync_version += 1
        action.save()

        return Response({
            'message': 'Corrective action deleted successfully'
        }, status=status.HTTP_200_OK)


# =============================================================================
# PHYSICAL VERIFICATION VIEWS
# =============================================================================

class PhysicalVerificationCreateView(APIView):
    """
    POST /api/psc/cars/{car_id}/physical-verification/

    Create physical verification.
    Per BACKEND_STRUCTURE.md Section 10.8
    Precondition: CAR status = DPA_CLOSED
    """
    permission_classes = [IsAuthenticated, CanCreatePV]

    def post(self, request, car_id, *args, **kwargs):
        # Get CAR
        try:
            car = CAR.objects.select_related('deficiency__inspection').get(
                id=car_id, is_deleted=False
            )
        except CAR.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'CAR not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check CAR status
        if car.status != CARStatus.CLOSED:
            return Response({
                'error': 'VALIDATION_ERROR',
                'message': 'Physical verification can only be created for DPA-closed CARs.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if PhysicalVerification.objects.filter(
            car=car,
            status=PVStatus.OPEN,
            is_deleted=False,
        ).exists():
            return Response({
                'error': 'VALIDATION_ERROR',
                'message': 'CAR already has an open physical verification'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PhysicalVerificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        pv = PhysicalVerification.objects.create(
            car=car,
            scheduled_date=data.get('scheduled_date'),
            visit_port=data.get('visit_port', ''),
            verifier_user_id=data.get('verifier_user_id', ''),
            created_by=str(request.user.id),
        )

        # Create activity and notification
        vessel_id = _get_vessel_id_from_car(car)
        if vessel_id:
            create_activity(
                'CAR', car.id, vessel_id, 'PHYSICAL_VERIFICATION_CREATED',
                f'Physical verification created for CAR {car.car_number}',
                request.user
            )
            notify_physical_verification_created(pv, car, vessel_id)

        return Response({
            'data': PhysicalVerificationSerializer(pv).data,
            'message': 'Physical verification created successfully'
        }, status=status.HTTP_201_CREATED)


class PhysicalVerificationUpdateView(APIView):
    """
    PUT /api/psc/physical-verifications/{id}/

    Update physical verification details.
    Per BACKEND_STRUCTURE.md Section 10.8
    """
    permission_classes = [IsAuthenticated, CanCreatePV]

    def put(self, request, id, *args, **kwargs):
        try:
            pv = PhysicalVerification.objects.get(id=id, is_deleted=False)
        except PhysicalVerification.DoesNotExist:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Physical verification not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        # Only update OPEN PVs
        if pv.status != PVStatus.OPEN:
            return Response({
                'error': 'VALIDATION_ERROR',
                'message': 'Only open physical verifications can be updated.'
            }, status=status.HTTP_400_BAD_REQUEST)

        data = request.data
        if 'scheduled_date' in data:
            pv.scheduled_date = data['scheduled_date']
        if 'visit_port' in data:
            pv.visit_port = data['visit_port']
        if 'verifier_user_id' in data:
            pv.verifier_user_id = data['verifier_user_id']

        pv.updated_by = str(request.user.id)
        pv.save()

        return Response({
            'data': PhysicalVerificationSerializer(pv).data,
            'message': 'Physical verification updated successfully'
        })


class PhysicalVerificationCloseView(APIView):
    """
    POST /api/psc/physical-verifications/{id}/close/

    Close physical verification.
    Per BACKEND_STRUCTURE.md Section 10.8
    """
    permission_classes = [IsAuthenticated, CanClosePV]

    def get_object(self):
        pv_id = self.kwargs.get('id')
        try:
            pv = PhysicalVerification.objects.select_related('car').get(
                id=pv_id, is_deleted=False
            )
            self.check_object_permissions(self.request, pv)
            return pv
        except PhysicalVerification.DoesNotExist:
            return None

    def post(self, request, *args, **kwargs):
        pv = self.get_object()
        if not pv:
            return Response({
                'error': 'NOT_FOUND',
                'message': 'Physical verification not found.'
            }, status=status.HTTP_404_NOT_FOUND)

        if pv.status != PVStatus.OPEN:
            return Response({
                'error': 'VALIDATION_ERROR',
                'message': 'Only open physical verifications can be closed.'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PhysicalVerificationCloseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pv.status = PVStatus.CLOSED
        pv.visit_date = serializer.validated_data['visit_date']
        pv.comments = serializer.validated_data['comments']
        pv.closed_by = str(request.user.id)
        pv.closed_at = timezone.now()
        pv.updated_by = str(request.user.id)
        pv.save()

        return Response({
            'data': PhysicalVerificationSerializer(pv).data,
            'message': 'Physical verification closed successfully'
        })