"""
URL configuration for circular_office app.

Handles all endpoints for office-side notification management.
"""
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Document and Lookup Endpoints
    path('api/roles/', views.get_master_roles, name='get_master_roles'),
    path('api/mapping-role-users/', views.get_mapping_role_users, name='get_mapping_role_users'),
    path('api/users/', views.get_users, name='get_users'),
    path('api/document-types/', views.get_document_types, name='document-types'),
    path('api/departments/', views.get_departments, name='departments'),
    path('api/priorities/', views.get_priorities, name='priorities'),
    path('api/sub-categories/', views.get_sub_categories, name='sub_categories'),
    path('api/second-sub-categories/', views.get_second_sub_categories, name='second_sub_categories'),
    path('api/vessels/', views.get_vessels, name='get_vessels'),
    path('api/master-applied-ranks/', views.get_master_applied_ranks, name='get_master_applied_ranks'),
    path('api/ranks/', views.get_all_ranks, name='get_all_ranks'),
    
    # Notification Endpoints
    path('api/notifications/', views.create_notification, name='create-notification'),
    path('api/submitted/', views.get_notifications, name='get_notifications'),
    path('api/submitted/<path:sr_no>/', views.get_notification_details, name='get_notification_details'),
    path('api/submitted/<uuid:notification_id>/', views.get_single_notification, name='get_single_notification'),
    path('api/notifications/<path:sr_no>/delete/', views.delete_notification, name='delete_notification'),
    path('api/notifications/<path:sr_no>/supersede/', views.supersede_notification, name='supersede_notification'),
    path('api/notifications/<path:notification_sr_no>/update-status/', views.update_notification_status, name='update_notification_status'),
    path('api/notifications/send-emails/', views.send_emails_to_vessels, name='send_emails_to_vessels'),
    path('api/notifications/<path:notification_sr_no>/link-ranks/', views.link_notification_to_ranks, name='link_notification_to_ranks'),
    path('api/notifications/<path:notification_sr_no>/crew-delivery-status/', views.get_crew_ids_and_status_by_notification_sr_no, name='get_crew_ids_and_status_by_notification_sr_no'),
    path('api/notifications/<path:notification_sr_no>/send-individual-reminder/', views.send_individual_notification_reminder, name='send_individual_notification_reminder'),
    path('api/notifications/create-delivery-records/', views.create_delivery_records, name='create_delivery_records'),
    
    # Draft Endpoints
    path('api/notifications/draft/', views.get_notifications_draft, name='get_notifications_draft'),
    path('api/user-drafts/', views.get_user_drafts, name='get_user_drafts'),
    path('api/draft/<path:sr_no>/update/', views.update_draft_by_sr_no, name='update_draft_by_sr_no'),
    path('api/drafts/<str:draft_id>/update/', views.update_draft_by_id, name='update_draft_by_id'),
    path('api/draft/<path:sr_no>/delete/', views.delete_draft_by_sr_no, name='delete_draft_by_sr_no'),
    path('api/draft/<path:sr_no>/', views.get_draft_by_sr_no, name='get_draft_by_sr_no'),
    
    # Approved and User Notifications
    path('api/approved-notifications/', views.get_approved_notifications, name='get_approved_notifications'),
    path('api/approved-notifications/download-csv/', views.get_approved_notifications_csv, name='get_approved_notifications_csv'),
    path('api/user-notifications/', views.get_user_notifications, name='user_notifications'),
    
    # Crew Endpoints
    path('api/crews-by-department/', views.get_crews_by_department, name='get_crews_by_department'),
    path('api/crews-by-department-and-vessel/', views.get_crews_by_department_and_vessel, name='get_crews_by_department_and_vessel'),
    
    # Edit Endpoints
    path('api/notifications/<path:notification_id>/edit-pending/', views.edit_pending_notification, name='edit_pending_notification'),
]


