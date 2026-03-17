"""
Evidence URL configuration per BACKEND_STRUCTURE.md Section 10.7.

Routes under /api/psc/evidence/
"""

from django.urls import path

from .views import EvidenceDeleteView, EvidenceViewFileView

app_name = 'evidence'  # Required for namespace in include()

urlpatterns = [
    # Evidence - View
    path('<uuid:id>/view/', EvidenceViewFileView.as_view(), name='view'),

    # Evidence - Delete
    path('<uuid:id>/', EvidenceDeleteView.as_view(), name='delete'),
]
