"""
Notification URL configuration.

Per BACKEND_STRUCTURE.md Section 10.11:
- GET /api/psc/notifications/
- POST /api/psc/notifications/mark-read/
- POST /api/psc/notifications/mark-all-read/

Implements: PRD.md FEAT-NOTIF-001
"""

from django.urls import path
from .views import NotificationListView, MarkReadView, MarkAllReadView

app_name = 'notifications'

urlpatterns = [
    path('', NotificationListView.as_view(), name='list'),
    path('mark-read/', MarkReadView.as_view(), name='mark-read'),
    path('mark-all-read/', MarkAllReadView.as_view(), name='mark-all-read'),
]
