"""
Corrective Action URL configuration per BACKEND_STRUCTURE.md Section 10.6.

Routes under /api/psc/actions/
"""

from django.urls import path

from .views import (
    CorrectiveActionUpdateView,
    CorrectiveActionCompleteView,
    CorrectiveActionDeleteView,
)

app_name = 'actions'  # Required for namespace in include()

urlpatterns = [
    # Action - Update
    path('<uuid:id>/', CorrectiveActionUpdateView.as_view(), name='update'),

    # Action - Complete
    path('<uuid:id>/complete/', CorrectiveActionCompleteView.as_view(), name='complete'),

    # Action - Delete (soft-delete)
    path('<uuid:id>/delete/', CorrectiveActionDeleteView.as_view(), name='delete'),
]
