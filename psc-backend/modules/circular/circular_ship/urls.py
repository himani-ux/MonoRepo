"""
URL configuration for circular_ship app.

Handles all endpoints for ship-side notification management and crew operations.
"""
from django.urls import path, re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    

    # Notification Endpoints
    path('api/ship/notifications/', views.get_master_notifications, name='get-master-notifications'),
    path('api/crew/notifications/', views.get_non_master_notifications, name='get-non-master-notifications'),
    path('api/msc/pdf-url/', views.get_notification_pdf_url, name='pdf-url'),
    
    # Acknowledgment Endpoints
    path('api/msc/read-ack/', views.crew_acknowledge_notification, name='read-ack'),
    
    # Reminder Endpoints
    path('api/msc/remind-crew/', views.send_reminder, name='remind-crew'),
    
    # Crew Endpoints
    path('api/crew/list/', views.get_crew_list, name='crew-list'),
    path('api/crew/status/', views.get_crew_status, name='crew-status-list'),
    re_path(
        r'^api/notifications/(?P<id>[^/].*?)/crew-status/$',
        views.get_crew_status,
        name='get_crew_status'
    ),
    
    # Report Endpoints
    path('api/reports/download-pdf/', views.download_filtered_report, name='download_filtered_report'),
]

