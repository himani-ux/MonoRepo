"""
Sync views per BACKEND_STRUCTURE.md Section 10.9.

Endpoints:
- POST /api/psc/sync/pull/ — Pull changes from server to vessel
- POST /api/psc/sync/push/ — Push changes from vessel to server
- PUT|POST /api/psc/sync/upload/{token}/ — Upload attachment payload by token
- POST /api/psc/sync/resolve-conflict/ — Resolve sync conflict
- GET /api/psc/sync/conflicts/ — List unresolved conflicts

Implements: FEAT-SYNC-002, FEAT-SYNC-003, FEAT-SYNC-004, FEAT-SYNC-005, FEAT-SYNC-006
"""

import logging
import os
import uuid as uuid_module

from django.conf import settings
from django.core import signing
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.car.models import Evidence
from .permissions import IsVesselUser, CanResolveConflict
from .serializers import (
    SyncPullRequestSerializer,
    SyncPushRequestSerializer,
    SyncConflictResolveSerializer,
    SyncConflictResponseSerializer,
)
from . import sync_service
from . import conflict_resolver
from .models import SyncConflict, ConflictStatus

logger = logging.getLogger(__name__)


class SyncPullView(APIView):
    """
    POST /api/psc/sync/pull/

    Pull changes from server to vessel using delta sync.
    Only vessel users (VESSEL_MASTER, VESSEL_CREW) can pull.

    Per BACKEND_STRUCTURE.md Section 10.9
    Implements: FEAT-SYNC-002

    Request:
        {
            "vessel_id": "uuid",
            "last_sync_token": "uuid" (optional),
            "last_server_version": 12345
        }

    Response:
        {
            "data": {
                "inspections": [...],
                "deficiencies": [...],
                "cars": [...],
                "corrective_actions": [...],
                "evidence_metadata": [...],
                "activity_history": [...]
            },
            "sync_token": "uuid",
            "server_version": 12350
        }
    """
    permission_classes = [IsAuthenticated, IsVesselUser]

    def post(self, request):
        serializer = SyncPullRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        vessel_id = serializer.validated_data['vessel_id']
        last_server_version = serializer.validated_data['last_server_version']
        last_sync_token = serializer.validated_data.get('last_sync_token')

        # Verify vessel_id matches user's vessel
        if hasattr(request.user, 'vessel_id') and request.user.vessel_id:
            if str(request.user.vessel_id) != str(vessel_id):
                return Response(
                    {'message': 'Vessel ID does not match your assigned vessel.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            result = sync_service.pull_changes(
                vessel_id=vessel_id,
                last_server_version=last_server_version,
                last_sync_token=last_sync_token,
                user_id=request.user.employee_id or str(request.user.id),
            )
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Sync pull failed: {e}")
            return Response(
                {'message': f'Sync pull failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SyncPushView(APIView):
    """
    POST /api/psc/sync/push/

    Push changes from vessel to server.
    Only vessel users (VESSEL_MASTER, VESSEL_CREW) can push.

    Per BACKEND_STRUCTURE.md Section 10.9
    Implements: FEAT-SYNC-003, FEAT-SYNC-004

    Request:
        {
            "sync_id": "uuid",
            "vessel_id": "uuid",
            "checksum": "sha256-hash",
            "events": [...],
            "attachments": [...]
        }

    Response:
        {
            "data": {
                "sync_id": "uuid",
                "processed": 5,
                "failed": 0,
                "conflicts": [],
                "id_mappings": {...},
                "attachment_upload_urls": [...]
            }
        }
    """
    permission_classes = [IsAuthenticated, IsVesselUser]

    def post(self, request):
        serializer = SyncPushRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        vessel_id = data['vessel_id']

        # Verify vessel_id matches user's vessel
        if hasattr(request.user, 'vessel_id') and request.user.vessel_id:
            if str(request.user.vessel_id) != str(vessel_id):
                return Response(
                    {'message': 'Vessel ID does not match your assigned vessel.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            result = sync_service.push_changes(
                sync_id=data['sync_id'],
                vessel_id=vessel_id,
                checksum=data['checksum'],
                events=data['events'],
                attachments=data.get('attachments', []),
                user_id=request.user.employee_id or str(request.user.id),
            )
            return Response({'data': result}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Sync push failed: {e}")
            return Response(
                {'message': f'Sync push failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SyncAttachmentUploadView(APIView):
    """
    PUT/POST /api/psc/sync/upload/{token}/

    Upload binary attachment payload to a tokenized sync URL.
    Token is issued by sync push response (attachment_upload_urls).
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def put(self, request, token):
        return self._handle_upload(request, token)

    def post(self, request, token):
        return self._handle_upload(request, token)

    def _handle_upload(self, request, token):
        try:
            payload = signing.loads(
                token,
                salt=sync_service.UPLOAD_TOKEN_SALT,
                max_age=sync_service.UPLOAD_TOKEN_MAX_AGE_SECONDS,
            )
        except signing.SignatureExpired:
            return Response(
                {'message': 'Upload token expired.'},
                status=status.HTTP_410_GONE,
            )
        except signing.BadSignature:
            return Response(
                {'message': 'Invalid upload token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        client_id = payload.get('client_id')
        if not client_id:
            return Response(
                {'message': 'Upload token missing client_id.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_bytes = request.body
        if not file_bytes:
            return Response(
                {'message': 'No file payload provided.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        evidence = (
            Evidence.objects.select_related('car__deficiency__inspection')
            .filter(client_id=client_id, is_deleted=False)
            .first()
        )
        if not evidence:
            return Response(
                {'message': 'Evidence record not found for upload token.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        vessel_id = getattr(
            getattr(
                getattr(evidence.car, 'deficiency', None),
                'inspection',
                None,
            ),
            'vessel_id',
            'unknown',
        )
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        short_uuid = str(uuid_module.uuid4())[:4]
        _, file_ext = os.path.splitext(evidence.file_name or '')
        safe_filename = f"{evidence.evidence_type.lower()}_{timestamp}_{short_uuid}{file_ext.lower()}"
        relative_path = f"psc/{vessel_id}/cars/{evidence.car_id}/{safe_filename}"
        upload_base = getattr(settings, 'UPLOAD_BASE_PATH', 'uploads')
        full_path = os.path.join(upload_base, relative_path)

        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as destination:
                destination.write(file_bytes)
        except OSError as exc:
            logger.error(f"Sync attachment write failed: {exc}")
            evidence.sync_status = 'FAILED'
            evidence.save(update_fields=['sync_status'])
            return Response(
                {'message': 'Failed to store attachment payload.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        content_type = request.content_type or evidence.mime_type or 'application/octet-stream'
        evidence.file_path = relative_path
        evidence.file_size = len(file_bytes)
        evidence.mime_type = content_type
        evidence.sync_status = 'SYNCED'
        evidence.save(update_fields=['file_path', 'file_size', 'mime_type', 'sync_status'])

        return Response(status=status.HTTP_204_NO_CONTENT)


class SyncResolveConflictView(APIView):
    """
    POST /api/psc/sync/resolve-conflict/

    Resolve a sync conflict. Only Office/DPA users can resolve.

    Per BACKEND_STRUCTURE.md Section 10.9
    Implements: FEAT-SYNC-005

    Request:
        {
            "conflict_id": "uuid",
            "resolution": "KEEP_SERVER" | "KEEP_VESSEL" | "REOPEN_FOR_MERGE",
            "notes": "optional reason"
        }

    Response:
        Resolved conflict object
    """
    permission_classes = [IsAuthenticated, CanResolveConflict]

    def post(self, request):
        serializer = SyncConflictResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            resolved_conflict = conflict_resolver.resolve_conflict(
                conflict_id=data['conflict_id'],
                resolution=data['resolution'],
                resolved_by=request.user.employee_id or str(request.user.id),
                notes=data.get('notes', ''),
            )

            response_serializer = SyncConflictResponseSerializer(resolved_conflict)
            return Response(
                {'data': response_serializer.data},
                status=status.HTTP_200_OK,
            )
        except SyncConflict.DoesNotExist:
            return Response(
                {'message': 'Conflict not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response(
                {'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}")
            return Response(
                {'message': f'Resolution failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SyncConflictListView(APIView):
    """
    GET /api/psc/sync/conflicts/

    List unresolved sync conflicts.
    Vessel users see only their vessel's conflicts.
    Office/DPA users see all pending conflicts.

    Per BACKEND_STRUCTURE.md Section 10.9
    Implements: FEAT-SYNC-004
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = SyncConflict.objects.filter(status=ConflictStatus.PENDING)

        # Vessel users see only their vessel's conflicts
        if hasattr(request.user, 'vessel_id') and request.user.vessel_id:
            queryset = queryset.filter(vessel_id=request.user.vessel_id)

        serializer = SyncConflictResponseSerializer(queryset, many=True)
        return Response(
            {'data': serializer.data},
            status=status.HTTP_200_OK,
        )
