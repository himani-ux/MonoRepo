"""
CAR URL configuration per BACKEND_STRUCTURE.md Section 10.5.

Routes under /api/psc/cars/
"""

from django.urls import path

from .views import (
    CARListView,
    CARDetailView,
    CARUpdateView,
    CARSubmitView,
    CARPICAcceptView,
    CARReworkView,
    CARDPACloseView,
    CARReopenView,
    CARWorkflowView,
    CARAvailableActionsView,
    EvidenceUploadView,
    CorrectiveActionCreateView,
    PhysicalVerificationCreateView,
)
from .report_views import CARExportPDFView

app_name = 'car'  # Required for namespace in include()

urlpatterns = [
    # CAR - List
    path('', CARListView.as_view(), name='list'),

    # CAR - Detail and Update
    path('<uuid:id>/', CARDetailView.as_view(), name='detail'),
    path('<uuid:id>/update/', CARUpdateView.as_view(), name='update'),

    # CAR - Unified workflow (new)
    path('<uuid:id>/workflow/', CARWorkflowView.as_view(), name='workflow'),
    path('<uuid:id>/available-actions/', CARAvailableActionsView.as_view(), name='available-actions'),

    # CAR - Legacy state transitions (deprecated, kept for backward compat)
    path('<uuid:id>/submit/', CARSubmitView.as_view(), name='submit'),
    path('<uuid:id>/pic-accept/', CARPICAcceptView.as_view(), name='pic-accept'),
    path('<uuid:id>/rework/', CARReworkView.as_view(), name='rework'),
    path('<uuid:id>/dpa-close/', CARDPACloseView.as_view(), name='dpa-close'),
    path('<uuid:id>/reopen/', CARReopenView.as_view(), name='reopen'),

    # Evidence - Upload (nested under CAR)
    path('<uuid:car_id>/evidence/', EvidenceUploadView.as_view(), name='evidence-upload'),

    # Corrective actions - Create (nested under CAR)
    path('<uuid:car_id>/actions/', CorrectiveActionCreateView.as_view(), name='action-create'),

    # Physical verification - Create (nested under CAR)
    path('<uuid:car_id>/physical-verification/', PhysicalVerificationCreateView.as_view(), name='pv-create'),

    # Reports - PDF export
    path('<uuid:id>/export-pdf/', CARExportPDFView.as_view(), name='export-pdf'),
]
