"""
Notification views per BACKEND_STRUCTURE.md Section 10.11.

Endpoints:
- GET /api/psc/notifications/ - List notifications
- POST /api/psc/notifications/mark-read/ - Mark specific notifications read
- POST /api/psc/notifications/mark-all-read/ - Mark all notifications read

Implements: PRD.md FEAT-NOTIF-001
"""

import math

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Notification
from .serializers import NotificationListSerializer, MarkReadSerializer


def _build_user_notification_filter(user):
    """Build visibility filter for notifications owned by the authenticated user."""
    if user.user_type == 'VESSEL':
        return Q(recipient_type='CREW', recipient_id=user.crew_id)
    if user.user_type == 'OFFICE':
        return Q(recipient_type='OFFICE', recipient_id=user.employee_id)
    return None


class NotificationListView(APIView):
    """
    GET /api/psc/notifications/

    List notifications for the authenticated user.
    Filtered by recipient_type + recipient_id from JWT.
    Supports is_read filter and pagination.

    Per BACKEND_STRUCTURE.md Section 10.11
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        recipient_filter = _build_user_notification_filter(user)
        if recipient_filter is None:
            return Response({
                'error': 'INVALID_USER_TYPE',
                'message': 'Unable to determine user type.',
            }, status=status.HTTP_403_FORBIDDEN)
        queryset = Notification.objects.filter(recipient_filter)

        # Optional is_read filter
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            is_read_bool = is_read.lower() in ('true', '1')
            queryset = queryset.filter(is_read=is_read_bool)

        # Order by created_date DESC (newest first)
        queryset = queryset.order_by('-created_date')

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        page_size = min(page_size, 100)  # Cap at 100

        total_count = queryset.count()
        total_pages = max(1, math.ceil(total_count / page_size))
        offset = (page - 1) * page_size

        notifications = queryset[offset:offset + page_size]
        serializer = NotificationListSerializer(notifications, many=True)

        return Response({
            'data': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
            },
        })


class MarkReadView(APIView):
    """
    POST /api/psc/notifications/mark-read/

    Mark specific notifications as read.
    Only marks notifications that belong to the requesting user.

    Per BACKEND_STRUCTURE.md Section 10.11
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = MarkReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data['notification_ids']
        user = request.user
        now = timezone.now()

        recipient_filter = _build_user_notification_filter(user)
        if recipient_filter is None:
            return Response({
                'error': 'INVALID_USER_TYPE',
                'message': 'Unable to determine user type.',
            }, status=status.HTTP_403_FORBIDDEN)

        updated = Notification.objects.filter(
            recipient_filter,
            id__in=notification_ids,
            is_read=False,
        ).update(is_read=True, read_at=now)

        return Response({
            'data': {'marked_count': updated},
            'message': f'{updated} notification(s) marked as read.',
        })


class MarkAllReadView(APIView):
    """
    POST /api/psc/notifications/mark-all-read/

    Mark all of the user's notifications as read.

    Per BACKEND_STRUCTURE.md Section 10.11
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        now = timezone.now()

        recipient_filter = _build_user_notification_filter(user)
        if recipient_filter is None:
            return Response({
                'error': 'INVALID_USER_TYPE',
                'message': 'Unable to determine user type.',
            }, status=status.HTTP_403_FORBIDDEN)

        updated = Notification.objects.filter(
            recipient_filter,
            is_read=False,
        ).update(is_read=True, read_at=now)

        return Response({
            'data': {'marked_count': updated},
            'message': f'{updated} notification(s) marked as read.',
        })
