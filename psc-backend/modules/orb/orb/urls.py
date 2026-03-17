# logbook/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Register all ViewSets
router = DefaultRouter()
router.register(r'vessels', views.VesselDataViewSet, basename='vesseldata')
router.register(r'tanks', views.VesselTankDetailsViewSet, basename='vesseltankdetails')
router.register(r'codes', views.ORBCodesViewSet, basename='orbcode')
router.register(r'operations', views.OperationEntryViewSet, basename='operation')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/operations/<uuid:pk>/soft_delete/', views.OperationEntryViewSet.as_view({'post': 'soft_delete_entry'}), name='operation-soft-delete'),
    path("api/tanks-for-orb/", views.get_tanks_for_orb_code, name="tanks-for-orb"),
    path('api/current-vessel/', views.current_vessel_handler, name='current_vessel'),
    path('api/operations/<str:id>/approve/', views.approve_operation, name='approve_operation'),
    path('api/operations/<str:id>/reject/', views.reject_operation, name='reject_operation'),
    path('operations/<str:pk>/', views.retrieve_operation, name='retrieve_operation'),
    path('api/get_last_page_number/', views.get_last_page_number, name='get_last_page_number'),
    path('api/non-deleted-entries/', views.get_non_deleted_entries_view, name='non-deleted-entries'),
    path('api/deleted-entries/', views.get_deleted_entries_view, name='deleted-entries'),
    path('api/rejected-entries/', views.get_rejected_entries_view, name='rejected-entries'),
    path('api/approved-entries/', views.get_approved_entries_view, name='approved-entries'),
    path('api/update-print-status/', views.update_print_status, name='update-print-status'),
    path('api/get-internal-ip/', views.get_client_internal_ip, name='get-internal-ip'),
    path('api/save-pdf-metadata/', views.save_pdf_metadata, name='save-pdf-metadata'),
    path('api/list-pdfs/', views.list_pdfs, name='list-pdfs'),
    path('api/download-pdf/<uuid:pdf_id>/', views.download_pdf, name='download-pdf'), 
    path('api/get-current-user-vessel/', views.get_vessel_id_for_current_user, name='get_current_user_vessel'),
    path('api/latest-entry-date/', views.get_latest_entry_date, name='get_latest_entry_date'),
] 
