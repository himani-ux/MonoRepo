"""
URL configuration for VIMS Inspection - PSC Backend.

API prefix: /api/psc/
Per BACKEND_STRUCTURE.md and IMPLEMENTATION_PLAN.md
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include

from apps.inspection.dashboard_views import DashboardView


def health_check(request):
    """Health check endpoint for monitoring."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'psc-backend',
        'version': '1.0.0',
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health check
    path('api/psc/health/', health_check, name='health-check'),

    # Authentication endpoints
    # Per IMPLEMENTATION_PLAN.md Step 2.1:
    # POST /api/psc/auth/login/
    # POST /api/psc/auth/refresh/
    # POST /api/psc/auth/logout/
    # GET /api/psc/auth/me/
    path('api/psc/auth/', include('apps.accounts.urls', namespace='accounts')),

    # Legacy VIMS_basic modules kept under their original API prefixes
    path('api/orb/', include('modules.orb.orb.urls')),
    path('api/circular/', include('modules.circular.circular_office.urls')),
    path('api/circular/', include('modules.circular.circular_ship.urls')),

    # Master data endpoints
    # Per IMPLEMENTATION_PLAN.md Step 3.1:
    # GET /api/psc/masters/mou/
    # GET /api/psc/masters/psc-action-codes/
    # GET /api/psc/masters/psc-def-codes/
    # GET /api/psc/masters/clc/
    # GET /api/psc/masters/pic/
    path('api/psc/masters/', include('apps.masters.urls', namespace='masters')),

    # Inspection endpoints
    # Per IMPLEMENTATION_PLAN.md Step 4.1:
    # GET/POST /api/psc/inspections/
    # GET/PUT/DELETE /api/psc/inspections/{id}/
    # POST /api/psc/inspections/{id}/submit/
    # POST /api/psc/inspections/{id}/pic-review/
    # POST /api/psc/inspections/{id}/dpa-close/
    # POST /api/psc/inspections/{id}/upload-report/
    # POST /api/psc/inspections/{id}/deficiencies/
    path('api/psc/inspections/', include('apps.inspection.urls', namespace='inspection')),

    # Deficiency endpoints (separate from inspection)
    # Per IMPLEMENTATION_PLAN.md Step 4.2:
    # PUT /api/psc/deficiencies/{id}/action-code/
    path('api/psc/deficiencies/', include('apps.inspection.urls_deficiency', namespace='deficiency')),

    # PSC Follow-up endpoints
    # Per IMPLEMENTATION_PLAN.md Step 4.3:
    # POST /api/psc/psc-follow-up/register/
    path('api/psc/psc-follow-up/', include('apps.inspection.urls_followup', namespace='psc_followup')),

    # CAR endpoints
    # Per IMPLEMENTATION_PLAN.md Step 5.1:
    # GET /api/psc/cars/
    # GET/PUT /api/psc/cars/{id}/
    # POST /api/psc/cars/{id}/submit/
    # POST /api/psc/cars/{id}/pic-accept/
    # POST /api/psc/cars/{id}/rework/
    # POST /api/psc/cars/{id}/dpa-close/
    # POST /api/psc/cars/{id}/reopen/
    # POST /api/psc/cars/{car_id}/evidence/
    # POST /api/psc/cars/{car_id}/actions/
    # POST /api/psc/cars/{car_id}/physical-verification/
    path('api/psc/cars/', include('apps.car.urls', namespace='car')),

    # Evidence endpoints (separate from CAR)
    # DELETE /api/psc/evidence/{id}/
    path('api/psc/evidence/', include('apps.car.urls_evidence', namespace='evidence')),

    # Corrective Action endpoints (separate from CAR)
    # PUT /api/psc/actions/{id}/
    # POST /api/psc/actions/{id}/complete/
    path('api/psc/actions/', include('apps.car.urls_actions', namespace='actions')),

    # Physical Verification endpoints (separate from CAR)
    # PUT /api/psc/physical-verifications/{id}/
    # POST /api/psc/physical-verifications/{id}/close/
    path('api/psc/physical-verifications/', include('apps.car.urls_pv', namespace='pv')),

    # Sync endpoints
    # Per IMPLEMENTATION_PLAN.md Step 7.1:
    # POST /api/psc/sync/pull/
    # POST /api/psc/sync/push/
    # PUT|POST /api/psc/sync/upload/{token}/
    # POST /api/psc/sync/resolve-conflict/
    # GET /api/psc/sync/conflicts/
    path('api/psc/sync/', include('apps.sync.urls', namespace='sync')),

    # Dashboard endpoint
    path('api/psc/dashboard/', DashboardView.as_view(), name='dashboard'),

    # Reports endpoints (DefIntel / OpenSource)
    path('api/psc/reports/', include('apps.inspection.urls_reports', namespace='reports')),

    # Notification endpoints
    # Per IMPLEMENTATION_PLAN.md Step 8.1:
    # GET /api/psc/notifications/
    # POST /api/psc/notifications/mark-read/
    # POST /api/psc/notifications/mark-all-read/
    path('api/psc/notifications/', include('apps.notifications.urls', namespace='notifications')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        '/uploads/',
        document_root=str(getattr(settings, 'UPLOAD_BASE_PATH', settings.BASE_DIR / 'uploads')),
    )
