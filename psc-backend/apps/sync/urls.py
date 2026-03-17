"""
Sync URL configuration per BACKEND_STRUCTURE.md Section 10.9.

Endpoints:
- POST /api/psc/sync/pull/
- POST /api/psc/sync/push/
- PUT|POST /api/psc/sync/upload/{token}/
- POST /api/psc/sync/resolve-conflict/
- GET /api/psc/sync/conflicts/

Implements: FEAT-SYNC-002, FEAT-SYNC-003, FEAT-SYNC-004, FEAT-SYNC-005
"""

from django.urls import path

from .views import (
    SyncPullView,
    SyncPushView,
    SyncAttachmentUploadView,
    SyncResolveConflictView,
    SyncConflictListView,
)

app_name = 'sync'

urlpatterns = [
    path('pull/', SyncPullView.as_view(), name='sync-pull'),
    path('push/', SyncPushView.as_view(), name='sync-push'),
    path('upload/<str:token>/', SyncAttachmentUploadView.as_view(), name='sync-upload'),
    path('resolve-conflict/', SyncResolveConflictView.as_view(), name='sync-resolve-conflict'),
    path('conflicts/', SyncConflictListView.as_view(), name='sync-conflicts'),
]
