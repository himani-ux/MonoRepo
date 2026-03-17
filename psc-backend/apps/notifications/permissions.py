"""
Notification permissions.

Implements: PRD.md FEAT-NOTIF-001
"""

from rest_framework.permissions import BasePermission


class IsNotificationRecipient(BasePermission):
    """
    Only allow users to access their own notifications.

    Vessel users (CREW) see notifications where:
    - recipient_type = 'CREW' AND recipient_id = user.crew_id

    Office users see notifications where:
    - recipient_type = 'OFFICE' AND recipient_id = user.employee_id
    """
    message = 'You can only access your own notifications.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.user_type == 'VESSEL':
            return (
                obj.recipient_type == 'CREW'
                and obj.recipient_id == user.crew_id
            )
        elif user.user_type == 'OFFICE':
            return (
                obj.recipient_type == 'OFFICE'
                and obj.recipient_id == user.employee_id
            )
        return False
