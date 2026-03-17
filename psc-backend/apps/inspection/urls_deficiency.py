"""
Deficiency URL configuration per BACKEND_STRUCTURE.md Section 10.4.

Endpoints at /api/psc/deficiencies/:
- GET  /api/psc/deficiencies/ - List with filters (vessel-scoped)
- PUT  /api/psc/deficiencies/{id}/action-code/ - Update action code
- POST /api/psc/deficiencies/{id}/workflow/ - Transition workflow status
- POST /api/psc/deficiencies/{id}/allocate/ - Allocate to crew member

Note: POST /api/psc/inspections/{id}/deficiencies/ is in urls.py
"""

from django.urls import path

from .deficiency_views import (
    DeficiencyActionCodeUpdateView,
    DeficiencyWorkflowTransitionView,
    DeficiencyAllocateView,
    DeficiencyListFilteredView,
)

app_name = 'deficiency'

urlpatterns = [
    # List with filters
    path('', DeficiencyListFilteredView.as_view(), name='list'),

    # Update action code
    path('<uuid:id>/action-code/', DeficiencyActionCodeUpdateView.as_view(), name='action-code'),

    # Workflow transition
    path('<uuid:id>/workflow/', DeficiencyWorkflowTransitionView.as_view(), name='workflow'),

    # Allocate to crew member
    path('<uuid:id>/allocate/', DeficiencyAllocateView.as_view(), name='allocate'),
]
