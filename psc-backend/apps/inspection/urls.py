"""
Inspection URL configuration per BACKEND_STRUCTURE.md Section 10.3 and 10.4.

Inspection Endpoints:
- GET /api/psc/inspections/ - List with filters
- POST /api/psc/inspections/ - Create new
- GET /api/psc/inspections/{id}/ - Detail
- PUT /api/psc/inspections/{id}/ - Update
- DELETE /api/psc/inspections/{id}/ - Soft delete
- POST /api/psc/inspections/{id}/submit/ - Submit for review
- POST /api/psc/inspections/{id}/pic-review/ - PIC review
- POST /api/psc/inspections/{id}/dpa-close/ - DPA close
- POST /api/psc/inspections/{id}/upload-report/ - Upload report

Deficiency Endpoints:
- POST /api/psc/inspections/{id}/deficiencies/ - Add deficiency (auto-creates CAR)
- PUT /api/psc/deficiencies/{id}/action-code/ - Update action code
"""

from django.urls import path

from .views import (
    InspectionListView,
    InspectionCreateView,
    InspectionDetailView,
    InspectionUpdateView,
    InspectionDeleteView,
    InspectionSubmitView,
    InspectionPICReviewView,
    InspectionDPACloseView,
    InspectionUploadReportView,
    InspectionReportViewFileView,
)
from .deficiency_views import (
    DeficiencyCreateView,
    DeficiencyActionCodeUpdateView,
    BulkDeficiencySubmitView,
)
from .followup_views import FollowUpView
from .report_views import DeficiencyExcelExportView, BulkCARExportView

app_name = 'inspection'

urlpatterns = [
    # Inspection - List and Create
    path('', InspectionListView.as_view(), name='list'),
    path('create/', InspectionCreateView.as_view(), name='create'),

    # Inspection - Detail, Update, Delete
    path('<uuid:id>/', InspectionDetailView.as_view(), name='detail'),
    path('<uuid:id>/update/', InspectionUpdateView.as_view(), name='update'),
    path('<uuid:id>/delete/', InspectionDeleteView.as_view(), name='delete'),

    # Inspection - State transitions
    path('<uuid:id>/submit/', InspectionSubmitView.as_view(), name='submit'),
    path('<uuid:id>/pic-review/', InspectionPICReviewView.as_view(), name='pic-review'),
    path('<uuid:id>/dpa-close/', InspectionDPACloseView.as_view(), name='dpa-close'),

    # Inspection - Report upload
    path('<uuid:id>/upload-report/', InspectionUploadReportView.as_view(), name='upload-report'),
    path('reports/<uuid:report_id>/view/', InspectionReportViewFileView.as_view(), name='report-view'),

    # Deficiency - Create (nested under inspection)
    path('<uuid:inspection_id>/deficiencies/', DeficiencyCreateView.as_view(), name='deficiency-create'),

    # Deficiency - Bulk submit (Master submits multiple APPROVED DEFs)
    path('<uuid:inspection_id>/deficiencies/bulk-submit/', BulkDeficiencySubmitView.as_view(), name='deficiency-bulk-submit'),

    # Reports - Bulk CAR PDF export (ZIP of all CARs for an inspection)
    path('<uuid:inspection_id>/cars/export-pdf/', BulkCARExportView.as_view(), name='bulk-car-export'),

    # Follow-up wizard (canonical endpoint)
    path('<uuid:inspection_id>/follow-up/', FollowUpView.as_view(), name='follow-up'),

    # Reports - Excel export
    path('export-excel/', DeficiencyExcelExportView.as_view(), name='export-excel'),
]

# Deficiency endpoints at /api/psc/deficiencies/
deficiency_urlpatterns = [
    path('<uuid:id>/action-code/', DeficiencyActionCodeUpdateView.as_view(), name='deficiency-action-code'),
]
