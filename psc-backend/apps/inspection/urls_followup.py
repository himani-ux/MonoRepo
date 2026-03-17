"""
PSC Follow-up URL routes.

Routes:
- POST /api/psc/inspections/<inspection_id>/follow-up/ (canonical, via inspection urls)
- POST /api/psc/psc-follow-up/register/ (legacy alias)
"""

from django.urls import path

from .followup_views import LegacyFollowUpView

app_name = 'psc_followup'

urlpatterns = [
    # Legacy alias — kept for backward compatibility
    path('register/', LegacyFollowUpView.as_view(), name='register'),
]
