"""
Physical Verification URL configuration per BACKEND_STRUCTURE.md Section 10.8.

Routes under /api/psc/physical-verifications/
"""

from django.urls import path

from .views import (
    PhysicalVerificationUpdateView,
    PhysicalVerificationCloseView,
)

app_name = 'pv'  # Required for namespace in include()

urlpatterns = [
    # PV - Update
    path('<uuid:id>/', PhysicalVerificationUpdateView.as_view(), name='update'),

    # PV - Close
    path('<uuid:id>/close/', PhysicalVerificationCloseView.as_view(), name='close'),
]
